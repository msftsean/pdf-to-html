"""
Unit tests for status_service — T020

Tests the Azure Blob-backed status tracking service.
All Azure Blob interactions are mocked — no real Azure
credentials needed.

The service uses _find_blob_by_id() which scans blobs by metadata
document_id, then reads/writes metadata on the matching blob.

Validates:
  - set_status (blob metadata writes)
  - get_status (retrieval + not-found)
  - list_documents (enumeration + empty)
  - get_summary (status counting)
  - State transitions (pending → processing → completed/failed)
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

import pytest

from backend.models import Document, DocumentStatus
from backend.status_service import get_status, get_summary, list_documents, set_status, _find_blob_by_id


# ---------------------------------------------------------------------------
# Helpers — mock blob objects matching Azure SDK shapes
# ---------------------------------------------------------------------------


def _make_blob_item(doc_id: str, status: str = "pending", **extra_meta) -> MagicMock:
    """Build a mock blob item as returned by container_client.list_blobs()."""
    blob = MagicMock()
    blob.name = f"{doc_id}.pdf"
    metadata = {
        "document_id": doc_id,
        "name": f"report-{doc_id}",
        "format": "pdf",
        "size_bytes": "1024",
        "upload_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "error_message": "",
        "page_count": "",
        "pages_processed": "0",
        "has_review_flags": "false",
        "blob_path": f"files/{doc_id}.pdf",
        "output_path": "",
    }
    metadata.update(extra_meta)
    blob.metadata = metadata
    return blob


def _make_blob_properties(doc_id: str, status: str = "pending", **extra_meta) -> MagicMock:
    """Build mock blob properties as returned by blob_client.get_blob_properties()."""
    props = MagicMock()
    metadata = {
        "document_id": doc_id,
        "name": f"report-{doc_id}",
        "format": "pdf",
        "size_bytes": "1024",
        "upload_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "error_message": "",
        "page_count": "",
        "pages_processed": "0",
        "has_review_flags": "false",
        "blob_path": f"files/{doc_id}.pdf",
        "output_path": "",
    }
    metadata.update(extra_meta)
    props.metadata = metadata
    return props


# ---------------------------------------------------------------------------
# Fixtures — wire up the blob service mock chain
# ---------------------------------------------------------------------------


@pytest.fixture
def blob_mocks():
    """Create a fully wired blob service mock that simulates _find_blob_by_id
    scanning and blob client access.  Returns (blob_service, container_client,
    blob_client) so tests can configure list_blobs and blob_client responses."""
    blob_service = MagicMock()
    container_client = MagicMock()
    blob_client = MagicMock()

    blob_service.get_container_client.return_value = container_client
    container_client.get_blob_client.return_value = blob_client

    return blob_service, container_client, blob_client


# ---------------------------------------------------------------------------
# set_status
# ---------------------------------------------------------------------------


class TestSetStatus:
    """Tests for status_service.set_status."""

    def test_set_status_updates_blob_metadata(self, blob_mocks):
        """set_status should find the blob and write updated metadata."""
        blob_service, container_client, blob_client = blob_mocks

        # _find_blob_by_id scans list_blobs(name_starts_with=doc_id) first
        blob_item = _make_blob_item("doc-001", status="pending")
        container_client.list_blobs.return_value = [blob_item]

        # get_blob_properties returns existing metadata
        blob_client.get_blob_properties.return_value = _make_blob_properties(
            "doc-001", status="pending"
        )

        set_status(blob_service, "doc-001", "processing")

        # Verify the metadata was updated on the blob
        blob_client.set_blob_metadata.assert_called_once()
        written_metadata = blob_client.set_blob_metadata.call_args[0][0]
        assert written_metadata["status"] == "processing"


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestGetStatus:
    """Tests for status_service.get_status."""

    def test_get_status_returns_document(self, blob_mocks):
        """get_status should return a Document when the blob exists."""
        blob_service, container_client, blob_client = blob_mocks

        blob_item = _make_blob_item("doc-001", status="processing")
        container_client.list_blobs.return_value = [blob_item]
        blob_client.get_blob_properties.return_value = _make_blob_properties(
            "doc-001", status="processing"
        )

        result = get_status(blob_service, "doc-001")

        assert result is not None
        assert isinstance(result, Document)
        assert result.id == "doc-001"
        assert result.status == DocumentStatus.PROCESSING.value  # "processing"

    def test_get_status_not_found_returns_none(self, blob_mocks):
        """get_status should return None when no blob matches the document_id."""
        blob_service, container_client, blob_client = blob_mocks

        # _find_blob_by_id returns None when no blobs match
        container_client.list_blobs.return_value = []

        result = get_status(blob_service, "nonexistent-id")

        assert result is None


# ---------------------------------------------------------------------------
# list_documents
# ---------------------------------------------------------------------------


class TestListDocuments:
    """Tests for status_service.list_documents."""

    def test_list_documents_returns_all(self, blob_mocks):
        """list_documents should return a list of Document objects."""
        blob_service, container_client, _ = blob_mocks

        blob1 = _make_blob_item("doc-001", status="pending")
        blob2 = _make_blob_item("doc-002", status="completed")
        container_client.list_blobs.return_value = [blob1, blob2]

        results = list_documents(blob_service)

        assert isinstance(results, list)
        assert len(results) == 2
        ids = {d.id for d in results}
        assert "doc-001" in ids
        assert "doc-002" in ids

    def test_list_documents_empty_container(self, blob_mocks):
        """list_documents should return an empty list when no blobs exist."""
        blob_service, container_client, _ = blob_mocks
        container_client.list_blobs.return_value = []

        results = list_documents(blob_service)

        assert results == []


# ---------------------------------------------------------------------------
# get_summary
# ---------------------------------------------------------------------------


class TestGetSummary:
    """Tests for status_service.get_summary."""

    def test_get_summary_counts_statuses(self, blob_mocks):
        """get_summary should return correct counts per status."""
        blob_service, container_client, _ = blob_mocks

        blobs = [
            _make_blob_item("d1", status="pending"),
            _make_blob_item("d2", status="processing"),
            _make_blob_item("d3", status="completed"),
            _make_blob_item("d4", status="completed"),
            _make_blob_item("d5", status="failed"),
        ]
        container_client.list_blobs.return_value = blobs

        summary = get_summary(blob_service)

        assert isinstance(summary, dict)
        assert summary["total"] == 5
        assert summary["pending"] == 1
        assert summary["processing"] == 1
        assert summary["completed"] == 2
        assert summary["failed"] == 1

    def test_get_summary_empty(self, blob_mocks):
        """get_summary with no documents should return all zeros."""
        blob_service, container_client, _ = blob_mocks
        container_client.list_blobs.return_value = []

        summary = get_summary(blob_service)

        assert summary["total"] == 0
        assert summary["pending"] == 0
        assert summary["processing"] == 0
        assert summary["completed"] == 0
        assert summary["failed"] == 0


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------


class TestStatusTransitions:
    """Validate legal status transitions per the data-model spec:

        pending → processing → completed
                             → failed
    """

    def test_status_transitions_pending_to_processing(self, blob_mocks):
        """A document in 'pending' should transition to 'processing'."""
        blob_service, container_client, blob_client = blob_mocks

        blob_item = _make_blob_item("doc-t1", status="pending")
        container_client.list_blobs.return_value = [blob_item]
        blob_client.get_blob_properties.return_value = _make_blob_properties(
            "doc-t1", status="pending"
        )

        set_status(blob_service, "doc-t1", "processing")

        blob_client.set_blob_metadata.assert_called()
        written = blob_client.set_blob_metadata.call_args[0][0]
        assert written["status"] == "processing"

    def test_status_transitions_processing_to_completed(self, blob_mocks):
        """A document in 'processing' should transition to 'completed'."""
        blob_service, container_client, blob_client = blob_mocks

        blob_item = _make_blob_item("doc-t2", status="processing")
        container_client.list_blobs.return_value = [blob_item]
        blob_client.get_blob_properties.return_value = _make_blob_properties(
            "doc-t2", status="processing"
        )

        set_status(
            blob_service,
            "doc-t2",
            "completed",
            output_path="converted/doc-t2.html",
        )

        blob_client.set_blob_metadata.assert_called()
        written = blob_client.set_blob_metadata.call_args[0][0]
        assert written["status"] == "completed"
        assert written["output_path"] == "converted/doc-t2.html"

    def test_status_transitions_processing_to_failed(self, blob_mocks):
        """A document in 'processing' should transition to 'failed' with
        an error message."""
        blob_service, container_client, blob_client = blob_mocks

        blob_item = _make_blob_item("doc-t3", status="processing")
        container_client.list_blobs.return_value = [blob_item]
        blob_client.get_blob_properties.return_value = _make_blob_properties(
            "doc-t3", status="processing"
        )

        set_status(
            blob_service,
            "doc-t3",
            "failed",
            error_message="OCR service timeout",
        )

        blob_client.set_blob_metadata.assert_called()
        written = blob_client.set_blob_metadata.call_args[0][0]
        assert written["status"] == "failed"
        assert written["error_message"] == "OCR service timeout"


# ---------------------------------------------------------------------------
# _find_blob_by_id — metadata-missing fallback (SAS overwrite bug fix)
# ---------------------------------------------------------------------------


class TestFindBlobByIdFallback:
    """Tests for _find_blob_by_id fallback when metadata is wiped by SAS upload."""

    def test_finds_blob_with_metadata(self, blob_mocks):
        """Fast path: blob has valid document_id metadata."""
        blob_service, container_client, blob_client = blob_mocks

        blob_item = _make_blob_item("doc-abc", status="pending")
        # First call (prefix scan with metadata) returns match
        container_client.list_blobs.return_value = [blob_item]

        result = _find_blob_by_id(blob_service, "doc-abc")

        assert result is not None
        container_client.get_blob_client.assert_called_with("doc-abc.pdf")

    def test_finds_blob_without_metadata_via_name_fallback(self, blob_mocks):
        """Fallback: blob exists by name but has NO metadata (SAS overwrite)."""
        blob_service, container_client, blob_client = blob_mocks

        # First call (prefix + metadata): blob found but metadata doesn't match
        blob_no_meta = MagicMock()
        blob_no_meta.name = "doc-xyz.pdf"
        blob_no_meta.metadata = {}  # wiped by SAS upload

        # First list_blobs call (with include=["metadata"]) — no match on metadata
        # Second list_blobs call (without include) — name-based fallback
        container_client.list_blobs.side_effect = [
            [blob_no_meta],  # prefix scan w/ metadata — doc_id not in metadata
            [blob_no_meta],  # prefix scan w/o metadata — name match
        ]

        result = _find_blob_by_id(blob_service, "doc-xyz")

        assert result is not None
        container_client.get_blob_client.assert_called_with("doc-xyz.pdf")

    def test_returns_none_when_no_blobs_exist(self, blob_mocks):
        """Returns None when no blob matches at all."""
        blob_service, container_client, blob_client = blob_mocks

        container_client.list_blobs.return_value = []

        result = _find_blob_by_id(blob_service, "nonexistent")

        assert result is None
