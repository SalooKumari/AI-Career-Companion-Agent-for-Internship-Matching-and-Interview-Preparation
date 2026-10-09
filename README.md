# AI Career Companion Agent — Internship Matching & Interview Preparation

**Milestone 1 — Foundation & Candidate Understanding**
**Milestone 2 — Internship Knowledge & Job-Resume Matching**
**Milestone 3 — Skill Gap, Application Customization & Interview Preparation**
**Milestone 4 — Application Tracking, Testing/Optimization & Final Polish**
**App layer — Authentication + multi-dashboard UI**

## Milestones Link
- [Milestone 1: Foundation & Candidate Understanding](docs/milestone-1.md)
- [Milestone 2: Knowledge Base, RAG & Matching](docs/milestone-2.md)
- [Milestone 3: AI Agents Suite](docs/milestone-3.md)
- [Milestone 4: Application Tracking & Testing](docs/milestone-4.md)

Milestone 4 adds: a full Application Tracking Module (status workflow —
applied/in-process/interview-called/rejected/completed/withdrawn, filters,
per-application reminder deadlines), a saved-jobs bookmark feature and a
deadline-notification bell in a new topbar, and a multi-factor match score
breakdown (skills/education/projects/domain fit) alongside the overall
compatibility score.

Milestone 1 built the foundation: a student can create a profile, upload a
resume, and have it parsed into a structured candidate profile (skills,
education, experience, projects) using an LLM.

Milestone 2 builds on top of that: a curated 180-posting internship
knowledge base, a RAG pipeline (chunk → embed → semantic search) over that
knowledge base, and a Job-Resume Matching Agent that retrieves relevant
postings for a student and scores + explains compatibility.

Milestone 3 adds four more agents, all grounded in one specific selected
internship: a **Skill Gap Analysis Agent** (categorized gaps + why each one
matters + recommendations), a **Resume & Cover Letter Customization Agent**
(tailored, editable, downloadable — never inventing skills the student
doesn't have), a job-specific **Interview Preparation Agent** (five question
categories with per-question guidance, plus revision topics informed by any
skill gaps already found), and a **Conversational Career Assistant** — an
ongoing chat that ties together the student's profile, matches, skill gaps,
application materials, interview prep, and the RAG knowledge base to answer
free-form questions and help with decisions.

On top of all three milestones, the app is a real per-user product:
students **register and log in** (email + password), and everything after
login lives inside a **sidebar-navigated dashboard** with eight sections —
Student Profile, Upload Resume & Parse, Find Matching Internships (with a
self-serve search bar alongside the AI ranking), Applied Internships,
**AI Chat Bot** (a 25-question voice-based general mock interview
personalized to the student's matched domain), **My Mock Interviews**
(saved history of every completed interview), **Application Toolkit**
(Skill Gap / Tailored Resume / Cover Letter / Interview Prep, all for one
chosen internship at a time), and **Career Assistant** (the ongoing chat).

See `docs/architecture.md` for the full system architecture (diagrams +
agent roles + data flow), `docs/tech_stack.md` for the tech stack,
`docs/job_posting_schema.md` for the job-posting dataset schema,
`docs/interview_question_bank.md` for the mock-interview question bank and
its sourcing notes, and `docs/research_notes.md` for the M1.1 research
(internship workflows, RAG, multi-agent patterns).

## Project structure

```
career-companion/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app entrypoint
│   │   ├── core/                  # config + database session + security (JWT/hashing) + auth deps
│   │   ├── models/                # SQLAlchemy models (student, job_posting, match, application, interview,
│   │   │                          #   skill_gap, application_material, interview_prep, chat)
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── routers/                # /auth, /students, /resumes, /jobs, /matches, /applications, /interviews,
│   │   │                          #   /skill-gap, /materials, /interview-prep, /chat
│   │   └── services/                # resume extraction, LLM calls, chunking, embeddings, vector store,
│   │                                #   matching agent, interview agent, skill gap agent, application material
│   │                                #   agent, interview prep agent, career assistant
│   ├── uploads/                    # uploaded resumes + profile photos (gitignored)
│   ├── vector_store/               # ChromaDB persisted index (built, not versioned)
│   ├── test_extraction.py          # standalone extraction test script (M1.4)
│   ├── seed_job_postings.py        # loads database/job_postings.json into Postgres (M2.1)
│   ├── build_knowledge_base.py     # chunks + embeds + indexes job postings (M2.2)
│   ├── evaluate_matching.py        # retrieval + matching evaluation script (M2.4)
│   ├── seed_interview_questions.py # loads database/interview_questions.json into Postgres
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html                  # auth screen (login/register) + 8-dashboard app shell
│   ├── css/style.css
│   └── js/script.js
├── database/
│   ├── generate_job_postings.py       # generates the 180-posting dataset (M2.1)
│   ├── job_postings.json              # the generated dataset
│   ├── generate_interview_questions.py # generates the 563-question interview bank
│   ├── interview_questions.json        # the generated question bank
│   └── schema.sql                     # reference SQL schema
├── samples/                        # sample resumes for testing extraction
│   ├── sample_resume_1.txt
│   ├── sample_resume_2.txt
│   └── sample_resume_3.txt
└── docs/
    ├── architecture.md
    ├── tech_stack.md
    ├── job_posting_schema.md
    ├── interview_question_bank.md
    └── research_notes.md
```

## Prerequisites

- Python 3.11+
- PostgreSQL installed and running locally
- A GroqCloud API key (recommended) or an OpenAI API key (for resume extraction and job-match reasoning)
- Internet access the first time you run the backend, so
  `sentence-transformers` can download the embedding model (~80MB, one-time,
  then fully offline)
- VS Code (recommended: Python extension + "Live Server" extension for the frontend)

## Setup (step by step, in VS Code's terminal)

### 1. Create the database

Open `psql` (or any PostgreSQL client) and run:

```sql
CREATE DATABASE career_companion;
```

> **Upgrading from a Milestone 1/2 database?** The `students` table now has
> new required columns (`password_hash`, `photo_path`) for the login system.
> Since this project doesn't use migrations (`Base.metadata.create_all` only
> creates tables that don't exist yet — it won't alter existing ones), the
> simplest fix is to drop and recreate the database:
> `DROP DATABASE career_companion; CREATE DATABASE career_companion;`
> then redo steps 3 (seed + build knowledge base) below. You'll need to
> register a fresh account through the app either way, since old profiles
> had no password.

