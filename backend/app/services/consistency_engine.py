"""
Consistency engine — the core rule-based analysis module.
Compares extracted UI properties across pages to detect inconsistencies.
All scoring is deterministic. No AI involvement.
"""

import logging
import math
from collections import Counter, defaultdict
from typing import Optional

from app.config import settings
from app.models.ui import PageUIData, ExtractedUI
from app.models.issue import Issue, IssueSeverity
from app.models.analysis import CategoryScore
from app.utils.scoring import (
    calculate_category_score,
    calculate_overall_score,
    determine_severity,
    get_score_label,
)

logger = logging.getLogger(__name__)

# Issue counter for generating unique IDs
_issue_counter = 0


def _next_issue_id() -> str:
    """Generate a sequential issue ID."""
    global _issue_counter
    _issue_counter += 1
    return f"ISSUE-{_issue_counter:03d}"


def _reset_issue_counter() -> None:
    """Reset the issue counter for a new analysis."""
    global _issue_counter
    _issue_counter = 0


def _hex_to_rgb(hex_color: str) -> Optional[tuple[int, int, int]]:
    """Convert hex color to RGB tuple."""
    if not hex_color:
        return None
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        return None
    try:
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def _color_difference(color1: str, color2: str) -> float:
    """
    Calculate approximate color difference (simplified deltaE).
    Returns a float where 0 = identical, higher = more different.
    """
    rgb1 = _hex_to_rgb(color1)
    rgb2 = _hex_to_rgb(color2)
    if not rgb1 or not rgb2:
        return 0.0

    # Euclidean distance in RGB space (simplified)
    return math.sqrt(
        sum((c1 - c2) ** 2 for c1, c2 in zip(rgb1, rgb2))
    )


def _find_most_common(values: list) -> Optional[any]:
    """Find the most common value in a list."""
    if not values:
        return None
    counter = Counter(values)
    return counter.most_common(1)[0][0]


def _numeric_diff(values: list[float]) -> float:
    """Calculate the range (max - min) of numeric values."""
    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return 0.0
    return max(valid) - min(valid)


def analyze_consistency(extracted_ui: ExtractedUI) -> tuple[
    list[CategoryScore],
    list[Issue],
    float,
]:
    """
    Run the full consistency analysis across all extracted pages.

    Returns:
        Tuple of (category_scores, issues, overall_score)
    """
    _reset_issue_counter()

    pages = extracted_ui.pages
    if not pages:
        return [], [], 100.0

    all_issues: list[Issue] = []

    # Run category analyses
    button_score, button_issues = _analyze_buttons(pages)
    typography_score, typography_issues = _analyze_typography(pages)
    spacing_score, spacing_issues = _analyze_spacing(pages)
    colors_score, colors_issues = _analyze_colors(pages)
    cards_score, cards_issues = _analyze_cards(pages)
    navbar_score, navbar_issues = _analyze_navbar(pages)
    forms_score, forms_issues = _analyze_forms(pages)
    responsive_score, responsive_issues = _analyze_responsive(pages)

    all_issues.extend(button_issues)
    all_issues.extend(typography_issues)
    all_issues.extend(spacing_issues)
    all_issues.extend(colors_issues)
    all_issues.extend(cards_issues)
    all_issues.extend(navbar_issues)
    all_issues.extend(forms_issues)
    all_issues.extend(responsive_issues)

    # Build category scores
    category_scores = []
    score_map = {}

    categories = [
        ("buttons", "Buttons", button_score, button_issues),
        ("typography", "Typography", typography_score, typography_issues),
        ("spacing", "Spacing", spacing_score, spacing_issues),
        ("colors", "Colors", colors_score, colors_issues),
        ("cards", "Cards", cards_score, cards_issues),
        ("navbar", "Navbar", navbar_score, navbar_issues),
        ("forms", "Forms", forms_score, forms_issues),
        ("responsive", "Responsive", responsive_score, responsive_issues),
    ]

    for key, name, score, issues in categories:
        cat_score = CategoryScore(
            category=name,
            score=score,
            label=get_score_label(score),
            issue_count=len(issues),
        )
        category_scores.append(cat_score)
        score_map[key] = score

    # Calculate overall score
    overall_score = calculate_overall_score(score_map, settings.SCORE_WEIGHTS)

    return category_scores, all_issues, overall_score


