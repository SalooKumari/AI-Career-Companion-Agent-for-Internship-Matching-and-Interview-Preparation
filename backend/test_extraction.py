"""
Standalone test script for M1.4: "Test extraction on several sample resumes."

Runs the text-extraction + LLM structured-extraction pipeline directly on
the sample resumes in ../samples, without needing the API or database
running. Useful for quickly sanity-checking the extraction quality.

Usage (from the backend/ folder, with .env configured):
    python test_extraction.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.services.resume_extractor import extract_text
from app.services.llm_service import extract_structured_data

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "samples")


def run():
    sample_files = sorted(
        f for f in os.listdir(SAMPLES_DIR) if f.lower().endswith((".txt", ".pdf", ".docx"))
    )

    if not sample_files:
        print(f"No sample resumes found in {SAMPLES_DIR}")
        return

    for filename in sample_files:
        path = os.path.join(SAMPLES_DIR, filename)
        print("=" * 70)
        print(f"Sample: {filename}")
        print("=" * 70)

        raw_text = extract_text(path)
        print(f"[extracted {len(raw_text)} characters of raw text]\n")

        try:
            result = extract_structured_data(raw_text)
            print(json.dumps(result.model_dump(), indent=2))
        except Exception as e:
            print(f"EXTRACTION FAILED: {e}")

        print()


if __name__ == "__main__":
    run()
