"""
Password-protection detection for uploaded documents.

Migrated from ``function_app.py`` helper functions — used by the API
upload endpoint and the queue worker to reject encrypted files early.
"""

from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)


def is_password_protected_pdf(file_data: bytes) -> bool:
    """Check if a PDF is password-protected or encrypted.

    Args:
        file_data: Raw PDF file bytes.

    Returns:
        True if the PDF is encrypted/password-protected.
    """
    import pymupdf

    try:
        doc = pymupdf.open(stream=file_data, filetype="pdf")
        is_encrypted = doc.is_encrypted
        doc.close()
        return is_encrypted
    except Exception as e:
        # If we can't open the document at all, it might be encrypted
        error_msg = str(e).lower()
        if "password" in error_msg or "encrypt" in error_msg:
            return True
        raise


def is_password_protected_docx(file_data: bytes) -> bool:
    """Check if a DOCX is password-protected or encrypted.

    Args:
        file_data: Raw DOCX file bytes.

    Returns:
        True if the DOCX is encrypted/password-protected.
    """
    from docx import Document

    try:
        Document(io.BytesIO(file_data))
        return False
    except Exception as e:
        error_msg = str(e).lower()
        if (
            "password" in error_msg
            or "encrypt" in error_msg
            or "protected" in error_msg
        ):
            return True
        # Check for specific python-docx encryption errors
        if "package" in error_msg and (
            "corrupt" in error_msg or "invalid" in error_msg
        ):
            # Could be encryption, but we'll re-raise to not mask other errors
            pass
        raise


def is_password_protected_pptx(file_data: bytes) -> bool:
    """Check if a PPTX is password-protected or encrypted.

    Args:
        file_data: Raw PPTX file bytes.

    Returns:
        True if the PPTX is encrypted/password-protected.
    """
    from pptx import Presentation

    try:
        Presentation(io.BytesIO(file_data))
        return False
    except Exception as e:
        error_msg = str(e).lower()
        if (
            "password" in error_msg
            or "encrypt" in error_msg
            or "protected" in error_msg
        ):
            return True
        # Check for specific python-pptx encryption errors
        if "package" in error_msg and (
            "corrupt" in error_msg or "invalid" in error_msg
        ):
            # Could be encryption, but we'll re-raise to not mask other errors
            pass
        raise


def check_password_protection(file_data: bytes, extension: str) -> bool:
    """Check if a file is password-protected based on its extension.

    Args:
        file_data: Raw file bytes.
        extension: File extension including dot (e.g. ".pdf").

    Returns:
        True if the file is password-protected.

    Raises:
        ValueError: If the extension is not supported.
    """
    ext = extension.lower()
    if ext == ".pdf":
        return is_password_protected_pdf(file_data)
    elif ext == ".docx":
        return is_password_protected_docx(file_data)
    elif ext == ".pptx":
        return is_password_protected_pptx(file_data)
    else:
        raise ValueError(f"Unsupported extension for password check: {ext}")
