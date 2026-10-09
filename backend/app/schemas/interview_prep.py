from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict

from app.schemas.job_posting import JobPostingSummary


class InterviewPrepRequest(BaseModel):
    job_posting_id: int


class PrepQuestion(BaseModel):
    question: str
    guidance: str


class InterviewPrepOut(BaseModel):
    id: int
    job: JobPostingSummary
    technical_questions: List[PrepQuestion] = []
    resume_based_questions: List[PrepQuestion] = []
    project_based_questions: List[PrepQuestion] = []
    role_specific_questions: List[PrepQuestion] = []
    hr_questions: List[PrepQuestion] = []
    revision_topics: List[str] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- LLM contract (internal) ----------

class LLMInterviewPrepResult(BaseModel):
    technical_questions: List[PrepQuestion] = []
    resume_based_questions: List[PrepQuestion] = []
    project_based_questions: List[PrepQuestion] = []
    role_specific_questions: List[PrepQuestion] = []
    hr_questions: List[PrepQuestion] = []
    revision_topics: List[str] = []
