"""
SQLAlchemy model for internship/job postings.
Matches the schema in docs/job_posting_schema.md.
List fields (responsibilities, required_skills, etc.) are stored as JSON
columns -- Postgres has native JSON support, no need for extra join tables
since these lists don't need independent querying yet.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from app.core.database import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(20), unique=True, nullable=False, index=True)

    title = Column(String(150), nullable=False)
    company = Column(String(150), nullable=False)
    location = Column(String(100), nullable=False)
    domain = Column(String(80), nullable=True, index=True)

    job_description = Column(Text, nullable=False)
    responsibilities = Column(JSON, nullable=False, default=list)
    required_skills = Column(JSON, nullable=False, default=list)
    preferred_skills = Column(JSON, nullable=False, default=list)
    qualifications = Column(JSON, nullable=False, default=list)

    experience_requirement = Column(String(255), nullable=True)
    education_requirement = Column(String(255), nullable=True)
    duration = Column(String(30), nullable=True)
    stipend_inr_per_month = Column(Integer, nullable=True)

    # When set (real, imported postings), the frontend's "Apply" button opens
    # this external URL in a new tab in addition to recording the internal
    # Application row -- so the student can genuinely apply, not just track.
    # Left null for the synthetic dataset (no real posting to link to).
    application_url = Column(String(500), nullable=True)
    source = Column(String(30), nullable=True, default="synthetic")  # "synthetic" | "kaggle_import"

    created_at = Column(DateTime, default=datetime.utcnow)
