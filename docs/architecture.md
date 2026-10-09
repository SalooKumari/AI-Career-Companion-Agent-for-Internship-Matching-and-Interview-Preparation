# System Architecture — AI Career Companion Agent

## 1. High-Level Architecture Diagram

```mermaid
flowchart TB
    subgraph Client["Student / User Interface"]
        UI["Web UI (HTML/CSS/JS)<br/>Auth screen → sidebar-navigated dashboard<br/>(8 dashboards — see Section 6)"]
    end

    subgraph AuthL["Auth Layer"]
        R0["/auth/register, /auth/login, /auth/me<br/>(JWT bearer tokens, bcrypt password hashing)"]
    end

    subgraph API["Backend / API Layer (FastAPI)"]
        R1["/students/{id} — profile read/update<br/>(self-only, JWT-protected)"]
        R2["/students/{id}/resume — upload + parse"]
        R3b["/jobs — browse + semantic search"]
        R3c["/students/{id}/matches — run Matching Agent"]
        R3d["/students/{id}/applications — apply + list"]
        R3e["/students/{id}/interviews — mock interview (25-Q sets)"]
        R3f["/students/{id}/skill-gap — Skill Gap Agent"]
        R3g["/students/{id}/materials — Resume & Cover Letter Agent"]
        R3h["/students/{id}/interview-prep — job-specific Interview Prep Agent"]
        R3i["/students/{id}/chat — Career Assistant"]
    end

    subgraph Storage["Storage"]
        FS["Resume + photo Upload/Storage<br/>(local /uploads, swappable for S3)"]
        DB[("PostgreSQL<br/>Students(+auth) · Resumes · Skills · Education · Experience ·<br/>Projects · JobPostings · Matches · Applications ·<br/>SkillGapAnalyses · ApplicationMaterials · InterviewPrepPlans · ChatMessages")]
    end

    subgraph Processing["Resume Parsing Module"]
        P1["Text Extraction<br/>(pdfplumber / python-docx)"]
        P2["LLM Structured Extraction<br/>(OpenAI API, JSON mode)"]
    end

    subgraph KB["Job-Posting Knowledge Base"]
        JKB[("180 curated job postings<br/>(database/job_postings.json → Postgres)")]
    end

    subgraph RAG["RAG Pipeline"]
        CHUNK["Chunking<br/>(overview / responsibilities / requirements)"]
        EMB["Embedding<br/>(sentence-transformers, local)"]
        VEC[("Vector store — ChromaDB<br/>backend/vector_store/")]
    end

    subgraph Agents["AI Agent Layer — all implemented"]
        CA["Career Assistant<br/>(conversational orchestrator)"]
        MA["Job-Resume Matching Agent"]
        SG["Skill Gap Analysis Agent"]
        RA["Resume Agent<br/>(parsing/extraction)"]
        RC["Resume & Cover Letter<br/>Customization Agent"]
        IA["Interview Agent<br/>(general mock interview,<br/>domain question bank)"]
        IP["Interview Preparation Agent<br/>(job-specific, uses skill gaps)"]
    end

    subgraph Track["Application Tracking Module"]
        AT[("Applications · Status<br/>(basic: apply + list, implemented)")]
    end

    UI -->|register/login| R0
    R0 -->|JWT bearer token| UI
    R0 --> DB
    UI -->|Bearer token + HTTP/JSON| R1
    UI -->|Bearer token + multipart upload| R2
    UI -->|Bearer token + HTTP/JSON| R3c
    UI -->|Bearer token + HTTP/JSON| R3d
    R1 --> DB
    R2 --> FS
    R2 --> P1
    P1 -->|raw text| P2
    P2 -->|structured JSON| DB
    RA -.-> P1 & P2

    JKB --> CHUNK --> EMB --> VEC
    R3b --> VEC
    R3c --> MA
    MA -->|1: profile summary as query| VEC
    VEC -->|candidate shortlist| MA
    MA -->|2: per-candidate reasoning call| LLM_MA["OpenAI API<br/>(score + reasoning)"]
    LLM_MA --> MA
    MA -->|ranked matches| DB
    DB --> R3c
    R3d --> AT
    AT --> DB
    R3e --> IA
    IA --> DB

    R3f --> SG --> DB
    R3g --> RC --> DB
    R3h --> IP
    SG -.->|reuses saved gap analysis, if any| IP
    IP --> DB
    R3i --> CA
    CA -->|reads: matches, skill gaps,<br/>materials, prep, RAG search| DB & VEC
    CA --> DB
```

