"""
Interview Preparation Agent (M3.3) — job-specific prep plan.

Distinct from the general Mock Interview / AI Chat Bot (Milestone 2): that
one practices with a static question bank per domain. This one generates a
fresh plan grounded in one specific job posting's actual text, the
student's actual resume/projects, and (if one exists) their skill-gap
analysis for that same job — so revision topics reflect real gaps, not
generic advice.
"""
from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.job_posting import JobPosting
from app.models.skill_gap import SkillGapAnalysis
from app.models.interview_prep import InterviewPrepPlan
from app.services.matching_agent import build_student_profile_summary, build_job_posting_summary
from app.services.skill_gap_agent import build_skill_gap_summary_text
from app.services.llm_service import generate_interview_prep as llm_generate_prep


def generate_prep_plan(db: Session, student: Student, job: JobPosting) -> InterviewPrepPlan:
    profile_summary = build_student_profile_summary(student)
    job_summary = build_job_posting_summary(job)

    # Reuse an existing skill-gap analysis for this job if one exists —
    # grounds revision topics in the student's actual gaps instead of
    # guessing generically.
    existing_gap = (
        db.query(SkillGapAnalysis)
        .filter(SkillGapAnalysis.student_id == student.id, SkillGapAnalysis.job_posting_id == job.id)
        .first()
    )
    skill_gap_summary = build_skill_gap_summary_text(existing_gap) if existing_gap else ""

    result = llm_generate_prep(profile_summary, job_summary, skill_gap_summary)

    payload = dict(
        technical_questions=[q.model_dump() for q in result.technical_questions],
        resume_based_questions=[q.model_dump() for q in result.resume_based_questions],
        project_based_questions=[q.model_dump() for q in result.project_based_questions],
        role_specific_questions=[q.model_dump() for q in result.role_specific_questions],
        hr_questions=[q.model_dump() for q in result.hr_questions],
        revision_topics=result.revision_topics,
    )

    existing_plan = (
        db.query(InterviewPrepPlan)
        .filter(InterviewPrepPlan.student_id == student.id, InterviewPrepPlan.job_posting_id == job.id)
        .first()
    )

    if existing_plan:
        for key, value in payload.items():
            setattr(existing_plan, key, value)
        plan = existing_plan
    else:
        plan = InterviewPrepPlan(student_id=student.id, job_posting_id=job.id, **payload)
        db.add(plan)

    db.commit()
    db.refresh(plan)
    return plan
