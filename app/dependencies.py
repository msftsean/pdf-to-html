"""
Dependency-injection helpers for the FastAPI application.

Migrated from ``function_app.py`` helper functions — every reference to
``os.environ`` is replaced with ``app.config.settings``.
"""

from __future__ import annotations

import logging
import random
import time as time_module
from datetime import datetime, timedelta, timezone

from azure.core.exceptions import (
    HttpResponseError,
    ServiceRequestError,
    ServiceResponseError,
)
from azure.identity import DefaultAzureCredential
from azure.storage.blob import (
    BlobSasPermissions,
    BlobServiceClient,
    generate_blob_sas,
)
from azure.storage.queue import QueueClient

from app.config import settings

logger = logging.getLogger(__name__)

# ── Well-known Azurite storage credentials ─────────────────────────────────
_AZURITE_ACCOUNT_NAME = "devstoreaccount1"
_AZURITE_ACCOUNT_KEY = (
    "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq"
    "/K1SZFPTOtr/KBHBeksoGMGw=="
)

# SAS token lifetimes
SAS_UPLOAD_EXPIRY_MINUTES = 15
SAS_DOWNLOAD_EXPIRY_MINUTES = 60


# ---------------------------------------------------------------------------
# Blob service client
# ---------------------------------------------------------------------------

def get_blob_service_client() -> BlobServiceClient:
    """Create a ``BlobServiceClient`` supporting both connection-string and
    identity-based authentication.

    * **Local / Azurite:** Uses the storage connection string.
    * **Azure (managed identity):** Uses ``AzureWebJobsStorage__accountName``
      with ``DefaultAzureCredential``.
    """
    conn_str = settings.storage_connection_string

    # Connection-string path (local dev / Azurite, or Azure with explicit key).
    if conn_str and (
        "AccountKey=" in conn_str or "UseDevelopmentStorage=true" in conn_str
    ):
        return BlobServiceClient.from_connection_string(conn_str)

    # Identity-based path (Azure managed identity).
    account_name = settings.AzureWebJobsStorage__accountName
    if account_name:
        account_url = f"https://{account_name}.blob.core.windows.net"
        return BlobServiceClient(account_url, credential=DefaultAzureCredential())

    raise RuntimeError(
        "Storage not configured. Set AZURE_STORAGE_CONNECTION_STRING "
        "(connection string) or AzureWebJobsStorage__accountName "
        "(identity-based auth)."
    )


# ---------------------------------------------------------------------------
# Queue client
# ---------------------------------------------------------------------------

def get_queue_client() -> QueueClient:
    """Return a ``QueueClient`` for the conversion-jobs queue.

    Supports the same connection-string vs. identity-based auth logic as
    ``get_blob_service_client``.
    """
    conn_str = settings.storage_connection_string

    if conn_str and (
        "AccountKey=" in conn_str or "UseDevelopmentStorage=true" in conn_str
    ):
        return QueueClient.from_connection_string(
            conn_str, queue_name=settings.QUEUE_NAME
        )

    account_name = settings.AzureWebJobsStorage__accountName
    if account_name:
        queue_url = (
            f"https://{account_name}.queue.core.windows.net/{settings.QUEUE_NAME}"
        )
        return QueueClient(queue_url, credential=DefaultAzureCredential())

    raise RuntimeError(
        "Storage not configured — cannot create queue client."
    )


# ---------------------------------------------------------------------------
# SAS helpers
# ---------------------------------------------------------------------------

def _is_azurite(connection_string: str) -> bool:
    """Return ``True`` when the connection string targets the Azurite emulator."""
    return (
        "UseDevelopmentStorage=true" in connection_string
        or "127.0.0.1:10000" in connection_string
    )


def _is_local_storage() -> bool:
    """Return ``True`` when the app is configured for Azurite local storage."""
    conn_str = settings.storage_connection_string
    return _is_azurite(conn_str)


def _uses_identity_auth() -> bool:
    """Return ``True`` when the app uses identity-based storage auth (no key)."""
    conn_str = settings.storage_connection_string
    if conn_str and (
        "AccountKey=" in conn_str or "UseDevelopmentStorage=true" in conn_str
    ):
        return False
    return bool(settings.AzureWebJobsStorage__accountName)