> **Milestone 1** built the solid Profile/Resume path: UI → API → Storage →
> Resume Parsing Module → Candidate Profile in PostgreSQL.
> **Milestone 2** adds the Job-Posting Knowledge Base, the RAG Pipeline
> (chunk → embed → ChromaDB), and the Job-Resume Matching Agent.
> **App layer** wraps these in a real per-user product: JWT-based
> auth (register/login), every endpoint scoped to "self only" via the
> logged-in token, and a basic Application Tracking Module (apply + list).
> **AI Chat Bot / Mock Interview** adds the general Interview Agent: a
> curated, domain-organized question bank (563 questions across the same
> 19 domains as the job-postings KB — see `docs/interview_question_bank.md`)
> that a student draws a personalized 25-question set from, answers by voice
> or typed text, and submits for LLM-generated feedback — saved in its own
> history tab.
> **Milestone 3** (this update) adds four more agents, all grounded in one
> specific selected internship posting and the student's real profile: the
> *Skill Gap Analysis Agent* (categorized gaps + recommendations), the
> *Resume & Cover Letter Customization Agent* (tailored materials the
> student can edit and download, with an explicit no-fabrication
> constraint), the **job-specific Interview Preparation Agent* (twenty-five
> question categories with per-question guidance + revision topics — reuses
> a saved Skill Gap analysis for that job when one exists, distinct from the
> general Mock Interview bot above), and the **Conversational Career
> Assistant** (a persistent chat that reads the student's profile, top
> matches, and — when a specific job is selected — that job's saved skill
> gap/materials/prep, plus a RAG lookup over the knowledge base when no job
> is selected, so its answers are grounded rather than generic). All four
> are implemented — see the README's "Try the full flow" section for where
> each one lives in the UI.
> Every agent (Milestone 2 onward) follows the same two-stage pattern:
> retrieve/assemble real context cheaply (DB rows, RAG search), then make
> one focused, JSON-constrained LLM call that reasons over that context —
> never inventing facts not present in it.
>**Milestone 4** (this update) *Application tracking model* manage applied roles,
> status update,and deadline remainders. *Conducted End ti End testing* and optimized embedding quality
> qality, prompt report, and final demonstration. **ALL Milestones are completed by sk**

## 2. Agent Responsibilities

| Agent | Status | Responsibility | Primary Inputs | Primary Outputs |
|---|---|---|---|---|
| **Resume Agent** | ✅ Implemented (M1) | Owns resume understanding: parsing, structured extraction. | Uploaded resume file | Structured candidate profile |
| **Job-Resume Matching Agent** | ✅ Implemented (M2) | Retrieves relevant job postings for a candidate via RAG and scores fit with reasoning. | Candidate profile, job KB | Ranked matches with rationale |
| **Interview Agent** | ✅ Implemented | General mock interview: 25-question set (technical + behavioral) from the candidate's matched domain, voice/typed answers, AI feedback + score. | Candidate profile, curated question bank | Q&A transcript, score, feedback |
| **Skill Gap Analysis Agent** | ✅ Implemented (M3.1) | Compares candidate profile against one specific job posting; classifies gaps (critical/partial/preferred/experience/qualification) with reasons and recommendations. | Candidate profile, one job posting | Categorized gap report + recommendations |
| **Resume & Cover Letter Customization Agent** | ✅ Implemented (M3.2) | Generates a tailored resume and cover letter for one specific job, reordering/rewording only what's true — never inventing skills or experience. Student can edit and download both. | Candidate profile, one job posting | Editable tailored resume + cover letter |
| **Interview Preparation Agent** | ✅ Implemented (M3.3) | Job-specific prep: 5 question categories (technical, resume-based, project-based, role-specific, HR) with per-question guidance, plus revision topics — reuses a saved Skill Gap analysis for that job when available. | Candidate profile, one job posting, saved skill gap (if any) | Categorized questions + guidance, revision topics |
| **Career Assistant** | ✅ Implemented (M3.4) | Persistent conversational assistant. Reads profile, top matches, and (per-job) saved gap/materials/prep, plus a RAG lookup when no job is selected. Answers questions, explains fit/gaps, helps with decisions. | Free-form student messages, all other agents' saved outputs, RAG KB | Conversational replies, grounded and personalized |

