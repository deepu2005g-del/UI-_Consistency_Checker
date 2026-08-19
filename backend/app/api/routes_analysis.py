"""
API routes for UI consistency analysis.
Handles screenshot upload and URL analysis endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.models.analysis import (
    AnalysisResult,
    AnalysisResponse,
    AnalysisStatus,
    AnalysisInputType,
    URLAnalysisRequest,
)
from app.models.ui import ExtractedUI
from app.services import screenshot_service, report_service
from app.services.ui_extractor import extract_from_screenshots, extract_from_url
from app.services.consistency_engine import analyze_consistency
from app.services.ai_service import generate_recommendations
from app.utils.validators import validate_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


async def _run_screenshot_analysis(analysis_id: str, screenshots: list[dict]) -> None:
    """Background task: run the full screenshot analysis pipeline."""
    try:
        # Step 1: Extract UI
        report_service.update_progress(
            analysis_id, AnalysisStatus.EXTRACTING,
            "Extracting UI properties", 20.0,
            "Analyzing screenshots with AI vision..."
        )

        extracted_ui = await extract_from_screenshots(screenshots)

        if not extracted_ui.pages:
            report_service.fail_analysis(
                analysis_id,
                "Failed to extract UI data from any of the uploaded screenshots. "
                "Please ensure the screenshots show clear webpage UI."
            )
            return

        # Step 2: Consistency analysis
        report_service.update_progress(
            analysis_id, AnalysisStatus.COMPARING,
            "Comparing pages", 50.0,
            "Running consistency analysis across pages..."
        )

        category_scores, issues, overall_score = analyze_consistency(extracted_ui)

        # Step 3: AI recommendations
        report_service.update_progress(
            analysis_id, AnalysisStatus.AI_ANALYSIS,
            "Running AI analysis", 70.0,
            "Generating AI-powered recommendations..."
        )

        recommendations = await generate_recommendations(issues)

        # Step 4: Generate report
        report_service.update_progress(
            analysis_id, AnalysisStatus.GENERATING,
            "Preparing report", 90.0,
            "Assembling final report..."
        )

        pages_analyzed = [p.page_name for p in extracted_ui.pages]

        report_service.complete_analysis(
            analysis_id=analysis_id,
            category_scores=category_scores,
            issues=issues,
            recommendations=recommendations,
            overall_score=overall_score,
            pages_analyzed=pages_analyzed,
        )

        logger.info(f"Screenshot analysis {analysis_id} completed. Score: {overall_score}")

    except Exception as e:
        logger.error(f"Screenshot analysis {analysis_id} failed: {e}", exc_info=True)
        report_service.fail_analysis(analysis_id, f"Analysis failed: {str(e)}")


async def _run_url_analysis(analysis_id: str, url: str) -> None:
    """Background task: run the full URL analysis pipeline."""
    try:
        # Step 1: Process website
        report_service.update_progress(
            analysis_id, AnalysisStatus.PROCESSING,
            "Processing website", 10.0,
            f"Opening {url} with browser automation..."
        )

        async def on_progress(message: str):
            report_service.update_progress(
                analysis_id, AnalysisStatus.EXTRACTING,
                "Extracting UI properties", 30.0,
                message
            )

        extracted_ui = await extract_from_url(
            url=url,
            analysis_id=analysis_id,
            on_progress=on_progress,
        )

        if not extracted_ui.pages:
            report_service.fail_analysis(
                analysis_id,
                "Failed to extract UI data from the website. "
                "Make sure the URL is publicly accessible and the website loads correctly."
            )
            return

        # Step 2: Consistency analysis
        report_service.update_progress(
            analysis_id, AnalysisStatus.COMPARING,
            "Comparing pages", 55.0,
            "Running consistency analysis across pages and viewports..."
        )

        category_scores, issues, overall_score = analyze_consistency(extracted_ui)

        # Step 3: AI recommendations
        report_service.update_progress(
            analysis_id, AnalysisStatus.AI_ANALYSIS,
            "Running AI analysis", 75.0,
            "Generating AI-powered recommendations..."
        )

        recommendations = await generate_recommendations(issues)

        # Step 4: Generate report
        report_service.update_progress(
            analysis_id, AnalysisStatus.GENERATING,
            "Preparing report", 90.0,
            "Assembling final report..."
        )

        pages_analyzed = list(set(p.page_name for p in extracted_ui.pages))

        # Extract project name from URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        project_name = parsed.hostname or "Web Application"

        report_service.complete_analysis(
            analysis_id=analysis_id,
            category_scores=category_scores,
            issues=issues,
            recommendations=recommendations,
            overall_score=overall_score,
            pages_analyzed=pages_analyzed,
            project_name=project_name,
        )

        logger.info(f"URL analysis {analysis_id} completed. Score: {overall_score}")

    except Exception as e:
        logger.error(f"URL analysis {analysis_id} failed: {e}", exc_info=True)
        report_service.fail_analysis(analysis_id, f"Analysis failed: {str(e)}")


@router.post("/analyze/screenshots")
async def analyze_screenshots(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
):
    """
    Analyze multiple webpage screenshots for UI consistency.

    Upload at least 2 screenshots (PNG, JPG, JPEG, WEBP, max 10MB each).
    The analysis runs asynchronously — poll the returned analysis_id for results.
    """
    # Validate screenshots
    is_valid, error = await screenshot_service.validate_screenshots(files)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Create analysis
    analysis_id = report_service.create_analysis(AnalysisInputType.SCREENSHOTS)

    # Save files
    report_service.update_progress(
        analysis_id, AnalysisStatus.UPLOADING,
        "Uploading screenshots", 5.0,
        "Saving uploaded files..."
    )

    saved_files = await screenshot_service.save_screenshots(files, analysis_id)

    # Start background analysis
    background_tasks.add_task(_run_screenshot_analysis, analysis_id, saved_files)

    return AnalysisResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus.UPLOADING,
        progress=report_service.get_analysis(analysis_id).progress,
    )


@router.post("/analyze/url")
async def analyze_url_endpoint(
    background_tasks: BackgroundTasks,
    request: URLAnalysisRequest,
):
    """
    Analyze a publicly accessible website URL for UI consistency.

    The system uses Playwright to capture the website at multiple viewports
    and extract CSS properties from the DOM.
    """
    # Validate URL
    is_valid, error = validate_url(request.url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Create analysis
    analysis_id = report_service.create_analysis(
        AnalysisInputType.URL,
        source_url=request.url,
    )

    # Start background analysis
    background_tasks.add_task(_run_url_analysis, analysis_id, request.url)

    return AnalysisResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus.PENDING,
        progress=report_service.get_analysis(analysis_id).progress,
    )


@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """
    Get the current status and results of an analysis.
    Poll this endpoint to track analysis progress.
    """
    result = report_service.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    return AnalysisResponse(
        analysis_id=analysis_id,
        status=result.status,
        progress=result.progress,
        result=result if result.status == AnalysisStatus.COMPLETE else None,
    )


@router.get("/analysis/{analysis_id}/report")
async def get_report(analysis_id: str):
    """
    Get the complete analysis report.
    Only available after analysis is complete.
    """
    result = report_service.get_analysis(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    if result.status == AnalysisStatus.FAILED:
        raise HTTPException(
            status_code=422,
            detail=result.error_message or "Analysis failed."
        )

    if result.status != AnalysisStatus.COMPLETE:
        raise HTTPException(
            status_code=202,
            detail="Analysis is still in progress. Please try again later."
        )

    return result
