"""
Builds the RAG knowledge base for internship retrieval (M2.2):
reads job postings from the database, chunks each one, embeds the chunks,
and upserts them into the local Chroma vector store.

Run this once after seed_job_postings.py, and again any time the job
postings change.

Usage (from backend/, with .env configured):
    python build_knowledge_base.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models.job_posting import JobPosting
from app.services.chunking import build_job_chunks
from app.services.vector_store import reset_collection, upsert_chunks


def main():
    db = SessionLocal()
    try:
        jobs = db.query(JobPosting).all()
        if not jobs:
            print("No job postings found in the database. Run seed_job_postings.py first.")
            return

        print(f"Building knowledge base from {len(jobs)} job postings…")
        reset_collection()

        all_chunks = []
        for job in jobs:
            job_dict = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "domain": job.domain,
                "job_description": job.job_description,
                "responsibilities": job.responsibilities,
                "required_skills": job.required_skills,
                "preferred_skills": job.preferred_skills,
                "qualifications": job.qualifications,
                "experience_requirement": job.experience_requirement,
                "education_requirement": job.education_requirement,
            }
            chunks = build_job_chunks(job_dict)
            for c in chunks:
                c["title"] = job.title
                c["company"] = job.company
                c["location"] = job.location
                c["domain"] = job.domain or ""
            all_chunks.extend(chunks)

        print(f"Generated {len(all_chunks)} chunks ({len(all_chunks) / len(jobs):.1f} per posting on average). Embedding…")
        upsert_chunks(all_chunks)

        print("Knowledge base built. Vector store saved under backend/vector_store/.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