The Matching Agent's implementation (`backend/app/services/matching_agent.py`)
is a two-stage pipeline, which is the concrete instance of the
Orchestrator/Pipeline pattern discussed in `research_notes.md` M1.3:

1. **Retrieval stage (cheap, no LLM):** the candidate profile is turned into
   a plain-text summary and used as a RAG query against the job-posting
   vector store, returning a shortlist (default 10) of semantically similar
   postings.
2. **Reasoning stage (LLM, one call per shortlisted job):** each candidate
   job is scored against the profile by the OpenAI API, which returns a 0-100
   compatibility score, matched/missing skills, and a short explanation.
   The shortlist is then re-ranked by this score (not just retrieval
   similarity) before returning the top-k.

This keeps the expensive step (LLM reasoning) bounded to a small shortlist
instead of scoring all ~180 postings per request.

## 3. Data Model (Milestone 1 candidate profile + Milestone 2 jobs/matches + app-layer auth/applications + Milestone 3 agent outputs)

```mermaid
erDiagram
    STUDENT ||--o| RESUME : uploads
    STUDENT ||--o{ SKILL : has
    STUDENT ||--o{ EDUCATION : has
    STUDENT ||--o{ EXPERIENCE : has
    STUDENT ||--o{ PROJECT : has
    STUDENT ||--o{ MATCH : "matched against"
    STUDENT ||--o{ APPLICATION : "applied via"
    STUDENT ||--o{ SKILL_GAP_ANALYSIS : "analyzed for"
    STUDENT ||--o{ APPLICATION_MATERIAL : "generated for"
    STUDENT ||--o{ INTERVIEW_PREP_PLAN : "prepared for"
    STUDENT ||--o{ CHAT_MESSAGE : sends
    JOB_POSTING ||--o{ MATCH : "matched to"
    JOB_POSTING ||--o{ APPLICATION : "applied to"
    JOB_POSTING ||--o{ SKILL_GAP_ANALYSIS : "gap-analyzed against"
    JOB_POSTING ||--o{ APPLICATION_MATERIAL : "tailored for"
    JOB_POSTING ||--o{ INTERVIEW_PREP_PLAN : "prepped for"

    JOB_POSTING {
        int id PK
        string job_id
        string title
        string company
        string location
        string domain
        string job_description
        json responsibilities
        json required_skills
        json preferred_skills
        json qualifications
        string experience_requirement
        string education_requirement
        string duration
        int stipend_inr_per_month
    }
    MATCH {
        int id PK
        int student_id FK
        int job_posting_id FK
        int score
        json matched_skills
        json missing_skills
        string reasoning
        int retrieval_rank
        datetime created_at
    }
    APPLICATION {
        int id PK
        int student_id FK
        int job_posting_id FK
        string status
        datetime applied_at
    }
    SKILL_GAP_ANALYSIS {
        int id PK
        int student_id FK
        int job_posting_id FK
        json critical_gaps
        json partial_gaps
        json preferred_gaps
        json experience_gaps
        json qualification_gaps
        json recommendations
        datetime created_at
    }
    APPLICATION_MATERIAL {
        int id PK
        int student_id FK
        int job_posting_id FK
        text resume_content
        text cover_letter_content
        datetime created_at
        datetime updated_at
    }
    INTERVIEW_PREP_PLAN {
        int id PK
        int student_id FK
        int job_posting_id FK
        json technical_questions
        json resume_based_questions
        json project_based_questions
        json role_specific_questions
        json hr_questions
        json revision_topics
        datetime created_at
    }
    CHAT_MESSAGE {
        int id PK
        int student_id FK
        int job_posting_id FK "nullable"
        string role
        text content
        datetime created_at
    }

    STUDENT {
        int id PK
        string full_name
        string email
        string password_hash
        string phone
        string photo_path
        datetime created_at
    }
    RESUME {
        int id PK
        int student_id FK
        string file_name
        string file_path
        string raw_text
        string parse_status
        datetime uploaded_at
    }
    SKILL {
        int id PK
        int student_id FK
        string name
        string category
        string proficiency
    }
    EDUCATION {
        int id PK
        int student_id FK
        string institution
        string degree
        string field_of_study
        string start_date
        string end_date
        string grade
    }
    EXPERIENCE {
        int id PK
        int student_id FK
        string title
        string organization
        string start_date
        string end_date
        string description
    }
    PROJECT {
        int id PK
        int student_id FK
        string title
        string description
        string tech_stack
        string link
    }
```