You don't need to run `database/schema.sql` manually — the FastAPI app
creates the tables automatically on first run. It's kept for reference.

### 2. Backend setup

```bash
cd backend
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Create your real .env from the example
cp .env.example .env      # on Windows: copy .env.example .env
```

Now open `backend/.env` and fill in:
- `DATABASE_URL` — your actual Postgres username/password if different from the default
- `GROQ_API_KEY` — your GroqCloud API key from https://console.groq.com/keys
- `GROQ_MODEL` — a model available to your Groq account, for example `openai/gpt-oss-120b`
- `GROQ_BASE_URL=https://api.groq.com/openai/v1`
- `JWT_SECRET_KEY` — any long random string (used to sign login tokens). The
  default placeholder works for local testing, but changing it later logs
  everyone out (existing tokens stop verifying).

The backend uses the OpenAI-compatible SDK against GroqCloud when `GROQ_API_KEY` is
set. If it is empty, it falls back to `OPENAI_API_KEY`, `OPENAI_MODEL`, and
`OPENAI_BASE_URL`. Resume uploads accept PDF, DOCX, and TXT files up to 5 MB.

### 3. Build the internship knowledge base (Milestone 2, one-time)

```bash
# still inside backend/, venv activated

# 1. Load the 180 job postings from database/job_postings.json into Postgres
python seed_job_postings.py

# 2. Chunk + embed + index them into the local vector store
python build_knowledge_base.py

# 3. Load the 563-question mock-interview bank into Postgres
python seed_interview_questions.py
```

Re-run any of these any time you regenerate the corresponding dataset (via
`python ../database/generate_job_postings.py` or
`python ../database/generate_interview_questions.py`) or otherwise change
the data.

### 4. Run the backend

```bash
# from inside backend/, with venv activated
uvicorn app.main:app --reload
```

- API base URL: `http://127.0.0.1:8000`
- Interactive API docs (auto-generated): `http://127.0.0.1:8000/docs`

### 5. Run the frontend

Install the VS Code "Live Server" extension, right-click
`frontend/index.html`, and choose **"Open with Live Server"**. It will
typically serve on `http://127.0.0.1:5500`, which is already whitelisted in
the backend's CORS config (`FRONTEND_ORIGIN` in `.env`).

(Opening `index.html` by double-clicking it also works in most browsers,
but Live Server avoids occasional `file://` quirks.)

### 6. Try the full flow

