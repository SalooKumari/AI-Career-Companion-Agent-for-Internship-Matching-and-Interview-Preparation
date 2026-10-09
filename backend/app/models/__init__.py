"""
SQLAlchemy models registration package.
Exporting all models here ensures all table definitions and relationships
are registered with Base.metadata regardless of which model is imported first.
"""
from app.models.student import Student, Resume, Skill, Education, Experience, Project
from app.models.job_posting import JobPosting
from app.models.match import Match
from app.models.application import Application
from app.models.saved_job import SavedJob
from app.models.interview import InterviewBankQuestion, InterviewSet, InterviewSetQuestion, InterviewFeedback
from app.models.skill_gap import SkillGapAnalysis
from app.models.application_material import ApplicationMaterial
from app.models.interview_prep import InterviewPrepPlan
from app.models.chat import ChatMessage

__all__ = [
    "Student",
    "Resume",
    "Skill",
    "Education",
    "Experience",
    "Project",
    "JobPosting",
    "Match",
    "Application",
    "SavedJob",
    "InterviewBankQuestion",
    "InterviewSet",
    "InterviewSetQuestion",
    "InterviewFeedback",
    "SkillGapAnalysis",
    "ApplicationMaterial",
    "InterviewPrepPlan",
    "ChatMessage",
]
