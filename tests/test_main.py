"""Tests for HTTP endpoints."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

pytestmark = pytest.mark.integration
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.conftest import SAMPLE_BREEDS, SAMPLE_IMAGE


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_ready_success(client: AsyncClient) -> None:
    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_ready_failure() -> None:
    app.state.http_client = httpx.AsyncClient(timeout=10)
    try:
        with patch("app.services.breeds.check_dog_api_ready", new=AsyncMock(return_value=False)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as http_client:
                response = await http_client.get("/ready")
        assert response.status_code == 503
    finally:
        await app.state.http_client.aclose()


@pytest.mark.asyncio
async def test_list_breeds_api(client: AsyncClient) -> None:
    response = await client.get("/api/breeds")
    assert response.status_code == 200
    assert response.json()["breeds"] == SAMPLE_BREEDS


@pytest.mark.asyncio
async def test_breed_detail_api(client: AsyncClient) -> None:
    response = await client.get("/api/breeds/bulldog")
    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "bulldog"
    assert body["image_url"] == SAMPLE_IMAGE
    assert "description" in body
    assert body["info_url"].startswith("https://")


@pytest.mark.asyncio
async def test_index_without_selection(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert "Dog Breeds" in response.text
    assert "Select a breed" in response.text


@pytest.mark.asyncio
async def test_index_with_breed(client: AsyncClient) -> None:
    response = await client.get("/?breed=bulldog")
    assert response.status_code == 200
    assert "Bulldog" in response.text
    assert SAMPLE_IMAGE in response.text
    assert "More about the Bulldog" in response.text


@pytest.mark.asyncio
async def test_index_unknown_breed(client: AsyncClient) -> None:
    response = await client.get("/?breed=not-a-real-breed")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_breeds_upstream_error() -> None:
    app.state.http_client = httpx.AsyncClient(timeout=10)
    try:
        with patch(
            "app.services.breeds.fetch_breed_slugs",
            new=AsyncMock(side_effect=httpx.HTTPError("boom")),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as http_client:
                response = await http_client.get("/api/breeds")
        assert response.status_code == 502
    finally:
        await app.state.http_client.aclose()
