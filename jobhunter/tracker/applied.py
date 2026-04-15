"""Application tracker — CLI for updating opportunity status."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
import core.storage as storage
from core.models import Opportunity

console = Console()

VALID_STATUSES = ["new", "drafted", "sent", "replied", "rejected", "interview", "offer"]


def list_opportunities(status_filter: str | None = None, limit: int = 30):
    with storage._conn() as c:
        if status_filter:
            rows = c.execute(
                "SELECT * FROM opportunities WHERE status=? ORDER BY score DESC LIMIT ?",
                (status_filter, limit)
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM opportunities ORDER BY score DESC LIMIT ?",
                (limit,)
            ).fetchall()

    table = Table(title=f"Opportunities [{status_filter or 'all'}]", show_lines=True)
    table.add_column("ID", style="dim", width=8)
    table.add_column("Score", width=6)
    table.add_column("Status", width=10)
    table.add_column("Title", max_width=40)
    table.add_column("Company", max_width=20)
    table.add_column("Source", width=12)
    table.add_column("URL", max_width=40, overflow="fold")

    for r in rows:
        status_color = {
            "new": "white", "drafted": "cyan", "sent": "blue",
            "replied": "yellow", "rejected": "red",
            "interview": "green", "offer": "bold green"
        }.get(r["status"], "white")
        table.add_row(
            r["id"][:8],
            f"{r['score']:.0f}",
            f"[{status_color}]{r['status']}[/{status_color}]",
            r["title"],
            r["company_or_client"],
            r["source"],
            r["url"],
        )
    console.print(table)


def update_status(opp_id_prefix: str, new_status: str):
    if new_status not in VALID_STATUSES:
        console.print(f"[red]Invalid status. Choose: {', '.join(VALID_STATUSES)}[/red]")
        return
    with storage._conn() as c:
        result = c.execute(
            "UPDATE opportunities SET status=? WHERE id LIKE ?",
            (new_status, f"{opp_id_prefix}%")
        )
        if result.rowcount == 0:
            console.print(f"[red]No opportunity found with id starting: {opp_id_prefix}[/red]")
        else:
            console.print(f"[green]Updated {result.rowcount} opportunity → {new_status}[/green]")


def show_pitch(opp_id_prefix: str):
    with storage._conn() as c:
        row = c.execute(
            "SELECT * FROM opportunities WHERE id LIKE ?",
            (f"{opp_id_prefix}%",)
        ).fetchone()
    if not row:
        console.print(f"[red]Not found: {opp_id_prefix}[/red]")
        return
    console.print(f"\n[bold]{row['title']}[/bold] — {row['company_or_client']}")
    console.print(f"[dim]{row['url']}[/dim]\n")
    console.print(f"[yellow]Score:[/yellow] {row['score']:.0f}")
    if row["llm_fit_note"]:
        console.print(f"[yellow]AI Note:[/yellow] {row['llm_fit_note']}\n")
    if row["pitch_draft"]:
        console.print("[bold cyan]── Pitch Draft ──[/bold cyan]")
        console.print(row["pitch_draft"])
    else:
        console.print("[dim]No pitch draft yet. Run main.py --draft <id>[/dim]")


def stats():
    with storage._conn() as c:
        total = c.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
        by_status = c.execute(
            "SELECT status, COUNT(*) as n FROM opportunities GROUP BY status ORDER BY n DESC"
        ).fetchall()
        top_sources = c.execute(
            "SELECT source, COUNT(*) as n FROM opportunities GROUP BY source ORDER BY n DESC LIMIT 5"
        ).fetchall()

    console.print(f"\n[bold]Total tracked:[/bold] {total}")
    table = Table(title="By Status")
    table.add_column("Status"); table.add_column("Count")
    for r in by_status:
        table.add_row(r["status"], str(r["n"]))
    console.print(table)

    table2 = Table(title="Top Sources")
    table2.add_column("Source"); table2.add_column("Count")
    for r in top_sources:
        table2.add_row(r["source"], str(r["n"]))
    console.print(table2)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JobHunter Tracker")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("stats", help="Show pipeline stats")

    ls = sub.add_parser("list", help="List opportunities")
    ls.add_argument("--status", default=None, help="Filter by status")
    ls.add_argument("--limit", type=int, default=30)

    up = sub.add_parser("update", help="Update status")
    up.add_argument("id", help="Opportunity ID prefix (first 8 chars)")
    up.add_argument("status", choices=VALID_STATUSES)

    pit = sub.add_parser("pitch", help="Show pitch draft for an opportunity")
    pit.add_argument("id", help="Opportunity ID prefix")

    args = parser.parse_args()
    storage.init_db()

    if args.cmd == "stats":
        stats()
    elif args.cmd == "list":
        list_opportunities(args.status, args.limit)
    elif args.cmd == "update":
        update_status(args.id, args.status)
    elif args.cmd == "pitch":
        show_pitch(args.id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
