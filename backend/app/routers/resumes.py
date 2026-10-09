"""
Endpoints for resume upload and resume parsing + LLM structured extraction.
This is the M1.3 / M1.4 pipeline: upload -> extract raw text -> LLM extract
structured fields -> store in candidate profile tables.
"""
import os
import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_self
from app.models.student import Student, Resume, Skill, Education, Experience, Project
from app.schemas.student import ResumeOut, CandidateProfileOut
from app.services.resume_extractor import extract_text, UnsupportedFileTypeError
from app.services.llm_service import extract_structured_data

router = APIRouter(prefix="/students", tags=["resumes"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/{student_id}/resume", response_model=ResumeOut, status_code=201)
def upload_resume(
    student_id: int,
    file: UploadFile = File(...),
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    student = current

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, or TXT resumes are accepted.",
        )

    file.file.seek(0, os.SEEK_END)
    size_bytes = file.file.tell()
    file.file.seek(0)
    if size_bytes > MAX_RESUME_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="PDF is larger than 5 MB.",
        )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    stored_filename = f"{student_id}_{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(settings.UPLOAD_DIR, stored_filename)

    with open(stored_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # One resume per student for Milestone 1: replace if one already exists
    existing_resume = db.query(Resume).filter(Resume.student_id == student_id).first()
    if existing_resume:
        db.delete(existing_resume)
        db.flush()

    resume = Resume(
        student_id=student_id,
        file_name=file.filename,
        file_path=stored_path,
        parse_status="pending",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.post("/{student_id}/resume/parse", response_model=CandidateProfileOut)
def parse_resume(student_id: int, current: Student = Depends(require_self), db: Session = Depends(get_db)):
    """Extracts raw text, calls the LLM for structured extraction, and
    stores the results in the Skill/Education/Experience/Project tables."""
    student = current

    resume = db.query(Resume).filter(Resume.student_id == student_id).first()
    if not resume:
        raise HTTPException(
            status_code=404, detail="No resume uploaded for this student yet."
        )

    try:
        raw_text = extract_text(resume.file_path)
    except UnsupportedFileTypeError as e:
        resume.parse_status = "failed"
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        resume.parse_status = "failed"
        db.commit()
        raise HTTPException(status_code=422, detail=f"Could not read the resume file: {e}")

    if not raw_text:
        resume.parse_status = "failed"
        db.commit()
        raise HTTPException(
            status_code=422,
            detail="Could not extract any text from the resume file.",
        )

    resume.raw_text = raw_text

    try:
        extracted = extract_structured_data(raw_text)
    except Exception as e:
        resume.parse_status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=f"LLM extraction failed: {e}")

    # Clear previous extraction results before inserting fresh ones
    db.query(Skill).filter(Skill.student_id == student_id).delete()
    db.query(Education).filter(Education.student_id == student_id).delete()
    db.query(Experience).filter(Experience.student_id == student_id).delete()
    db.query(Project).filter(Project.student_id == student_id).delete()

    for s in extracted.skills:
        db.add(Skill(student_id=student_id, name=s.name, category=s.category, proficiency=s.proficiency))

    for ed in extracted.education:
        db.add(Education(
            student_id=student_id, institution=ed.institution, degree=ed.degree,
            field_of_study=ed.field_of_study, start_date=ed.start_date,
            end_date=ed.end_date, grade=ed.grade,
        ))

    for exp in extracted.experience:
        db.add(Experience(
            student_id=student_id, title=exp.title, organization=exp.organization,
            start_date=exp.start_date, end_date=exp.end_date, description=exp.description,
        ))

    for p in extracted.projects:
        db.add(Project(
            student_id=student_id, title=p.title, description=p.description,
            tech_stack=p.tech_stack, link=p.link,
        ))

    resume.parse_status = "done"
    db.commit()
    db.refresh(student)

    return CandidateProfileOut(
        student=student,
        resume=resume,
        skills=student.skills,
        education=student.education,
        experience=student.experience,
        projects=student.projects,
    )
