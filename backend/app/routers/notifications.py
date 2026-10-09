"""
Deadline and interview-date reminder notifications for the navbar bell
(M4.1). Computed on the fly from applications that have a student-set
deadline and/or interview date — not a stored/stateful notification system
(no "mark as read"), which keeps this simple and always accurate to the
current applications table.
"""
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_self
from app.models.application import Application, ACTIVE_STATUSES
from app.models.student import Student
from app.schemas.notification import NotificationOut

router = APIRouter(prefix="/students", tags=["notifications"])

# How far ahead to surface a date at all. Overdue ones are always included
# regardless of how long ago they passed.
LOOKAHEAD_DAYS = 5


def _urgency(days_remaining: int) -> str:
    if days_remaining < 0:
        return "overdue"
    if days_remaining == 0:
        return "today"
    if days_remaining == 1:
        return "tomorrow"
    return "this_week"


def _message(kind: str, days_remaining: int, job_title: str, company: str) -> str:
    label = "Interview" if kind == "interview" else "Deadline"
    if days_remaining < 0:
        return f"{label} was {abs(days_remaining)} day(s) ago for {job_title} at {company}."
    if days_remaining == 0:
        return f"{label} is today for {job_title} at {company}."
    if days_remaining == 1:
        return f"{label} is tomorrow for {job_title} at {company}."
    return f"{label} in {days_remaining} days for {job_title} at {company}."


@router.get("/{student_id}/notifications", response_model=List[NotificationOut])
def list_notifications(
    student_id: int,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    today = date.today()
    cutoff = today + timedelta(days=LOOKAHEAD_DAYS)

    applications = (
        db.query(Application)
        .filter(
            Application.student_id == student_id,
            Application.status.in_(ACTIVE_STATUSES),
        )
        .all()
    )

    notifications = []
    for app_row in applications:
        if not app_row.job:
            continue

        if app_row.deadline and app_row.deadline <= cutoff:
            days_remaining = (app_row.deadline - today).days
            notifications.append(NotificationOut(
                application_id=app_row.id,
                job_title=app_row.job.title,
                company=app_row.job.company,
                kind="deadline",
                date=app_row.deadline,
                days_remaining=days_remaining,
                urgency=_urgency(days_remaining),
                message=_message("deadline", days_remaining, app_row.job.title, app_row.job.company),
                status=app_row.status,
                job_posting_id=app_row.job_posting_id,
            ))

        if app_row.interview_date and app_row.interview_date <= cutoff:
            days_remaining = (app_row.interview_date - today).days
            notifications.append(NotificationOut(
                application_id=app_row.id,
                job_title=app_row.job.title,
                company=app_row.job.company,
                kind="interview",
                date=app_row.interview_date,
                days_remaining=days_remaining,
                urgency=_urgency(days_remaining),
                message=_message("interview", days_remaining, app_row.job.title, app_row.job.company),
                status=app_row.status,
                job_posting_id=app_row.job_posting_id,
            ))

    notifications.sort(key=lambda n: n.date)
    return notifications
