"""
Resume & Cover Letter Customization Agent (M3.2).

Generates a tailored resume + cover letter for one specific (student, job)
pair and saves both. Re-running overwrites the previous generation, but the
student can also hand-edit the saved content afterward (see
routers/materials.py PUT endpoint) — regenerating overwrites those edits
too, which the frontend warns about before calling it.
"""
from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.job_posting import JobPosting
from app.models.application_material import ApplicationMaterial
from app.services.matching_agent import build_student_profile_summary, build_job_posting_summary
from app.services.llm_service import generate_application_materials as llm_generate_materials


def generate_materials(db: Session, student: Student, job: JobPosting) -> ApplicationMaterial:
    profile_summary = build_student_profile_summary(student)
    job_summary = build_job_posting_summary(job)

    result = llm_generate_materials(profile_summary, job_summary)

    existing = (
        db.query(ApplicationMaterial)
        .filter(ApplicationMaterial.student_id == student.id, ApplicationMaterial.job_posting_id == job.id)
        .first()
    )

    if existing:
        existing.resume_content = result.resume_content
        existing.cover_letter_content = result.cover_letter_content
        material = existing
    else:
        material = ApplicationMaterial(
            student_id=student.id,
            job_posting_id=job.id,
            resume_content=result.resume_content,
            cover_letter_content=result.cover_letter_content,
        )
        db.add(material)

    db.commit()
    db.refresh(material)
    return material
