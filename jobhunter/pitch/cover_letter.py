"""Cover letter generator — Claude Sonnet, tailored per job."""
from __future__ import annotations
import os
from pathlib import Path

from core.models import Opportunity

PROFILE_DIR = Path(__file__).parent.parent / "profile"
CV_TEXT   = (PROFILE_DIR / "cv_frontend.md").read_text()
WINS_TEXT = (PROFILE_DIR / "wins.md").read_text()
PREFS_TEXT = (PROFILE_DIR / "preferences.md").read_text()

SYSTEM = f"""You write concise, non-generic cover letters for Tabish Hassan.

<profile cache_control={{"type":"ephemeral"}}>
{CV_TEXT}

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
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return f"[cover letter error: {e}]"
