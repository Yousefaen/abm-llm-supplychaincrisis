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
import ssl
import sys
import time
import urllib.error
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
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except urllib.error.URLError as e:
        # Some IR sites (e.g. annualreport2019.volkswagenag.com) serve cert
        # chains that don't validate against Windows Python's bundled CA
        # store.  Fall back to an unverified context for those hosts only —
        # the data we're fetching is public, so the integrity tradeoff is
        # acceptable for prototype-stage research.
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            print(f"  [warn] cert verification failed for {url[:80]}, retrying unverified")
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
                return r.read()
        raise


def get_filing_url(
    cik: int, form: str, fiscal_year: int | None = None
) -> tuple[str, str, str, str]:
    """Resolve a filing for the given CIK / form.  If ``fiscal_year`` is set,
    return the filing whose period_of_report falls in that calendar year
    (i.e. fiscal year ending in that year — for a 2019 10-K, period_of_report
    is typically 2019-12-31, filed early 2020).  Otherwise return the most
    recent filing of that form.

    Returns ``(url, accession_number, filing_date, report_date)``.

    Note: only searches the ``filings.recent`` slice (~last 1000 filings),
    which covers ~5-10 years for an active filer.  Older filings would
    require fetching the additional shards in ``filings.files[]`` — not
    needed for our 2019-2025 window.
    """
    idx_url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    idx = json.loads(_request(idx_url))
    rec = idx["filings"]["recent"]
    forms = rec["form"]
    accs = rec["accessionNumber"]
    docs = rec["primaryDocument"]
    f_dates = rec["filingDate"]
    r_dates = rec.get("reportDate", [""] * len(forms))

    for f, acc, doc, fdate, rdate in zip(forms, accs, docs, f_dates, r_dates):
        if f != form:
            continue
        if fiscal_year is not None and not (rdate or "").startswith(str(fiscal_year)):
            continue
        acc_no_dashes = acc.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_dashes}/{doc}"
        return url, acc, fdate, rdate

    fy_msg = f" (fiscal year {fiscal_year})" if fiscal_year else ""
    raise RuntimeError(f"No {form} filing found for CIK {cik}{fy_msg}")


# Backward-compatible alias for the latest-only call site.
def get_latest_filing_url(cik: int, form: str) -> tuple[str, str, str]:
    url, acc, fdate, _ = get_filing_url(cik, form)
    return url, acc, fdate


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


# ---------------------------------------------------------------------------
# IR-website PDF fetch (for non-SEC filers — Samsung, Infineon, Continental,
# Bosch, VW). EDGAR's submissions API is replaced with a direct PDF URL,
# downloaded and text-extracted via pypdf.  The extracted text is then
# consumed by persona_builder identically to the EDGAR text path, so
# downstream code doesn't care which source the text came from.
# ---------------------------------------------------------------------------
def _download_pdf(url: str, dest: Path) -> int:
    """Download a PDF to ``dest``. Returns size in bytes."""
    raw = _request(url)
    dest.write_bytes(raw)
    return len(raw)


def pdf_to_text(pdf_path: Path) -> str:
    """Extract plain text from every page of a PDF.

    Uses pypdf.  Pages are joined with double-newlines so paragraph and
    section boundaries survive into the trim regex.  Most annual reports
    extract reasonably cleanly — the heavy formatting / image content gets
    dropped, which is fine for persona generation since we only need the
    narrative strategy/risk/operations sections.
    """
    from pypdf import PdfReader  # imported here so EDGAR-only usage doesn't pay the cost

    reader = PdfReader(str(pdf_path))
    parts: list[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t.strip():
            parts.append(t)
    return "\n\n".join(parts)


def fetch_ir_filing(agent_id: str, url: str, fiscal_year: int) -> Path:
    """Fetch a non-SEC company's annual report PDF and cache its extracted
    text alongside the EDGAR-style cache layout.  Idempotent.

    Returns the path to the extracted .txt file (NOT the .pdf), so the
    downstream persona builder consumes the same shape from both
    sources.
    """
    out_dir = CACHE_DIR / agent_id
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"ir_{fiscal_year}.pdf"
    txt_path = out_dir / f"ir_{fiscal_year}.txt"

    if txt_path.exists():
        rel = txt_path.relative_to(Path(__file__).parent)
        print(f"  [{agent_id}] cached -> {rel} ({txt_path.stat().st_size//1024}KB)")
        return txt_path

    if not pdf_path.exists():
        print(f"  [{agent_id}] downloading IR PDF FY{fiscal_year} from {url[:80]}...")
        time.sleep(0.15)
        size = _download_pdf(url, pdf_path)
        print(f"  [{agent_id}] saved {size//1024}KB PDF")

    print(f"  [{agent_id}] extracting text from PDF...")
    text = pdf_to_text(pdf_path)
    txt_path.write_text(text, encoding="utf-8")
    print(f"  [{agent_id}] saved {len(text)//1024}KB plain text")
    return txt_path


def fetch_filing(
    agent_id: str, cik: int, form: str, fiscal_year: int | None = None
) -> Path:
    """Resolve, fetch, and cache a filing for this agent.

    With ``fiscal_year``, fetches the 10-K/20-F covering that fiscal year
    (intended for pre-crisis baseline personas — 2019 captures pre-COVID
    posture without leaking crisis-era observations into agent prompts).

    Cache is partitioned by year so 2019 and latest can coexist.
    Returns the path to the cached plain-text file.
    """
    out_dir = CACHE_DIR / agent_id
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"_{fiscal_year}" if fiscal_year is not None else ""
    out_file = out_dir / f"{form.lower().replace('-', '_')}{suffix}.txt"
    if out_file.exists():
        rel = out_file.relative_to(Path(__file__).parent)
        print(f"  [{agent_id}] cached -> {rel} ({out_file.stat().st_size//1024}KB)")
        return out_file

    fy_label = f" FY{fiscal_year}" if fiscal_year else " (latest)"
    print(f"  [{agent_id}] resolving CIK {cik} {form}{fy_label}...")
    url, acc, fdate, rdate = get_filing_url(cik, form, fiscal_year)
    print(f"  [{agent_id}] downloading {acc} (filed {fdate}, period {rdate}) ...")
    time.sleep(0.15)
    raw = _request(url)
    text = html_to_text(raw)
    out_file.write_text(text, encoding="utf-8")
    print(f"  [{agent_id}] saved {len(text)//1024}KB plain text")
    return out_file


if __name__ == "__main__":
    # CLI:
    #   python fetch_filings.py                  -> all sources, latest filing
    #   python fetch_filings.py TaiwanSemi       -> one source, latest filing
    #   python fetch_filings.py --fy 2019        -> all sources, FY2019 filing
    #   python fetch_filings.py FordAuto --fy 2019
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from persona_sources import EDGAR_SOURCES

    args = list(sys.argv[1:])
    fiscal_year: int | None = None
    if "--fy" in args:
        i = args.index("--fy")
        fiscal_year = int(args.pop(i + 1))
        args.pop(i)
    targets = args or list(EDGAR_SOURCES)
    for aid in targets:
        if aid not in EDGAR_SOURCES:
            print(f"  [{aid}] no EDGAR source wired up; skipping")
            continue
        src = EDGAR_SOURCES[aid]
        fetch_filing(aid, src["cik"], src["form"], fiscal_year)