1. **Register** with your name, email, and a password (6+ characters) → you're logged straight in
2. **Dashboard 01 — Student Profile**: edit your name/phone, upload a profile photo, add skills manually
3. **Dashboard 02 — Upload Resume & Parse**: upload a **PDF under 5 MB** (or one of the files in `samples/`) → **Parse resume** → your structured profile fills in on Dashboard 01
4. **Dashboard 03 — Find Matching Internships**: use the search bar to look up postings yourself (e.g. "machine learning internship using Python"), or click **Find my matches** for the AI-ranked list with a score and a "why this matches" explanation per posting. **Apply** to any posting you like.
5. **Dashboard 04 — Applied Internships**: see everything you've applied to
6. **Dashboard 05 — AI Chat Bot**: pick a specific internship from your matches/applications for a tailored mock interview (grounded in that exact job and your skill gaps), or leave it blank and pick a domain instead for general practice → **Start mock interview** → answer each question by tapping the mic (voice, via your browser's speech recognition) or typing → **Submit for AI Feedback** at the end → see your score, strengths, and an improvement list where each item explains *why* it matters and names real resources to work on it, plus personalized recommendations
7. **Dashboard 06 — My Mock Interviews**: every completed (or in-progress) interview is listed here — click **View details** to re-read the full transcript and feedback any time
8. **Dashboard 07 — Application Toolkit**: pick one internship from the dropdown (populated from your matches/applications), then work through its four tabs — **Skill Gap** (click Analyze), **Tailored Resume** and **Cover Letter** (one click generates both — edit either freely, then Save, or download as .txt), and **Interview Prep** (job-specific questions + guidance + revision topics, grounded in your actual skill gaps if you ran that first)
9. **Dashboard 08 — Career Assistant**: ask anything about your search in plain language — optionally pick a specific internship from the dropdown first so it answers about that one; it remembers the whole conversation and everything else you've generated for that job

Voice input needs a Chrome-based browser (uses the Web Speech API) — it
degrades gracefully to typing in browsers without support, with a message
saying so.

Logging out clears your session; logging back in (or refreshing the page)
restores it from the saved token.

### 7. Test extraction directly (optional, no server needed)

```bash
cd backend
python test_extraction.py
```

Runs the extraction pipeline against every file in `samples/` and prints
the structured JSON output for each.

### 8. Evaluate retrieval + matching (M2.4, optional, no server needed)

```bash
cd backend
python evaluate_matching.py
```

Runs 5 sample student profiles (spanning different domains) through
semantic search and the Matching Agent, printing retrieval relevance and
LLM-scored rankings with reasoning for manual review. Works without an API
key too (falls back to retrieval-only evaluation) — see the script's output
for details.

### 9. End-to-end testing & optimization evaluation (M4.2 / M4.3)

```bash
cd backend

# Baseline vs. optimized retrieval — no LLM key needed, fast
python evaluate_optimization.py

# Full workflow test: profile -> retrieval -> matching -> skill gap ->
# materials -> interview prep -> tracking -> multi-turn chat, with
# per-stage latency and cross-agent consistency checks. Needs an LLM key.
python test_end_to_end.py
```

Both create their own throwaway data (or none at all) and don't touch real
student accounts. `test_end_to_end.py` writes `test_results.json`;
`evaluate_optimization.py` writes `optimization_results.json` — both are
referenced in `docs/Intence_Find_Final_Project_Report.docx` (Sections
11–12) as the source of the project's testing/optimization results.

## API summary

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register` | Create an account (name, email, password) → returns a login token |
| POST | `/auth/login` | Log in (email, password) → returns a login token |
| GET | `/auth/me` | Get the logged-in student's basic info |
| GET | `/students/{id}` | Get a student's basic info (self only) |
| PUT | `/students/{id}` | Update name/phone (self only) |
| PUT | `/students/{id}/skills` | Replace the student's skill list (self only) |
| POST | `/students/{id}/photo` | Upload/replace profile photo (self only) |
| GET | `/students/{id}/profile` | Get the full structured candidate profile (self only) |
| POST | `/students/{id}/resume` | Upload a resume file (self only) |
| POST | `/students/{id}/resume/parse` | Parse the uploaded resume + run LLM extraction (self only) |
| GET | `/jobs/` | List job postings (optionally filter by `domain`) |
| GET | `/jobs/domains` | List all distinct domains in the knowledge base |
| GET | `/jobs/search?q=...` | Semantic search — lets a student search the knowledge base themselves |
| GET | `/jobs/{id}` | Get one job posting |
| POST | `/students/{id}/matches` | Run the Job-Resume Matching Agent, store + return ranked matches (self only) |
| GET | `/students/{id}/matches` | Read back the most recently computed matches (self only) |
| POST | `/students/{id}/applications` | Apply to a job posting (self only) |
| GET | `/students/{id}/applications` | List applied internships (self only) |
| POST | `/students/{id}/interviews` | Start a new 25-question mock interview set for a domain (self only) |
| GET | `/students/{id}/interviews` | List past mock interview sets — the "My Mock Interviews" history (self only) |
| GET | `/students/{id}/interviews/{interview_id}` | Read back one full set (questions, answers, feedback) (self only) |
| POST | `/students/{id}/interviews/{interview_id}/answers` | Save one or more voice/typed answers (self only) |
| POST | `/students/{id}/interviews/{interview_id}/submit` | Finalize the set, run LLM feedback, mark completed (self only) |
| POST | `/students/{id}/skill-gap` | Run the Skill Gap Analysis Agent for one job, save + return categorized gaps (self only) |
| GET | `/students/{id}/skill-gap/{job_posting_id}` | Read back the saved gap analysis for that job (self only) |
| POST | `/students/{id}/materials` | Generate a tailored resume + cover letter for one job (self only) |
| GET | `/students/{id}/materials/{job_posting_id}` | Read back the saved materials for that job (self only) |
| PUT | `/students/{id}/materials/{job_posting_id}` | Save hand-edited resume/cover-letter text (self only) |
| POST | `/students/{id}/interview-prep` | Generate a job-specific interview prep plan (self only) |
| GET | `/students/{id}/interview-prep/{job_posting_id}` | Read back the saved prep plan for that job (self only) |
| GET | `/students/{id}/chat` | Read the full Career Assistant conversation history (self only) |
| POST | `/students/{id}/chat` | Send a message (optionally about a specific job) → assistant's reply (self only) |
| POST | `/students/{id}/saved-jobs` | Bookmark a posting (self only) |
| GET | `/students/{id}/saved-jobs` | List saved postings (self only) |
| DELETE | `/students/{id}/saved-jobs/{job_posting_id}` | Unsave (self only) |
| PATCH | `/students/{id}/applications/{application_id}` | Change status, set/change a reminder deadline, or add notes (self only) |
| GET | `/students/{id}/applications/statuses` | Valid status values, for filter/status dropdowns (self only) |
| GET | `/students/{id}/notifications` | Upcoming deadline reminders — powers the notification bell (self only) |

"Self only" endpoints require the `Authorization: Bearer <token>` header
(the frontend handles this automatically once logged in) and only let a
student act on their own `{id}` — attempting another student's id returns
403.

Full interactive docs (with request/response schemas) are auto-generated at
`/docs` once the server is running. Click **Authorize** there and paste a
token (from a `/auth/login` response) to test protected endpoints directly.

## Notes for the milestones

- All agents through Milestone 3 are now implemented: Resume Agent (M1),
  Job-Resume Matching Agent (M2), Interview Agent / AI Chat Bot (app layer),
  and Skill Gap Analysis, Resume & Cover Letter Customization, job-specific
  Interview Preparation, and the Conversational Career Assistant (M3).
  `docs/architecture.md` has the full diagram, data model, and per-agent
  status table.
- Every agent from Milestone 2 onward follows the same pattern: retrieve or
  assemble real context cheaply (a DB row, a RAG search), then make one
  focused, JSON-constrained LLM call that reasons over that context —
  never inventing facts not present in it. This is worth keeping consistent
  if Milestone 4 adds more agents.
- `docs/architecture.md`'s remaining open item is the Career Assistant
  becoming a true *orchestrator* (deciding which specialist agent to invoke
  and calling it automatically) rather than the current design, where it
  reads other agents' *already-saved* outputs as context and answers
  conversationally — e.g. it can explain an existing skill-gap analysis,
  but won't run a new one for a job that hasn't been analyzed yet. That
  gap, plus richer application statuses (shortlisted/interviewing/
  rejected/offer) beyond the current apply-and-list tracking, are the
  natural next steps if Milestone 4 is orchestration-focused.
- The interview question bank (563 questions, `docs/interview_question_bank.md`)
  and the job-postings dataset (180 postings, `docs/job_posting_schema.md`)
  are both synthetic-but-realistic and versioned rather than scraped —
  the reasoning is the same in both docs, and both are designed to be
  swapped for a real external dataset later without touching the code that
  reads them, if that's ever wanted.
