"""FastAPI application for browsing dog breeds."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import DOG_API_TIMEOUT_SECONDS
from app.services import breeds

logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Shared HTTP client for upstream Dog API calls."""
    app.state.http_client = httpx.AsyncClient(timeout=DOG_API_TIMEOUT_SECONDS)
    yield
    await app.state.http_client.aclose()


app = FastAPI(title="Dog Breeds", description="Browse dog breeds with photos and info", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")


@app.get("/health")
async def health() -> dict[str, str]:
    """Process liveness probe."""
    return {"status": "ok"}


@app.get("/ready")
async def ready(request: Request) -> dict[str, str]:
    """Readiness probe; verifies the upstream Dog API is reachable."""
    client: httpx.AsyncClient = request.app.state.http_client
    if await breeds.check_dog_api_ready(client=client):
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Dog breed API is not available")


@app.get("/api/breeds")
async def list_breeds(request: Request) -> dict[str, list[str]]:
    """JSON list of breed slugs for clients."""
    client: httpx.AsyncClient = request.app.state.http_client
    try:
        slugs = await breeds.fetch_breed_slugs(client=client)
    except httpx.HTTPError as exc:
        logger.exception("Failed to load breed list")
        raise HTTPException(status_code=502, detail="Could not load breeds") from exc
    return {"breeds": slugs}


@app.get("/api/breeds/{breed_path:path}")
async def breed_detail_api(breed_path: str, request: Request) -> dict[str, str]:
    """JSON detail for a single breed (breed_path may contain slashes)."""
    client: httpx.AsyncClient = request.app.state.http_client
    try:
        detail = await breeds.get_breed_detail(breed_path, client=client)
    except httpx.HTTPError as exc:
        logger.exception("Failed to load breed detail for %s", breed_path)
        raise HTTPException(status_code=502, detail="Could not load breed") from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "slug": detail.slug,
        "display_name": detail.display_name,
        "image_url": detail.image_url,
        "description": detail.description,
        "info_url": detail.info_url,
    }


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    breed: str | None = Query(default=None, description="Breed slug from the list"),
) -> HTMLResponse:
    """HTML page: breed picker and optional breed detail panel."""
    client: httpx.AsyncClient = request.app.state.http_client
    try:
        breed_slugs = await breeds.fetch_breed_slugs(client=client)
    except httpx.HTTPError as exc:
        logger.exception("Failed to load breeds for index page")
        raise HTTPException(status_code=502, detail="Could not load breeds") from exc

    selected = None
    if breed:
        if breed not in breed_slugs:
            raise HTTPException(status_code=404, detail="Unknown breed")
        try:
            selected = await breeds.get_breed_detail(breed, client=client)
        except httpx.HTTPError as exc:
            logger.exception("Failed to load breed %s", breed)
            raise HTTPException(status_code=502, detail="Could not load breed") from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "breeds": breed_slugs,
            "selected_breed": breed,
            "detail": selected,
        },
    )
