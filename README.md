# DC Water Attribution Audit

Credibility-first data engineering and analytics project for estimating workload-level
data center water usage (WUE) from public evidence only.

## Core policy

- No fabricated facility, permit, or disclosure data.
- If a value is unsourced, it stays null and is surfaced as "no public data".
- Every data row must include `source_url`.
- Derived estimates always include confidence, sample size (`N`), assumptions used, and sources.

## Repository layout

```
data/raw/                  # manually collected PDFs, permit exports, screenshots
data/staging/              # cleaned CSVs before dbt
db/                        # postgres schema/migrations
dbt/                       # dbt staging + marts models
etl/                       # ingestion and validation scripts
model/                     # workload water attribution logic
api/                       # fastapi endpoints
dashboard/                 # streamlit app
docs/                      # methodology + writeup summaries
tests/                     # unit tests
```

## Local setup

1. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
2. Start Postgres:
   ```bash
   docker compose up -d postgres
   ```
3. Place disclosure PDFs in:
   - `data/raw/disclosures/`
   - and map each file to a public URL in `data/raw/disclosures/source_index.csv`
4. Fill target regions in `data/staging/target_regions.csv` with public-source links.

## ETL commands

```bash
python3 etl/extract_pdf_disclosures.py
python3 etl/fetch_noaa_climate.py --start-year 2021 --end-year 2025
python3 etl/validate_sources.py
```

## dbt

Copy `dbt/profiles.example.yml` into your local dbt profiles location, then:

```bash
cd dbt
dbt run
dbt test
```

## API

```bash
uvicorn api.main:app --reload
```

- `POST /estimate` with `{ region, hardware_type, gpu_hours, month, facility_id? }`
- `GET /facilities`

## Dashboard

```bash
streamlit run dashboard/app.py
```

## Tests

```bash
pytest
```