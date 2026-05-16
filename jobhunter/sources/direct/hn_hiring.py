"""Hacker News 'Who is hiring?' monthly thread — Channel A.

Posted by the dedicated `whoishiring` account on the first of every month
(e.g. "Ask HN: Who is hiring? (November 2026)"). Every top-level comment is a
company hiring post. Heavy on YC-backed and similar early-stage startups —
exactly what we're targeting.

Convention from past years:
- Each comment is one job posting
- First line typically reads "Company | Position | Location | Tech | comp/url"
- "REMOTE" or "ONSITE" markers in caps
- Many include "ANY COUNTRY", "WORLDWIDE", "Visa: Yes/No" for Pakistan-relevance
"""
from __future__ import annotations
import hashlib
import re
import time
from datetime import datetime, timezone

from core.fetcher import fetch_json
from core.models import Opportunity


def _get_latest_thread_id() -> int | None:
    """Find the most recent 'Ask HN: Who is hiring? (Month YYYY)' thread
    posted by the whoishiring account."""
    sixty_days_ago = int(time.time()) - 60 * 86400
    url = (
        "https://hn.algolia.com/api/v1/search"
        f"?tags=story,author_whoishiring"
        f"&numericFilters=created_at_i>{sixty_days_ago}"
        "&hitsPerPage=10"
    )
    data = fetch_json(url)
    if not data:
        return None
    for hit in data.get("hits", []):
        title = (hit.get("title") or "").lower()
        if "who is hiring" in title or "who's hiring" in title:
            return hit.get("objectID")
    return None


def _strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", s).strip()


def _parse_first_line(text: str) -> tuple[str, str]:
    """Extract a 'Company - Title' summary from the first ~120 chars of a
    typical 'Company | Role | Location | Stack' format."""
    head = text.split("\n")[0] if "\n" in text else text[:200]
    head = head.strip()
    parts = [p.strip() for p in head.split("|")]
    if len(parts) >= 2:
        return parts[0], parts[1]
    # Fall back: just first phrase
    return head[:60], head[60:160] if len(head) > 60 else "Hiring post"


def fetch() -> list[Opportunity]:
    thread_id = _get_latest_thread_id()
    if not thread_id:
        return []

    # Pull only TOP-LEVEL comments (job posts), not nested replies/discussion.
    # parent_id == thread_id filters to direct children of the story.
    url = (
        "https://hn.algolia.com/api/v1/search"
        f"?tags=comment,story_{thread_id}"
        f"&numericFilters=parent_id={thread_id}"
        "&hitsPerPage=500"
    )
    data = fetch_json(url)
    if not data:
        return []

    out: list[Opportunity] = []
    for hit in data.get("hits", []):
        text_html = hit.get("comment_text") or ""
        if not text_html:
            continue
        text = _strip_html(text_html)
        if len(text) < 80:  # skip drive-by replies
            continue

        # The thread also has "ME WANTS TO WORK" replies and meta comments
        # without "REMOTE/ONSITE" markers. Keep only ones that look like
        # company hiring posts (mention a location or REMOTE).
        text_upper = text.upper()
        if not (
            "REMOTE" in text_upper
            or "ONSITE" in text_upper
            or "HYBRID" in text_upper
            or "|" in text  # the canonical Company|Role|Location format
        ):
            continue

        obj_id = hit.get("objectID", "")
        if not obj_id:
            continue
        url_full = f"https://news.ycombinator.com/item?id={obj_id}"

        company, role = _parse_first_line(text)
        created = hit.get("created_at_i")
        posted_at = datetime.fromtimestamp(created, tz=timezone.utc) if created else None

        opp = Opportunity(
            id=hashlib.md5(url_full.encode()).hexdigest(),
            url=url_full,
            source="hn_who_is_hiring",
            channel="A",
            title=f"{company} — {role}"[:140] if role else company[:140],
            company_or_client=company[:80],
            description=text[:3000],
            stack=[],
            is_remote=("REMOTE" in text_upper or "WORLDWIDE" in text_upper),
            contact_method="hn_reply",
            posted_at=posted_at,
        )
        out.append(opp)
    return out
