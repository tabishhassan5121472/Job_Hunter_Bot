# Session Handoff — read this first in Cursor

**Date**: 2026-04-15
**Switching from**: Claude Code (Opus 4.6, quota almost out)
**Switching to**: Cursor with **Claude Sonnet 4.6** (recommended) or GPT-5-Codex as fallback

## Project goal
Build (1) a personal portfolio for **Tabish Hassan** (React/TS specialist, Rawalpindi, remote-seeking) and (2) a **JobHunter bot** that finds remote frontend jobs, freelance gigs, and direct clients. Portfolio ships first because the bot's cover letters link to it.

## Where the files live
- **Portfolio repo (existing)**: `/Users/Tabish/Documents/cursor-ai/My-Portfolio` — already cloned, `origin = github.com/tabishhassan5121472/My-Portfolio.git`, branch `main`
- **Plans + this handoff**: `/Users/Tabish/Documents/Personal Data/Make Something that will find a job for me, or collaboration team to work with them and earn money. /` (PLAN.md, PORTFOLIO_PLAN.md, HANDOFF.md)
- **CV**: `/Users/Tabish/Documents/Personal Data/BestCV-Tabish-Hassan.pdf`

## Decisions already made
- **Hosting**: Netlify free tier (Vercel blocked Pakistan phone verification). Account exists under team `ticketbazaar`, email `tabishhassan01998@gmail.com`. GitHub login authorized.
- **Domain**: none for now (free `.netlify.app` subdomain). Revisit later.
- **Stack**: Keep the existing **Vite + React + Tailwind + MUI + Framer Motion** in `My-Portfolio`. Do NOT migrate to Next.js — the Vite app already works.
- **Focus**: Frontend-first. Backend pitched only as "learning since Dec 2025" — never as expertise.
- **Jobhunter**: Python + SQLite + Claude API. Builds *after* portfolio is live. Channels: remote boards (Remotive, RemoteOK, Himalayas, WWR, HN hiring) + freelance (Upwork RSS, Freelancer, Contra) + **direct clients (Reddit r/forhire, IH, HN "Seeking freelancer", GitHub `help wanted`)** + OSS/volunteer.
- **Filters**: Frontend keywords weighted 40%, $2–$50/hr range, reject gambling/adult, both full-time + freelance.

## Critical state of the portfolio repo (DON'T just `git add .`!)

Current `git status` shows:
- **Deleted** (uncommitted, restorable): `DEPLOYMENT-FAILURES-ANALYSIS.md`, `DEPLOYMENT-SUMMARY.md`, `FIXES-APPLIED.md`, `deploy-projects.sh` — I restored these with `git restore`
- **Modified**: `src/components/ProjectCard.jsx`, `src/data/portfolioData.js`, `src/pages/About.jsx`, `src/pages/Home.jsx`
- **Untracked**: `vercel.json` + **25 sub-projects in `projects/`** totaling **8.5 GB**

**The 8.5 GB is 99% bloat**:
- 654 nested `node_modules` directories
- Build caches (`.next`, `.cache`, etc.)
- Only **4,212 actual source files** across all 25 projects
- All files >50 MB are inside `node_modules`/`.next/cache` — zero oversized source files
- Existing root `.gitignore` has `node_modules` and `dist` but the user has never staged the projects/ folder, so it's never been filtered

**Why prior Vercel deploys failed** (per `DEPLOYMENT-FAILURES-ANALYSIS.md`):
1. **DevCanvas** — TypeScript compile errors (`Cannot find module '../../../../lib/types'` should be `'../../lib/types'`) + unused-variable errors treated as fatal
2. **AffinityHub** — `linkedin-api-client@^1.0.1` doesn't exist in npm registry. Latest is `0.3.0`.
3. These were *individual project* deploys, **not the main portfolio site**. The portfolio Vite app itself is healthy.

## Recommended next steps (do these in Cursor)

