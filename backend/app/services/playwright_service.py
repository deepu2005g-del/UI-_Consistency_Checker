"""
Playwright service for website URL analysis.
Launches a browser, navigates to the URL, captures screenshots at multiple viewports,
and extracts DOM/CSS properties for UI analysis.
"""

import logging
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urljoin

from app.config import settings
from app.models.ui import (
    PageUIData, ViewportInfo, ButtonInfo, HeadingInfo, TextInfo,
    CardInfo, NavbarInfo, FormInputInfo, SpacingInfo, ColorPalette,
    ResponsiveIssue,
)

logger = logging.getLogger(__name__)

# Viewport configurations for responsive analysis
VIEWPORTS = [
    {"width": 1440, "height": 900, "label": "desktop"},
    {"width": 768, "height": 1024, "label": "tablet"},
    {"width": 390, "height": 844, "label": "mobile"},
]

# JavaScript to extract CSS properties from DOM elements
DOM_EXTRACTION_SCRIPT = """
() => {
    const getStyle = (el) => window.getComputedStyle(el);
    const px = (val) => parseFloat(val) || null;
    const rgb2hex = (rgb) => {
        if (!rgb || rgb === 'transparent' || rgb === 'rgba(0, 0, 0, 0)') return null;
        const match = rgb.match(/\\d+/g);
        if (!match || match.length < 3) return null;
        return '#' + match.slice(0, 3).map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
    };

    // Extract buttons
    const buttons = [];
    document.querySelectorAll('button, a.btn, [role="button"], input[type="submit"], input[type="button"], .button, .btn').forEach((el, i) => {
        if (i >= 20 || el.offsetWidth === 0) return;
        const s = getStyle(el);
        buttons.push({
            label: el.textContent?.trim()?.substring(0, 50) || null,
            type: el.classList.contains('primary') || el.classList.contains('btn-primary') ? 'primary' :
                  el.classList.contains('secondary') || el.classList.contains('btn-secondary') ? 'secondary' :
                  el.classList.contains('outline') || el.classList.contains('btn-outline') ? 'outline' : 'unknown',
            background_color: rgb2hex(s.backgroundColor),
            text_color: rgb2hex(s.color),
            font_size: px(s.fontSize),
            font_weight: parseInt(s.fontWeight) || null,
            padding_vertical: px(s.paddingTop),
            padding_horizontal: px(s.paddingLeft),
            width: px(s.width),
            height: px(s.height),
            border_radius: px(s.borderRadius),
            border_color: rgb2hex(s.borderColor),
            box_shadow: s.boxShadow !== 'none' ? s.boxShadow : null,
        });
    });

    // Extract headings
    const headings = [];
    document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach((el, i) => {
        if (i >= 20 || el.offsetWidth === 0) return;
        const s = getStyle(el);
        headings.push({
            level: parseInt(el.tagName[1]),
            text: el.textContent?.trim()?.substring(0, 100) || null,
            font_size: px(s.fontSize),
            font_weight: parseInt(s.fontWeight) || null,
            font_family: s.fontFamily?.split(',')[0]?.replace(/['"]/g, '') || null,
            line_height: px(s.lineHeight),
            color: rgb2hex(s.color),
            margin_top: px(s.marginTop),
            margin_bottom: px(s.marginBottom),
        });
    });

    // Extract body text
    const body_text = [];
    document.querySelectorAll('p, span, li, td, label').forEach((el, i) => {
        if (i >= 10 || el.offsetWidth === 0 || !el.textContent?.trim()) return;
        const s = getStyle(el);
        body_text.push({
            font_size: px(s.fontSize),
            font_weight: parseInt(s.fontWeight) || null,
            font_family: s.fontFamily?.split(',')[0]?.replace(/['"]/g, '') || null,
            line_height: px(s.lineHeight),
            color: rgb2hex(s.color),
        });
    });

    // Extract cards (common card patterns)
    const cards = [];
    document.querySelectorAll('.card, [class*="card"], article, .panel, [class*="panel"]').forEach((el, i) => {
        if (i >= 15 || el.offsetWidth === 0 || el.offsetHeight < 50) return;
        const s = getStyle(el);
        cards.push({
            border_radius: px(s.borderRadius),
            padding: px(s.padding) || px(s.paddingTop),
            padding_top: px(s.paddingTop),
            padding_bottom: px(s.paddingBottom),
            padding_left: px(s.paddingLeft),
            padding_right: px(s.paddingRight),
            border_color: rgb2hex(s.borderColor),
            box_shadow: s.boxShadow !== 'none' ? s.boxShadow : null,
            background_color: rgb2hex(s.backgroundColor),
            gap: px(s.gap),
        });
    });

    // Extract navbar
    let navbar = null;
    const navEl = document.querySelector('nav, header, [role="navigation"], .navbar, .nav');
    if (navEl && navEl.offsetWidth > 0) {
        const s = getStyle(navEl);
        navbar = {
            height: px(s.height) || navEl.offsetHeight,
            background_color: rgb2hex(s.backgroundColor),
            text_color: rgb2hex(s.color),
            font_size: px(s.fontSize),
            font_weight: parseInt(s.fontWeight) || null,
            font_family: s.fontFamily?.split(',')[0]?.replace(/['"]/g, '') || null,
            padding: s.padding,
            position: s.position,
            box_shadow: s.boxShadow !== 'none' ? s.boxShadow : null,
            border_bottom: s.borderBottom !== 'none' ? s.borderBottom : null,
            menu_gap: px(s.gap),
        };
    }

    // Extract form inputs
    const form_inputs = [];
    document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select').forEach((el, i) => {
        if (i >= 15 || el.offsetWidth === 0) return;
        const s = getStyle(el);
        // Find associated label
        const labelEl = el.id ? document.querySelector(`label[for="${el.id}"]`) : el.closest('label');
        const labelStyle = labelEl ? getStyle(labelEl) : null;
        form_inputs.push({
            type: el.type || el.tagName.toLowerCase(),
            height: px(s.height),
            padding_vertical: px(s.paddingTop),
            padding_horizontal: px(s.paddingLeft),
            border_radius: px(s.borderRadius),
            border_color: rgb2hex(s.borderColor),
            border_width: px(s.borderWidth),
            background_color: rgb2hex(s.backgroundColor),
            font_size: px(s.fontSize),
            font_family: s.fontFamily?.split(',')[0]?.replace(/['"]/g, '') || null,
            label_font_size: labelStyle ? px(labelStyle.fontSize) : null,
            label_font_weight: labelStyle ? parseInt(labelStyle.fontWeight) : null,
            label_color: labelStyle ? rgb2hex(labelStyle.color) : null,
        });
    });

    // Extract colors
    const allColors = {
        primary_colors: [],
        secondary_colors: [],
        background_colors: [],
        text_colors: [],
        border_colors: [],
        button_colors: [],
        accent_colors: [],
    };

    // Background colors from major sections
    document.querySelectorAll('body, main, section, .container, header, footer').forEach(el => {
        const bg = rgb2hex(getStyle(el).backgroundColor);
        if (bg && !allColors.background_colors.includes(bg)) allColors.background_colors.push(bg);
    });

    // Text colors
    document.querySelectorAll('h1, h2, h3, p, span, a, li').forEach((el, i) => {
        if (i >= 30) return;
        const color = rgb2hex(getStyle(el).color);
        if (color && !allColors.text_colors.includes(color)) allColors.text_colors.push(color);
    });

    // Button colors
    buttons.forEach(btn => {
        if (btn.background_color && !allColors.button_colors.includes(btn.background_color)) {
            allColors.button_colors.push(btn.background_color);
        }
    });

    // Spacing info
    const spacing = [];
    document.querySelectorAll('section, main, .container, .content, .wrapper').forEach((el, i) => {
        if (i >= 10 || el.offsetWidth === 0) return;
        const s = getStyle(el);
        spacing.push({
            element_type: el.tagName.toLowerCase() === 'section' ? 'section' : 'container',
            padding_top: px(s.paddingTop),
            padding_bottom: px(s.paddingBottom),
            padding_left: px(s.paddingLeft),
            padding_right: px(s.paddingRight),
            margin_top: px(s.marginTop),
            margin_bottom: px(s.marginBottom),
            gap: px(s.gap),
        });
    });

    return {
        buttons, headings, body_text, cards, navbar,
        form_inputs, colors: allColors, spacing,
    };
}
"""

