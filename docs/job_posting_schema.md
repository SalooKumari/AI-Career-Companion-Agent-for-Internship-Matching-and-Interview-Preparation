# Job Posting Schema (Milestone 2, M2.1)

Every posting in `database/job_postings.json` — and every row in the
`job_postings` table — follows this schema:

| Field | Type | Notes |
|---|---|---|
| `job_id` | string | Stable unique identifier, e.g. `JOB0001` |
| `title` | string | Role title, e.g. "Software Engineering Intern" |
| `company` | string | Company name (synthetic in this dataset — see note below) |
| `location` | string | City + country, or "Remote (India)" |
| `domain` | string | Broad category used for evaluation/grouping, e.g. "Data Science & Analytics" |
| `job_description` | string | Free-text overview of the role |
| `responsibilities` | array[string] | Day-to-day responsibilities |
| `required_skills` | array[string] | Must-have skills |
| `preferred_skills` | array[string] | Nice-to-have skills |
| `qualifications` | array[string] | Other qualifying criteria (attitude, project experience, etc.) |
| `experience_requirement` | string | Free-text experience expectation |
| `education_requirement` | string | Free-text education expectation (degree + field) |
| `duration` | string | Internship duration, e.g. "3 months" |
| `stipend_inr_per_month` | integer | Monthly stipend in INR |
| `application_url` | string, nullable | Link to the real external posting — when set, the "Apply" button opens it in a new tab so the student can genuinely apply, not just track internally. Null for the synthetic dataset. |
| `source` | string | `"synthetic"` (generated), `"kaggle_import"` (static dataset), or `"adzuna_live"` (live API pull) — the frontend shows a "Real posting ✓" badge for the latter two. |

## Current dataset in use

`database/job_postings.json` currently holds **381 postings, 333 of them
real** — built from a Kaggle Naukri jobs dataset (`kuchhbhi/latest-30k-jobs-data`),
filtered down to genuine internship-titled and fresher/entry-level (0-1 yr
experience) roles, deduplicated, and capped per domain. Real title,
company, location, job description, required skills, and experience
requirement are taken exactly as scraped. The remaining 48 are synthetic
top-ups (`source: "synthetic"`) added only for domains the source dataset
covers thinly (Mechanical, Electrical, Civil, Biotech, Cybersecurity,
Content & Writing), so every domain has at least 12 postings for retrieval
and matching to work with. This is one snapshot, not a live feed — see
"Getting real, live postings" below for a genuinely current alternative,
or "Importing a static dataset" to swap in a different one.

## Why a synthetic dataset (background)

The 180 postings in `job_postings.json` are generated from domain templates
(`database/generate_job_postings.py`) rather than scraped from real job
boards. This keeps the dataset:
- **Free of copyright/ToS issues** — no scraped listing text is reused.
- **Reproducible** — fixed random seed, anyone can regenerate the exact same
  180 postings.
- **Clean by construction** — no duplicates, no missing fields, no irrelevant
  postings, since M2.1 explicitly asks for the dataset to be cleaned of
  those. A generation script sidesteps the cleaning step by not introducing
  the mess in the first place, while still producing realistic, varied
  postings across 19 domains (Software, Data Science, ML/AI, Embedded/IoT,
  Mechanical, Electrical, Cloud/DevOps, Cybersecurity, Product, Design,
  Marketing, Finance, HR, Operations, Biotech, Civil, Content, Sales, and
  more).

If you'd rather use real scraped postings later, drop a differently-shaped
JSON/CSV into `database/` and adjust `backend/seed_job_postings.py`'s field
mapping — the rest of the pipeline (chunking, embedding, matching) doesn't
care where the data came from, only that it matches this schema.

## Getting real, live postings (Adzuna API)

`database/fetch_adzuna_internships.py` pulls genuinely current postings
from Adzuna's job-search API (India), across the same 19 domains, with a
real application link per posting — unlike a Kaggle dataset, this reflects
whatever is actually live right now, not a static snapshot from whenever
someone uploaded it.

```bash
# one-time: register free at https://developer.adzuna.com/signup,
# add ADZUNA_APP_ID and ADZUNA_APP_KEY to backend/.env

cd database
python fetch_adzuna_internships.py --enrich   # --enrich fills missing skills/qualifications via LLM
cd ../backend
python seed_job_postings.py
python build_knowledge_base.py
```

Title, company, location, the application URL, and salary (when Adzuna
provides one) are taken exactly as returned by the API. Postings get
`source: "adzuna_live"` and the same "Real posting ✓" badge + real Apply
link as a Kaggle import. See the docstring at the top of that script for
full details (rate limits, pagination, `--append` to combine with existing
data).

## Importing a static dataset (e.g. from Kaggle)

`database/import_kaggle_dataset.py` converts a downloaded Kaggle CSV into
this exact schema, so it drops straight into the same pipeline as the
synthetic postings. See the docstring at the top of that file for the full
usage — short version:

```bash
cd database
python import_kaggle_dataset.py --inspect path/to/downloaded.csv   # see its real column names
# edit COLUMN_MAP in the script to match, then:
python import_kaggle_dataset.py path/to/downloaded.csv --enrich    # --enrich fills missing detail via LLM
cd ../backend
python seed_job_postings.py
python build_knowledge_base.py
```

`title`, `company`, `location`, `duration`, `stipend_inr_per_month`, and
`application_url` are taken exactly as scraped — never edited or invented.
`--enrich` only fills fields your CSV doesn't have (description, skills,
qualifications), grounded in the real title/company, and only when they're
genuinely missing. Rows without a real title and company are skipped rather
than guessed. Imported postings get `source: "kaggle_import"` and show a
"Real posting ✓" badge in the UI; when `application_url` is present, the
student's "Apply" button opens that real link in a new tab in addition to
recording the application internally.

**Domain classification (important for a diverse dataset):** if your CSV
has no domain/category column, each posting's domain is guessed from
keywords in its real title (e.g. "Marketing Intern" → Marketing, "HR
Intern" → Human Resources) — this runs automatically, even without
`--enrich`, specifically so a diverse dataset (marketing, HR, finance,
mechanical, civil, etc., not just software roles) doesn't silently collapse
into a single default domain. `--enrich` replaces the keyword guess with a
more accurate LLM classification, constrained to the same 19 domains used
everywhere else in the project. The script prints a domain breakdown after
every run so you can see the mix at a glance.

## Where this data lives at runtime

1. `database/job_postings.json` — the source-of-truth dataset file (versioned in git).
2. `job_postings` table in PostgreSQL — loaded from the JSON via `backend/seed_job_postings.py`. This is the "structured format" storage required by M2.1.
3. A local vector index (`backend/vector_store/`) — built from chunks of these postings by `backend/build_knowledge_base.py`, used for semantic retrieval (M2.2).
