"""
Endpoints for saving/bookmarking a job posting — independent of applying
(M4: "View all saved jobs" navbar button).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_self
from app.models.student import Student
from app.models.saved_job import SavedJob
from app.models.job_posting import JobPosting
from app.schemas.saved_job import SavedJobCreate, SavedJobOut

router = APIRouter(prefix="/students/{student_id}", tags=["saved-jobs"])


@router.post("/saved-jobs", response_model=SavedJobOut, status_code=201)
def save_job(
    student_id: int,
    payload: SavedJobCreate,
    db: Session = Depends(get_db),
    current: Student = Depends(require_self),
):
    job = db.query(JobPosting).filter(JobPosting.id == payload.job_posting_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")

    existing = (
        db.query(SavedJob)
        .filter(SavedJob.student_id == student_id, SavedJob.job_posting_id == payload.job_posting_id)
        .first()
    )
    if existing:
        return existing  # already saved — idempotent

    saved = SavedJob(student_id=student_id, job_posting_id=payload.job_posting_id)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


@router.get("/saved-jobs", response_model=list[SavedJobOut])
def list_saved_jobs(
    student_id: int,
    db: Session = Depends(get_db),
    current: Student = Depends(require_self),
):
    return (
        db.query(SavedJob)
        .filter(SavedJob.student_id == student_id)
        .order_by(SavedJob.saved_at.desc())
        .all()
    )


@router.delete("/saved-jobs/{job_posting_id}", status_code=204)
def unsave_job(
    student_id: int,
    job_posting_id: int,
    db: Session = Depends(get_db),
    current: Student = Depends(require_self),
):
    saved = (
        db.query(SavedJob)
        .filter(SavedJob.student_id == student_id, SavedJob.job_posting_id == job_posting_id)
        .first()
    )
    if not saved:
        raise HTTPException(status_code=404, detail="This job isn't saved.")
    db.delete(saved)
    db.commit()
    return None
