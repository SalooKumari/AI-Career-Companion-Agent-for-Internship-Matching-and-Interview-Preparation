from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.job_posting import JobPostingSummary


class SavedJobCreate(BaseModel):
    job_posting_id: int


class SavedJobOut(BaseModel):
    id: int
    job: JobPostingSummary
    saved_at: datetime

    model_config = ConfigDict(from_attributes=True)
