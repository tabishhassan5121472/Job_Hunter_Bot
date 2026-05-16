"""Frontend-weighted scorer."""
from __future__ import annotations
import re
from datetime import datetime, timezone

from .models import Opportunity, ScoreBreakdown

REACT_STACK = {
    "react", "reactjs", "react.js", "typescript", "ts", "tailwind",
    "tailwindcss", "next.js", "nextjs", "redux", "zustand", "material-ui",
    "mui", "framer-motion", "vite", "webpack", "jest", "rtl",
}
FRONTEND_SIGNALS = {
    "frontend", "front-end", "front end", "ui developer", "ux developer",
    "web developer", "javascript", "css", "html", "spa", "pwa",
}
REMOTE_SIGNALS = {
    "remote", "worldwide", "anywhere", "distributed", "fully remote",
    "work from home", "wfh", "remote-first",
}
A11Y_SIGNALS = {"a11y", "wcag", "ada", "accessibility", "aria", "508"}
SENIORITY_GOOD = {"mid", "intermediate", "3-5", "3+", "4+", "5 years", "5+"}
SENIORITY_BAD = {"lead", "principal", "staff", "director", "vp", "10+", "8+"}

REJECT_PATTERNS = [
    r"\bgambling\b", r"\bcasino\b", r"\badult\b",
    r"\bcrypto\b", r"\bblockchain\b",
    r"\bsenior node\b", r"\bnestjs lead\b",
    r"\bbackend engineer\b.*senior",
    r"\bon.site\b", r"\bus citizen\b", r"\beu citizen\b",
    r"\bright to work\b",
]


def _tokens(text: str) -> set[str]:
    text = text.lower()
    # preserve hyphenated and dotted terms
    text = re.sub(r"[^a-z0-9.\-+ ]", " ", text)
    return set(text.split())


def score(opp: Opportunity) -> Opportunity:
    blob = f"{opp.title} {opp.description} {' '.join(opp.stack)}".lower()

    # Hard reject check
    for pat in REJECT_PATTERNS:
        if re.search(pat, blob):
            opp.score = 0.0
            opp.score_breakdown = ScoreBreakdown(total=0.0, penalties=-100.0)
            return opp

    toks = _tokens(blob)
    bd = ScoreBreakdown()

    # React stack match (0–1)
    hits = REACT_STACK & toks
    bd.react_stack_match = min(len(hits) / 4, 1.0)

    # Frontend signal (0–1)
    bd.frontend_signal = 1.0 if FRONTEND_SIGNALS & toks else 0.0

    # Remote friendly (0–1)
    bd.remote_friendly = 1.0 if (REMOTE_SIGNALS & toks or opp.is_remote) else 0.0

    # Seniority fit (0–1)
    if SENIORITY_BAD & toks:
        bd.seniority_fit = 0.2
    elif SENIORITY_GOOD & toks:
        bd.seniority_fit = 1.0
    else:
        bd.seniority_fit = 0.6  # unknown = neutral

    # Recency (0–1) — full if < 7 days
    if opp.posted_at:
        now = datetime.now(timezone.utc)
        posted = opp.posted_at
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)
        age_days = (now - posted).days
        bd.recency = max(0.0, 1.0 - age_days / 14)
    else:
        bd.recency = 0.5

    # Pay signal (0–1)
    bd.pay_signal = 1.0 if (opp.budget or re.search(r"\$\d+|\d+k|\d+/hr", blob)) else 0.0

    # Accessibility bonus (0–1)
    bd.accessibility_bonus = 1.0 if A11Y_SIGNALS & toks else 0.0

    # Weighted total
    w = dict(
        react_stack_match=0.40,
        frontend_signal=0.15,
        remote_friendly=0.15,
        seniority_fit=0.10,
        recency=0.10,
        pay_signal=0.05,
        accessibility_bonus=0.05,
    )
    bd.total = sum(getattr(bd, k) * v for k, v in w.items())
    bd.total = round(bd.total * 100, 1)  # 0–100

    opp.score = bd.total
    opp.score_breakdown = bd

    # CV variant selection: full-time / Channel A roles get the employer-led
    # CV framing; freelance / direct / OSS channels stay with cv_frontend
    # which is positioned around independent shipping. The cover-letter
    # generator picks the matching file at draft time.
    opp.cv_variant = "cv_employed" if opp.channel == "A" else "cv_frontend"
    return opp
