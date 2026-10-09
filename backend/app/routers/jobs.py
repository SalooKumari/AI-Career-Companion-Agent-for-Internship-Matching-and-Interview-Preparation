"""
Endpoints for browsing the internship knowledge base and testing the
RAG semantic search directly (M2.1 + M2.2).
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job_posting import JobPosting
from app.schemas.job_posting import JobPostingOut, SemanticSearchResult, JobPostingSummary
from app.services.vector_store import semantic_search

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=List[JobPostingOut])
def list_jobs(
    domain: Optional[str] = Query(None, description="Filter by domain, e.g. 'Data Science & Analytics'"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(JobPosting)
    if domain:
        query = query.filter(JobPosting.domain == domain)
    return query.order_by(JobPosting.id).limit(limit).all()


@router.get("/domains", response_model=List[str])
def list_domains(db: Session = Depends(get_db)):
    rows = db.query(JobPosting.domain).distinct().all()
    return sorted({r[0] for r in rows if r[0]})


@router.get("/search", response_model=List[SemanticSearchResult])
def search_jobs(
    q: str = Query(..., description="Natural-language query, e.g. 'machine learning internship using Python'"),
    top_k: int = Query(5, le=25),
    db: Session = Depends(get_db),
):
    """Direct RAG retrieval test endpoint (M2.2) — lets you sanity-check
    that a natural-language query surfaces relevant postings, without
    going through the full Matching Agent / LLM scoring step."""
    hits = semantic_search(q, top_k_jobs=top_k)

    results = []
    for hit in hits:
        job = db.query(JobPosting).filter(JobPosting.id == hit["job_posting_id"]).first()
        if job is None:
            continue
        results.append(SemanticSearchResult(
            job=JobPostingSummary.model_validate(job),
            similarity=hit["similarity"],
            matched_chunk_type=hit["matched_chunk_type"],
        ))
    return results


@router.get("/{job_pk}", response_model=JobPostingOut)
def get_job(job_pk: int, db: Session = Depends(get_db)):
    job = db.query(JobPosting).filter(JobPosting.id == job_pk).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")
    return job