Design notes:
- One `Student` can have one active `Resume` at a time (Milestone 1); we keep
  the raw text + parse status so re-parsing/debugging is possible without
  re-uploading.
- Skills/Education/Experience/Projects are separate normalized tables (not one
  JSON blob) so the Matching/Gap agents can query, filter, and summarize at
  the row level.
- `JOB_POSTING` (M2) stores the 180-posting knowledge base; list fields
  (`responsibilities`, `required_skills`, etc.) are Postgres `JSON` columns
  since they're read as whole lists, not queried field-by-field.
- `MATCH` (M2) persists each Job-Resume Matching Agent run's results per
  student, so results can be re-displayed without recomputation and so the
  M2.4 evaluation has concrete rows to inspect.
- `STUDENT.password_hash` (bcrypt, never the plain password) and
  `STUDENT.photo_path` support the login system and editable profile photo
  — registering *is* creating the Student row now (`POST /auth/register`),
  rather than the separate profile-creation step from Milestone 1.
- `APPLICATION` records that a student applied to a posting (Dashboard 04
  "Applied Internships"). `status` defaults to `"applied"` and is a plain
  string precisely so Milestone 3 can extend it (shortlisted/rejected/offer)
  without a schema change — this is the seed of the fuller Application
  Tracking Module sketched in Section 1.
- `SKILL_GAP_ANALYSIS`, `APPLICATION_MATERIAL`, and `INTERVIEW_PREP_PLAN`
  (M3.1–M3.3) all share the same shape: one row per `(student_id,
  job_posting_id)` pair, unique-constrained, overwritten on re-generation
  rather than versioned — a student's profile and the job posting can both
  change, so an old analysis/plan/draft isn't worth keeping once a fresh one
  exists. `APPLICATION_MATERIAL` is the one exception the student can edit
  by hand afterward (`PUT /students/{id}/materials/{job_posting_id}`) — that
  hand-edit is overwritten too if they click "regenerate" (frontend warns
  before doing so).
- `CHAT_MESSAGE` (M3.4) is a flat, append-only log per student — one
  continuous thread rather than multiple named sessions, matching "ongoing
  guidance" from the brief. `job_posting_id` is nullable and records which
  job (if any) a given turn was about, so the Career Assistant can favor
  recently-discussed jobs without re-parsing message text.
- Job-posting **chunk embeddings** are *not* in PostgreSQL — they live in a
  separate local ChromaDB store (`backend/vector_store/`), keyed by chunk id
  with `job_posting_id` as metadata linking back to `JOB_POSTING.id`. This
  keeps the relational data (source of truth) and the vector index
  (a rebuildable derived artifact) cleanly separated — the vector store can
  be deleted and rebuilt from Postgres at any time via
  `build_knowledge_base.py`.

## 4. Data Flow: Upload → Parse → Structured Profile

