# Data Model: Azure Container Apps Migration

**Phase 1 Output** | **Date**: 2026-06-15

## Overview

This migration does **not** introduce new persistent entities. The existing
data model (Document status in blob metadata, PageResult pipeline objects)
is unchanged. This document defines the **new infrastructure entities** and
**message schemas** introduced by the Container Apps architecture.

## Existing Entities (Unchanged)

### Document (blob metadata — no database)

Stored as flat string key-value pairs on blobs in `files/` container.
**No changes.** See `specs/001-sean/data-model.md` for full schema.

| Field | Type | Description |
|-------|------|-------------|
| document_id | string (UUID) | Unique identifier |
| name | string | Original filename |
| format | string | pdf, docx, pptx |
| status | string | pending → processing → completed / failed |
| size_bytes | string | File size |
| page_count | string | Total pages (nullable) |
| output_path | string | Path in `converted/` container |
| ... | ... | (15 total metadata fields, see 001-sean) |

**State transitions** (unchanged):
```
pending → processing → completed
                    → failed
```

### PageResult, TextSpan, ImageInfo, TableData (pipeline objects)

In-memory data classes. **No changes.** See `backend/models.py`.

---

## New Entities

### QueueMessage

Message placed on `conversion-jobs` Azure Storage Queue by Event Grid
subscription when a blob is created in `files/` container.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| blob_name | string | Yes | Full blob name (e.g., `abc123.pdf`) |
| container | string | Yes | Source container (always `files`) |
| document_id | string | Yes | UUID extracted from blob name |
| content_type | string | Yes | MIME type from Event Grid event |
| size_bytes | integer | Yes | File size from Event Grid event |
| timestamp | string (ISO 8601) | Yes | Event timestamp |
| source | string | No | Event Grid topic identifier |

**Lifecycle**:
```
Event Grid BlobCreated event
  → Event Grid subscription transforms to QueueMessage
  → Enqueued to `conversion-jobs` queue
  → Worker dequeues (visibility timeout: 5 minutes)
  → Worker processes blob
  → On success: message deleted
  → On failure: message becomes visible again after timeout
  → After 3 failed attempts: moved to `conversion-jobs-poison` queue
```

**Validation rules**:
- `blob_name` must end with `.pdf`, `.docx`, or `.pptx`
- `size_bytes` must be > 0 (Event Grid filter handles 0-byte placeholders)
- `container` must be `files`

### ContainerAppRevision

Represents a deployment revision in Azure Container Apps. Not stored in
application code — managed by Azure. Documented here for operational context.

| Field | Type | Description |
|-------|------|-------------|
| revision_name | string | Auto-generated (e.g., `api--abc123`) |
| image | string | Full ACR image reference with tag/SHA |
| traffic_weight | integer (0-100) | Percentage of traffic routed here |
| active | boolean | Whether revision is accepting traffic |
| created_time | datetime | When revision was created |
| health_status | enum | Healthy, Unhealthy, Degraded |

---

## Infrastructure Entities

### Azure Container App: `api`

| Property | Value |
|----------|-------|
| Name | `ca-pdftohtml-api` |
| Image | `<acr>.azurecr.io/pdf-to-html-api:<sha>` |
| Port | 8000 |
| Min replicas | 1 |
| Max replicas | 5 |
| Scale rule | HTTP concurrent requests (10 per replica) |
| Health probe | `GET /health` → 200 |
| Ingress | External (HTTPS, port 8000) |

### Azure Container App: `worker`

| Property | Value |
|----------|-------|
| Name | `ca-pdftohtml-worker` |
| Image | `<acr>.azurecr.io/pdf-to-html-api:<sha>` (same image) |
| Entrypoint | `python -m app.worker` |
| Min replicas | 0 (scale to zero) |
| Max replicas | 10 |
| Scale rule | KEDA `azure-queue` (queue length = 1 per replica) |
| Ingress | None (no HTTP traffic) |

### Azure Container App: `frontend`

| Property | Value |
|----------|-------|
| Name | `ca-pdftohtml-frontend` |
| Image | `<acr>.azurecr.io/pdf-to-html-frontend:<sha>` |
| Port | 3000 |
| Min replicas | 1 |
| Max replicas | 3 |
| Scale rule | HTTP concurrent requests (50 per replica) |
| Health probe | `GET /` → 200 |
| Ingress | External (HTTPS, port 3000) |
| Env | `BACKEND_URL=https://ca-pdftohtml-api.<env>.azurecontainerapps.io` |

### Azure Container Registry

| Property | Value |
|----------|-------|
| Name | `crpdftohtml` |
| SKU | Basic |
| Admin enabled | No (use managed identity) |
| Repositories | `pdf-to-html-api`, `pdf-to-html-frontend` |

### Azure Storage Queue

| Property | Value |
|----------|-------|
| Name | `conversion-jobs` |
| Storage Account | `stpdftohtml331ef3` (existing) |
| Poison Queue | `conversion-jobs-poison` (auto-created) |
| Visibility Timeout | 300 seconds (5 minutes) |
| Message TTL | 7 days |
| Max Dequeue Count | 3 |

### Event Grid System Topic

| Property | Value |
|----------|-------|
| Name | `evgt-pdftohtml-storage` |
| Source | `stpdftohtml331ef3` storage account |
| Topic Type | `Microsoft.Storage.StorageAccounts` |

### Event Grid Subscription

| Property | Value |
|----------|-------|
| Name | `evgs-pdftohtml-blobcreated` |
| Event Types | `Microsoft.Storage.BlobCreated` |
| Subject Filter | `/blobServices/default/containers/files/` |
| Endpoint Type | Storage Queue |
| Endpoint | `conversion-jobs` queue |
| Advanced Filter | `data.contentLength > 0` |

---

## Environment Variables

### Backend (API + Worker) Container

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `AZURE_STORAGE_CONNECTION_STRING` | Yes | `DefaultEndpoints...` | Blob + Queue access |
| `DOCUMENT_INTELLIGENCE_ENDPOINT` | Yes (prod) | `https://di-pdftohtml.cognitiveservices.azure.com/` | OCR service |
| `DOCUMENT_INTELLIGENCE_KEY` | Yes (prod) | `abc123...` | OCR API key |
| `OUTPUT_CONTAINER` | No | `converted` | Output container (default: converted) |
| `INPUT_CONTAINER` | No | `files` | Input container (default: files) |
| `QUEUE_NAME` | No | `conversion-jobs` | Job queue (default: conversion-jobs) |
| `PORT` | No | `8000` | HTTP port (default: 8000) |
| `WORKER_MODE` | No | `true` | Run as queue worker instead of API |
| `LOG_LEVEL` | No | `INFO` | Python logging level |

### Frontend Container

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `BACKEND_URL` | Yes | `https://ca-pdftohtml-api...` | Backend API URL for rewrites |
| `PORT` | No | `3000` | HTTP port (default: 3000) |
