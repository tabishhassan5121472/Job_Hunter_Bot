"""Upwork — public RSS feed, Channel B."""
from __future__ import annotations
import hashlib
import re
from datetime import datetime

import feedparser

from core.fetcher import fetch_text
from core.models import Opportunity

# Public Upwork RSS — no auth needed, searches recent postings
FEEDS = [
    "https://www.upwork.com/ab/feed/jobs/rss?q=react+frontend&sort=recency&paging=0%3B50",
    "https://www.upwork.com/ab/feed/jobs/rss?q=react+typescript&sort=recency&paging=0%3B50",
    "https://www.upwork.com/ab/feed/jobs/rss?q=reactjs+developer&sort=recency&paging=0%3B50",
]


def fetch() -> list[Opportunity]:
    out = []
    seen_urls: set[str] = set()

    for feed_url in FEEDS:
        text = fetch_text(feed_url)
        if not text:
            continue
        feed = feedparser.parse(text)
        for entry in feed.entries:
            url = entry.get("link", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            title = entry.get("title", "")
            desc = re.sub(r"<[^>]+>", " ", entry.get("summary", ""))
            published = entry.get("published", "")
            try:
                posted_at = datetime(*entry.published_parsed[:6])
            except Exception:
                posted_at = None

            # Extract budget hint
            budget_match = re.search(r"\$(\d+(?:\.\d+)?)", desc)
            budget = float(budget_match.group(1)) if budget_match else None

            opp = Opportunity(
                id=hashlib.md5(url.encode()).hexdigest(),
                url=url,
                source="upwork",
                channel="B",
                title=title,
                company_or_client="Upwork Client",
                description=desc[:3000],
                stack=[],
                is_remote=True,
                contact_method="upwork_proposal",
                budget=budget,
                posted_at=posted_at,
            )
            out.append(opp)
    return out
