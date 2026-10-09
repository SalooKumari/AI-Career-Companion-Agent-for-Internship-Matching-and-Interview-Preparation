"""
Skill Gap Analysis Agent (M3.1) — one saved analysis per (student, job)
pair. Re-running the analysis for the same job overwrites the previous row
(a student's profile keeps changing as they update skills/resume, so a
stale gap analysis isn't useful to keep around).
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class SkillGapAnalysis(Base):
    __tablename__ = "skill_gap_analyses"
    __table_args__ = (UniqueConstraint("student_id", "job_posting_id", name="uq_skill_gap_student_job"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False, index=True)

    # Each item: {"item": str, "why_it_matters": str}
    critical_gaps = Column(JSON, nullable=False, default=list)
    partial_gaps = Column(JSON, nullable=False, default=list)
    preferred_gaps = Column(JSON, nullable=False, default=list)
    # Plain strings — these read more like short notes than named "items"
    experience_gaps = Column(JSON, nullable=False, default=list)
    qualification_gaps = Column(JSON, nullable=False, default=list)
    recommendations = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="skill_gap_analyses")
    job = relationship("JobPosting")
