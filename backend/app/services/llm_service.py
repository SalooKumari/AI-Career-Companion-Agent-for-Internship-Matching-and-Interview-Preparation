"""
Uses the OpenAI API for three jobs:
  1. Turning raw resume text into structured JSON (skills, education,
     experience, projects) — Milestone 1.
  2. Scoring student-profile x job-posting compatibility with reasoning —
     Milestone 2 (Job-Resume Matching Agent).
  3. Reviewing a completed mock interview transcript and generating
     calibrated feedback — AI Chat Bot / Mock Interview feature.

All three use OpenAI's JSON mode (response_format={"type": "json_object"}) so
the model is constrained to return a single valid JSON object, which we
then validate against a Pydantic schema.

Why an LLM instead of regex/rule-based parsing for extraction: resumes vary
wildly in layout and wording, and a constrained-JSON prompt handles that
variance far better than brittle pattern matching (see
docs/research_notes.md, M1.1).
"""
import json

from openai import OpenAI

from app.core.config import settings
from app.schemas.student import ExtractedResumeData
from app.schemas.match import LLMMatchResult
from app.schemas.interview import LLMInterviewFeedback
from app.schemas.skill_gap import LLMSkillGapResult
from app.schemas.application_material import LLMApplicationMaterials
from app.schemas.interview_prep import LLMInterviewPrepResult

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            raise RuntimeError(
                "No LLM API key is configured. Add GROQ_API_KEY to backend/.env "
                "(see .env.example)."
            )
        base_url = settings.GROQ_BASE_URL if settings.GROQ_API_KEY else settings.OPENAI_BASE_URL
        _client = OpenAI(
            api_key=api_key,
            base_url=base_url or None,
        )
    return _client


def _model_name() -> str:
    """Use Groq settings when a Groq key is configured, otherwise OpenAI settings."""
    return settings.GROQ_MODEL if settings.GROQ_API_KEY else settings.OPENAI_MODEL


EXTRACTION_SYSTEM_PROMPT = """You are a resume parsing engine. You extract \
structured data from resume text and return ONLY a single valid JSON object \
— no prose, no markdown code fences, no explanations before or after.

Return an object with exactly these keys: "skills", "education", \
"experience", "projects".

- "skills": array of {"name": string, "category": string|null, \
"proficiency": string|null}. category is one of "programming", "tool", \
"framework", "soft-skill", "language", "other". proficiency is one of \
"beginner", "intermediate", "advanced", or null if unknown — never guess it.
- "education": array of {"institution": string, "degree": string|null, \
"field_of_study": string|null, "start_date": string|null, "end_date": \
string|null, "grade": string|null}.
- "experience": array of {"title": string, "organization": string|null, \
"start_date": string|null, "end_date": string|null, "description": \
string|null}. description should be a concise 1-3 sentence summary in your \
own words, not a verbatim copy of bullet points.
- "projects": array of {"title": string, "description": string|null, \
"tech_stack": string|null, "link": string|null}.

Rules:
- If a section is genuinely absent from the resume, return an empty array \
for it — never fabricate entries.
- Do not invent dates, grades, or links that are not present in the text.
- Output must be a single valid JSON object and nothing else.
"""


def extract_structured_data(raw_resume_text: str) -> ExtractedResumeData:
    """
    Sends resume text to the OpenAI API and parses the JSON response into
    an ExtractedResumeData object. Raises ValueError if the model
    response isn't valid JSON matching the expected schema.
    """
    client = _get_client()

    response = client.chat.completions.create(
        model=_model_name(),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Resume text:\n\n{raw_resume_text}"},
        ],
    )

    text_output = response.choices[0].message.content.strip()

    try:
        data = json.loads(text_output)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM did not return valid JSON. Raw output was:\n{text_output}"
        ) from e

    return ExtractedResumeData.model_validate(data)


