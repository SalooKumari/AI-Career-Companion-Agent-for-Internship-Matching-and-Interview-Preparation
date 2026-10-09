"""Endpoints for the Skill Gap Analysis Agent (M3.1)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_self
from app.models.student import Student
from app.models.job_posting import JobPosting
from app.models.skill_gap import SkillGapAnalysis
from app.schemas.skill_gap import SkillGapRequest, SkillGapOut
from app.services.skill_gap_agent import run_skill_gap_analysis

router = APIRouter(prefix="/students", tags=["skill-gap"])


@router.post("/{student_id}/skill-gap", response_model=SkillGapOut, status_code=201)
def analyze_gap(
    student_id: int,
    payload: SkillGapRequest,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    job = db.query(JobPosting).filter(JobPosting.id == payload.job_posting_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")

    try:
        analysis = run_skill_gap_analysis(db, current, job)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Skill gap analysis failed: {e}")

    return analysis


@router.get("/{student_id}/skill-gap/{job_posting_id}", response_model=SkillGapOut)
def get_gap(
    student_id: int,
    job_posting_id: int,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    analysis = (
        db.query(SkillGapAnalysis)
        .filter(SkillGapAnalysis.student_id == student_id, SkillGapAnalysis.job_posting_id == job_posting_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="No skill gap analysis for this job yet.")
    return analysis