```mermaid
sequenceDiagram
    participant U as Student (UI)
    participant API as FastAPI
    participant FS as File Storage
    participant TX as Text Extractor
    participant LLM as OpenAI API
    participant DB as PostgreSQL

    U->>API: POST /students (profile form)
    API->>DB: INSERT Student
    DB-->>API: student_id
    API-->>U: 201 Created

    U->>API: POST /students/{id}/resume (file)
    API->>FS: save file
    API->>DB: INSERT Resume (parse_status=pending)
    API-->>U: 201 Created (resume_id)

    U->>API: POST /students/{id}/resume/parse
    API->>FS: read file
    API->>TX: extract raw text
    TX-->>API: raw_text
    API->>DB: UPDATE Resume.raw_text
    API->>LLM: prompt(raw_text, JSON schema)
    LLM-->>API: structured JSON (skills, education, experience, projects)
    API->>DB: INSERT Skill/Education/Experience/Project rows
    API->>DB: UPDATE Resume.parse_status=done
    API-->>U: 200 OK (structured profile)

    U->>API: GET /students/{id}/profile
    API->>DB: SELECT joined profile
    DB-->>API: profile rows
    API-->>U: 200 OK (full candidate profile JSON)
```

## 5. Data Flow: Knowledge Base Build → Semantic Search → Matching Agent

```mermaid
sequenceDiagram
    participant Dev as Developer (one-time / on data change)
    participant Seed as seed_job_postings.py
    participant Build as build_knowledge_base.py
    participant DB as PostgreSQL
    participant Chunk as Chunking
    participant Emb as Embedding Model
    participant Vec as ChromaDB

    Dev->>Seed: run
    Seed->>DB: INSERT 180 JobPosting rows (from job_postings.json)

    Dev->>Build: run
    Build->>DB: SELECT all JobPosting rows
    loop each job posting
        Build->>Chunk: build_job_chunks(job)
        Chunk-->>Build: overview / responsibilities / requirements chunks
    end
    Build->>Emb: embed_texts(all chunk texts)
    Emb-->>Build: embedding vectors
    Build->>Vec: upsert(chunk_id, embedding, metadata)

    Note over Dev,Vec: Knowledge base is now ready for retrieval.

    participant U as Student (UI)
    participant API as FastAPI
    participant MA as Matching Agent
    participant LLM as OpenAI API

    U->>API: POST /students/{id}/matches
    API->>MA: run_matching(student_id)
    MA->>DB: load Student + Skills/Education/Experience/Projects
    MA->>MA: build_student_profile_summary()
    MA->>Vec: semantic_search(profile_summary, top_k=10)
    Vec-->>MA: shortlist of candidate JobPostings (deduped, ranked by similarity)
    loop each shortlisted job
        MA->>LLM: score_job_match(profile_summary, job_summary)
        LLM-->>MA: {score, matched_skills, missing_skills, reasoning}
    end
    MA->>MA: sort shortlist by LLM score, keep top-k
    MA->>DB: replace previous Match rows for student, INSERT new ones
    MA-->>API: ranked Match list
    API-->>U: 200 OK (ranked matches with scores + reasoning)
```

## 6. Tech Stack

- **Language:** Python 3.11+
- **Backend:** FastAPI + Uvicorn
- **ORM / DB:** SQLAlchemy + PostgreSQL (`psycopg2-binary`)
- **Validation:** Pydantic v2
- **Resume text extraction:** `pdfplumber` (PDF), `python-docx` (DOCX)
- **Embeddings (M2):** `sentence-transformers` (`all-MiniLM-L6-v2`) — local, no API key needed
- **Vector store (M2):** ChromaDB, embedded/local, persisted to `backend/vector_store/`
- **LLM (structured extraction + match reasoning):** OpenAI API (`openai` SDK)
- **Frontend:** HTML5, CSS3, vanilla JavaScript (Fetch API)
- **Environment/config:** `python-dotenv`
- **Dev tooling:** VS Code, Uvicorn `--reload`, FastAPI auto docs at `/docs`

This document will be updated in-place as each subsequent milestone's brief
arrives, per the instructions given — the dotted-line components in
Section 1 are the ones scheduled for that expansion.