MATCH_SYSTEM_PROMPT = """You are the reasoning component of a Job-Resume \
Matching Agent for student internships. You are given a student's \
structured profile and one internship posting. You return ONLY a single \
valid JSON object — no prose, no markdown code fences, no explanation \
outside the JSON.

Return an object with exactly these keys:
- "score": integer 0-100. This is the OVERALL compatibility score — your \
holistic judgment of how well this specific student matches this specific \
role, considering all factors together (skills matter most, but not \
exclusively). Required skills should carry more weight than preferred \
skills. A student missing most required skills should score low (below \
40) even if they look impressive in general. This does not have to be a \
simple average of the four factor scores below — use your judgment on how \
they combine for this particular role.
- "skills_score": integer 0-100 — specifically how well the student's \
listed technical/soft skills and tools cover this job's required and \
preferred skills. 0 = covers almost none of the required skills, 100 = \
covers essentially all required skills plus most preferred ones.
- "education_score": integer 0-100 — how well the student's education \
(degree, field of study, and CGPA/grade if the student's profile states \
one) matches this job's stated education requirement. If the job states \
no specific education requirement, score based on general field-of-study \
relevance. Never penalize a student for not stating a CGPA — score based \
on what is actually in their profile, and treat an unstated CGPA as \
neutral, not as a gap.
- "project_score": integer 0-100 — how relevant the student's listed \
projects (and internship/work experience, if any) are to this specific \
role's responsibilities and domain. A student with no projects listed \
should score low here, not neutral.
- "domain_fit_score": integer 0-100 — how well this job's domain/role type \
aligns with the trajectory implied by the student's overall profile \
(skills, education field, and past experience/projects together) — i.e. \
does this role make sense as a next step for someone with this \
background, independent of whether they have every specific skill yet.
- "matched_skills": array of skill names (strings) that genuinely appear \
in both the student's profile and the job's required/preferred skills — \
do not include a skill unless it is reasonably implied by the student's \
listed skills, education, experience, or projects.
- "missing_skills": array of the job's required (and, if relevant, \
preferred) skills that the student's profile does NOT show evidence of.
- "reasoning": a concise, specific 2-4 sentence explanation referencing \
actual details from the student's profile and the job posting — not a \
generic statement. Explain both the strengths and the gaps, and briefly \
note which of the four factors above most helped or hurt this match.

Be honest and calibrated: most students will not be a perfect match for \
most postings, and every score (overall and each factor) should reflect \
that — don't default to a comfortable middling number when the evidence \
points lower or higher.
"""


def score_job_match(student_profile_summary: str, job_posting_summary: str) -> LLMMatchResult:
    """
    Asks the LLM to score compatibility between a student profile and a
    single job posting, with reasoning and a factor-level breakdown
    (skills / education / projects / domain fit). Used by the Job-Resume
    Matching Agent (M2.3, extended M4.3) once per candidate job returned by
    the RAG retrieval step.
    """
    client = _get_client()

    response = client.chat.completions.create(
        model=_model_name(),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": MATCH_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"STUDENT PROFILE:\n{student_profile_summary}\n\n"
                    f"JOB POSTING:\n{job_posting_summary}"
                ),
            },
        ],
    )

    text_output = response.choices[0].message.content.strip()

    try:
        data = json.loads(text_output)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM did not return valid JSON for match scoring. Raw output was:\n{text_output}"
        ) from e

    result = LLMMatchResult.model_validate(data)
    result.score = max(0, min(100, result.score))  # clamp defensively
    result.skills_score = max(0, min(100, result.skills_score))
    result.education_score = max(0, min(100, result.education_score))
    result.project_score = max(0, min(100, result.project_score))
    result.domain_fit_score = max(0, min(100, result.domain_fit_score))
    return result


