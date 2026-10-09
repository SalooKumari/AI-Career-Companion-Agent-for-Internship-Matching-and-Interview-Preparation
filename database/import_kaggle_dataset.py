"""
Imports a real Kaggle CSV of internship/job postings into
database/job_postings.json, in the same schema the rest of the pipeline
(seed_job_postings.py -> build_knowledge_base.py) already expects.

Company, location, stipend, duration, and the application URL are taken
EXACTLY as they appear in your CSV -- this script never invents or edits
those. Rows missing a real title or company are skipped rather than
guessed.

------------------------------------------------------------------------
STEP 1 — see what columns your downloaded CSV actually has:

    python import_kaggle_dataset.py --inspect path/to/your_file.csv

STEP 2 — edit COLUMN_MAP below to match what you saw, then run:

    python import_kaggle_dataset.py path/to/your_file.csv

Optional flags:
  --enrich   Fill in job_description / required_skills / preferred_skills /
             qualifications / responsibilities / experience_requirement /
             education_requirement using the LLM, grounded only in the
             REAL title + company + domain already on each posting (never
             touches company/location/stipend/duration/application_url).
             Needs backend/.env configured (OPENAI_API_KEY) and must be run
             with the backend's venv active, since it reuses
             backend/app/services/llm_service.py. Costs a small amount of
             API usage per row -- fine for a few hundred rows.
  --append   Add to the existing database/job_postings.json instead of
             replacing it (combine multiple Kaggle datasets by running this
             once per file, with --append from the second run onward).
------------------------------------------------------------------------

After running, seed the database and rebuild the knowledge base as usual:
    cd ../backend
    python seed_job_postings.py
    python build_knowledge_base.py
"""
import argparse
import csv
import json
import os
import sys

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "job_postings.json")

# --------------------------------------------------------------------------
# STEP 2: edit this after running --inspect on your downloaded CSV.
# Left side = our schema field name (don't change these).
# Right side = the exact column name from YOUR CSV, in quotes.
# Set a field to None if your CSV doesn't have that column at all.
# --------------------------------------------------------------------------
COLUMN_MAP = {
    "title": "internship_title",       # <-- EDIT to match your CSV
    "company": "company_name",         # <-- EDIT to match your CSV
    "location": "location",            # <-- EDIT to match your CSV
    "duration": "duration",            # <-- EDIT to match your CSV
    "stipend": "stipend",              # <-- EDIT to match your CSV
    "application_url": None,           # e.g. "listing_url" or "job_url" if your CSV has one
    "job_description": None,           # e.g. "description" / "summary" if your CSV has one
    "required_skills": None,           # a comma/semicolon-separated skills column, if present
    "domain": None,                    # e.g. "category" if your CSV has one
}

# Used only as a last-resort fallback when a title can't be matched to any
# domain below and --enrich isn't used to classify it via the LLM instead.
DEFAULT_DOMAIN = "Software Engineering"

# The 19 domains used everywhere else in this project (job_postings.json,
# the RAG chunking/matching, the interview question bank). Keep this list in
# sync with database/generate_job_postings.py's DOMAINS keys.
KNOWN_DOMAINS = [
    "Software Engineering", "Web Development", "Data Science & Analytics",
    "Machine Learning / AI", "Embedded Systems / IoT", "Mechanical Engineering",
    "Electrical Engineering", "Cloud / DevOps", "Cybersecurity",
    "Product Management", "UI/UX Design", "Marketing", "Finance",
    "Human Resources", "Operations / Supply Chain", "Biotechnology",
    "Civil Engineering", "Content & Writing", "Sales & Business Development",
]

