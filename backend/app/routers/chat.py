"""Endpoints for the Conversational Career Assistant (M3.4)."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_self
from app.models.student import Student
from app.models.job_posting import JobPosting
from app.models.chat import ChatMessage
from app.schemas.chat import ChatMessageIn, ChatMessageOut, ChatReplyOut
from app.services.career_assistant import send_message

router = APIRouter(prefix="/students", tags=["career-assistant"])


@router.get("/{student_id}/chat", response_model=List[ChatMessageOut])
def get_history(
    student_id: int,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.student_id == student_id)
        .order_by(ChatMessage.created_at)
        .all()
    )


@router.post("/{student_id}/chat", response_model=ChatReplyOut)
def post_message(
    student_id: int,
    payload: ChatMessageIn,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    job: Optional[JobPosting] = None
    if payload.job_posting_id is not None:
        job = db.query(JobPosting).filter(JobPosting.id == payload.job_posting_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job posting not found.")

    try:
        assistant_msg = send_message(db, current, payload.message, job)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Career Assistant failed to reply: {e}")

    full_history = (
        db.query(ChatMessage)
        .filter(ChatMessage.student_id == student_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return ChatReplyOut(reply=assistant_msg, history=full_history)
