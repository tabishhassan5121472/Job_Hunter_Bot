"""GitHub 'help wanted' issues in React/TS repos — Channel C/D.

Filters out bot-generated noise (daily repo-status reports, dependabot,
automated workflow output) so the feed only shows real human asks for help.
"""
from __future__ import annotations
import hashlib
import re
from datetime import datetime

from core.fetcher import fetch_json
from core.models import Opportunity

QUERIES = [
    "label:\"help+wanted\"+language:TypeScript+state:open",
    "label:\"help+wanted\"+language:JavaScript+react+state:open",
    "label:\"good+first+issue\"+language:TypeScript+react+state:open",
]
BASE = "https://api.github.com/search/issues?q={q}&sort=created&order=desc&per_page=30"

# Label names that signal automated / status-report issues (case-insensitive)
NOISE_LABELS = {
    "daily-status", "repo-status", "weekly-status", "monthly-status",
    "automated", "auto-generated", "bot", "report",
    "dependencies", "dependabot",  # dependency bumps aren't a fit either
}

# Title prefixes that scream "bot-generated" — usually bracket-wrapped tags
NOISE_TITLE_PREFIX_RE = re.compile(
    r"^\s*\[(repo-status|daily-status|status|report|dependabot|bot|auto)\]",
    re.IGNORECASE,
)


def _is_bot_noise(issue: dict, labels: list[str], title: str) -> bool:
    # 1. Author is a GitHub bot account (e.g. github-actions[bot], dependabot[bot])
    user = issue.get("user") or {}
    login = (user.get("login") or "").lower()
    if login.endswith("[bot]") or user.get("type") == "Bot":
        return True
    # 2. Any label matches the noise list
    if any(l in NOISE_LABELS for l in labels):
        return True
    # 3. Title prefix gives it away
    if NOISE_TITLE_PREFIX_RE.match(title or ""):
        return True
    return False


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

            title = issue.get("title", "")
            labels = [l["name"].lower() for l in issue.get("labels", [])]
            if _is_bot_noise(issue, labels, title):
                continue

            repo = issue.get("repository_url", "").replace("https://api.github.com/repos/", "")
            body = (issue.get("body") or "")[:2000]
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