def _analyze_buttons(pages: list[PageUIData]) -> tuple[float, list[Issue]]:
    """Analyze button consistency across pages."""
    issues = []
    total_checks = 0
    consistent_checks = 0

    # Collect button properties per page (use only desktop viewport or all)
    page_buttons = {}
    for page in pages:
        if page.buttons:
            page_buttons[page.page_name] = page.buttons

    if len(page_buttons) < 2:
        return 100.0, []

    # Compare border radius
    radius_values = {}
    for page_name, buttons in page_buttons.items():
        radii = [b.border_radius for b in buttons if b.border_radius is not None]
        if radii:
            radius_values[page_name] = round(sum(radii) / len(radii), 1)

    if len(radius_values) >= 2:
        total_checks += 1
        unique_radii = set(radius_values.values())
        diff = _numeric_diff(list(radius_values.values()))
        severity = determine_severity(diff, settings.RADIUS_TOLERANCE_IGNORE, settings.RADIUS_TOLERANCE_ISSUE)
        if severity:
            most_common = _find_most_common(list(radius_values.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Buttons",
                title="Button border radius differs across pages",
                description=f"Button border radius varies from {min(radius_values.values())}px to {max(radius_values.values())}px across pages.",
                severity=severity,
                affected_pages=[p for p, v in radius_values.items() if v != most_common],
                detected_values={p: f"{v}px" for p, v in radius_values.items()},
                recommended_standard=f"{most_common}px",
                confidence=0.9,
            ))
        else:
            consistent_checks += 1

    # Compare background colors
    bg_colors = {}
    for page_name, buttons in page_buttons.items():
        colors = [b.background_color for b in buttons if b.background_color]
        if colors:
            bg_colors[page_name] = colors[0]  # Use first/primary button color

    if len(bg_colors) >= 2:
        total_checks += 1
        unique_colors = set(bg_colors.values())
        if len(unique_colors) > 1:
            # Check if colors are actually different enough
            color_list = list(bg_colors.values())
            max_diff = max(
                _color_difference(color_list[i], color_list[j])
                for i in range(len(color_list))
                for j in range(i + 1, len(color_list))
            )
            severity = determine_severity(max_diff, settings.COLOR_TOLERANCE_IGNORE, settings.COLOR_TOLERANCE_ISSUE)
            if severity:
                most_common = _find_most_common(list(bg_colors.values()))
                issues.append(Issue(
                    id=_next_issue_id(),
                    category="Buttons",
                    title="Button background colors are inconsistent",
                    description="Primary button colors differ across pages.",
                    severity=severity,
                    affected_pages=[p for p, v in bg_colors.items() if v != most_common],
                    detected_values=bg_colors,
                    recommended_standard=most_common,
                    confidence=0.85,
                ))
            else:
                consistent_checks += 1
        else:
            consistent_checks += 1

    # Compare font sizes
    font_sizes = {}
    for page_name, buttons in page_buttons.items():
        sizes = [b.font_size for b in buttons if b.font_size is not None]
        if sizes:
            font_sizes[page_name] = round(sum(sizes) / len(sizes), 1)

    if len(font_sizes) >= 2:
        total_checks += 1
        diff = _numeric_diff(list(font_sizes.values()))
        severity = determine_severity(diff, settings.SIZE_TOLERANCE_IGNORE, settings.SIZE_TOLERANCE_ISSUE)
        if severity:
            most_common = _find_most_common(list(font_sizes.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Buttons",
                title="Button font sizes are inconsistent",
                description=f"Button text size varies from {min(font_sizes.values())}px to {max(font_sizes.values())}px.",
                severity=severity,
                affected_pages=[p for p, v in font_sizes.items() if v != most_common],
                detected_values={p: f"{v}px" for p, v in font_sizes.items()},
                recommended_standard=f"{most_common}px",
                confidence=0.85,
            ))
        else:
            consistent_checks += 1

    # Compare padding
    paddings = {}
    for page_name, buttons in page_buttons.items():
        pads = [b.padding_vertical for b in buttons if b.padding_vertical is not None]
        if pads:
            paddings[page_name] = round(sum(pads) / len(pads), 1)

    if len(paddings) >= 2:
        total_checks += 1
        diff = _numeric_diff(list(paddings.values()))
        severity = determine_severity(diff, settings.SPACING_TOLERANCE_IGNORE, settings.SPACING_TOLERANCE_ISSUE)
        if severity:
            most_common = _find_most_common(list(paddings.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Buttons",
                title="Button padding differs across pages",
                description=f"Button vertical padding varies across pages.",
                severity=severity,
                affected_pages=[p for p, v in paddings.items() if v != most_common],
                detected_values={p: f"{v}px" for p, v in paddings.items()},
                recommended_standard=f"{most_common}px",
                confidence=0.8,
            ))
        else:
            consistent_checks += 1

    score = calculate_category_score(max(total_checks, 1), consistent_checks, issues)
    return score, issues