### Phase 0 — repo cleanup (must do before any push)
1. **Decide what to do with `projects/` folder**. Two options:
   - **(A) Gitignore it entirely** — add `projects/` to root `.gitignore`. Cleanest. The folder stays on disk as backup but never enters the repo. The portfolio still references the projects via `src/data/portfolioData.js` with external links.
   - **(B) Move `projects/` out of the repo** — `mv projects ../My-Portfolio-projects-backup`. Equivalent but more explicit. Preferred if user wants to one-day make each project its own repo.
2. Confirm root `.gitignore` covers `node_modules`, `dist`, `build`, `.next`, `.vite`, `*.local`, `.DS_Store`, `.vercel`, `.netlify`, `coverage`. Current one is missing some of these.
3. Stage only the portfolio source: `git add src/ public/ index.html package.json package-lock.json vite.config.js tailwind.config.js postcss.config.js .gitignore netlify.toml README.md`
4. **Do NOT commit**: `vercel.json` (we're on Netlify now), the deleted `*-ANALYSIS.md` files (decide whether to keep them in repo or move to `docs/`).

### Phase 1 — Netlify deploy
1. Create `netlify.toml` at repo root:
   ```toml
   [build]
     command = "npm run build"
     publish = "dist"
   [build.environment]
     NODE_VERSION = "20"
   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200
   ```
2. Verify `npm run build` works locally (`cd /Users/Tabish/Documents/cursor-ai/My-Portfolio && npm install && npm run build`) — should produce `dist/`.
3. Commit + push to `origin/main`.
4. User clicks: Netlify → Add new project → Import from GitHub → My-Portfolio → Deploy. Auto-detects Vite. Should be live in ~90s.
5. Rename site to `tabish-portfolio.netlify.app` (or similar) in Site settings.

### Phase 2 — portfolio content polish
1. Read `src/data/portfolioData.js` and audit: which projects are real, which are placeholders. Update with real screenshots, descriptions, links.
2. Read `src/pages/Home.jsx`, `About.jsx` — make sure pitch matches the CV (React 4y, accessibility, perf optimization).
3. Add CV PDF download link.
4. Add proper `<title>` and meta tags (SEO).
5. Hook up contact form to Formspree or Resend (free).

### Phase 3 — pick top 4-6 projects to feature
From the 25 in `projects/`, pick the strongest. Candidates worth checking:
- Crypto-Dashboard / Crypto-Dashboard-Live-Updates
- Ai-Interview-Taker
- DevCanvas (after fixing TS errors)
- restaurant-pos-system
- analytics-dashboard / sales-forecast-dashboard
- Pinterest-Affliate-Marketing-Dashboard

Each featured project later gets its own GitHub repo + own Netlify site + linked from the portfolio.

### Phase 4 — start jobhunter bot
See `PLAN.md` in this directory for the full bot spec. Build phases 1-7. Python, SQLite, Claude API. Begin only after portfolio is live.

## Open tasks (Claude Code task list at handoff time)
1. ✅ Diagnose prior Vercel deploy failures
2. 🔄 Audit projects/ folder bloat (in progress)
3. ⬜ Fix .gitignore to exclude bloat
4. ⬜ Curate top 4-6 projects for portfolio
5. ⬜ Add netlify.toml + Vite build config
6. ⬜ Push cleaned portfolio to GitHub
7. ⬜ Connect Netlify to GitHub repo

## What to ask Tabish first thing in Cursor
1. "Have you decided whether to **gitignore** or **move out** the `projects/` folder?" (Phase 0 step 1)
2. "Did the Netlify GitHub authorization complete? (You should see your repo list when clicking Add new project → Import.)"
3. "OK to delete the `vercel.json` file? We're on Netlify now."

## Important constraints (from user's CLAUDE.md and memory)
- User is in Pakistan, Rawalpindi. Remote-seeking. Pakistan phone numbers fail Vercel verification.
- Job-hunt scope: $2–$50/hr freelance, both full-time + contract, reject gambling/adult.
- Backend skills minimal (started Dec 2025 = ~4 months). Pitch only as "learning full-stack".
- Budget-conscious — no paid services unless essential.
