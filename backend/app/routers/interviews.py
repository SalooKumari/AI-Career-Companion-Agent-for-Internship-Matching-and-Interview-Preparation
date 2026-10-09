"""
Endpoints for the AI Chat Bot / Mock Interview feature:
- start a new 25-question set (technical + behavioral, from the curated bank)
- submit voice-transcribed answers
- submit the completed set for AI feedback
- list / re-view past sets (the "saved interviews" history tab)
"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_self
from app.models.student import Student
from app.models.interview import InterviewSet, InterviewSetQuestion, InterviewFeedback
from app.schemas.interview import (
    InterviewSetCreate, InterviewSetOut, InterviewSetSummaryOut, AnswersSubmitBatch,
)
from app.services.interview_agent import generate_question_set, score_and_generate_feedback
from app.services.matching_agent import build_student_profile_summary

router = APIRouter(prefix="/students", tags=["interviews"])


@router.post("/{student_id}/interviews", response_model=InterviewSetOut, status_code=201)
def start_interview(
    student_id: int,
    payload: InterviewSetCreate,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    """Generates a new mock interview set for this student — domain-general
    (25 questions from the curated bank) or, when job_posting_id is given,
    grounded in that specific job's InterviewPrepPlan."""
    interview_set = generate_question_set(db, current, domain=payload.domain, job_posting_id=payload.job_posting_id)
    return interview_set


@router.get("/{student_id}/interviews", response_model=List[InterviewSetSummaryOut])
def list_interviews(
    student_id: int,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    """The 'saved interviews' history tab — past sets with their score if completed."""
    sets = (
        db.query(InterviewSet)
        .filter(InterviewSet.student_id == student_id)
        .order_by(InterviewSet.created_at.desc())
        .all()
    )
    out = []
    for s in sets:
        out.append(InterviewSetSummaryOut(
            id=s.id, domain=s.domain, job_posting_id=s.job_posting_id, status=s.status,
            created_at=s.created_at, completed_at=s.completed_at,
            overall_score=s.feedback.overall_score if s.feedback else None,
        ))
    return out


@router.get("/{student_id}/interviews/{interview_id}", response_model=InterviewSetOut)
def get_interview(
    student_id: int,
    interview_id: int,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    interview_set = (
        db.query(InterviewSet)
        .filter(InterviewSet.id == interview_id, InterviewSet.student_id == student_id)
        .first()
    )
    if not interview_set:
        raise HTTPException(status_code=404, detail="Interview set not found.")
    return interview_set


@router.post("/{student_id}/interviews/{interview_id}/answers", response_model=InterviewSetOut)
def submit_answers(
    student_id: int,
    interview_id: int,
    payload: AnswersSubmitBatch,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    """Saves one or more voice-transcribed answers. Can be called once per
    question (as the student answers each one) or in a batch at the end."""
    interview_set = (
        db.query(InterviewSet)
        .filter(InterviewSet.id == interview_id, InterviewSet.student_id == student_id)
        .first()
    )
    if not interview_set:
        raise HTTPException(status_code=404, detail="Interview set not found.")
    if interview_set.status == "completed":
        raise HTTPException(status_code=400, detail="This interview set has already been submitted for feedback.")

    question_by_id = {q.id: q for q in interview_set.questions}
    for ans in payload.answers:
        question = question_by_id.get(ans.question_id)
        if not question:
            raise HTTPException(status_code=400, detail=f"Question {ans.question_id} is not part of this interview set.")
        question.answer_text = ans.answer_text
        question.answered_at = datetime.utcnow()

    db.commit()
    db.refresh(interview_set)
    return interview_set


@router.post("/{student_id}/interviews/{interview_id}/submit", response_model=InterviewSetOut)
def submit_interview(
    student_id: int,
    interview_id: int,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    """Finalizes the set: sends the full Q&A transcript to the LLM for
    feedback, stores it, and marks the set completed."""
    interview_set = (
        db.query(InterviewSet)
        .filter(InterviewSet.id == interview_id, InterviewSet.student_id == student_id)
        .first()
    )
    if not interview_set:
        raise HTTPException(status_code=404, detail="Interview set not found.")
    if interview_set.status == "completed":
        return interview_set

    answered_count = sum(1 for q in interview_set.questions if q.answer_text)
    if answered_count == 0:
        raise HTTPException(status_code=400, detail="Answer at least one question before submitting for feedback.")

    profile_summary = build_student_profile_summary(current)

    try:
        result = score_and_generate_feedback(profile_summary, interview_set)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Feedback generation failed: {e}")

    feedback = InterviewFeedback(
        interview_set_id=interview_set.id,
        overall_score=result.overall_score,
        strengths=result.strengths,
        improvements=[imp.model_dump() for imp in result.improvements],
        recommendations=result.recommendations,
    )
    db.add(feedback)
    interview_set.status = "completed"
    interview_set.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(interview_set)
    return interview_set
