"""Jobicy — RSS feed, Channel A (replaces dead Upwork RSS)."""
from __future__ import annotations
import hashlib
import re
from datetime import datetime

import feedparser

from core.fetcher import fetch_text
from core.models import Opportunity

FEEDS = [
    "https://jobicy.com/?feed=job_feed&job_categories=dev&job_types=remote&search_keywords=react",
    "https://jobicy.com/?feed=job_feed&job_categories=dev&job_types=remote&search_keywords=frontend",
]


def fetch() -> list[Opportunity]:
    out = []
    seen: set[str] = set()

    for feed_url in FEEDS:
        text = fetch_text(feed_url)
        if not text:
            continue
        feed = feedparser.parse(text)
        for entry in feed.entries:
            url = entry.get("link", "")
            if not url or url in seen:
                continue
            seen.add(url)

            desc = re.sub(r"<[^>]+>", " ", entry.get("summary", ""))
            try:
                posted_at = datetime(*entry.published_parsed[:6])
            except Exception:
                posted_at = None

            opp = Opportunity(
                id=hashlib.md5(url.encode()).hexdigest(),
                url=url,
                source="jobicy",
                channel="A",
                title=entry.get("title", ""),
                company_or_client=entry.get("author", ""),
                description=desc[:3000],
                stack=[],
                is_remote=True,
                posted_at=posted_at,
            )
            out.append(opp)
    return out
