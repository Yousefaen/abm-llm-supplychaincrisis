"""Fetch the most recent 10-K / 20-F filing from SEC EDGAR for a sim agent.

EDGAR rules we comply with:
- Custom User-Agent including a contact email is REQUIRED. EDGAR rejects
  anonymous or generic UAs with a 403.
- Rate limit is 10 req/sec; we sleep 150ms between calls.
- Submissions index lives at data.sec.gov/submissions/CIK{cik:010d}.json
- Filing documents live at
  www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{primary_document}

Strips HTML to plain text with a regex pass — good enough for EDGAR's
relatively clean inline-XBRL HTML.  We do not parse XBRL.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

# EDGAR's policy page asks that the User-Agent include a name and a contact
# email.  This is the same operator behind the project's git history.
USER_AGENT = "ABM-LLM-Agents-Research yousef.aboelnour@gmail.com"

CACHE_DIR = Path(__file__).parent / "personas_cache" / "docs"


def _request(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def get_latest_filing_url(cik: int, form: str) -> tuple[str, str, str]:
    """Return (filing_url, accession_number, filing_date) for the most recent
    filing of ``form`` (e.g. "10-K" or "20-F") for the given CIK."""
    idx_url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    idx = json.loads(_request(idx_url))
    rec = idx["filings"]["recent"]
    forms = rec["form"]
    accs = rec["accessionNumber"]
    docs = rec["primaryDocument"]
    dates = rec["filingDate"]
    for f, acc, doc, date in zip(forms, accs, docs, dates):
        if f == form:
            acc_no_dashes = acc.replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_dashes}/{doc}"
            return url, acc, date
    raise RuntimeError(f"No {form} filing found for CIK {cik}")


# Strip script/style blocks first (their content is irrelevant), then any tag.
_BLOCK = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def html_to_text(html: bytes) -> str:
    text = html.decode("utf-8", errors="replace")
    text = _BLOCK.sub(" ", text)
    text = _TAG.sub(" ", text)
    text = _WS.sub(" ", text)
    return text.strip()


def fetch_filing(agent_id: str, cik: int, form: str) -> Path:
    """Resolve, fetch, and cache the latest filing for this agent.  Returns
    the path to the cached plain-text file. Idempotent — re-runs are no-ops
    once the cache file exists."""
    out_dir = CACHE_DIR / agent_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{form.lower().replace('-', '_')}.txt"
    if out_file.exists():
        print(f"  [{agent_id}] cached -> {out_file.relative_to(Path(__file__).parent)} ({out_file.stat().st_size//1024}KB)")
        return out_file

    print(f"  [{agent_id}] resolving CIK {cik} {form}...")
    url, acc, date = get_latest_filing_url(cik, form)
    print(f"  [{agent_id}] downloading {acc} ({date}) ...")
    time.sleep(0.15)
    raw = _request(url)
    text = html_to_text(raw)
    out_file.write_text(text, encoding="utf-8")
    print(f"  [{agent_id}] saved {len(text)//1024}KB plain text")
    return out_file


if __name__ == "__main__":
    # CLI: python fetch_filings.py            -> fetch all wired sources
    #      python fetch_filings.py TaiwanSemi -> fetch one
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from persona_sources import EDGAR_SOURCES

    targets = sys.argv[1:] or list(EDGAR_SOURCES)
    for aid in targets:
        if aid not in EDGAR_SOURCES:
            print(f"  [{aid}] no EDGAR source wired up; skipping")
            continue
        src = EDGAR_SOURCES[aid]
        fetch_filing(aid, src["cik"], src["form"])