# JavaScript to detect responsive issues
RESPONSIVE_CHECK_SCRIPT = """
() => {
    const issues = [];
    const viewportWidth = window.innerWidth;

    // Check for horizontal overflow
    if (document.body.scrollWidth > viewportWidth + 5) {
        issues.push({
            issue_type: 'horizontal_overflow',
            description: `Page has horizontal overflow (body width: ${document.body.scrollWidth}px, viewport: ${viewportWidth}px)`,
            severity: 'HIGH',
        });
    }

    // Check elements extending outside viewport
    document.querySelectorAll('div, section, nav, header, main, img, table').forEach((el, i) => {
        if (i >= 100) return;
        const rect = el.getBoundingClientRect();
        if (rect.width > viewportWidth + 10 && el.offsetHeight > 0) {
            issues.push({
                issue_type: 'element_overflow',
                description: `Element ${el.tagName}${el.className ? '.' + el.className.split(' ')[0] : ''} extends beyond viewport (${Math.round(rect.width)}px wide)`,
                element: el.tagName + (el.className ? '.' + el.className.split(' ')[0] : ''),
                severity: 'MEDIUM',
            });
        }
    });

    // Check for very small text on mobile
    if (viewportWidth < 500) {
        document.querySelectorAll('p, span, li, td, a').forEach((el, i) => {
            if (i >= 30) return;
            const fontSize = parseFloat(window.getComputedStyle(el).fontSize);
            if (fontSize < 12 && el.textContent?.trim()?.length > 0 && el.offsetWidth > 0) {
                issues.push({
                    issue_type: 'small_text',
                    description: `Text element has very small font size (${fontSize}px) on mobile`,
                    element: el.tagName,
                    severity: 'LOW',
                });
            }
        });
    }

    // Check for tiny buttons on mobile
    if (viewportWidth < 500) {
        document.querySelectorAll('button, a.btn, [role="button"], .btn').forEach((el, i) => {
            if (i >= 20) return;
            const rect = el.getBoundingClientRect();
            if ((rect.width < 44 || rect.height < 44) && el.offsetWidth > 0) {
                issues.push({
                    issue_type: 'small_button',
                    description: `Button "${el.textContent?.trim()?.substring(0, 30)}" is too small for touch targets (${Math.round(rect.width)}x${Math.round(rect.height)}px)`,
                    element: 'button',
                    severity: 'MEDIUM',
                });
            }
        });
    }

    // Check for overlapping elements (simplified check)
    const navEl = document.querySelector('nav, header, .navbar');
    if (navEl) {
        const navRect = navEl.getBoundingClientRect();
        const mainEl = document.querySelector('main, .main, .content, section');
        if (mainEl) {
            const mainRect = mainEl.getBoundingClientRect();
            if (navRect.bottom > mainRect.top + 5 && navEl.style?.position !== 'fixed') {
                issues.push({
                    issue_type: 'overlap',
                    description: 'Navbar may be overlapping with main content',
                    severity: 'MEDIUM',
                });
            }
        }
    }

    return issues;
}
"""

