"""
Endpoints for tracking which internships a student has applied to — the
full Application Tracking Module (M4.1): status lifecycle, interview
scheduling, deadline reminders, notes, search/filter, and an overview-stats
endpoint for the tracker's summary dashboard.
"""
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_self
from app.models.application import Application, APPLICATION_STATUSES, ACTIVE_STATUSES
from app.models.job_posting import JobPosting
from app.models.student import Student
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationOut, ApplicationStatsOut

router = APIRouter(prefix="/students", tags=["applications"])

# How far ahead a deadline counts as "upcoming" for the stats overview —
# kept in sync with routers/notifications.py's own lookahead window.
STATS_DEADLINE_LOOKAHEAD_DAYS = 5


@router.post("/{student_id}/applications", response_model=ApplicationOut, status_code=201)
def apply_to_job(
    student_id: int,
    payload: ApplicationCreate,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    job = db.query(JobPosting).filter(JobPosting.id == payload.job_posting_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")

    existing = (
        db.query(Application)
        .filter(Application.student_id == student_id, Application.job_posting_id == payload.job_posting_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="You've already applied to this internship.")

    application = Application(
        student_id=student_id,
        job_posting_id=payload.job_posting_id,
        deadline=payload.deadline,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/{student_id}/applications", response_model=List[ApplicationOut])
def list_applications(
    student_id: int,
    status: Optional[str] = Query(None, description="Filter by exact status, e.g. 'interview_scheduled'. Omit for all."),
    search: Optional[str] = Query(None, description="Case-insensitive match against company name or job title."),
    sort_by: str = Query("applied_at", description="'applied_at' (default), 'deadline', or 'interview_date'."),
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    query = db.query(Application).filter(Application.student_id == student_id)

    if status:
        if status not in APPLICATION_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown status '{status}'. Valid values: {', '.join(APPLICATION_STATUSES)}",
            )
        query = query.filter(Application.status == status)

    if search:
        like = f"%{search.strip()}%"
        query = query.join(JobPosting).filter(
            (JobPosting.company.ilike(like)) | (JobPosting.title.ilike(like))
        )

    applications = query.all()

    if sort_by == "deadline":
        applications.sort(key=lambda a: (a.deadline is None, a.deadline or date.min))
    elif sort_by == "interview_date":
        applications.sort(key=lambda a: (a.interview_date is None, a.interview_date or date.min))
    else:
        applications.sort(key=lambda a: a.applied_at, reverse=True)

    return applications


@router.get("/{student_id}/applications/stats", response_model=ApplicationStatsOut)
def application_stats(
    student_id: int,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    """Overview counters for the tracker dashboard: total, active,
    upcoming deadlines, interviews scheduled, offers received, rejected."""
    applications = db.query(Application).filter(Application.student_id == student_id).all()

    today = date.today()
    cutoff = today + timedelta(days=STATS_DEADLINE_LOOKAHEAD_DAYS)

    total = len(applications)
    active = sum(1 for a in applications if a.status in ACTIVE_STATUSES)
    upcoming_deadlines = sum(
        1 for a in applications
        if a.deadline and today <= a.deadline <= cutoff and a.status in ACTIVE_STATUSES
    )
    interviews_scheduled = sum(1 for a in applications if a.status == "interview_scheduled")
    offers_received = sum(1 for a in applications if a.status == "offer_received")
    rejected = sum(1 for a in applications if a.status == "rejected")

    return ApplicationStatsOut(
        total=total,
        active=active,
        upcoming_deadlines=upcoming_deadlines,
        interviews_scheduled=interviews_scheduled,
        offers_received=offers_received,
        rejected=rejected,
    )


@router.get("/{student_id}/applications/statuses", response_model=List[str])
def list_application_statuses(student_id: int, current: Student = Depends(require_self)):
    """The valid status values, for the frontend's filter/status-change dropdowns."""
    return APPLICATION_STATUSES


@router.patch("/{student_id}/applications/{application_id}", response_model=ApplicationOut)
def update_application(
    student_id: int,
    application_id: int,
    payload: ApplicationUpdate,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    """Change status (e.g. applied -> interview_scheduled -> offer_received),
    set/change the reminder deadline or interview date, or add notes. Any
    field left out of the request body is left unchanged."""
    application = (
        db.query(Application)
        .filter(Application.id == application_id, Application.student_id == student_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    if payload.status is not None:
        if payload.status not in APPLICATION_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown status '{payload.status}'. Valid values: {', '.join(APPLICATION_STATUSES)}",
            )
        application.status = payload.status

    if payload.deadline is not None:
        application.deadline = payload.deadline

    if payload.interview_date is not None:
        application.interview_date = payload.interview_date

    if payload.notes is not None:
        application.notes = payload.notes

    db.commit()
    db.refresh(application)
    return application


@router.delete("/{student_id}/applications/{application_id}", status_code=204)
def withdraw_application(
    student_id: int,
    application_id: int,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    """Hard-delete. For most cases prefer PATCH status='withdrawn' instead,
    which keeps the application visible in history — this is here for a
    student who wants it gone entirely (e.g. applied to the wrong posting)."""
    application = (
        db.query(Application)
        .filter(Application.id == application_id, Application.student_id == student_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")
    db.delete(application)
    db.commit()
    return None
