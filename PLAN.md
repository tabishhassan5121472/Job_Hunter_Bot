# JobHunter Bot — Plan (v2, Frontend-First)

Personalized opportunity-finder for **Tabish Hassan** — React.js specialist, remote-seeking, Rawalpindi.

> **v2 changes**: Focus shifted to **frontend/React** as primary. Backend treated as "learning, not selling" (started Dec 2025). Added **direct client discovery** channels beyond job boards.

## 1. Profile (locked)

- **Sell**: React.js, TypeScript, Tailwind, Material UI, Redux Toolkit/Saga, perf optimization, accessibility (ADA/ARIA), responsive/mobile-first, REST integration — **4 years** at Citrusbits + RadiusXR
- **Don't sell**: Backend. Started Dec 2025 (~4 months). Mention only as "growing into full-stack".
- **Search for**:
  1. Remote **React / Frontend** jobs (primary)
  2. **Freelance React gigs** & direct clients
  3. **Collaborations** / co-founder / indie projects needing a frontend dev
  4. Junior full-stack **only if frontend-heavy**
  5. Volunteer / OSS React contributions (portfolio + network)
- **Reject**: Senior backend, pure-Node/NestJS roles, "5+ yrs Node", on-site, US-citizens-only

## 2. Scoring — frontend-weighted

```
score = 0.40 * react_stack_match       # react, reactjs, typescript, tailwind, mui, redux, next.js
      + 0.15 * frontend_signal         # frontend, ui, ux, web developer, css
      + 0.15 * remote_friendly         # remote, worldwide, anywhere
      + 0.10 * seniority_fit           # mid/3-5y good; senior ok; lead/principal penalized
      + 0.10 * recency                 # posted < 7 days
      + 0.05 * pay_signal              # salary/budget present
      + 0.05 * accessibility_bonus     # a11y, ADA, WCAG — Tabish's edge
- PENALTIES:
      - 30 if "backend-only" / "senior node" / "nestjs lead"
      - 20 if "on-site" / "must be in [city]"
      - 15 if US/EU citizenship required
      - full reject if role == "backend engineer" senior+
```

Top-20 re-ranked by Claude Haiku with a "fit or not?" prompt, CV cached.

## 3. Where to look — 4 channels

### Channel A — Remote job boards (structured)
| Source | Why | Access |
|---|---|---|
| **Remotive** | Strong frontend category | JSON API |
| **RemoteOK** | High React volume | JSON API |
| **WeWorkRemotely** | Senior-leaning, remote-only | RSS |
| **Arbeitnow** | EU remote, friendly to Pakistan | JSON API |
| **Himalayas.app** | Remote-first, filterable | JSON/RSS |
| **Jobicy** | Remote, has frontend filter | RSS |
| **Working Nomads** | Aggregator, remote only | RSS |
| **Hacker News "Who is hiring"** | Monthly thread, startups | HN Algolia API (`REMOTE` + `react`) |
| **LinkedIn Jobs** | Via user-saved RSS search URL | RSS |

### Channel B — Freelance / gig platforms (client-facing)
| Source | Why | Access |
|---|---|---|
| **Upwork RSS** | Public job search RSS (`?q=react&t=0`) | RSS feed |
| **Freelancer.com** | Public feed for React projects | RSS |
| **PeoplePerHour** | Short gigs | RSS |
| **Contra** | Curated freelance, no platform fees | RSS / public listings |
| **Codeable** (if accepted) | Premium WP+React | manual |
| **Toptal** (aspirational) | Track as stretch goal | manual |

### Channel C — Direct client discovery (people asking for devs)
These are *where actual clients post in plain language*, not curated boards.

