#!/usr/bin/env python3
"""Fetch Google Scholar citation stats and write them to results/gs_data.json.

Run by .github/workflows/google-scholar-stats.yml on a daily schedule. Uses the
free `scholarly` library (no API key). If Scholar blocks the request or returns
no citation count, the script exits non-zero so the workflow fails and simply
retries on the next run — it never overwrites good data with an empty value.
"""

import json
import os
import sys
from datetime import datetime, timezone

from scholarly import scholarly

# Google Scholar profile id (from _config.yml / _data/authors.yml)
SCHOLAR_ID = os.environ.get("GOOGLE_SCHOLAR_ID", "RMoZ_8IAAAAJ")
OUT_DIR = "results"


def main() -> int:
    author = scholarly.search_author_id(SCHOLAR_ID)
    scholarly.fill(author, sections=["basics", "indices", "counts"])

    citedby = author.get("citedby")
    if citedby is None:
        print("ERROR: no 'citedby' returned (likely blocked by Scholar).", file=sys.stderr)
        return 1

    data = {
        "name": author.get("name"),
        "citedby": citedby,
        "citedby5y": author.get("citedby5y"),
        "hindex": author.get("hindex"),
        "hindex5y": author.get("hindex5y"),
        "i10index": author.get("i10index"),
        "i10index5y": author.get("i10index5y"),
        "cites_per_year": author.get("cites_per_year"),
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "gs_data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # shields.io-compatible endpoint blob (optional: enables a badge)
    shields = {
        "schemaVersion": 1,
        "label": "citations",
        "message": str(citedby),
        "color": "b0533a",
    }
    with open(os.path.join(OUT_DIR, "gs_data_shieldsio.json"), "w", encoding="utf-8") as f:
        json.dump(shields, f, ensure_ascii=False, indent=2)

    print(f"OK: {data['name']} — {citedby} citations (h-index {data['hindex']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
