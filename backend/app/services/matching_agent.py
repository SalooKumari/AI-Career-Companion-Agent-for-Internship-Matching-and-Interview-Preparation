"""
Job-Resume Matching Agent (M2.3, optimized in M4.3).

Pipeline:
  1. Build a text summary of the student's structured profile (skills,
     education, experience, projects) from Milestone 1's data — used for the
     LLM scoring prompt.
  2. Build a separate, tighter RETRIEVAL query (skills, field of study,
     project tech/titles, experience titles — no name or institution, which
     are pure noise for semantic search) and use it against the job-posting
     chunk index (M2.2) to pull a wide candidate pool — cheap, no LLM call.
  3. HYBRID RE-RANK the pool: blend embedding similarity with an explicit
     skill-overlap signal (required skills weighted above preferred). This
     fixes a known weakness of embedding-only retrieval — a posting can be
     semantically "close" to a profile yet require none of the student's
     actual skills — and means the expensive LLM step is spent on the most
     promising candidates.
  4. For only the top LLM_SCORING_LIMIT re-ranked candidates, ask the LLM to
     score compatibility with reasoning and a factor breakdown (one call
     per candidate — this is why steps 2-3 narrow the field first instead of
     scoring every posting).
  5. Sort by score, store the top-k as Match rows, return them.

Retrieval (fast, semantic, cheap), re-ranking (fast, deterministic,
explainable) and reasoning (slow, precise) stay three clearly separate
stages.
"""
import re
from typing import List

from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.job_posting import JobPosting
from app.models.match import Match
from app.services.vector_store import semantic_search
from app.services.llm_service import score_job_match

# --- M4.3 tuning parameters (see docs/optimization_report.md for rationale) ---
RETRIEVAL_POOL = 20      # wide, cheap semantic retrieval
LLM_SCORING_LIMIT = 8    # only the best re-ranked candidates get an LLM call
W_SIMILARITY = 0.55      # embedding cosine similarity
W_REQUIRED = 0.35        # fraction of the job's REQUIRED skills the student shows
W_PREFERRED = 0.10       # fraction of the job's PREFERRED skills the student shows


def _tokens(text: str) -> frozenset:
    """Lowercased word tokens, keeping c++/c#/.net-style symbols attached."""
    return frozenset(t for t in re.findall(r"[a-z0-9+#.]+", (text or "").lower()) if t.strip("."))


def _skill_matches(student_skill_tokens: frozenset, job_skill_tokens: frozenset) -> bool:
    """Token-subset match in either direction, so "Python (pandas)" matches
    a required "Python" and "machine learning" matches "machine learning
    fundamentals" — but "java" does NOT match "javascript" (which a plain
    substring check would wrongly allow)."""
    if not student_skill_tokens or not job_skill_tokens:
        return False
    return student_skill_tokens <= job_skill_tokens or job_skill_tokens <= student_skill_tokens


def student_skill_token_sets(student: Student) -> List[frozenset]:
    """Every skill the student demonstrably has: listed skills plus the
    tech stacks of their projects (a project using Streamlit is evidence of
    Streamlit even if it isn't in the skills list)."""
    sets = [_tokens(s.name) for s in (student.skills or [])]
    for p in (student.projects or []):
        for piece in re.split(r"[,;/]", p.tech_stack or ""):
            if piece.strip():
                sets.append(_tokens(piece))
    return [t for t in sets if t]


def skill_overlap_fraction(student_sets: List[frozenset], job_skills: List[str]) -> float:
    job_sets = [_tokens(s) for s in (job_skills or []) if s]
    job_sets = [j for j in job_sets if j]
    if not job_sets:
        return 0.0
    hits = sum(1 for j in job_sets if any(_skill_matches(s, j) for s in student_sets))
    return hits / len(job_sets)


def build_retrieval_query(student: Student) -> str:
    """Signal-only text for semantic retrieval: skills, field of study,
    project titles/tech, and experience titles. Deliberately omits the
    student's name, institution and grade."""
    parts = []
    if student.skills:
        parts.append("Skills: " + ", ".join(s.name for s in student.skills))
    for ed in (student.education or []):
        bit = " ".join(x for x in [ed.degree, ed.field_of_study] if x)
        if bit:
            parts.append(f"Studying: {bit}")
    for exp in (student.experience or []):
        parts.append(f"Experience: {exp.title}" + (f" — {exp.description}" if exp.description else ""))
    for p in (student.projects or []):
        bit = p.title + (f" (tech: {p.tech_stack})" if p.tech_stack else "")
        if p.description:
            bit += f" — {p.description}"
        parts.append(f"Project: {bit}")
    return "\n".join(parts)


def hybrid_rerank(candidates: List[dict], student: Student, jobs_by_id: dict) -> List[dict]:
    """Re-orders retrieval candidates by a blend of embedding similarity and
    explicit skill overlap. Adds `hybrid_score`, `required_overlap`,
    `preferred_overlap` to each candidate dict (kept for the evaluation
    scripts and the optimization report)."""
    student_sets = student_skill_token_sets(student)
    for c in candidates:
        job = jobs_by_id.get(c["job_posting_id"])
        if job is None:
            c.update(hybrid_score=c["similarity"] * W_SIMILARITY, required_overlap=0.0, preferred_overlap=0.0)
            continue
        req = skill_overlap_fraction(student_sets, job.required_skills)
        pref = skill_overlap_fraction(student_sets, job.preferred_skills)
        if job.required_skills:
            score = W_SIMILARITY * c["similarity"] + W_REQUIRED * req + W_PREFERRED * pref
        else:
            # A posting listing no required skills can't be judged on overlap —
            # fall back to similarity alone rather than unfairly penalizing it.
            score = c["similarity"]
        c.update(hybrid_score=score, required_overlap=req, preferred_overlap=pref)
    return sorted(candidates, key=lambda c: c["hybrid_score"], reverse=True)


