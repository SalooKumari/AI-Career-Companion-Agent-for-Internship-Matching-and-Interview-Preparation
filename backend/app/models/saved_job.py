"""
SavedJob — a lightweight bookmark, separate from Application. A student can
save a posting to look at later without having applied to it yet (M4: "View
all saved jobs" navbar button). Saving and applying are independent: a job
can be saved, applied, both, or neither.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class SavedJob(Base):
    __tablename__ = "saved_jobs"
    __table_args__ = (UniqueConstraint("student_id", "job_posting_id", name="uq_saved_student_job"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False, index=True)
    saved_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="saved_jobs")
    job = relationship("JobPosting")
