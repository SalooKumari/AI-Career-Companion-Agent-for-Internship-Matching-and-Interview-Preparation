# Milestone 2: Knowledge Base, RAG & Job-Resume Matching

## M2.1 — Internship Knowledge Base
- Curate dataset of 150-200 sample job/internship postings
- Cover multiple domains (19 domains span)
- Define structured schema: title, company, required skills, 
  preferred skills, qualifications, responsibilities
- Store in database for retrieval

## M2.2 — RAG Pipeline
- Design chunking strategy for job postings
- Generate embeddings for each chunk
- Build vector store index
- Implement semantic search endpoint
- Test retrieval relevance on sample queries

## M2.3 — Job-Resume Matching Agent
- Build Matching Agent that retrieves relevant postings via RAG
- Score compatibility across factors:
  - Skills match
  - Education fit
  - Projects relevance
  - Domain fit
- Return match score + reasoning for each match
- Rank results by hybrid score

## M2.4 — Validation & Evaluation
- Test matching accuracy on 5 sample student profiles
- Measure retrieval precision@K
- Evaluate ranking quality across different domains
- Document baseline vs. observed results

## Deliverables
- 150-200 posting knowledge base
- Working RAG pipeline with semantic search
- Job-Resume Matching Agent with reasoning
- Evaluation report with retrieval + matching metrics

## Status
✅ Completed
