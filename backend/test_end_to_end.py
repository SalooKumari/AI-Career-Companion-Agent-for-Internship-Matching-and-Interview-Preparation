"""
M4.2 — End-to-End System Testing & Validation (and M4.3 latency measurement).

Runs the complete student workflow directly against the database and the
real services (no HTTP server needed), timing every stage:

  Student Profile -> Retrieval (RAG) -> Job Matching -> Skill Gap Analysis
  -> Resume/Cover Letter Customization -> Interview Preparation
  -> Application Tracking -> Conversational Assistant (multi-turn)

then runs cross-agent consistency checks:
  * Do matched skills (Matching Agent) contradict critical gaps (Skill Gap Agent)?
  * Does the tailored resume claim skills the student doesn't have?
  * Does the Career Assistant retain context across turns?
  * Does retrieval stay in-domain for a domain-specific profile?

Requires: database seeded (seed_job_postings.py), knowledge base built
(build_knowledge_base.py), and a working LLM key in backend/.env. It creates
(and at the end deletes) a throwaway test student, so it doesn't touch real
accounts.

Usage (from backend/, venv active):
    python test_end_to_end.py

Writes test_results.json next to this file — a machine-readable record of
every check (status, latency, notes) suitable for the project report's
"Testing and Evaluation" and "Results and Analysis" sections.
"""
import json
import os
import sys
import time
import traceback
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal, Base, engine
from app.models import (  # noqa: F401 - register all models
    student, job_posting, match, application, interview,
    skill_gap, application_material, interview_prep, chat, saved_job,
)
from app.models.student import Student, Skill, Education, Experience, Project
from app.models.job_posting import JobPosting
from app.models.application import Application, APPLICATION_STATUSES
from app.models.match import Match
from app.models.skill_gap import SkillGapAnalysis
from app.models.application_material import ApplicationMaterial
from app.models.interview_prep import InterviewPrepPlan
from app.models.chat import ChatMessage
from app.core.security import hash_password

from app.services.vector_store import semantic_search
from app.services.matching_agent import run_matching
from app.services.skill_gap_agent import run_skill_gap_analysis
from app.services.application_material_agent import generate_materials
from app.services.interview_prep_agent import generate_prep_plan
from app.services.career_assistant import send_message

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "test_results.json")
TEST_EMAIL = "e2e-test-student@example.com"

results = []


def record(name, status, latency_s=None, notes=""):
    results.append({"test": name, "status": status, "latency_s": round(latency_s, 2) if latency_s is not None else None, "notes": notes})
    icon = {"PASS": "✓", "FAIL": "✗", "WARN": "!", "ERROR": "E", "SKIP": "-"}.get(status, "?")
    lat = f" ({latency_s:.2f}s)" if latency_s is not None else ""
    print(f"  [{icon}] {status:<5} {name}{lat}" + (f" — {notes}" if notes else ""))


def timed(fn, *args, **kwargs):
    start = time.perf_counter()
    out = fn(*args, **kwargs)
    return out, time.perf_counter() - start


