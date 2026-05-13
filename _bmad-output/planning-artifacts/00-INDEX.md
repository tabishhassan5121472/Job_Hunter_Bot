# BMAD Planning — JobHunter v2

| # | Phase | Doc | Status |
|---|---|---|---|
| 01 | Analyst | [Project Brief](01-project-brief.md) | ✅ Complete |
| 02 | Analyst | [Market Research](02-market-research.md) | ✅ Complete (live API probes) |
| 03 | PM | [PRD](03-prd.md) | ✅ Complete (5 epics, 22 stories) |
| 04 | Architect | [Architecture](04-architecture.md) | ✅ Complete |
| 05 | Scrum | [Sprint 1 Stories](05-sprint-1-stories.md) | ✅ Ready to implement |
| 06 | Dev | Implementation | ⏳ Next |

## Three biggest findings
1. **3 of 11 sources are broken** (Himalayas, RemoteOK API, Jobicy return zero usable React data)
2. **WeWorkRemotely Full-stack RSS + ATS direct (Vercel/Stripe/etc.) hold ~5× more React jobs** than the bot's current top sources
3. **Scoring is keyword-only** — a CV-aware embedding scorer would lift precision from ~30% to a target ≥70%

## Sprint 1 ready (one dev day, biggest win)
Drop 3 broken sources, add WW Full-stack feed + Greenhouse ATS for 15 remote-first companies, fix Reddit flair filter. Triples React-job volume immediately.

## Then Sprint 2-4
- Sprint 2 — Smart scoring (geo/tz/seniority/rate classifiers + embedding)
- Sprint 3 — Dedup + tracker + feedback loop
- Sprint 4 — Multi-agent reasoning (this is "Option B")
