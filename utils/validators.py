"""
Validation utilities for Abel Promotion bot.
"""

import re
from typing import Tuple, Optional

# Supported platform URL patterns
PLATFORM_PATTERNS = {
    "Instagram": re.compile(
        r"^(https?://)?(www\.)?instagram\.com/[A-Za-z0-9_.-]+/?.*$",
        re.IGNORECASE
    ),
    "Facebook": re.compile(
        r"^(https?://)?(www\.|m\.)?facebook\.com/[A-Za-z0-9_.-]+/?.*$|^https?://(www\.)?fb\.watch/.*$",
        re.IGNORECASE
    ),
    "YouTube": re.compile(
        r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/[A-Za-z0-9_.-]+/?.*$",
        re.IGNORECASE
    ),
}

def validate_social_media_link(platform: str, url: str) -> Tuple[bool, str]:
    """
    Validate that the provided link looks like a legitimate URL for the chosen platform.
    Returns (is_valid, cleaned_url_or_error_message).
    """
    if not url:
        return False, "Link cannot be empty."

    url = url.strip()

    # Prevent malicious command injections or huge text
    if len(url) > 500:
        return False, "Link is too long."

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    pattern = PLATFORM_PATTERNS.get(platform)
    if pattern:
        if pattern.match(url):
            return True, url
        return False, f"Link does not match standard {platform} URL format."

    # General fallback for any other platform
    general_pattern = re.compile(r"^https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,}/.*$", re.IGNORECASE)
    if general_pattern.match(url):
        return True, url
    return False, "Please enter a valid URL."

def validate_quantity(quantity_str: str, min_qty: int = 1, max_qty: int = 100000) -> Tuple[bool, Optional[int]]:
    """
    Validate integer quantity within allowed boundaries.
    """
    if not quantity_str:
        return False, None

    cleaned = quantity_str.strip()
    if not cleaned.isdigit():
        return False, None

    val = int(cleaned)
    if min_qty <= val <= max_qty:
        return True, val
    return False, None

def validate_transaction_reference(ref: str) -> Tuple[bool, str]:
    """
    Validate transaction reference formatting.
    """
    if not ref:
        return False, "Reference cannot be empty."

    cleaned = ref.strip().upper()
    # Transaction references in CBE / Telebirr typically alphanumeric, between 5 and 40 characters
    if not (4 <= len(cleaned) <= 50):
        return False, "Reference must be between 4 and 50 characters."

    # Ensure it's not containing invalid symbols
    if not re.match(r"^[A-Z0-9_-]+$", cleaned):
        return False, "Reference contains invalid characters."

    return True, cleaned
