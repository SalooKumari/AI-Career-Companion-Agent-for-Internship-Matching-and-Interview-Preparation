# Technology Stack

## Complete Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Presentation Layer** | React / Next.js | Student user interface |
| **API Layer** | FastAPI | Backend REST API framework |
| **Resume Processing** | PDF/DOCX Parser, Text Cleaning | Extract raw text from resumes |
| **LLM Layer** | OpenAI GPT-4 / Anthropic Claude | Resume information extraction |
| **Database** | PostgreSQL | Store student profiles and data |
| **Storage** | Cloud/File Storage (AWS S3) | Store uploaded resume files |
| **Future Components** | RAG Pipeline, LangChain | Internship matching, interview prep |

## Detailed Layer Description

### 1. Presentation Layer
- **React / Next.js**: Frontend framework for student interface
- Responsive design for desktop and mobile
- Resume upload drag-and-drop functionality

### 2. API Layer
- **FastAPI**: Python-based REST API framework
- Student Profile Service: CRUD operations
- Resume Service: Upload and processing endpoints
- Automatic OpenAPI documentation

### 3. Resume Processing Layer
- **PDF/DOCX Parser**: Extract text from uploaded resumes
- **Text Cleaning**: Remove noise, normalize text
- Output: Clean raw resume text ready for LLM

### 4. LLM Layer
- **OpenAI GPT-4** or **Anthropic Claude**
- Extract structured information from resume text
- Output: Structured JSON with education, skills, experience, projects
- Validation: Data quality checks

### 5. Database Layer
- **PostgreSQL**: Primary relational database
- Stores: Student profiles, resumes, education, skills, experience, projects, certifications
- JSON support for flexible data storage

### 6. Storage Layer
- **Cloud/File Storage (AWS S3)**: Store uploaded resume files
- Secure file access
- Version management

### 7. Future Components
- **RAG Pipeline**: Retrieval-Augmented Generation for job matching
- **LangChain**: Agent framework for multi-agent system
- **Internship Matching Agent**: Match students with internships
- **Interview Prep Agent**: Mock interview generation
- **Career Advisor Agent**: Orchestrator agent

## Why These Choices?

| Technology | Reason |
|------------|--------|
| React/Next.js | Popular, component-based, excellent ecosystem |
| FastAPI | Fast, async, automatic API docs |
| PostgreSQL | Reliable, ACID compliance, JSON support |
| OpenAI/Anthropic | Best-in-class LLM, structured output |
| AWS S3 | Scalable, secure file storage |
| LangChain | Industry standard for agent frameworks |

## Data Flow Summary
