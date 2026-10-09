"""
M4.3 — Retrieval/matching optimization, measured (not assumed).

Compares two retrieval strategies on the same five sample student profiles
used by evaluate_matching.py (M2.4), with NO LLM calls (so it is free and
fast to run):

  BASELINE   the M2 approach — full profile text (including name and
             institution) as the query, top-K by embedding similarity only.
  OPTIMIZED  the M4.3 approach — signal-only query (no name/institution),
             wide pool of RETRIEVAL_POOL candidates, hybrid re-rank
             (embedding similarity + required/preferred skill overlap),
             top-K of the re-ranked list.

Metrics, per profile and averaged:
  * Domain precision@K  — share of the top-K postings in the profile's
                          manually-defined expected domain(s).
  * Required-skill overlap@K — average fraction of each retrieved
                          posting's REQUIRED skills the student actually has
                          (higher = the shortlist is more genuinely doable).
  * Latency (ms) of the retrieval step.

Usage (from backend/, knowledge base already built):
    python evaluate_optimization.py

Writes optimization_results.json for the project report's
"Testing and Evaluation" / "Results and Analysis" sections.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models import student, job_posting, match, application, interview  # noqa: F401
from app.models.job_posting import JobPosting
from app.services.vector_store import semantic_search
from app.services.matching_agent import (
    RETRIEVAL_POOL, W_SIMILARITY, W_REQUIRED, W_PREFERRED,
    _tokens, skill_overlap_fraction, hybrid_rerank,
)
from evaluate_matching import SAMPLE_PROFILES

TOP_K = 8
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "optimization_results.json")


class _Skill:
    def __init__(self, name):
        self.name = name


class _Project:
    def __init__(self, tech_stack):
        self.tech_stack = tech_stack


class _ProfileFromText:
    """Minimal duck-typed stand-in for a Student, built from the plain-text
    sample profiles, exposing just what hybrid_rerank reads."""

    @staticmethod
    def _split_top_level(text):
        """Split on commas that are NOT inside parentheses, so
        "Python (pandas, numpy), SQL" -> ["Python (pandas, numpy)", "SQL"]."""
        parts, depth, cur = [], 0, ""
        for ch in text:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth = max(0, depth - 1)
            if ch == "," and depth == 0:
                parts.append(cur)
                cur = ""
            else:
                cur += ch
        parts.append(cur)
        return [p.strip() for p in parts if p.strip()]

    def __init__(self, profile_text):
        skills_line = next((l for l in profile_text.splitlines() if l.startswith("Skills:")), "")
        skills = self._split_top_level(skills_line.replace("Skills:", ""))
        self.skills = [_Skill(re.sub(r"\(.*?\)", "", s).strip() or s) for s in skills]
        # expand "Python (pandas, numpy)" style entries into their inner skills too
        for s in skills:
            inner = re.findall(r"\((.*?)\)", s)
            for group in inner:
                self.skills += [_Skill(x.strip()) for x in group.split(",") if x.strip()]
        techs = re.findall(r"\(tech: (.*?)\)", profile_text)
        self.projects = [_Project(t) for t in techs]


def signal_only_query(profile_text):
    """profile_text minus the Name line and minus institution names."""
    lines = []
    for line in profile_text.splitlines():
        if line.startswith("Name:"):
            continue
        if line.startswith("Education:"):
            line = line.split("—")[0].strip()
        lines.append(line)
    return "\n".join(lines)


def metrics(hits, expected_domains, student_sets, jobs_by_id):
    if not hits:
        return {"domain_precision": 0.0, "required_overlap": 0.0}
    in_domain = sum(1 for h in hits if h.get("domain") in expected_domains)
    overlaps = []
    for h in hits:
        job = jobs_by_id.get(h["job_posting_id"])
        if job is not None and job.required_skills:
            overlaps.append(skill_overlap_fraction(student_sets, job.required_skills))
    return {
        "domain_precision": in_domain / len(hits),
        "required_overlap": sum(overlaps) / len(overlaps) if overlaps else 0.0,
    }


def main():
    db = SessionLocal()
    jobs_by_id = {j.id: j for j in db.query(JobPosting).all()}
    if not jobs_by_id:
        print("No job postings in the database. Run seed_job_postings.py + build_knowledge_base.py first.")
        return

    print(f"Parameters: pool={RETRIEVAL_POOL}, top-K={TOP_K}, "
          f"weights sim/required/preferred = {W_SIMILARITY}/{W_REQUIRED}/{W_PREFERRED}\n")

    rows = []
    for profile in SAMPLE_PROFILES:
        expected = set(profile["expected_domains"])
        stud = _ProfileFromText(profile["profile_text"])
        student_sets = [_tokens(s.name) for s in stud.skills] + [
            _tokens(x) for p in stud.projects for x in re.split(r"[,;/]", p.tech_stack)
        ]
        student_sets = [s for s in student_sets if s]

        t0 = time.perf_counter()
        baseline = semantic_search(profile["profile_text"], top_k_jobs=TOP_K)
        t_base = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        pool = semantic_search(signal_only_query(profile["profile_text"]), top_k_jobs=RETRIEVAL_POOL)
        optimized = hybrid_rerank(pool, stud, jobs_by_id)[:TOP_K]
        t_opt = (time.perf_counter() - t0) * 1000

        mb = metrics(baseline, expected, student_sets, jobs_by_id)
        mo = metrics(optimized, expected, student_sets, jobs_by_id)
        rows.append({
            "profile": profile["name"],
            "expected_domains": sorted(expected),
            "baseline": {**mb, "latency_ms": round(t_base, 1)},
            "optimized": {**mo, "latency_ms": round(t_opt, 1)},
        })

    print(f"{'Profile':<16} {'Domain P@K (base -> opt)':<28} {'Req-skill overlap (base -> opt)':<34} {'Latency ms (base -> opt)'}")
    print("-" * 110)
    for r in rows:
        b, o = r["baseline"], r["optimized"]
        print(f"{r['profile']:<16} {b['domain_precision']:>6.0%} -> {o['domain_precision']:<14.0%} "
              f"{b['required_overlap']:>6.0%} -> {o['required_overlap']:<22.0%} "
              f"{b['latency_ms']:>7.1f} -> {o['latency_ms']:.1f}")

    n = len(rows)
    avg = lambda key, side: sum(r[side][key] for r in rows) / n
    print("-" * 110)
    print(f"{'AVERAGE':<16} {avg('domain_precision','baseline'):>6.0%} -> {avg('domain_precision','optimized'):<14.0%} "
          f"{avg('required_overlap','baseline'):>6.0%} -> {avg('required_overlap','optimized'):<22.0%} "
          f"{avg('latency_ms','baseline'):>7.1f} -> {avg('latency_ms','optimized'):.1f}")

    summary = {
        "parameters": {"retrieval_pool": RETRIEVAL_POOL, "top_k": TOP_K,
                       "w_similarity": W_SIMILARITY, "w_required": W_REQUIRED, "w_preferred": W_PREFERRED},
        "per_profile": rows,
        "average": {
            "baseline": {k: avg(k, "baseline") for k in ("domain_precision", "required_overlap", "latency_ms")},
            "optimized": {k: avg(k, "optimized") for k in ("domain_precision", "required_overlap", "latency_ms")},
        },
    }
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {RESULTS_PATH}")
    db.close()


if __name__ == "__main__":
    main()
