"""Tests for breed service helpers."""

import pytest

from app.services.breeds import breed_info, slug_to_display_name

pytestmark = pytest.mark.unit


def test_slug_to_display_name_simple() -> None:
    assert slug_to_display_name("germanshepherd") == "Germanshepherd"


def test_slug_to_display_name_sub_breed() -> None:
    assert slug_to_display_name("retriever/golden") == "Retriever Golden"


def test_breed_info_known_breed() -> None:
    description, url = breed_info("bulldog")
    assert "bulldog" in description.lower() or "wrinkled" in description.lower()
    assert url == "https://en.wikipedia.org/wiki/Bulldog"


def test_breed_info_fallback() -> None:
    description, url = breed_info("xyzunknownbreed")
    assert "Xyzunknownbreed" in description
    assert url == "https://en.wikipedia.org/wiki/Xyzunknownbreed"
