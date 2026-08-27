"""
Unit tests for resume parser
"""

import pytest
from backend.app.services.resume_parser import ResumeParser

class TestResumeParser:
    """Test cases for ResumeParser class"""
    
    def setup_method(self):
        """Setup before each test"""
        self.parser = ResumeParser()
    
    def test_parse_software_engineer_resume(self):
        """Test parsing software engineer resume"""
        sample_text = """
        JOHN DOE
        john.doe@email.com | (123) 456-7890 | San Francisco, CA
        
        EDUCATION
        University of California, Berkeley
        BS Computer Science, Expected May 2026
        GPA: 3.8
        
        TECHNICAL SKILLS
        Python, Java, JavaScript, React, Node.js
        
        EXPERIENCE
        Software Engineering Intern | TechCorp | June 2025 - Aug 2025
        - Developed RESTful APIs using Python
        - Improved performance by 40%
        
        PROJECTS
        Portfolio Website | React, Next.js
        - Built responsive website
        """
        
        result = self.parser.parse_with_llm(sample_text)
        
        # Verify structure
        assert "personal_info" in result
        assert result["personal_info"]["full_name"] == "John Doe"
        assert "education" in result
        assert "skills" in result
        assert "work_experience" in result
        assert len(result.get("skills", [])) > 0
        
        print("✅ Test passed for software engineer resume!")
    
    def test_parse_marketing_resume(self):
        """Test parsing marketing student resume"""
        sample_text = """
        SARAH SMITH
        sarah.smith@email.com | (987) 654-3210 | Austin, TX
        
        EDUCATION
        University of Texas at Austin
        BBA Marketing, May 2026
        GPA: 3.7
        
        EXPERIENCE
        Marketing Intern | SocialFlow Agency | Jan 2025 - Present
        - Managed social media accounts
        - Increased engagement by 25%
        
        SKILLS
        Google Analytics, SEO, Social Media
        """
        
        result = self.parser.parse_with_llm(sample_text)
        
        assert "personal_info" in result
        assert result["personal_info"]["full_name"] == "Sarah Smith"
        assert len(result.get("work_experience", [])) > 0
        
        print("✅ Test passed for marketing resume!")
    
    def test_parse_empty_resume(self):
        """Test parsing empty resume"""
        result = self.parser.parse_with_llm("")
        
        assert "personal_info" in result
        assert "education" in result
        print("✅ Test passed for empty resume!")

if __name__ == "__main__":
    # Run all tests
    parser = ResumeParser()
    
    # Test 1: Software Engineer
    sample1 = """
    JOHN DOE
    john.doe@email.com | (123) 456-7890
    
    SKILLS: Python, Java, React
    """
    result1 = parser.parse_with_llm(sample1)
    assert "personal_info" in result1
    print("✅ Test 1 passed!")
    
    # Test 2: Marketing
    sample2 = """
    SARAH SMITH
    sarah@email.com | (987) 654-3210
    
    SKILLS: Google Analytics, SEO
    """
    result2 = parser.parse_with_llm(sample2)
    assert "personal_info" in result2
    print("✅ Test 2 passed!")
    
    print("\n🎉 All tests passed successfully! ")