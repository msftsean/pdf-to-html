"""
Shared pytest fixtures for pdf-to-html test suite.

These fixtures provide common test data aligned with the data model spec
(specs/001-sean/data-model.md). All modules under test are being built
by Wonder-Woman — tests are written TDD-first.
"""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Model fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_document_kwargs():
    """Minimal valid kwargs for creating a Document."""
    return {
        "name": "annual-report-2025",
        "format": "pdf",
        "size_bytes": 2_048_576,
        "blob_path": "files/annual-report-2025.pdf",
    }


@pytest.fixture
def sample_wcag_violation_kwargs():
    """Minimal valid kwargs for creating a WcagViolation."""
    return {
        "rule_id": "image-alt",
        "severity": "critical",
        "description": "Images must have alternate text",
        "html_element": '<img src="chart.png">',
        "help_url": "https://dequeuniversity.com/rules/axe/4.4/image-alt",
    }


@pytest.fixture
def valid_html():
    """Minimal WCAG-compliant HTML snippet for testing."""
    return (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head><meta charset="utf-8"><title>Test</title></head>\n'
        '<body>\n'
        '  <h1>Main Heading</h1>\n'
        '  <p>Content paragraph.</p>\n'
        '  <h2>Sub Heading</h2>\n'
        '  <p>More content.</p>\n'
        '  <img src="photo.png" alt="A descriptive alt text">\n'
        '  <table>\n'
        '    <thead><tr><th scope="col">Name</th><th scope="col">Value</th></tr></thead>\n'
        '    <tbody><tr><td>Item</td><td>42</td></tr></tbody>\n'
        '  </table>\n'
        '  <a href="https://example.com">Example link</a>\n'
        '</body>\n'
        '</html>'
    )


# ---------------------------------------------------------------------------
# Blob service mock fixtures (for status_service tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_blob_service():
    """Return a MagicMock mimicking azure.storage.blob.BlobServiceClient."""
    return MagicMock()


@pytest.fixture
def mock_container_client(mock_blob_service):
    """Return the container client mock wired to the blob service."""
    container = MagicMock()
    mock_blob_service.get_container_client.return_value = container
    return container


@pytest.fixture
def mock_blob_client(mock_container_client):
    """Return a blob client mock wired to the container."""
    blob = MagicMock()
    mock_container_client.get_blob_client.return_value = blob
    return blob
