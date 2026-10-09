"""
Resume & Cover Letter Customization Agent (M3.2) — one row per (student,
job) pair holding both the tailored resume text and the cover letter text,
so a student has a single place to review/refine both for a given role.
Editable after generation (student review/refine — see routers/materials.py).
"""
from datetime import datetime

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class ApplicationMaterial(Base):
    __tablename__ = "application_materials"
    __table_args__ = (UniqueConstraint("student_id", "job_posting_id", name="uq_material_student_job"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False, index=True)

    resume_content = Column(Text, nullable=True)         # markdown-ish plain text, tailored resume
    cover_letter_content = Column(Text, nullable=True)    # plain text, tailored cover letter

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="application_materials")
    job = relationship("JobPosting")