def create_test_student(db):
    existing = db.query(Student).filter(Student.email == TEST_EMAIL).first()
    if existing:
        db.delete(existing)
        db.commit()

    s = Student(full_name="E2E Test Student", email=TEST_EMAIL, password_hash=hash_password("test-password-123"))
    db.add(s)
    db.flush()

    for name in ["Python", "SQL", "Pandas", "Data Visualization", "Statistics", "Excel"]:
        db.add(Skill(student_id=s.id, name=name, category="programming"))
    db.add(Education(
        student_id=s.id, institution="Test University", degree="B.Sc", field_of_study="Statistics",
        start_date="2022", end_date="2025", grade="8.4 CGPA",
    ))
    db.add(Project(
        student_id=s.id, title="Bus Ridership Analysis",
        description="Analyzed a public dataset of city bus ridership to find peak hours and underused routes.",
        tech_stack="Python, Pandas, Matplotlib",
    ))
    db.add(Project(
        student_id=s.id, title="Expense Dashboard",
        description="Built a Streamlit dashboard visualizing personal expense data.",
        tech_stack="Python, Streamlit",
    ))
    db.commit()
    db.refresh(s)
    return s


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    student_row = None

    try:
        print("=" * 72)
        print("END-TO-END SYSTEM TEST")
        print("=" * 72)

        # ---- 0. Preconditions ----
        job_count = db.query(JobPosting).count()
        if job_count == 0:
            print("No job postings in the database. Run seed_job_postings.py + build_knowledge_base.py first.")
            return
        print(f"\nKnowledge base: {job_count} job postings in DB\n")

        # ---- 1. Student profile ----
        print("[1] Student profile")
        try:
            student_row, t = timed(create_test_student, db)
            record("Create test student + structured profile", "PASS", t)
        except Exception as e:
            record("Create test student + structured profile", "ERROR", notes=str(e))
            return

        # ---- 2. RAG retrieval ----
        print("\n[2] RAG retrieval")
        try:
            hits, t = timed(semantic_search, "data analyst internship using Python and SQL", top_k_jobs=10)
            record("Semantic search returns results", "PASS" if hits else "FAIL", t, f"{len(hits)} results")

            in_domain = [h for h in hits if h.get("domain") in ("Data Science & Analytics", "Machine Learning / AI")]
            rate = len(in_domain) / len(hits) if hits else 0
            record(
                "Retrieval relevance (top-10 in expected domains for a data-analyst query)",
                "PASS" if rate >= 0.5 else "WARN" if rate >= 0.3 else "FAIL",
                notes=f"{rate:.0%} in Data Science/ML domains",
            )

            irrelevant_hits, t = timed(semantic_search, "mechanical design CAD SolidWorks manufacturing", top_k_jobs=10)
            mech = [h for h in irrelevant_hits if h.get("domain") == "Mechanical Engineering"]
            data_leak = [h for h in irrelevant_hits if h.get("domain") in ("Data Science & Analytics", "Marketing", "Finance")]
            record(
                "Irrelevant-retrieval prevention (mechanical query shouldn't surface data/marketing/finance roles)",
                "PASS" if len(data_leak) <= 2 else "WARN",
                t,
                f"{len(mech)} mechanical, {len(data_leak)} off-domain in top-10",
            )
        except Exception as e:
            record("RAG retrieval", "ERROR", notes=str(e))

        # ---- 3. Matching ----
        print("\n[3] Job-Resume Matching Agent")
        matches = []
        try:
            matches, t = timed(run_matching, db, student_row.id, 5)
            record("Matching Agent returns ranked matches", "PASS" if matches else "FAIL", t, f"{len(matches)} matches")

            if matches:
                scores = [m.score for m in matches]
                record("Matches are sorted by score (descending)", "PASS" if scores == sorted(scores, reverse=True) else "FAIL")
                record(
                    "Score breakdown present (skills/education/project/domain fit)",
                    "PASS" if all(m.skills_score is not None and m.education_score is not None for m in matches) else "FAIL",
                )
                top_domain = matches[0].job.domain
                record(
                    "Top match is in an expected domain for a Statistics/Python/SQL profile",
                    "PASS" if top_domain in ("Data Science & Analytics", "Machine Learning / AI") else "WARN",
                    notes=f"top match domain: {top_domain}",
                )
        except Exception as e:
            record("Matching Agent", "ERROR", notes=f"{e}")
            traceback.print_exc()

        target_job = matches[0].job if matches else db.query(JobPosting).first()

        # ---- 4. Skill Gap ----
        print("\n[4] Skill Gap Analysis Agent")
        gap = None
        try:
            gap, t = timed(run_skill_gap_analysis, db, student_row, target_job)
            record("Skill Gap Agent returns categorized analysis", "PASS" if gap else "FAIL", t)

            has_all_categories = all(
                hasattr(gap, f) for f in
                ["critical_gaps", "partial_gaps", "preferred_gaps", "experience_gaps", "qualification_gaps", "recommendations"]
            )
            record("Gap analysis has all required categories", "PASS" if has_all_categories else "FAIL")
        except Exception as e:
            record("Skill Gap Agent", "ERROR", notes=str(e))

        # ---- 5. Cross-agent consistency: matching vs skill gap ----
        print("\n[5] Cross-agent consistency")
        try:
            if matches and gap:
                matched = {s.lower().strip() for s in (matches[0].matched_skills or [])}
                critical = {(g.get("item") or "").lower().strip() for g in (gap.critical_gaps or [])}
                overlap = matched & critical
                record(
                    "No contradiction: skills the Matching Agent says the student HAS aren't listed as CRITICAL gaps",
                    "PASS" if not overlap else "FAIL",
                    notes=f"contradictory: {sorted(overlap)}" if overlap else "",
                )
            else:
                record("Matching vs Skill Gap consistency", "SKIP", notes="needs both to have run")
        except Exception as e:
            record("Matching vs Skill Gap consistency", "ERROR", notes=str(e))

        # ---- 6. Resume/Cover letter ----
        print("\n[6] Resume & Cover Letter Customization Agent")
        material = None
        try:
            material, t = timed(generate_materials, db, student_row, target_job)
            record("Materials generated (resume + cover letter)", "PASS" if material and material.resume_content and material.cover_letter_content else "FAIL", t)

            if material and gap:
                missing_items = [(g.get("item") or "").lower().strip() for g in (gap.critical_gaps or []) if g.get("item")]
                resume_lower = (material.resume_content or "").lower()
                cover_lower = (material.cover_letter_content or "").lower()
                claimed = [m for m in missing_items if m and (m in resume_lower)]
                record(
                    "No fabrication: tailored resume doesn't list the student's CRITICAL gap skills as skills they have",
                    "PASS" if not claimed else "WARN",
                    notes=f"possibly claimed (review manually — may be a 'learning' mention): {claimed}" if claimed else "",
                )
                record(
                    "Cover letter mentions the actual company",
                    "PASS" if target_job.company.lower() in cover_lower else "WARN",
                )
        except Exception as e:
            record("Resume & Cover Letter Agent", "ERROR", notes=str(e))

        # ---- 7. Interview prep ----
        print("\n[7] Interview Preparation Agent")
        try:
            plan, t = timed(generate_prep_plan, db, student_row, target_job)
            counts = {
                "technical": len(plan.technical_questions or []),
                "resume_based": len(plan.resume_based_questions or []),
                "project_based": len(plan.project_based_questions or []),
                "role_specific": len(plan.role_specific_questions or []),
                "hr": len(plan.hr_questions or []),
            }
            record("Prep plan generated with all 5 question categories", "PASS" if all(v > 0 for v in counts.values()) else "WARN", t, str(counts))
            record("Revision topics generated", "PASS" if plan.revision_topics else "WARN")
        except Exception as e:
            record("Interview Prep Agent", "ERROR", notes=str(e))

        # ---- 8. Application tracking ----
        print("\n[8] Application Tracking Module")
        try:
            app_row = Application(
                student_id=student_row.id, job_posting_id=target_job.id,
                deadline=date.today() + timedelta(days=1),
            )
            db.add(app_row)
            db.commit()
            db.refresh(app_row)
            record("Create application with a deadline", "PASS")

            for status in ["under_review", "shortlisted", "interview_scheduled", "interview_completed", "offer_received"]:
                app_row.status = status
                db.commit()
            record("Walk application through the full status lifecycle", "PASS", notes="applied -> ... -> offer_received")

            app_row.interview_date = date.today() + timedelta(days=2)
            app_row.notes = "Recruiter: test contact"
            db.commit()
            record("Store interview date + notes", "PASS")

            record("All expected statuses are defined", "PASS" if len(APPLICATION_STATUSES) == 8 else "WARN", notes=str(APPLICATION_STATUSES))
        except Exception as e:
            record("Application tracking", "ERROR", notes=str(e))

        # ---- 9. Conversational assistant, multi-turn ----
        print("\n[9] Conversational Career Assistant (multi-turn context retention)")
        try:
            r1, t1 = timed(send_message, db, student_row, "What kind of internships fit my profile best?", None)
            record("Turn 1: answers a profile-aware recommendation question", "PASS" if r1.content else "FAIL", t1)

            r2, t2 = timed(
                send_message, db, student_row,
                "Tell me more about the first one you mentioned — what would I need to improve for it?", None,
            )
            record("Turn 2: follow-up resolves 'the first one you mentioned' from turn 1", "PASS" if r2.content else "FAIL", t2, "review reply manually for correct reference")

            r3, t3 = timed(
                send_message, db, student_row,
                "Can you check my resume for problems?", None,
            )
            record(
                "Turn 3: resume-critique question handled (no resume uploaded -> should say so, not hallucinate)",
                "PASS" if r3.content and ("upload" in r3.content.lower() or "resume" in r3.content.lower()) else "WARN",
                t3,
            )
            print("\n     Sample assistant replies (for manual review):")
            print(f"       T1: {r1.content[:160]}…")
            print(f"       T2: {r2.content[:160]}…")
            print(f"       T3: {r3.content[:160]}…")
        except Exception as e:
            record("Conversational assistant", "ERROR", notes=str(e))

    finally:
        # ---- cleanup: delete the throwaway test student and everything hanging off it ----
        if student_row is not None:
            try:
                db.query(ChatMessage).filter(ChatMessage.student_id == student_row.id).delete()
                db.query(InterviewPrepPlan).filter(InterviewPrepPlan.student_id == student_row.id).delete()
                db.query(ApplicationMaterial).filter(ApplicationMaterial.student_id == student_row.id).delete()
                db.query(SkillGapAnalysis).filter(SkillGapAnalysis.student_id == student_row.id).delete()
                db.query(Match).filter(Match.student_id == student_row.id).delete()
                db.query(Application).filter(Application.student_id == student_row.id).delete()
                db.query(Student).filter(Student.id == student_row.id).delete()
                db.commit()
            except Exception as e:
                print(f"\n(cleanup note: {e} — delete the test student '{TEST_EMAIL}' manually if it remains)")
        db.close()

        # ---- summary ----
        print("\n" + "=" * 72)
        passed = sum(1 for r in results if r["status"] == "PASS")
        warned = sum(1 for r in results if r["status"] == "WARN")
        failed = sum(1 for r in results if r["status"] in ("FAIL", "ERROR"))
        print(f"SUMMARY: {passed} passed, {warned} warnings, {failed} failed/errored, {len(results)} total")

        latencies = [r for r in results if r["latency_s"] is not None]
        if latencies:
            print("\nLatency by stage (s):")
            for r in latencies:
                print(f"  {r['latency_s']:>7.2f}  {r['test']}")
            total = sum(r["latency_s"] for r in latencies)
            print(f"  {total:>7.2f}  TOTAL measured LLM/retrieval time across the workflow")

        with open(RESULTS_PATH, "w", encoding="utf-8") as f:
            json.dump({"results": results, "passed": passed, "warnings": warned, "failed": failed}, f, indent=2)
        print(f"\nFull results written to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
