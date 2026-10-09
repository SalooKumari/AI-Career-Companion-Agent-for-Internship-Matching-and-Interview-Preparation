from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.job_posting import JobPostingSummary


class ApplicationCreate(BaseModel):
    job_posting_id: int
    deadline: Optional[date] = None  # optional reminder date the student sets when applying


class ApplicationUpdate(BaseModel):
    """Partial update — status change, deadline/interview date set or
    change, or notes. Any field left out is left unchanged."""
    status: Optional[str] = None
    deadline: Optional[date] = None
    interview_date: Optional[date] = None
    notes: Optional[str] = None


class ApplicationOut(BaseModel):
    id: int
    job: JobPostingSummary
    status: str
    applied_at: datetime
    updated_at: datetime
    deadline: Optional[date] = None
    interview_date: Optional[date] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationStatsOut(BaseModel):
    """Overview counters for the Application Tracking dashboard (M4.1)."""
    total: int
    active: int
    upcoming_deadlines: int
    interviews_scheduled: int
    offers_received: int
    rejected: int
