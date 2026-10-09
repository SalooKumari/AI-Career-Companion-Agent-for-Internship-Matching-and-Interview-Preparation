"""
Conversational Career Assistant (M3.4) — a flat, ordered message log per
student (one continuous thread, not multiple named sessions — matches
"ongoing guidance" from the brief). job_posting_id is an optional pointer
to which internship a given turn was about, so the assistant/context
builder can favor recently-discussed jobs without re-parsing message text.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="chat_messages")
    job = relationship("JobPosting")
