"""
Endpoints for running and reading the Job-Resume Matching Agent (M2.3) —
Dashboard 3 "Find Matching Internships".
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.student import Student
from app.models.match import Match
from app.schemas.match import MatchOut
from app.services.matching_agent import run_matching
from app.core.deps import require_self

router = APIRouter(prefix="/students", tags=["matching"])


@router.post("/{student_id}/matches", response_model=List[MatchOut])
def create_matches(
    student_id: int,
    top_k: int = Query(5, le=20),
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    """Runs the full pipeline: retrieve candidate jobs via RAG, score each
    with the LLM, rank, store, and return the top-k matches."""
    try:
        matches = run_matching(db, student_id, top_k=top_k)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Matching failed: {e}")

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="No matching jobs found — is the job posting knowledge base loaded? "
                   "Run seed_job_postings.py and then build_knowledge_base.py first.",
        )

    return matches


@router.get("/{student_id}/matches", response_model=List[MatchOut])
def get_matches(student_id: int, current: Student = Depends(require_self), db: Session = Depends(get_db)):
    """Returns the most recently computed matches for this student, without
    re-running the pipeline (fast — just reads stored rows)."""
    matches = (
        db.query(Match)
        .filter(Match.student_id == student_id)
        .order_by(Match.score.desc())
        .all()
    )
    return matches
