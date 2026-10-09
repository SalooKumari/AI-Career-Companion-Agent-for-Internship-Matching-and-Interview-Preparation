"""
AI Chat Bot / Mock Interview agent.

Two ways to start a set:
1. Domain-general (job_posting_id not given): pick 25 questions (mix of
   technical + behavioral) from the curated interview_bank_questions table
   for a relevant domain, copy them into a new InterviewSet so the set
   stays stable even if the bank changes later.
2. Job-specific (job_posting_id given): reuse (or generate, if missing) a
   Skill-Gap-aware InterviewPrepPlan (M3.3) for that exact posting, and
   flatten its five question categories into one 25-ish-question mock
   interview set — so voice practice is grounded in that specific role's
   real requirements and the student's actual profile, not just their
   general domain.

Domain inference (domain-general path only): if the student doesn't pick a
domain, we use their most recent Job-Resume Match's job domain (Milestone 2)
as a reasonable default, falling back to "Software Engineering" if they
have no matches yet.

Feedback generation (both paths): after the student answers all questions,
build_qa_transcript + score_and_generate_feedback ask the LLM
(llm_service.generate_interview_feedback) for calibrated, grounded
feedback — strengths, improvements (each with why it matters and concrete
resources to work on it), an overall score, and personalized
recommendations.
"""
import random
from typing import Optional

from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.match import Match
from app.models.job_posting import JobPosting
from app.models.interview import InterviewBankQuestion, InterviewSet, InterviewSetQuestion
from app.models.interview_prep import InterviewPrepPlan
from app.services.llm_service import generate_interview_feedback

TECHNICAL_COUNT = 18
BEHAVIORAL_COUNT = 7
TOTAL_QUESTIONS = TECHNICAL_COUNT + BEHAVIORAL_COUNT

DEFAULT_DOMAIN = "Software Engineering"

# Maps an InterviewPrepPlan category -> the label used on InterviewSetQuestion.
# technical/behavioral is kept for the domain-general path; job-specific
# sets get the fuller M3.3 category set so the UI can show which kind of
# question it is (technical / resume-based / project-based / role-specific
# / HR) rather than collapsing everything into just two buckets.
PREP_CATEGORY_LABELS = {
    "technical_questions": "technical",
    "resume_based_questions": "resume_based",
    "project_based_questions": "project_based",
    "role_specific_questions": "role_specific",
    "hr_questions": "hr",
}


def infer_domain(db: Session, student: Student) -> str:
    latest_match = (
        db.query(Match)
        .filter(Match.student_id == student.id)
        .order_by(Match.created_at.desc())
        .first()
    )
    if latest_match and latest_match.job and latest_match.job.domain:
        return latest_match.job.domain
    return DEFAULT_DOMAIN


def generate_question_set(
    db: Session, student: Student, domain: Optional[str] = None, job_posting_id: Optional[int] = None,
) -> InterviewSet:
    if job_posting_id:
        return _generate_job_specific_set(db, student, job_posting_id)
    return _generate_domain_general_set(db, student, domain)


def _generate_job_specific_set(db: Session, student: Student, job_posting_id: int) -> InterviewSet:
    job = db.query(JobPosting).filter(JobPosting.id == job_posting_id).first()
    if not job:
        raise ValueError("Job posting not found.")

    plan = (
        db.query(InterviewPrepPlan)
        .filter(InterviewPrepPlan.student_id == student.id, InterviewPrepPlan.job_posting_id == job_posting_id)
        .first()
    )
    if not plan:
        # Generate one on the fly rather than making the student go to the
        # Application Toolkit first — same agent, just triggered here too.
        from app.services.interview_prep_agent import generate_prep_plan
        plan = generate_prep_plan(db, student, job)

    interview_set = InterviewSet(
        student_id=student.id,
        job_posting_id=job.id,
        domain=job.domain,
        status="in_progress",
        revision_topics=plan.revision_topics,
    )
    db.add(interview_set)
    db.flush()

    order_index = 1
    for plan_field, category_label in PREP_CATEGORY_LABELS.items():
        for item in (getattr(plan, plan_field) or []):
            db.add(InterviewSetQuestion(
                interview_set_id=interview_set.id,
                order_index=order_index,
                question_text=item.get("question", ""),
                category=category_label,
                prep_guidance=item.get("guidance"),
            ))
            order_index += 1

    interview_set.total_questions = order_index - 1
    db.commit()
    db.refresh(interview_set)
    return interview_set


