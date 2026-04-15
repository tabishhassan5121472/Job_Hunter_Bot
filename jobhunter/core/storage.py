"""SQLite storage and dedup."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from datetime import datetime

from .models import Opportunity

DB_PATH = Path(__file__).parent.parent / "jobs.db"


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id TEXT PRIMARY KEY,
            url TEXT UNIQUE,
            source TEXT,
            channel TEXT,
            title TEXT,
            company_or_client TEXT,
            description TEXT,
            stack TEXT,
            is_remote INTEGER,
            seniority TEXT,
            budget REAL,
            currency TEXT,
            posted_at TEXT,
            score REAL,
            score_breakdown TEXT,
            llm_fit_note TEXT,
            pitch_draft TEXT,
            cv_variant TEXT,
            status TEXT DEFAULT 'new',
            seen_at TEXT
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_score ON opportunities(score DESC)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_status ON opportunities(status)")


def is_seen(url: str) -> bool:
    with _conn() as c:
        row = c.execute("SELECT 1 FROM opportunities WHERE url=?", (url,)).fetchone()
        return row is not None


def save(opp: Opportunity):
    with _conn() as c:
        c.execute("""
        INSERT OR IGNORE INTO opportunities
        (id, url, source, channel, title, company_or_client, description,
         stack, is_remote, seniority, budget, currency, posted_at,
         score, score_breakdown, llm_fit_note, pitch_draft, cv_variant, status, seen_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            opp.id, opp.url, opp.source, opp.channel,
            opp.title, opp.company_or_client, opp.description[:4000],
            json.dumps(opp.stack), int(opp.is_remote), opp.seniority,
            opp.budget, opp.currency,
            opp.posted_at.isoformat() if opp.posted_at else None,
            opp.score, opp.score_breakdown.model_dump_json(),
            opp.llm_fit_note, opp.pitch_draft, opp.cv_variant,
            opp.status, opp.seen_at.isoformat(),
        ))


def top_new(limit: int = 20) -> list[Opportunity]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM opportunities WHERE status='new' ORDER BY score DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [_row_to_opp(r) for r in rows]


def _row_to_opp(r) -> Opportunity:
    d = dict(r)
    d["stack"] = json.loads(d["stack"] or "[]")
    d["score_breakdown"] = json.loads(d["score_breakdown"] or "{}")
    d["is_remote"] = bool(d["is_remote"])
    if d["posted_at"]:
        d["posted_at"] = datetime.fromisoformat(d["posted_at"])
    if d["seen_at"]:
        d["seen_at"] = datetime.fromisoformat(d["seen_at"])
    return Opportunity(**d)
