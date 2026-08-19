"""
Pydantic models for extracted UI element data.
These models represent the structured output from vision AI or DOM inspection.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ButtonInfo(BaseModel):
    """Extracted button properties."""
    label: Optional[str] = None
    type: str = "unknown"  # primary, secondary, outline, ghost, etc.
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    font_size: Optional[float] = None  # px
    font_weight: Optional[int] = None
    padding: Optional[str] = None  # e.g., "12px 20px"
    padding_vertical: Optional[float] = None  # px
    padding_horizontal: Optional[float] = None  # px
    width: Optional[float] = None  # px
    height: Optional[float] = None  # px
    border_radius: Optional[float] = None  # px
    border: Optional[str] = None
    border_color: Optional[str] = None
    box_shadow: Optional[str] = None
    alignment: Optional[str] = None


class HeadingInfo(BaseModel):
    """Extracted heading properties."""
    level: int = Field(ge=1, le=6)  # h1-h6
    text: Optional[str] = None
    font_size: Optional[float] = None  # px
    font_weight: Optional[int] = None
    font_family: Optional[str] = None
    line_height: Optional[float] = None
    color: Optional[str] = None
    margin_top: Optional[float] = None
    margin_bottom: Optional[float] = None


class TextInfo(BaseModel):
    """Extracted body text properties."""
    font_size: Optional[float] = None
    font_weight: Optional[int] = None
    font_family: Optional[str] = None
    line_height: Optional[float] = None
    color: Optional[str] = None
    letter_spacing: Optional[float] = None


class CardInfo(BaseModel):
    """Extracted card component properties."""
    border_radius: Optional[float] = None
    padding: Optional[float] = None
    padding_top: Optional[float] = None
    padding_bottom: Optional[float] = None
    padding_left: Optional[float] = None
    padding_right: Optional[float] = None
    border: Optional[str] = None
    border_color: Optional[str] = None
    box_shadow: Optional[str] = None
    background_color: Optional[str] = None
    gap: Optional[float] = None  # internal spacing


class NavbarInfo(BaseModel):
    """Extracted navbar properties."""
    height: Optional[float] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    font_size: Optional[float] = None
    font_family: Optional[str] = None
    font_weight: Optional[int] = None
    padding: Optional[str] = None
    logo_position: Optional[str] = None  # left, center, right
    menu_gap: Optional[float] = None
    alignment: Optional[str] = None
    position: Optional[str] = None  # fixed, sticky, static
    border_bottom: Optional[str] = None
    box_shadow: Optional[str] = None


class FormInputInfo(BaseModel):
    """Extracted form input properties."""
    type: str = "text"  # text, email, password, select, textarea
    height: Optional[float] = None
    padding: Optional[str] = None
    padding_vertical: Optional[float] = None
    padding_horizontal: Optional[float] = None
    border_radius: Optional[float] = None
    border_color: Optional[str] = None
    border_width: Optional[float] = None
    background_color: Optional[str] = None
    font_size: Optional[float] = None
    font_family: Optional[str] = None
    placeholder_color: Optional[str] = None
    label_font_size: Optional[float] = None
    label_font_weight: Optional[int] = None
    label_color: Optional[str] = None
    field_gap: Optional[float] = None  # spacing between fields


class SpacingInfo(BaseModel):
    """Extracted spacing properties for sections/containers."""
    element_type: str = "section"  # section, container, card-group
    margin_top: Optional[float] = None
    margin_bottom: Optional[float] = None
    padding_top: Optional[float] = None
    padding_bottom: Optional[float] = None
    padding_left: Optional[float] = None
    padding_right: Optional[float] = None
    gap: Optional[float] = None


class ColorPalette(BaseModel):
    """Extracted color palette from a page."""
    primary_colors: list[str] = Field(default_factory=list)
    secondary_colors: list[str] = Field(default_factory=list)
    background_colors: list[str] = Field(default_factory=list)
    text_colors: list[str] = Field(default_factory=list)
    border_colors: list[str] = Field(default_factory=list)
    button_colors: list[str] = Field(default_factory=list)
    accent_colors: list[str] = Field(default_factory=list)


class ResponsiveIssue(BaseModel):
    """A responsive design issue detected at a specific viewport."""
    viewport: str  # e.g., "mobile_390x844"
    issue_type: str  # overflow, overlap, alignment, wrapping, etc.
    description: str
    element: Optional[str] = None
    severity: str = "MEDIUM"


class ViewportInfo(BaseModel):
    """Viewport metadata."""
    width: int
    height: int
    label: str = "desktop"  # desktop, tablet, mobile


class PageUIData(BaseModel):
    """Complete extracted UI data for a single page."""
    page_name: str
    page_url: Optional[str] = None
    viewport: Optional[ViewportInfo] = None
    buttons: list[ButtonInfo] = Field(default_factory=list)
    headings: list[HeadingInfo] = Field(default_factory=list)
    body_text: list[TextInfo] = Field(default_factory=list)
    cards: list[CardInfo] = Field(default_factory=list)
    navbar: Optional[NavbarInfo] = None
    form_inputs: list[FormInputInfo] = Field(default_factory=list)
    spacing: list[SpacingInfo] = Field(default_factory=list)
    colors: Optional[ColorPalette] = None
    responsive_issues: list[ResponsiveIssue] = Field(default_factory=list)


class ExtractedUI(BaseModel):
    """Collection of extracted UI data across all pages."""
    pages: list[PageUIData] = Field(default_factory=list)
    source_type: str = "screenshots"  # screenshots or url
    source_url: Optional[str] = None
