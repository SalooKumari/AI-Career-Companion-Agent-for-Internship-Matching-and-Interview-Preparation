"""
Pydantic schemas: what the API accepts (Create) and returns (Out).
Kept separate from SQLAlchemy models so the DB layer can change independently
of the API contract.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Student ----------

class StudentCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None


class StudentUpdate(BaseModel):
    """Fields a student can edit on their own profile."""
    full_name: Optional[str] = None
    phone: Optional[str] = None


class StudentOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    photo_path: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Resume ----------

class ResumeOut(BaseModel):
    id: int
    student_id: int
    file_name: str
    parse_status: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Extracted profile sub-objects ----------

class SkillOut(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    proficiency: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EducationOut(BaseModel):
    id: int
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    grade: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ExperienceOut(BaseModel):
    id: int
    title: str
    organization: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    link: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CandidateProfileOut(BaseModel):
    """The full structured profile returned by GET /students/{id}/profile"""
    student: StudentOut
    resume: Optional[ResumeOut] = None
    skills: List[SkillOut] = []
    education: List[EducationOut] = []
    experience: List[ExperienceOut] = []
    projects: List[ProjectOut] = []


# ---------- LLM extraction contract (internal) — also reused for manual edits ----------

class ExtractedSkill(BaseModel):
    name: str
    category: Optional[str] = None
    proficiency: Optional[str] = None


class ExtractedEducation(BaseModel):
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    grade: Optional[str] = None


class ExtractedExperience(BaseModel):
    title: str
    organization: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class ExtractedProject(BaseModel):
    title: str
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    link: Optional[str] = None


class ExtractedResumeData(BaseModel):
    """The exact JSON shape we instruct the LLM to return."""
    skills: List[ExtractedSkill] = []
    education: List[ExtractedEducation] = []
    experience: List[ExtractedExperience] = []
    projects: List[ExtractedProject] = []


class SkillsUpdate(BaseModel):
    """Body for PUT /students/{id}/skills — lets a student manually edit
    their skill list from the Profile dashboard (in addition to whatever
    the resume parser extracted)."""
    skills: List[ExtractedSkill]