def _analyze_typography(pages: list[PageUIData]) -> tuple[float, list[Issue]]:
    """Analyze typography consistency across pages."""
    issues = []
    total_checks = 0
    consistent_checks = 0

    # Compare heading sizes by level
    for level in range(1, 4):  # H1, H2, H3
        heading_sizes = {}
        for page in pages:
            level_headings = [h for h in page.headings if h.level == level and h.font_size]
            if level_headings:
                heading_sizes[page.page_name] = level_headings[0].font_size

        if len(heading_sizes) >= 2:
            total_checks += 1
            diff = _numeric_diff(list(heading_sizes.values()))
            severity = determine_severity(diff, settings.SIZE_TOLERANCE_IGNORE, settings.SIZE_TOLERANCE_ISSUE)
            if severity:
                most_common = _find_most_common(list(heading_sizes.values()))
                issues.append(Issue(
                    id=_next_issue_id(),
                    category="Typography",
                    title=f"H{level} heading sizes are inconsistent",
                    description=f"H{level} heading font size varies from {min(heading_sizes.values())}px to {max(heading_sizes.values())}px.",
                    severity=severity,
                    affected_pages=[p for p, v in heading_sizes.items() if v != most_common],
                    detected_values={p: f"{v}px" for p, v in heading_sizes.items()},
                    recommended_standard=f"{most_common}px",
                    confidence=0.9,
                ))
            else:
                consistent_checks += 1

    # Compare heading font weights
    for level in range(1, 4):
        weights = {}
        for page in pages:
            level_headings = [h for h in page.headings if h.level == level and h.font_weight]
            if level_headings:
                weights[page.page_name] = level_headings[0].font_weight

        if len(weights) >= 2:
            total_checks += 1
            unique = set(weights.values())
            if len(unique) > 1:
                most_common = _find_most_common(list(weights.values()))
                issues.append(Issue(
                    id=_next_issue_id(),
                    category="Typography",
                    title=f"H{level} font weight varies across pages",
                    description=f"H{level} heading uses different font weights.",
                    severity=IssueSeverity.LOW,
                    affected_pages=[p for p, v in weights.items() if v != most_common],
                    detected_values={p: str(v) for p, v in weights.items()},
                    recommended_standard=str(most_common),
                    confidence=0.8,
                ))
            else:
                consistent_checks += 1

    # Compare body text sizes
    body_sizes = {}
    for page in pages:
        if page.body_text:
            sizes = [t.font_size for t in page.body_text if t.font_size]
            if sizes:
                body_sizes[page.page_name] = round(sum(sizes) / len(sizes), 1)

    if len(body_sizes) >= 2:
        total_checks += 1
        diff = _numeric_diff(list(body_sizes.values()))
        severity = determine_severity(diff, settings.SIZE_TOLERANCE_IGNORE, settings.SIZE_TOLERANCE_ISSUE)
        if severity:
            most_common = _find_most_common(list(body_sizes.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Typography",
                title="Body text sizes differ across pages",
                description=f"Body text font size varies from {min(body_sizes.values())}px to {max(body_sizes.values())}px.",
                severity=severity,
                affected_pages=[p for p, v in body_sizes.items() if v != most_common],
                detected_values={p: f"{v}px" for p, v in body_sizes.items()},
                recommended_standard=f"{most_common}px",
                confidence=0.85,
            ))
        else:
            consistent_checks += 1

    # Compare heading colors
    heading_colors = {}
    for page in pages:
        h_colors = [h.color for h in page.headings if h.color]
        if h_colors:
            heading_colors[page.page_name] = h_colors[0]

    if len(heading_colors) >= 2:
        total_checks += 1
        unique = set(heading_colors.values())
        if len(unique) > 1:
            color_list = list(heading_colors.values())
            max_diff = max(
                _color_difference(color_list[i], color_list[j])
                for i in range(len(color_list))
                for j in range(i + 1, len(color_list))
            )
            severity = determine_severity(max_diff, settings.COLOR_TOLERANCE_IGNORE, settings.COLOR_TOLERANCE_ISSUE)
            if severity:
                most_common = _find_most_common(list(heading_colors.values()))
                issues.append(Issue(
                    id=_next_issue_id(),
                    category="Typography",
                    title="Heading colors are inconsistent",
                    description="Heading text colors differ across pages.",
                    severity=severity,
                    affected_pages=[p for p, v in heading_colors.items() if v != most_common],
                    detected_values=heading_colors,
                    recommended_standard=most_common,
                    confidence=0.8,
                ))
            else:
                consistent_checks += 1
        else:
            consistent_checks += 1

    score = calculate_category_score(max(total_checks, 1), consistent_checks, issues)
    return score, issues


