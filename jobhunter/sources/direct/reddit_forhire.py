"""Reddit r/forhire + r/remotejs + r/reactjs — Channel C (direct clients).

Uses Reddit's public RSS feeds (no API, no auth) with a proper User-Agent so
GitHub Actions IPs don't get the anonymous-JSON 403 block. Reddit tolerates
RSS reads from any IP as long as the User-Agent isn't generic/empty.
"""
from __future__ import annotations
import hashlib
import re
from datetime import datetime, timezone

import feedparser

from core.models import Opportunity

SUBREDDITS = ["forhire", "remotejs", "reactjs"]

USER_AGENT = "JobHunter/1.0 (by /u/Tabish-Software-Dev - personal job search)"


def _parse_one(subreddit: str) -> list[Opportunity]:
    url = f"https://www.reddit.com/r/{subreddit}/new/.rss"
    parsed = feedparser.parse(url, request_headers={"User-Agent": USER_AGENT})
    if parsed.bozo and not parsed.entries:
        return []

    out: list[Opportunity] = []
    for entry in parsed.entries:
        title = entry.get("title", "") or ""
        # Strict hiring filter: must contain [Hiring]; skip [For Hire] etc.
        # RSS doesn't expose flair, so we rely on title prefix.
        if "[hiring]" not in title.lower():
            continue

        link = entry.get("link", "") or ""
        if not link:
            continue

        # RSS 'summary' is HTML; pull the readable text portion
        summary_html = entry.get("summary", "") or ""
        desc = re.sub(r"<[^>]+>", " ", summary_html)
        desc = re.sub(r"\s+", " ", desc).strip()[:3000]

        author = (entry.get("author") or "").lstrip("/u/")
        # Title sometimes encodes [HIRING] / [HIRING][Remote] etc.; keep raw.

        published = entry.get("published_parsed")
        if published:
            posted_at = datetime(*published[:6], tzinfo=timezone.utc)
        else:
            posted_at = None

        budget_match = re.search(r"\$(\d+)(?:/hr|/hour|/h\b)", title + " " + desc, re.IGNORECASE)
        budget = float(budget_match.group(1)) if budget_match else None

        out.append(
            Opportunity(
                id=hashlib.md5(link.encode()).hexdigest(),
                url=link,
                source=f"reddit_r_{subreddit}",
                channel="C",
                title=title,
                company_or_client=author,
                description=f"{title}\n\n{desc}",
                stack=[],
                is_remote=True,
                contact_method="reddit_dm",
                budget=budget,
                posted_at=posted_at,
            )
        )
    return out


def fetch() -> list[Opportunity]:
    out: list[Opportunity] = []
    seen: set[str] = set()
    for sr in SUBREDDITS:
        for opp in _parse_one(sr):
            if opp.url in seen:
                continue
            seen.add(opp.url)
            out.append(opp)
    return out
