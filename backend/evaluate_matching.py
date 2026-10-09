"""
M2.4 — Matching & Retrieval Evaluation.

Runs several sample student profiles (different skill sets, spanning
different domains) through:
  1. The RAG retrieval step alone (semantic_search) — checks whether a
     natural-language profile summary retrieves postings from the expected
     domain(s), i.e. retrieval relevance / Top-K quality.
  2. The full Job-Resume Matching Agent (retrieval + LLM scoring) — checks
     whether the LLM's score ranks the expected-domain postings higher than
     unrelated ones, and prints the reasoning for manual quality review.

"Expected domain(s)" per profile is the manually-defined ground truth this
script checks retrieval/ranking against (M2.4: "compare AI recommendations
against manually expected results"). This is a lightweight heuristic eval,
not a formal benchmark — it's meant to catch obviously broken retrieval or
scoring, and to give concrete examples to read the reasoning quality from.

Usage (from backend/, with the knowledge base already built):
    python evaluate_matching.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models.job_posting import JobPosting
from app.services.vector_store import semantic_search
from app.services.llm_service import score_job_match

TOP_K_RETRIEVAL = 10
TOP_K_SCORED = 5

# Five sample profiles spanning different domains, written as plain-text
# summaries in the same shape build_student_profile_summary() would produce
# from a real parsed resume (Milestone 1). Kept as plain text here so this
# script can run without needing real Student/Skill rows in the database.
SAMPLE_PROFILES = [
    {
        "name": "Ananya Sharma",
        "expected_domains": ["Software Engineering", "Web Development"],
        "profile_text": (
            "Name: Ananya Sharma\n"
            "Skills: Python, Java, C++, React, Flask, Node.js, Git, Docker, "
            "Team Leadership, Communication\n"
            "Education: B.Tech in Computer Science — Indian Institute of Technology, Dhanbad\n"
            "Experience: Software Engineering Intern at Zeta Technologies — built and shipped a "
            "REST API used by the internal analytics dashboard.\n"
            "Project: Campus Event Finder (tech: React, Node.js, MongoDB) — a web app that "
            "aggregates college event listings.\n"
            "Project: Expense Splitter Bot (tech: Python, Telegram Bot API) — splits shared "
            "group expenses."
        ),
    },
    {
        "name": "Rohan Mehta",
        "expected_domains": ["Embedded Systems / IoT", "Electrical Engineering"],
        "profile_text": (
            "Name: Rohan Mehta\n"
            "Skills: C, Embedded C, Python, MATLAB, Arduino, Raspberry Pi, KiCad, Altium Designer\n"
            "Education: B.Tech in Electronics and Communication Engineering — NIT Surathkal\n"
            "Experience: Hardware Intern at Sensewave Robotics — worked on firmware for a "
            "battery management system for a delivery robot prototype.\n"
            "Experience: Teaching Assistant, NITK Dept. of ECE — assists first-year students "
            "with digital logic design labs.\n"
            "Project: Smart Irrigation Controller (tech: Arduino) — soil-moisture-based "
            "irrigation controller.\n"
            "Project: Line-Following Robot — PID-controlled robot for the robotics club."
        ),
    },
    {
        "name": "Priya Nair",
        "expected_domains": ["Data Science & Analytics"],
        "profile_text": (
            "Name: Priya Nair\n"
            "Skills: Python (pandas, numpy, matplotlib), SQL, Excel, basic R\n"
            "Education: B.Sc Statistics — University of Delhi\n"
            "Project: Analyzed a public dataset of city bus ridership to identify peak hours "
            "and underused routes; presented findings to the college data club.\n"
            "Project: Built a simple dashboard in Python (Streamlit) to visualize personal "
            "expense data."
        ),
    },
    {
        "name": "Kabir Anand",
        "expected_domains": ["Marketing", "Content & Writing"],
        "profile_text": (
            "Name: Kabir Anand\n"
            "Skills: Content writing, Social media strategy, SEO, Google Analytics, Canva\n"
            "Education: BA in Mass Communication — Delhi University\n"
            "Experience: Social Media Intern at a college startup incubator — grew an "
            "Instagram account from 500 to 4,000 followers through a content calendar.\n"
            "Project: Ran a small email newsletter for the campus entrepreneurship club, "
            "covering weekly open rates and subject-line A/B tests."
        ),
    },
    {
        "name": "Sneha Iyer",
        "expected_domains": ["Mechanical Engineering"],
        "profile_text": (
            "Name: Sneha Iyer\n"
            "Skills: SolidWorks, AutoCAD, GD&T, basic FEA, 3D printing\n"
            "Education: B.Tech in Mechanical Engineering — VIT Vellore\n"
            "Project: Designed and 3D-printed a redesigned bicycle gear housing to reduce "
            "weight, verified with basic FEA simulation.\n"
            "Project: Team lead for the college SAE Baja chassis sub-team, responsible for "
            "CAD models and drawing packages."
        ),
    },
]


def evaluate_retrieval(profile):
    hits = semantic_search(profile["profile_text"], top_k_jobs=TOP_K_RETRIEVAL)
    expected = set(profile["expected_domains"])

    relevant_count = sum(1 for h in hits if h.get("domain") in expected)
    relevance_rate = relevant_count / len(hits) if hits else 0.0

    print(f"\n--- {profile['name']} — expected domain(s): {', '.join(expected)} ---")
    print(f"Retrieved top-{len(hits)}:")
    for rank, h in enumerate(hits, start=1):
        flag = "✓" if h.get("domain") in expected else " "
        print(f"  [{flag}] #{rank:<2} sim={h['similarity']:.3f}  {h['title']} @ {h['company']}  ({h.get('domain')})")

    print(f"Retrieval relevance: {relevant_count}/{len(hits)} ({relevance_rate:.0%}) of top-{TOP_K_RETRIEVAL} are in the expected domain(s).")
    return hits, relevance_rate


def evaluate_scoring(db, profile, hits):
    expected = set(profile["expected_domains"])
    candidates = hits[:TOP_K_SCORED]

    scored = []
    for h in candidates:
        job = db.query(JobPosting).filter(JobPosting.id == h["job_posting_id"]).first()
        if job is None:
            continue
        job_summary = (
            f"Title: {job.title}\nCompany: {job.company}\nLocation: {job.location}\n"
            f"Description: {job.job_description}\n"
            f"Required skills: {', '.join(job.required_skills)}\n"
            f"Preferred skills: {', '.join(job.preferred_skills)}\n"
            f"Experience required: {job.experience_requirement}\n"
            f"Education required: {job.education_requirement}"
        )
        try:
            result = score_job_match(profile["profile_text"], job_summary)
        except Exception as e:
            print(f"  [scoring failed for {job.title}: {e}]")
            continue
        scored.append((job, result))

    scored.sort(key=lambda x: x[1].score, reverse=True)

    print("LLM-scored ranking (top candidates re-ranked by compatibility score):")
    for job, result in scored:
        flag = "✓" if job.domain in expected else " "
        print(f"  [{flag}] score={result.score:<3} {job.title} @ {job.company}  ({job.domain})")
        print(f"        reasoning: {result.reasoning}")

    if scored:
        top_score_job, _ = scored[0]
        top_is_expected = top_score_job.domain in expected
        print(f"Top-ranked-by-score posting is in the expected domain: {top_is_expected}")

    return scored


def main():
    db = SessionLocal()
    api_key_present = bool(os.environ.get("OPENAI_API_KEY"))

    if not api_key_present:
        print("NOTE: OPENAI_API_KEY not set — running retrieval-only evaluation "
              "(skipping LLM scoring step). Set it in backend/.env to evaluate the "
              "full Matching Agent.\n")

    retrieval_scores = []
    try:
        for profile in SAMPLE_PROFILES:
            hits, relevance_rate = evaluate_retrieval(profile)
            retrieval_scores.append((profile["name"], relevance_rate))

            if api_key_present and hits:
                evaluate_scoring(db, profile, hits)

        print("\n=== Summary: retrieval relevance by profile ===")
        for name, rate in retrieval_scores:
            print(f"  {name:<15} {rate:.0%}")
        avg = sum(r for _, r in retrieval_scores) / len(retrieval_scores) if retrieval_scores else 0
        print(f"  {'Average':<15} {avg:.0%}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
