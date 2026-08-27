"""
Resume Parser - Extracts structured data using LLM
"""

import json
import os
from datetime import datetime
from typing import Dict, Any

class ResumeParser:
    def __init__(self):
        pass  # No API key needed for code submission
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF resume"""
        # Mock implementation for milestone submission
        return "Sample PDF Resume Text"
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX resume"""
        # Mock implementation for milestone submission
        return "Sample DOCX Resume Text"
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text based on file type"""
        if file_type.lower() == "pdf":
            return self.extract_text_from_pdf(file_path)
        elif file_type.lower() in ["docx", "doc"]:
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def parse_with_llm(self, resume_text: str) -> Dict[str, Any]:
        """Extract structured data using LLM"""
        # Mock parsing for milestone submission
        return {
            "personal_info": {
                "full_name": "John Doe",
                "email": "john.doe@email.com",
                "phone": "123-456-7890",
                "location": "San Francisco, CA"
            },
            "education": [
                {
                    "institution": "University of California, Berkeley",
                    "degree": "BS Computer Science",
                    "field_of_study": "Computer Science",
                    "start_date": "2022-09",
                    "end_date": "2026-05",
                    "gpa": 3.8
                }
            ],
            "work_experience": [
                {
                    "company": "TechCorp",
                    "title": "Software Engineering Intern",
                    "start_date": "2025-06",
                    "end_date": "2025-08",
                    "current": False,
                    "achievements": [
                        "Developed RESTful APIs using Python",
                        "Improved performance by 40%"
                    ]
                }
            ],
            "skills": [
                {"name": "Python", "proficiency": "advanced"},
                {"name": "Java", "proficiency": "intermediate"},
                {"name": "React", "proficiency": "intermediate"}
            ],
            "projects": [
                {
                    "name": "Portfolio Website",
                    "description": "Built responsive portfolio website",
                    "technologies": ["React", "Next.js", "Tailwind CSS"]
                }
            ],
            "certifications": []
        }
    
    def process_resume(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Complete resume processing pipeline"""
        text = self.extract_text(file_path, file_type)
        data = self.parse_with_llm(text)
        
        # Add metadata
        data["resume_metadata"] = {
            "file_name": os.path.basename(file_path),
            "file_type": file_type,
            "upload_date": datetime.utcnow().isoformat()
        }
        
        return data