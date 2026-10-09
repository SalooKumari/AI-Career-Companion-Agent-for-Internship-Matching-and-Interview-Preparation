"""
Endpoints for reading and updating a student's own profile — Dashboard 1
"Student Profile" (M1 foundation, extended for editable profile + photo).
Registration/login now live in app/routers/auth.py.
"""
import os
import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_self
from app.models.student import Student, Skill
from app.schemas.student import (
    StudentOut, StudentUpdate, CandidateProfileOut, SkillsUpdate, SkillOut,
)

router = APIRouter(prefix="/students", tags=["students"])

ALLOWED_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, current: Student = Depends(require_self), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student


@router.put("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    """Lets a student update their own name/phone from the Profile dashboard."""
    if payload.full_name is not None:
        current.full_name = payload.full_name
    if payload.phone is not None:
        current.phone = payload.phone

    db.commit()
    db.refresh(current)
    return current


@router.put("/{student_id}/skills", response_model=list[SkillOut])
def update_skills(
    student_id: int,
    payload: SkillsUpdate,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    """Replaces the student's skill list — used both after resume parsing
    and for manual edits on the Profile dashboard."""
    db.query(Skill).filter(Skill.student_id == student_id).delete()
    for s in payload.skills:
        db.add(Skill(student_id=student_id, name=s.name, category=s.category, proficiency=s.proficiency))
    db.commit()
    return db.query(Skill).filter(Skill.student_id == student_id).all()


@router.post("/{student_id}/photo", response_model=StudentOut)
def upload_photo(
    student_id: int,
    file: UploadFile = File(...),
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_PHOTO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type '{ext}'. Use JPG, PNG, or WEBP.",
        )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    stored_filename = f"photo_{student_id}_{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(settings.UPLOAD_DIR, stored_filename)

    with open(stored_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current.photo_path = stored_path
    db.commit()
    db.refresh(current)
    return current


@router.get("/{student_id}/profile", response_model=CandidateProfileOut)
def get_candidate_profile(student_id: int, current: Student = Depends(require_self), db: Session = Depends(get_db)):
    """Returns the full structured profile: student + resume + skills +
    education + experience + projects."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    return CandidateProfileOut(
        student=student,
        resume=student.resume,
        skills=student.skills,
        education=student.education,
        experience=student.experience,
        projects=student.projects,
    )
