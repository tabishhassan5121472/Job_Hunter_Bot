# Architecture — JobHunter v2

**Author**: BMAD Architect agent
**Date**: 2026-04-30
**PRD**: `03-prd.md`

## 1. High-level shape (no big rewrite)
The current pipeline is fundamentally sound:

```
fetch → dedup → score → rerank (LLM) → digest → notify
```

We **enhance**, not replace. New stages slot in cleanly:

```
fetch (more+better sources)
  → dedup (cross-source hash)
  → classify (geo, tz, rate, seniority)   # NEW
  → score (keyword + embedding)            # ENHANCED
  → rerank (multi-agent, top-20 only)      # NEW (Epic 5)
  → digest (with verdict + portfolio refs) # ENHANCED
  → notify
```

## 2. New & changed files

### Sources (Epic 1)
```
jobhunter/sources/
  boards/
    weworkremotely_fullstack.py    [NEW]   # WW Fullstack RSS feed
    weworkremotely_all.py           [NEW]   # WW all-remote feed
    himalayas.py                    [REMOVE → _deprecated/]
    jobicy.py                       [REMOVE → _deprecated/]
    remoteok.py                     [REMOVE → _deprecated/]
  ats/                              [NEW DIR]
    __init__.py
    greenhouse.py                   [NEW]   # iterate company list
    lever.py                        [NEW]
  direct/
    reddit_forhire.py               [FIX]   # filter flair == "Hiring"
```

### Config
```
jobhunter/config/
  ats_companies.yaml                [NEW]   # 30 remote-first firms
  scoring_weights.yaml              [NEW]   # extracted from main config for tuning
```

### Core (Epic 2)
```
jobhunter/core/
  classifiers/                      [NEW DIR]
    geo.py        # Pakistan/global friendliness
    timezone.py   # tz overlap detection
    seniority.py  # match 4+ yrs profile
    rate.py       # extract $/hr or salary range
  embedding.py    [NEW]   # JD↔CV cosine similarity via Anthropic
  scorer.py       [REWRITE — multi-criteria]
```

### Tracking & feedback (Epic 3)
```
jobhunter/tracker/
  applied.py      [ENHANCE]  # auto-seed from digest, mark commands
  feedback.py     [NEW]      # writes feedback.jsonl, reads it for penalty
```

### Pitch (Epic 4)
```
jobhunter/pitch/
  cover_letter.py [ENHANCE]  # portfolio URL injection + evidence cites
  portfolio_refs.py [NEW]    # selects 2-3 best deployed projects per JD
```

### Multi-agent (Epic 5)
```
jobhunter/agents/                   [NEW DIR]
  __init__.py
  analyst.py      # fit assessment
  researcher.py   # company background lookup
  strategist.py   # pitch angle suggestion
  orchestrator.py # runs trio on top-20, caches by company
```

## 3. Data model changes

### `Opportunity` (extend existing pydantic model)
```python
class Opportunity(BaseModel):
    # existing fields...
    geo_friendly: Literal["green", "yellow", "red"]      # NEW
    tz_overlap: Literal["good", "marginal", "bad"]        # NEW
    seniority_match: Literal["below", "match", "above"]   # NEW
    min_rate_usd: int | None                              # NEW
    max_rate_usd: int | None                              # NEW
    embedding_score: float                                # NEW (0-1)
    company_normalized: str                               # NEW (for dedup)
    title_normalized: str                                 # NEW (for dedup)
    agent_verdict: str | None                             # NEW (Epic 5)
    portfolio_refs: list[str]                             # NEW (Epic 4)
```

### New SQLite tables
```sql
CREATE TABLE feedback (
    opportunity_id TEXT PRIMARY KEY,
    label TEXT,             -- good|bad|applied|interview|rejected
    notes TEXT,
    timestamp TEXT
);

CREATE TABLE company_cache (
    company_normalized TEXT PRIMARY KEY,
    research_json TEXT,
    last_updated TEXT       -- 7-day TTL
);
```

