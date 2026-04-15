#!/usr/bin/env python3
"""
JobHunter — complete pipeline (Phases 1–6)
Run: python main.py [--draft] [--top N]
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table
from rich.progress import track

from core import storage, scorer
from core.models import Opportunity
from delivery import digest_md

console = Console()

# ── Source registry ────────────────────────────────────────────────────────────
BOARD_SOURCES = [
    ("remotive",       "sources.boards.remotive"),
    ("remoteok",       "sources.boards.remoteok"),
    ("himalayas",      "sources.boards.himalayas"),
    ("arbeitnow",      "sources.boards.arbeitnow"),
    ("jobicy",         "sources.boards.jobicy"),
    ("weworkremotely", "sources.boards.weworkremotely"),
]
FREELANCE_SOURCES = [
    ("freelancer", "sources.freelance.freelancer"),
]
DIRECT_SOURCES = [
    ("reddit",       "sources.direct.reddit_forhire"),
    ("hn_freelance", "sources.direct.hn_freelancer"),
    ("github_oss",   "sources.direct.github_issues"),
]


def _import_fetch(module_path: str):
    import importlib
    return importlib.import_module(module_path)


def run_sources(sources: list, label: str) -> list[Opportunity]:
    all_opps: list[Opportunity] = []
    for name, module_path in track(sources, description=f"[cyan]{label}[/cyan]"):
        try:
            mod = _import_fetch(module_path)
            opps = mod.fetch()
            console.print(f"  [green]{name}[/green]: {len(opps)} raw")
            all_opps.extend(opps)
        except Exception as e:
            console.print(f"  [red]{name}[/red]: {e}")
    return all_opps


def print_table(opportunities: list[Opportunity], title: str = "Top Opportunities"):
    table = Table(title=title, show_lines=True)
    table.add_column("#",      style="dim", width=3)
    table.add_column("Score",  width=6)
    table.add_column("Ch",     width=3)
    table.add_column("Title",  max_width=36)
    table.add_column("Company", max_width=18)
    table.add_column("Source", width=13)
    table.add_column("Note",   max_width=30)

    for i, opp in enumerate(opportunities[:15], 1):
        note = opp.llm_fit_note[:50] if opp.llm_fit_note else ""
        score_color = "green" if opp.score >= 70 else ("yellow" if opp.score >= 50 else "red")
        table.add_row(
            str(i),
            f"[{score_color}]{opp.score:.0f}[/{score_color}]",
            opp.channel,
            opp.title[:36],
            opp.company_or_client[:18],
            opp.source,
            note,
        )
    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="JobHunter")
    parser.add_argument("--draft", action="store_true",
                        help="Generate cover letter drafts for top opportunities (requires ANTHROPIC_API_KEY)")
    parser.add_argument("--top", type=int, default=20,
                        help="Number of top opportunities to show/draft (default: 20)")
    parser.add_argument("--no-llm", action="store_true",
                        help="Skip LLM reranking even if API key is set")
    args = parser.parse_args()

    storage.init_db()
    console.rule("[bold blue]JobHunter — Full Pipeline[/bold blue]")

    # ── 1. Fetch all sources ───────────────────────────────────────────────────
    raw: list[Opportunity] = []
    raw += run_sources(BOARD_SOURCES,     "Channel A — Remote Boards")
    raw += run_sources(FREELANCE_SOURCES, "Channel B — Freelance")
    raw += run_sources(DIRECT_SOURCES,    "Channel C/D — Direct & OSS")
    console.print(f"\n[bold]Total raw:[/bold] {len(raw)}")

    # ── 2. Deduplicate + score ─────────────────────────────────────────────────
    new_opps: list[Opportunity] = []
    for opp in raw:
        if storage.is_seen(opp.url):
            continue
        opp = scorer.score(opp)
        if opp.score > 0:
            storage.save(opp)
            new_opps.append(opp)

    console.print(f"[bold]New & scored:[/bold] {len(new_opps)}")

    if not new_opps:
        console.print("[yellow]No new opportunities found.[/yellow]")
        return

    # ── 3. Sort, take top N ────────────────────────────────────────────────────
    top = sorted(new_opps, key=lambda o: o.score, reverse=True)[:args.top]

    # ── 4. LLM rerank (optional) ───────────────────────────────────────────────
    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if has_api_key and not args.no_llm:
        console.print(f"\n[bold cyan]LLM reranking top {len(top)} via Claude Haiku...[/bold cyan]")
        try:
            from core.llm_rerank import rerank
            top = rerank(top)
            top = sorted(top, key=lambda o: o.score, reverse=True)
            # Persist updated scores
            for opp in top:
                with storage._conn() as c:
                    c.execute(
                        "UPDATE opportunities SET score=?, llm_fit_note=? WHERE id=?",
                        (opp.score, opp.llm_fit_note, opp.id)
                    )
            console.print("[green]Reranking complete.[/green]")
        except Exception as e:
            console.print(f"[red]LLM rerank failed: {e}[/red]")
    elif not has_api_key:
        console.print("[dim]Tip: set ANTHROPIC_API_KEY to enable LLM reranking + cover letters[/dim]")

    # ── 5. Generate cover letter drafts ───────────────────────────────────────
    if args.draft and has_api_key:
        console.print(f"\n[bold cyan]Drafting cover letters for top {min(5, len(top))}...[/bold cyan]")
        try:
            from pitch.cover_letter import generate
            for opp in top[:5]:
                console.print(f"  Drafting: {opp.title[:50]}...")
                draft = generate(opp)
                opp.pitch_draft = draft
                with storage._conn() as c:
                    c.execute(
                        "UPDATE opportunities SET pitch_draft=?, status='drafted' WHERE id=?",
                        (draft, opp.id)
                    )
            console.print("[green]Drafts saved to DB. Use: python tracker/applied.py pitch <id>[/green]")
        except Exception as e:
            console.print(f"[red]Draft generation failed: {e}[/red]")

    # ── 6. Telegram alerts for urgent Channel-C hits ───────────────────────────
    telegram_enabled = bool(os.environ.get("TELEGRAM_BOT_TOKEN"))
    if telegram_enabled:
        urgent = [o for o in top if o.channel in ("B", "C") and o.score >= 65 and "URGENT" in o.llm_fit_note]
        if urgent:
            try:
                from delivery.telegram_bot import send_alert
                for opp in urgent[:3]:
                    send_alert(opp)
                    console.print(f"  [green]Telegram alert sent:[/green] {opp.title[:50]}")
            except Exception as e:
                console.print(f"  [red]Telegram error: {e}[/red]")

    # ── 7. Print table + save digest ──────────────────────────────────────────
    print_table(top, f"Top {len(top)} Opportunities")

    report_path = digest_md.generate(top)
    console.print(f"\n[bold green]Digest:[/bold green] {report_path}")

    # Telegram summary
    if telegram_enabled:
        try:
            from delivery.telegram_bot import send_digest_summary
            send_digest_summary(len(new_opps), top[0].score if top else 0, str(report_path))
        except Exception:
            pass

    console.print("\n[dim]Track applications: python tracker/applied.py --help[/dim]")
    console.print("[dim]Draft cover letter: python main.py --draft[/dim]")


if __name__ == "__main__":
    main()
