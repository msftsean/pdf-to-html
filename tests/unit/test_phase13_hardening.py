"""
Unit tests for Phase 13 Backend Hardening (T071-T074).

Tests password-protected document detection, multi-language support,
blob storage retry logic, and filename conflict handling.
"""

import io
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timezone

# Test imports
import function_app
from html_builder import _detect_language


# ---------------------------------------------------------------------------
# T071: Password-Protected Document Rejection
# ---------------------------------------------------------------------------

class TestPasswordProtectedDetection:
    """Test detection of password-protected/encrypted documents."""

    def test_pdf_password_protected_detected(self):
        """Verify encrypted PDF is detected."""
        # Create a mock encrypted PDF
        encrypted_pdf = b"%PDF-1.4\n%encrypted content"
        
        with patch("pymupdf.open") as mock_open:
            mock_doc = Mock()
            mock_doc.is_encrypted = True
            mock_open.return_value = mock_doc
            
            result = function_app._is_password_protected_pdf(encrypted_pdf)
            assert result is True
            mock_doc.close.assert_called_once()

    def test_pdf_not_password_protected(self):
        """Verify non-encrypted PDF is not flagged."""
        normal_pdf = b"%PDF-1.4\n%normal content"
        
        with patch("pymupdf.open") as mock_open:
            mock_doc = Mock()
            mock_doc.is_encrypted = False
            mock_open.return_value = mock_doc
            
            result = function_app._is_password_protected_pdf(normal_pdf)
            assert result is False
            mock_doc.close.assert_called_once()

    def test_pdf_password_error_detected(self):
        """Verify PDF that raises password error is detected as encrypted."""
        encrypted_pdf = b"%PDF-1.4\n%encrypted"
        
        with patch("pymupdf.open") as mock_open:
            mock_open.side_effect = Exception("password required")
            
            result = function_app._is_password_protected_pdf(encrypted_pdf)
            assert result is True

    def test_docx_password_protected_detected(self):
        """Verify encrypted DOCX is detected."""
        encrypted_docx = b"PK\x03\x04encrypted"
        
        with patch("docx.Document") as mock_doc_class:
            mock_doc_class.side_effect = Exception("This file is password protected")
            
            result = function_app._is_password_protected_docx(encrypted_docx)
            assert result is True

    def test_docx_not_password_protected(self):
        """Verify non-encrypted DOCX is not flagged."""
        normal_docx = b"PK\x03\x04normal"
        
        with patch("docx.Document") as mock_doc_class:
            mock_doc_class.return_value = Mock()
            
            result = function_app._is_password_protected_docx(normal_docx)
            assert result is False

    def test_pptx_password_protected_detected(self):
        """Verify encrypted PPTX is detected."""
        encrypted_pptx = b"PK\x03\x04encrypted"
        
        with patch("pptx.Presentation") as mock_pres_class:
            mock_pres_class.side_effect = Exception("document is encrypted")
            
            result = function_app._is_password_protected_pptx(encrypted_pptx)
            assert result is True

    def test_pptx_not_password_protected(self):
        """Verify non-encrypted PPTX is not flagged."""
        normal_pptx = b"PK\x03\x04normal"
        
        with patch("pptx.Presentation") as mock_pres_class:
            mock_pres_class.return_value = Mock()
            
            result = function_app._is_password_protected_pptx(normal_pptx)
            assert result is False


# ---------------------------------------------------------------------------
# T072: Multi-Language Lang Attribute Detection
# ---------------------------------------------------------------------------

class TestLanguageDetection:
    """Test language detection for content sections."""

    def test_detect_english_default(self):
        """Short or English text should return default."""
        text = "This is a simple English sentence with common words."
        result = _detect_language(text, default="en")
        assert result == "en"

    def test_detect_spanish(self):
        """Spanish text with accented characters should be detected."""
        text = "El gobierno español está trabajando en la educación de los niños y niñas del país."
        result = _detect_language(text, default="en")
        assert result == "es"

    def test_detect_french(self):
        """French text with characteristic words should be detected."""
        text = "Le gouvernement français travaille à améliorer le système éducatif pour les enfants."
        result = _detect_language(text, default="en")
        assert result == "fr"

    def test_detect_german(self):
        """German text with umlauts and common words should be detected."""
        text = "Die deutsche Regierung arbeitet an der Verbesserung und Förderung des Schulsystems für Kinder."
        result = _detect_language(text, default="en")
        assert result == "de"

    def test_detect_italian(self):
        """Italian text with characteristic words should be detected."""
        text = "Il governo italiano e la camera dei deputati lavorano per migliorare il sistema di educazione."
        result = _detect_language(text, default="en")
        assert result == "it"

    def test_detect_portuguese(self):
        """Portuguese text with characteristic markers should be detected."""
        text = "O governo português está trabalhando ação educação melhoramento com coordenação dos alunos."
        result = _detect_language(text, default="en")
        assert result == "pt"

    def test_short_text_returns_default(self):
        """Very short text should return default language."""
        text = "Hello"
        result = _detect_language(text, default="en")
        assert result == "en"

    def test_empty_text_returns_default(self):
        """Empty text should return default language."""
        text = ""
        result = _detect_language(text, default="fr")
        assert result == "fr"


