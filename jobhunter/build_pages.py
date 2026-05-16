#!/usr/bin/env python3
"""Build _site/index.html — a single-page static job browser.

Aggregates all opportunities from JSON reports of the last 7 days into one
searchable, filterable React (Preact + htm via CDN) page. No per-run page —
the user sees actual job titles + companies + scores + links immediately
without clicking into anything.

Data source: reports/<date>-<time>.json (written by delivery.digest_md).
"""
from __future__ import annotations
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORTS = HERE / "reports"
OUT = HERE / "_site"
MAX_AGE_DAYS = 7

# Language filter for stale jobs already in committed JSON reports — newer
# reports won't have non-English jobs (main.py drops them upfront), but old
# reports might. Keep the page clean retroactively.
try:
    from langdetect import detect, DetectorFactory, LangDetectException
    DetectorFactory.seed = 0
    _LANG_DETECT_AVAILABLE = True
except ImportError:
    _LANG_DETECT_AVAILABLE = False


def _is_english(opp: dict) -> bool:
    if not _LANG_DETECT_AVAILABLE:
        return True
    text = ((opp.get("title") or "") + ". " + (opp.get("description") or "")).strip()
    if len(text) < 40:
        return True
    try:
        return detect(text[:1500]) == "en"
    except LangDetectException:
        return True


# Retroactive bot-noise filter for old reports (newer fetches already drop
# these upstream in sources/direct/github_issues.py).
import re as _re
_NOISE_TITLE_RE = _re.compile(
    r"\[(repo-status|daily-status|status|report|dependabot|bot|auto)\]",
    _re.IGNORECASE,
)


def _is_bot_noise(opp: dict) -> bool:
    title = opp.get("title") or ""
    if _NOISE_TITLE_RE.search(title):
        return True
    return False


# Cap how many OSS issues we surface from a single GitHub repo. Catches
# spam patterns like "Add Etiquette Tip #1..200" from a single project.
PER_REPO_CAP = 3


