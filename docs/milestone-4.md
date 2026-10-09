# Milestone 4: Application Tracking, Testing & Documentation

## M4.1 — Application Tracking Module
- Application model with 8-stage lifecycle:
  applied → under_review → shortlisted → interview_scheduled 
  → interview_completed → offer_received / rejected / withdrawn
- Track: company, title, description, dates, status, notes, 
  linked tailored materials
- Saved jobs (bookmarking) as separate lightweight table
- Deadline + interview reminders (5-day lookahead + overdue state)
- Search / filter / sort on dashboard
- Overview stats row via /applications/stats
- Dashboard 04 + top bar navigation

## M4.2 — End-to-End Testing
- evaluate_matching.py — retrieval relevance + match ranking 
  across 5 sample profiles
- evaluate_optimization.py — baseline vs optimized retrieval 
  (domain precision@K, skill overlap@K, latency)
- test_end_to_end.py — full workflow from profile → retrieval 
  → matching → skill gap → materials → interview prep → 
  tracking → multi-turn conversation
- Cross-agent consistency check (matched skills vs critical gaps)
- Machine-readable JSON outputs (test_results.json)

## M4.3 — Optimization
- Signal-only retrieval query (skills, field, projects, 
  experience titles — no name/institution noise)
- Widen retrieval pool (10 → 20 candidates)
- Hybrid re-ranking: 
  0.55×similarity + 0.35×(required-skill overlap) 
  + 0.10×(preferred-skill overlap)
- Send only top 8 to LLM
- Restructure score_job_match prompt for 4 named factor scores
- Harden Career Assistant prompt (grounding, consistency, 
  reference resolution)
- Structured interview feedback (area, why it matters, 
  named resources)

## M4.4 — Documentation & Final Demo
- Technical documentation (architecture, agents, APIs)
- Project report (milestones, results, analysis)
- Final demonstration walkthrough
- Submission of GitHub repo link + architecture + tech stack

## Deliverables
- Working application tracking module with dashboard
- 3 automated test scripts
- Measured optimization results (baseline vs optimized)
- Technical documentation + project report
- Final demo

## Status
✅ Completed
