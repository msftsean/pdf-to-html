"""
Pydantic request / response models for the FastAPI endpoints.

Every model mirrors the EXACT JSON shape returned by the original
``function_app.py`` Azure Functions implementation so the frontend
integration is fully backwards-compatible.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


# ---------------------------------------------------------------------------
# Upload (SAS token generation)
# ---------------------------------------------------------------------------

class SasTokenRequest(BaseModel):
    """POST /upload/sas-token request body."""
    filename: str
    content_type: str
    size_bytes: int = Field(..., gt=0)


class SasTokenResponse(BaseModel):
    """POST /upload/sas-token response body."""
    document_id: str
    upload_url: str
    expires_at: str
    metadata: dict[str, str] | None = None


# ---------------------------------------------------------------------------
# Document status
# ---------------------------------------------------------------------------

class DocumentStatusResponse(BaseModel):
    """GET /documents/status?document_id=<id> — single-document shape."""
    document_id: str
    name: str
    format: str
    size_bytes: int
    upload_timestamp: str
    status: str
    error_message: str | None = None
    page_count: int | None = None
    pages_processed: int = 0
    has_review_flags: bool = False
    review_pages: list[int] = Field(default_factory=list)
    processing_time_ms: int | None = None
    is_compliant: bool | None = None


class StatusListResponse(BaseModel):
    """GET /documents/status (no query param) — list shape."""
    documents: list[DocumentStatusResponse]
    summary: dict[str, Any]
    batch_summary: dict[str, Any]


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

class DownloadAsset(BaseModel):
    """A single image asset inside a download response."""
    filename: str
    url: str
    size_bytes: int = 0


class DownloadResponse(BaseModel):
    """GET /documents/{document_id}/download response body."""
    document_id: str
    name: str
    html_url: str
    preview_url: str
    assets: list[DownloadAsset] = Field(default_factory=list)
    zip_url: str
    wcag_compliant: bool = True
    review_pages: list[int] = Field(default_factory=list)
    expires_at: str
    # Frontend-compatible aliases (downloadService.ts expects these)
    download_url: str
    filename: str
    image_urls: list[str] | None = None


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

class DeleteResponse(BaseModel):
    """DELETE /documents/{document_id} response body."""
    message: str
    document_id: str
    blobs_removed: int


class DeleteAllResponse(BaseModel):
    """DELETE /documents response body."""
    message: str
    deleted_input: int
    deleted_output: int


# ---------------------------------------------------------------------------
# Health / readiness
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """GET /health response body."""
    status: str
    version: str
    checks: dict[str, str]


class ReadyResponse(BaseModel):
    """GET /ready response body."""
    status: str


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """Standard error envelope returned by all endpoints."""
    error: str
