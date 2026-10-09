"""
FastAPI application entrypoint.
Run with: uvicorn app.main:app --reload   (from the backend/ folder)
Docs available at http://127.0.0.1:8000/docs
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine
from app.models import (  # noqa: F401 (register all models before create_all)
    student, job_posting, match, application, interview,
    skill_gap, application_material, interview_prep, chat, saved_job,
)
from app.routers import (
    auth, students, resumes, jobs, matches, applications, interviews,
    skill_gap as skill_gap_router, materials, interview_prep as interview_prep_router, chat as chat_router,
    saved_jobs, notifications,
)

# Create tables if they don't exist yet (fine for dev; use Alembic migrations later)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Career Companion Agent — API",
    description=(
        "Milestone 1: Candidate profile creation, resume upload, and LLM-based structured extraction. "
        "Milestone 2: Internship knowledge base, RAG semantic search, and the Job-Resume Matching Agent. "
        "Milestone 3: Skill Gap Analysis, Resume & Cover Letter Customization, job-specific Interview Prep, "
        "and the Conversational Career Assistant. "
        "Milestone 4: full Application Tracking Module (status workflow, saved jobs, deadline notifications) "
        "and a multi-factor Job-Resume match score breakdown. "
        "App layer: authentication (register/login), applied-internships tracking, and the AI Chat Bot mock interview feature."
    ),
    version="0.6.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5500", "http://127.0.0.1:5500", "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded profile photos (not resumes — those stay private) at /uploads/<filename>
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(matches.router)
app.include_router(applications.router)
app.include_router(saved_jobs.router)
app.include_router(notifications.router)
app.include_router(interviews.router)
app.include_router(skill_gap_router.router)
app.include_router(materials.router)
app.include_router(interview_prep_router.router)
app.include_router(chat_router.router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "ai-career-companion-agent", "milestone": 3}