def _repo_key(opp: dict) -> str:
    """Extract 'owner/repo' from an [OSS] title; empty for non-OSS."""
    title = opp.get("title") or ""
    if not title.startswith("[OSS]"):
        return ""
    # Title format: "[OSS] owner/repo: <issue title>"
    rest = title[len("[OSS]"):].lstrip()
    return rest.split(":", 1)[0].strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

    # Collect all opportunities from JSON reports within the window.
    opps_by_url: dict[str, dict] = {}
    run_count = 0

    if REPORTS.exists():
        for p in sorted(REPORTS.glob("*.json"), key=lambda p: p.name, reverse=True):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            ts_str = data.get("generated_at")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                continue
            if ts < cutoff:
                continue
            run_count += 1
            run_id = data.get("run_id", p.stem)
            for opp in data.get("opportunities", []):
                url = opp.get("url") or ""
                if not url:
                    continue
                # Dedup across runs by URL — keep the entry from the newest run
                if url in opps_by_url:
                    continue
                # Drop Channel D (OSS) entirely — user wants startup/job focus,
                # not OSS busywork. Old reports still contain D entries.
                if (opp.get("channel") or "").upper() == "D":
                    continue
                # Drop non-English postings from stale reports
                if not _is_english(opp):
                    continue
                # Drop bot-status reports / dependency bumps that were ingested
                # before the upstream filter was added
                if _is_bot_noise(opp):
                    continue
                opp["_run_id"] = run_id
                opp["_seen_at"] = ts.isoformat()
                opps_by_url[url] = opp

    opps = list(opps_by_url.values())

    # Cap entries-per-repo for the OSS channel — kills contribution-farm spam
    # like "lingdojo/kana-dojo: Add Etiquette Tip #1..200".
    per_repo: dict[str, int] = {}
    capped: list[dict] = []
    sorted_for_cap = sorted(opps, key=lambda o: o.get("score", 0), reverse=True)
    for opp in sorted_for_cap:
        repo = _repo_key(opp)
        if repo:
            per_repo[repo] = per_repo.get(repo, 0) + 1
            if per_repo[repo] > PER_REPO_CAP:
                continue
        capped.append(opp)
    opps = capped

    # Final sort: real-job channels (A=Remote boards, B=Freelance, C=Direct)
    # come before D (OSS), then by score within each tier. So the user sees
    # actual jobs at the top, OSS at the bottom.
    CHANNEL_RANK = {"A": 0, "B": 1, "C": 2, "D": 3}
    opps.sort(
        key=lambda o: (CHANNEL_RANK.get(o.get("channel", "Z"), 9), -float(o.get("score", 0) or 0))
    )

    payload = json.dumps(
        {
            "opportunities": opps,
            "run_count": run_count,
            "window_days": MAX_AGE_DAYS,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    page = TEMPLATE.replace("__PAYLOAD__", payload)
    (OUT / "index.html").write_text(page, encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(
        f"[build_pages] wrote _site/index.html · "
        f"{len(opps)} unique jobs from {run_count} run(s) (last {MAX_AGE_DAYS} days)"
    )


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>JobHunter</title>
<style>
:root {
  color-scheme: dark;
  --bg: #0f1115;
  --surface: #181b22;
  --surface-2: #1f232c;
  --border: #2a2f3a;
  --text: #e6e9ef;
  --dim: #9aa3b2;
  --accent: #6aa6ff;
  --accent-strong: #4f8bff;
  --good: #2ecc71;
  --warn: #f5a524;
  --bad: #7a8190;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--bg); color: var(--text); }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  line-height: 1.5;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.app { max-width: 1100px; margin: 0 auto; padding: 36px 22px 80px; }
.header { display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 24px; }
.title { font-size: 28px; margin: 0; letter-spacing: -0.02em; }
.sub { color: var(--dim); font-size: 13px; margin: 4px 0 0; }
.toolbar { display: grid; grid-template-columns: 1fr auto auto; gap: 10px; margin-bottom: 18px; }
@media (max-width: 600px) { .toolbar { grid-template-columns: 1fr; } }
.toolbar input, .toolbar select {
  background: var(--surface); border: 1px solid var(--border); color: var(--text);
  padding: 9px 12px; border-radius: 8px; font: inherit;
}
.counts { color: var(--dim); font-size: 12.5px; margin-bottom: 14px; }
.cards { display: flex; flex-direction: column; gap: 10px; }
.card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px;
  transition: border-color 0.15s ease;
}
.card:hover { border-color: var(--accent); }
.card-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.card-title { margin: 0; font-size: 15px; line-height: 1.35; font-weight: 600; }
.card-title a { color: var(--text); }
.card-title a:hover { color: var(--accent); }
.score { font-variant-numeric: tabular-nums; font-size: 13px; font-weight: 600; padding: 3px 9px; border-radius: 999px; white-space: nowrap; border: 1px solid var(--border); }
.score.high { color: #06321a; background: var(--good); border-color: transparent; }
.score.mid  { color: #1a1a1a; background: var(--warn); border-color: transparent; }
.score.low  { color: var(--dim); }
.meta { margin: 6px 0 0; color: var(--dim); font-size: 12.5px; display: flex; flex-wrap: wrap; gap: 6px 12px; }
.meta .pill { background: var(--surface-2); padding: 2px 9px; border-radius: 999px; }
.fit { margin: 8px 0 0; font-size: 12.5px; }
.fit .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; letter-spacing: 0.04em; margin-right: 6px; }
.fit .badge.strong { background: var(--good); color: #06321a; }
.fit .badge.ok     { background: var(--accent); color: #001f4d; }
.fit .badge.weak   { background: var(--warn); color: #1a1a1a; }
.fit .badge.reject { background: var(--bad); color: #fff; }
.fit .badge.urgent { background: #ff5252; color: #fff; }
.desc { margin: 8px 0 0; font-size: 13px; color: var(--text); opacity: 0.85; }
.actions { margin: 10px 0 0; display: flex; gap: 10px; align-items: center; }
.actions .open {
  display: inline-block; background: var(--accent-strong); color: white !important;
  padding: 6px 14px; border-radius: 6px; font-size: 12.5px; font-weight: 600;
}
.actions .open:hover { background: var(--accent); text-decoration: none; }
.empty { background: var(--surface); border: 1px dashed var(--border); border-radius: 10px; padding: 40px; text-align: center; color: var(--dim); }
footer { margin-top: 28px; text-align: center; color: var(--dim); font-size: 12px; }
</style>
</head>
<body>
<div id="root"></div>
<script type="application/json" id="bootstrap">__PAYLOAD__</script>
<script type="module">
import { h, render } from "https://esm.sh/preact@10.22.0";
import { useState, useMemo } from "https://esm.sh/preact@10.22.0/hooks";
import htm from "https://esm.sh/htm@3.1.1";
const html = htm.bind(h);

const CHANNEL_LABEL = {
  A: "Remote Boards",
  B: "Freelance",
  C: "Direct",
  D: "OSS",
};

const boot = JSON.parse(document.getElementById("bootstrap").textContent || "{}");
const ALL = boot.opportunities || [];

function scoreClass(s) {
  if (s >= 70) return "score high";
  if (s >= 45) return "score mid";
  return "score low";
}

function fitFromNote(note) {
  if (!note) return null;
  const m = note.match(/^\s*(?:⚡\s*URGENT\s*—\s*)?\[(STRONG|OK|WEAK|REJECT)\]/i);
  if (!m) return null;
  const urgent = /⚡|URGENT/.test(note);
  return { verdict: m[1].toLowerCase(), urgent };
}

function fmtDate(iso) {
  if (!iso) return "";
  try { return new Date(iso).toLocaleDateString(); } catch { return ""; }
}

function Card({ o }) {
  const fit = fitFromNote(o.llm_fit_note);
  const reason = (o.llm_fit_note || "").replace(/^\s*(?:⚡\s*URGENT\s*—\s*)?\[\w+\]\s*/i, "").split(" | wins:")[0].trim();
  return html`
    <article class="card">
      <div class="card-head">
        <h3 class="card-title"><a href=${o.url} target="_blank" rel="noopener">${o.title}</a></h3>
        <span class=${scoreClass(o.score || 0)}>${(o.score || 0).toFixed(0)}/100</span>
      </div>
      <div class="meta">
        <span>${o.company || "—"}</span>
        <span class="pill">Ch ${o.channel} · ${CHANNEL_LABEL[o.channel] || ""}</span>
        <span>${o.source}</span>
        ${o.posted_at ? html`<span>posted ${fmtDate(o.posted_at)}</span>` : null}
        ${o.is_remote ? html`<span class="pill">Remote</span>` : null}
      </div>
      ${fit ? html`
        <div class="fit">
          ${fit.urgent ? html`<span class="badge urgent">URGENT</span>` : null}
          <span class=${"badge " + fit.verdict}>${fit.verdict.toUpperCase()}</span>
          <span>${reason}</span>
        </div>` : null}
      ${o.description ? html`<p class="desc">${o.description.slice(0, 240)}${o.description.length > 240 ? "…" : ""}</p>` : null}
      <div class="actions">
        <a class="open" href=${o.url} target="_blank" rel="noopener">Open & apply →</a>
        <span style="color:var(--dim);font-size:11.5px">seen ${o._run_id || ""}</span>
      </div>
    </article>
  `;
}

function App() {
  const [query, setQuery] = useState("");
  const [minScore, setMinScore] = useState(0);
  const [channel, setChannel] = useState("any");

  const filtered = useMemo(() => {
    let list = ALL.slice();
    if (channel !== "any") list = list.filter(o => o.channel === channel);
    if (minScore > 0) list = list.filter(o => (o.score || 0) >= minScore);
    if (query) {
      const q = query.toLowerCase();
      list = list.filter(o =>
        (o.title || "").toLowerCase().includes(q) ||
        (o.company || "").toLowerCase().includes(q) ||
        (o.description || "").toLowerCase().includes(q) ||
        (o.source || "").toLowerCase().includes(q) ||
        (o.llm_fit_note || "").toLowerCase().includes(q)
      );
    }
    return list;
  }, [query, minScore, channel]);

  return html`
    <div class="app">
      <header class="header">
        <div>
          <h1 class="title">JobHunter</h1>
          <p class="sub">${ALL.length} unique jobs from the last ${boot.window_days} days · ${boot.run_count} run(s)</p>
        </div>
        <a href="https://github.com/tabishhassan5121472/Job_Hunter_Bot" target="_blank" rel="noopener">View source ↗</a>
      </header>

      <div class="toolbar">
        <input
          type="search"
          placeholder="Search title, company, source, fit note…"
          value=${query}
          onInput=${(e) => setQuery(e.target.value)}
        />
        <select value=${minScore} onChange=${(e) => setMinScore(Number(e.target.value))}>
          <option value="0">All scores</option>
          <option value="40">≥ 40</option>
          <option value="55">≥ 55</option>
          <option value="65">≥ 65</option>
          <option value="75">≥ 75</option>
        </select>
        <select value=${channel} onChange=${(e) => setChannel(e.target.value)}>
          <option value="any">All channels</option>
          <option value="A">Remote boards</option>
          <option value="B">Freelance</option>
          <option value="C">Direct</option>
          <option value="D">OSS</option>
        </select>
      </div>

      <p class="counts">${filtered.length} match(es)</p>

      ${filtered.length === 0
        ? html`<div class="empty">No matches — clear filters or wait for the next scheduled run.</div>`
        : html`<div class="cards">${filtered.map(o => html`<${Card} o=${o} />`)}</div>`}

      <footer>Built with Preact · rebuilt automatically every 5 hours by GitHub Actions</footer>
    </div>
  `;
}

render(html`<${App} />`, document.getElementById("root"));
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
