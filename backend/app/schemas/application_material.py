from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.job_posting import JobPostingSummary


class MaterialRequest(BaseModel):
    job_posting_id: int


class MaterialUpdate(BaseModel):
    """For the student to review/refine the generated text before using it."""
    resume_content: Optional[str] = None
    cover_letter_content: Optional[str] = None


class ApplicationMaterialOut(BaseModel):
    id: int
    job: JobPostingSummary
    resume_content: Optional[str] = None
    cover_letter_content: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- LLM contract (internal) ----------

class LLMApplicationMaterials(BaseModel):
    resume_content: str
    cover_letter_content: str
