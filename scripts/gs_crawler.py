#!/usr/bin/env python3
"""Google Scholar citation stats for the homepage sidebar.

Driven by .github/workflows/google-scholar-stats.yml. Standard library only, so
it runs on the stock python3 of every GitHub-hosted runner (Python >= 3.9).

Subcommands
  fetch    Fetch the profile stats and write <out>/gs_data.json (+ a shields.io
           endpoint blob). ``--source direct`` GETs the public profile page (no
           key needed, but Google Scholar blocks most datacenter IPs);
           ``--source serpapi`` uses SerpApi and needs SERPAPI_KEY.
  resolve  Pick the freshest valid result among the crawl artifacts, fall back
           to SerpApi when SERPAPI_KEY is set, and decide whether to publish.
           When nothing new is available the previous data is kept and the
           command succeeds, unless that data is older than --stale-days.

Exit codes: 0 ok, 1 unexpected error / stale data, 2 no data (blocked, etc.).
"""

from __future__ import annotations

import argparse
import gzip
import html
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

DEFAULT_SCHOLAR_ID = "RMoZ_8IAAAAJ"  # from _config.yml / _data/authors.yml
PROFILE_URL = "https://scholar.google.com/citations?user={id}&hl=en"
SERPAPI_URL = "https://serpapi.com/search.json"

DATA_FILE = "gs_data.json"
SHIELDS_FILE = "gs_data_shieldsio.json"

EXIT_OK, EXIT_ERROR, EXIT_NO_DATA = 0, 1, 2

# A plain browser-like request. Scholar decides mostly on IP reputation, but
# the consent cookies avoid the EU consent interstitial some runner regions get.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip",
    "Cookie": "CONSENT=YES+; SOCS=CAI",
}

CAPTCHA_MARKERS = (
    'id="gs_captcha_ccl"',
    'id="recaptcha"',
    'id="captcha-form"',
    "unusual traffic from your computer network",
)


class NoData(Exception):
    """Scholar (or SerpApi) did not give us a usable citation count."""


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def annotate(level: str, msg: str) -> None:
    """Emit a GitHub Actions annotation (harmless plain text elsewhere)."""
    print(f"::{level}::{msg}", flush=True)


def append_env_file(var: str, text: str) -> None:
    """Append to $GITHUB_OUTPUT / $GITHUB_STEP_SUMMARY when running in Actions."""
    path = os.environ.get(var)
    if not path:
        return
    with open(path, "a", encoding="utf-8") as f:
        f.write(text if text.endswith("\n") else text + "\n")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def http_get(url: str, headers: dict, timeout: float = 30.0) -> tuple[int, str, str]:
    """GET ``url`` following redirects. Returns (status, final_url, body)."""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status, final_url, raw = resp.status, resp.geturl(), resp.read()
            encoding = resp.headers.get("Content-Encoding", "")
            charset = resp.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as err:
        # err.fp is None when the error carries no body; then geturl()/read()
        # are unavailable too.
        has_body = err.fp is not None
        status = err.code
        final_url = err.geturl() if has_body else url
        raw = err.read() if has_body else b""
        encoding = err.headers.get("Content-Encoding", "") if err.headers else ""
        charset = (err.headers.get_content_charset() if err.headers else None) or "utf-8"
    if "gzip" in encoding.lower():
        raw = gzip.decompress(raw)
    return status, final_url, raw.decode(charset, errors="replace")


# --------------------------------------------------------------------------- #
# source: the public Google Scholar profile page
# --------------------------------------------------------------------------- #

def blocked_reason(status: int, final_url: str, body: str) -> str | None:
    if status in (403, 429, 503):
        return f"HTTP {status}"
    if "/sorry/" in final_url or "consent.google" in final_url:
        return f"redirected to {final_url.split('?')[0]}"
    lowered = body.lower()
    if any(marker in lowered for marker in CAPTCHA_MARKERS):
        return "captcha page"
    return None


