#!/usr/bin/env python3
"""Export top opportunities from jobs.db → My-Portfolio/public/jobs.json for the dashboard."""
from __future__ import annotations
import json
import os
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent / "jobs.db"
DEFAULT_OUT = Path("/Users/Tabish/Documents/cursor-ai/My-Portfolio/public/jobs.json")


def export(out_path: Path = DEFAULT_OUT, limit: int = 200, min_score: int = 50) -> int:
    if not DB.exists():
        print(f"DB not found at {DB}", file=sys.stderr)
        return 0

    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    rows = c.execute(
        """
        SELECT id, url, source, channel, title, company_or_client, description,
               stack, is_remote, seniority, budget, currency, posted_at, score,
               llm_fit_note, status, seen_at
        FROM opportunities
        WHERE score >= ?
        ORDER BY score DESC, seen_at DESC
        LIMIT ?
        """,
        (min_score, limit),
    ).fetchall()
    c.close()

    jobs = []
    for r in rows:
        d = dict(r)
        # Trim long descriptions for fast page load
        if d.get("description"):
            d["description"] = d["description"][:1200]
        # Coerce types
        d["is_remote"] = bool(d.get("is_remote"))
        try:
            d["score"] = int(d.get("score") or 0)
        except (TypeError, ValueError):
            d["score"] = 0
        try:
            d["budget"] = float(d["budget"]) if d.get("budget") is not None else None
        except (TypeError, ValueError):
            d["budget"] = None
        # Parse stack if it's a JSON string
        try:
            if isinstance(d.get("stack"), str) and d["stack"].startswith("["):
                d["stack"] = json.loads(d["stack"])
        except Exception:
            pass
        jobs.append(d)

    payload = {
        "generated_at": rows[0]["seen_at"] if rows else None,
        "total": len(jobs),
        "jobs": jobs,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, default=str))
    print(f"Exported {len(jobs)} jobs → {out_path}")
    return len(jobs)


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    export(out)
