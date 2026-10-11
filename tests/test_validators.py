"""
Unit tests for URL and input validators.
"""

import pytest
from utils.validators import validate_social_media_link, validate_quantity, validate_transaction_reference

def test_instagram_link_validation():
    valid, url = validate_social_media_link("Instagram", "https://instagram.com/abel_promotion")
    assert valid is True
    assert "instagram.com" in url

    valid, url = validate_social_media_link("Instagram", "instagram.com/my_page")
    assert valid is True
    assert url.startswith("https://")

    valid, msg = validate_social_media_link("Instagram", "https://twitter.com/my_page")
    assert valid is False

def test_facebook_link_validation():
    valid, url = validate_social_media_link("Facebook", "https://facebook.com/abel_business")
    assert valid is True

    valid, msg = validate_social_media_link("Facebook", "not_a_valid_link")
    assert valid is False

def test_youtube_link_validation():
    valid, url = validate_social_media_link("YouTube", "https://youtube.com/c/AbelTech")
    assert valid is True

    valid, url = validate_social_media_link("YouTube", "https://youtu.be/xyz12345")
    assert valid is True

def test_quantity_validation():
    valid, val = validate_quantity("5", min_qty=1, max_qty=10)
    assert valid is True
    assert val == 5

    valid, val = validate_quantity("0", min_qty=1, max_qty=10)
    assert valid is False

    valid, val = validate_quantity("100", min_qty=1, max_qty=10)
    assert valid is False

    valid, val = validate_quantity("abc", min_qty=1, max_qty=10)
    assert valid is False

def test_transaction_reference_validation():
    valid, ref = validate_transaction_reference("FT26071890")
    assert valid is True
    assert ref == "FT26071890"

    valid, ref = validate_transaction_reference("tb-987654321")
    assert valid is True
    assert ref == "TB-987654321"

    valid, err = validate_transaction_reference("ab")
    assert valid is False

    valid, err = validate_transaction_reference("FT@#$$%^")
    assert valid is False
