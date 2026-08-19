"""
Report service — assembles final analysis results and manages storage.
Uses in-memory storage by default, with optional MongoDB persistence.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from app.models.analysis import (
    AnalysisResult,
    AnalysisStatus,
    AnalysisProgress,
    AnalysisInputType,
    CategoryScore,
    OverallScore,
)
from app.models.issue import Issue, AIRecommendation, IssueWithRecommendation
from app.utils.scoring import get_score_label

logger = logging.getLogger(__name__)

# In-memory storage (fallback when MongoDB is not configured)
_analysis_store: dict[str, AnalysisResult] = {}


def create_analysis(input_type: AnalysisInputType, source_url: Optional[str] = None) -> str:
    """Create a new analysis entry and return its ID."""
    analysis_id = str(uuid.uuid4())

    result = AnalysisResult(
        analysis_id=analysis_id,
        input_type=input_type,
        source_url=source_url,
        status=AnalysisStatus.PENDING,
        progress=AnalysisProgress(
            status=AnalysisStatus.PENDING,
            current_step="Initializing",
            progress_percent=0.0,
            message="Analysis created, waiting to start.",
        ),
    )

    _analysis_store[analysis_id] = result
    return analysis_id


def get_analysis(analysis_id: str) -> Optional[AnalysisResult]:
    """Get an analysis result by ID."""
    return _analysis_store.get(analysis_id)


def update_progress(
    analysis_id: str,
    status: AnalysisStatus,
    step: str,
    progress_percent: float,
    message: str = "",
) -> None:
    """Update the progress of an ongoing analysis."""
    result = _analysis_store.get(analysis_id)
    if result:
        result.status = status
        result.progress = AnalysisProgress(
            status=status,
            current_step=step,
            progress_percent=progress_percent,
            message=message,
        )


def complete_analysis(
    analysis_id: str,
    category_scores: list[CategoryScore],
    issues: list[Issue],
    recommendations: list[AIRecommendation],
    overall_score: float,
    pages_analyzed: list[str],
    project_name: str = "Web Application",
) -> Optional[AnalysisResult]:
    """
    Complete an analysis with final results.
    Assembles the full report.
    """
    result = _analysis_store.get(analysis_id)
    if not result:
        return None

    # Build overall score
    overall = OverallScore(
        score=overall_score,
        label=get_score_label(overall_score),
        total_issues=len(issues),
        high_issues=len([i for i in issues if i.severity.value == "HIGH"]),
        medium_issues=len([i for i in issues if i.severity.value == "MEDIUM"]),
        low_issues=len([i for i in issues if i.severity.value == "LOW"]),
    )

    # Match recommendations to issues
    rec_map = {r.issue_id: r for r in recommendations}
    issues_with_recs = []
    for issue in issues:
        issues_with_recs.append(IssueWithRecommendation(
            issue=issue,
            recommendation=rec_map.get(issue.id),
        ))

    # Update result
    result.status = AnalysisStatus.COMPLETE
    result.progress = AnalysisProgress(
        status=AnalysisStatus.COMPLETE,
        current_step="Complete",
        progress_percent=100.0,
        message="Analysis complete.",
    )
    result.overall_score = overall
    result.category_scores = category_scores
    result.issues = issues
    result.recommendations = recommendations
    result.issues_with_recommendations = issues_with_recs
    result.pages_analyzed = pages_analyzed
    result.project_name = project_name
    result.completed_at = datetime.utcnow()

    return result


def fail_analysis(analysis_id: str, error_message: str) -> None:
    """Mark an analysis as failed."""
    result = _analysis_store.get(analysis_id)
    if result:
        result.status = AnalysisStatus.FAILED
        result.progress = AnalysisProgress(
            status=AnalysisStatus.FAILED,
            current_step="Failed",
            progress_percent=0.0,
            message=error_message,
        )
        result.error_message = error_message
