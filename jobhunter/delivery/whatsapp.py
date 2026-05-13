"""WhatsApp delivery via CallMeBot — works in Pakistan without VPN.

Setup (one-time):
  1. Save the number +34 623 78 64 49 to your phone contacts.
     (CallMeBot rotates this number occasionally — if it's not on WhatsApp,
      check https://www.callmebot.com/blog/free-api-whatsapp-messages/ for the
      latest activation number.)
  2. On WhatsApp, message that number: "I allow callmebot to send me messages".
  3. Wait for the reply containing your APIKEY (usually within a minute).
  4. Export the env vars before running JobHunter:
       CALLMEBOT_PHONE="92XXXXXXXXXX"   # your WhatsApp number, no +
       CALLMEBOT_APIKEY="123456"         # from the reply

The pipeline skips WhatsApp silently if either env var is missing.
"""
from __future__ import annotations
import os
import urllib.parse
from core.models import Opportunity


def _send(text: str) -> bool:
    phone = os.environ.get("CALLMEBOT_PHONE")
    apikey = os.environ.get("CALLMEBOT_APIKEY")
    if not phone or not apikey:
        return False
    try:
        import httpx
        url = "https://api.callmebot.com/whatsapp.php"
        params = {"phone": phone, "text": text, "apikey": apikey}
        r = httpx.get(url, params=params, timeout=15)
        # CallMeBot returns 200 on success; body contains "Message queued" etc.
        return r.status_code == 200 and "ERROR" not in r.text.upper()
    except Exception:
        return False


def _truncate(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def send_alert(opp: Opportunity) -> bool:
    """One WhatsApp message per high-value opportunity. WhatsApp markdown:
    *bold*, _italic_, `mono`. Raw URLs auto-link."""
    score_bar = "█" * int(opp.score / 10)
    lines = [
        f"🎯 *Lead — {opp.score:.0f}/100* {score_bar}",
        f"*{_truncate(opp.title, 80)}*",
        f"_{_truncate(opp.company_or_client, 40)}_ · `{opp.source}`",
        "",
        _truncate(opp.description, 220),
        "",
        opp.url,
    ]
    if opp.llm_fit_note:
        lines.append("")
        lines.append(f"💡 _{_truncate(opp.llm_fit_note, 140)}_")
    return _send("\n".join(lines))


def send_digest_summary(total: int, top_score: float, report_path: str) -> bool:
    """Short daily/run summary."""
    text = (
        "📋 *JobHunter run complete*\n"
        f"New opportunities: *{total}*\n"
        f"Top score: *{top_score:.0f}/100*\n"
        f"Report: `{report_path}`"
    )
    return _send(text)
