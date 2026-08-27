"""
Candidate/Student Profile Data Model
"""

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, EmailStr
from uuid import UUID, uuid4

class PersonalInfo(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None

class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[float] = None

class WorkExperience(BaseModel):
    company: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    current: bool = False
    achievements: List[str] = []

class Skill(BaseModel):
    name: str
    proficiency: str

class Project(BaseModel):
    name: str
    description: str
    technologies: List[str] = []

class CandidateProfile(BaseModel):
    profile_id: UUID = uuid4()
    student_id: str
    personal_info: PersonalInfo
    education: List[Education] = []
    work_experience: List[WorkExperience] = []
    skills: List[Skill] = []
    projects: List[Project] = []
    resume_metadata: Optional[Dict] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()