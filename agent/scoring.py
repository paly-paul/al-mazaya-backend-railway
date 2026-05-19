"""Lead scoring logic for Mazaya FM."""
from config import settings

TIMELINE_SCORES = {
    "within_1_month": 25,
    "1_3_months": 20,
    "3_6_months": 10,
    "just_exploring": 5,
}

# Budget bands per tower/clinic size (KD/month)
BUDGET_BANDS = {
    "clinic_iii": {"min": 1200, "max": 3000},
    "clinic_iv": {"min": 900, "max": 2000},
    "small": {"min": 500, "max": 1200},
    "medium": {"min": 1000, "max": 2500},
    "large": {"min": 2000, "max": 5000},
}

# Medical specialties that are high priority for Mazaya
HIGH_PRIORITY_SPECIALTIES = {
    "cardiology", "oncology", "orthopedics", "ophthalmology", "dermatology",
    "radiology", "neurology", "gastroenterology", "urology", "gynecology",
    "pediatrics", "dentistry", "endocrinology", "rheumatology", "nephrology",
}

MEDIUM_PRIORITY_SPECIALTIES = {
    "general_practice", "general practice", "family medicine", "internal medicine",
    "psychiatry", "psychology", "physiotherapy", "nutrition", "audiology",
}


def _parse_budget(budget_range: str) -> float:
    """Extract a numeric mid-point from a budget string like '1000-2000' or '1500 KD'."""
    if not budget_range:
        return 0.0
    import re
    numbers = re.findall(r'\d+(?:\.\d+)?', budget_range.replace(',', ''))
    if not numbers:
        return 0.0
    nums = [float(n) for n in numbers]
    return sum(nums) / len(nums)


def calculate_lead_score(
    specialty: str = None,
    tower_preference: str = None,
    budget_range: str = None,
    timeline: str = None,
    clinic_size: str = None,
) -> dict:
    """
    Calculate lead score 0-100 and return tier.

    Weights:
      specialty_match:    30 pts  (is specialty high/medium priority?)
      budget_fit:         25 pts  (does budget align with expected range?)
      timeline_urgency:   25 pts  (how soon do they need space?)
      tower_availability: 20 pts  (do they have a tower preference = availability signal)
    """
    score = 0
    breakdown = {}

    # 1. Specialty match (0, 15, or 30)
    specialty_lower = (specialty or "").lower().strip()
    if specialty_lower in HIGH_PRIORITY_SPECIALTIES:
        specialty_pts = 30
    elif specialty_lower in MEDIUM_PRIORITY_SPECIALTIES:
        specialty_pts = 15
    elif specialty_lower:
        specialty_pts = 8  # At least some specialty is better than none
    else:
        specialty_pts = 0
    score += specialty_pts
    breakdown["specialty_match"] = specialty_pts

    # 2. Budget fit (0, 12, or 25)
    budget_mid = _parse_budget(budget_range or "")
    budget_pts = 0
    if budget_mid > 0:
        size_key = (clinic_size or "medium").lower()
        band = BUDGET_BANDS.get(size_key, BUDGET_BANDS["medium"])
        if band["min"] <= budget_mid <= band["max"]:
            budget_pts = 25
        elif budget_mid >= band["min"] * 0.8:  # within 20% of lower bound
            budget_pts = 12
        else:
            budget_pts = 5  # Has a budget but doesn't fit well
    score += budget_pts
    breakdown["budget_fit"] = budget_pts

    # 3. Timeline urgency
    timeline_lower = (timeline or "").lower().replace(" ", "_").replace("-", "_")
    timeline_pts = 5  # default
    for key, pts in TIMELINE_SCORES.items():
        if key in timeline_lower:
            timeline_pts = pts
            break
    score += timeline_pts
    breakdown["timeline_urgency"] = timeline_pts

    # 4. Tower availability (0 or 20 — has preference = serious = 20, no preference = 10)
    if tower_preference and tower_preference.lower() not in ("", "unknown", "any"):
        tower_pts = 20
    elif tower_preference:
        tower_pts = 10
    else:
        tower_pts = 0
    score += tower_pts
    breakdown["tower_availability"] = tower_pts

    # Cap at 100
    score = min(score, 100)

    tier = (
        "hot" if score >= settings.lead_score_hot_threshold
        else "warm" if score >= settings.lead_score_warm_threshold
        else "cold"
    )

    return {
        "score": round(score, 1),
        "tier": tier,
        "breakdown": breakdown,
    }
