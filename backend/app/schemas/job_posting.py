"""
Pydantic schemas for job postings — request/response shapes for the
/jobs endpoints and for semantic search results (M2.1 + M2.2).
Field names mirror docs/job_posting_schema.md exactly.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class JobPostingOut(BaseModel):
    id: int
    job_id: str
    title: str
    company: str
    location: str
    domain: Optional[str] = None
    job_description: str
    responsibilities: List[str] = []
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    qualifications: List[str] = []
    experience_requirement: Optional[str] = None
    education_requirement: Optional[str] = None
    duration: Optional[str] = None
    stipend_inr_per_month: Optional[int] = None
    application_url: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobPostingSummary(BaseModel):
    """Lightweight version used inside search/match/application results."""
    id: int
    job_id: str
    title: str
    company: str
    location: str
    domain: Optional[str] = None
    application_url: Optional[str] = None  # if set, "Apply" opens the real posting
    source: Optional[str] = None  # "kaggle_import" -> shown as a "Real posting" badge

    model_config = ConfigDict(from_attributes=True)


class SemanticSearchResult(BaseModel):
    job: JobPostingSummary
    similarity: float
    matched_chunk_type: str