def parse_profile(page: str) -> dict:
    """Extract the citation table, name and per-year counts from the profile HTML.

    Mirrors what the ``scholarly`` package parses: the six ``td.gsc_rsb_std``
    cells (citations / h-index / i10-index, all-time and recent), and the
    histogram bars whose ``z-index`` counts years from the right.
    """
    cells = re.findall(r'class="gsc_rsb_std"[^>]*>\s*([\d,]+)\s*<', page)
    if len(cells) < 6:
        raise NoData("profile page has no citation table (unexpected markup or interstitial)")
    citedby, citedby5y, hindex, hindex5y, i10index, i10index5y = (
        int(c.replace(",", "")) for c in cells[:6]
    )

    name = None
    m = re.search(r'id="gsc_prf_in"[^>]*>(.*?)</div>', page, flags=re.S)
    if m:
        name = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() or None

    years = [int(y) for y in re.findall(r'class="gsc_g_t"[^>]*>\s*(\d{4})\s*<', page)]
    counts = [0] * len(years)
    bar_re = re.compile(
        r'<a\b[^>]*\bclass="gsc_g_a"[^>]*>\s*<span class="gsc_g_al">\s*([\d,]+)\s*</span>'
    )
    for bar in bar_re.finditer(page):
        z = re.search(r"z-index:\s*(\d+)", bar.group(0))
        if not z:
            continue
        idx = int(z.group(1))
        if 1 <= idx <= len(years):
            counts[-idx] = int(bar.group(1).replace(",", ""))

    return {
        "name": name,
        "citedby": citedby,
        "citedby5y": citedby5y,
        "hindex": hindex,
        "hindex5y": hindex5y,
        "i10index": i10index,
        "i10index5y": i10index5y,
        "cites_per_year": dict(zip(years, counts)),
    }


def fetch_direct(scholar_id: str, attempts: int = 3, base_delay: float = 15.0) -> dict:
    url = PROFILE_URL.format(id=urllib.parse.quote(scholar_id, safe=""))
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            status, final_url, body = http_get(url, BROWSER_HEADERS)
            reason = blocked_reason(status, final_url, body)
            if reason:
                raise NoData(f"blocked by Google Scholar ({reason})")
            if status != 200:
                raise NoData(f"HTTP {status}")
            data = parse_profile(body)
            data["source"] = "scholar.google.com"
            return data
        except (NoData, urllib.error.URLError, OSError) as err:
            last_error = err
            log(f"direct fetch attempt {attempt}/{attempts} failed: {err}")
            if attempt < attempts:
                delay = base_delay * attempt + random.uniform(0, 5)
                log(f"retrying in {delay:.0f}s")
                time.sleep(delay)
    raise NoData(str(last_error))


# --------------------------------------------------------------------------- #
# source: SerpApi (https://serpapi.com/google-scholar-author-api)
# --------------------------------------------------------------------------- #

def _table_pair(entry: object) -> tuple[int, int | None]:
    """``{"citations": {"all": 10, "since_2021": 8}}`` -> (10, 8).

    Keys are localized by SerpApi and the "since_YYYY" key moves every year, so
    only positions are trusted.
    """
    if not isinstance(entry, dict) or not entry:
        raise NoData("SerpApi cited_by.table entry has an unexpected shape")
    values = next(iter(entry.values()))
    if not isinstance(values, dict) or "all" not in values:
        raise NoData("SerpApi cited_by.table entry has no 'all' value")
    total = int(str(values["all"]).replace(",", ""))
    recent = next(
        (int(str(v).replace(",", "")) for k, v in values.items() if k != "all"),
        None,
    )
    return total, recent


