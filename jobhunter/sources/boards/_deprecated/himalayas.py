"""Himalayas.app — JSON API, Channel A."""
from __future__ import annotations
import hashlib
from datetime import datetime

from core.fetcher import fetch_json
from core.models import Opportunity

URL = "https://himalayas.app/jobs/api?limit=100"


def fetch() -> list[Opportunity]:
    data = fetch_json(URL)
    if not data:
        return []
    jobs = data if isinstance(data, list) else data.get("jobs", [])
    out = []
    for j in jobs:
        url = j.get("applicationLink") or j.get("url", "")
        if not url:
            continue
        skills = [s.get("title", "").lower() for s in j.get("skills", []) if isinstance(s, dict)]
        posted_raw = j.get("createdAt") or j.get("publishedAt", "")
        try:
            posted_at = datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
        except Exception:
            posted_at = None

        raw_sen = j.get("seniority", "")
        seniority = raw_sen[0] if isinstance(raw_sen, list) else str(raw_sen) if raw_sen else ""

        opp = Opportunity(
            id=hashlib.md5(url.encode()).hexdigest(),
            url=url,
            source="himalayas",
            channel="A",
            title=j.get("title", ""),
            company_or_client=j.get("company", {}).get("name", "") if isinstance(j.get("company"), dict) else "",
            description=j.get("description", ""),
            stack=skills,
            is_remote=True,
            seniority=seniority,
            posted_at=posted_at,
        )
        out.append(opp)
    return out
