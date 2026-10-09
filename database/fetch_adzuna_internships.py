"""
Fetches REAL, live internship/job postings from the Adzuna API (India) and
writes them into database/job_postings.json in the same schema the rest of
the pipeline (seed_job_postings.py -> build_knowledge_base.py) expects.

Unlike the Kaggle import, this is genuinely live data -- every run pulls
whatever is currently posted on Adzuna right now, across the same 19
domains used throughout this project (so results aren't just software/CS
roles -- one search per domain, using that domain's representative title
from database/generate_job_postings.py).

------------------------------------------------------------------------
SETUP (one-time, free, ~2 minutes, no credit card):

    1. Register at https://developer.adzuna.com/signup
       You get an app_id + app_key instantly.
    2. Add both to backend/.env:
         ADZUNA_APP_ID=your-app-id
         ADZUNA_APP_KEY=your-app-key

USAGE:

    python fetch_adzuna_internships.py                # 1 page per domain (~20 results x 19 domains)
    python fetch_adzuna_internships.py --pages 2       # more results per domain
    python fetch_adzuna_internships.py --enrich        # fill missing skills/qualifications via LLM
    python fetch_adzuna_internships.py --append        # add to the existing dataset instead of replacing it
------------------------------------------------------------------------

Company, title, location, the application URL, and salary (when Adzuna
provides one) are taken exactly as returned by the API -- never edited or
invented. Postings get source: "adzuna_live", and show a "Real posting ✓"
badge in the UI, same as Kaggle imports. Adzuna's free tier allows a few
hundred calls/day, which comfortably covers one run across all 19 domains
(19-38 calls for --pages 1 or 2).

After running, seed the database and rebuild the knowledge base as usual:
    cd ../backend
    python seed_job_postings.py
    python build_knowledge_base.py
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(__file__))
from generate_job_postings import DOMAINS  # reuse the same 19 domains + a representative title each

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "job_postings.json")
COUNTRY = "in"  # India
RESULTS_PER_PAGE = 20


def load_credentials():
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        # This script doesn't depend on the backend's settings module for
        # anything else, so read backend/.env directly rather than
        # requiring the backend venv just for two values.
        env_path = os.path.join(os.path.dirname(__file__), "..", "backend", ".env")
        if os.path.exists(env_path):
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("ADZUNA_APP_ID="):
                        app_id = line.split("=", 1)[1].strip()
                    if line.startswith("ADZUNA_APP_KEY="):
                        app_key = line.split("=", 1)[1].strip()

    if not app_id or not app_key:
        print("ERROR: ADZUNA_APP_ID / ADZUNA_APP_KEY not found.")
        print("Register free (instant, no card) at https://developer.adzuna.com/signup")
        print("then add both to backend/.env")
        sys.exit(1)

    return app_id, app_key


def fetch_page(app_id, app_key, query, page):
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": RESULTS_PER_PAGE,
        "what": query,
        "content-type": "application/json",
    }
    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/{page}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def to_posting(raw, domain, index):
    title = (raw.get("title") or "").strip()
    company = ((raw.get("company") or {}).get("display_name") or "").strip()
    if not title or not company:
        return None  # never invent a title/company for an incomplete listing

    location = ((raw.get("location") or {}).get("display_name") or "Not specified").strip()

    # Adzuna reports annual salary in local currency for most listings, not
    # a monthly internship stipend -- only use it if it looks stipend-sized
    # (a plausible monthly INR figure), otherwise leave it blank rather than
    # showing a misleading number.
    salary_min = raw.get("salary_min")
    stipend = int(salary_min) if salary_min and salary_min < 100000 else None

    return {
        "job_id": f"ADZ{index:04d}",
        "title": title,
        "company": company,
        "location": location,
        "domain": domain,
        "job_description": (raw.get("description") or "").strip(),
        "responsibilities": [],
        "required_skills": [],
        "preferred_skills": [],
        "qualifications": [],
        "experience_requirement": None,
        "education_requirement": None,
        "duration": None,
        "stipend_inr_per_month": stipend,
        "application_url": raw.get("redirect_url"),
        "source": "adzuna_live",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pages", type=int, default=1, help="Pages per domain to fetch (each page ~20 results)")
    parser.add_argument("--enrich", action="store_true", help="Fill missing skills/qualifications via LLM")
    parser.add_argument("--append", action="store_true", help="Append to the existing dataset instead of replacing it")
    args = parser.parse_args()

    app_id, app_key = load_credentials()

    postings = []
    index = 1
    for domain_name, domain in DOMAINS.items():
        query = domain["titles"][0]  # e.g. "Software Engineering Intern"
        print(f"Fetching '{query}' ({domain_name})…")
        for page in range(1, args.pages + 1):
            try:
                data = fetch_page(app_id, app_key, query, page)
            except urllib.error.HTTPError as e:
                print(f"  page {page} failed: HTTP {e.code} — {e.read().decode('utf-8', errors='ignore')[:200]}")
                break
            except Exception as e:
                print(f"  page {page} failed: {e}")
                break

            results = data.get("results", [])
            if not results:
                break
            for raw in results:
                posting = to_posting(raw, domain_name, index)
                if posting:
                    postings.append(posting)
                    index += 1
            time.sleep(0.3)  # be polite to the free tier's rate limit

    print(f"\nFetched {len(postings)} real postings across {len(DOMAINS)} domains.")

    if not postings:
        print("No postings fetched — check your ADZUNA_APP_ID/ADZUNA_APP_KEY and try again.")
        return

    if args.enrich:
        from import_kaggle_dataset import enrich_with_llm  # reuse the same enrichment logic
        for p in postings:
            p["_domain_guessed"] = False  # Adzuna postings already have a confirmed real domain
        postings = enrich_with_llm(postings)
        for p in postings:
            p.pop("_domain_guessed", None)

    if args.append and os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            existing = json.load(f)
        postings = existing + postings

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(postings, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(postings)} total postings -> {OUTPUT_PATH}")

    by_domain = {}
    for p in postings:
        by_domain[p["domain"]] = by_domain.get(p["domain"], 0) + 1
    print("\nDomain breakdown:")
    for domain, count in sorted(by_domain.items(), key=lambda x: -x[1]):
        print(f"  {domain:<28} {count}")

    print("\nNext:\n  cd ../backend\n  python seed_job_postings.py\n  python build_knowledge_base.py")


if __name__ == "__main__":
    main()