# JavaScript to discover internal links
LINK_DISCOVERY_SCRIPT = """
(baseUrl) => {
    const links = new Set();
    const baseOrigin = new URL(baseUrl).origin;
    const basePath = new URL(baseUrl).pathname;

    document.querySelectorAll('a[href]').forEach(a => {
        try {
            const href = a.href;
            const url = new URL(href);

            // Only same origin
            if (url.origin !== baseOrigin) return;

            // Skip anchors, javascript, mailto
            if (url.pathname === basePath) return;
            if (href.startsWith('javascript:')) return;
            if (href.startsWith('mailto:')) return;
            if (href.startsWith('tel:')) return;
            if (url.hash && url.pathname === basePath) return;

            // Skip common non-page paths
            const skip = ['/api/', '/static/', '/assets/', '/images/', '.pdf', '.zip', '.js', '.css'];
            if (skip.some(s => url.pathname.toLowerCase().includes(s))) return;

            links.add(url.origin + url.pathname);
        } catch(e) {}
    });

    return [...links];
}
"""


async def analyze_url(
    url: str,
    analysis_id: str,
    on_progress: Optional[callable] = None,
) -> list[PageUIData]:
    """
    Analyze a website URL using Playwright.
    Captures screenshots at multiple viewports and extracts DOM/CSS properties.

    Args:
        url: The website URL to analyze.
        analysis_id: Unique analysis identifier.
        on_progress: Optional callback for progress updates.

    Returns:
        List of PageUIData objects for each analyzed page/viewport.
    """
    from playwright.async_api import async_playwright

    upload_dir = Path("uploads") / analysis_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    all_page_data: list[PageUIData] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        try:
            # Discover pages from the main URL
            pages_to_analyze = [url]

            # First pass: discover internal links
            context = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) UIConsistencyChecker/1.0",
            )
            page = await context.new_page()

            try:
                await page.goto(url, timeout=settings.PLAYWRIGHT_TIMEOUT_MS, wait_until="networkidle")
                await page.wait_for_timeout(1000)

                # Discover internal links
                discovered_links = await page.evaluate(LINK_DISCOVERY_SCRIPT, url)
                logger.info(f"Discovered {len(discovered_links)} internal links from {url}")

                # Add discovered links (up to max)
                for link in discovered_links[:settings.MAX_PAGES_TO_CRAWL - 1]:
                    if link not in pages_to_analyze:
                        pages_to_analyze.append(link)

            except Exception as e:
                logger.warning(f"Link discovery failed: {e}")
            finally:
                await context.close()

            logger.info(f"Will analyze {len(pages_to_analyze)} pages: {pages_to_analyze}")

            # Analyze each page at each viewport
            for page_idx, page_url in enumerate(pages_to_analyze):
                parsed = urlparse(page_url)
                page_name = parsed.path.strip("/").replace("/", "_") or "home"
                page_name = page_name.title() if page_name != "home" else "Home"

                if on_progress:
                    await on_progress(
                        f"Analyzing page {page_idx + 1}/{len(pages_to_analyze)}: {page_name}"
                    )

                for viewport in VIEWPORTS:
                    context = await browser.new_context(
                        viewport={"width": viewport["width"], "height": viewport["height"]},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) UIConsistencyChecker/1.0",
                    )
                    page = await context.new_page()

                    try:
                        await page.goto(
                            page_url,
                            timeout=settings.PLAYWRIGHT_TIMEOUT_MS,
                            wait_until="networkidle",
                        )
                        await page.wait_for_timeout(1500)

                        # Capture screenshot
                        screenshot_path = upload_dir / f"{page_name}_{viewport['label']}.png"
                        await page.screenshot(path=str(screenshot_path), full_page=True)

                        # Extract DOM/CSS properties
                        dom_data = await page.evaluate(DOM_EXTRACTION_SCRIPT)

                        # Check for responsive issues
                        responsive_issues_raw = await page.evaluate(RESPONSIVE_CHECK_SCRIPT)

                        # Build PageUIData
                        viewport_info = ViewportInfo(
                            width=viewport["width"],
                            height=viewport["height"],
                            label=viewport["label"],
                        )

                        page_data = _build_page_data(
                            page_name=f"{page_name} ({viewport['label']})",
                            page_url=page_url,
                            viewport=viewport_info,
                            dom_data=dom_data,
                            responsive_issues_raw=responsive_issues_raw,
                            viewport_label=viewport["label"],
                        )

                        all_page_data.append(page_data)

                    except Exception as e:
                        logger.error(f"Failed to analyze {page_url} at {viewport['label']}: {e}")
                    finally:
                        await context.close()

        finally:
            await browser.close()

    return all_page_data


