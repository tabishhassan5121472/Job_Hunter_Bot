# Sprint 1 — Source Quality Overhaul (ready-to-implement stories)

**Sprint goal**: Replace 3 broken sources with 4 high-signal ones. Triple the daily React-job count.
**Estimated effort**: 1 dev day
**Owner**: Dev agent (next BMAD phase)

## Story E1.S1 — Drop broken sources
**Files**:
- `jobhunter/main.py` — remove `himalayas`, `remoteok`, `jobicy` from `BOARD_SOURCES`
- `jobhunter/sources/boards/_deprecated/` — move the 3 fetcher files here
- `jobhunter/config.yaml` — set `sources.boards.{himalayas, remoteok, jobicy}: false`

**Acceptance**: Bot still runs, no import errors, log line shows fewer sources. Total raw count drops 0–10% (those sources contributed almost nothing).

**Test**: `python main.py --top 5 --no-llm` succeeds without those 3 sources.

---

## Story E1.S2 — Add WW Full-stack RSS source
**File**: `jobhunter/sources/boards/weworkremotely_fullstack.py`

```python
"""WeWorkRemotely — Full-stack RSS feed (Channel A)."""
from __future__ import annotations
import hashlib
import re
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
from core.fetcher import fetch_text
from core.models import Opportunity

FEED_URL = "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss"

def _to_opportunity(entry) -> Opportunity:
    title = entry.get("title", "")
    summary = re.sub(r"<[^>]+>", " ", entry.get("summary", ""))[:1500]
    company = title.split(":")[0].strip() if ":" in title else "Unknown"
    clean_title = title.split(":", 1)[1].strip() if ":" in title else title
    posted = parsedate_to_datetime(entry.get("published", "")) if entry.get("published") else datetime.now()
    uid = hashlib.md5(entry.get("link", title).encode()).hexdigest()
    return Opportunity(
        id=uid, channel="A", source="weworkremotely_fullstack",
        title=clean_title, company_or_client=company, location="Remote",
        url=entry.get("link", ""), description=summary,
        posted_at=posted.isoformat(), is_remote=True,
    )

def fetch() -> list[Opportunity]:
    text = fetch_text(FEED_URL)
    feed = feedparser.parse(text)
    return [_to_opportunity(e) for e in feed.entries]
```

**Register in `main.py`**:
```python
BOARD_SOURCES = [
    ("remotive",                "sources.boards.remotive"),
    ("arbeitnow",               "sources.boards.arbeitnow"),
    ("weworkremotely",          "sources.boards.weworkremotely"),
    ("weworkremotely_fullstack","sources.boards.weworkremotely_fullstack"),  # NEW
]
```

**Acceptance**: Bot run shows `weworkremotely_fullstack: 25-50 raw` and at least 5 score ≥70.

---

## Story E1.S3 — Greenhouse ATS multi-company source
**Files**:
- `jobhunter/sources/ats/__init__.py`
- `jobhunter/sources/ats/greenhouse.py`
- `jobhunter/config/ats_companies.yaml`

```python
# greenhouse.py
import time, hashlib, re, yaml
from pathlib import Path
from datetime import datetime
import httpx
from core.models import Opportunity

CONFIG = yaml.safe_load(Path(__file__).parent.parent.parent.joinpath("config/ats_companies.yaml").read_text())

def _to_opp(j, company_cfg) -> Opportunity:
    content = re.sub(r"<[^>]+>", " ", j.get("content", ""))[:1500]
    uid = hashlib.md5(f"gh-{company_cfg['name']}-{j['id']}".encode()).hexdigest()
    return Opportunity(
        id=uid, channel="A", source=f"ats_greenhouse_{company_cfg['name']}",
        title=j.get("title","")[:120],
        company_or_client=company_cfg["name"].title(),
        location=j.get("location",{}).get("name","Remote"),
        url=j.get("absolute_url",""), description=content,
        posted_at=j.get("updated_at", datetime.now().isoformat()),
        is_remote="remote" in (j.get("location",{}).get("name","").lower()),
    )

def fetch() -> list[Opportunity]:
    out = []
    for c in CONFIG["companies"]:
        if c.get("ats") != "greenhouse":
            continue
        try:
            r = httpx.get(f"https://boards-api.greenhouse.io/v1/boards/{c['board_id']}/jobs?content=true", timeout=10)
            r.raise_for_status()
            for j in r.json().get("jobs", []):
                blob = (j.get("title","") + j.get("content","")).lower()
                if any(kw in blob for kw in c.get("keywords_must_match", ["react"])):
                    out.append(_to_opp(j, c))
            time.sleep(0.4)  # rate limit politeness
        except Exception:
            continue
    return out
```

