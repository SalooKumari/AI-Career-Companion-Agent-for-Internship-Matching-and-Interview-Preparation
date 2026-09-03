# System Architecture

## Architecture Diagram

```mermaid
graph TB
    subgraph "Presentation Layer"
        Student[Student/User]
        UI[Streamlit Frontend]
    end

    subgraph "API Layer"
        API[FastAPI Backend]
        ProfileService[Student Profile Service]
        ResumeService[Resume Service]
    end

    subgraph "Resume Processing Layer"
        Upload[Resume Upload]
        Parser[PDF/DOCX Parser]
        Clean[Text Cleaning]
        Raw[Raw Resume Text]
    end

    subgraph "LLM Layer"
        LLM[LLM-based Resume Information Extraction]
        API_Call[External LLM API]
        JSON[Structured JSON]
        Validate[Validation]
        OpenAI[OpenAI / Anthropic]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL Database)]
        Storage[Cloud/File Storage]
        
        subgraph "Student Profile"
            S1[Student]
            S2[Resume]
            S3[Education]
            S4[Skills]
            S5[Experience]
            S6[Projects]
            S7[Certifications]
        end
    end

    subgraph "Future Components"
        RAG[RAG Pipeline]
        Matching[Internship Matching]
        Interview[Interview Prep]
        Advisor[Career Advisor]
    end

    Student --> UI
    UI --> API
    API --> ProfileService
    API --> ResumeService
    
    ProfileService --> DB
    ResumeService --> Upload
    
    Upload --> Parser
    Parser --> Clean
    Clean --> Raw
    Raw --> LLM
    
    LLM --> API_Call
    API_Call --> OpenAI
    LLM --> JSON
    JSON --> Validate
    Validate --> DB
    
    DB --> Storage
    Storage --> S1
    Storage --> S2
    Storage --> S3
    Storage --> S4
    Storage --> S5
    Storage --> S6
    Storage --> S7
    
    DB -.-> RAG
    RAG -.-> Matching
    Matching -.-> Interview
    Interview -.-> Advisor