## 4. ATS architecture

```yaml
# config/ats_companies.yaml
companies:
  - name: vercel
    ats: greenhouse
    board_id: vercel
    keywords_must_match: [react, frontend, full-stack, javascript, typescript]
    geo_default: global   # known remote-first
  - name: stripe
    ats: greenhouse
    board_id: stripe
    keywords_must_match: [react, frontend]
    geo_default: yellow
  # ... 28 more
```

Fetcher pseudocode:
```python
def fetch():
    all_jobs = []
    for company in ats_companies:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company.board_id}/jobs?content=true"
        jobs = httpx.get(url, timeout=10).json()["jobs"]
        for j in jobs:
            if any(kw in (j["title"] + j["content"]).lower() for kw in company.keywords_must_match):
                all_jobs.append(to_opportunity(j, company))
        time.sleep(0.5)  # rate-limit
    return all_jobs
```

## 5. Embedding scorer architecture

```python
class EmbeddingScorer:
    def __init__(self, cv_path="profile/cv_frontend.md"):
        self.cv_text = Path(cv_path).read_text()
        self.client = anthropic.Anthropic()
        self.cv_embedding = self._embed(self.cv_text)

    def _embed(self, text):
        # Anthropic doesn't have native embeddings yet — use Voyage AI (Anthropic-recommended)
        # OR use Claude with "score this match" prompt as proxy
        # OR use sentence-transformers locally for $0
        ...

    def score(self, jd_text):
        jd_emb = self._embed(jd_text)
        return cosine_similarity(self.cv_embedding, jd_emb)  # 0-1
```

**Decision**: Use **`sentence-transformers/all-MiniLM-L6-v2`** locally — free, fast, runs on CPU, 90% as good as Claude embeddings for this use-case. Falls back to Claude rerank for tie-breaking.

## 6. Multi-agent orchestrator (Epic 5 / Option B)

```python
# agents/orchestrator.py
class MultiAgent:
    def evaluate(self, opp: Opportunity) -> dict:
        cached = company_cache.get(opp.company_normalized)
        company_research = cached or self.researcher.run(opp.company_or_client)
        if not cached:
            company_cache.set(opp.company_normalized, company_research, ttl_days=7)

        analyst_verdict = self.analyst.run(opp, cv=USER_CV)        # fit, gaps, risks
        strategist_pitch = self.strategist.run(opp, company_research, analyst_verdict)

        return {
            "fit_score": analyst_verdict.score,
            "company_summary": company_research.summary,
            "pitch_angle": strategist_pitch.angle,
            "concerns": analyst_verdict.concerns,
        }
```

**Cost control**:
- Run only on top-20 (after rule scoring)
- Cache company research 7 days (most listings come from <50 unique companies/week)
- Use `claude-haiku-20240307` for analyst & researcher; `claude-sonnet-20241022` only for strategist on top-5

Estimated cost per run: 20 × (3 × ~500 tokens × Haiku) + 5 × Sonnet ≈ **$0.04/run**.

## 7. Backwards compatibility
- `python main.py` works exactly as before (all new behavior is additive)
- Old digests in `reports/` remain valid
- New columns added with defaults; existing DB rows unaffected
- All new features behind feature flags in `config.yaml`

## 8. Testing strategy
- Unit tests for each classifier (`geo`, `tz`, `seniority`, `rate`) with 20+ JD samples
- Integration test that runs the full pipeline against fixture JSON (no network)
- Dry-run flag `--dry-run` (no DB writes, no LLM calls) for CI

## 9. Migration steps (zero-downtime)
1. Land Epic 1 (source overhaul) behind `sources.v2_enabled: true` flag
2. Run both old + new for 3 days, compare digests
3. Flip default; archive old fetchers
4. Land Epic 2 (scoring) — same pattern
5. Epic 3, 4, 5 land independently

→ Next: Story breakdown for Sprint 1. See `05-sprint-1-stories.md`.
