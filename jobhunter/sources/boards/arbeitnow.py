"""Arbeitnow — JSON API, Channel A (EU remote, Pakistan-friendly)."""
from __future__ import annotations
import hashlib
from datetime import datetime

from core.fetcher import fetch_json
from core.models import Opportunity

URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch() -> list[Opportunity]:
    data = fetch_json(URL)
    if not data:
        return []
    jobs = data.get("data", [])
    out = []
    for j in jobs:
        url = j.get("url", "")
        if not url:
            continue
        tags = j.get("tags", []) or []
        posted_raw = j.get("created_at", "")
        try:
            posted_at = datetime.fromisoformat(str(posted_raw))
        except Exception:
            posted_at = None

        opp = Opportunity(
            id=hashlib.md5(url.encode()).hexdigest(),
            url=url,
            source="arbeitnow",
            channel="A",
            title=j.get("title", ""),
            company_or_client=j.get("company_name", ""),
            description=j.get("description", ""),
            stack=[t.lower() for t in tags if isinstance(t, str)],
            is_remote=bool(j.get("remote")),
            location_restriction=j.get("location", ""),
            posted_at=posted_at,
        )
        out.append(opp)
    return out
