"""Markdown digest generator."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path

from core.models import Opportunity

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def generate(opportunities: list[Opportunity], run_id: str | None = None) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    run_id = run_id or datetime.now().strftime("%H%M")
    path = REPORTS_DIR / f"{today}-{run_id}.md"

    lines = [
        f"# JobHunter Digest — {today}",
        f"*{len(opportunities)} opportunities · sorted by score*",
        "",
    ]

    channel_labels = {"A": "Remote Job Boards", "B": "Freelance / Gig", "C": "Direct Clients", "D": "OSS / Collab"}

    by_channel: dict[str, list[Opportunity]] = {}
    for opp in opportunities:
        by_channel.setdefault(opp.channel, []).append(opp)

    for ch in sorted(by_channel.keys()):
        label = channel_labels.get(ch, ch)
        opps = sorted(by_channel[ch], key=lambda o: o.score, reverse=True)
        lines.append(f"## Channel {ch} — {label}")
        lines.append("")
        for i, opp in enumerate(opps, 1):
            posted = opp.posted_at.strftime("%b %d") if opp.posted_at else "unknown"
            score_bar = "█" * int(opp.score / 10) + "░" * (10 - int(opp.score / 10))
            lines += [
                f"### {i}. [{opp.title}]({opp.url})",
                f"**{opp.company_or_client or 'Unknown'}** · `{opp.source}` · posted {posted}",
                f"**Score**: {opp.score:.0f}/100 `{score_bar}`",
                "",
            ]
            if opp.stack:
                lines.append(f"**Stack**: {', '.join(opp.stack[:8])}")
            if opp.description:
                snippet = opp.description.replace("\n", " ").strip()[:300]
                lines.append(f"> {snippet}...")
            if opp.llm_fit_note:
                lines.append(f"\n**AI note**: {opp.llm_fit_note}")
            lines.append("")

    path.write_text("\n".join(lines))
    return path
