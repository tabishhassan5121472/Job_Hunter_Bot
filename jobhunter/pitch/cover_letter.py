"""Cover letter generator — Claude Sonnet, tailored per job.

Picks the CV variant per-opportunity (opp.cv_variant), set by the scorer.
Defaults to cv_frontend if the variant file is missing.
"""
from __future__ import annotations
import os
from functools import lru_cache
from pathlib import Path

from core.models import Opportunity

PROFILE_DIR = Path(__file__).parent.parent / "profile"
WINS_TEXT = (PROFILE_DIR / "wins.md").read_text()
PREFS_TEXT = (PROFILE_DIR / "preferences.md").read_text()


@lru_cache(maxsize=8)
def _load_cv(variant: str) -> str:
    """Load a CV variant by stem name (e.g. 'cv_frontend', 'cv_employed').
    Falls back to cv_frontend if the requested variant doesn't exist."""
    path = PROFILE_DIR / f"{variant}.md"
    if not path.exists():
        path = PROFILE_DIR / "cv_frontend.md"
    return path.read_text()


def _system_prompt(cv_text: str) -> str:
    return f"""You write concise, non-generic cover letters for Tabish Hassan.

<profile cache_control={{"type":"ephemeral"}}>
{cv_text}

{WINS_TEXT}

{PREFS_TEXT}
</profile>

Rules:
- NEVER start with "I am writing to apply"
- NEVER use: passionate, rockstar, synergy, ninja, guru
- Lead with ONE specific metric or achievement relevant to THIS job
- Reference something specific from THEIR post (tech stack, product, problem)
- Close with a clear ask (call, quick chat, send portfolio link)
- For Channel B/C (freelance/direct): max 120 words, DM-friendly tone
- For Channel A (job boards): max 250 words, slightly more formal
- Return ONLY the letter text, no subject line, no "Dear Hiring Manager"
"""


def generate(opp: Opportunity) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "[Set ANTHROPIC_API_KEY to enable cover letter generation]"

    try:
        import anthropic
    except ImportError:
        return "[anthropic package not installed]"

    client = anthropic.Anthropic(api_key=api_key)

    cv_text = _load_cv(opp.cv_variant or "cv_frontend")
    word_limit = "120 words" if opp.channel in ("B", "C") else "250 words"
    tone = "casual DM" if opp.channel in ("B", "C") else "professional email"

    prompt = f"""Write a {tone} cover letter (max {word_limit}) for this opportunity:

Title: {opp.title}
Company/Client: {opp.company_or_client}
Channel: {opp.channel} ({opp.source})
LLM fit note: {opp.llm_fit_note}
Description:
{opp.description[:1200]}

Pick the 2-3 most relevant achievements from the wins bank and weave them in naturally."""

    try:
        msg = client.messages.create(
            model="claude-sonnet-20241022",
            max_tokens=500,
            system=_system_prompt(cv_text),
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return f"[cover letter error: {e}]"