# ---------------------------------------------------------------------------
# T073: Exponential Backoff Retry for Blob Storage
# ---------------------------------------------------------------------------

class TestBlobStorageRetry:
    """Test exponential backoff retry logic for blob operations."""

    def test_retry_succeeds_first_attempt(self):
        """Operation that succeeds immediately should not retry."""
        mock_operation = Mock(return_value="success")
        
        result = function_app._retry_blob_operation(mock_operation, max_retries=3)
        
        assert result == "success"
        assert mock_operation.call_count == 1

    def test_retry_succeeds_after_failures(self):
        """Operation that fails then succeeds should retry correctly."""
        from azure.core.exceptions import ServiceResponseError
        
        mock_operation = Mock(
            side_effect=[
                ServiceResponseError("Transient error"),
                ServiceResponseError("Another transient error"),
                "success"
            ]
        )
        
        with patch("function_app.time_module.sleep"):
            result = function_app._retry_blob_operation(mock_operation, max_retries=3)
        
        assert result == "success"
        assert mock_operation.call_count == 3

    def test_retry_fails_after_max_attempts(self):
        """Operation that always fails should raise after max retries."""
        from azure.core.exceptions import ServiceResponseError
        
        mock_operation = Mock(
            side_effect=ServiceResponseError("Persistent error")
        )
        
        with patch("function_app.time_module.sleep"):
            with pytest.raises(ServiceResponseError):
                function_app._retry_blob_operation(mock_operation, max_retries=3)
        
        assert mock_operation.call_count == 3

    def test_retry_exponential_backoff_with_jitter(self):
        """Verify exponential backoff delays are applied correctly."""
        from azure.core.exceptions import ServiceRequestError
        
        mock_operation = Mock(
            side_effect=[
                ServiceRequestError("Error 1"),
                ServiceRequestError("Error 2"),
                "success"
            ]
        )
        
        with patch("function_app.time_module.sleep") as mock_sleep:
            with patch("function_app.random.random", return_value=0.5):
                result = function_app._retry_blob_operation(
                    mock_operation, 
                    max_retries=3, 
                    initial_delay=1.0
                )
        
        # Verify sleep was called with increasing delays (with jitter)
        assert mock_sleep.call_count == 2
        # First retry: 1.0 * (1.0 + 0.5 * 0.5) = 1.25s
        # Second retry: 2.0 * (1.0 + 0.5 * 0.5) = 2.5s
        calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert calls[0] == 1.25  # First delay with jitter
        assert calls[1] == 2.5   # Second delay (doubled) with jitter

    def test_retry_logs_attempts(self, caplog):
        """Verify retry attempts are logged."""
        from azure.core.exceptions import HttpResponseError
        
        mock_operation = Mock(
            side_effect=[
                HttpResponseError("Transient failure"),
                "success"
            ]
        )
        
        with patch("function_app.time_module.sleep"):
            function_app._retry_blob_operation(mock_operation, max_retries=3)
        
        # Check that warning was logged for the retry
        assert any("Blob operation failed" in record.message for record in caplog.records)
        assert any("Retrying" in record.message for record in caplog.records)

    def test_retry_does_not_catch_other_exceptions(self):
        """Non-transient exceptions should not be retried."""
        mock_operation = Mock(side_effect=ValueError("Invalid argument"))
        
        with pytest.raises(ValueError):
            function_app._retry_blob_operation(mock_operation, max_retries=3)
        
        assert mock_operation.call_count == 1


# ---------------------------------------------------------------------------
# T074: Filename Conflict Handling
# ---------------------------------------------------------------------------

