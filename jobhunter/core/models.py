"""Unified Opportunity schema."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    react_stack_match: float = 0.0
    frontend_signal: float = 0.0
    remote_friendly: float = 0.0
    seniority_fit: float = 0.0
    recency: float = 0.0
    pay_signal: float = 0.0
    accessibility_bonus: float = 0.0
    startup_signal: float = 0.0
    penalties: float = 0.0
    total: float = 0.0


class Opportunity(BaseModel):
    id: str
    url: str
    source: str
    channel: str  # A / B / C / D

    title: str
    company_or_client: str = ""
    description: str = ""
    stack: list[str] = Field(default_factory=list)

    is_remote: bool = False
    timezone: str = ""
    location_restriction: str = ""
    seniority: str = ""
    budget: Optional[float] = None
    currency: str = "USD"
    posted_at: Optional[datetime] = None

    contact_method: str = ""

    score: float = 0.0
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    llm_fit_note: str = ""

    pitch_draft: str = ""
    cv_variant: str = "cv_frontend"

    status: str = "new"  # new | drafted | sent | replied | rejected | interview | offer
    seen_at: datetime = Field(default_factory=datetime.utcnow)