def _generate_domain_general_set(db: Session, student: Student, domain: Optional[str]) -> InterviewSet:
    resolved_domain = domain or infer_domain(db, student)
    available_domains = [row[0] for row in db.query(InterviewBankQuestion.domain).distinct().all() if row[0]]
    canonical_domain = next(
        (candidate for candidate in available_domains if candidate.casefold() == resolved_domain.casefold()),
        None,
    )
    if canonical_domain is None:
        canonical_domain = next(
            (candidate for candidate in sorted(available_domains) if resolved_domain.casefold() in candidate.casefold()),
            None,
        )
    if canonical_domain:
        resolved_domain = canonical_domain

    technical_pool = (
        db.query(InterviewBankQuestion)
        .filter(InterviewBankQuestion.domain == resolved_domain, InterviewBankQuestion.category == "technical")
        .all()
    )
    behavioral_pool = (
        db.query(InterviewBankQuestion)
        .filter(InterviewBankQuestion.domain == resolved_domain, InterviewBankQuestion.category == "behavioral")
        .all()
    )

    # If a domain has too few technical questions in the bank, top up from
    # behavioral instead of failing — keeps this robust for any domain.
    tech_k = min(TECHNICAL_COUNT, len(technical_pool))
    picked_technical = random.sample(technical_pool, k=tech_k)

    behav_k = min(BEHAVIORAL_COUNT, len(behavioral_pool))
    picked_behavioral = random.sample(behavioral_pool, k=behav_k)

    picked = picked_technical + picked_behavioral
    shortfall = TOTAL_QUESTIONS - len(picked)
    if shortfall > 0:
        remaining_pool = [q for q in (technical_pool + behavioral_pool) if q not in picked]
        picked += random.sample(remaining_pool, k=min(shortfall, len(remaining_pool)))

    random.shuffle(picked)

    interview_set = InterviewSet(
        student_id=student.id,
        domain=resolved_domain,
        total_questions=len(picked),
        status="in_progress",
    )
    db.add(interview_set)
    db.flush()  # get interview_set.id before creating children

    for idx, bank_q in enumerate(picked, start=1):
        db.add(InterviewSetQuestion(
            interview_set_id=interview_set.id,
            order_index=idx,
            question_text=bank_q.question_text,
            category=bank_q.category,
        ))

    db.commit()
    db.refresh(interview_set)
    return interview_set


def build_qa_transcript(interview_set: InterviewSet) -> str:
    lines = []
    for q in sorted(interview_set.questions, key=lambda x: x.order_index):
        answer = q.answer_text.strip() if q.answer_text else "(no answer given)"
        lines.append(f"Q{q.order_index} [{q.category}]: {q.question_text}\nA{q.order_index}: {answer}")
    return "\n\n".join(lines)


def score_and_generate_feedback(student_profile_summary: str, interview_set: InterviewSet):
    """Calls the LLM once over the full transcript and returns an
    LLMInterviewFeedback object. Raises on LLM/parsing failure — the caller
    is responsible for handling that (see routers/interviews.py)."""
    transcript = build_qa_transcript(interview_set)
    job_context = None
    if interview_set.job:
        from app.services.matching_agent import build_job_posting_summary
        job_context = build_job_posting_summary(interview_set.job)
    return generate_interview_feedback(student_profile_summary, transcript, job_context)
