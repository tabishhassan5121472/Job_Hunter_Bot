"""Freelancer.com — public RSS, Channel B."""
from __future__ import annotations
import hashlib
import re
from datetime import datetime

import feedparser

from core.fetcher import fetch_text
from core.models import Opportunity

FEEDS = [
    "https://www.freelancer.com/jobs/react/?format=rss",
    "https://www.freelancer.com/jobs/website-design/react/?format=rss",
    "https://www.freelancer.com/jobs/javascript/?format=rss",
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

            budget_match = re.search(r"\$(\d+(?:\.\d+)?)", desc)
            budget = float(budget_match.group(1)) if budget_match else None

            opp = Opportunity(
                id=hashlib.md5(url.encode()).hexdigest(),
                url=url,
                source="freelancer",
                channel="B",
                title=entry.get("title", ""),
                company_or_client="Freelancer Client",
                description=desc[:3000],
                stack=[],
                is_remote=True,
                contact_method="freelancer_bid",
                budget=budget,
                posted_at=posted_at,
            )
            out.append(opp)
    return out