def parse_serpapi(payload: dict) -> dict:
    if payload.get("error"):
        raise NoData(f"SerpApi error: {payload['error']}")
    cited_by = payload.get("cited_by")
    if not isinstance(cited_by, dict):
        raise NoData("SerpApi response has no cited_by object")
    table = cited_by.get("table")
    if not isinstance(table, list) or len(table) < 3:
        raise NoData("SerpApi response has no cited_by.table")
    citedby, citedby5y = _table_pair(table[0])
    hindex, hindex5y = _table_pair(table[1])
    i10index, i10index5y = _table_pair(table[2])

    cites_per_year = {}
    graph = cited_by.get("graph")
    for point in graph if isinstance(graph, list) else []:
        try:
            cites_per_year[int(point["year"])] = int(str(point.get("citations", 0)).replace(",", ""))
        except (AttributeError, KeyError, TypeError, ValueError):
            continue

    author = payload.get("author")
    return {
        "name": author.get("name") if isinstance(author, dict) else None,
        "citedby": citedby,
        "citedby5y": citedby5y,
        "hindex": hindex,
        "hindex5y": hindex5y,
        "i10index": i10index,
        "i10index5y": i10index5y,
        "cites_per_year": cites_per_year,
        "source": "serpapi.com",
    }


def fetch_serpapi(scholar_id: str, api_key: str) -> dict:
    query = urllib.parse.urlencode(
        {"engine": "google_scholar_author", "author_id": scholar_id, "hl": "en", "api_key": api_key}
    )
    # Never log the URL: it carries the API key.
    try:
        status, _, body = http_get(f"{SERPAPI_URL}?{query}", {"Accept": "application/json"}, timeout=60)
    except (urllib.error.URLError, OSError) as err:
        raise NoData(f"SerpApi request failed: {err}") from err
    try:
        payload = json.loads(body)
    except ValueError as err:
        raise NoData(f"SerpApi returned non-JSON (HTTP {status})") from err
    if not isinstance(payload, dict):
        raise NoData("SerpApi returned an unexpected JSON shape")
    if status != 200 and not payload.get("error"):
        raise NoData(f"SerpApi HTTP {status}")
    try:
        return parse_serpapi(payload)
    except (AttributeError, KeyError, TypeError, ValueError) as err:
        # Any schema anomaly is "no data", never a crash of the publish job.
        raise NoData(f"SerpApi response could not be parsed: {err!r}") from err


# --------------------------------------------------------------------------- #
# records on disk
# --------------------------------------------------------------------------- #

def finish_record(stats: dict, label: str) -> dict:
    record = dict(stats)
    record["runner"] = label
    record["updated"] = now_utc().isoformat(timespec="seconds")
    return record


