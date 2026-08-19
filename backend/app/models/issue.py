"""
Pydantic models for issues detected by the consistency engine.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class IssueSeverity(str, Enum):
    """Issue severity levels."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Issue(BaseModel):
    """A detected UI consistency issue."""
    id: str  # e.g., "ISSUE-001"
    category: str  # Buttons, Typography, Spacing, Colors, Cards, Navbar, Forms, Responsive
    title: str
    description: str
    severity: IssueSeverity
    affected_pages: list[str] = Field(default_factory=list)
    detected_values: dict[str, str] = Field(default_factory=dict)  # page -> value
    recommended_standard: Optional[str] = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class AIRecommendation(BaseModel):
    """AI-generated recommendation for a detected issue."""
    issue_id: str
    issue_title: str
    category: str
    explanation: str  # Why this issue matters
    visual_impact: str  # How it affects the user
    recommendation: str  # What to do
    css_fix: Optional[str] = None
    tailwind_fix: Optional[str] = None
    priority: int = Field(default=2, ge=1, le=3)  # 1=highest


class IssueWithRecommendation(BaseModel):
    """Combined issue and its AI recommendation for the results."""
    issue: Issue
    recommendation: Optional[AIRecommendation] = None
