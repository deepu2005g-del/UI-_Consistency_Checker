"""
AI service for generating human-readable explanations and recommendations.
Uses Gemini to interpret detected issues and provide CSS/Tailwind fixes.
This runs AFTER the deterministic consistency analysis.
"""

import json
import logging
from typing import Optional

from google import genai
from google.genai import types

from app.config import settings
from app.models.issue import Issue, AIRecommendation
from app.utils.validators import extract_json_from_text

logger = logging.getLogger(__name__)

RECOMMENDATION_PROMPT = """You are a senior UI/UX consistency expert and CSS specialist.

You have been given a list of detected UI consistency issues found by an automated analysis tool.

For EACH issue, provide:
1. A clear explanation of why this inconsistency matters
2. The visual impact on the user experience
3. A specific recommendation for the consistent value to use
4. A CSS fix snippet
5. A Tailwind CSS equivalent where applicable

CRITICAL RULES:
- Do NOT invent or make up measurements. Use ONLY the values provided in the detected data.
- Base your recommended value on the most common value detected.
- Provide practical, copy-paste-ready CSS fixes.
- Return strict JSON, no markdown, no extra text.

Return a JSON array of objects with this exact structure:
[
  {
    "issue_id": "ISSUE-001",
    "issue_title": "Button radius differs across pages",
    "category": "Buttons",
    "explanation": "Inconsistent button border radius creates visual fragmentation...",
    "visual_impact": "Users perceive the interface as unpolished...",
    "recommendation": "Standardize all primary button border-radius to 8px.",
    "css_fix": ".primary-button {\\n  border-radius: 8px;\\n}",
    "tailwind_fix": "rounded-lg",
    "priority": 2
  }
]

Priority levels:
1 = Critical (affects usability)
2 = Important (affects visual consistency)
3 = Minor (cosmetic improvement)

Here are the detected issues:

"""


def _configure_genai() -> genai.Client:
    """Configure the Google Generative AI client."""
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY is not configured. "
            "Please set it in your .env file."
        )
    return genai.Client(api_key=settings.GEMINI_API_KEY)


async def generate_recommendations(
    issues: list[Issue],
    retry_count: int = 2,
) -> list[AIRecommendation]:
    """
    Generate AI-powered recommendations for detected issues.

    Args:
        issues: List of detected consistency issues.
        retry_count: Number of retries for invalid responses.

    Returns:
        List of AIRecommendation objects.
    """
    if not issues:
        return []

    client = _configure_genai()

    # Format issues for the prompt
    issues_data = []
    for issue in issues:
        issues_data.append({
            "id": issue.id,
            "category": issue.category,
            "title": issue.title,
            "description": issue.description,
            "severity": issue.severity.value,
            "affected_pages": issue.affected_pages,
            "detected_values": issue.detected_values,
            "recommended_standard": issue.recommended_standard,
        })

    prompt = RECOMMENDATION_PROMPT + json.dumps(issues_data, indent=2)

    for attempt in range(retry_count + 1):
        try:
            extra_instruction = ""
            if attempt > 0:
                extra_instruction = "\n\nPREVIOUS ATTEMPT RETURNED INVALID JSON. Return ONLY a valid JSON array, nothing else."

            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt + extra_instruction,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json" if attempt > 0 else None,
                    temperature=0.2,
                    max_output_tokens=4096,
                ),
            )

            response_text = response.text.strip()
            logger.debug(f"AI recommendation response (attempt {attempt + 1}): {response_text[:500]}")

            # Parse JSON
            data = extract_json_from_text(response_text)
            if data is None:
                logger.warning(f"Failed to parse recommendation JSON (attempt {attempt + 1})")
                continue

            # Ensure it's a list
            if isinstance(data, dict):
                data = [data]

            if not isinstance(data, list):
                logger.warning(f"Unexpected response format (attempt {attempt + 1})")
                continue

            # Parse into Pydantic models
            recommendations = []
            for item in data:
                try:
                    rec = AIRecommendation(
                        issue_id=item.get("issue_id", ""),
                        issue_title=item.get("issue_title", ""),
                        category=item.get("category", ""),
                        explanation=item.get("explanation", ""),
                        visual_impact=item.get("visual_impact", ""),
                        recommendation=item.get("recommendation", ""),
                        css_fix=item.get("css_fix"),
                        tailwind_fix=item.get("tailwind_fix"),
                        priority=item.get("priority", 2),
                    )
                    recommendations.append(rec)
                except Exception as e:
                    logger.warning(f"Failed to parse recommendation item: {e}")
                    continue

            if recommendations:
                return recommendations

        except Exception as e:
            logger.error(f"AI recommendation generation failed (attempt {attempt + 1}): {e}")
            if attempt == retry_count:
                # Return fallback recommendations
                return _generate_fallback_recommendations(issues)

    return _generate_fallback_recommendations(issues)


def _generate_fallback_recommendations(issues: list[Issue]) -> list[AIRecommendation]:
    """
    Generate basic fallback recommendations when AI is unavailable.
    These are simple rule-based recommendations without AI explanation depth.
    """
    recommendations = []

    for issue in issues:
        css_fix = None
        tailwind_fix = None
        recommendation = f"Standardize {issue.title.lower()} across all pages."

        # Generate basic CSS fix based on recommended standard
        if issue.recommended_standard:
            if "radius" in issue.title.lower():
                css_fix = f"/* Standardize border-radius */\n.element {{\n  border-radius: {issue.recommended_standard};\n}}"
                try:
                    radius_val = float(issue.recommended_standard.replace("px", ""))
                    if radius_val <= 2:
                        tailwind_fix = "rounded-sm"
                    elif radius_val <= 4:
                        tailwind_fix = "rounded"
                    elif radius_val <= 6:
                        tailwind_fix = "rounded-md"
                    elif radius_val <= 8:
                        tailwind_fix = "rounded-lg"
                    elif radius_val <= 12:
                        tailwind_fix = "rounded-xl"
                    else:
                        tailwind_fix = "rounded-2xl"
                except ValueError:
                    pass
            elif "color" in issue.title.lower():
                css_fix = f"/* Standardize color */\n:root {{\n  --primary-color: {issue.recommended_standard};\n}}"
            elif "size" in issue.title.lower() or "height" in issue.title.lower():
                css_fix = f"/* Standardize size */\n.element {{\n  font-size: {issue.recommended_standard};\n}}"
            elif "padding" in issue.title.lower() or "spacing" in issue.title.lower():
                css_fix = f"/* Standardize spacing */\n.element {{\n  padding: {issue.recommended_standard};\n}}"

        rec = AIRecommendation(
            issue_id=issue.id,
            issue_title=issue.title,
            category=issue.category,
            explanation=f"This inconsistency in {issue.category.lower()} affects the visual cohesion of your application.",
            visual_impact="Users may perceive the interface as unpolished or fragmented when UI elements are inconsistent.",
            recommendation=recommendation,
            css_fix=css_fix,
            tailwind_fix=tailwind_fix,
            priority=1 if issue.severity.value == "HIGH" else (2 if issue.severity.value == "MEDIUM" else 3),
        )
        recommendations.append(rec)

    return recommendations
