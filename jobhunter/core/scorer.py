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
# Startup signals — used as a positive multiplier; we want startup roles.
STARTUP_SIGNAL_RE = re.compile(
    r"\b("
    r"startup|start-up|early.stage|early.career|"
    r"seed|pre.seed|series\s*a|series\s*b|series\s*c|"
    r"yc|y.combinator|y combinator|techstars|"
    r"founding\s+(?:engineer|developer|frontend|backend|fullstack|full.stack)|"
    r"founding\s+team|"
    r"small\s+team|fast.paced|wear\s+many\s+hats|ship\s+fast|"
    r"product.minded|generalist|0\s*to\s*1|zero\s+to\s+one"
    r")\b",
    re.IGNORECASE,
)
ENTERPRISE_SIGNAL_RE = re.compile(
    r"\b(fortune\s*\d+|enterprise\s+(?:client|customer)|public\s+sector|government\s+agency)\b",
    re.IGNORECASE,
)

REJECT_PATTERNS = [
    # Sectors
    r"\bgambling\b", r"\bcasino\b", r"\badult\b",
    r"\bcrypto\b", r"\bblockchain\b",
    # Seniority overreach
    r"\bsenior node\b", r"\bnestjs lead\b",
    r"\bbackend engineer\b.*senior",
    # Onsite / hybrid hard-blockers
    r"\bon.site\b", r"\bhybrid\b",
    # Country restrictions that block Pakistan-based candidates
    r"\bus citizen", r"\bus citizenship\b", r"\bus only\b", r"\bus.based only\b",
    r"\beu citizen", r"\beu citizenship\b", r"\beu only\b", r"\beu.based only\b",
    r"\buk citizen", r"\buk only\b",
    r"\bcanadian citizen", r"\bcanada only\b",
    r"\baustralian citizen", r"\baustralia only\b",
    r"\bgreen.card\b", r"\bright to work\b", r"\bwork permit\b",
    r"\bus.work.authorization\b", r"\bauthorized to work in the\b",
    r"\bsecurity clearance\b", r"\btop.secret\b",
    # Pakistan-specific blockers (no banking with Israel)
    r"\bisrael.based\b", r"\btel aviv\b",
]

# Positive signal for worldwide-remote jobs (Pakistan-hireable)
WORLDWIDE_SIGNAL_RE = re.compile(
    r"\b("
    r"worldwide|any\s+country|any\s+timezone|"
    r"global\s+team|globally\s+distributed|"
    r"100%\s+remote|fully\s+remote\s+global|remote\s+global|"
    r"deel|remote\.com|wise|payoneer|"
    r"hire\s+(?:internationally|globally|from\s+anywhere)|"
    r"open\s+to\s+(?:applicants|candidates)\s+from\s+anywhere"
    r")\b",
    re.IGNORECASE,
)


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

    # Remote friendly (0–1) — explicit "worldwide" / "any country" / "global"
    # scores 1.0, ordinary "remote" scores 0.6, nothing scores 0.
    if WORLDWIDE_SIGNAL_RE.search(blob):
        bd.remote_friendly = 1.0
    elif REMOTE_SIGNALS & toks or opp.is_remote:
        bd.remote_friendly = 0.6
    else:
        bd.remote_friendly = 0.0

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

    # Startup bonus (0–1) — target startup roles preferentially.
    # 1.0 = clear startup signal; -0.5 = strong enterprise signal (penalty).
    if STARTUP_SIGNAL_RE.search(blob):
        bd.startup_signal = 1.0
    elif ENTERPRISE_SIGNAL_RE.search(blob):
        bd.startup_signal = -0.5
    else:
        bd.startup_signal = 0.0

    # Weighted total. Re-tuned to make startup_signal meaningful (10%) and
    # nudge react_stack_match down from 0.40 → 0.30 since the candidate's
    # profile is broader than just React now.
    w = dict(
        react_stack_match=0.30,
        frontend_signal=0.15,
        remote_friendly=0.15,
        seniority_fit=0.10,
        recency=0.10,
        startup_signal=0.10,
        pay_signal=0.05,
        accessibility_bonus=0.05,
    )
    bd.total = sum(getattr(bd, k) * v for k, v in w.items())
    bd.total = round(bd.total * 100, 1)  # 0–100

    opp.score = bd.total
    opp.score_breakdown = bd

    # CV variant selection by job content. The cover-letter generator loads
    # the matching profile/cv_<variant>.md when drafting.
    #   cv_ai       — AI / LLM / ML / agentic / generative engineer roles
    #   cv_fullstack — full-stack, NestJS, Node backend, microservice work
    #   cv_frontend — pure React / frontend / UI / Web Developer roles (default)
    AI_KW = (
        "ai engineer", "ml engineer", "llm engineer", "ai/ml", "agentic",
        "rag ", "openai", "anthropic", " llm ", "generative ai",
        "machine learning engineer", "applied ai", "ai application",
        "prompt engineer", "ai platform", "langchain", "vector",
    )
    FS_KW = (
        "full-stack", "fullstack", "full stack",
        "nestjs", "node.js", "node js", " node ",
        "backend engineer", "backend developer",
        "microservice", "rest api", "graphql api",
        "software engineer",
    )
    blob_low = blob  # already lowercased above
    if any(k in blob_low for k in AI_KW):
        opp.cv_variant = "cv_ai"
    elif any(k in blob_low for k in FS_KW):
        opp.cv_variant = "cv_fullstack"
    else:
        opp.cv_variant = "cv_frontend"
    return opp
