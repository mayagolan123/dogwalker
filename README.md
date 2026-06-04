# Dog Breeds (FastAPI)

A small FastAPI web app that lets you pick a dog breed from a list and view:

1. A photo of the breed (from the [Dog CEO API](https://dog.ceo/dog-api/))
2. A short description (curated locally, with sensible fallbacks)
3. A link for more information (usually Wikipedia)

## Requirements

- Python 3.11+
- Network access to `dog.ceo` when running the app (for breed lists and images)

## Setup (local)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run (local)

```bash
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000), choose a breed, and click **Show breed**.

## Run (Docker)

Build and start with Compose:

```bash
docker compose up --build
```

Or build and run the image directly:

```bash
docker build -t dogwalker .
docker run --rm -p 8000:8000 dogwalker
```

The app listens on port 8000. Override configuration with `-e` flags, for example:

```bash
docker run --rm -p 8000:8000 -e DOG_API_TIMEOUT_SECONDS=15 dogwalker
```

## API

| Endpoint | Description |
|----------|-------------|
| `GET /` | HTML UI with breed selector |
| `GET /api/breeds` | JSON list of breed slugs |
| `GET /api/breeds/{slug}` | JSON detail (image, description, info URL); slug may include `/` |
| `GET /health` | Liveness |
| `GET /ready` | Readiness (checks Dog CEO API) |

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `DOG_API_BASE_URL` | `https://dog.ceo/api` | Upstream API base URL |
| `DOG_API_TIMEOUT_SECONDS` | `10` | HTTP timeout for upstream calls |

## Tests

```bash
pip install -r requirements.txt
pytest
```

Tests mock the Dog CEO API so they do not need network access.

## Project layout

```
app/
  main.py              # Routes and app setup
  config.py            # Environment-based settings
  services/breeds.py   # Breed list, images, and metadata
  data/breeds_metadata.json
  templates/index.html
  static/style.css
tests/
```
