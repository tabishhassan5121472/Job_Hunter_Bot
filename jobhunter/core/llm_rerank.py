"""LLM rerank of top opportunities — provider-agnostic via core.llm_provider."""
from __future__ import annotations
import json
from pathlib import Path

from core.models import Opportunity
from core.llm_provider import complete, is_configured, strip_json_fences

PROFILE_DIR = Path(__file__).parent.parent / "profile"
CV_TEXT = (PROFILE_DIR / "cv_frontend.md").read_text()
WINS_TEXT = (PROFILE_DIR / "wins.md").read_text()
PREFS_TEXT = (PROFILE_DIR / "preferences.md").read_text()

SYSTEM_PROMPT = f"""You are a job-fit analyst for Tabish Hassan — a full-stack React developer (with NestJS microservices experience as of Dec 2025), iOS app shipper (20+ apps), and AI/automation tinkerer. Based in Rawalpindi, Pakistan (UTC+5), remote-only.

<candidate_profile>
{CV_TEXT}

## Achievement Bank
{WINS_TEXT}

## Preferences
{PREFS_TEXT}
</candidate_profile>

Your job: given a job/opportunity, output a JSON object with these exact keys:
- "fit": one of "strong" | "ok" | "weak" | "reject"
- "score_adjustment": integer between -30 and +20 (added to current rule-based score)
- "reason": one short sentence why
- "matching_wins": array of 2-3 short labels from the achievement bank (e.g. "rubios_perf", "ios_shipping", "a11y_wcag")
- "flag": "urgent" if it's a very strong fit AND looks freshly posted, else ""

Respond with ONLY a valid JSON object. No markdown fences, no prose around it."""


def rerank(opportunities: list[Opportunity]) -> list[Opportunity]:
    """Rerank top opportunities. No-op if no LLM provider is configured."""
    if not is_configured():
        return opportunities

    updated = []
    for opp in opportunities:
        job_text = f"""Title: {opp.title}
Company: {opp.company_or_client}
Source: {opp.source} (Channel {opp.channel})
Current score: {opp.score}
Stack mentioned: {', '.join(opp.stack[:10])}
Description (first 800 chars):
{opp.description[:800]}"""

        raw = complete(
            system=SYSTEM_PROMPT,
            user=job_text,
            max_tokens=300,
            model_hint="fast",
            temperature=0.1,
        )
        if not raw or raw.startswith("[llm error"):
            opp.llm_fit_note = raw or "[rerank skipped]"
            updated.append(opp)
            continue

        try:
            result = json.loads(strip_json_fences(raw))
            adj = int(result.get("score_adjustment", 0))
            opp.score = max(0.0, min(100.0, opp.score + adj))
            opp.llm_fit_note = f"[{str(result.get('fit', '?')).upper()}] {result.get('reason', '')}"
            if result.get("flag") == "urgent":
                opp.llm_fit_note = "⚡ URGENT — " + opp.llm_fit_note
            wins = result.get("matching_wins", [])
            if wins:
                opp.llm_fit_note += f" | wins: {', '.join(wins)}"
        except Exception as e:
            opp.llm_fit_note = f"[rerank parse error: {e}]"

        updated.append(opp)

    return updated
