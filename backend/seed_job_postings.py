"""
Loads database/job_postings.json into the `job_postings` table (M2.1:
"Store the dataset in a structured format").

Idempotent: clears the table and re-inserts, so it's safe to re-run after
regenerating the dataset.

Usage (from backend/, with .env configured and the database created):
    python seed_job_postings.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import Base, engine, SessionLocal
from app.models import student, job_posting, match, application, interview, skill_gap, application_material, interview_prep, chat, saved_job  # noqa: F401 - register all models
from app.models.job_posting import JobPosting
from app.models.match import Match
from app.models.application import Application
from app.models.skill_gap import SkillGapAnalysis
from app.models.application_material import ApplicationMaterial
from app.models.interview_prep import InterviewPrepPlan
from app.models.interview import InterviewFeedback, InterviewSet, InterviewSetQuestion
from app.models.saved_job import SavedJob
from app.models.chat import ChatMessage

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "job_postings.json")


def main():
    Base.metadata.create_all(bind=engine)

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        postings = json.load(f)

    db = SessionLocal()
    try:
        existing_count = db.query(JobPosting).count()
        if existing_count:
            print(f"Clearing {existing_count} existing job postings…")
            # Everything below holds a foreign key to job_postings, so it
            # must be cleared first or Postgres blocks the delete. All of
            # it is recomputable/re-doable from the app (matches, gap
            # analyses, materials, and prep plans can be regenerated;
            # applications would need to be re-applied by the student) —
            # acceptable for a dev-stage reseed.
            deleted_matches = db.query(Match).delete()
            deleted_applications = db.query(Application).delete()
            deleted_gaps = db.query(SkillGapAnalysis).delete()
            deleted_materials = db.query(ApplicationMaterial).delete()
            deleted_preps = db.query(InterviewPrepPlan).delete()
            deleted_saved = db.query(SavedJob).delete()
            detached_chat_references = db.query(ChatMessage).filter(ChatMessage.job_posting_id.isnot(None)).update(
                {ChatMessage.job_posting_id: None}, synchronize_session=False
            )
            job_specific_set_ids = [row[0] for row in db.query(InterviewSet.id).filter(InterviewSet.job_posting_id.isnot(None)).all()]
            deleted_feedback = db.query(InterviewFeedback).filter(InterviewFeedback.interview_set_id.in_(job_specific_set_ids)).delete(synchronize_session=False)
            deleted_questions = db.query(InterviewSetQuestion).filter(InterviewSetQuestion.interview_set_id.in_(job_specific_set_ids)).delete(synchronize_session=False)
            deleted_interview_sets = db.query(InterviewSet).filter(InterviewSet.id.in_(job_specific_set_ids)).delete(synchronize_session=False)
            cleared = deleted_matches + deleted_applications + deleted_gaps + deleted_materials + deleted_preps + deleted_saved + deleted_interview_sets
            if cleared:
                print(f"  Also cleared {deleted_matches} match(es), {deleted_applications} application(s), "
                      f"{deleted_gaps} skill gap analysis/es, {deleted_materials} application material(s), "
                      f"{deleted_preps} interview prep plan(s), {deleted_saved} saved job(s), and "
                      f"{deleted_interview_sets} job-specific interview set(s) that referenced them.")
            if detached_chat_references:
                print(f"  Removed job references from {detached_chat_references} chat message(s); messages were preserved.")
            db.query(JobPosting).delete()
            db.commit()

        for p in postings:
            db.add(JobPosting(
                job_id=p["job_id"],
                title=p["title"],
                company=p["company"],
                location=p["location"],
                domain=p.get("domain"),
                job_description=p["job_description"],
                responsibilities=p.get("responsibilities", []),
                required_skills=p.get("required_skills", []),
                preferred_skills=p.get("preferred_skills", []),
                qualifications=p.get("qualifications", []),
                experience_requirement=p.get("experience_requirement"),
                education_requirement=p.get("education_requirement"),
                duration=p.get("duration"),
                stipend_inr_per_month=p.get("stipend_inr_per_month"),
                application_url=p.get("application_url"),
                source=p.get("source", "synthetic"),
            ))

        db.commit()
        print(f"Inserted {len(postings)} job postings into the database.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
