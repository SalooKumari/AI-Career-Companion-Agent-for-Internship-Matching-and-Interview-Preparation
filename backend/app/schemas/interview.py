from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class InterviewSetCreate(BaseModel):
    domain: Optional[str] = None  # if omitted (and no job_posting_id), inferred from the student's top match
    job_posting_id: Optional[int] = None  # if set, draws from that job's InterviewPrepPlan instead of the domain bank


class InterviewSetQuestionOut(BaseModel):
    id: int
    order_index: int
    question_text: str
    category: Optional[str] = None
    prep_guidance: Optional[str] = None
    answer_text: Optional[str] = None
    answered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ImprovementAreaOut(BaseModel):
    area: str
    why_it_matters: str
    resources: List[str] = []


class InterviewFeedbackOut(BaseModel):
    overall_score: int
    strengths: List[str] = []
    improvements: List[ImprovementAreaOut] = []
    recommendations: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewSetOut(BaseModel):
    id: int
    domain: Optional[str] = None
    job_posting_id: Optional[int] = None
    total_questions: int
    status: str
    revision_topics: Optional[List[str]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    questions: List[InterviewSetQuestionOut] = []
    feedback: Optional[InterviewFeedbackOut] = None

    model_config = ConfigDict(from_attributes=True)


class InterviewSetSummaryOut(BaseModel):
    """Lightweight version for the history/list view."""
    id: int
    domain: Optional[str] = None
    job_posting_id: Optional[int] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    overall_score: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: str


class AnswersSubmitBatch(BaseModel):
    answers: List[AnswerSubmit]


# ---------- LLM feedback contract (internal) ----------

class LLMImprovementArea(BaseModel):
    area: str
    why_it_matters: str
    resources: List[str] = []


class LLMInterviewFeedback(BaseModel):
    overall_score: int
    strengths: List[str] = []
    improvements: List[LLMImprovementArea] = []
    recommendations: str
