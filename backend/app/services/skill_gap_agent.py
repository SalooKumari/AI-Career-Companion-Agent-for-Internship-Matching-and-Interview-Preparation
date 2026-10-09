"""
Skill Gap Analysis Agent (M3.1).

Compares a student's structured profile against one specific job posting
and saves a categorized gap analysis. Re-running for the same (student,
job) pair overwrites the previous analysis — see models/skill_gap.py for why.
"""
from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.job_posting import JobPosting
from app.models.skill_gap import SkillGapAnalysis
from app.services.matching_agent import build_student_profile_summary, build_job_posting_summary
from app.services.llm_service import analyze_skill_gap as llm_analyze_skill_gap


def run_skill_gap_analysis(db: Session, student: Student, job: JobPosting) -> SkillGapAnalysis:
    profile_summary = build_student_profile_summary(student)
    job_summary = build_job_posting_summary(job)

    result = llm_analyze_skill_gap(profile_summary, job_summary)

    existing = (
        db.query(SkillGapAnalysis)
        .filter(SkillGapAnalysis.student_id == student.id, SkillGapAnalysis.job_posting_id == job.id)
        .first()
    )

    payload = dict(
        critical_gaps=[g.model_dump() for g in result.critical_gaps],
        partial_gaps=[g.model_dump() for g in result.partial_gaps],
        preferred_gaps=[g.model_dump() for g in result.preferred_gaps],
        experience_gaps=result.experience_gaps,
        qualification_gaps=result.qualification_gaps,
        recommendations=result.recommendations,
    )

    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
        analysis = existing
    else:
        analysis = SkillGapAnalysis(student_id=student.id, job_posting_id=job.id, **payload)
        db.add(analysis)

    db.commit()
    db.refresh(analysis)
    return analysis


def build_skill_gap_summary_text(analysis: SkillGapAnalysis) -> str:
    """Short plain-text summary of a saved analysis, for feeding into the
    Interview Prep Agent (which uses skill gaps to pick revision topics)."""
    parts = []
    if analysis.critical_gaps:
        parts.append("Critical gaps: " + "; ".join(g["item"] for g in analysis.critical_gaps))
    if analysis.partial_gaps:
        parts.append("Partially demonstrated: " + "; ".join(g["item"] for g in analysis.partial_gaps))
    if analysis.experience_gaps:
        parts.append("Experience gaps: " + "; ".join(analysis.experience_gaps))
    if analysis.qualification_gaps:
        parts.append("Qualification gaps: " + "; ".join(analysis.qualification_gaps))
    return "\n".join(parts)
