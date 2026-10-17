# TrialMirror v0.4 — Missing Data & Peer Explorer Update

Changes from v0.3:
- Missing registry fields (including absent/empty location arrays) show **No data**, not a misleading zero.
- Missing study values do not receive percentiles. Peer medians are computed from available peer data only.
- All eligible matched peer records are displayed in the dashboard with study title, NCT link (live mode), sponsor, phase, year, outcomes and sites.
- The review export includes the eligible peer IDs and corresponding metadata.
- Small-cohort warning remains; live retrieval still uses a capped candidate pool (up to 500 by default) and therefore is exploratory rather than exhaustive.
- Missing data are distinguished from genuine numeric zeros when a field is explicitly supplied.

## Windows: update an existing installation
1. Close the existing server terminal (Ctrl+C).
2. Download and **Extract All** of the new ZIP (do not run from within ZIP).
3. Open the new TrialMirror-Beta folder and double-click `start.bat`.
4. Open http://127.0.0.1:8000 and press Ctrl+Shift+R to clear cached browser assets.
5. Select Live ClinicalTrials.gov, enter `NCT01866319`, click Analyze trial and scroll to **Eligible peer studies and traceability**.

## Tests
Run `.venv\Scripts\python.exe -m pytest -q` in the extracted folder.

# TrialMirror Beta — HackHarvard × Regeneron challenge

A functioning local prototype for the **“How Extra Is Your Trial?”** clinical trial complexity challenge. Run peer-adjusted comparisons of trial design dimensions, inspect transparent evidence, and explore synthetic sponsor trend analytics.

## Windows (recommended)

1. Install **Python 3.10+** from python.org and enable **Add Python to PATH**.
2. Extract `TrialMirror-Beta.zip`.
3. Double-click **`start.bat`**. The first run creates `.venv` and installs dependencies (internet needed to install packages).
4. Navigate to **http://127.0.0.1:8000** if the browser does not open automatically.
5. Select **Offline demo**, choose a synthetic study, then click **Analyze trial**. Visit **Sponsor trends** for synthetic three-year normalized outcome-measure trends.
6. Select **Live ClinicalTrials.gov** and enter a real NCT ID to fetch registered study data and benchmark against a limited candidate sample. Internet is required for live mode. Use the database search at https://clinicaltrials.gov to find an NCT ID.
7. To stop, focus the terminal window and press **Ctrl+C**.

**Port taken?** Stop another app using port 8000 or start manually with `python -m uvicorn main:app --port 8001` (inside the activated virtualenv) and open http://127.0.0.1:8001.

## macOS / Linux

```bash
cd TrialMirror-Beta
bash start.sh
# open http://127.0.0.1:8000
```

## Run tests

Windows:
```powershell
.venv\Scripts\python.exe -m pytest -q
```
macOS / Linux:
```bash
.venv/bin/python -m pytest -q
```

## Architecture

- `main.py`: FastAPI REST API + static server, live ClinicalTrials.gov API requests, bounded study candidate retrieval.
- `engine.py`: registry parsing, eligibility criteria approximations, strict peer matching, midrank percentile comparisons, sponsor ratio trends.
- `demo_data.py`: deterministic and clearly labeled synthetic studies for offline UI testing.
- `static/index.html`: responsive zero-build HTML/CSS/JS UI; optional Chart.js loaded via CDN for sponsor line chart.
- `tests/test_engine.py`: five automated core-engine tests.

## API routes

- `/api/health`
- `/api/demo/studies`, `/api/demo/benchmark/{DEMO-ID}`, `/api/demo/trends?sponsor=...`
- `/api/live/study/{NCT-ID}`, `/api/live/benchmark/{NCT-ID}`
- `/docs` — interactive OpenAPI documentation.

## Key caveats

**This is a beta, not a validated clinical decision-support system.** Synthetic company name labels do **not** represent real sponsor performance. Live API benchmarks are limited to a maximum of 250 condition-query candidates sampled from the registry, then restricted to study type, phase, exact condition, and ±6-year start date. A low number of peers (especially oncology conditions with varying terminology) can make percentile comparisons unstable; no silent fallback to synthetic data occurs.

A registered outcome measure is not synonymous with a scientific endpoint. Eligibility counts are approximate; protocols differ substantially in structure. Number of registered locations or countries is not necessarily an indicator of unnecessary trial complexity. No cost savings, adverse outcomes, or shortened recruitment times are claimed.

For a production-quality study: collect a complete cached registry export, normalize disease categories (e.g. MeSH or condition taxonomies), validate extraction against manual labels, define peer matching criteria with clinical experts, address study versions, and add calibrated cost/burden models with uncertainty.

## Further improvements before submission

1. Load a complete, frozen, real-condition cohort rather than capped live API pages.
2. Add study-date and study-design peer-filter controls.
3. Implement real sponsor-adjusted trends with verified matched cohorts.
4. Collect validation examples and screenshot a reproducible real-data analysis for the pitch deck.
5. Add server-side export to PDF after methodology review.

Data source: https://clinicaltrials.gov/data-api/api. This independent prototype is not affiliated with Regeneron or the NIH.

## v0.3 Design Studio addition

The `Design optimizer` sidebar tab now provides a parameterized scenario engine (`POST /api/optimizer/run`), hard locking for visit and site counts, a nondominated scenario frontier, cost/duration/visit calculations and visible model assumptions. It does not optimize clinical outcomes or decide which assessments can be removed. 

For live studies, the app displays a direct original-record hyperlink and `GET /api/live/verify/{NCT_ID}` checks registry ID equality. The registry endpoint must be accessible from the user's network; it has not been end-to-end validated in this sandbox. Live peer analysis uses a *capped 500-candidate* sample, not all registry studies; outputs are exploratory. Offline demo values are synthetic.

Open `RUN-WINDOWS.txt` for click-by-click instructions.
