"""
Integration tests for batch processing — T044 & T047

Validates:
  - Multiple documents are tracked independently (T044)
  - Failure isolation — one document failing doesn't affect others (T044)
  - Concurrent / stateless execution — no shared state between
    blob-trigger invocations (T047)

All Azure Blob Storage interactions are mocked; no credentials required.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from models import Document, DocumentStatus
from status_service import (
    get_batch_summary,
    get_status,
    list_documents,
    set_status,
)


# ---------------------------------------------------------------------------
# Helpers — mock blob objects matching Azure SDK shapes
# ---------------------------------------------------------------------------


def _make_blob_item(
    doc_id: str,
    status: str = "pending",
    **extra_meta: str,
) -> MagicMock:
    """Build a mock blob item as returned by ``container_client.list_blobs()``."""
    blob = MagicMock()
    blob.name = f"{doc_id}.pdf"
    metadata = {
        "document_id": doc_id,
        "name": f"doc-{doc_id}",
        "format": "pdf",
        "size_bytes": "2048",
        "upload_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "error_message": "",
        "page_count": "",
        "pages_processed": "0",
        "has_review_flags": "false",
        "blob_path": f"files/{doc_id}.pdf",
        "output_path": "",
        "review_pages": "[]",
        "processing_time_ms": "",
        "is_compliant": "",
    }
    metadata.update(extra_meta)
    blob.metadata = metadata
    return blob


def _make_blob_properties(
    doc_id: str,
    status: str = "pending",
    **extra_meta: str,
) -> MagicMock:
    """Build mock blob properties as returned by ``blob_client.get_blob_properties()``."""
    props = MagicMock()
    metadata = {
        "document_id": doc_id,
        "name": f"doc-{doc_id}",
        "format": "pdf",
        "size_bytes": "2048",
        "upload_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "error_message": "",
        "page_count": "",
        "pages_processed": "0",
        "has_review_flags": "false",
        "blob_path": f"files/{doc_id}.pdf",
        "output_path": "",
        "review_pages": "[]",
        "processing_time_ms": "",
        "is_compliant": "",
    }
    metadata.update(extra_meta)
    props.metadata = metadata
    return props


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def batch_blob_mocks():
    """Create a fully wired blob service mock for batch processing tests.

    Returns ``(blob_service, container_client, blob_client)`` so tests
    can configure ``list_blobs`` and ``blob_client`` responses.
    """
    blob_service = MagicMock()
    container_client = MagicMock()
    blob_client = MagicMock()

    blob_service.get_container_client.return_value = container_client
    container_client.get_blob_client.return_value = blob_client

    return blob_service, container_client, blob_client


# ===================================================================
# T044 — Batch processing integration tests
# ===================================================================


class TestBatchProcessingIndependence:
    """Test that multiple documents are tracked independently."""

    def test_five_documents_tracked_independently(self, batch_blob_mocks):
        """Upload 5 documents and verify each is tracked with its own status."""
        blob_service, container_client, _ = batch_blob_mocks

        doc_ids = [f"batch-{i}" for i in range(5)]
        statuses = ["pending", "processing", "completed", "completed", "failed"]

        blobs = [
            _make_blob_item(did, st)
            for did, st in zip(doc_ids, statuses)
        ]
        container_client.list_blobs.return_value = blobs

        documents = list_documents(blob_service)

        assert len(documents) == 5
        for doc, expected_id, expected_status in zip(
            documents, doc_ids, statuses
        ):
            assert doc.id == expected_id
            assert doc.status == expected_status

    def test_batch_summary_reflects_all_statuses(self, batch_blob_mocks):
        """Batch summary should count all document statuses correctly."""
        blob_service, container_client, _ = batch_blob_mocks

        blobs = [
            _make_blob_item("b1", "pending"),
            _make_blob_item("b2", "processing"),
            _make_blob_item("b3", "completed"),
            _make_blob_item("b4", "completed"),
            _make_blob_item("b5", "failed"),
        ]
        container_client.list_blobs.return_value = blobs

        summary = get_batch_summary(blob_service)

        assert summary["total"] == 5
        assert summary["pending"] == 1
        assert summary["processing"] == 1
        assert summary["completed"] == 2
        assert summary["failed"] == 1

    def test_individual_status_retrieval_in_batch(self, batch_blob_mocks):
        """get_status for each document returns the correct individual status."""
        blob_service, container_client, blob_client = batch_blob_mocks

        # _find_blob_by_id uses name_starts_with scan
        blob_item = _make_blob_item("doc-specific", status="completed",
                                     page_count="10", pages_processed="10")
        container_client.list_blobs.return_value = [blob_item]
        blob_client.get_blob_properties.return_value = _make_blob_properties(
            "doc-specific", status="completed",
            page_count="10", pages_processed="10",
        )

        doc = get_status(blob_service, "doc-specific")

        assert doc is not None
        assert doc.id == "doc-specific"
        assert doc.status == "completed"
        assert doc.page_count == 10
        assert doc.pages_processed == 10

    def test_batch_summary_empty_batch(self, batch_blob_mocks):
        """Batch summary with no documents should return all zeros."""
        blob_service, container_client, _ = batch_blob_mocks
        container_client.list_blobs.return_value = []

        summary = get_batch_summary(blob_service)

        assert summary["total"] == 0
        assert summary["pending"] == 0
        assert summary["processing"] == 0
        assert summary["completed"] == 0
        assert summary["failed"] == 0

    def test_batch_summary_all_pending(self, batch_blob_mocks):
        """Batch of 5 all-pending documents should show total=5, pending=5."""
        blob_service, container_client, _ = batch_blob_mocks

        blobs = [_make_blob_item(f"p{i}", "pending") for i in range(5)]
        container_client.list_blobs.return_value = blobs

        summary = get_batch_summary(blob_service)

        assert summary["total"] == 5
        assert summary["pending"] == 5
        assert summary["processing"] == 0
        assert summary["completed"] == 0
        assert summary["failed"] == 0


# ===================================================================
# T044 — Failure isolation tests
# ===================================================================


class TestBatchFailureIsolation:
    """Verify that one document failing doesn't affect others."""

    def test_failed_document_does_not_affect_completed(self, batch_blob_mocks):
        """A failed document should not change the status of completed ones."""
        blob_service, container_client, _ = batch_blob_mocks

        blobs = [
            _make_blob_item("ok-1", "completed",
                            page_count="5", pages_processed="5"),
            _make_blob_item("ok-2", "completed",
                            page_count="3", pages_processed="3"),
            _make_blob_item("fail-1", "failed",
                            error_message="OCR timeout"),
            _make_blob_item("ok-3", "completed",
                            page_count="2", pages_processed="2"),
            _make_blob_item("ok-4", "pending"),
        ]
        container_client.list_blobs.return_value = blobs

        documents = list_documents(blob_service)

        completed = [d for d in documents if d.status == "completed"]
        failed = [d for d in documents if d.status == "failed"]
        pending = [d for d in documents if d.status == "pending"]

        assert len(completed) == 3
        assert len(failed) == 1
        assert len(pending) == 1

        # The failed document should carry its error
        assert failed[0].id == "fail-1"
        assert failed[0].error_message == "OCR timeout"

        # Completed documents should be completely unaffected
        for doc in completed:
            assert doc.error_message is None or doc.error_message == ""
            assert doc.page_count is not None

    def test_setting_one_status_does_not_modify_others(self, batch_blob_mocks):
        """set_status on one document should only update that blob's metadata."""
        blob_service, container_client, blob_client = batch_blob_mocks

        # _find_blob_by_id will match this single blob
        blob_item = _make_blob_item("doc-fail", status="processing")
        container_client.list_blobs.return_value = [blob_item]
        blob_client.get_blob_properties.return_value = _make_blob_properties(
            "doc-fail", status="processing",
        )

        set_status(blob_service, "doc-fail", "failed",
                   error_message="Parse error")

        # Only one blob should have its metadata written
        blob_client.set_blob_metadata.assert_called_once()
        written = blob_client.set_blob_metadata.call_args[0][0]
        assert written["status"] == "failed"
        assert written["error_message"] == "Parse error"

    def test_batch_summary_with_mixed_failures(self, batch_blob_mocks):
        """Batch summary should accurately count when some documents fail."""
        blob_service, container_client, _ = batch_blob_mocks

        blobs = [
            _make_blob_item("m1", "completed"),
            _make_blob_item("m2", "failed"),
            _make_blob_item("m3", "completed"),
            _make_blob_item("m4", "failed"),
            _make_blob_item("m5", "completed"),
        ]
        container_client.list_blobs.return_value = blobs

        summary = get_batch_summary(blob_service)

        assert summary["total"] == 5
        assert summary["completed"] == 3
        assert summary["failed"] == 2
        assert summary["pending"] == 0
        assert summary["processing"] == 0

    def test_failure_error_messages_are_document_specific(self, batch_blob_mocks):
        """Each failed document should carry its own error message."""
        blob_service, container_client, _ = batch_blob_mocks

        blobs = [
            _make_blob_item("f1", "failed", error_message="Corrupt PDF"),
            _make_blob_item("f2", "failed", error_message="OCR timeout"),
            _make_blob_item("ok", "completed"),
        ]
        container_client.list_blobs.return_value = blobs

        documents = list_documents(blob_service)
        failed = sorted(
            [d for d in documents if d.status == "failed"],
            key=lambda d: d.id,
        )

        assert len(failed) == 2
        assert failed[0].error_message == "Corrupt PDF"
        assert failed[1].error_message == "OCR timeout"

        ok = [d for d in documents if d.status == "completed"]
        assert len(ok) == 1
        assert ok[0].error_message is None or ok[0].error_message == ""


