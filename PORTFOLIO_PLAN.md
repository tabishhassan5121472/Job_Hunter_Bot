# Portfolio Plan — ships *before* jobhunter

**Why this comes first**: Jobhunter bot drafts cover letters that link to your portfolio. If the link is dead or weak, the bot wastes its best leads. So we invest 2–3 days in a real portfolio, then the bot amplifies it.

---

## 1. Deployment — Vercel (decided)

**Host**: Vercel free tier. User is creating a new Vercel account to replace the deactivated one.

**URL**: Free `.vercel.app` subdomain for now (e.g. `tabish-portfolio.vercel.app`). Custom domain can be added later for ~$10/yr if/when needed — not a blocker.

**Why Vercel is fine**:
- Free tier is generous for personal portfolio traffic
- Native Next.js support (same company makes both)
- Zero-config deploys from GitHub
- Fast global CDN, free SSL
- Preview deployments on every PR

**One risk to avoid**: the previous account deactivation. To reduce re-occurrence, stay within free-tier limits, don't run scrapers/proxies on it, and keep the account tied to a real email you check.

## 2. Domain — skip for now

User decision: no custom domain yet. Free `.vercel.app` subdomain is fine. Revisit later once the portfolio is landing leads and a pro URL becomes worth $10/yr.

## 3. Portfolio stack

- **Framework**: **Next.js 14** (App Router) — SSR, fast, SEO-friendly, recruiters' crawlers see real content. Bonus: Next.js is a hot keyword in React job ads, using it *is* a portfolio piece.
- **Styling**: Tailwind CSS + Framer Motion (tasteful animations)
- **Content**: MDX for project case studies (write once, renders beautifully)
- **Forms**: Formspree or Resend free tier for the contact form
- **Analytics**: Cloudflare Web Analytics (free, privacy-friendly, no cookies)
- **SEO**: `next-seo`, proper Open Graph images (recruiters share links)

## 4. Content — what goes on it

A portfolio is not a decoration. It's a sales page. Structure:

### Home (one screen, above-the-fold)
- Name + one-line pitch: *"React.js Developer — 4 years building fast, accessible web apps"*
- CTA: "View Projects" + "Hire me" (email / LinkedIn)
- Subtle animation, no slow hero video

### Projects — **3 to 4 case studies** (the heart of the site)
Each case study = its own page with:
- Hero screenshot (real, not Figma mockup)
- Problem / Your role / Stack / Outcome with numbers
- 2–3 architecture or UI detail shots
- Live demo + code links

**Candidate projects** (pick 3–4):

1. **Rubios Ordering Site** (from your CV)
   - Talk about ADA compliance + keyboard nav + perf wins
   - If the real site is under NDA, redraw the flow with mock data

2. **Soul Link Meditation** (from your CV)
   - MUI component library, responsive design

3. **RadiusXR portals** (NDA-safe version)
   - "Spearheaded frontend across 3 portals" — show architecture diagram + component library screenshots, no real data

4. **New built-for-portfolio project** — this is the differentiator. Pick ONE:
   - **Pokedex Pro** — React + TS + TanStack Query, filters, offline PWA
   - **Kanban board** — drag-drop with `dnd-kit`, Zustand state, local persistence
   - **Markdown blog engine** — MDX, syntax highlighting, tag pages (meta: your blog uses it)
   - **Accessibility audit tool** — paste URL → run axe-core → show report (plays to your a11y strength, genuinely useful)

   **My pick: the accessibility audit tool.** It's useful, unusual, and showcases your #1 differentiator (accessibility work). Recruiters will remember it.

### About
- Short bio. Where you are, what you care about, what you're learning (mention backend *as a learning journey*, not expertise).
- Timeline: Citrusbits → RadiusXR → learning full-stack
- Languages spoken, timezone, remote-ready

### Contact
- Email (not an image — a real mailto)
- LinkedIn, GitHub, optionally Twitter/X
- Simple form (Formspree/Resend)
- **Downloadable CV as PDF** (the frontend-focused variant)

## 5. GitHub — the silent half of the portfolio

Recruiters click your GitHub as often as your portfolio. Clean it:

1. **Pin 6 repos** — portfolio, accessibility tool, 3 case-study repos, 1 OSS contribution
2. **Every pinned repo needs**:
   - `README.md` with: what/why, screenshot, live link, stack, run instructions
   - Clean commit history (squash messy branches)
   - MIT license
3. **Profile README** (`github.com/<you>/<you>`) — short bio + current focus + contact. Takes 20 min, looks pro.
4. **Contribution graph** — stop worrying about it, just commit while building the portfolio + jobhunter. Naturally fills in.

## 6. Two CV variants (to be stored in `profile/`)

- **`cv_frontend.pdf`** — what you sell. Citrusbits + RadiusXR bullets, React/TS/Tailwind, accessibility wins. **No backend section.**
- **`cv_fullstack_junior.pdf`** — frontend content + small "Learning Node/NestJS since December 2025" line at the bottom. For "junior full-stack" roles only.

The jobhunter bot will pick which one to attach per opportunity.

## 7. Build phases (portfolio)

- **Phase P1 (Day 1)** — Scaffold Next.js + Tailwind, deploy placeholder to Cloudflare Pages, wire custom domain. Home page + About. Ship something live by end of day.
- **Phase P2 (Day 2)** — Build the accessibility audit tool project + write its case study. Write Rubios + Soul Link case studies (from CV memory).
- **Phase P3 (Day 3)** — Contact form, SEO, OG images, CV PDF downloads. Polish animations. GitHub pin + READMEs.
- **Phase P4 (ongoing)** — Add one case study per real project you finish.

**Total active time**: ~3 days of focused work. Can stretch over a week around your day job.

## 8. Parallel track — jobhunter scaffolding

While the portfolio is being built, I can scaffold the `jobhunter/` directory structure, write the config, and build Channel A (Remotive + RemoteOK + Himalayas) in parallel. It won't *send* cover letters until the portfolio is live, but the data pipeline runs immediately so we see what the market looks like.

## 9. Proposed order of work

**Week 1** (portfolio sprint, jobhunter scaffolding in background)
- Day 1 — Next.js + Cloudflare Pages deploy + domain purchase
- Day 2 — Accessibility audit tool project + 2 case studies
- Day 3 — Case studies + polish + GitHub cleanup
- (background) — jobhunter skeleton + Channel A fetchers (read-only mode)

**Week 2** (jobhunter comes online)
- Day 4 — Scoring + dedup + SQLite + markdown digest
- Day 5 — Channel B (Upwork/Freelancer/Contra RSS)
- Day 6 — Channel C (Reddit, IH, HN, GitHub issues) — the gold mine
- Day 7 — Claude API pitch drafts + Gmail delivery + launchd cron

**Week 3** — iterate based on what actually lands in your inbox

## 10. What I need from you to start Day 1

1. **Pick a domain name** — `tabishhassan.dev`, `tabishhassan.com`, or another. (I'll check availability.)
2. **Confirm Cloudflare Pages** as host — or pick a different one from the table.
3. **Confirm the accessibility audit tool** as the new portfolio project — or pick a different one.
4. **GitHub username** you want me to reference.
5. **Are you OK spending ~$10–15/year on a domain?** Everything else is free.

Say "go" with answers and I'll start building Day 1 immediately — Next.js scaffold, Tailwind, first deploy to Cloudflare Pages (if you set up the account), and a working home page. Or if you'd rather defer the deploy and just get the code running locally first, say so.