INTERVIEW_FEEDBACK_SYSTEM_PROMPT = """You are an experienced technical and \
behavioral interview coach reviewing a student's completed mock interview \
for an internship. You are given the student's profile summary, the full \
list of questions asked alongside their (voice-transcribed) answers, and — \
when this mock interview was generated for one specific job posting rather \
than general practice — that job's details too. You return ONLY a single \
valid JSON object — no prose, no markdown code fences, no explanation \
outside the JSON.

Return an object with exactly these keys:
- "overall_score": integer 0-100 reflecting overall interview performance \
across clarity, technical accuracy, and depth of answers. Be honest and \
calibrated — most students will not score above 85, and a student who left \
many answers blank or very short should score well below 50.
- "strengths": array of 2-5 short, specific strings. Reference actual \
answers the student gave — not generic praise.
- "improvements": array of 2-5 objects, each with exactly these keys:
  - "area": a short label for the weak spot (e.g. "Explaining time \
complexity", "STAR structure in behavioral answers", "Depth on REST API \
design")
  - "why_it_matters": 1-2 sentences explaining, concretely, why this \
matters for this role/domain — not a generic platitude
  - "resources": array of 2-4 short strings naming REAL, well-known, \
specific resources to work on exactly this gap — official docs, well-known \
free courses or platforms (e.g. "MDN Web Docs — Promises guide", \
"freeCodeCamp's Responsive Web Design course", "LeetCode — Arrays & \
Hashing study plan", "Cracking the Coding Interview, Ch. 4"). Name real, \
stable, well-known resources only — never invent a URL or a course that \
may not exist. A well-known platform/publisher name plus what to study \
there is enough; you don't need to fabricate an exact link.
  Ground every "area" in a specific weak or missing answer, and state what \
a stronger answer would have included.
- "recommendations": a 3-6 sentence personalized paragraph giving the \
student concrete next steps to become a stronger candidate — what to \
practice, what to learn, and how their profile could better support the \
kind of role these questions were for.

Notes:
- Transcribed answers may contain minor speech-to-text errors (filler \
words, mis-transcribed technical terms) — judge the substance, not \
transcription artifacts.
- An empty or near-empty answer to a question should be treated as a real \
gap, not skipped over.
- Ground every point in the actual questions and answers given, not in \
generic interview advice.
- When a specific job posting's details are provided, calibrate strengths, \
improvements, and resources to that exact role's real requirements — not \
generic advice for the broader domain.
"""


def generate_interview_feedback(
    student_profile_summary: str, qa_transcript: str, job_context: str | None = None
) -> LLMInterviewFeedback:
    """
    Asks the LLM to review a completed mock interview transcript (question/
    answer pairs) and return calibrated feedback. Used by the Mock
    Interview / AI Chat Bot feature once a student submits their set.
    job_context (optional): that job's details, when this set was
    generated for one specific posting rather than general domain practice
    (see services/interview_agent.py) — lets feedback (and resource
    suggestions) be calibrated to that exact role.
    """
    client = _get_client()

    user_content = f"STUDENT PROFILE:\n{student_profile_summary}\n\n"
    if job_context:
        user_content += f"THIS MOCK INTERVIEW WAS FOR THIS SPECIFIC JOB POSTING:\n{job_context}\n\n"
    user_content += f"MOCK INTERVIEW TRANSCRIPT:\n{qa_transcript}"

    response = client.chat.completions.create(
        model=_model_name(),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": INTERVIEW_FEEDBACK_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )

    text_output = response.choices[0].message.content.strip()

    try:
        data = json.loads(text_output)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM did not return valid JSON for interview feedback. Raw output was:\n{text_output}"
        ) from e

    result = LLMInterviewFeedback.model_validate(data)
    result.overall_score = max(0, min(100, result.overall_score))
    return result


# ---------------------------------------------------------------------------
# Milestone 3 — Skill Gap Analysis Agent
# ---------------------------------------------------------------------------

SKILL_GAP_SYSTEM_PROMPT = """You are a Skill Gap Analysis agent for internship \
candidates. You compare a student's profile against one specific job \
posting and return ONLY valid JSON — no prose, no markdown fences.

Return an object with exactly these keys:
- "critical_gaps": array of {"item": string, "why_it_matters": string} — \
required skills/qualifications the student does NOT show any evidence of \
having. Keep "why_it_matters" concrete and specific to this role.
- "partial_gaps": array of {"item": string, "why_it_matters": string} — \
skills the student has some evidence of (e.g. via a related project or \
course) but not clearly at the level the role wants.
- "preferred_gaps": array of {"item": string, "why_it_matters": string} — \
preferred (not required) skills/qualifications the student is missing.
- "experience_gaps": array of short strings describing gaps between the \
role's experience expectations and the student's actual experience.
- "qualification_gaps": array of short strings for education/certification \
gaps specifically (leave empty if the student meets them).
- "recommendations": array of short, concrete, actionable strings — things \
the student could do (a project, a course, a certification, practice) to \
close the most important gaps. Order by impact, most important first.

Rules:
- Ground every item in the actual job posting text and the actual student \
profile given — never invent a requirement that isn't in the posting, and \
never credit the student with a skill they didn't list.
- If the student is a strong match with few or no gaps, it's fine for some \
arrays to be empty — don't invent gaps to fill space.
- Keep each "why_it_matters" to one or two sentences.
"""


