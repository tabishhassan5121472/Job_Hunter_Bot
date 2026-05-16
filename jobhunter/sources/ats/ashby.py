"""Ashby ATS — public per-company job board API.

Ashby exposes a free JSON API:
  https://api.ashbyhq.com/posting-api/job-board/<company>?includeCompensation=true

Companies on Ashby are configured in config/ats_companies.yaml with ats: ashby.
"""
from __future__ import annotations
import hashlib
import re
import time
from pathlib import Path
from datetime import datetime, timezone

import httpx
import yaml

from core.models import Opportunity

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "ats_companies.yaml"


def _load_config():
    if not CONFIG_PATH.exists():
        return {"companies": []}
    return yaml.safe_load(CONFIG_PATH.read_text()) or {"companies": []}


def _matches(text: str, kws: list[str]) -> bool:
    t = text.lower()
    return any(kw in t for kw in kws)


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _to_opportunity(j: dict, c: dict) -> Opportunity:
    title = (j.get("title") or "")[:120]
    desc = re.sub(r"<[^>]+>", " ", j.get("descriptionHtml") or j.get("descriptionPlain") or "")[:1500]
    loc = j.get("location") or "Remote"
    if isinstance(loc, dict):
        loc = loc.get("locationName") or "Remote"
    uid = hashlib.md5(f"ashby-{c['name']}-{j.get('id', title)}".encode()).hexdigest()
    return Opportunity(
        id=uid,
        channel="A",
        source=f"ats_ashby_{c['name']}",
        title=title,
        company_or_client=c["name"].title(),
        url=j.get("jobUrl") or j.get("applyUrl") or "",
        description=desc,
        posted_at=_parse_iso(j.get("publishedAt") or j.get("updatedAt")),
        is_remote=bool(j.get("isRemote")) or "remote" in str(loc).lower(),
    )


def fetch() -> list[Opportunity]:
    cfg = _load_config()
    out: list[Opportunity] = []
    for c in cfg.get("companies", []):
        if c.get("ats") != "ashby":
            continue
        slug = c.get("board_id") or c["name"]
        url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
        try:
            r = httpx.get(url, timeout=10, headers={"User-Agent": "jobhunter/2.0"})
            if r.status_code != 200:
                continue
            payload = r.json()
        except Exception:
            continue
        jobs = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(jobs, list):
            continue
        kws = c.get("keywords_must_match") or ["react"]
        for j in jobs:
            blob = (j.get("title", "") or "") + " " + (j.get("descriptionPlain", "") or j.get("descriptionHtml", "") or "")
            if _matches(blob, kws):
                out.append(_to_opportunity(j, c))
        time.sleep(0.3)
    return out