def write_outputs(out_dir: str, record: dict) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, DATA_FILE), "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
        f.write("\n")
    shields = {
        "schemaVersion": 1,
        "label": "citations",
        "message": str(record["citedby"]),
        "color": "b0533a",
    }
    with open(os.path.join(out_dir, SHIELDS_FILE), "w", encoding="utf-8") as f:
        json.dump(shields, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_record(path: str) -> dict | None:
    """Read a gs_data.json; None when missing, unreadable or without a valid count."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    citedby = data.get("citedby")
    if isinstance(citedby, bool) or not isinstance(citedby, int) or citedby < 0:
        return None
    if parse_timestamp(data.get("updated")) is None:
        return None
    return data


def describe(record: dict) -> str:
    return (
        f"{record.get('citedby')} citations, h-index {record.get('hindex')} "
        f"(source {record.get('source', '?')}, runner {record.get('runner', '?')}, "
        f"updated {str(record.get('updated', ''))[:19]})"
    )


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #

def cmd_fetch(args: argparse.Namespace) -> int:
    try:
        if args.source == "serpapi":
            key = os.environ.get("SERPAPI_KEY", "").strip()
            if not key:
                log("ERROR: --source serpapi needs the SERPAPI_KEY environment variable")
                return EXIT_ERROR
            stats = fetch_serpapi(args.scholar_id, key)
        else:
            stats = fetch_direct(args.scholar_id, attempts=args.attempts)
    except NoData as err:
        annotate("warning", f"[{args.label}] no citation data: {err}")
        append_env_file("GITHUB_STEP_SUMMARY", f"- ⚠️ `{args.label}`: {err}")
        return EXIT_NO_DATA

    record = finish_record(stats, args.label)
    write_outputs(args.out, record)
    log(f"OK: {describe(record)}")
    append_env_file(
        "GITHUB_STEP_SUMMARY",
        f"- ✅ `{args.label}`: {record['citedby']} citations via {record['source']}",
    )
    return EXIT_OK


def collect_candidates(root: str) -> list[tuple[str, dict]]:
    found = []
    if not os.path.isdir(root):
        return found
    for dirpath, _, filenames in os.walk(root):
        if DATA_FILE in filenames:
            path = os.path.join(dirpath, DATA_FILE)
            record = load_record(path)
            if record is None:
                log(f"ignoring invalid {path}")
                continue
            found.append((path, record))
    found.sort(key=lambda item: parse_timestamp(item[1]["updated"]), reverse=True)
    return found


def cmd_resolve(args: argparse.Namespace) -> int:
    candidates = collect_candidates(args.collected)
    for path, record in candidates:
        log(f"candidate {path}: {describe(record)}")

    chosen: dict | None = candidates[0][1] if candidates else None
    counts = sorted({record["citedby"] for _, record in candidates})
    if len(counts) > 1:
        annotate(
            "warning",
            f"crawl results disagree on the citation count {counts}; "
            f"publishing the freshest one ({chosen['citedby']}).",
        )

    if chosen is None:
        key = os.environ.get("SERPAPI_KEY", "").strip()
        if key:
            log("no crawl result; trying SerpApi")
            try:
                chosen = finish_record(fetch_serpapi(args.scholar_id, key), "serpapi")
            except NoData as err:
                annotate("warning", f"SerpApi fallback failed: {err}")
                append_env_file("GITHUB_STEP_SUMMARY", f"- ⚠️ SerpApi fallback: {err}")
        else:
            log("no crawl result and SERPAPI_KEY is not set; skipping SerpApi fallback")

    if chosen is not None:
        write_outputs(args.out, chosen)
        append_env_file("GITHUB_OUTPUT", "publish=true")
        append_env_file(
            "GITHUB_STEP_SUMMARY",
            f"\n**Publishing:** {chosen['citedby']} citations "
            f"(h-index {chosen.get('hindex')}), source `{chosen.get('source')}` "
            f"via `{chosen.get('runner')}`.",
        )
        log(f"publishing: {describe(chosen)}")
        return EXIT_OK

    append_env_file("GITHUB_OUTPUT", "publish=false")
    previous = load_record(args.previous)
    if previous is None:
        annotate("error", "No citation data could be fetched and there is no previous data to keep.")
        return EXIT_ERROR

    age_days = (now_utc() - parse_timestamp(previous["updated"])).total_seconds() / 86400
    kept = f"kept previous data: {describe(previous)}, {age_days:.1f} days old"
    if age_days <= args.stale_days:
        annotate("warning", f"Google Scholar blocked every crawl; {kept}.")
        append_env_file("GITHUB_STEP_SUMMARY", f"\n**Not publishing** — {kept}.")
        return EXIT_OK

    annotate(
        "error",
        f"Google Scholar data is stale: {kept}, above the {args.stale_days}-day limit. "
        "Consider adding a SERPAPI_KEY repository secret.",
    )
    append_env_file("GITHUB_STEP_SUMMARY", f"\n**Stale data** — {kept}.")
    return EXIT_ERROR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--scholar-id",
        default=os.environ.get("GOOGLE_SCHOLAR_ID", DEFAULT_SCHOLAR_ID),
        help="Google Scholar profile id (env GOOGLE_SCHOLAR_ID)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="fetch the stats and write gs_data.json")
    fetch.add_argument("--source", choices=("direct", "serpapi"), default="direct")
    fetch.add_argument("--out", default="results", help="output directory")
    fetch.add_argument("--label", default="local", help="runner label recorded in the output")
    fetch.add_argument("--attempts", type=int, default=3, help="direct-fetch attempts")
    fetch.set_defaults(func=cmd_fetch)

    resolve = sub.add_parser("resolve", help="choose the result to publish")
    resolve.add_argument("--collected", default="collected", help="directory with crawl artifacts")
    resolve.add_argument("--previous", default="stats/gs_data.json", help="currently published gs_data.json")
    resolve.add_argument("--out", default="results", help="output directory")
    resolve.add_argument("--stale-days", type=float, default=14, help="fail once the kept data is older than this")
    resolve.set_defaults(func=cmd_resolve)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
