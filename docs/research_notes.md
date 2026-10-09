# M1.1 — Research & Technical Understanding

## 1. Internship Application Workflow (as-is, in the real world)

A typical internship application journey has five stages, and the pain point at
each stage is what our agent is meant to remove:

1. **Discovery** — student searches multiple portals (LinkedIn, Internshala,
   company career pages) for roles that match their branch/skills. Pain: no
   single place aggregates relevance for *this specific* student.
2. **Fit-checking** — student reads the JD and guesses whether they qualify.
   Pain: no objective skill-gap signal, so students either under-apply (skip
   roles they'd actually qualify for) or spray-and-pray (apply everywhere).
3. **Application material prep** — tailoring a resume/cover letter per role.
   Pain: manual, repetitive, and quality varies with how tired the student is.
4. **Submission & tracking** — filling forms, tracking status across many
   portals. Pain: no unified tracker, follow-ups get missed.
5. **Interview prep** — practising for an unknown interviewer, unknown
   question style. Pain: generic prep, not tailored to the specific role/JD.

Our system maps one agent to each pain point (see `architecture.md`), so the
architecture is a direct reflection of this workflow, not an abstract design.

## 2. RAG (Retrieval-Augmented Generation) — how we're using it

RAG lets an LLM answer using facts it was never trained on, by retrieving
relevant text at query time and putting it into the prompt, instead of relying
purely on the model's parametric memory.

Standard pipeline:
```
query --> embed(query) --> vector search over indexed documents
        --> top-k relevant chunks --> inject into prompt
        --> LLM generates grounded answer
```

Why we need it here specifically:
- **Job-Resume Matching Agent** needs to compare a candidate profile against a
  *knowledge base of job postings* — this is a textbook retrieval problem
  (embed postings once, embed the candidate profile as the query, retrieve
  nearest postings).
- **Skill Gap Agent** needs to ground its answer in the *actual text of a
  specific job posting* (retrieved) rather than a generic "what skills should
  I learn" answer.
- **Interview Agent** needs to retrieve the *specific JD + company info* to
  ask role-relevant questions instead of generic ones.

Design decision for Milestone 1: we are building the **document store and
structured extraction layer first** (candidate profile), because RAG over job
postings is meaningless without a clean, structured candidate representation
to embed and query with. Milestone 1 is therefore the foundation the RAG
pipeline (Milestone 2+) will sit on top of.

## 3. Multi-Agent Design Patterns

Two patterns are relevant to this project:

- **Orchestrator–Worker pattern**: a central "Career Assistant" agent receives
  the user's intent, decides which specialist agent(s) to invoke, and
  composes their outputs into one answer. This avoids one giant prompt trying
  to do everything (matching + gap analysis + writing + interview prep) and
  keeps each agent's prompt/context small and testable.
- **Pipeline pattern**: some agents naturally feed each other in sequence
  (Resume Agent → Job-Resume Matching Agent → Skill Gap Agent → Cover Letter
  Agent). Output of one becomes input of the next, rather than every agent
  hitting the raw resume text independently.

We use **Orchestrator–Worker as the outer pattern** (Career Assistant is the
orchestrator) and **Pipeline as the inner pattern** for agents that logically
depend on each other's output. This is documented per-agent in
`architecture.md`.

## 4. Technology Choices (Milestone 1 scope)

| Concern | Choice | Why |
|---|---|---|
| Backend framework | FastAPI | Async-first, native Pydantic validation, auto OpenAPI docs, plays well with LLM API calls that are I/O bound |
| Database | PostgreSQL | Relational integrity for structured profile data (skills/education/experience are naturally normalized tables); mature, free, works great with SQLAlchemy |
| ORM | SQLAlchemy | De-facto standard, keeps DB layer swappable |
| Resume text extraction | `pdfplumber` (PDF), `python-docx` (DOCX) | Reliable text extraction without OCR complexity for Milestone 1 scope |
| Structured extraction | OpenAI API (`openai` SDK, JSON mode) with a strict JSON-output prompt | We need reasoning over unstructured resume text (varying formats/wording) — plain regex/rule-based parsing breaks on non-standard resumes; an LLM with a constrained JSON schema in the prompt handles that variance |
| Frontend | Plain HTML/CSS/JS | No build step needed, runs directly in the browser, keeps the project simple to run in VS Code with Live Server or just opening the file |

This choice list will be extended in later milestones (embeddings model,
vector index choice, etc. — see note in `architecture.md`).
