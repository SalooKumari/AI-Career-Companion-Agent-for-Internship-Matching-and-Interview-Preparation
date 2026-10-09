"""
Match: one Job-Resume Matching Agent result — a student x job posting pair
with a compatibility score and the agent's reasoning (M2.3).
Stored (not just computed on the fly) so results can be viewed later and
so M2.4 evaluation has something concrete to inspect/compare.

M4.3 adds a score breakdown (skills / education / projects / domain fit)
alongside the overall score, so the student can see *what* drove a match's
score, not just the number — see services/matching_agent.py and
llm_service.score_job_match for how each factor is computed.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False, index=True)

    score = Column(Integer, nullable=False)                 # 0-100 overall compatibility score
    matched_skills = Column(JSON, nullable=False, default=list)   # list[str]
    missing_skills = Column(JSON, nullable=False, default=list)   # list[str]
    reasoning = Column(Text, nullable=False)

    # Score breakdown (each 0-100), added M4.3. Nullable so old rows (or a
    # re-run against an older LLM response) don't break — the frontend
    # falls back to just the overall score when these are absent.
    skills_score = Column(Integer, nullable=True)
    education_score = Column(Integer, nullable=True)   # education/CGPA fit against the role's requirement
    project_score = Column(Integer, nullable=True)      # relevance of the student's projects to the role
    domain_fit_score = Column(Integer, nullable=True)   # how well the role's domain matches the student's trajectory

    retrieval_rank = Column(Integer, nullable=True)  # position returned by the RAG retrieval step, before re-ranking
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("JobPosting")
