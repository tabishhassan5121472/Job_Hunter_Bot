# Tabish Hassan — Full-stack + AI Application Engineer CV (prompt-cached for LLM)

> Use this variant for **AI Engineer / LLM Application / ML Platform / Agentic
> Software / AI-Frontend** roles. Lead with shipped AI projects (real systems,
> not "I used ChatGPT") and pair them with the React + NestJS + iOS shipping
> base so it doesn't read as "AI tourist".

## Identity
- **Name**: Tabish Hassan
- **Role**: Full-stack + AI Application Engineer · Built and operate JobHunter (LLM-reranked job pipeline)
- **Location**: Rawalpindi, Pakistan · UTC+5 · Remote-only · worldwide
- **Portfolio**: https://tabishhassan5121472.github.io/My-Portfolio
- **GitHub**: https://github.com/tabishhassan5121472
- **Availability**: Immediate · Full-time, contract, or freelance

## Core Stack

**AI / LLM application**: Anthropic Claude SDK (Sonnet / Haiku) · Cerebras Cloud (Qwen 3 235B, gpt-oss, Llama 3.x) · OpenAI-compatible APIs · prompt design + prompt caching · structured-output (JSON) extraction · multi-source data pipelines · vector-less retrieval where appropriate · cost-aware model routing

**Frontend (4+ years)**: React.js · TypeScript · Tailwind CSS · Material UI · Redux Toolkit · Next.js · Vite · React Query · Storybook

**Backend (Dec 2025 → present)**: NestJS · Node.js · Python · REST APIs · JWT auth · MongoDB · PostgreSQL · Socket.IO · microservice architecture

**Mobile (iOS)**: Swift · SwiftUI · UIKit · fastlane · AdMob · StoreKit subscriptions

**Infra / DevOps**: GitHub Actions cron pipelines · GitHub Pages · Netlify · Azure App Service · scheduled deploy + commit-back workflows

## Featured AI / Automation Projects

### JobHunter — autonomous job-search pipeline
*github.com/tabishhassan5121472/Job_Hunter_Bot · operates 24/7*
- 8 source scrapers (Remotive, ArbeitNow, WeWorkRemotely×2, RemoteOK, Greenhouse + Ashby + Lever + Workable ATS, Reddit RSS, HN "Who is Hiring" thread) merge into one normalised `Opportunity` schema (Pydantic)
- Heuristic scorer + **LLM rerank via Cerebras Qwen 3 235B** scores each top job against my CV/preferences/wins bank, returns `STRONG/OK/WEAK/REJECT` verdict + matching wins
- Per-channel CV variant selection drives Claude/Qwen-generated cover-letter drafts
- Language filter (`langdetect`) drops non-English postings; freshness filter (3 days); bot-noise filter; per-repo cap to kill spam patterns
- Runs every 5h on GitHub Actions cron → commits `jobs.db` + reports back → builds static Preact site → auto-deploys to GitHub Pages
- Cost-controlled: prefers free Cerebras tier (1M tokens/day) over paid Anthropic; falls back gracefully when no key configured

### BMAD-style agent workflows (Blogging / Suggest engines)
- Autonomous content-generation pipelines using BMAD method (Brief / Map / Act / Decide loops with LLM-as-orchestrator)
- Used for personal blogging automation and a suggestion engine for content discovery

### AI Content Dashboard (in My-Portfolio)
- React frontend with multi-format AI content generation, quality analytics, and localStorage persistence
- Live at https://tabish-ai-content-dashboard.netlify.app

### Twitter / News automation
- Integrated Twitter API v2 + OpenAI API in a news automation platform with viral-prediction scoring

## Experience

### Software Engineer (Frontend → Full-stack) — Citrusbits / RadiusXR (Jul 2022 – Present)
- Built three React-based RadiusXR portals (Practice, SuperAdmin, Eyevia) with TypeScript + Material UI / Tailwind
- Delivered `order.rubios.com` (high-traffic ordering) — improved performance 40% via React optimisations
- Built `soul-link.org` from scratch — ADA/WCAG 2.1 AA compliant
- **Dec 2025 → present**: expanded into backend, owning NestJS microservices powering 5 RadiusXR portals

## Independent Shipping
- **20+ iOS apps** published to the App Store (featured: StoryBoard · QuoteVault · Spell Bee · Habit Grid) — Swift / SwiftUI, AdMob, StoreKit subscriptions, fastlane CI/CD
- **14+ deployed React apps** at https://tabishhassan5121472.github.io/My-Portfolio

## Education
BS Software Engineering · The University of Lahore (Jan 2017 – Jan 2021)

## Languages
English (Fluent) · Urdu (Native) · Punjabi (Native)
