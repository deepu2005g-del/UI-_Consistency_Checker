"""
UI Extractor orchestrator service.
Coordinates between vision service and playwright service to produce unified ExtractedUI.
"""

import logging
from typing import Optional

from app.models.ui import ExtractedUI, PageUIData
from app.services.vision_service import extract_ui_from_multiple_screenshots
from app.services.playwright_service import analyze_url

logger = logging.getLogger(__name__)


async def extract_from_screenshots(
    screenshots: list[dict[str, str]],
) -> ExtractedUI:
    """
    Extract UI data from uploaded screenshots using vision AI.

    Args:
        screenshots: List of dicts with 'filepath' and 'page_name' keys.

    Returns:
        ExtractedUI with data from all screenshots.
    """
    logger.info(f"Extracting UI from {len(screenshots)} screenshots")

    pages = await extract_ui_from_multiple_screenshots(screenshots)

    return ExtractedUI(
        pages=pages,
        source_type="screenshots",
    )


async def extract_from_url(
    url: str,
    analysis_id: str,
    on_progress: Optional[callable] = None,
) -> ExtractedUI:
    """
    Extract UI data from a website URL using Playwright + DOM inspection.

    Args:
        url: Website URL to analyze.
        analysis_id: Unique analysis identifier.
        on_progress: Optional progress callback.

    Returns:
        ExtractedUI with data from all analyzed pages/viewports.
    """
    logger.info(f"Extracting UI from URL: {url}")

    pages = await analyze_url(
        url=url,
        analysis_id=analysis_id,
        on_progress=on_progress,
    )

    return ExtractedUI(
        pages=pages,
        source_type="url",
        source_url=url,
    )