def _analyze_spacing(pages: list[PageUIData]) -> tuple[float, list[Issue]]:
    """Analyze spacing consistency across pages."""
    issues = []
    total_checks = 0
    consistent_checks = 0

    # Compare section padding
    section_paddings = {}
    for page in pages:
        sections = [s for s in page.spacing if s.element_type == "section"]
        if sections:
            pads = [s.padding_top for s in sections if s.padding_top is not None]
            if pads:
                section_paddings[page.page_name] = round(sum(pads) / len(pads), 1)

    if len(section_paddings) >= 2:
        total_checks += 1
        diff = _numeric_diff(list(section_paddings.values()))
        severity = determine_severity(diff, settings.SPACING_TOLERANCE_IGNORE, settings.SPACING_TOLERANCE_ISSUE)
        if severity:
            most_common = _find_most_common(list(section_paddings.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Spacing",
                title="Section padding differs across pages",
                description=f"Section padding varies from {min(section_paddings.values())}px to {max(section_paddings.values())}px.",
                severity=severity,
                affected_pages=[p for p, v in section_paddings.items() if v != most_common],
                detected_values={p: f"{v}px" for p, v in section_paddings.items()},
                recommended_standard=f"{most_common}px",
                confidence=0.8,
            ))
        else:
            consistent_checks += 1

    # Compare container gaps
    gaps = {}
    for page in pages:
        page_gaps = [s.gap for s in page.spacing if s.gap is not None]
        if page_gaps:
            gaps[page.page_name] = round(sum(page_gaps) / len(page_gaps), 1)

    if len(gaps) >= 2:
        total_checks += 1
        diff = _numeric_diff(list(gaps.values()))
        severity = determine_severity(diff, settings.SPACING_TOLERANCE_IGNORE, settings.SPACING_TOLERANCE_ISSUE)
        if severity:
            most_common = _find_most_common(list(gaps.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Spacing",
                title="Container gap spacing is inconsistent",
                description=f"Gap spacing varies across pages.",
                severity=severity,
                affected_pages=[p for p, v in gaps.items() if v != most_common],
                detected_values={p: f"{v}px" for p, v in gaps.items()},
                recommended_standard=f"{most_common}px",
                confidence=0.75,
            ))
        else:
            consistent_checks += 1

    # If no spacing data found, give benefit of doubt
    if total_checks == 0:
        return 95.0, []

    score = calculate_category_score(max(total_checks, 1), consistent_checks, issues)
    return score, issues


