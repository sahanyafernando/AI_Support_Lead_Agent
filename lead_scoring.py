from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class LeadScore:
    score: int
    status: str
    reasons: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_lead_score(
    company_size: int | None = None,
    budget_usd: float | None = None,
    timeline_days: int | None = None,
    decision_maker: bool | None = None,
) -> LeadScore:
    """Deterministic, auditable BANT-like score. Max = 100."""
    score = 0
    reasons: list[str] = []

    if company_size is not None:
        if company_size >= 200:
            score += 30
            reasons.append("Company size 200+ (+30)")
        elif company_size >= 51:
            score += 25
            reasons.append("Company size 51-199 (+25)")
        elif company_size >= 11:
            score += 15
            reasons.append("Company size 11-50 (+15)")
        else:
            score += 5
            reasons.append("Company size 1-10 (+5)")

    if budget_usd is not None:
        if budget_usd >= 10_000:
            score += 30
            reasons.append("Budget $10k+ (+30)")
        elif budget_usd >= 1_000:
            score += 20
            reasons.append("Budget $1k-$9,999 (+20)")
        elif budget_usd > 0:
            score += 5
            reasons.append("Budget below $1k (+5)")

    if timeline_days is not None:
        if timeline_days <= 30:
            score += 25
            reasons.append("Timeline within 30 days (+25)")
        elif timeline_days <= 90:
            score += 15
            reasons.append("Timeline within 90 days (+15)")
        else:
            score += 5
            reasons.append("Timeline beyond 90 days (+5)")

    if decision_maker is True:
        score += 15
        reasons.append("Decision maker (+15)")
    elif decision_maker is False:
        reasons.append("Not the decision maker (+0)")

    if score >= 60:
        status = "HOT"
    elif score >= 35:
        status = "WARM"
    else:
        status = "COLD"

    return LeadScore(score=min(score, 100), status=status, reasons=reasons)
