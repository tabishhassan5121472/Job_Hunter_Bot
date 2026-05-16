"""RemoteOK — JSON API, Channel A."""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone

from core.fetcher import fetch_json
from core.models import Opportunity

URL = "https://remoteok.com/api"


def fetch() -> list[Opportunity]:
    data = fetch_json(URL)
    if not data or not isinstance(data, list):
        return []
    out = []
    for j in data:
        if not isinstance(j, dict) or not j.get("url"):
            continue
        url = j["url"]
        if not url.startswith("http"):
            url = f"https://remoteok.com{url}"
        tags = j.get("tags", []) or []
        epoch = j.get("epoch")
        posted_at = datetime.fromtimestamp(epoch, tz=timezone.utc) if epoch else None

        opp = Opportunity(
            id=hashlib.md5(url.encode()).hexdigest(),
            url=url,
            source="remoteok",
            channel="A",
            title=j.get("position", ""),
            company_or_client=j.get("company", ""),
            description=j.get("description", ""),
            stack=[t.lower() for t in tags if isinstance(t, str)],
            is_remote=True,
            posted_at=posted_at,
        )
        out.append(opp)
    return out
