# External validation data

Public time-series the eval pipeline correlates against. Not bundled in
the repo — drop the file at the path indicated and the harness will pick
it up.

## NY Fed Global Supply Chain Pressure Index (GSCPI)

**File expected at:** `backend/data/fred_gscpi.csv`

**Where to download:**
1. Go to https://fred.stlouisfed.org/series/GSCPI
2. Click _Download_ → choose CSV
3. Save the file as `fred_gscpi.csv` in this directory

The file is a small monthly time series (~250 rows for the 1997-present
window). FRED-format CSV with `DATE,GSCPI` columns. The harness picks
up `observation_date,GSCPI` or `DATE,VALUE` variants automatically.

**Why we don't fetch it programmatically:** `fred.stlouisfed.org` times
out / connection-resets when hit from `urllib` on at least some networks
(likely UA-based bot mitigation). One-click manual download is more
reliable than a brittle live-fetch path.

**Used by:** `backend/_eval_pmi.py` for the GSCPI ↔ sim-stress
correlation report.