def _analyze_colors(pages: list[PageUIData]) -> tuple[float, list[Issue]]:
    """Analyze color consistency across pages."""
    issues = []
    total_checks = 0
    consistent_checks = 0

    # Compare primary colors
    primary_colors = {}
    for page in pages:
        if page.colors and page.colors.primary_colors:
            primary_colors[page.page_name] = page.colors.primary_colors[0]
        elif page.buttons:
            btn_colors = [b.background_color for b in page.buttons if b.background_color]
            if btn_colors:
                primary_colors[page.page_name] = btn_colors[0]

    if len(primary_colors) >= 2:
        total_checks += 1
        unique = set(primary_colors.values())
        if len(unique) > 1:
            color_list = list(primary_colors.values())
            max_diff = max(
                _color_difference(color_list[i], color_list[j])
                for i in range(len(color_list))
                for j in range(i + 1, len(color_list))
            )
            severity = determine_severity(max_diff, settings.COLOR_TOLERANCE_IGNORE, settings.COLOR_TOLERANCE_ISSUE)
            if severity:
                most_common = _find_most_common(list(primary_colors.values()))
                issues.append(Issue(
                    id=_next_issue_id(),
                    category="Colors",
                    title="Primary colors are inconsistent across pages",
                    description="The primary/brand color varies between pages.",
                    severity=severity,
                    affected_pages=[p for p, v in primary_colors.items() if v != most_common],
                    detected_values=primary_colors,
                    recommended_standard=most_common,
                    confidence=0.9,
                ))
            else:
                consistent_checks += 1
        else:
            consistent_checks += 1

    # Compare background colors
    bg_colors = {}
    for page in pages:
        if page.colors and page.colors.background_colors:
            bg_colors[page.page_name] = page.colors.background_colors[0]

    if len(bg_colors) >= 2:
        total_checks += 1
        unique = set(bg_colors.values())
        if len(unique) > 1:
            color_list = list(bg_colors.values())
            max_diff = max(
                _color_difference(color_list[i], color_list[j])
                for i in range(len(color_list))
                for j in range(i + 1, len(color_list))
            )
            severity = determine_severity(max_diff, settings.COLOR_TOLERANCE_IGNORE, settings.COLOR_TOLERANCE_ISSUE)
            if severity:
                most_common = _find_most_common(list(bg_colors.values()))
                issues.append(Issue(
                    id=_next_issue_id(),
                    category="Colors",
                    title="Background colors differ across pages",
                    description="Page background colors are not consistent.",
                    severity=severity,
                    affected_pages=[p for p, v in bg_colors.items() if v != most_common],
                    detected_values=bg_colors,
                    recommended_standard=most_common,
                    confidence=0.8,
                ))
            else:
                consistent_checks += 1
        else:
            consistent_checks += 1

    # Compare text colors
    text_colors = {}
    for page in pages:
        if page.colors and page.colors.text_colors:
            text_colors[page.page_name] = page.colors.text_colors[0]

    if len(text_colors) >= 2:
        total_checks += 1
        unique = set(text_colors.values())
        if len(unique) > 1:
            color_list = list(text_colors.values())
            max_diff = max(
                _color_difference(color_list[i], color_list[j])
                for i in range(len(color_list))
                for j in range(i + 1, len(color_list))
            )
            severity = determine_severity(max_diff, settings.COLOR_TOLERANCE_IGNORE, settings.COLOR_TOLERANCE_ISSUE)
            if severity:
                most_common = _find_most_common(list(text_colors.values()))
                issues.append(Issue(
                    id=_next_issue_id(),
                    category="Colors",
                    title="Text colors are inconsistent",
                    description="Body text colors differ across pages.",
                    severity=severity,
                    affected_pages=[p for p, v in text_colors.items() if v != most_common],
                    detected_values=text_colors,
                    recommended_standard=most_common,
                    confidence=0.8,
                ))
            else:
                consistent_checks += 1
        else:
            consistent_checks += 1

    if total_checks == 0:
        return 95.0, []

    score = calculate_category_score(max(total_checks, 1), consistent_checks, issues)
    return score, issues


