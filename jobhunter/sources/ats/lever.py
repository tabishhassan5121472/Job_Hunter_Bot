"""Lever ATS — public per-company job feeds.

Lever exposes a free JSON API per company at:
  https://api.lever.co/v0/postings/<company>?mode=json

Companies that use Lever are configured in config/ats_companies.yaml under
ats: lever. Maintained list as of 2026: brex, lattice, mercury, ramp,
plaid, kraken, eventbrite, mux, opendoor, netflix.
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


def _to_opportunity(j: dict, c: dict) -> Opportunity:
    title = (j.get("text") or "")[:120]
    desc = re.sub(r"<[^>]+>", " ", j.get("descriptionPlain") or j.get("description") or "")[:1500]
    cats = j.get("categories") or {}
    loc = cats.get("location") or "Remote"
    work_type = (cats.get("commitment") or "").lower()
    posted_ms = j.get("createdAt")
    if isinstance(posted_ms, (int, float)) and posted_ms > 0:
        posted_at = datetime.fromtimestamp(posted_ms / 1000, tz=timezone.utc)
    else:
        posted_at = None
    uid = hashlib.md5(f"lever-{c['name']}-{j.get('id', title)}".encode()).hexdigest()
    return Opportunity(
        id=uid,
        channel="A",
        source=f"ats_lever_{c['name']}",
        title=title,
        company_or_client=c["name"].title(),
        url=j.get("hostedUrl") or j.get("applyUrl") or "",
        description=desc,
        posted_at=posted_at,
        is_remote="remote" in (loc or "").lower() or "anywhere" in (loc or "").lower(),
    )


def fetch() -> list[Opportunity]:
    cfg = _load_config()
    out: list[Opportunity] = []
    for c in cfg.get("companies", []):
        if c.get("ats") != "lever":
            continue
        slug = c.get("board_id") or c["name"]
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
        try:
            r = httpx.get(url, timeout=10, headers={"User-Agent": "jobhunter/2.0"})
            if r.status_code != 200:
                continue
            jobs = r.json()
            if not isinstance(jobs, list):
                continue
        except Exception:
            continue
        kws = c.get("keywords_must_match") or ["react"]
        for j in jobs:
            blob = (j.get("text", "") or "") + " " + (j.get("descriptionPlain", "") or j.get("description", "") or "")
            if _matches(blob, kws):
                out.append(_to_opportunity(j, c))
        time.sleep(0.3)
    return out
