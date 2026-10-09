"""
SQLAlchemy ORM models for the candidate profile domain.
Matches the ER diagram in docs/architecture.md.
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=True)
    photo_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="student", uselist=False, cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="student", cascade="all, delete-orphan")
    education = relationship("Education", back_populates="student", cascade="all, delete-orphan")
    experience = relationship("Experience", back_populates="student", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="student", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="student", cascade="all, delete-orphan")
    saved_jobs = relationship("SavedJob", back_populates="student", cascade="all, delete-orphan")
    interview_sets = relationship("InterviewSet", back_populates="student", cascade="all, delete-orphan")
    skill_gap_analyses = relationship("SkillGapAnalysis", back_populates="student", cascade="all, delete-orphan")
    application_materials = relationship("ApplicationMaterial", back_populates="student", cascade="all, delete-orphan")
    interview_prep_plans = relationship("InterviewPrepPlan", back_populates="student", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="student", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, unique=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    raw_text = Column(Text, nullable=True)
    parse_status = Column(String(20), default="pending")  # pending | done | failed
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="resume")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    name = Column(String(120), nullable=False)
    category = Column(String(60), nullable=True)      # e.g. "programming", "tool", "soft-skill"
    proficiency = Column(String(30), nullable=True)    # e.g. "beginner", "intermediate", "advanced"

    student = relationship("Student", back_populates="skills")


class Education(Base):
    __tablename__ = "education"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    institution = Column(String(200), nullable=False)
    degree = Column(String(150), nullable=True)
    field_of_study = Column(String(150), nullable=True)
    start_date = Column(String(30), nullable=True)
    end_date = Column(String(30), nullable=True)
    grade = Column(String(30), nullable=True)

    student = relationship("Student", back_populates="education")


class Experience(Base):
    __tablename__ = "experience"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    title = Column(String(150), nullable=False)
    organization = Column(String(200), nullable=True)
    start_date = Column(String(30), nullable=True)
    end_date = Column(String(30), nullable=True)
    description = Column(Text, nullable=True)

    student = relationship("Student", back_populates="experience")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    tech_stack = Column(String(255), nullable=True)
    link = Column(String(300), nullable=True)

    student = relationship("Student", back_populates="projects")
