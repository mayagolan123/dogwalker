"""Shared pytest fixtures."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import DOG_API_TIMEOUT_SECONDS
from app.main import app

SAMPLE_BREEDS = ["bulldog", "retriever/golden", "husky"]
SAMPLE_IMAGE = "https://images.dog.ceo/breeds/bulldog/example.jpg"


@pytest.fixture
def mock_breed_slugs() -> list[str]:
    return SAMPLE_BREEDS.copy()


@pytest.fixture
async def client(mock_breed_slugs: list[str]) -> AsyncIterator[AsyncClient]:
    """HTTP client against the app with Dog API calls mocked."""
    app.state.http_client = httpx.AsyncClient(timeout=DOG_API_TIMEOUT_SECONDS)
    with (
        patch(
            "app.services.breeds.fetch_breed_slugs",
            new=AsyncMock(return_value=mock_breed_slugs),
        ),
        patch(
            "app.services.breeds.fetch_breed_image",
            new=AsyncMock(return_value=SAMPLE_IMAGE),
        ),
        patch(
            "app.services.breeds.check_dog_api_ready",
            new=AsyncMock(return_value=True),
        ),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            yield http_client
    await app.state.http_client.aclose()