def build_student_profile_summary(student: Student) -> str:
    """Turns the structured profile into plain text for the LLM prompt
    and for use as the RAG retrieval query."""
    parts = [f"Name: {student.full_name}"]

    if student.skills:
        skill_bits = [
            f"{s.name}" + (f" ({s.proficiency})" if s.proficiency else "")
            for s in student.skills
        ]
        parts.append("Skills: " + ", ".join(skill_bits))

    if student.education:
        for ed in student.education:
            edu_bit = f"{ed.degree or ''} in {ed.field_of_study or ''} — {ed.institution}".strip()
            if ed.grade:
                edu_bit += f" (grade/CGPA: {ed.grade})"
            parts.append(f"Education: {edu_bit}")

    if student.experience:
        for exp in student.experience:
            exp_bit = f"{exp.title} at {exp.organization or 'N/A'}"
            if exp.description:
                exp_bit += f": {exp.description}"
            parts.append(f"Experience: {exp_bit}")

    if student.projects:
        for p in student.projects:
            proj_bit = p.title
            if p.tech_stack:
                proj_bit += f" (tech: {p.tech_stack})"
            if p.description:
                proj_bit += f" — {p.description}"
            parts.append(f"Project: {proj_bit}")

    return "\n".join(parts)


def build_job_posting_summary(job: JobPosting) -> str:
    parts = [
        f"Title: {job.title}",
        f"Company: {job.company}",
        f"Location: {job.location}",
        f"Description: {job.job_description}",
    ]
    if job.responsibilities:
        parts.append("Responsibilities: " + "; ".join(job.responsibilities))
    if job.required_skills:
        parts.append("Required skills: " + ", ".join(job.required_skills))
    if job.preferred_skills:
        parts.append("Preferred skills: " + ", ".join(job.preferred_skills))
    if job.qualifications:
        parts.append("Qualifications: " + "; ".join(job.qualifications))
    if job.experience_requirement:
        parts.append(f"Experience required: {job.experience_requirement}")
    if job.education_requirement:
        parts.append(f"Education required: {job.education_requirement}")
    return "\n".join(parts)


def run_matching(
    db: Session, student_id: int, top_k: int = 5,
    retrieval_pool: int = RETRIEVAL_POOL, llm_scoring_limit: int = LLM_SCORING_LIMIT,
) -> List[Match]:
    """
    Runs the full matching pipeline for one student and persists the
    top-k Match rows (replacing any previous matches for that student).
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if student is None:
        raise ValueError(f"Student {student_id} not found.")

    profile_summary = build_student_profile_summary(student)
    if not profile_summary.strip():
        raise ValueError(
            "Student profile has no skills/education/experience/projects yet — "
            "upload and parse a resume first (Milestone 1)."
        )

    # Step 1: cheap semantic retrieval over a wide pool, using a signal-only query
    candidates = semantic_search(build_retrieval_query(student) or profile_summary, top_k_jobs=retrieval_pool)

    if not candidates:
        return []

    # Step 2: hybrid re-rank (embedding similarity + explicit skill overlap),
    # then keep only the best few for the expensive LLM scoring step
    jobs_by_id = {
        j.id: j for j in db.query(JobPosting).filter(JobPosting.id.in_([c["job_posting_id"] for c in candidates])).all()
    }
    candidates = hybrid_rerank(candidates, student, jobs_by_id)[:llm_scoring_limit]

    # Step 3: LLM reasoning + scoring, one call per re-ranked candidate
    scored = []
    for rank, candidate in enumerate(candidates, start=1):
        job = jobs_by_id.get(candidate["job_posting_id"])
        if job is None:
            continue

        job_summary = build_job_posting_summary(job)
        try:
            llm_result = score_job_match(profile_summary, job_summary)
        except Exception:
            # If one job's scoring call fails, skip it rather than fail the whole batch
            continue

        scored.append({
            "job": job,
            "score": llm_result.score,
            "skills_score": llm_result.skills_score,
            "education_score": llm_result.education_score,
            "project_score": llm_result.project_score,
            "domain_fit_score": llm_result.domain_fit_score,
            "matched_skills": llm_result.matched_skills,
            "missing_skills": llm_result.missing_skills,
            "reasoning": llm_result.reasoning,
            "retrieval_rank": rank,
        })

    # Step 3: rank by LLM score (not just retrieval similarity) and keep top-k
    scored.sort(key=lambda x: x["score"], reverse=True)
    top_results = scored[:top_k]

    # Replace previous matches for this student
    db.query(Match).filter(Match.student_id == student_id).delete()

    match_rows = []
    for r in top_results:
        m = Match(
            student_id=student_id,
            job_posting_id=r["job"].id,
            score=r["score"],
            skills_score=r["skills_score"],
            education_score=r["education_score"],
            project_score=r["project_score"],
            domain_fit_score=r["domain_fit_score"],
            matched_skills=r["matched_skills"],
            missing_skills=r["missing_skills"],
            reasoning=r["reasoning"],
            retrieval_rank=r["retrieval_rank"],
        )
        db.add(m)
        match_rows.append(m)

    db.commit()
    for m in match_rows:
        db.refresh(m)

    return match_rows