# Keyword -> domain, checked against the real title (lowercased) when the
# CSV has no domain/category column. This runs even without --enrich, so a
# diverse CSV (marketing, HR, finance, mechanical, ...) doesn't silently
# collapse into a single default domain. --enrich replaces this guess with
# a more accurate LLM classification when used.
DOMAIN_KEYWORDS = [
    ("Data Science & Analytics", ["data scien", "data analy", "business analy", "bi analyst", "analytics"]),
    ("Machine Learning / AI", ["machine learning", " ml ", "artificial intelligence", " ai ", "deep learning", "nlp"]),
    ("Web Development", ["web develop", "frontend", "front-end", "front end", "full stack", "full-stack", "react", "wordpress"]),
    ("Embedded Systems / IoT", ["embedded", "firmware", "iot", "robotics", "hardware"]),
    ("Mechanical Engineering", ["mechanical"]),
    ("Electrical Engineering", ["electrical", "power systems", "controls engineer"]),
    ("Civil Engineering", ["civil engineer", "structural", "site engineer"]),
    ("Biotechnology", ["biotech", "biology", "life science", "lab assistant", "pharma", "clinical research"]),
    ("Cloud / DevOps", ["devops", "cloud engineer", "site reliability", "sre"]),
    ("Cybersecurity", ["cyber security", "cybersecurity", "security analyst", "penetration test", "infosec"]),
    ("Product Management", ["product manag", "product intern", "associate product"]),
    ("UI/UX Design", ["ui/ux", "ui design", "ux design", "product design", "graphic design", "visual design"]),
    ("Marketing", ["marketing", "seo", "social media", "growth intern", "brand"]),
    ("Finance", ["finance", "financial analyst", "investment", "accounting", "audit", "fp&a"]),
    ("Human Resources", ["human resource", " hr ", "hr intern", "talent acquisition", "recruit", "people operations"]),
    ("Operations / Supply Chain", ["operations", "supply chain", "logistics", "procurement", "inventory"]),
    ("Content & Writing", ["content writ", "technical writ", "copywrit", "editorial", "journalis"]),
    ("Sales & Business Development", ["sales intern", "business development", "bd intern"]),
    ("Software Engineering", ["software engineer", "backend", "back-end", "back end", "sde", "programmer", "developer intern"]),
]


def classify_domain_by_keyword(title):
    lowered = f" {title.lower()} "
    for domain, keywords in DOMAIN_KEYWORDS:
        if any(kw in lowered for kw in keywords):
            return domain
    return None  # no confident match — caller decides the fallback


