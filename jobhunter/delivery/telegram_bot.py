"""Telegram delivery — real-time alerts for high-value Channel C hits."""
from __future__ import annotations
import os
from core.models import Opportunity


def send_alert(opp: Opportunity) -> bool:
    """Send a Telegram message for a high-value opportunity. Returns True on success."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False

    try:
        import httpx
        score_bar = "█" * int(opp.score / 10)
        text = (
            f"🎯 *New Lead — Score {opp.score:.0f}/100* {score_bar}\n\n"
            f"*{opp.title}*\n"
            f"_{opp.company_or_client}_ · `{opp.source}`\n\n"
            f"{opp.description[:300].strip()}...\n\n"
            f"[Open]({opp.url})"
        )
        if opp.llm_fit_note:
            text += f"\n\n💡 _{opp.llm_fit_note}_"

        r = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            },
            timeout=10,
        )
        return r.status_code == 200
    except Exception:
        return False


def send_digest_summary(total: int, top_score: float, report_path: str) -> bool:
    """Send a brief daily summary to Telegram."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False

    try:
        import httpx
        text = (
            f"📋 *JobHunter Daily Digest*\n"
            f"Found *{total}* new opportunities\n"
            f"Top score: *{top_score:.0f}/100*\n"
            f"Report: `{report_path}`"
        )
        r = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
        return r.status_code == 200
    except Exception:
        return False