def _extract_account_key(connection_string: str) -> str | None:
    """Parse ``AccountKey`` from an Azure Storage connection string.

    When the connection string is the Azurite shorthand
    ``UseDevelopmentStorage=true``, returns the well-known Azurite account key
    (there is no explicit ``AccountKey`` in that string).

    Returns ``None`` if no account key is available (identity-based auth).
    """
    if _is_azurite(connection_string):
        return _AZURITE_ACCOUNT_KEY
    for part in connection_string.split(";"):
        part = part.strip()
        if part.lower().startswith("accountkey="):
            return part.split("=", 1)[1]
    return None


def _generate_sas_token_str(
    blob_service: BlobServiceClient,
    container: str,
    blob_name: str,
    permission: BlobSasPermissions,
    expiry: datetime,
) -> str:
    """Generate a SAS token string using account key or user delegation key.

    * **Local / Azurite:** Uses account key from connection string.
    * **Azure (managed identity):** Requests a ``UserDelegationKey`` from the
      blob service and generates a user-delegation SAS.
    """
    account_name = blob_service.account_name
    conn_str = settings.storage_connection_string
    account_key = _extract_account_key(conn_str) if conn_str else None

    if account_key:
        # Account-key SAS (local / Azurite / connection-string deployments)
        return generate_blob_sas(
            account_name=account_name,
            container_name=container,
            blob_name=blob_name,
            account_key=account_key,
            permission=permission,
            expiry=expiry,
        )

    # User-delegation SAS (identity-based auth on Azure)
    start_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    delegation_key = blob_service.get_user_delegation_key(start_time, expiry)
    return generate_blob_sas(
        account_name=account_name,
        container_name=container,
        blob_name=blob_name,
        user_delegation_key=delegation_key,
        permission=permission,
        expiry=expiry,
    )


def _generate_download_sas_url(
    blob_service: BlobServiceClient,
    container: str,
    blob_name: str,
    expiry: datetime,
) -> str:
    """Generate a read-only SAS URL for downloading a blob."""
    account_name = blob_service.account_name
    sas_token = _generate_sas_token_str(
        blob_service,
        container,
        blob_name,
        BlobSasPermissions(read=True),
        expiry,
    )
    if _is_local_storage():
        return f"http://127.0.0.1:10000/{account_name}/{container}/{blob_name}?{sas_token}"
    return f"https://{account_name}.blob.core.windows.net/{container}/{blob_name}?{sas_token}"


# ---------------------------------------------------------------------------
# Retry with exponential backoff
# ---------------------------------------------------------------------------

def _retry_blob_operation(
    operation,
    max_retries: int = 3,
    initial_delay: float = 1.0,
):
    """Execute a blob operation with exponential-backoff retry logic.

    Args:
        operation: A callable that performs the blob operation.
        max_retries: Maximum number of retry attempts (default 3).
        initial_delay: Initial delay in seconds (default 1.0).

    Returns:
        The result of the operation.

    Raises:
        The last exception if all retries fail.
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries):
        try:
            return operation()
        except (ServiceRequestError, ServiceResponseError, HttpResponseError) as e:
            last_exception = e
            if attempt < max_retries - 1:
                jitter = delay * (1.0 + random.random() * 0.5)
                logger.warning(
                    "Blob operation failed (attempt %d/%d): %s. Retrying in %.2fs…",
                    attempt + 1,
                    max_retries,
                    str(e),
                    jitter,
                )
                time_module.sleep(jitter)
                delay *= 2  # Exponential backoff
            else:
                logger.error(
                    "Blob operation failed after %d attempts: %s",
                    max_retries,
                    str(e),
                )

    if last_exception:
        raise last_exception


# ---------------------------------------------------------------------------
# Public aliases — used by app.main and app.worker
# ---------------------------------------------------------------------------

# Re-export with public names so endpoints can ``from app.dependencies import …``
generate_sas_token_str = _generate_sas_token_str
generate_download_sas_url = _generate_download_sas_url
retry_blob_operation = _retry_blob_operation
is_local_storage = _is_local_storage
is_azurite = _is_azurite
extract_account_key = _extract_account_key
