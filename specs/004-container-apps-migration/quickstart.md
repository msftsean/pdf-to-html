# Quickstart: Container Apps Migration Development

**Phase 1 Output** | **Date**: 2026-06-15

## Prerequisites

- Docker Desktop (or Podman) with docker-compose
- Python 3.12+ (for running tests outside containers)
- Node.js 20+ (for frontend development)
- Azure CLI (`az`) with Container Apps extension
- Git

## Local Development

### 1. Clone and Configure

```bash
git clone <repo-url>
cd pdf-to-html
git checkout 004-container-apps-migration
cp .env.example .env
```

### 2. Start All Services

```bash
docker-compose up --build
```

This starts three services:

| Service | Port | Description |
|---------|------|-------------|
| `azurite` | 10000, 10001, 10002 | Azure Storage emulator (blob + queue + table) |
| `backend` | 8000 | FastAPI backend (Uvicorn with hot-reload) |
| `frontend` | 3000 | Next.js frontend |

### 3. Verify

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend
open http://localhost:3000
```

### 4. Upload a Test File

```bash
# Request SAS token
curl -X POST http://localhost:8000/api/upload/sas-token \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.pdf", "content_type": "application/pdf", "size_bytes": 1024}'

# Upload file to the returned upload_url
curl -X PUT "<upload_url>" \
  -H "x-ms-blob-type: BlockBlob" \
  -H "Content-Type: application/pdf" \
  --data-binary @test.pdf

# Check status
curl http://localhost:8000/api/documents/status
```

### 5. Hot Reload

- **Backend**: Edit any file in `backend/` or `app/` → Uvicorn auto-reloads
- **Frontend**: Edit any file in `frontend/` → Next.js auto-reloads
- **Queue worker**: Runs in the backend container; restarts with Uvicorn

---

## docker-compose.yml Structure

```yaml
version: '3.8'

services:
  azurite:
    image: mcr.microsoft.com/azure-storage/azurite
    command: >
      azurite --loose --blobHost 0.0.0.0 --blobPort 10000
              --queueHost 0.0.0.0 --queuePort 10001
              --tableHost 0.0.0.0 --tablePort 10002
              --location /data --debug /data/debug.log
              --skipApiVersionCheck
    ports:
      - "10000:10000"
      - "10001:10001"
      - "10002:10002"
    volumes:
      - azurite-data:/data

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      AZURE_STORAGE_CONNECTION_STRING: >-
        DefaultEndpointsProtocol=http;
        AccountName=devstoreaccount1;
        AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;
        BlobEndpoint=http://azurite:10000/devstoreaccount1;
        QueueEndpoint=http://azurite:10001/devstoreaccount1;
      OUTPUT_CONTAINER: converted
      INPUT_CONTAINER: files
      QUEUE_NAME: conversion-jobs
      LOG_LEVEL: DEBUG
      WORKER_MODE: "false"
    volumes:
      - ./backend:/app/backend
      - ./app:/app/app
    depends_on:
      - azurite
    command: >
      uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      AZURE_STORAGE_CONNECTION_STRING: >-
        DefaultEndpointsProtocol=http;
        AccountName=devstoreaccount1;
        AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;
        BlobEndpoint=http://azurite:10000/devstoreaccount1;
        QueueEndpoint=http://azurite:10001/devstoreaccount1;
      OUTPUT_CONTAINER: converted
      INPUT_CONTAINER: files
      QUEUE_NAME: conversion-jobs
      LOG_LEVEL: DEBUG
    volumes:
      - ./backend:/app/backend
      - ./app:/app/app
    depends_on:
      - azurite
    command: >
      python -m app.worker

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      BACKEND_URL: http://backend:8000
    depends_on:
      - backend

volumes:
  azurite-data:
```

---

## Running Tests

### Backend Tests (outside container)

```bash
# Install dependencies
pip install -r requirements.txt

# All tests (existing tests should pass without changes)
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest tests/ -v --cov=backend --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm install
npm test
npm run lint
```

---

## Project Structure (Post-Migration)

```
pdf-to-html/
├── app/                          # NEW: FastAPI application
│   ├── __init__.py
│   ├── main.py                   # FastAPI app + HTTP routes
│   ├── worker.py                 # Queue consumer (replaces blob trigger)
│   ├── dependencies.py           # Dependency injection (blob client, etc.)
│   ├── config.py                 # Environment variable config
│   └── models.py                 # Pydantic request/response models
├── backend/                      # UNCHANGED: Core pipeline
│   ├── pdf_extractor.py
│   ├── docx_extractor.py
│   ├── pptx_extractor.py
│   ├── ocr_service.py
│   ├── html_builder.py
│   ├── wcag_validator.py
│   ├── status_service.py
│   └── models.py
├── frontend/                     # MINIMAL CHANGES
│   ├── Dockerfile                # NEW: Multi-stage build
│   └── ...                       # Existing Next.js app
├── tests/                        # UPDATED: Test imports
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── Dockerfile.backend            # NEW: Python backend image
├── docker-compose.yml            # NEW: Local dev orchestration
├── function_app.py               # DEPRECATED (kept for reference)
├── requirements.txt              # UPDATED: +fastapi +uvicorn, -azure-functions
├── infra/                        # NEW: Infrastructure as code
│   ├── main.bicep                # Container Apps + ACR + Event Grid
│   ├── modules/
│   │   ├── container-apps.bicep
│   │   ├── container-registry.bicep
│   │   └── event-grid.bicep
│   └── parameters/
│       ├── dev.bicepparam
│       └── prod.bicepparam
└── .github/
    └── workflows/
        ├── ci.yml                # UPDATED: Build + push + deploy
        └── eval.yml              # UPDATED: Run in container
```

---

## Deployment

### First-Time Setup

```bash
# Create Container Apps Environment
az containerapp env create \
  --name cae-pdftohtml \
  --resource-group rg-pdftohtml \
  --location eastus

# Create ACR
az acr create \
  --name crpdftohtml \
  --resource-group rg-pdftohtml \
  --sku Basic

# Build and push backend image
az acr build \
  --registry crpdftohtml \
  --image pdf-to-html-api:latest \
  --file Dockerfile.backend .

# Create API Container App
az containerapp create \
  --name ca-pdftohtml-api \
  --resource-group rg-pdftohtml \
  --environment cae-pdftohtml \
  --image crpdftohtml.azurecr.io/pdf-to-html-api:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 5

# Create Worker Container App
az containerapp create \
  --name ca-pdftohtml-worker \
  --resource-group rg-pdftohtml \
  --environment cae-pdftohtml \
  --image crpdftohtml.azurecr.io/pdf-to-html-api:latest \
  --min-replicas 0 \
  --max-replicas 10 \
  --scale-rule-name queue-scaling \
  --scale-rule-type azure-queue \
  --scale-rule-metadata "queueName=conversion-jobs" "queueLength=1" \
  --scale-rule-auth "connection=queue-connection-string" \
  --command "python" "-m" "app.worker"
```

### Subsequent Deploys (~30s)

```bash
# Build + push
az acr build --registry crpdftohtml --image pdf-to-html-api:$(git rev-parse --short HEAD) .

# Update revision
az containerapp update \
  --name ca-pdftohtml-api \
  --resource-group rg-pdftohtml \
  --image crpdftohtml.azurecr.io/pdf-to-html-api:$(git rev-parse --short HEAD)
```
