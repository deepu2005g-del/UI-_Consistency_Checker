"""
Pydantic models for analysis requests, responses, and results.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime

from app.models.issue import Issue, AIRecommendation, IssueWithRecommendation


class AnalysisStatus(str, Enum):
    """Analysis pipeline status."""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    EXTRACTING = "extracting"
    COMPARING = "comparing"
    AI_ANALYSIS = "ai_analysis"
    GENERATING = "generating"
    COMPLETE = "complete"
    FAILED = "failed"


class AnalysisInputType(str, Enum):
    """Type of analysis input."""
    SCREENSHOTS = "screenshots"
    URL = "url"


class CategoryScore(BaseModel):
    """Score for a single analysis category."""
    category: str
    score: float = Field(ge=0.0, le=100.0)
    label: str = ""  # Excellent, Good, Needs Improvement, Poor
    issue_count: int = 0
    details: Optional[str] = None


class OverallScore(BaseModel):
    """Overall UI consistency score."""
    score: float = Field(ge=0.0, le=100.0)
    label: str = ""
    total_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0


class AnalysisProgress(BaseModel):
    """Progress information for an ongoing analysis."""
    status: AnalysisStatus
    current_step: str = ""
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    message: str = ""


class URLAnalysisRequest(BaseModel):
    """Request body for URL analysis."""
    url: str


class AnalysisResult(BaseModel):
    """Complete analysis result."""
    analysis_id: str
    input_type: AnalysisInputType
    source_url: Optional[str] = None
    project_name: str = "Web Application"
    status: AnalysisStatus = AnalysisStatus.PENDING
    progress: AnalysisProgress = Field(
        default_factory=lambda: AnalysisProgress(status=AnalysisStatus.PENDING)
    )

    # Scores
    overall_score: Optional[OverallScore] = None
    category_scores: list[CategoryScore] = Field(default_factory=list)

    # Issues & Recommendations
    issues: list[Issue] = Field(default_factory=list)
    recommendations: list[AIRecommendation] = Field(default_factory=list)
    issues_with_recommendations: list[IssueWithRecommendation] = Field(default_factory=list)

    # Metadata
    pages_analyzed: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class AnalysisResponse(BaseModel):
    """API response for analysis status/results."""
    analysis_id: str
    status: AnalysisStatus
    progress: Optional[AnalysisProgress] = None
    result: Optional[AnalysisResult] = None
