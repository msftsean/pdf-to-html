"""
Document processing status tracking via Azure Blob Storage metadata.

Each uploaded document is tracked by storing metadata on its blob in the
``files/`` container.  This avoids a separate database — the blob itself
is the source of truth for document lifecycle state.
"""

from __future__ import annotations

import logging
from typing import Any

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

from .models import Document, DocumentStatus

logger = logging.getLogger(__name__)

# Container where raw uploads are stored (must match function_app.py trigger)
_INPUT_CONTAINER = "files"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def set_status(
    blob_service: BlobServiceClient,
    document_id: str,
    status: str,
    **kwargs: Any,
) -> None:
    """Update the processing status (and optional extra fields) on a document blob.

    Args:
        blob_service: An authenticated ``BlobServiceClient``.
        document_id: The UUID identifying the document.
        status: New status value (must be a valid ``DocumentStatus``).
        **kwargs: Additional metadata fields to set (e.g. ``page_count=10``).

    Raises:
        ValueError: If *status* is not a recognised ``DocumentStatus`` value.
        azure.core.exceptions.ResourceNotFoundError: If the blob does not exist.
    """
    # Validate the target status
    try:
        DocumentStatus(status)
    except ValueError:
        raise ValueError(
            f"Invalid status '{status}'. Must be one of "
            f"{[s.value for s in DocumentStatus]}"
        )

    blob_client = _find_blob_by_id(blob_service, document_id)
    if blob_client is None:
        logger.warning("set_status: blob not found for document_id=%s", document_id)
        return

    # Read existing metadata, merge in updates
    props = blob_client.get_blob_properties()
    metadata: dict[str, str] = dict(props.metadata or {})

    metadata["status"] = status
    for key, value in kwargs.items():
        metadata[key] = str(value) if value is not None else ""

    blob_client.set_blob_metadata(metadata)
    logger.info("Updated document %s → status=%s", document_id, status)


def get_status(
    blob_service: BlobServiceClient,
    document_id: str,
) -> Document | None:
    """Read the status of a single document by its UUID.

    Returns:
        A ``Document`` populated from blob metadata, or ``None`` if not found.
    """
    blob_client = _find_blob_by_id(blob_service, document_id)
    if blob_client is None:
        return None

    props = blob_client.get_blob_properties()
    metadata = dict(props.metadata or {})
    return Document.from_metadata(document_id, metadata)


def list_documents(
    blob_service: BlobServiceClient,
) -> list[Document]:
    """List every tracked document in the input container.

    Scans all blobs under ``files/`` and reads their metadata.  This is
    suitable for the current scale (< 1 000 documents); if the project
    grows significantly, add paging or an index.
    """
    container_client = blob_service.get_container_client(_INPUT_CONTAINER)
    documents: list[Document] = []

    try:
        for blob in container_client.list_blobs(include=["metadata"]):
            metadata = dict(blob.metadata or {}) if blob.metadata else {}
            # Only include blobs that have been registered via the SAS flow
            # (they will have a "status" metadata key set by generate_sas_token)
            if "status" not in metadata:
                continue

            # Derive document_id — stored explicitly or fall back to blob name
            doc_id = metadata.get("document_id", blob.name)
            doc = Document.from_metadata(doc_id, metadata)
            # Fill in blob_path if not already set
            if not doc.blob_path:
                doc.blob_path = blob.name
            documents.append(doc)
    except Exception:
        logger.exception("Failed to list documents in container '%s'", _INPUT_CONTAINER)

    return documents


def get_summary(
    blob_service: BlobServiceClient,
) -> dict[str, int]:
    """Return aggregate counts of documents by status.

    Returns a dict matching the status API summary shape::

        {"total": 15, "pending": 3, "processing": 2, "completed": 9, "failed": 1}
    """
    documents = list_documents(blob_service)
    summary: dict[str, int] = {
        "total": len(documents),
        "pending": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0,
    }
    for doc in documents:
        if doc.status in summary:
            summary[doc.status] += 1
    return summary


def get_batch_summary(
    blob_service: BlobServiceClient,
    documents: list[Document] | None = None,
) -> dict[str, int]:
    """Return aggregate batch-processing counts by status.

    When *documents* is provided the counts are computed from the list
    directly — this avoids a redundant blob scan when the caller already
    has the full document list (e.g. the status API endpoint that also
    returns the list).

    Returns a dict matching the batch summary shape::

        {"total": 15, "pending": 3, "processing": 2, "completed": 9, "failed": 1}
    """
    if documents is None:
        documents = list_documents(blob_service)

    summary: dict[str, int] = {
        "total": len(documents),
        "pending": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0,
    }
    for doc in documents:
        if doc.status in summary:
            summary[doc.status] += 1
    return summary


