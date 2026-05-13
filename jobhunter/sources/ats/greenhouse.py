"""Greenhouse ATS — direct job feeds from a curated list of remote-first companies.

Per market research (2026-04-30), this is the highest-quality React source: Stripe, Vercel,
Airbnb alone returned 61 React roles in one probe — more than all the bot's board sources combined.
"""
from __future__ import annotations
import hashlib
import re
import time
from pathlib import Path
from datetime import datetime

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


def _to_opportunity(j: dict, c: dict) -> Opportunity:
    content = re.sub(r"<[^>]+>", " ", j.get("content", "") or "")[:1500]
    title = (j.get("title") or "")[:120]
    loc_name = (j.get("location") or {}).get("name", "Remote")
    uid = hashlib.md5(f"gh-{c['name']}-{j.get('id', title)}".encode()).hexdigest()
    posted = j.get("updated_at") or j.get("created_at") or datetime.now().isoformat()
    return Opportunity(
        id=uid,
        channel="A",
        source=f"ats_greenhouse_{c['name']}",
        title=title,
        company_or_client=c["name"].title(),
        location=loc_name,
        url=j.get("absolute_url", ""),
        description=content,
        posted_at=posted,
        is_remote="remote" in loc_name.lower() or "anywhere" in loc_name.lower(),
    )


def fetch() -> list[Opportunity]:
    cfg = _load_config()
    out: list[Opportunity] = []
    for c in cfg.get("companies", []):
        if c.get("ats") != "greenhouse":
            continue
        url = f"https://boards-api.greenhouse.io/v1/boards/{c['board_id']}/jobs?content=true"
        try:
            r = httpx.get(url, timeout=10, headers={"User-Agent": "jobhunter/2.0"})
            if r.status_code != 200:
                continue
            jobs = r.json().get("jobs", [])
        except Exception:
            continue
        kws = c.get("keywords_must_match") or ["react"]
        for j in jobs:
            blob = (j.get("title", "") or "") + " " + (j.get("content", "") or "")
            if _matches(blob, kws):
                out.append(_to_opportunity(j, c))
        time.sleep(0.4)  # be polite
    return out
