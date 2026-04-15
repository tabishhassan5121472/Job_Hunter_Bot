"""HN 'Freelancer? Seeking Freelancer?' monthly thread — Channel C."""
from __future__ import annotations
import hashlib
import re
from datetime import datetime, timezone

from core.fetcher import fetch_json
from core.models import Opportunity

HN_SEARCH = "https://hn.algolia.com/api/v1/search?query=seeking+freelancer&tags=story&numericFilters=created_at_i%3E{since}"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
HN_ITEM_SEARCH = "https://hn.algolia.com/api/v1/search?tags=comment,story_{story_id}&query=react&hitsPerPage=100"


def _get_monthly_thread_id() -> int | None:
    """Find the latest 'Ask HN: Freelancer? Seeking freelancer?' thread."""
    import time
    thirty_days_ago = int(time.time()) - 30 * 86400
    url = f"https://hn.algolia.com/api/v1/search?query=Freelancer+Seeking+freelancer&tags=story&numericFilters=created_at_i>{thirty_days_ago}"
    data = fetch_json(url)
    if not data:
        return None
    for hit in data.get("hits", []):
        title = hit.get("title", "").lower()
        if "freelancer" in title and "seeking" in title:
            return hit.get("objectID")
    return None


def fetch() -> list[Opportunity]:
    thread_id = _get_monthly_thread_id()
    if not thread_id:
        return []

    data = fetch_json(HN_ITEM_SEARCH.format(story_id=thread_id))
    if not data:
        return []

    out = []
    for hit in data.get("hits", []):
        text = hit.get("comment_text") or hit.get("story_text") or ""
        text_clean = re.sub(r"<[^>]+>", " ", text)
        title_line = text_clean.strip()[:100].replace("\n", " ")

        # Only "SEEKING WORK" style comments, not "SEEKING FREELANCER"
        if "seeking work" not in text_clean.lower() and "available" not in text_clean.lower():
            continue

        obj_id = hit.get("objectID", "")
        url = f"https://news.ycombinator.com/item?id={obj_id}"

        created = hit.get("created_at_i")
        posted_at = datetime.fromtimestamp(created, tz=timezone.utc) if created else None

        opp = Opportunity(
            id=hashlib.md5(url.encode()).hexdigest(),
            url=url,
            source="hn_freelancer",
            channel="C",
            title=f"HN Freelancer Thread: {title_line}",
            company_or_client=hit.get("author", ""),
            description=text_clean[:3000],
            stack=[],
            is_remote=True,
            contact_method="hn_reply",
            posted_at=posted_at,
        )
        out.append(opp)
    return out
