"""
Scoring utilities for calculating consistency scores.
All scoring is deterministic — no AI involvement in score calculation.
"""

from app.models.issue import Issue, IssueSeverity


def get_score_label(score: float) -> str:
    """Assign a human-readable label to a numeric score."""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Needs Improvement"
    else:
        return "Poor"


def calculate_category_score(
    total_properties_checked: int,
    consistent_properties: int,
    issues: list[Issue],
) -> float:
    """
    Calculate a category score (0-100) based on consistency ratio and issue severity.

    The base score is the ratio of consistent properties.
    Penalties are applied per issue based on severity:
      - HIGH: -8 points
      - MEDIUM: -4 points
      - LOW: -2 points

    Score is clamped to [0, 100].
    """
    if total_properties_checked == 0:
        return 100.0  # No properties to check = no issues

    # Base score from consistency ratio
    base_score = (consistent_properties / total_properties_checked) * 100.0

    # Apply severity penalties
    penalty = 0.0
    for issue in issues:
        if issue.severity == IssueSeverity.HIGH:
            penalty += 8.0
        elif issue.severity == IssueSeverity.MEDIUM:
            penalty += 4.0
        elif issue.severity == IssueSeverity.LOW:
            penalty += 2.0

    final_score = base_score - penalty
    return max(0.0, min(100.0, round(final_score, 1)))


def calculate_overall_score(
    category_scores: dict[str, float],
    weights: dict[str, float],
) -> float:
    """
    Calculate overall score as a weighted average of available category scores.
    Only includes categories that have scores (non-None).
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for category, score in category_scores.items():
        weight = weights.get(category, 0.1)  # Default weight if not specified
        weighted_sum += score * weight
        total_weight += weight

    if total_weight == 0:
        return 100.0

    overall = weighted_sum / total_weight
    return max(0.0, min(100.0, round(overall, 1)))


def determine_severity(
    difference: float,
    tolerance_ignore: float,
    tolerance_issue: float,
) -> IssueSeverity | None:
    """
    Determine issue severity based on the difference magnitude.

    Returns None if the difference is within the ignore threshold.
    """
    if difference <= tolerance_ignore:
        return None  # Within tolerance, no issue
    elif difference <= tolerance_issue:
        return IssueSeverity.LOW
    elif difference <= tolerance_issue * 1.5:
        return IssueSeverity.MEDIUM
    else:
        return IssueSeverity.HIGH
