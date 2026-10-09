"""
Conversational Career Assistant (M3.4).

Ties together the outputs of the other agents (Matching, Skill Gap,
Application Materials, Interview Prep) plus the RAG job-posting knowledge
base as context for a free-form chat, and maintains a flat per-student
message history so the conversation stays contextual across turns.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.job_posting import JobPosting
from app.models.match import Match
from app.models.chat import ChatMessage
from app.models.skill_gap import SkillGapAnalysis
from app.models.application_material import ApplicationMaterial
from app.models.interview_prep import InterviewPrepPlan
from app.services.matching_agent import build_student_profile_summary, build_job_posting_summary
from app.services.skill_gap_agent import build_skill_gap_summary_text
from app.services.vector_store import semantic_search
from app.services.llm_service import career_assistant_reply as llm_chat_reply

MAX_HISTORY_MESSAGES = 20  # keep recent context bounded — this is a chat, not the whole transcript forever
RAG_FALLBACK_TOP_K = 4  # postings surfaced via semantic search when no specific job is selected


def build_context_block(db: Session, student: Student, job: Optional[JobPosting], message: str) -> str:
    parts = [build_student_profile_summary(student)]

    if student.resume and student.resume.raw_text:
        # Full raw resume text (not just the structured profile above) so
        # the assistant can critique actual wording/sections when asked,
        # not just discuss extracted skills/education/experience.
        parts.append(f"STUDENT'S RAW RESUME TEXT (as uploaded/parsed):\n{student.resume.raw_text}")
    else:
        parts.append("STUDENT HAS NOT UPLOADED A RESUME YET — if they ask for resume feedback, "
                      "tell them to upload one on the Resume dashboard first.")

    recent_matches = (
        db.query(Match)
        .filter(Match.student_id == student.id)
        .order_by(Match.score.desc())
        .limit(5)
        .all()
    )
    if recent_matches:
        match_lines = [
            f"- {m.job.title} at {m.job.company} ({m.job.domain}) — match score {m.score}/100"
            for m in recent_matches if m.job
        ]
        parts.append("CURRENT TOP MATCHES:\n" + "\n".join(match_lines))
    else:
        parts.append("CURRENT TOP MATCHES: none yet — the student hasn't run matching yet.")

    if job:
        parts.append(f"JOB CURRENTLY BEING DISCUSSED:\n{build_job_posting_summary(job)}")

        # Pull in any saved agent outputs for this specific (student, job) pair
        # so the assistant's answers stay consistent with what the student has
        # already seen on the Skill Gap / Materials / Interview Prep dashboards,
        # rather than re-deriving a possibly-different answer from scratch.
        gap = (
            db.query(SkillGapAnalysis)
            .filter(SkillGapAnalysis.student_id == student.id, SkillGapAnalysis.job_posting_id == job.id)
            .first()
        )
        if gap:
            parts.append("ALREADY-COMPUTED SKILL GAP ANALYSIS FOR THIS JOB:\n" + build_skill_gap_summary_text(gap))

        material = (
            db.query(ApplicationMaterial)
            .filter(ApplicationMaterial.student_id == student.id, ApplicationMaterial.job_posting_id == job.id)
            .first()
        )
        if material and (material.resume_content or material.cover_letter_content):
            parts.append(
                "STUDENT ALREADY HAS TAILORED APPLICATION MATERIALS FOR THIS JOB "
                "(resume and/or cover letter generated) — reference this instead of "
                "re-generating from scratch unless they ask you to revise it."
            )

        prep = (
            db.query(InterviewPrepPlan)
            .filter(InterviewPrepPlan.student_id == student.id, InterviewPrepPlan.job_posting_id == job.id)
            .first()
        )
        if prep and prep.revision_topics:
            parts.append(
                "ALREADY-IDENTIFIED INTERVIEW REVISION TOPICS FOR THIS JOB:\n"
                + "; ".join(prep.revision_topics)
            )
    else:
        # No specific job selected — ground the conversation in the RAG
        # knowledge base using the student's message itself as the query,
        # so "what roles involve X" / "is there anything in fintech" type
        # questions can be answered from real postings, not guesses.
        try:
            hits = semantic_search(message, top_k_jobs=RAG_FALLBACK_TOP_K)
        except Exception:
            hits = []
        if hits:
            lines = [f"- {h['title']} at {h['company']} ({h.get('domain')})" for h in hits]
            parts.append(
                "POTENTIALLY RELEVANT POSTINGS FROM THE KNOWLEDGE BASE (retrieved for this "
                "message — mention only if actually relevant to what they asked):\n" + "\n".join(lines)
            )

    return "\n\n".join(parts)


def send_message(db: Session, student: Student, message: str, job: Optional[JobPosting]) -> ChatMessage:
    """Saves the user's message, calls the LLM with recent history + context,
    saves and returns the assistant's reply."""
    user_msg = ChatMessage(
        student_id=student.id, role="user", content=message,
        job_posting_id=job.id if job else None,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    history_rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.student_id == student.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(MAX_HISTORY_MESSAGES)
        .all()
    )
    history_rows.reverse()  # chronological order for the LLM
    conversation_history = [{"role": m.role, "content": m.content} for m in history_rows]

    context_block = build_context_block(db, student, job, message)
    reply_text = llm_chat_reply(context_block, conversation_history)

    assistant_msg = ChatMessage(
        student_id=student.id, role="assistant", content=reply_text,
        job_posting_id=job.id if job else None,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    return assistant_msg
