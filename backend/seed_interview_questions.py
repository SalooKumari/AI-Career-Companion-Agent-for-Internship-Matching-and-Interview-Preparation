"""
Loads database/interview_questions.json into the `interview_bank_questions`
table. Idempotent: clears and re-inserts.

Usage (from backend/, with .env configured):
    python seed_interview_questions.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import Base, engine, SessionLocal
from app.models import student, job_posting, match, application, interview  # noqa: F401
from app.models.interview import InterviewBankQuestion

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "interview_questions.json")


def main():
    Base.metadata.create_all(bind=engine)

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)

    db = SessionLocal()
    try:
        existing_count = db.query(InterviewBankQuestion).count()
        if existing_count:
            print(f"Clearing {existing_count} existing bank questions…")
            db.query(InterviewBankQuestion).delete()
            db.commit()

        for q in questions:
            db.add(InterviewBankQuestion(
                domain=q["domain"],
                category=q["category"],
                question_text=q["question_text"],
                difficulty=q.get("difficulty"),
            ))

        db.commit()
        print(f"Inserted {len(questions)} interview bank questions into the database.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
