"""
Models for the AI Chat Bot / Mock Interview feature.

- InterviewBankQuestion: the master question library (curated, domain-organized —
  see database/generate_interview_questions.py for how it's built and why).
- InterviewSet: one 25-question mock interview attempt by a student. Can be
  domain-general (job_posting_id is null, questions drawn from the bank) or
  job-specific (job_posting_id set, questions drawn from that job's
  InterviewPrepPlan if one exists — see M3.3 / services/interview_agent.py).
- InterviewSetQuestion: a single question within a set, plus the student's
  voice-transcribed answer once they've answered it. Question text is
  copied from the source (bank or prep plan) at generation time so a set
  stays stable even if the source is regenerated later. prep_guidance is
  only populated for job-specific sets (carried over from the prep plan).
- InterviewFeedback: the AI-generated feedback for a completed set (one row
  per set).

Note: the job-specific Interview Prep Plan (M3.3) is a separate model in
app.models.interview_prep.InterviewPrepPlan — not defined here, to avoid a
duplicate/conflicting mapping of the same table.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class InterviewBankQuestion(Base):
    __tablename__ = "interview_bank_questions"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(80), nullable=False, index=True)
    category = Column(String(30), nullable=False)  # "technical" | "behavioral"
    question_text = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=True)  # "easy" | "medium" | "hard"


class InterviewSet(Base):
    __tablename__ = "interview_sets"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True, index=True)
    domain = Column(String(80), nullable=True)
    total_questions = Column(Integer, default=25)
    status = Column(String(20), default="in_progress")  # in_progress | completed
    revision_topics = Column(JSON, nullable=True)  # carried over from the InterviewPrepPlan, if job-specific
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="interview_sets")
    job = relationship("JobPosting")
    questions = relationship(
        "InterviewSetQuestion", back_populates="interview_set",
        cascade="all, delete-orphan", order_by="InterviewSetQuestion.order_index",
    )
    feedback = relationship(
        "InterviewFeedback", back_populates="interview_set",
        uselist=False, cascade="all, delete-orphan",
    )


class InterviewSetQuestion(Base):
    __tablename__ = "interview_set_questions"

    id = Column(Integer, primary_key=True, index=True)
    interview_set_id = Column(Integer, ForeignKey("interview_sets.id"), nullable=False, index=True)
    order_index = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    category = Column(String(30), nullable=True)
    prep_guidance = Column(Text, nullable=True)  # only set for job-specific sets (from the prep plan)
    answer_text = Column(Text, nullable=True)
    answered_at = Column(DateTime, nullable=True)

    interview_set = relationship("InterviewSet", back_populates="questions")


class InterviewFeedback(Base):
    __tablename__ = "interview_feedback"

    id = Column(Integer, primary_key=True, index=True)
    interview_set_id = Column(Integer, ForeignKey("interview_sets.id"), unique=True, nullable=False)
    overall_score = Column(Integer, nullable=False)  # 0-100
    strengths = Column(JSON, nullable=False, default=list)
    improvements = Column(JSON, nullable=False, default=list)
    recommendations = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    interview_set = relationship("InterviewSet", back_populates="feedback")

