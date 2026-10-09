"""
Interview Preparation Agent (M3.3) — one saved prep plan per (student, job)
pair. Distinct from the AI Chat Bot / Mock Interview feature (Milestone 2,
app.models.interview): that one draws from a static, domain-organized
question bank for general practice; this one is generated fresh per
specific job posting, grounded in that posting's actual text, the
student's actual resume/projects, and their skill-gap analysis for that
role (see services/interview_prep_agent.py for how those are combined).
"""
from datetime import datetime

from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class InterviewPrepPlan(Base):
    __tablename__ = "interview_prep_plans"
    __table_args__ = (UniqueConstraint("student_id", "job_posting_id", name="uq_prep_student_job"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False, index=True)

    # Each item: {"question": str, "guidance": str}
    technical_questions = Column(JSON, nullable=False, default=list)
    resume_based_questions = Column(JSON, nullable=False, default=list)
    project_based_questions = Column(JSON, nullable=False, default=list)
    role_specific_questions = Column(JSON, nullable=False, default=list)
    hr_questions = Column(JSON, nullable=False, default=list)
    # Plain strings
    revision_topics = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="interview_prep_plans")
    job = relationship("JobPosting")
