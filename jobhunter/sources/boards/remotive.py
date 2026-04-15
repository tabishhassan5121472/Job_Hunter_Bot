"""Remotive.com — JSON API, Channel A."""
from __future__ import annotations
import hashlib
from datetime import datetime

from core.fetcher import fetch_json
from core.models import Opportunity

URL = "https://remotive.com/api/remote-jobs?category=software-dev&limit=100"


def fetch() -> list[Opportunity]:
    data = fetch_json(URL)
    if not data or "jobs" not in data:
        return []
    out = []
    for j in data["jobs"]:
        url = j.get("url", "")
        if not url:
            continue
        desc = j.get("description", "")
        tags = [t.lower() for t in j.get("tags", [])]
        posted_raw = j.get("publication_date", "")
        try:
            posted_at = datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
        except Exception:
            posted_at = None

        opp = Opportunity(
            id=hashlib.md5(url.encode()).hexdigest(),
            url=url,
            source="remotive",
            channel="A",
            title=j.get("job_title", ""),
            company_or_client=j.get("company_name", ""),
            description=desc,
            stack=tags,
            is_remote=True,
            seniority=j.get("job_type", ""),
            posted_at=posted_at,
        )
        out.append(opp)
    return out
