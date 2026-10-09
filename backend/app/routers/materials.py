"""Endpoints for the Resume & Cover Letter Customization Agent (M3.2)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_self
from app.models.student import Student
from app.models.job_posting import JobPosting
from app.models.application_material import ApplicationMaterial
from app.schemas.application_material import MaterialRequest, MaterialUpdate, ApplicationMaterialOut
from app.services.application_material_agent import generate_materials

router = APIRouter(prefix="/students", tags=["materials"])


@router.post("/{student_id}/materials", response_model=ApplicationMaterialOut, status_code=201)
def generate(
    student_id: int,
    payload: MaterialRequest,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    job = db.query(JobPosting).filter(JobPosting.id == payload.job_posting_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found.")

    try:
        material = generate_materials(db, current, job)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Application material generation failed: {e}")

    return material


@router.get("/{student_id}/materials/{job_posting_id}", response_model=ApplicationMaterialOut)
def get_materials(
    student_id: int,
    job_posting_id: int,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    material = (
        db.query(ApplicationMaterial)
        .filter(ApplicationMaterial.student_id == student_id, ApplicationMaterial.job_posting_id == job_posting_id)
        .first()
    )
    if not material:
        raise HTTPException(status_code=404, detail="No generated materials for this job yet.")
    return material


@router.put("/{student_id}/materials/{job_posting_id}", response_model=ApplicationMaterialOut)
def update_materials(
    student_id: int,
    job_posting_id: int,
    payload: MaterialUpdate,
    current: Student = Depends(require_self),
    db: Session = Depends(get_db),
):
    """Lets the student review/refine the generated text by hand and save
    their own edits (M3.2: 'Allow the student to review and refine the
    generated application materials')."""
    material = (
        db.query(ApplicationMaterial)
        .filter(ApplicationMaterial.student_id == student_id, ApplicationMaterial.job_posting_id == job_posting_id)
        .first()
    )
    if not material:
        raise HTTPException(status_code=404, detail="No generated materials for this job yet.")

    if payload.resume_content is not None:
        material.resume_content = payload.resume_content
    if payload.cover_letter_content is not None:
        material.cover_letter_content = payload.cover_letter_content

    db.commit()
    db.refresh(material)
    return material
