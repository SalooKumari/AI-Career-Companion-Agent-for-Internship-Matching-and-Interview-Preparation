"""Endpoints for the job-specific Interview Preparation Agent (M3.3)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_self
from app.models.student import Student
from app.models.job_posting import JobPosting
from app.models.interview_prep import InterviewPrepPlan
from app.schemas.interview_prep import InterviewPrepRequest, InterviewPrepOut
from app.services.interview_prep_agent import generate_prep_plan

router = APIRouter(prefix="/students", tags=["interview-prep"])


@router.post("/{student_id}/interview-prep", response_model=InterviewPrepOut, status_code=201)
def generate_prep(
    student_id: int,
    payload: InterviewPrepRequest,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    job = db.query(JobPosting).filter(JobPosting.id == payload.job_posting_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")

    try:
        plan = generate_prep_plan(db, current, job)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Interview prep generation failed: {e}")

    return plan


@router.get("/{student_id}/interview-prep/{job_posting_id}", response_model=InterviewPrepOut)
def get_prep(
    student_id: int,
    job_posting_id: int,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    plan = (
        db.query(InterviewPrepPlan)
        .filter(InterviewPrepPlan.student_id == student_id, InterviewPrepPlan.job_posting_id == job_posting_id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="No interview prep plan for this job yet.")
    return plan