class TestFilenameConflictHandling:
    """Test handling of concurrent uploads with same filename."""

    def test_generate_sas_token_preserves_original_filename(self):
        """Verify original filename is stored in metadata."""
        from azure.functions import HttpRequest
        
        # Mock request
        req = Mock(spec=HttpRequest)
        req.get_json.return_value = {
            "filename": "report.pdf",
            "content_type": "application/pdf",
            "size_bytes": 1024000
        }
        req.params.get.return_value = None
        
        with patch("function_app._get_blob_service_client") as mock_blob_service:
            mock_blob_service.return_value = Mock(account_name="testaccount")
            mock_container = Mock()
            mock_blob_service.return_value.get_container_client.return_value = mock_container
            mock_blob_client = Mock()
            mock_container.get_blob_client.return_value = mock_blob_client
            
            with patch("function_app._extract_account_key", return_value="testkey"):
                with patch("function_app.generate_blob_sas", return_value="sas_token"):
                    with patch("function_app._retry_blob_operation") as mock_retry:
                        mock_retry.side_effect = lambda op: op()
                        
                        response = function_app.generate_sas_token(req)
        
        # Verify the blob was created with original_filename in metadata
        upload_call = mock_blob_client.upload_blob.call_args
        metadata = upload_call.kwargs["metadata"]
        assert "original_filename" in metadata
        assert metadata["original_filename"] == "report.pdf"
        assert metadata["name"] == "report"  # Basename without extension

    def test_document_id_ensures_uniqueness(self):
        """Verify each upload gets a unique document_id (UUID)."""
        from azure.functions import HttpRequest
        import json
        
        req = Mock(spec=HttpRequest)
        req.get_json.return_value = {
            "filename": "report.pdf",
            "content_type": "application/pdf",
            "size_bytes": 1024000
        }
        
        with patch.dict("os.environ", {"AzureWebJobsStorage": "test_connection_string"}):
            with patch("function_app._get_blob_service_client") as mock_blob_service:
                mock_blob_service.return_value = Mock(account_name="testaccount")
                mock_container = Mock()
                mock_blob_service.return_value.get_container_client.return_value = mock_container
                mock_blob_client = Mock()
                mock_container.get_blob_client.return_value = mock_blob_client
                
                with patch("function_app._extract_account_key", return_value="testkey"):
                    with patch("function_app.generate_blob_sas", return_value="sas_token"):
                        with patch("function_app._retry_blob_operation") as mock_retry:
                            mock_retry.side_effect = lambda op: op()
                            
                            # Generate two SAS tokens for same filename
                            response1 = function_app.generate_sas_token(req)
                            response2 = function_app.generate_sas_token(req)
        
        # Verify different document_ids were generated
        # Both should succeed without conflict since UUIDs are unique
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Parse the responses and verify different document_ids
        data1 = json.loads(response1.get_body())
        data2 = json.loads(response2.get_body())
        assert data1["document_id"] != data2["document_id"]

    def test_blob_name_uses_document_id(self):
        """Verify blob name is based on document_id, not original filename."""
        from azure.functions import HttpRequest
        
        req = Mock(spec=HttpRequest)
        req.get_json.return_value = {
            "filename": "my document with spaces.pdf",
            "content_type": "application/pdf",
            "size_bytes": 1024000
        }
        
        with patch("function_app._get_blob_service_client") as mock_blob_service:
            mock_blob_service.return_value = Mock(account_name="testaccount")
            mock_container = Mock()
            mock_blob_service.return_value.get_container_client.return_value = mock_container
            mock_blob_client = Mock()
            mock_container.get_blob_client.return_value = mock_blob_client
            
            with patch("function_app._extract_account_key", return_value="testkey"):
                with patch("function_app.generate_blob_sas", return_value="sas_token"):
                    with patch("function_app.uuid.uuid4") as mock_uuid:
                        mock_uuid.return_value = Mock(__str__=lambda self: "test-uuid-123")
                        
                        with patch("function_app._retry_blob_operation") as mock_retry:
                            mock_retry.side_effect = lambda op: op()
                            
                            response = function_app.generate_sas_token(req)
        
        # Verify blob_client was called with UUID-based name, not original filename
        get_blob_call = mock_container.get_blob_client.call_args
        blob_name = get_blob_call.args[0]
        assert blob_name == "test-uuid-123.pdf"
        assert " " not in blob_name  # No spaces from original filename