| Source | What we fetch |
|---|---|
| **Reddit r/forhire, r/slavelabour, r/remotejs, r/reactjs** | Posts tagged `[Hiring]` — Reddit JSON API |
| **Indie Hackers** — "looking for cofounder/dev" | Public listings + RSS |
| **Hacker News "Freelancer? Seeking freelancer?"** | Monthly thread, HN API |
| **Twitter/X search** | `"looking for" "react developer"` recent posts (via Nitter RSS or X API if keys provided) |
| **Dev.to tagged #forhire / #hiring** | Public RSS by tag |
| **LinkedIn post search** (manual seed URLs) | "#hiring react remote" — fetchable RSS |
| **Discord/Slack communities** | Out of scope automated; bot surfaces a weekly reminder list to check manually |
| **Product Hunt Makers** — solo founders who just launched without a frontend | PH API → filter by product + check if they have web presence gaps |
| **GitHub** — repos with `help wanted` + `good first issue` in React/TS | GitHub Search API |
| **Y Combinator Work at a Startup** | Public company list, manual seeding |

### Channel D — Collaboration / volunteer / OSS
| Source | Purpose |
|---|---|
| **GitHub trending** (language: TypeScript/JavaScript) | Find React projects that need contributors |
| **First Timers Only / Up For Grabs** | Curated OSS entry points |
| **CodeTriage** | Weekly OSS issue recommendations |
| **Catchafire / VolunteerMatch** | Nonprofit web projects needing a frontend dev — resume + network |
| **Indie Hackers "looking for cofounder"** | Equity / revenue-share collabs |

## 4. Client-matching — *the bot pitches you*

For every **Channel B/C hit**, the bot does extra work beyond scoring:

1. **Parse the ask** — extract: stack, deadline, budget, timezone, contact method
2. **Match to your wins** — pick 2–3 bullets from your CV that map (e.g., "Rubios ordering site" for an e-commerce gig, "accessibility work" for a gov/nonprofit gig)
3. **Draft a personalized first message** — ≤120 words, no template smell, with a specific reference to *their* project
4. **Attach the tailored CV variant** (frontend-only, backend section hidden or reduced)
5. **Flag urgency** — "posted 2h ago, reply fast"

You get: a one-line pitch + the drafted message + the contact link. You approve + send.

## 5. Tech stack

- **Language**: Python 3.11 (feedparser, httpx, pydantic)
- **Storage**: SQLite (`jobs.db`) — jobs, clients, seen-URLs, application tracker
- **Scheduler**: `launchd` plist on macOS — runs 09:00 and 18:00 PKT
- **LLM**: Claude API — Haiku for re-rank & parse, Sonnet for cover letters. **Prompt cache** the CV + preferences (huge token savings)
- **Delivery**:
  - Daily Markdown digest in `reports/`
  - Gmail API email (top 10)
  - Optional Telegram bot for real-time Channel-C hits (high-value freelance posts)
- **Config**: `config.yaml` (keywords, blacklist, thresholds, source toggles)

## 6. Project structure

```
jobhunter/
├── config.yaml
├── profile/
│   ├── cv_frontend.md          # frontend-focused CV (generated)
│   ├── cv_fullstack_junior.md  # alt variant when "junior full-stack" role
│   ├── preferences.md          # must/nice/reject rules
│   └── wins.md                 # reusable achievement bullets w/ metrics
├── sources/
│   ├── boards/                 # remotive, remoteok, wwr, arbeitnow, himalayas, jobicy, wn, hn_hiring
│   ├── freelance/              # upwork_rss, freelancer, peopleperhour, contra
│   ├── direct/                 # reddit_forhire, ih, hn_freelance, devto, github_issues, twitter
│   └── oss/                    # github_trending, up_for_grabs, codetriage
├── core/
│   ├── fetcher.py              # HTTP + retry + ETag cache
│   ├── normalizer.py           # -> unified Opportunity schema
│   ├── scorer.py               # frontend-weighted rules
│   ├── llm_rerank.py           # Claude Haiku, prompt-cached CV
│   ├── dedup.py
│   └── storage.py
├── pitch/
│   ├── cover_letter.py         # Claude Sonnet, per-job tailored
│   ├── client_message.py       # short DM-style for Channel C
│   └── cv_tailor.py            # swaps bullets based on JD keywords
├── delivery/
│   ├── digest_md.py
│   ├── email_gmail.py
│   └── telegram_bot.py
├── tracker/
│   └── applied.py              # SQLite: status, replied, interview, offer
├── reports/                    # YYYY-MM-DD.md
├── jobs.db
├── main.py
└── requirements.txt
```