def analyze_skill_gap(student_profile_summary: str, job_summary: str) -> LLMSkillGapResult:
    """M3.1 — Skill Gap Analysis Agent. Compares a student's structured
    profile against one job posting and returns categorized gaps plus
    recommendations for closing them."""
    client = _get_client()

    response = client.chat.completions.create(
        model=_model_name(),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SKILL_GAP_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"STUDENT PROFILE:\n{student_profile_summary}\n\nJOB POSTING:\n{job_summary}",
            },
        ],
    )

    text_output = response.choices[0].message.content.strip()
    try:
        data = json.loads(text_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON for skill gap analysis. Raw output was:\n{text_output}") from e

    return LLMSkillGapResult.model_validate(data)


# ---------------------------------------------------------------------------
# Milestone 3 — Resume & Cover Letter Customization Agent
# ---------------------------------------------------------------------------

APPLICATION_MATERIALS_SYSTEM_PROMPT = """You are a Resume & Cover Letter \
Customization agent for internship applications. Given a student's \
structured profile and one specific job posting, you produce a tailored \
resume and a tailored cover letter for that role. Return ONLY valid JSON — \
no prose, no markdown fences.

Return an object with exactly these keys:
- "resume_content": a complete tailored resume as plain text (use blank \
lines between sections and simple "- " bullet points — no markdown \
headers/asterisks). Structure: contact line, then a short 2-3 line summary \
tailored to this role, then Skills (most relevant to this job first), then \
Experience (most relevant entries first, bullets reworded to foreground \
what matters for this role and to naturally include a few real keywords \
from the job description), then Projects (most relevant first, same \
treatment), then Education.
- "cover_letter_content": a complete tailored cover letter as plain text \
(3-4 paragraphs, professional but not stiff, no placeholder brackets like \
"[Company Name]" — use the real company/role name given). It should \
connect specific pieces of the student's real background/projects to \
specific requirements in the job posting, and close with genuine interest \
in the role.

CRITICAL RULES:
- Never invent skills, experiences, achievements, metrics, or projects the \
student did not report. Every claim in both documents must trace back to \
something in the student's actual profile.
- Reorder and reword what's already true — don't fabricate to fill gaps. \
If the student is missing something the role wants, simply don't claim it.
- Use the real job title and company name from the posting throughout.
"""


def generate_application_materials(
    student_profile_summary: str, job_summary: str
) -> "LLMApplicationMaterials":
    """M3.2 — Resume & Cover Letter Customization Agent."""
    client = _get_client()

    response = client.chat.completions.create(
        model=_model_name(),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": APPLICATION_MATERIALS_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"STUDENT PROFILE:\n{student_profile_summary}\n\nJOB POSTING:\n{job_summary}",
            },
        ],
    )

    text_output = response.choices[0].message.content.strip()
    try:
        data = json.loads(text_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON for application materials. Raw output was:\n{text_output}") from e

    return LLMApplicationMaterials.model_validate(data)


# ---------------------------------------------------------------------------
# Milestone 3 — Interview Preparation Agent (job-specific)
# ---------------------------------------------------------------------------

INTERVIEW_PREP_SYSTEM_PROMPT = """You are an Interview Preparation agent for \
one specific internship a student is preparing to interview for. Return \
ONLY valid JSON — no prose, no markdown fences.

Return an object with exactly these keys, each an array of \
{"question": string, "guidance": string} EXCEPT "revision_topics" which is \
an array of short strings:
- "technical_questions": core technical questions for this specific role/domain.
- "resume_based_questions": questions an interviewer would ask by looking \
directly at THIS student's resume (reference their actual listed \
experience/skills by name in the question).
- "project_based_questions": questions specifically about THIS student's \
actual listed projects (name the project in the question where natural).
- "role_specific_questions": questions specific to what this exact job \
posting says the role involves (its responsibilities/domain), not generic.
- "hr_questions": general/behavioral HR-style questions (fit, motivation, \
teamwork, why this company/role).
- "revision_topics": concrete topics/concepts the student should revise \
before the interview, informed by the job's requirements and any skill \
gaps — e.g. "Big-O complexity of common data structures", not vague advice.

For every question, "guidance" is 1-3 sentences of concrete advice on how \
to structure a strong answer (not the answer itself) — what to mention, \
what structure to use (e.g. STAR for behavioral), what to avoid.

Aim for roughly 4-6 questions per category. Ground resume/project-based \
questions strictly in what the student's profile actually contains — never \
invent a project or skill they didn't list.
"""


def generate_interview_prep(
    student_profile_summary: str, job_summary: str, skill_gap_summary: str = ""
) -> LLMInterviewPrepResult:
    """M3.3 — Interview Preparation Agent, grounded in one specific job
    posting, the student's real profile, and (optionally) their skill-gap
    analysis for that role."""
    client = _get_client()

    user_content = f"STUDENT PROFILE:\n{student_profile_summary}\n\nJOB POSTING:\n{job_summary}"
    if skill_gap_summary:
        user_content += f"\n\nKNOWN SKILL GAPS FOR THIS ROLE:\n{skill_gap_summary}"

    response = client.chat.completions.create(
        model=_model_name(),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": INTERVIEW_PREP_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )

    text_output = response.choices[0].message.content.strip()
    try:
        data = json.loads(text_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON for interview prep. Raw output was:\n{text_output}") from e

    return LLMInterviewPrepResult.model_validate(data)


# ---------------------------------------------------------------------------
# Milestone 3 — Conversational Career Assistant
# ---------------------------------------------------------------------------

CAREER_ASSISTANT_SYSTEM_PROMPT = """You are the Career Assistant inside an \
internship-matching platform — a helpful, direct personal career advisor \
for one specific student, having an ongoing conversation with them. Many \
students you talk to are freshers with little or no work experience yet, \
so be encouraging and concrete rather than assuming prior industry \
knowledge — but never dumb down or hedge factual/technical answers.

You have access to the student's profile summary, the raw text of their \
uploaded resume (when they've uploaded one), their current top internship \
matches, and (when relevant) a specific job posting they're asking about. \
Use this context to give SPECIFIC, PERSONALIZED answers — never generic \
career advice that could apply to anyone.

You can help with things like: recommending suitable internships from \
their matches (and explaining why), explaining a skill gap for a role, \
suggesting skills or projects to improve their employability, helping \
think through application materials, outlining an interview prep plan, \
answering questions about a job's requirements, comparing internship \
options, and helping them decide between choices. You can also critique \
their actual resume when asked — point to specific lines/sections in the \
raw resume text provided (weak bullet points, missing sections, unclear \
phrasing, formatting issues you can infer from the text, a mismatch \
between what they've written and what target roles need) rather than \
giving generic "resume tips." If no resume has been uploaded yet, say so \
and suggest they upload one on the Resume dashboard so you can review it \
properly, rather than guessing at generic advice.

Style: conversational but substantive, like a knowledgeable mentor — not a \
generic chatbot. Reference specific things from their profile/resume/\
matches when relevant instead of speaking in the abstract. If you don't \
have enough context to answer specifically (e.g. they ask about a job \
that isn't in the context provided, or ask you to review a resume that \
hasn't been uploaded), say so plainly and ask a clarifying question rather \
than guessing. Keep responses focused — a few short paragraphs or a short \
list, not an essay, unless they've asked for depth.

Grounding and consistency rules:
- Only state facts about the student, a job, or a company that appear in \
the context you were given. Never invent a job, a company, a skill the \
student has, a deadline, or a statistic. If something isn't in the \
context, say you don't have it.
- If saved analyses appear in the context (a skill gap analysis, tailored \
materials, or interview prep for a job), treat them as the source of truth \
for that job and stay consistent with them — do not contradict a gap \
analysis the student has already seen; if you think it's incomplete, say \
so explicitly instead of silently disagreeing.
- Use the earlier turns of this conversation: resolve references like "the \
first one" or "that role" from what was just discussed, and do not repeat \
recommendations, greetings, or explanations you've already given unless \
the student asks for them again. Build on the previous answer instead of \
restarting from scratch.
"""


def career_assistant_reply(context_block: str, conversation_history: list[dict]) -> str:
    """
    M3.4 — Conversational Career Assistant. `context_block` is a text
    summary of the student's profile, current matches, and (optionally) a
    specific job being discussed. `conversation_history` is a list of
    {"role": "user"|"assistant", "content": str} dicts in chronological
    order (the new user message is the last item). Returns the assistant's
    plain-text reply — no JSON mode here, since this is free-form
    conversation, not structured extraction.
    """
    client = _get_client()

    messages = [
        {"role": "system", "content": CAREER_ASSISTANT_SYSTEM_PROMPT + f"\n\nCONTEXT:\n{context_block}"},
    ]
    messages.extend(conversation_history)

    response = client.chat.completions.create(
        model=_model_name(),
        messages=messages,
    )

    return response.choices[0].message.content.strip()