def delete_document(
    blob_service: BlobServiceClient,
    document_id: str,
    output_container: str = "converted",
) -> dict[str, Any]:
    """Delete a document and all its conversion output from storage.

    Locates the input blob in the ``files`` container using
    :func:`_find_blob_by_id`, reads its metadata to derive the output
    prefix, deletes all output blobs (HTML + images), then deletes the
    input blob itself.

    Args:
        blob_service: An authenticated ``BlobServiceClient``.
        document_id: The UUID identifying the document.
        output_container: Name of the output container (default ``"converted"``).

    Returns:
        ``{"deleted": True, "document_id": str, "blobs_removed": int}``

    Raises:
        azure.core.exceptions.ResourceNotFoundError: If the document blob
            does not exist in the input container.
    """
    blob_client = _find_blob_by_id(blob_service, document_id)
    if blob_client is None:
        raise ResourceNotFoundError(f"Document '{document_id}' not found")

    # Read metadata to derive the output prefix
    props = blob_client.get_blob_properties()
    metadata = dict(props.metadata or {})
    output_path = metadata.get("output_path", "")

    # Derive the directory prefix under which output blobs are stored.
    # output_path is typically "converted/<doc_id>/<doc_id>.html".
    if output_path:
        prefix_part = output_path
        if prefix_part.startswith(output_container + "/"):
            prefix_part = prefix_part[len(output_container) + 1:]
        # "uuid/uuid.html" → prefix "uuid/"
        if "/" in prefix_part:
            output_prefix = prefix_part.split("/")[0] + "/"
        else:
            output_prefix = document_id + "/"
    else:
        # Fallback: use document_id (matches blob trigger naming convention)
        output_prefix = document_id + "/"

    blobs_removed = 0

    # Delete all output blobs under the prefix
    try:
        output_client = blob_service.get_container_client(output_container)
        for blob in output_client.list_blobs(name_starts_with=output_prefix):
            output_client.delete_blob(blob.name)
            blobs_removed += 1
            logger.debug("Deleted output blob: %s/%s", output_container, blob.name)
    except Exception:
        logger.warning(
            "Could not delete output blobs for document_id=%s prefix='%s'",
            document_id,
            output_prefix,
        )

    # Delete the input blob
    blob_client.delete_blob()
    blobs_removed += 1

    logger.info("Deleted document %s (%d blobs removed)", document_id, blobs_removed)

    return {
        "deleted": True,
        "document_id": document_id,
        "blobs_removed": blobs_removed,
    }


def delete_all_documents(
    blob_service: BlobServiceClient,
    output_container: str = "converted",
) -> dict[str, int]:
    """Delete every document from the input and output containers.

    Iterates all blobs in the ``files`` container and the
    *output_container*, deleting each one.

    Args:
        blob_service: An authenticated ``BlobServiceClient``.
        output_container: Name of the output container (default ``"converted"``).

    Returns:
        ``{"deleted_input": int, "deleted_output": int}`` with per-container
        deletion counts.
    """
    deleted_input = 0
    deleted_output = 0

    # Delete all input blobs
    input_client = blob_service.get_container_client(_INPUT_CONTAINER)
    try:
        for blob in input_client.list_blobs():
            input_client.delete_blob(blob.name)
            deleted_input += 1
    except Exception:
        logger.exception("Error deleting blobs from '%s'", _INPUT_CONTAINER)

    # Delete all output blobs
    output_client = blob_service.get_container_client(output_container)
    try:
        for blob in output_client.list_blobs():
            output_client.delete_blob(blob.name)
            deleted_output += 1
    except Exception:
        logger.exception("Error deleting blobs from '%s'", output_container)

    logger.info(
        "Deleted all documents: %d input, %d output",
        deleted_input,
        deleted_output,
    )

    return {
        "deleted_input": deleted_input,
        "deleted_output": deleted_output,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_blob_by_id(
    blob_service: BlobServiceClient,
    document_id: str,
):
    """Locate the blob whose metadata ``document_id`` matches *document_id*.

    The upload flow names blobs ``files/<document_id>.<ext>`` so we first try
    a prefix scan.  Falls back to matching by blob name prefix even when
    metadata is missing (e.g. wiped by SAS upload overwrite), then to a full
    scan if the prefix doesn't match.
    """
    container_client = blob_service.get_container_client(_INPUT_CONTAINER)

    # Fast path: blob name starts with the document_id, metadata matches
    for blob in container_client.list_blobs(name_starts_with=document_id, include=["metadata"]):
        metadata = dict(blob.metadata or {}) if blob.metadata else {}
        if metadata.get("document_id") == document_id:
            return container_client.get_blob_client(blob.name)

    # Fallback: blob name starts with document_id but metadata may be missing
    # (covers the case where SAS upload overwrote the placeholder and wiped metadata)
    for blob in container_client.list_blobs(name_starts_with=document_id):
        return container_client.get_blob_client(blob.name)

    # Slow path: scan all blobs (only needed if naming convention differs)
    for blob in container_client.list_blobs(include=["metadata"]):
        metadata = dict(blob.metadata or {}) if blob.metadata else {}
        if metadata.get("document_id") == document_id:
            return container_client.get_blob_client(blob.name)

    return None
