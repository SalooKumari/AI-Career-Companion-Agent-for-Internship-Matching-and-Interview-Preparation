"""
SQLAlchemy model for a student's internship applications — Dashboard 4
"Applied Internships" and the full Application Tracking Module (M4.1):
status lifecycle, interview scheduling, deadline reminders, notes, and a
link back to any tailored resume/cover letter generated for this job.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

# Valid status values (checked in the router, not a DB-level enum, so new
# statuses can be added later without a migration). Ordered roughly as the
# lifecycle progresses; "rejected" and "withdrawn" are terminal exits that
# can happen from any earlier stage.
#   applied              — just submitted (default)
#   under_review         — application acknowledged / being reviewed, no decision yet
#   shortlisted          — moved forward before an interview is scheduled
#   interview_scheduled  — an interview date is set (see Application.interview_date)
#   interview_completed  — the interview happened, awaiting a decision
#   offer_received       — got the offer
#   rejected             — the company passed, at any stage
#   withdrawn            — the student pulled their own application
APPLICATION_STATUSES = [
    "applied", "under_review", "shortlisted", "interview_scheduled",
    "interview_completed", "offer_received", "rejected", "withdrawn",
]

# Statuses that still count as an open/active application (for the
# tracker's overview stats) — i.e. not yet at a terminal outcome.
ACTIVE_STATUSES = ["applied", "under_review", "shortlisted", "interview_scheduled", "interview_completed"]


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    status = Column(String(30), default="applied")
    applied_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Student-set reminder date for this application's own deadline (e.g. a
    # "follow up by" date, or a deadline they noted from the original
    # posting) — used to power the notification bell (M4.1). Nullable: we
    # never invent a deadline the student didn't provide.
    deadline = Column(Date, nullable=True)

    # Separate from `deadline` — when the student has (or is scheduling)
    # an actual interview for this application. Also feeds the
    # notification bell, labeled distinctly from the deadline reminder.
    interview_date = Column(Date, nullable=True)

    notes = Column(Text, nullable=True)  # free-text student notes (e.g. "recruiter: Priya, referred by Aman")

    student = relationship("Student", back_populates="applications")
    job = relationship("JobPosting")
