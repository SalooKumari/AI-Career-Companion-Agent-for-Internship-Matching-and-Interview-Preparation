from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ChatMessageIn(BaseModel):
    message: str
    job_posting_id: Optional[int] = None  # lets the UI say "I'm asking about this job"


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    job_posting_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatReplyOut(BaseModel):
    """Returned after posting a message: the assistant's new reply, plus
    the full updated history so the frontend can just re-render."""
    reply: ChatMessageOut
    history: List[ChatMessageOut]
