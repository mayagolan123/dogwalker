# Dog Breeds (FastAPI)

A small FastAPI web app that lets you pick a dog breed from a list and view:

1. A photo of the breed (from the [Dog CEO API](https://dog.ceo/dog-api/))
2. A short description (curated locally, with sensible fallbacks)
3. A link for more information (usually Wikipedia)

## Requirements

- Python 3.11+
- Network access to `dog.ceo` when running the app (for breed lists and images)

## Setup (local)

Clone with submodules (includes environment values):

```bash
git clone --recurse-submodules https://github.com/mayagolan123/dogwalker.git
cd dogwalker
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

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

## Deploy (Kubernetes / Helm)

The Helm chart lives in `deployment/dogwalker/`. It runs **2 replicas** by default (HA), with liveness (`/health`), readiness (`/ready`), resource requests/limits, and non-root pods (UID 1000, matching the Docker image).

Per-environment overrides and **`targetRevision`** (which Git ref to deploy) live in the **`environments/`** git submodule ([mayagolan123/environments](https://github.com/mayagolan123/environments)):

| Environment directory | `targetRevision` | Git ref |
|----------------------|------------------|---------|
| `environments/dogwalker/feature-add-this-feature/` | `feature/add-this-feature` | branch |
| `environments/dogwalker/feature-fix-this/` | `feature/fix-this` | branch |
| `environments/dogwalker/staging/` | `main` | branch |
| `environments/dogwalker/production/` | `v1.0.0` | tag on `main` |

Install with an environment values file (set `targetRevision` on your Argo CD Application to match):

```bash
helm upgrade --install dogwalker ./deployment/dogwalker \
  -f environments/dogwalker/staging/values.yaml \
  --set image.repository=your-registry/dogwalker
```

Build and push your image, then install without the environments repo:

```bash
docker build -t your-registry/dogwalker:1.0.0 .
docker push your-registry/dogwalker:1.0.0

helm upgrade --install dogwalker ./deployment/dogwalker \
  --set image.repository=your-registry/dogwalker \
  --set image.tag=1.0.0
```

Access locally via port-forward:

```bash
kubectl port-forward svc/dogwalker-dogwalker 8000:8000
```

Optional ingress:

```bash
helm upgrade --install dogwalker ./deployment/dogwalker \
  --set image.repository=your-registry/dogwalker \
  --set image.tag=1.0.0 \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=dogwalker.example.com
```

Validate the chart without installing:

```bash
helm template dogwalker ./deployment/dogwalker
```

## Project layout

```
app/
  main.py              # Routes and app setup
  config.py            # Environment-based settings
  services/breeds.py   # Breed list, images, and metadata
  data/breeds_metadata.json
  templates/index.html
  static/style.css
deployment/dogwalker/  # Helm chart
environments/        # git submodule (per-env values + targetRevision)
tests/
```