def _analyze_cards(pages: list[PageUIData]) -> tuple[float, list[Issue]]:
    """Analyze card component consistency across pages."""
    issues = []
    total_checks = 0
    consistent_checks = 0

    page_cards = {p.page_name: p.cards for p in pages if p.cards}

    if len(page_cards) < 2:
        return 100.0, []

    # Compare card border radius
    radii = {}
    for page_name, cards in page_cards.items():
        r = [c.border_radius for c in cards if c.border_radius is not None]
        if r:
            radii[page_name] = round(sum(r) / len(r), 1)

    if len(radii) >= 2:
        total_checks += 1
        diff = _numeric_diff(list(radii.values()))
        severity = determine_severity(diff, settings.RADIUS_TOLERANCE_IGNORE, settings.RADIUS_TOLERANCE_ISSUE)
        if severity:
            most_common = _find_most_common(list(radii.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Cards",
                title="Card border radius differs between pages",
                description=f"Card border radius varies from {min(radii.values())}px to {max(radii.values())}px.",
                severity=severity,
                affected_pages=[p for p, v in radii.items() if v != most_common],
                detected_values={p: f"{v}px" for p, v in radii.items()},
                recommended_standard=f"{most_common}px",
                confidence=0.85,
            ))
        else:
            consistent_checks += 1

    # Compare card padding
    paddings = {}
    for page_name, cards in page_cards.items():
        p = [c.padding for c in cards if c.padding is not None]
        if p:
            paddings[page_name] = round(sum(p) / len(p), 1)

    if len(paddings) >= 2:
        total_checks += 1
        diff = _numeric_diff(list(paddings.values()))
        severity = determine_severity(diff, settings.SPACING_TOLERANCE_IGNORE, settings.SPACING_TOLERANCE_ISSUE)
        if severity:
            most_common = _find_most_common(list(paddings.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Cards",
                title="Card padding differs between pages",
                description=f"Card internal padding varies across pages.",
                severity=severity,
                affected_pages=[p for p, v in paddings.items() if v != most_common],
                detected_values={p: f"{v}px" for p, v in paddings.items()},
                recommended_standard=f"{most_common}px",
                confidence=0.8,
            ))
        else:
            consistent_checks += 1

    # Compare card shadows
    shadows = {}
    for page_name, cards in page_cards.items():
        s = [c.box_shadow for c in cards if c.box_shadow]
        if s:
            shadows[page_name] = s[0]

    if len(shadows) >= 2:
        total_checks += 1
        unique = set(shadows.values())
        if len(unique) > 1:
            most_common = _find_most_common(list(shadows.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Cards",
                title="Card shadow styles differ across pages",
                description="Card box-shadow is not consistent.",
                severity=IssueSeverity.LOW,
                affected_pages=[p for p, v in shadows.items() if v != most_common],
                detected_values=shadows,
                recommended_standard=most_common,
                confidence=0.7,
            ))
        else:
            consistent_checks += 1

    score = calculate_category_score(max(total_checks, 1), consistent_checks, issues)
    return score, issues


def _analyze_navbar(pages: list[PageUIData]) -> tuple[float, list[Issue]]:
    """Analyze navbar consistency across pages."""
    issues = []
    total_checks = 0
    consistent_checks = 0

    navbars = {p.page_name: p.navbar for p in pages if p.navbar}

    if len(navbars) < 2:
        return 100.0, []

    # Compare navbar height
    heights = {p: n.height for p, n in navbars.items() if n.height is not None}
    if len(heights) >= 2:
        total_checks += 1
        diff = _numeric_diff(list(heights.values()))
        severity = determine_severity(diff, settings.SIZE_TOLERANCE_IGNORE, settings.SIZE_TOLERANCE_ISSUE)
        if severity:
            most_common = _find_most_common(list(heights.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Navbar",
                title="Navbar height differs across pages",
                description=f"Navbar height varies from {min(heights.values())}px to {max(heights.values())}px.",
                severity=severity,
                affected_pages=[p for p, v in heights.items() if v != most_common],
                detected_values={p: f"{v}px" for p, v in heights.items()},
                recommended_standard=f"{most_common}px",
                confidence=0.9,
            ))
        else:
            consistent_checks += 1

    # Compare navbar background color
    bg_colors = {p: n.background_color for p, n in navbars.items() if n.background_color}
    if len(bg_colors) >= 2:
        total_checks += 1
        unique = set(bg_colors.values())
        if len(unique) > 1:
            most_common = _find_most_common(list(bg_colors.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Navbar",
                title="Navbar background color varies across pages",
                description="The navigation bar background color is not consistent.",
                severity=IssueSeverity.MEDIUM,
                affected_pages=[p for p, v in bg_colors.items() if v != most_common],
                detected_values=bg_colors,
                recommended_standard=most_common,
                confidence=0.85,
            ))
        else:
            consistent_checks += 1

    score = calculate_category_score(max(total_checks, 1), consistent_checks, issues)
    return score, issues


