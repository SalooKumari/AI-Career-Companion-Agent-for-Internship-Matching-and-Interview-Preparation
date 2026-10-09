-- Reference schema for the AI Career Companion Agent (Milestone 1).
-- NOTE: The FastAPI app creates these tables automatically on startup via
-- SQLAlchemy (Base.metadata.create_all). This file is kept for reference,
-- manual inspection, and so the schema is visible without running the app.

CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(30),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS resumes (
    id SERIAL PRIMARY KEY,
    student_id INTEGER UNIQUE NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    raw_text TEXT,
    parse_status VARCHAR(20) DEFAULT 'pending',
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    name VARCHAR(120) NOT NULL,
    category VARCHAR(60),
    proficiency VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS education (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    institution VARCHAR(200) NOT NULL,
    degree VARCHAR(150),
    field_of_study VARCHAR(150),
    start_date VARCHAR(30),
    end_date VARCHAR(30),
    grade VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS experience (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    organization VARCHAR(200),
    start_date VARCHAR(30),
    end_date VARCHAR(30),
    description TEXT
);

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    tech_stack VARCHAR(255),
    link VARCHAR(300)
);

-- Milestone 2: internship knowledge base -----------------------------------

CREATE TABLE IF NOT EXISTS job_postings (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(150) NOT NULL,
    company VARCHAR(150) NOT NULL,
    location VARCHAR(100) NOT NULL,
    domain VARCHAR(80),
    job_description TEXT NOT NULL,
    responsibilities JSON NOT NULL DEFAULT '[]',
    required_skills JSON NOT NULL DEFAULT '[]',
    preferred_skills JSON NOT NULL DEFAULT '[]',
    qualifications JSON NOT NULL DEFAULT '[]',
    experience_requirement VARCHAR(255),
    education_requirement VARCHAR(255),
    duration VARCHAR(30),
    stipend_inr_per_month INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Milestone 2: Job-Resume Matching Agent results -----------------------------

CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    job_posting_id INTEGER NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    matched_skills JSON NOT NULL DEFAULT '[]',
    missing_skills JSON NOT NULL DEFAULT '[]',
    reasoning TEXT NOT NULL,
    retrieval_rank INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Note: chunk embeddings for semantic search are NOT stored in Postgres —
-- they live in a local ChromaDB store under backend/vector_store/, keyed by
-- chunk id with job_posting_id as metadata. See docs/architecture.md.
