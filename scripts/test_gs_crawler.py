"""Unit tests for scripts/gs_crawler.py (standard library only).

Run from the repo root:  python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import contextlib
import gzip
import io
import json
import os
import shutil
import tempfile
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
from email.message import Message
from unittest import mock

import gs_crawler as gs

# Trimmed from a real profile page (2026-09-10): the stats table, the name and
# the citation histogram, with the surrounding markup Scholar actually emits.
PROFILE_HTML = """
<div id="gsc_prf_i"><div id="gsc_prf_inw"><div id="gsc_prf_in">Xiaoxiong Zhang</div></div>
<div class="gsc_prf_il">Master Student, Southern University of Science and Technology</div></div>
<table id="gsc_rsb_st"><thead><tr><th class="gsc_rsb_sth"></th><th class="gsc_rsb_sth">All</th>
<th class="gsc_rsb_sth">Since 2021</th></tr></thead><tbody>
<tr><td class="gsc_rsb_sc1"><a href="javascript:void(0)" class="gsc_rsb_f gs_ibl">Citations</a></td>
<td class="gsc_rsb_std">11</td><td class="gsc_rsb_std">11</td></tr>
<tr><td class="gsc_rsb_sc1"><a href="javascript:void(0)" class="gsc_rsb_f gs_ibl">h-index</a></td>
<td class="gsc_rsb_std">2</td><td class="gsc_rsb_std">2</td></tr>
<tr><td class="gsc_rsb_sc1"><a href="javascript:void(0)" class="gsc_rsb_f gs_ibl">i10-index</a></td>
<td class="gsc_rsb_std">0</td><td class="gsc_rsb_std">0</td></tr></tbody></table>
<div class="gsc_md_hist_w"><div class="gsc_md_hist_b">
<span class="gsc_g_t" style="right:35px">2025</span><span class="gsc_g_t" style="right:3px">2026</span>
<a href="javascript:void(0)" class="gsc_g_a" style="right:40px;top:128px;height:32px;z-index:2"><span class="gsc_g_al">2</span></a>
<a href="javascript:void(0)" class="gsc_g_a" style="right:8px;top:16px;height:144px;z-index:1"><span class="gsc_g_al">9</span></a>
</div></div>
"""

SERPAPI_PAYLOAD = {
    "author": {"name": "Cliff Meyer"},
    "cited_by": {
        # Keys are localized (this is the hl=fr example from the SerpApi docs).
        "table": [
            {"citations": {"all": 21934, "depuis_2016": 12302}},
            {"indice_h": {"all": 45, "depuis_2016": 36}},
            {"indice_i10": {"all": 59, "depuis_2016": 51}},
        ],
        "graph": [{"year": 2004, "citations": "59"}, {"year": 2005, "citations": "1,065"}],
    },
}


def record(citedby, days_old=0.0, **extra):
    rec = {
        "name": "n", "citedby": citedby, "hindex": 1, "source": "test", "runner": "r",
        "updated": (datetime.now(timezone.utc) - timedelta(days=days_old)).isoformat(timespec="seconds"),
    }
    rec.update(extra)
    return rec


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def http_error(url, code, body=None, headers=None):
    fp = io.BytesIO(body) if body is not None else None
    return urllib.error.HTTPError(url, code, "err", headers, fp)


class ParseProfileTests(unittest.TestCase):
    def test_real_markup(self):
        d = gs.parse_profile(PROFILE_HTML)
        self.assertEqual(d["name"], "Xiaoxiong Zhang")
        self.assertEqual(
            (d["citedby"], d["citedby5y"], d["hindex"], d["hindex5y"], d["i10index"], d["i10index5y"]),
            (11, 11, 2, 2, 0, 0),
        )
        self.assertEqual(d["cites_per_year"], {2025: 2, 2026: 9})

    def test_histogram_gap_and_thousands_separator(self):
        page = (
            '<td class="gsc_rsb_std">1,234</td>' * 6
            + '<span class="gsc_g_t">2023</span><span class="gsc_g_t">2024</span><span class="gsc_g_t">2025</span>'
            + '<a href="#" class="gsc_g_a" style="right:8px;z-index:1"><span class="gsc_g_al">9</span></a>'
            + '<a href="#" style="z-index:3" class="gsc_g_a"><span class="gsc_g_al">2</span></a>'
        )
        d = gs.parse_profile(page)
        self.assertEqual(d["citedby"], 1234)
        self.assertEqual(d["cites_per_year"], {2023: 2, 2024: 0, 2025: 9})

    def test_no_histogram(self):
        d = gs.parse_profile('<td class="gsc_rsb_std">0</td>' * 6)
        self.assertEqual(d["cites_per_year"], {})

    def test_missing_table_is_no_data(self):
        with self.assertRaises(gs.NoData):
            gs.parse_profile("<html><body>Please show you're not a robot</body></html>")


class BlockedDetectionTests(unittest.TestCase):
    def test_reasons(self):
        self.assertEqual(gs.blocked_reason(429, "https://scholar.google.com/x", ""), "HTTP 429")
        self.assertIn("sorry", gs.blocked_reason(200, "https://www.google.com/sorry/index?continue=x", ""))
        self.assertIn("consent", gs.blocked_reason(200, "https://consent.google.com/m?continue=x", ""))
        self.assertEqual(gs.blocked_reason(200, "https://scholar.google.com/x", '<div id="gs_captcha_ccl">'), "captcha page")
        self.assertIsNone(gs.blocked_reason(200, "https://scholar.google.com/citations?user=x", PROFILE_HTML))


class HttpGetTests(unittest.TestCase):
    def test_http_error_without_body(self):
        err = http_error("https://x", 404)
        with mock.patch.object(gs.urllib.request, "urlopen", side_effect=err):
            self.assertEqual(gs.http_get("https://x", {}), (404, "https://x", ""))

    def test_http_error_with_gzip_body(self):
        headers = Message()
        headers["Content-Encoding"] = "gzip"
        err = http_error("https://x/y", 429, gzip.compress(b"slow down"), headers)
        with mock.patch.object(gs.urllib.request, "urlopen", side_effect=err):
            self.assertEqual(gs.http_get("https://x", {}), (429, "https://x/y", "slow down"))


class FetchDirectTests(unittest.TestCase):
    def test_success_first_try(self):
        with mock.patch.object(gs, "http_get", return_value=(200, "https://scholar.google.com/citations?user=X", PROFILE_HTML)):
            d = gs.fetch_direct("X")
        self.assertEqual((d["citedby"], d["source"]), (11, "scholar.google.com"))

    def test_gives_up_after_attempts(self):
        with mock.patch.object(gs, "http_get", return_value=(429, "https://scholar.google.com/x", "")), \
             mock.patch.object(gs.time, "sleep") as sleep:
            with self.assertRaises(gs.NoData) as cm:
                gs.fetch_direct("X", attempts=3)
        self.assertIn("429", str(cm.exception))
        self.assertEqual(sleep.call_count, 2)

    def test_network_error_is_no_data(self):
        with mock.patch.object(gs, "http_get", side_effect=urllib.error.URLError("dns down")), \
             mock.patch.object(gs.time, "sleep"):
            with self.assertRaises(gs.NoData):
                gs.fetch_direct("X", attempts=2)


class SerpApiTests(unittest.TestCase):
    def test_parse_localized_payload(self):
        d = gs.parse_serpapi(SERPAPI_PAYLOAD)
        self.assertEqual(
            (d["name"], d["citedby"], d["citedby5y"], d["hindex"], d["hindex5y"], d["i10index"], d["i10index5y"]),
            ("Cliff Meyer", 21934, 12302, 45, 36, 59, 51),
        )
        self.assertEqual(d["cites_per_year"], {2004: 59, 2005: 1065})
        self.assertEqual(d["source"], "serpapi.com")

    def test_error_payloads(self):
        with self.assertRaises(gs.NoData):
            gs.parse_serpapi({"error": "Invalid API key."})
        with self.assertRaises(gs.NoData):
            gs.parse_serpapi({"cited_by": {"table": []}})

    def test_malformed_shapes_are_no_data(self):
        shapes = [
            {"cited_by": []},
            {"cited_by": {"table": {"citations": {}}}},
            {"cited_by": {"table": [None, None, None]}},
            {"cited_by": {"table": [{"citations": None}, {}, {}]}},
            {"cited_by": {"table": [{"citations": {"all": "abc"}}, {}, {}]}},
            {"cited_by": {"table": [[1], [2], [3]]}},
        ]
        for payload in shapes:
            with self.subTest(payload=payload), \
                 mock.patch.object(gs, "http_get", return_value=(200, "u", json.dumps(payload))), \
                 self.assertRaises(gs.NoData):
                gs.fetch_serpapi("X", "key")

    def test_tolerates_odd_graph_and_author(self):
        payload = json.loads(json.dumps(SERPAPI_PAYLOAD))
        payload["cited_by"]["graph"] = [None, {"year": "x"}, {"year": 2020, "citations": "3"}]
        payload["author"] = "not a dict"
        d = gs.parse_serpapi(payload)
        self.assertEqual((d["cites_per_year"], d["name"]), ({2020: 3}, None))

    def test_fetch_wraps_failures_as_no_data(self):
        cases = [
            mock.patch.object(gs, "http_get", side_effect=urllib.error.URLError("dns down")),
            mock.patch.object(gs, "http_get", return_value=(200, "u", "not json")),
            mock.patch.object(gs, "http_get", return_value=(200, "u", "[1, 2]")),
            mock.patch.object(gs, "http_get", return_value=(500, "u", "{}")),
        ]
        for patcher in cases:
            with patcher, self.assertRaises(gs.NoData):
                gs.fetch_serpapi("X", "key")

    def test_key_never_logged(self):
        seen = {}

        def fake_get(url, headers, timeout=30.0):
            seen["url"] = url
            return 200, url, json.dumps(SERPAPI_PAYLOAD)

        with mock.patch.object(gs, "http_get", side_effect=fake_get):
            gs.fetch_serpapi("X", "s3cret")
        self.assertIn("api_key=s3cret", seen["url"])  # sent to SerpApi ...
        with self.assertRaises(gs.NoData) as cm, \
             mock.patch.object(gs, "http_get", side_effect=urllib.error.URLError("boom")):
            gs.fetch_serpapi("X", "s3cret")
        self.assertNotIn("s3cret", str(cm.exception))  # ... but never in messages


class LoadRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def check(self, obj):
        path = os.path.join(self.tmp, "gs_data.json")
        write_json(path, obj)
        return gs.load_record(path)

    def test_validation(self):
        self.assertIsNone(gs.load_record(os.path.join(self.tmp, "missing.json")))
        self.assertIsNotNone(self.check(record(10)))
        self.assertIsNotNone(self.check(record(10, updated="2026-09-09T00:00:00Z")))
        self.assertIsNone(self.check(record("10")))
        self.assertIsNone(self.check(record(True)))
        self.assertIsNone(self.check(record(-1)))
        self.assertIsNone(self.check(record(10, updated="yesterday")))
        self.assertIsNone(self.check([1, 2]))


class CommandTests(unittest.TestCase):
    """Drive `fetch` and `resolve` through main() inside a temp working dir."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.cwd = os.getcwd()
        os.chdir(self.tmp)
        self.addCleanup(os.chdir, self.cwd)
        self.gh_output = os.path.join(self.tmp, "gh_output")
        env = {"GITHUB_OUTPUT": self.gh_output, "GITHUB_STEP_SUMMARY": os.path.join(self.tmp, "gh_summary")}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("SERPAPI_KEY", None)

    def run_main(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = gs.main(argv)
        return code, out.getvalue()

    def resolve(self, stale_days=14):
        return self.run_main(["resolve", "--collected", "collected", "--previous", "stats/gs_data.json",
                              "--out", "results", "--stale-days", str(stale_days)])

    def gh_out(self):
        with open(self.gh_output, encoding="utf-8") as f:
            return f.read()

    def published(self):
        with open("results/gs_data.json", encoding="utf-8") as f:
            return json.load(f)

    # fetch -------------------------------------------------------------
    def test_fetch_writes_outputs(self):
        with mock.patch.object(gs, "http_get", return_value=(200, "https://scholar.google.com/x", PROFILE_HTML)):
            code, out = self.run_main(["fetch", "--out", "results", "--label", "ubuntu-latest"])
        self.assertEqual(code, gs.EXIT_OK)
        data = self.published()
        self.assertEqual((data["citedby"], data["runner"], data["source"]), (11, "ubuntu-latest", "scholar.google.com"))
        self.assertIsNotNone(gs.parse_timestamp(data["updated"]))
        with open("results/gs_data_shieldsio.json", encoding="utf-8") as f:
            self.assertEqual(json.load(f)["message"], "11")

    def test_fetch_blocked_exits_2_without_output(self):
        with mock.patch.object(gs, "http_get", return_value=(200, "https://www.google.com/sorry/index", "")), \
             mock.patch.object(gs.time, "sleep"):
            code, out = self.run_main(["fetch", "--out", "results", "--label", "t", "--attempts", "2"])
        self.assertEqual(code, gs.EXIT_NO_DATA)
        self.assertIn("::warning::[t] no citation data", out)
        self.assertFalse(os.path.exists("results"))

    def test_fetch_serpapi_requires_key(self):
        code, _ = self.run_main(["fetch", "--source", "serpapi", "--out", "results"])
        self.assertEqual(code, gs.EXIT_ERROR)

    # resolve -----------------------------------------------------------
    def test_resolve_picks_freshest_and_warns_on_disagreement(self):
        write_json("collected/gs-data-a/gs_data.json", record(11, days_old=0.0, runner="a"))
        write_json("collected/gs-data-b/gs_data.json", record(10, days_old=0.01, runner="b"))
        write_json("collected/gs-data-c/gs_data.json", {"citedby": "bad"})
        code, out = self.resolve()
        self.assertEqual(code, gs.EXIT_OK)
        self.assertIn("publish=true", self.gh_out())
        self.assertIn("::warning::crawl results disagree on the citation count [10, 11]", out)
        self.assertEqual((self.published()["citedby"], self.published()["runner"]), (11, "a"))

    def test_resolve_keeps_fresh_previous(self):
        write_json("stats/gs_data.json", record(10, days_old=5))
        code, out = self.resolve()
        self.assertEqual(code, gs.EXIT_OK)
        self.assertIn("publish=false", self.gh_out())
        self.assertIn("::warning::", out)
        self.assertFalse(os.path.exists("results"))

    def test_resolve_stale_boundary(self):
        write_json("stats/gs_data.json", record(10, days_old=13.9))
        self.assertEqual(self.resolve()[0], gs.EXIT_OK)
        write_json("stats/gs_data.json", record(10, days_old=14.1))
        code, out = self.resolve()
        self.assertEqual(code, gs.EXIT_ERROR)
        self.assertIn("::error::Google Scholar data is stale", out)

    def test_resolve_without_anything_fails(self):
        code, out = self.resolve()
        self.assertEqual(code, gs.EXIT_ERROR)
        self.assertIn("::error::", out)

    def test_resolve_serpapi_fallback(self):
        with mock.patch.dict(os.environ, {"SERPAPI_KEY": "k"}), \
             mock.patch.object(gs, "http_get", return_value=(200, "u", json.dumps(SERPAPI_PAYLOAD))):
            code, _ = self.resolve()
        self.assertEqual(code, gs.EXIT_OK)
        self.assertIn("publish=true", self.gh_out())
        self.assertEqual((self.published()["citedby"], self.published()["runner"]), (21934, "serpapi"))

    def test_resolve_serpapi_failure_keeps_previous(self):
        write_json("stats/gs_data.json", record(10, days_old=1))
        with mock.patch.dict(os.environ, {"SERPAPI_KEY": "k"}), \
             mock.patch.object(gs, "http_get", return_value=(401, "u", json.dumps({"error": "Invalid API key."}))):
            code, out = self.resolve()
        self.assertEqual(code, gs.EXIT_OK)
        self.assertIn("::warning::SerpApi fallback failed", out)
        self.assertIn("publish=false", self.gh_out())

    def test_resolve_malformed_serpapi_keeps_previous(self):
        write_json("stats/gs_data.json", record(10, days_old=1))
        with mock.patch.dict(os.environ, {"SERPAPI_KEY": "k"}), \
             mock.patch.object(gs, "http_get", return_value=(200, "u", json.dumps({"cited_by": []}))):
            code, out = self.resolve()
        self.assertEqual(code, gs.EXIT_OK)
        self.assertIn("::warning::SerpApi fallback failed", out)
        self.assertIn("publish=false", self.gh_out())

    def test_resolve_prefers_crawl_result_over_serpapi(self):
        write_json("collected/gs-data-a/gs_data.json", record(11))
        with mock.patch.dict(os.environ, {"SERPAPI_KEY": "k"}), \
             mock.patch.object(gs, "http_get", side_effect=AssertionError("must not call SerpApi")):
            code, _ = self.resolve()
        self.assertEqual(code, gs.EXIT_OK)
        self.assertEqual(self.published()["citedby"], 11)


if __name__ == "__main__":
    unittest.main()