def _build_page_data(
    page_name: str,
    page_url: str,
    viewport: ViewportInfo,
    dom_data: dict,
    responsive_issues_raw: list,
    viewport_label: str,
) -> PageUIData:
    """Build a PageUIData object from raw DOM extraction data."""
    buttons = []
    for btn in dom_data.get("buttons", []):
        try:
            buttons.append(ButtonInfo(**btn))
        except Exception:
            pass

    headings = []
    for h in dom_data.get("headings", []):
        try:
            headings.append(HeadingInfo(**h))
        except Exception:
            pass

    body_text = []
    for t in dom_data.get("body_text", []):
        try:
            body_text.append(TextInfo(**t))
        except Exception:
            pass

    cards = []
    for c in dom_data.get("cards", []):
        try:
            cards.append(CardInfo(**c))
        except Exception:
            pass

    navbar = None
    if dom_data.get("navbar"):
        try:
            navbar = NavbarInfo(**dom_data["navbar"])
        except Exception:
            pass

    form_inputs = []
    for f in dom_data.get("form_inputs", []):
        try:
            form_inputs.append(FormInputInfo(**f))
        except Exception:
            pass

    spacing = []
    for s in dom_data.get("spacing", []):
        try:
            spacing.append(SpacingInfo(**s))
        except Exception:
            pass

    colors = None
    if dom_data.get("colors"):
        try:
            colors = ColorPalette(**dom_data["colors"])
        except Exception:
            pass

    responsive_issues = []
    for ri in responsive_issues_raw:
        try:
            ri["viewport"] = f"{viewport_label}_{viewport.width}x{viewport.height}"
            responsive_issues.append(ResponsiveIssue(**ri))
        except Exception:
            pass

    return PageUIData(
        page_name=page_name,
        page_url=page_url,
        viewport=viewport,
        buttons=buttons,
        headings=headings,
        body_text=body_text,
        cards=cards,
        navbar=navbar,
        form_inputs=form_inputs,
        spacing=spacing,
        colors=colors,
        responsive_issues=responsive_issues,
    )
