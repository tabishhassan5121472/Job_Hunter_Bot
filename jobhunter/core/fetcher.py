"""HTTP fetcher with retry and ETag caching."""
from __future__ import annotations
import hashlib
import json
import time
from pathlib import Path
from typing import Optional

import httpx

CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "JobHunterBot/1.0 (personal use; contact: tabishhassan01998@gmail.com)",
}


def _cache_path(url: str) -> Path:
    key = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{key}.json"


def fetch_text(url: str, timeout: int = 20, retries: int = 3) -> Optional[str]:
    """Fetch URL text with ETag-based caching and retry."""
    cache_file = _cache_path(url)
    etag = None
    last_modified = None

    if cache_file.exists():
        cached = json.loads(cache_file.read_text())
        etag = cached.get("etag")
        last_modified = cached.get("last_modified")

    headers = dict(HEADERS)
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    for attempt in range(retries):
        try:
            r = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
            if r.status_code == 304:
                return json.loads(cache_file.read_text()).get("body", "")
            r.raise_for_status()
            body = r.text
            cache_file.write_text(json.dumps({
                "etag": r.headers.get("etag"),
                "last_modified": r.headers.get("last-modified"),
                "body": body,
            }))
            return body
        except Exception as e:
            if attempt == retries - 1:
                print(f"[fetcher] FAIL {url}: {e}")
                return None
            time.sleep(2 ** attempt)
    return None


def fetch_json(url: str, **kwargs) -> Optional[dict | list]:
    text = fetch_text(url, **kwargs)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
