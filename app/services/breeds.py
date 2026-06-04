"""Dog breed listing, images, and breed information."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from app.config import DOG_API_BASE_URL, DOG_API_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

_METADATA_PATH = Path(__file__).resolve().parent.parent / "data" / "breeds_metadata.json"


@dataclass(frozen=True)
class BreedDetail:
    """Display data for a selected dog breed."""

    slug: str
    display_name: str
    image_url: str
    description: str
    info_url: str


def _load_metadata() -> dict[str, dict[str, str]]:
    """Load curated breed descriptions and info links from JSON."""
    with _METADATA_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def _flatten_breeds(breeds_tree: dict[str, list[str]]) -> list[str]:
    """Turn the Dog CEO nested breed map into sorted slugs (e.g. retriever/golden)."""
    slugs: list[str] = []
    for breed, sub_breeds in breeds_tree.items():
        if sub_breeds:
            for sub in sub_breeds:
                slugs.append(f"{breed}/{sub}")
        else:
            slugs.append(breed)
    return sorted(slugs, key=str.lower)


def slug_to_display_name(slug: str) -> str:
    """Convert API slug to a readable breed name."""
    parts = slug.replace("/", " ").replace("-", " ").split()
    return " ".join(part.capitalize() for part in parts)


def _metadata_key(slug: str) -> str:
    """Best-effort key into curated metadata (parent breed or full slug)."""
    if "/" in slug:
        return slug.split("/", 1)[0]
    return slug.replace("-", "")


def _fallback_description(display_name: str) -> str:
    return (
        f"The {display_name} is a recognized dog breed. "
        "Explore the link below for history, temperament, and care."
    )


def _fallback_info_url(display_name: str) -> str:
    title = display_name.replace(" ", "_")
    return f"https://en.wikipedia.org/wiki/{title}"


def breed_info(slug: str, metadata: dict[str, dict[str, str]] | None = None) -> tuple[str, str]:
    """Return short description and external info URL for a breed slug."""
    meta = metadata if metadata is not None else _load_metadata()
    display_name = slug_to_display_name(slug)
    entry = meta.get(slug) or meta.get(_metadata_key(slug))
    if entry:
        return entry["description"], entry["info_url"]
    return _fallback_description(display_name), _fallback_info_url(display_name)


async def fetch_breed_slugs(client: httpx.AsyncClient | None = None) -> list[str]:
    """Fetch all breed slugs from the Dog CEO API."""
    url = f"{DOG_API_BASE_URL}/breeds/list/all"
    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=DOG_API_TIMEOUT_SECONDS)
    try:
        response = await client.get(url)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        if payload.get("status") != "success":
            raise ValueError("Dog API returned unsuccessful status for breed list")
        message = payload.get("message")
        if not isinstance(message, dict):
            raise ValueError("Unexpected breed list format from Dog API")
        return _flatten_breeds(message)
    finally:
        if owns_client:
            await client.aclose()


async def fetch_breed_image(slug: str, client: httpx.AsyncClient | None = None) -> str:
    """Fetch a random image URL for the given breed slug."""
    url = f"{DOG_API_BASE_URL}/breed/{slug}/images/random"
    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=DOG_API_TIMEOUT_SECONDS)
    try:
        response = await client.get(url)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        if payload.get("status") != "success":
            raise ValueError(f"Dog API returned no image for breed: {slug}")
        image_url = payload.get("message")
        if not isinstance(image_url, str):
            raise ValueError("Unexpected image response from Dog API")
        return image_url
    finally:
        if owns_client:
            await client.aclose()


async def get_breed_detail(slug: str, client: httpx.AsyncClient | None = None) -> BreedDetail:
    """Resolve image and text for a breed slug."""
    display_name = slug_to_display_name(slug)
    description, info_url = breed_info(slug)
    image_url = await fetch_breed_image(slug, client=client)
    return BreedDetail(
        slug=slug,
        display_name=display_name,
        image_url=image_url,
        description=description,
        info_url=info_url,
    )


async def check_dog_api_ready(client: httpx.AsyncClient | None = None) -> bool:
    """Return True if the Dog CEO API responds successfully."""
    url = f"{DOG_API_BASE_URL}/breeds/list/all"
    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=DOG_API_TIMEOUT_SECONDS)
    try:
        response = await client.get(url)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        return payload.get("status") == "success"
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Dog API readiness check failed: %s", exc)
        return False
    finally:
        if owns_client:
            await client.aclose()
