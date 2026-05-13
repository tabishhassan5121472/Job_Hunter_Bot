"""WeWorkRemotely — Full-stack RSS feed (Channel A). Highest-volume React source per market research."""
from __future__ import annotations
import hashlib
import re
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser

from core.fetcher import fetch_text
from core.models import Opportunity

FEED_URL = "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss"


def _to_opportunity(entry) -> Opportunity:
    title = entry.get("title", "") or ""
    summary = re.sub(r"<[^>]+>", " ", entry.get("summary", "") or "")[:1500]
    if ":" in title:
        company, clean_title = title.split(":", 1)
        company, clean_title = company.strip(), clean_title.strip()
    else:
        company, clean_title = "Unknown", title
    try:
        posted = parsedate_to_datetime(entry.get("published", ""))
    except Exception:
        posted = datetime.now()
    uid = hashlib.md5(entry.get("link", title).encode()).hexdigest()
    return Opportunity(
        id=uid,
        channel="A",
        source="weworkremotely_fullstack",
        title=clean_title[:120],
        company_or_client=company[:60],
        location="Remote",
        url=entry.get("link", ""),
        description=summary,
        posted_at=posted.isoformat() if hasattr(posted, "isoformat") else str(posted),
        is_remote=True,
    )


def fetch() -> list[Opportunity]:
    text = fetch_text(FEED_URL)
    if not text:
        return []
    feed = feedparser.parse(text)
    return [_to_opportunity(e) for e in feed.entries]
