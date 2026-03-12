"""
Deployment smoke tests for the FastAPI backend.

These tests run against a LIVE backend (local or Azure) — no mocks.
They verify the actual API endpoints work end-to-end with real blob storage.

Usage:
    # Against local stack (Azurite + FastAPI on :8000)
    pytest tests/deployment/ -v

    # Against Azure Container Apps
    BASE_URL=https://ca-pdftohtml-api.whatever.azurecontainerapps.io pytest tests/deployment/ -v
"""

import os
import time

import pytest
import requests

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

# Minimal valid PDF with selectable text
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
    b"   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    b"4 0 obj\n<< /Length 44 >>\nstream\n"
    b"BT /F1 24 Tf 100 700 Td (Hello WCAG) Tj ET\n"
    b"endstream\nendobj\n"
    b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
    b"0000000115 00000 n \n0000000266 00000 n \n0000000360 00000 n \n"
    b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n441\n%%EOF"
)


class TestHealthEndpoints:
    """Verify the deployment is alive and storage is connected."""

    def test_health_returns_200(self):
        resp = requests.get(f"{BASE_URL}/health", timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "checks" in data

    def test_health_storage_ok(self):
        resp = requests.get(f"{BASE_URL}/health", timeout=30)
        data = resp.json()
        assert data["checks"]["storage"] == "ok", (
            f"Storage check failed — backend can't reach blob storage: {data}"
        )

    def test_health_queue_ok(self):
        resp = requests.get(f"{BASE_URL}/health", timeout=30)
        data = resp.json()
        assert data["checks"]["queue"] == "ok", (
            f"Queue check failed — backend can't reach storage queue: {data}"
        )

    def test_ready_returns_200(self):
        resp = requests.get(f"{BASE_URL}/ready", timeout=30)
        assert resp.status_code == 200


class TestSasTokenEndpoint:
    """Verify the SAS token endpoint works against real storage."""

    def test_valid_pdf_request(self):
        resp = requests.post(
            f"{BASE_URL}/api/upload/sas-token",
            json={
                "filename": "test-smoke.pdf",
                "content_type": "application/pdf",
                "size_bytes": 1024,
            },
            timeout=30,
        )
        assert resp.status_code == 200, f"SAS token failed: {resp.text}"
        data = resp.json()
        assert "document_id" in data
        assert "upload_url" in data
        assert "expires_at" in data
        # Upload URL should be a real blob storage URL
        assert "devstoreaccount1" in data["upload_url"] or "blob.core.windows.net" in data["upload_url"]

    def test_invalid_extension_rejected(self):
        resp = requests.post(
            f"{BASE_URL}/api/upload/sas-token",
            json={
                "filename": "test.exe",
                "content_type": "application/octet-stream",
                "size_bytes": 1024,
            },
            timeout=30,
        )
        assert resp.status_code == 400

    def test_oversized_file_rejected(self):
        resp = requests.post(
            f"{BASE_URL}/api/upload/sas-token",
            json={
                "filename": "huge.pdf",
                "content_type": "application/pdf",
                "size_bytes": 200_000_000,  # 200MB > 100MB limit
            },
            timeout=30,
        )
        assert resp.status_code == 400


class TestFullConversionPipeline:
    """End-to-end: upload → convert → status → download → delete.
    
    This is the critical test that verifies the ENTIRE pipeline works
    against real infrastructure — no mocks, no fakes.
    """

    @pytest.fixture(autouse=True)
    def _cleanup(self):
        """Track documents created during test for cleanup."""
        self._doc_ids: list[str] = []
        yield
        for doc_id in self._doc_ids:
            try:
                requests.delete(f"{BASE_URL}/api/documents/{doc_id}", timeout=10)
            except Exception:
                pass

    def _upload_pdf(self, filename: str = "smoke-test.pdf") -> str:
        """Upload a PDF and return the document_id."""
        # Step 1: Get SAS token
        sas_resp = requests.post(
            f"{BASE_URL}/api/upload/sas-token",
            json={
                "filename": filename,
                "content_type": "application/pdf",
                "size_bytes": len(MINIMAL_PDF),
            },
            timeout=30,
        )
        assert sas_resp.status_code == 200, f"SAS token failed: {sas_resp.text}"
        sas_data = sas_resp.json()
        doc_id = sas_data["document_id"]
        self._doc_ids.append(doc_id)

        # Step 2: Upload via SAS URL
        upload_resp = requests.put(
            sas_data["upload_url"],
            data=MINIMAL_PDF,
            headers={
                "x-ms-blob-type": "BlockBlob",
                "Content-Type": "application/pdf",
            },
            timeout=30,
        )
        assert upload_resp.status_code == 201, (
            f"Blob upload failed ({upload_resp.status_code}): {upload_resp.text}"
        )
        return doc_id

    def _wait_for_completion(self, doc_id: str, timeout_seconds: int = 120) -> dict:
        """Poll status endpoint until conversion completes or times out."""
        deadline = time.time() + timeout_seconds
        last_status = "unknown"
        while time.time() < deadline:
            resp = requests.get(
                f"{BASE_URL}/api/documents/status",
                params={"document_id": doc_id},
                timeout=30,
            )
            assert resp.status_code == 200, f"Status check failed: {resp.text}"
            data = resp.json()
            last_status = data.get("status", "unknown")
            if last_status in ("completed", "failed"):
                return data
            time.sleep(2)
        pytest.fail(
            f"Conversion timed out after {timeout_seconds}s (last status: {last_status})"
        )

    def test_upload_and_convert_pdf(self):
        """The big one: upload a real PDF and verify it converts to WCAG HTML."""
        doc_id = self._upload_pdf()

        # Wait for worker to process
        status = self._wait_for_completion(doc_id)
        assert status["status"] == "completed", (
            f"Conversion failed: {status.get('error_message', 'unknown error')}"
        )

    def test_download_after_conversion(self):
        """Verify download endpoint returns valid WCAG HTML after conversion."""
        doc_id = self._upload_pdf()
        self._wait_for_completion(doc_id)

        # Get download URL
        dl_resp = requests.get(
            f"{BASE_URL}/api/documents/{doc_id}/download", timeout=30,
        )
        assert dl_resp.status_code == 200, f"Download failed: {dl_resp.text}"
        dl_data = dl_resp.json()

        assert "html_url" in dl_data or "download_url" in dl_data
        html_url = dl_data.get("download_url") or dl_data.get("html_url")
        assert html_url, "No HTML download URL in response"

        # Actually download the HTML
        html_resp = requests.get(html_url, timeout=30)
        assert html_resp.status_code == 200, f"HTML download failed: {html_resp.status_code}"
        html = html_resp.text
        assert len(html) > 100, f"HTML too short ({len(html)} chars)"

        # WCAG checks on the actual output
        assert 'lang="en"' in html or "lang=" in html, "Missing lang attribute"
        assert "main-content" in html, "Missing skip-nav target"

    def test_status_lists_all_documents(self):
        """Verify the status endpoint lists documents without a document_id filter."""
        doc_id = self._upload_pdf("list-test.pdf")
        self._wait_for_completion(doc_id)

        resp = requests.get(f"{BASE_URL}/api/documents/status", timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        assert "documents" in data
        assert "summary" in data
        doc_ids = [d.get("document_id") for d in data["documents"]]
        assert doc_id in doc_ids, f"Uploaded doc {doc_id} not in document list"

    def test_delete_document(self):
        """Verify single document deletion works."""
        doc_id = self._upload_pdf("delete-test.pdf")
        self._wait_for_completion(doc_id)

        del_resp = requests.delete(
            f"{BASE_URL}/api/documents/{doc_id}", timeout=30,
        )
        assert del_resp.status_code == 200

        # Verify it's gone
        status_resp = requests.get(
            f"{BASE_URL}/api/documents/status",
            params={"document_id": doc_id},
            timeout=30,
        )
        assert status_resp.status_code == 404
        self._doc_ids.remove(doc_id)  # Already deleted

    def test_delete_all_documents(self):
        """Verify bulk deletion works."""
        self._upload_pdf("bulk-delete-1.pdf")
        self._upload_pdf("bulk-delete-2.pdf")

        del_resp = requests.delete(f"{BASE_URL}/api/documents", timeout=30)
        assert del_resp.status_code == 200
        data = del_resp.json()
        assert data.get("deleted_input", 0) >= 2
        self._doc_ids.clear()  # All deleted

    def test_download_pending_returns_409(self):
        """Verify downloading a document that hasn't finished returns 409."""
        # Get a SAS token but DON'T upload — status should be pending
        sas_resp = requests.post(
            f"{BASE_URL}/api/upload/sas-token",
            json={
                "filename": "pending-test.pdf",
                "content_type": "application/pdf",
                "size_bytes": 1024,
            },
            timeout=30,
        )
        doc_id = sas_resp.json()["document_id"]
        self._doc_ids.append(doc_id)

        dl_resp = requests.get(
            f"{BASE_URL}/api/documents/{doc_id}/download", timeout=30,
        )
        assert dl_resp.status_code == 409
