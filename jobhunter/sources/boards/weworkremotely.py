"""WeWorkRemotely — RSS feed, Channel A."""
from __future__ import annotations
import hashlib
import re
from datetime import datetime

import feedparser

from core.fetcher import fetch_text
from core.models import Opportunity

FEEDS = [
    "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
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

            title = entry.get("title", "")
            # WWR title format: "Company: Job Title"
            company = ""
            if ": " in title:
                parts = title.split(": ", 1)
                company, title = parts[0], parts[1]

            desc = re.sub(r"<[^>]+>", " ", entry.get("summary", ""))
            try:
                posted_at = datetime(*entry.published_parsed[:6])
            except Exception:
                posted_at = None

            opp = Opportunity(
                id=hashlib.md5(url.encode()).hexdigest(),
                url=url,
                source="weworkremotely",
                channel="A",
                title=title,
                company_or_client=company,
                description=desc[:3000],
                stack=[],
                is_remote=True,
                posted_at=posted_at,
            )
            out.append(opp)
    return out
