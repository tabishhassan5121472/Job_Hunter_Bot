"""Workable ATS — public per-company job board API.

Workable exposes a public posting API:
  https://apply.workable.com/api/v3/accounts/<account>/jobs

Companies on Workable are configured in config/ats_companies.yaml with ats: workable.
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
    desc = re.sub(r"<[^>]+>", " ", j.get("description") or "")[:1500]
    loc_obj = j.get("location") or {}
    loc = "Remote"
    if isinstance(loc_obj, dict):
        country = loc_obj.get("country") or ""
        city = loc_obj.get("city") or ""
        loc = ", ".join(filter(None, [city, country])) or "Remote"
    workplace = (j.get("workplace") or "").lower()
    is_remote = workplace == "remote" or bool(j.get("remote"))
    uid = hashlib.md5(f"workable-{c['name']}-{j.get('shortcode', title)}".encode()).hexdigest()
    short = j.get("shortcode") or j.get("id") or ""
    slug = c.get("board_id") or c["name"]
    url = j.get("application_url") or f"https://apply.workable.com/{slug}/j/{short}/"
    return Opportunity(
        id=uid,
        channel="A",
        source=f"ats_workable_{c['name']}",
        title=title,
        company_or_client=c["name"].title(),
        url=url,
        description=desc,
        posted_at=_parse_iso(j.get("published_on") or j.get("created_at")),
        is_remote=is_remote,
    )


def fetch() -> list[Opportunity]:
    cfg = _load_config()
    out: list[Opportunity] = []
    for c in cfg.get("companies", []):
        if c.get("ats") != "workable":
            continue
        slug = c.get("board_id") or c["name"]
        url = f"https://apply.workable.com/api/v3/accounts/{slug}/jobs"
        try:
            r = httpx.get(url, timeout=10, headers={"User-Agent": "jobhunter/2.0"})
            if r.status_code != 200:
                continue
            payload = r.json()
        except Exception:
            continue
        jobs = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(jobs, list):
            continue
        kws = c.get("keywords_must_match") or ["react"]
        for j in jobs:
            blob = (j.get("title", "") or "") + " " + (j.get("description", "") or "")
            if _matches(blob, kws):
                out.append(_to_opportunity(j, c))
        time.sleep(0.3)
    return out
