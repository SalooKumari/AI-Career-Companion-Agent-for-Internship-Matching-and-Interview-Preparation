from datetime import date
from typing import Optional

from pydantic import BaseModel


class NotificationOut(BaseModel):
    """Computed on the fly from applications with an upcoming deadline or
    interview date — not a stored row (see routers/notifications.py).
    kind is "deadline" | "interview". urgency is one of:
    "overdue" | "today" | "tomorrow" | "this_week" (2-5 days out)."""
    application_id: int
    job_title: str
    company: str
    kind: str
    date: date
    days_remaining: int
    urgency: str
    message: str
    status: str
    job_posting_id: int
