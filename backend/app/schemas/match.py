from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.job_posting import JobPostingSummary


class MatchOut(BaseModel):
    id: int
    job: JobPostingSummary
    score: int
    skills_score: Optional[int] = None
    education_score: Optional[int] = None
    project_score: Optional[int] = None
    domain_fit_score: Optional[int] = None
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    reasoning: str
    retrieval_rank: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LLMMatchResult(BaseModel):
    """Exact JSON shape the LLM is asked to return when scoring one job
    against one profile. `score` is the LLM's own holistic overall score;
    the four factor scores are a breakdown of what drove it, each 0-100."""
    score: int
    skills_score: int
    education_score: int
    project_score: int
    domain_fit_score: int
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    reasoning: str
