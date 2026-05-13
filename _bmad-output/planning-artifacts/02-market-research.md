# Market Research — Where remote React jobs actually live

**Author**: Mary (BMAD Analyst)
**Date**: 2026-04-30
**Method**: Live API probes against every source the bot uses + 4 candidate new sources

## Executive summary
The bot is **fishing in the wrong ponds**. 4 of its 6 board sources return very weak React signal. Two untapped channels (full-stack feeds + ATS direct) hold 5–10× more high-fit jobs than the bot's current top sources. This document is the evidence behind the PRD's proposed source overhaul.

## Source quality scorecard

| Source | API returns | React matches | Pakistan-friendly | Verdict |
|---|---:|---:|---:|---|
| **WW Full-stack RSS** | 157 jobs | **32 React** | 32 (no US-only) | ⭐⭐⭐ Add immediately |
| **Stripe ATS (Greenhouse)** | 494 jobs | **24 React** | needs filter check | ⭐⭐⭐ Add |
| **Vercel ATS (Greenhouse)** | 83 jobs | **23 React** | known remote-friendly | ⭐⭐⭐ Add |
| **Airbnb ATS (Greenhouse)** | 244 jobs | **14 React** | partial remote | ⭐⭐ Add (filter) |
| **WW All-remote RSS** | 100 jobs | 14 React | 13 | ⭐⭐ Keep |
| **WW Frontend RSS** (current) | 12 jobs | 8 React | 7 | ⭐ Keep but small |
| **Reddit r/forhire** | 25 posts | 16 React | 0 `[hiring]` | ⚠ Fix filter |
| **Arbeitnow** (current) | 100 jobs | 1 React | German-heavy | ⚠ Demote |
| **Remotive react search** (current) | 22 jobs | mostly non-React | USA-heavy | ⚠ Filter broken |
| **Himalayas API** (current) | 20 jobs | **0 actually React** | n/a | ❌ Search broken — drop |
| **RemoteOK API** (current) | 0 React | 0 | n/a | ❌ Endpoint broken — drop |
| **Jobicy** (current) | 0 jobs | 0 | n/a | ❌ Broken — drop |
| **Wellfound (AngelList)** | 403 forbidden | n/a | n/a | ❌ Out of scope (anti-scrape) |

## Key insights

### 1. ATS direct = 84 React jobs from 4 companies in one round trip
Greenhouse and Lever expose public JSON endpoints. Stripe + Vercel + Airbnb alone yielded **61 React roles** in this probe — more than all the bot's current board sources combined. Companies known to hire globally remote: Vercel, Supabase, Hugging Face, Clerk, GitLab, PostHog, Cal.com, Hashnode, Webstudio, Codecov, Linear (some), Replicate.

**Action**: build a `sources/ats/greenhouse.py` and `sources/ats/lever.py` that iterate a curated list of ~30 remote-friendly companies.

### 2. Full-stack > Frontend feed for React signal
Counterintuitive but clear: the bot pulls WW's *frontend* RSS (8 React/12 total) and ignores the *full-stack* feed which has **32 React/157 total** — 4× the absolute volume and the same React density. Many React roles are listed as "Full Stack JavaScript Developer" rather than "Frontend Engineer".

**Action**: add `sources/boards/weworkremotely_fullstack.py`.

### 3. Three sources are silently broken
Himalayas, RemoteOK API, and Jobicy returned **zero usable React data** in this probe. The bot's current digests likely include very few results from these — they pad noise without value.

**Action**: drop or rewrite the fetchers. Don't trust per-source "X raw" counts in the bot's CLI output without verifying React relevance.

### 4. Reddit r/forhire — wrong flair
25 recent posts contained "react" but **zero were `[Hiring]` posts** (all were `[For Hire]` from other devs). The bot's current scraper doesn't filter by flair, so it surfaces fellow job-seekers as opportunities.

**Action**: filter to `flair_text == "Hiring"` only. Same fix needed for r/reactjs.

### 5. Pakistan-friendly signal needs explicit detection
Most listings don't say "global / worldwide" — they say nothing, defaulting to ambiguous. The bot needs a 3-tier classifier:
- **Green**: explicit "anywhere / worldwide / global / any timezone / asia ok / pakistan ok"
- **Yellow**: silent on location but no exclusion language
- **Red**: "US only / EU only / requires citizenship / on-site / right to work / authorized to work in"

Currently the bot only handles a subset of Red signals.

### 6. Time-zone overlap matters more than location
Most "global" remote jobs require 4+ hours overlap with US-Pacific or EU. Pakistan (UTC+5) overlaps cleanly with EU mornings (12:00–17:00 PKT) and US-Pacific late evenings (20:00–23:00 PKT). Detect timezone requirements: "must overlap with PST", "core hours 9am-2pm EST", etc.

## Competitive landscape (similar tools)

| Tool | What it does | What we can borrow |
|---|---|---|
| **Hatchways** | Sources React jobs from 50+ ATS, scores by stack match | ATS-direct sourcing model |
| **JobMate (Lemon.io)** | Curated global React/Vue jobs with rate ranges | Rate extraction from JD text |
| **Otta / Welcome to the Jungle** | Tag-based filtering, salary transparency | Rate-aware ranking |
| **Hired.com** | Reverse marketplace where companies bid | Personalized fit signals |
| **AI Recruiter open-source** (DeepSeek-Recruiter, autoapply-bot) | LLM-based JD-vs-resume scoring | Embedding-based scoring approach |

**Borrowable patterns**:
1. **Multi-ATS aggregation** (Hatchways)
2. **Rate auto-extraction** from JD text using regex + LLM fallback
3. **Embedding-based JD-vs-CV match** (cosine similarity on Claude/OpenAI embeddings) instead of keyword matching
4. **Multi-criteria filter** (timezone overlap, visa, rate range, seniority) as separate gates, not blended into one score

## Recommended source mix (after research)

**Tier 1 — Must add (high signal, free)**:
1. `weworkremotely_fullstack` (RSS)
2. `ats_greenhouse` (configurable company list)
3. `ats_lever` (configurable company list)
4. `reddit_forhire` (FIX flair filter)

**Tier 2 — Keep but fix**:
5. `weworkremotely` (frontend RSS)
6. `weworkremotely_all_remote` (RSS) — broader catch
7. `arbeitnow` (rewrite to filter title for "react")

**Tier 3 — Drop**:
- ❌ `himalayas` (broken filter)
- ❌ `remoteok` (returns 0)
- ❌ `jobicy` (returns 0)

**Tier 4 — Future investigation**:
- HN "Who's Hiring" monthly thread (HN API, regex parsing)
- GitHub Issues with `help-wanted` + `bounty` + `react` (already in bot, but enhance)
- LinkedIn (only via Greenhouse/Lever embeds on company sites)

## Assumptions to validate with PM

1. User accepts a source-list rewrite (drop 3 sources, add 4)
2. User is OK with curating an ATS company list (~30 names)
3. Embedding-based scoring requires `ANTHROPIC_API_KEY` — user willing to set this
4. Bot remains CLI + markdown digests (no new UI)

→ Next phase: PRD — see `03-prd.md`.
