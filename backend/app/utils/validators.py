"""
Validation utilities for URLs, images, and AI responses.
"""

import re
import ipaddress
from urllib.parse import urlparse
from typing import Optional
import json


def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate a URL for safety and correctness.
    Returns (is_valid, error_message).
    Blocks localhost, private IPs, file:// URLs, and non-HTTP schemes.
    """
    if not url or not url.strip():
        return False, "URL cannot be empty."

    url = url.strip()

    # Check scheme
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "Only HTTP and HTTPS URLs are allowed."

    if not parsed.hostname:
        return False, "Invalid URL: no hostname found."

    hostname = parsed.hostname.lower()

    # Block localhost
    localhost_patterns = ["localhost", "127.0.0.1", "0.0.0.0", "::1"]
    if hostname in localhost_patterns:
        return False, "Localhost URLs are not allowed. Please provide a publicly accessible URL."

    # Block private IPs
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            return False, "Private/reserved IP addresses are not allowed."
    except ValueError:
        # Not an IP address, that's fine (it's a hostname)
        pass

    # Block common internal domains
    internal_patterns = [
        r"\.local$",
        r"\.internal$",
        r"\.intranet$",
        r"^10\.",
        r"^172\.(1[6-9]|2[0-9]|3[01])\.",
        r"^192\.168\.",
    ]
    for pattern in internal_patterns:
        if re.search(pattern, hostname):
            return False, "Internal/private network URLs are not allowed."

    return True, ""


def validate_image_content_type(content_type: str) -> bool:
    """Check if the content type is an allowed image type."""
    allowed = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
    return content_type.lower() in allowed


def validate_image_extension(filename: str) -> bool:
    """Check if the file extension is an allowed image type."""
    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed_extensions


def extract_json_from_text(text: str) -> Optional[dict | list]:
    """
    Attempt to extract JSON from AI response text.
    Handles cases where JSON is wrapped in markdown code blocks or has extra text.
    """
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code blocks
    patterns = [
        r"```json\s*\n(.*?)\n\s*```",  # ```json ... ```
        r"```\s*\n(.*?)\n\s*```",       # ``` ... ```
        r"\{[\s\S]*\}",                  # Raw JSON object
        r"\[[\s\S]*\]",                  # Raw JSON array
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                json_str = match.group(1) if match.lastindex else match.group(0)
                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                continue

    return None


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal."""
    # Remove path separators and null bytes
    filename = filename.replace("/", "_").replace("\\", "_").replace("\x00", "")
    # Remove leading dots to prevent hidden files
    filename = filename.lstrip(".")
    # Limit length
    if len(filename) > 200:
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        filename = filename[:195] + "." + ext if ext else filename[:200]
    return filename or "unnamed_file"