# ===================================================================
# T047 — Concurrent processing verification
# ===================================================================


class TestConcurrentProcessing:
    """Verify stateless execution — no shared state between invocations."""

    def test_blob_trigger_has_no_module_level_mutable_state(self):
        """The blob trigger module should not use mutable module-level state
        that could leak between concurrent invocations.

        Module-level mutable containers (list, dict, set) used for
        per-request tracking would cause data races.  Only immutable
        constants and the Azure Functions ``app`` singleton are allowed.
        """
        import function_app

        # Collect all public, non-dunder module-level attributes
        module_attrs = {
            name: getattr(function_app, name)
            for name in dir(function_app)
            if not name.startswith("_")
        }

        # Known safe objects that *are* expected at module level:
        # - app / logger: framework singletons
        # - ALLOWED_EXTENSIONS, EXTENSION_CONTENT_TYPES: read-only config
        #   dicts imported from models.py (never mutated at runtime)
        safe_names = {
            "app",
            "logger",
            "ALLOWED_EXTENSIONS",
            "EXTENSION_CONTENT_TYPES",
            "MAX_FILE_SIZE_BYTES",
            "DocumentStatus",
            "status_service",
        }

        for name, value in module_attrs.items():
            if name in safe_names:
                continue
            if isinstance(value, (list, dict, set)):
                pytest.fail(
                    f"Module-level mutable state found: {name} "
                    f"({type(value).__name__}). Concurrent blob triggers "
                    "would share this state."
                )

    def test_concurrent_status_updates_are_independent(self):
        """Simulate concurrent status updates across 5 documents and verify
        that each one lands with its intended final status."""
        results: dict[str, str] = {}
        errors: list[tuple[str, str]] = []

        def process_document(doc_id: str, target_status: str) -> None:
            """Simulate one blob-trigger invocation updating status."""
            try:
                # Each invocation creates its own mock service — just like
                # the real blob trigger calls _get_blob_service_client().
                svc = MagicMock()
                cc = MagicMock()
                bc = MagicMock()
                svc.get_container_client.return_value = cc
                cc.get_blob_client.return_value = bc

                blob_item = _make_blob_item(doc_id, status="processing")
                cc.list_blobs.return_value = [blob_item]
                bc.get_blob_properties.return_value = _make_blob_properties(
                    doc_id, status="processing",
                )

                set_status(svc, doc_id, target_status)

                written = bc.set_blob_metadata.call_args[0][0]
                results[doc_id] = written["status"]
            except Exception as exc:
                errors.append((doc_id, str(exc)))

        # Run 5 status updates concurrently
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = []
            for i in range(5):
                doc_id = f"concurrent-{i}"
                target = "completed" if i % 2 == 0 else "failed"
                futures.append(pool.submit(process_document, doc_id, target))

            for f in futures:
                f.result()  # propagate exceptions

        assert not errors, f"Errors during concurrent processing: {errors}"
        assert len(results) == 5

        for i in range(5):
            expected = "completed" if i % 2 == 0 else "failed"
            assert results[f"concurrent-{i}"] == expected

    def test_batch_summary_from_preloaded_documents(self):
        """get_batch_summary should compute from a pre-loaded document list
        without scanning blobs again."""
        blob_service = MagicMock()
        container_client = MagicMock()
        blob_service.get_container_client.return_value = container_client

        documents = [
            Document(id="d1", name="doc1", status="pending",
                     blob_path="files/d1.pdf"),
            Document(id="d2", name="doc2", status="completed",
                     blob_path="files/d2.pdf"),
            Document(id="d3", name="doc3", status="completed",
                     blob_path="files/d3.pdf"),
            Document(id="d4", name="doc4", status="failed",
                     blob_path="files/d4.pdf"),
        ]

        summary = get_batch_summary(blob_service, documents=documents)

        assert summary["total"] == 4
        assert summary["pending"] == 1
        assert summary["completed"] == 2
        assert summary["failed"] == 1
        assert summary["processing"] == 0

        # The key optimisation: no blob scan when documents are provided
        container_client.list_blobs.assert_not_called()

    def test_each_trigger_invocation_creates_own_blob_service(self):
        """Each blob trigger invocation should get its own BlobServiceClient
        from the environment — verify no caching between calls."""
        import function_app

        conn_str = (
            "DefaultEndpointsProtocol=https;"
            "AccountName=test;"
            "AccountKey=dGVzdA==;"
            "EndpointSuffix=core.windows.net"
        )

        with patch.dict("os.environ", {"AzureWebJobsStorage": conn_str}):
            with patch("function_app.BlobServiceClient") as mock_bsc:
                mock_bsc.from_connection_string.return_value = MagicMock()

                function_app._get_blob_service_client()
                function_app._get_blob_service_client()

                # Must call from_connection_string each time (no cache)
                assert mock_bsc.from_connection_string.call_count == 2

    def test_concurrent_batch_summary_computations(self):
        """Multiple threads computing batch_summary concurrently should
        each produce correct, independent results."""
        results: dict[int, dict[str, int]] = {}

        def compute_summary(thread_id: int, n_docs: int) -> None:
            svc = MagicMock()
            cc = MagicMock()
            svc.get_container_client.return_value = cc

            blobs = [
                _make_blob_item(f"t{thread_id}-{i}", "completed")
                for i in range(n_docs)
            ]
            cc.list_blobs.return_value = blobs

            results[thread_id] = get_batch_summary(svc)

        with ThreadPoolExecutor(max_workers=4) as pool:
            # Each thread processes a different number of documents
            futures = [
                pool.submit(compute_summary, tid, count)
                for tid, count in [(0, 3), (1, 5), (2, 1), (3, 10)]
            ]
            for f in futures:
                f.result()

        assert results[0]["total"] == 3
        assert results[1]["total"] == 5
        assert results[2]["total"] == 1
        assert results[3]["total"] == 10

        # All should show 100 % completed
        for summary in results.values():
            assert summary["completed"] == summary["total"]
            assert summary["pending"] == 0
            assert summary["failed"] == 0
