# JobHunter Bot — Project Brief

**Author**: Mary (BMAD Analyst)
**Date**: 2026-04-30
**Status**: Phase 1 — Discovery

## 1. Project name
JobHunter — Personal opportunity-finder bot for Tabish Hassan

## 2. Owner profile
- **Name**: Tabish Hassan
- **Role**: React.js Frontend Developer (4+ yrs)
- **Stack sold**: React, TypeScript, Tailwind, Material UI, Redux/Zustand, Framer Motion
- **Stack learning (don't sell)**: Node.js, Express, MongoDB (since Dec 2025)
- **Location**: Rawalpindi, Pakistan (UTC+5)
- **Availability**: Immediate, full-time + freelance + contracts
- **Constraint**: Pakistan-based — needs remote-only roles, no on-site, no citizenship-required, no relocation
- **Rate range**: $5–$50/hr (preferred $15/hr+)
- **Reject**: gambling, casino, adult, crypto/blockchain trading, backend-only roles

## 3. Current bot state (as observed)
- 6 board sources (Remotive, RemoteOK, Himalayas, Arbeitnow, Jobicy, WeWorkRemotely)
- 1 freelance source (Freelancer.com only — Upwork RSS likely broken)
- 3 direct sources (Reddit r/forhire, HN Freelancer, GitHub Issues)
- Scoring: rule-based (keyword match × weights) — no semantic understanding
- LLM rerank: optional Claude Haiku — disabled (no API key set)
- Output: markdown digests in `jobhunter/reports/`
- Latest run (2026-04-30): 15 opportunities, top score 85/100 — tool works

## 4. Stated goal
> "Find me a job, freelance gig, or collaboration so I can earn money."

## 5. Implicit goals (extracted from PLAN.md, HANDOFF.md, profile docs)
- **Quality over quantity**: 15-20 high-fit opportunities daily, not 200 mediocre ones
- **Action-ready**: each lead should come with enough context to apply within 5 min
- **Pakistan-friendly filtering**: skip jobs that require US/EU work auth, on-site presence, daily standup in PST
- **Frontend-first scoring**: backend-heavy roles get penalized heavily
- **Cover-letter ready**: for top hits, draft a personalized pitch using portfolio links

## 6. Success metrics (proposed)
| Metric | Current | Target |
|---|---|---|
| Daily new opportunities surfaced | ~15 | 20–30 |
| Top-score precision (manual review) | unmeasured | ≥70% are "I'd actually apply" |
| Cover letter draft quality | n/a | Reusable with <2 min editing |
| False positives (rejected post-review) | ~40% (estimated) | <15% |
| Time from bot run → application sent | ~30 min | <10 min |

## 7. Known gaps (preliminary, before research)
1. **No LinkedIn coverage** — biggest job board for remote React roles
2. **No Wellfound (AngelList)** — startup-heavy, often Pakistan-friendly
3. **Upwork integration broken** — RSS feeds deprecated by Upwork in 2024
4. **Scoring is brittle** — keyword matching can't tell "React Native" from "React" or detect senior-level fit
5. **No CV-aware ranking** — bot doesn't read Tabish's actual experience to match
6. **No application tracking integration** — `tracker/applied.py` exists but isn't auto-populated
7. **No deduplication across sources** — same job posted on 3 boards = 3 entries
8. **Time-decay missing** — 60-day-old jobs score same as today's
9. **No portfolio-link injection** — cover letters don't reference deployed Netlify URLs
10. **No human feedback loop** — no way to tell bot "this match was great" / "this was wrong"

## 8. Out of scope (explicitly)
- Scraping LinkedIn (ToS-violating; will use signed-in RSS or Greenhouse/Lever ATS)
- Auto-applying to jobs (high risk; user must approve every application)
- Hosting bot on cloud (runs locally on user's Mac via launchd)
- Building a UI (CLI + markdown digests are sufficient)

## 9. Stakeholders
- **Primary user**: Tabish (single user, owns and tunes the bot)
- **Indirect beneficiaries**: Companies receiving high-quality applications

## 10. Next phase
→ **Market research**: which sources actually have remote React jobs that accept Pakistan-based applicants? What scoring approaches do similar tools use? See `02-market-research.md`.
