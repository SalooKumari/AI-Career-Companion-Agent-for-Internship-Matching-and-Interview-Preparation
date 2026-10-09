from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict

from app.schemas.job_posting import JobPostingSummary


class SkillGapRequest(BaseModel):
    job_posting_id: int


class GapItem(BaseModel):
    item: str
    why_it_matters: str


class SkillGapOut(BaseModel):
    id: int
    job: JobPostingSummary
    critical_gaps: List[GapItem] = []
    partial_gaps: List[GapItem] = []
    preferred_gaps: List[GapItem] = []
    experience_gaps: List[str] = []
    qualification_gaps: List[str] = []
    recommendations: List[str] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- LLM contract (internal) ----------

class LLMSkillGapResult(BaseModel):
    critical_gaps: List[GapItem] = []
    partial_gaps: List[GapItem] = []
    preferred_gaps: List[GapItem] = []
    experience_gaps: List[str] = []
    qualification_gaps: List[str] = []
    recommendations: List[str] = []
