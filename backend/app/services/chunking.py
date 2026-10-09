"""
Splits a job posting into a small number of meaningful chunks for
embedding (M2.2). Rather than treating the whole posting as one blob, or
splitting arbitrarily by character count, we split by *semantic section* —
each chunk is a coherent unit a query is likely to match against on its own:

  - "overview"        -> title, company, location, description
  - "responsibilities" -> what the intern will actually do day to day
  - "requirements"     -> skills, qualifications, experience, education

This means a skills-heavy query ("Python and TensorFlow internship")
matches strongly against the requirements chunk even if the overview text
is generic, and a role-flavour query ("internship building mobile apps")
matches the overview/responsibilities chunk even if it doesn't name a
specific tool. Retrieval later de-duplicates back to one job per result.
"""
from typing import List, Dict


def build_job_chunks(job: Dict) -> List[Dict]:
    """
    job: a dict with the JobPosting fields (title, company, location,
    domain, job_description, responsibilities, required_skills,
    preferred_skills, qualifications, experience_requirement,
    education_requirement, id).

    Returns a list of chunk dicts: {chunk_id, job_posting_id, chunk_type, text}
    """
    job_id = job["id"]
    chunks = []

    overview_text = (
        f"{job['title']} at {job['company']} ({job['location']}). "
        f"{job['job_description']}"
    )
    chunks.append({
        "chunk_id": f"{job_id}_overview",
        "job_posting_id": job_id,
        "chunk_type": "overview",
        "text": overview_text,
    })

    if job.get("responsibilities"):
        resp_text = "Responsibilities: " + "; ".join(job["responsibilities"])
        chunks.append({
            "chunk_id": f"{job_id}_responsibilities",
            "job_posting_id": job_id,
            "chunk_type": "responsibilities",
            "text": resp_text,
        })

    requirement_parts = []
    if job.get("required_skills"):
        requirement_parts.append("Required skills: " + ", ".join(job["required_skills"]))
    if job.get("preferred_skills"):
        requirement_parts.append("Preferred skills: " + ", ".join(job["preferred_skills"]))
    if job.get("qualifications"):
        requirement_parts.append("Qualifications: " + "; ".join(job["qualifications"]))
    if job.get("experience_requirement"):
        requirement_parts.append(f"Experience required: {job['experience_requirement']}")
    if job.get("education_requirement"):
        requirement_parts.append(f"Education required: {job['education_requirement']}")

    if requirement_parts:
        chunks.append({
            "chunk_id": f"{job_id}_requirements",
            "job_posting_id": job_id,
            "chunk_type": "requirements",
            "text": " ".join(requirement_parts),
        })

    return chunks