def _analyze_forms(pages: list[PageUIData]) -> tuple[float, list[Issue]]:
    """Analyze form input consistency across pages."""
    issues = []
    total_checks = 0
    consistent_checks = 0

    page_forms = {p.page_name: p.form_inputs for p in pages if p.form_inputs}

    if len(page_forms) < 2:
        return 100.0, []

    # Compare input border radius
    radii = {}
    for page_name, inputs in page_forms.items():
        r = [f.border_radius for f in inputs if f.border_radius is not None]
        if r:
            radii[page_name] = round(sum(r) / len(r), 1)

    if len(radii) >= 2:
        total_checks += 1
        diff = _numeric_diff(list(radii.values()))
        severity = determine_severity(diff, settings.RADIUS_TOLERANCE_IGNORE, settings.RADIUS_TOLERANCE_ISSUE)
        if severity:
            most_common = _find_most_common(list(radii.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Forms",
                title="Input border radius differs across pages",
                description=f"Form input border radius varies from {min(radii.values())}px to {max(radii.values())}px.",
                severity=severity,
                affected_pages=[p for p, v in radii.items() if v != most_common],
                detected_values={p: f"{v}px" for p, v in radii.items()},
                recommended_standard=f"{most_common}px",
                confidence=0.85,
            ))
        else:
            consistent_checks += 1

    # Compare input heights
    heights = {}
    for page_name, inputs in page_forms.items():
        h = [f.height for f in inputs if f.height is not None]
        if h:
            heights[page_name] = round(sum(h) / len(h), 1)

    if len(heights) >= 2:
        total_checks += 1
        diff = _numeric_diff(list(heights.values()))
        severity = determine_severity(diff, settings.SIZE_TOLERANCE_IGNORE, settings.SIZE_TOLERANCE_ISSUE)
        if severity:
            most_common = _find_most_common(list(heights.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Forms",
                title="Input field heights are inconsistent",
                description=f"Input heights vary from {min(heights.values())}px to {max(heights.values())}px.",
                severity=severity,
                affected_pages=[p for p, v in heights.items() if v != most_common],
                detected_values={p: f"{v}px" for p, v in heights.items()},
                recommended_standard=f"{most_common}px",
                confidence=0.8,
            ))
        else:
            consistent_checks += 1

    # Compare input padding
    paddings = {}
    for page_name, inputs in page_forms.items():
        p = [f.padding_horizontal for f in inputs if f.padding_horizontal is not None]
        if p:
            paddings[page_name] = round(sum(p) / len(p), 1)

    if len(paddings) >= 2:
        total_checks += 1
        diff = _numeric_diff(list(paddings.values()))
        severity = determine_severity(diff, settings.SPACING_TOLERANCE_IGNORE, settings.SPACING_TOLERANCE_ISSUE)
        if severity:
            most_common = _find_most_common(list(paddings.values()))
            issues.append(Issue(
                id=_next_issue_id(),
                category="Forms",
                title="Input padding differs across pages",
                description="Form input horizontal padding is not consistent.",
                severity=severity,
                affected_pages=[p_name for p_name, v in paddings.items() if v != most_common],
                detected_values={p_name: f"{v}px" for p_name, v in paddings.items()},
                recommended_standard=f"{most_common}px",
                confidence=0.75,
            ))
        else:
            consistent_checks += 1

    score = calculate_category_score(max(total_checks, 1), consistent_checks, issues)
    return score, issues


def _analyze_responsive(pages: list[PageUIData]) -> tuple[float, list[Issue]]:
    """Analyze responsive design issues."""
    issues = []
    total_checks = 0
    consistent_checks = 0

    # Collect all responsive issues from pages
    all_responsive_issues = []
    for page in pages:
        all_responsive_issues.extend(page.responsive_issues)

    if not all_responsive_issues:
        return 100.0, []

    # Group by issue type
    issue_types = defaultdict(list)
    for ri in all_responsive_issues:
        issue_types[ri.issue_type].append(ri)

    for issue_type, responsive_issues in issue_types.items():
        total_checks += 1

        # Map issue type to severity
        severity_map = {
            "horizontal_overflow": IssueSeverity.HIGH,
            "element_overflow": IssueSeverity.MEDIUM,
            "overlap": IssueSeverity.HIGH,
            "small_button": IssueSeverity.MEDIUM,
            "small_text": IssueSeverity.LOW,
        }

        severity = severity_map.get(issue_type, IssueSeverity.MEDIUM)
        affected_viewports = list(set(ri.viewport for ri in responsive_issues))

        title_map = {
            "horizontal_overflow": "Horizontal overflow detected on mobile/tablet",
            "element_overflow": "Elements extend beyond viewport",
            "overlap": "Overlapping elements detected",
            "small_button": "Buttons too small for touch targets",
            "small_text": "Text too small on mobile viewport",
        }

        issues.append(Issue(
            id=_next_issue_id(),
            category="Responsive",
            title=title_map.get(issue_type, f"Responsive issue: {issue_type}"),
            description=responsive_issues[0].description,
            severity=severity,
            affected_pages=affected_viewports,
            detected_values={ri.viewport: ri.description for ri in responsive_issues[:5]},
            confidence=0.8,
        ))

    score = calculate_category_score(max(total_checks, 1), consistent_checks, issues)
    return score, issues
