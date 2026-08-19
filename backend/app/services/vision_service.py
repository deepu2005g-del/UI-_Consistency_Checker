"""
Vision AI service for extracting structured UI data from screenshots.
Uses Google Gemini Vision to analyze screenshots and return structured JSON.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from PIL import Image

from app.config import settings
from app.models.ui import PageUIData, ViewportInfo
from app.utils.validators import extract_json_from_text

logger = logging.getLogger(__name__)

# The structured extraction prompt for vision AI
EXTRACTION_PROMPT = """You are a UI analysis expert. Analyze this webpage screenshot and extract STRUCTURED information about the UI elements.

Return a JSON object with the following structure. Only include elements you can actually detect in the screenshot. Use pixel values where possible. For colors use hex format (#RRGGBB).

{
  "page_name": "detected page name or description",
  "viewport": {
    "width": estimated_width,
    "height": estimated_height,
    "label": "desktop" or "tablet" or "mobile"
  },
  "buttons": [
    {
      "label": "button text",
      "type": "primary|secondary|outline|ghost",
      "background_color": "#hex",
      "text_color": "#hex",
      "font_size": number_in_px,
      "font_weight": 400|500|600|700,
      "padding_vertical": number_in_px,
      "padding_horizontal": number_in_px,
      "border_radius": number_in_px,
      "border_color": "#hex or null",
      "box_shadow": "css shadow string or null"
    }
  ],
  "headings": [
    {
      "level": 1-6,
      "text": "heading text",
      "font_size": number_in_px,
      "font_weight": 400-900,
      "font_family": "font name or null",
      "color": "#hex",
      "margin_bottom": number_in_px
    }
  ],
  "body_text": [
    {
      "font_size": number_in_px,
      "font_weight": 400,
      "font_family": "font name or null",
      "line_height": number_in_px,
      "color": "#hex"
    }
  ],
  "cards": [
    {
      "border_radius": number_in_px,
      "padding": number_in_px,
      "border_color": "#hex or null",
      "box_shadow": "css shadow or null",
      "background_color": "#hex"
    }
  ],
  "navbar": {
    "height": number_in_px,
    "background_color": "#hex",
    "text_color": "#hex",
    "font_size": number_in_px,
    "font_weight": 400-700,
    "logo_position": "left|center|right",
    "menu_gap": number_in_px,
    "position": "fixed|sticky|static",
    "box_shadow": "css shadow or null"
  },
  "form_inputs": [
    {
      "type": "text|email|password|select|textarea",
      "height": number_in_px,
      "padding_vertical": number_in_px,
      "padding_horizontal": number_in_px,
      "border_radius": number_in_px,
      "border_color": "#hex",
      "background_color": "#hex",
      "font_size": number_in_px,
      "label_font_size": number_in_px,
      "label_font_weight": 400-700,
      "field_gap": number_in_px
    }
  ],
  "colors": {
    "primary_colors": ["#hex"],
    "secondary_colors": ["#hex"],
    "background_colors": ["#hex"],
    "text_colors": ["#hex"],
    "border_colors": ["#hex"],
    "button_colors": ["#hex"],
    "accent_colors": ["#hex"]
  },
  "spacing": [
    {
      "element_type": "section|container|card-group",
      "padding_top": number_in_px,
      "padding_bottom": number_in_px,
      "gap": number_in_px
    }
  ]
}

IMPORTANT RULES:
1. Return ONLY valid JSON, no markdown, no explanations.
2. Use pixel values (numbers only, no "px" suffix).
3. Use hex colors (#RRGGBB format).
4. Only include elements you can actually see in the screenshot.
5. Estimate values as accurately as possible.
6. If you cannot detect a property, use null.
7. Do NOT invent elements that are not visible."""


def _configure_genai() -> genai.Client:
    """Configure the Google Generative AI client."""
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY is not configured. "
            "Please set it in your .env file."
        )
    return genai.Client(api_key=settings.GEMINI_API_KEY)


async def extract_ui_from_screenshot(
    image_path: str,
    page_name: str = "Unknown Page",
    retry_count: int = 2,
) -> Optional[PageUIData]:
    """
    Extract structured UI data from a screenshot using Gemini Vision.

    Args:
        image_path: Path to the screenshot image.
        page_name: Human-readable name for the page.
        retry_count: Number of retries for invalid JSON responses.

    Returns:
        PageUIData object or None if extraction fails.
    """
    client = _configure_genai()

    try:
        img = Image.open(image_path)
    except Exception as e:
        logger.error(f"Failed to open image {image_path}: {e}")
        return None

    for attempt in range(retry_count + 1):
        try:
            prompt = EXTRACTION_PROMPT
            if attempt > 0:
                prompt += "\n\nPREVIOUS ATTEMPT RETURNED INVALID JSON. Return ONLY a valid JSON object, nothing else."

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt, img],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json" if attempt > 0 else None,
                    temperature=0.1,
                ),
            )

            response_text = response.text.strip()
            logger.debug(f"Vision AI response (attempt {attempt + 1}): {response_text[:500]}")

            # Parse JSON
            data = extract_json_from_text(response_text)
            if data is None:
                logger.warning(f"Failed to parse JSON from vision AI (attempt {attempt + 1})")
                continue

            if isinstance(data, list):
                data = data[0] if data else {}

            # Override page name with user-provided name
            data["page_name"] = page_name

            # Parse into Pydantic model (with validation)
            page_data = PageUIData.model_validate(data)
            return page_data

        except Exception as e:
            logger.error(f"Vision AI extraction failed (attempt {attempt + 1}): {e}")
            if attempt == retry_count:
                return None

    return None


async def extract_ui_from_multiple_screenshots(
    screenshots: list[dict[str, str]],
) -> list[PageUIData]:
    """
    Extract UI data from multiple screenshots.

    Args:
        screenshots: List of dicts with 'filepath' and 'page_name' keys.

    Returns:
        List of PageUIData objects.
    """
    results = []

    for screenshot in screenshots:
        filepath = screenshot["filepath"]
        page_name = screenshot.get("page_name", "Unknown Page")

        logger.info(f"Extracting UI from screenshot: {page_name} ({filepath})")

        page_data = await extract_ui_from_screenshot(
            image_path=filepath,
            page_name=page_name,
        )

        if page_data:
            results.append(page_data)
        else:
            logger.warning(f"Failed to extract UI from {page_name}, skipping.")

    return results
