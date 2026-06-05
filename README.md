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

## CI/CD (GitHub Actions)

Entry workflows are `pr.yml`, `main.yml`, and `release.yml`. Reusable jobs live in `reusable-*.yml` for static analysis, tests, image build/push, security scans, environments updates, EKS deploy, and health checks.

| Workflow | Trigger | Target cluster | Environments update |
|----------|---------|----------------|---------------------|
| `pr.yml` | `pull_request` | **dev** EKS (feature branches) | Creates/updates `environments/dogwalker/{sanitized-branch}/values.yaml` with `targetRevision` = branch name |
| `main.yml` | `push` to `main` | **staging** EKS | Updates `environments/dogwalker/staging/values.yaml` (`targetRevision` + `image.tag` = commit SHA) |
| `release.yml` | `push` tag `v*.*.*` | **production** EKS | Updates `environments/dogwalker/production/values.yaml` (`targetRevision` + `image.tag` = tag) |

Branch names are sanitized for Docker tags and environment directories by replacing `/` with `-` (e.g. `feature/add-this-feature` → `feature-add-this-feature`). Each feature branch maps to a GitHub environment `feature-{sanitized-branch}` (e.g. `feature-feature-add-this-feature`).

### Environments repo updates

The `environments/` directory is a git submodule pointing at [mayagolan123/environments](https://github.com/mayagolan123/environments). CI does **not** commit submodule pointer changes in the app repo. Instead, `reusable-environments-update.yml` checks out the environments repository with a PAT, writes the values file, and pushes directly to that repo. Deploy jobs then check out the latest environments repo before `helm upgrade`.

### Required GitHub secrets

| Secret | Used for |
|--------|----------|
| `DOCKERHUB_USERNAME` | Docker Hub login and image namespace |
| `DOCKERHUB_TOKEN` | Docker Hub push/pull |
| `ENVIRONMENTS_REPO_TOKEN` | Push to `mayagolan123/environments` (PAT with `contents: write`) |
| `AWS_ACCESS_KEY_ID` | EKS `kubectl` / `helm` access |
| `AWS_SECRET_ACCESS_KEY` | EKS access |

### Required GitHub variables

| Variable | Purpose |
|----------|---------|
| `AWS_REGION` | AWS region (default `us-east-1` in workflows if unset) |
| `EKS_CLUSTER_DEV` | Dev cluster name (all feature envs) |
| `EKS_CLUSTER_STAGING` | Staging cluster name |
| `EKS_CLUSTER_PRODUCTION` | Production cluster name |
| `ENABLE_EKS_DEPLOY` | Set to `true` to run real EKS deploys (otherwise deploy/health jobs emit a warning and skip live cluster access) |
| `DEV_APP_URL` | Optional ingress URL for dev health checks (uses `kubectl port-forward` when empty) |
| `STAGING_APP_URL` | Optional staging ingress URL for health + load test |
| `PRODUCTION_APP_URL` | Optional production URL for pre/post-deploy health checks |

### GitHub environments

Configure GitHub environments for deployment approval gates:

| Environment | Used by | Notes |
|-------------|---------|-------|
| `feature-{sanitized-branch}` | PR pipeline (per branch) | Auto-created on first deploy; optional reviewers per feature |
| `staging` | `main.yml` | Environments update, deploy, and health jobs |
| `production` | `release.yml` | Pre-deploy health, environments update, deploy, and post-deploy health |

Environments-update jobs run inside the matching GitHub environment so staging/production (and feature) changes can require manual approval before values are pushed.

Fork PRs run static analysis and tests only; image push, environments updates, and deploy are skipped for untrusted forks.

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
