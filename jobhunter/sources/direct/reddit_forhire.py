"""Reddit r/forhire + r/remotejs — Channel C (direct clients)."""
from __future__ import annotations
import hashlib
import re
from datetime import datetime, timezone

from core.fetcher import fetch_json
from core.models import Opportunity

SUBREDDITS = [
    ("forhire",  "hiring"),
    ("remotejs", "hiring"),
    ("reactjs",  "hiring"),
]


def fetch() -> list[Opportunity]:
    out = []
    seen: set[str] = set()

    for subreddit, flair_filter in SUBREDDITS:
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=50&t=week"
        data = fetch_json(url)
        if not data:
            continue

        posts = data.get("data", {}).get("children", [])
        for post in posts:
            p = post.get("data", {})
            title = p.get("title", "")
            flair = (p.get("link_flair_text") or "").strip().lower()

            # Strict hiring filter: title must say [Hiring] OR flair must equal "hiring"
            # (avoids surfacing "[For Hire]" posts as opportunities)
            title_has_hiring = "[hiring]" in title.lower()
            flair_is_hiring = flair == "hiring"
            if not (title_has_hiring or flair_is_hiring):
                continue

            permalink = p.get("permalink", "")
            if not permalink:
                continue
            full_url = f"https://www.reddit.com{permalink}"
            if full_url in seen:
                continue
            seen.add(full_url)

            desc = p.get("selftext", "")[:3000]
            created = p.get("created_utc")
            posted_at = datetime.fromtimestamp(created, tz=timezone.utc) if created else None

            # Extract budget hint
            budget_match = re.search(r"\$(\d+)(?:/hr|/hour|/h\b)", desc, re.IGNORECASE)
            budget = float(budget_match.group(1)) if budget_match else None

            opp = Opportunity(
                id=hashlib.md5(full_url.encode()).hexdigest(),
                url=full_url,
                source=f"reddit_r_{subreddit}",
                channel="C",
                title=title,
                company_or_client=p.get("author", ""),
                description=f"{title}\n\n{desc}",
                stack=[],
                is_remote=True,
                contact_method="reddit_dm",
                budget=budget,
                posted_at=posted_at,
            )
            out.append(opp)

    return out
