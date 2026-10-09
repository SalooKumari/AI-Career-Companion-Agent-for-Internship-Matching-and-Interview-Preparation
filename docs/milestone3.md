# Milestone 3: AI Agents Suite

## M3.1 — Skill Gap Analysis Agent
- Compare student profile against a job's requirements
- Return gaps in 5 categories:
  - Critical/missing
  - Partially demonstrated
  - Preferred-only
  - Experience gaps
  - Qualification gaps
- Each gap includes: reason why it matters for the role
- Personalized recommendation list
- Save analysis per (student, job) pair for reuse

## M3.2 — Resume & Cover Letter Customization Agent
- Generate tailored resume per job (relevant skills surfaced, 
  JD keywords worked in, bullet points reworded)
- Generate role-specific cover letter
- Both in one LLM call
- Hard constraint: never invent skills/experience not in profile
- Outputs editable via PATCH

## M3.3 — Interview Preparation Agent
- Role-specific question generation in 5 categories:
  - Technical
  - Resume-based
  - Project-based
  - Role-specific
  - HR/general
- Prep guidance per question
- Revision topics list
- Reuse Skill Gap output when available

## M3.4 — Conversational Career Assistant
- Persistent per-student message log (not per session)
- Context assembled from: profile, resume text, top matches, 
  skill gaps, tailored materials, prep plans
- RAG fallback for general questions
- Resolve conversational references from history
- Stay consistent with saved agent outputs
- No hallucination — say plainly when context is missing

## Deliverables
- 4 working AI agents with LLM integration
- Saved outputs per (student, job) pair
- Cross-agent consistency (Skill Gap reused by other agents)
- Editable application materials

## Status
✅ Completed