def inspect(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        print(f"Columns found in {csv_path}:")
        for c in reader.fieldnames:
            print(f"  - {c}")
        print("\nFirst 2 rows (to sanity-check the data):")
        for i, row in enumerate(reader):
            if i >= 2:
                break
            print(json.dumps(row, indent=2, ensure_ascii=False))
    print("\nNow edit COLUMN_MAP in this script to match the column names above, then re-run without --inspect.")


def parse_stipend(raw):
    if not raw:
        return None
    digits = "".join(ch for ch in str(raw) if ch.isdigit())
    return int(digits) if digits else None


def parse_skills(raw):
    if not raw:
        return []
    seps = ";" if ";" in raw else ","
    return [s.strip() for s in raw.split(seps) if s.strip()]


def load_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def build_posting(row, index):
    def get(field):
        col = COLUMN_MAP.get(field)
        return (row.get(col) or "").strip() if col else ""

    title = get("title")
    company = get("company")
    if not title or not company:
        return None  # never invent a title/company for an incomplete row

    csv_domain = get("domain")
    domain = csv_domain or classify_domain_by_keyword(title) or DEFAULT_DOMAIN
    domain_guessed = not csv_domain  # flagged so --enrich knows to double-check/replace it

    return {
        "job_id": f"KAG{index:04d}",
        "title": title,
        "company": company,
        "location": get("location") or "Not specified",
        "domain": domain,
        "_domain_guessed": domain_guessed,  # internal flag, stripped before writing output
        "job_description": get("job_description"),
        "responsibilities": [],
        "required_skills": parse_skills(get("required_skills")),
        "preferred_skills": [],
        "qualifications": [],
        "experience_requirement": None,
        "education_requirement": None,
        "duration": get("duration") or None,
        "stipend_inr_per_month": parse_stipend(get("stipend")),
        "application_url": get("application_url") or None,
        "source": "kaggle_import",
    }


def enrich_with_llm(postings):
    """Fills in missing detail fields for postings that need it, and
    replaces keyword-guessed domains with a more accurate LLM
    classification (constrained to the project's 19 known domains).
    Grounded only in each posting's real title/company. Never touches
    company, location, stipend, duration, or application_url."""
    backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
    sys.path.insert(0, backend_dir)
    from app.services.llm_service import _get_client
    from app.core.config import settings

    client = _get_client()
    to_enrich = [
        p for p in postings
        if not p["job_description"] or not p["required_skills"] or p.get("_domain_guessed")
    ]
    print(f"Enriching {len(to_enrich)} of {len(postings)} postings "
          f"(missing description/skills, and/or refining a keyword-guessed domain)…")

    domain_list = ", ".join(f'"{d}"' for d in KNOWN_DOMAINS)

    for i, posting in enumerate(to_enrich, start=1):
        prompt = f"""A real internship posting has this title and company \
(do not change these — only classify/describe the likely role):
Title: {posting['title']}
Company: {posting['company']}
Current best-guess domain: {posting['domain']}

Return ONLY a JSON object with these keys:
"domain" — exactly one of: [{domain_list}] — pick the single best fit for \
this title, even if the current best-guess above is already correct.
"job_description" (2-3 sentences), "responsibilities" (3-5 short bullet \
strings), "required_skills" (4-6 strings), "preferred_skills" (2-4 \
strings), "qualifications" (1-3 strings), "experience_requirement" (1 \
short sentence), "education_requirement" (1 short sentence)."""

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            max_tokens=700,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        data = json.loads(response.choices[0].message.content)

        if data.get("domain") in KNOWN_DOMAINS and posting.get("_domain_guessed"):
            posting["domain"] = data["domain"]

        for field in ["job_description", "responsibilities", "required_skills",
                      "preferred_skills", "qualifications",
                      "experience_requirement", "education_requirement"]:
            if not posting.get(field):
                posting[field] = data.get(field, posting.get(field))

        if i % 10 == 0 or i == len(to_enrich):
            print(f"  ...{i}/{len(to_enrich)}")

    return postings


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_path", nargs="?", help="Path to your downloaded Kaggle CSV")
    parser.add_argument("--inspect", metavar="CSV_PATH", help="Print columns + sample rows, then exit")
    parser.add_argument("--enrich", action="store_true", help="Fill missing detail fields via LLM")
    parser.add_argument("--append", action="store_true", help="Append to the existing dataset instead of replacing it")
    args = parser.parse_args()

    if args.inspect:
        inspect(args.inspect)
        return

    if not args.csv_path:
        parser.error("Provide a CSV path, or run with --inspect <csv_path> first.")

    rows = load_rows(args.csv_path)
    print(f"Read {len(rows)} rows from {args.csv_path}")

    postings = [p for p in (build_posting(row, i) for i, row in enumerate(rows, start=1)) if p]
    print(f"Built {len(postings)} postings ({len(rows) - len(postings)} skipped — missing title/company).")

    if args.enrich and postings:
        postings = enrich_with_llm(postings)

    for p in postings:
        p.pop("_domain_guessed", None)  # internal-only flag, not part of the schema

    if args.append and os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            existing = json.load(f)
        offset = len(existing)
        for j, p in enumerate(postings):
            p["job_id"] = f"KAG{offset + j + 1:04d}"
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
    if not args.enrich:
        print("\n(Domains above were guessed from keywords in the title — "
              "re-run with --enrich for more accurate LLM-based classification.)")

    print("\nNext:\n  cd ../backend\n  python seed_job_postings.py\n  python build_knowledge_base.py")


if __name__ == "__main__":
    main()