## 7. Unified `Opportunity` schema

```python
Opportunity {
  id, url, source, channel,           # A/B/C/D
  title, company_or_client,
  description, stack[],
  is_remote, timezone, location_restriction,
  seniority, budget, currency, posted_at,
  contact_method,                      # email, DM, form, apply link
  score, score_breakdown, llm_fit_note,
  pitch_draft, cv_variant,
  status                               # new, drafted, sent, replied, rejected, interview, offer
}
```

## 8. Build phases

- **Phase 1 — MVP (1 day)** · Channel A only: Remotive + RemoteOK + Himalayas. Frontend-weighted scorer. Markdown digest. Prove the loop.
- **Phase 2 — Channel B freelance (1 day)** · Upwork RSS + Freelancer + Contra. Dedup in SQLite.
- **Phase 3 — Channel C direct clients (1 day)** · Reddit r/forhire + IH + HN "Seeking freelancer" + GitHub issues. **This is where the highest-leverage leads are.**
- **Phase 4 — LLM rerank + pitch drafts (1 day)** · Claude Haiku re-rank; Sonnet-generated personalized messages with prompt-cached CV. Tailored CV variant.
- **Phase 5 — Delivery (0.5 day)** · Gmail digest + Telegram for real-time Channel-C hits. launchd schedule.
- **Phase 6 — Channel D + tracker (0.5 day)** · OSS/volunteer feed + application tracker.
- **Phase 7 — Polish** · Simple local web dashboard (React, obviously — portfolio piece).

## 9. Parallel wins (bot amplifies these — don't skip)

1. **Portfolio polish** — current Vercel URL is a preview slug. Custom domain, 3–4 case studies with live demos + code + metrics ("reduced load time 40%"). **The bot will link employers here; make it count.**
2. **GitHub** — pin 4–6 repos, real READMEs with screenshots + live links. Clean contribution graph by doing the OSS work the bot surfaces.
3. **LinkedIn** — headline: "React.js Developer | TypeScript, Tailwind, Redux | Remote | 4y experience". Open-to-work: Remote. Add 2–3 "I built X" posts with screenshots.
4. **Two CV variants**:
   - `cv_frontend.md` — what you sell (no backend section)
   - `cv_fullstack_junior.md` — frontend + small "learning backend since Dec 2025" line for junior full-stack roles
5. **Rates** — decide now: hourly for Upwork ($X), project minimum, monthly retainer. Bot filters by these.

## 10. What I need from you to start Phase 1

1. **Confirm keywords** I should match on (default list below — add/remove):
   `react, reactjs, typescript, tailwind, next.js, redux, material-ui, mui, frontend, front-end, web developer, javascript, accessibility`
2. **Hard rejects** — any companies, industries, or keywords to always skip? (e.g., crypto, gambling, adult)
3. **Minimum rate** for freelance filtering (USD/hr)
4. **Time commitment** — are you looking for full-time, contract, or both?
5. **Portfolio URL** you want the bot to send to employers (the Vercel preview URL, or will you set up a custom domain first?)
6. **Should I fetch your actual portfolio** now (give me the URL) so I can reference real projects in cover letters?

---

**Proposed next step**: Answer the 6 questions above → I scaffold `jobhunter/`, ship Phase 1 against Remotive + RemoteOK + Himalayas, and we see *today's* ranked frontend-only digest within a single session.
