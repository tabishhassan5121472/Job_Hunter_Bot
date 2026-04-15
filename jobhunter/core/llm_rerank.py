"""Claude Haiku rerank with prompt-cached CV + preferences."""
from __future__ import annotations
import os
import json
from pathlib import Path

from core.models import Opportunity

PROFILE_DIR = Path(__file__).parent.parent / "profile"
CV_TEXT = (PROFILE_DIR / "cv_frontend.md").read_text()
WINS_TEXT = (PROFILE_DIR / "wins.md").read_text()
PREFS_TEXT = (PROFILE_DIR / "preferences.md").read_text()

SYSTEM_PROMPT = f"""You are a job-fit analyst for Tabish Hassan, a React.js frontend developer seeking remote work.

<candidate_profile cache_control={{"type":"ephemeral"}}>
{CV_TEXT}

## Achievement Bank
{WINS_TEXT}

## Preferences
{PREFS_TEXT}
</candidate_profile>

Your job: given a job/opportunity, output a JSON object with:
- "fit": "strong" | "ok" | "weak" | "reject"
- "score_adjustment": integer -30 to +20 (adjustment to add to current rule-based score)
- "reason": one sentence why
- "matching_wins": list of 2-3 win bullet IDs from the achievement bank that best match this job (use short labels like "rubios_perf", "crm_kanban", "a11y_wcag" etc)
- "flag": "urgent" if posted <24h AND score>60, else ""

Respond ONLY with valid JSON. No markdown fences."""


def rerank(opportunities: list[Opportunity]) -> list[Opportunity]:
    """Rerank top opportunities using Claude Haiku. Returns updated list."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return opportunities

    try:
        import anthropic
    except ImportError:
        return opportunities

    client = anthropic.Anthropic(api_key=api_key)

    updated = []
    for opp in opportunities:
        job_text = f"""Title: {opp.title}
Company: {opp.company_or_client}
Source: {opp.source} (Channel {opp.channel})
Current score: {opp.score}
Stack mentioned: {', '.join(opp.stack[:10])}
Description (first 800 chars):
{opp.description[:800]}"""

        try:
            msg = client.messages.create(
                model="claude-haiku-20240307",
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": job_text}],
            )
            result = json.loads(msg.content[0].text)

            adj = int(result.get("score_adjustment", 0))
            opp.score = max(0.0, min(100.0, opp.score + adj))
            opp.llm_fit_note = f"[{result.get('fit','?').upper()}] {result.get('reason','')}"
            if result.get("flag") == "urgent":
                opp.llm_fit_note = "⚡ URGENT — " + opp.llm_fit_note

            # Store matching wins in llm_fit_note for cover letter use
            wins = result.get("matching_wins", [])
            if wins:
                opp.llm_fit_note += f" | wins: {', '.join(wins)}"

        except Exception as e:
            opp.llm_fit_note = f"[rerank error: {e}]"

        updated.append(opp)

    return updated