**Initial company list** (`config/ats_companies.yaml`) — 15 to start, expand later:
```yaml
companies:
  - {name: vercel,      ats: greenhouse, board_id: vercel,      keywords_must_match: [react, next, frontend]}
  - {name: stripe,      ats: greenhouse, board_id: stripe,      keywords_must_match: [react, frontend]}
  - {name: airbnb,      ats: greenhouse, board_id: airbnb,      keywords_must_match: [react, frontend]}
  - {name: gitlab,      ats: greenhouse, board_id: gitlab,      keywords_must_match: [vue, react, frontend]}
  - {name: hashicorp,   ats: greenhouse, board_id: hashicorp,   keywords_must_match: [react, frontend]}
  - {name: cloudflare,  ats: greenhouse, board_id: cloudflare,  keywords_must_match: [react, frontend]}
  - {name: discord,     ats: greenhouse, board_id: discord,     keywords_must_match: [react, frontend]}
  - {name: notion,      ats: greenhouse, board_id: notion,      keywords_must_match: [react, frontend]}
  - {name: sentry,      ats: greenhouse, board_id: sentry,      keywords_must_match: [react, frontend]}
  - {name: replicate,   ats: greenhouse, board_id: replicate,   keywords_must_match: [react, frontend, next]}
  - {name: huggingface, ats: greenhouse, board_id: huggingface, keywords_must_match: [react, frontend, next]}
  - {name: linear,      ats: greenhouse, board_id: linear,      keywords_must_match: [react, frontend]}
  - {name: posthog,     ats: greenhouse, board_id: posthog,     keywords_must_match: [react, frontend]}
  - {name: cal-com,     ats: greenhouse, board_id: cal,         keywords_must_match: [react, next, frontend]}
  - {name: clerk,       ats: greenhouse, board_id: clerk,       keywords_must_match: [react, next, frontend]}
```

**Register**:
```python
ATS_SOURCES = [
    ("ats_greenhouse", "sources.ats.greenhouse"),
]
# call run_sources(ATS_SOURCES, "Channel A — ATS Direct")
```

**Acceptance**: Run prints `ats_greenhouse: 30-80 raw`. Top-15 includes ≥3 ATS hits.

---

## Story E1.S4 — Lever ATS source (mirror of E1.S3)
Same structure with `https://api.lever.co/v0/postings/{slug}?mode=json` endpoint. Add Lever-using companies (Cloudflare partial, Toptal, Lemon.io, Toptal, Replit, Webflow). Skip if time-boxed; Greenhouse alone is the bigger win.

---

## Story E1.S5 — Fix Reddit r/forhire flair filter
**File**: `jobhunter/sources/direct/reddit_forhire.py`
**Change**: Add filter `if post.get("link_flair_text") != "Hiring": continue` before creating an Opportunity.

**Acceptance**: Bot run no longer surfaces `[For Hire]` posts as opportunities. Channel C count drops 50–80% but precision rises.

---

## Story E1.S6 — Update config.yaml & document changes
**File**: `jobhunter/config.yaml`

```yaml
sources:
  boards:
    remotive: true
    remoteok: false        # broken — see _deprecated
    himalayas: false       # broken — see _deprecated
    arbeitnow: true
    jobicy: false          # broken — see _deprecated
    weworkremotely: true
    weworkremotely_fullstack: true   # NEW
    hn_hiring: true
  ats:                                # NEW SECTION
    greenhouse: true
    lever: false           # not yet implemented
  freelance:
    upwork: false          # RSS deprecated by Upwork
    freelancer: true
  direct:
    reddit_forhire: true   # now flair-filtered
    hn_freelancer: true
    github_issues: true
```

---

## Definition of Done (Sprint 1)
- [ ] `python main.py --top 20 --no-llm` produces a digest with **≥25 React-relevant jobs scored ≥60**
- [ ] At least 5 entries from `ats_greenhouse_*` in top-20
- [ ] Zero `[For Hire]` posts surfaced from Reddit
- [ ] All deprecated sources moved to `sources/boards/_deprecated/`
- [ ] One QA run reviewed by user → ≥70% would-apply rate

→ After this sprint: Sprint 2 designs the smart scoring. See `06-sprint-2-stories.md` (to be drafted post-Sprint-1).
