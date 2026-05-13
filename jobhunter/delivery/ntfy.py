"""ntfy.sh delivery — free open-source push notifications.

How it works:
  - ntfy uses 'topics' as the addressing scheme. A topic is just a secret URL
    path like https://ntfy.sh/<topic>. Anyone who knows the topic can subscribe
    or publish — so pick something hard to guess.
  - Publishing: HTTP POST to https://ntfy.sh/<topic> with the message in the body.
  - Subscribing: open the 'ntfy' app on your phone, tap '+', enter the topic name.

Setup (one-time):
  1. Install the ntfy app: https://ntfy.sh/app (Play Store / App Store).
  2. In the app, subscribe to a topic of your choosing (must be hard to guess).
  3. Export the env var:
       NTFY_TOPIC="jobhunter-tabish-h7k2m9"   # pick your own, keep secret
  4. (Optional) self-host on your own server and set NTFY_SERVER.

The pipeline skips ntfy silently if NTFY_TOPIC is missing.
"""
from __future__ import annotations
import os
from core.models import Opportunity


def _send(title: str, body: str, *, priority: int = 3, click: str | None = None, tags: str | None = None) -> bool:
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        return False
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    try:
        import httpx
        headers = {
            "Title": title,
            "Priority": str(priority),
        }
        if click:
            headers["Click"] = click
        if tags:
            headers["Tags"] = tags
        r = httpx.post(f"{server}/{topic}", content=body.encode("utf-8"), headers=headers, timeout=10)
        return r.status_code in (200, 202)
    except Exception:
        return False


def _truncate(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def send_alert(opp: Opportunity) -> bool:
    """Push notification per high-value opportunity. Tapping opens the URL.
    Emojis are passed via ntfy's `Tags` header (which the apps render as icons)
    instead of inline in the title, because emojis are not valid in HTTP headers."""
    title = f"{opp.score:.0f}/100 - {_truncate(opp.title, 70)}"
    body_lines = [
        f"{_truncate(opp.company_or_client, 60)} | {opp.source}",
        "",
        _truncate(opp.description, 280),
    ]
    if opp.llm_fit_note:
        body_lines.append("")
        body_lines.append(f"Fit: {_truncate(opp.llm_fit_note, 160)}")
    priority = 4 if opp.score >= 75 else 3
    return _send(
        title=title,
        body="\n".join(body_lines),
        priority=priority,
        click=opp.url,
        tags="dart",
    )


def send_digest_summary(total: int, top_score: float, report_path: str) -> bool:
    """Short per-run summary notification."""
    title = f"JobHunter - {total} new (top {top_score:.0f}/100)"
    body = f"Latest report:\n{report_path}"
    return _send(title=title, body=body, priority=2, tags="clipboard")
