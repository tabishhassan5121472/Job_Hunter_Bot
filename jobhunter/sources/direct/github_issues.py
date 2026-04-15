"""GitHub 'help wanted' issues in React/TS repos — Channel C/D."""
from __future__ import annotations
import hashlib
from datetime import datetime

from core.fetcher import fetch_json
from core.models import Opportunity

QUERIES = [
    "label:\"help+wanted\"+language:TypeScript+state:open",
    "label:\"help+wanted\"+language:JavaScript+react+state:open",
    "label:\"good+first+issue\"+language:TypeScript+react+state:open",
]
BASE = "https://api.github.com/search/issues?q={q}&sort=created&order=desc&per_page=30"


def fetch() -> list[Opportunity]:
    out = []
    seen: set[str] = set()

    for q in QUERIES:
        data = fetch_json(BASE.format(q=q))
        if not data or "items" not in data:
            continue
        for issue in data["items"]:
            url = issue.get("html_url", "")
            if not url or url in seen:
                continue
            seen.add(url)

            repo = issue.get("repository_url", "").replace("https://api.github.com/repos/", "")
            title = issue.get("title", "")
            body = (issue.get("body") or "")[:2000]
            labels = [l["name"].lower() for l in issue.get("labels", [])]
            created = issue.get("created_at", "")
            try:
                posted_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except Exception:
                posted_at = None

            opp = Opportunity(
                id=hashlib.md5(url.encode()).hexdigest(),
                url=url,
                source="github_issues",
                channel="D",
                title=f"[OSS] {repo}: {title}",
                company_or_client=repo.split("/")[0] if "/" in repo else repo,
                description=body,
                stack=labels,
                is_remote=True,
                contact_method="github_pr",
                posted_at=posted_at,
            )
            out.append(opp)
    return out
