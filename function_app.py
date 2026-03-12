import io
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

import azure.functions as func
from azure.storage.blob import (
    BlobSasPermissions,
    BlobServiceClient,
    ContentSettings,
    generate_blob_sas,
)

from pdf_extractor import extract_pdf
from ocr_service import ocr_pdf_pages
from html_builder import build_html
from models import (
    ALLOWED_EXTENSIONS,
    EXTENSION_CONTENT_TYPES,
    MAX_FILE_SIZE_BYTES,
    DocumentStatus,
)
import status_service

app = func.FunctionApp()

logger = logging.getLogger(__name__)

# Output container for converted HTML and images
_OUTPUT_CONTAINER = os.environ.get("OUTPUT_CONTAINER", "converted")

# Input container for uploaded files
_INPUT_CONTAINER = "files"

# SAS token lifetime
_SAS_UPLOAD_EXPIRY_MINUTES = 15
_SAS_DOWNLOAD_EXPIRY_MINUTES = 60


def _get_blob_service_client() -> BlobServiceClient:
    conn_str = os.environ["AzureWebJobsStorage"]
    return BlobServiceClient.from_connection_string(conn_str)


@app.blob_trigger(arg_name="myblob", path="files/{name}",
                               connection="AzureWebJobsStorage")
def file_upload(myblob: func.InputStream):
    blob_name = myblob.name or "unknown"
    logger.info("Processing file: %s (%d bytes)", blob_name, myblob.length or 0)

    # Derive document_id from blob filename (format: <uuid>.<ext>)
    base_filename = blob_name.rsplit("/", 1)[-1]
    document_id = base_filename.rsplit(".", 1)[0] if "." in base_filename else base_filename

    # --- Set status to "processing" ---
    import time
    start_time = time.monotonic()

    try:
        blob_service = _get_blob_service_client()
        status_service.set_status(blob_service, document_id, "processing")
    except Exception:
        logger.warning("Could not set processing status for %s", document_id)
        blob_service = None

    try:
        # Read file into memory
        file_data = myblob.read()

        # --- Step 1: Extract content (route by file extension) ---
        ext = ("." + base_filename.rsplit(".", 1)[-1].lower()) if "." in base_filename else ""
        if ext == ".docx":
            from docx_extractor import extract_docx
            pages, metadata = extract_docx(file_data)
        else:
            pages, metadata = extract_pdf(file_data)
        logger.info("Extracted %d pages. Metadata: %s", len(pages), metadata.get("title", "N/A"))

        # --- Step 2: Identify scanned pages that need OCR ---
        scanned_pages = [p.page_number for p in pages if p.is_scanned]
        ocr_results = {}

        if scanned_pages and ext != ".docx":
            logger.info("Sending %d scanned page(s) to Document Intelligence for OCR", len(scanned_pages))
            try:
                ocr_results = ocr_pdf_pages(pdf_data=file_data, page_numbers=scanned_pages)
                logger.info("OCR complete for %d page(s)", len(ocr_results))
            except Exception:
                logger.exception("Document Intelligence OCR failed — scanned pages will have no text")

        # --- Step 3: Build accessible HTML ---
        html_content, image_files = build_html(
            pages=pages,
            ocr_results=ocr_results,
            metadata=metadata,
            embed_images=False,  # Store images as separate blobs
        )

        # --- Step 3b: Run WCAG validation on generated HTML ---
        from wcag_validator import validate_html as wcag_validate
        wcag_violations = wcag_validate(html_content)
        is_compliant = not any(
            v.severity in ("critical", "serious") for v in wcag_violations
        )
        if wcag_violations:
            logger.warning(
                "WCAG validation found %d violation(s) (compliant=%s)",
                len(wcag_violations),
                is_compliant,
            )

        # --- Step 3c: Collect OCR review flags ---
        review_pages: list[int] = []
        for page_num, ocr_page in ocr_results.items():
            if ocr_page.needs_review:
                review_pages.append(page_num + 1)  # 1-based for user-facing
        review_pages.sort()
        has_review_flags = len(review_pages) > 0

        # --- Step 4: Upload results to blob storage ---
        if blob_service is None:
            blob_service = _get_blob_service_client()
        container_client = blob_service.get_container_client(_OUTPUT_CONTAINER)

        # Ensure output container exists
        try:
            container_client.create_container()
        except Exception:
            pass  # Container already exists

        # Derive output path from input blob name
        # e.g. "files/report.pdf" -> "report"
        base_name = blob_name.rsplit("/", 1)[-1]
        for known_ext in (".pdf", ".docx", ".pptx"):
            if base_name.lower().endswith(known_ext):
                base_name = base_name[:-len(known_ext)]
                break

        # Upload HTML
        html_blob_name = f"{base_name}/{base_name}.html"
        container_client.upload_blob(
            name=html_blob_name,
            data=html_content.encode("utf-8"),
            overwrite=True,
            content_settings=ContentSettings(content_type="text/html; charset=utf-8"),
        )
        logger.info("Uploaded HTML: %s/%s", _OUTPUT_CONTAINER, html_blob_name)

        # Upload extracted images
        for img_filename, img_bytes in image_files.items():
            img_blob_name = f"{base_name}/images/{img_filename}"
            ext = img_filename.rsplit(".", 1)[-1].lower()
            mime = {"png": "image/png", "jpeg": "image/jpeg", "jpg": "image/jpeg"}.get(ext, "application/octet-stream")
            container_client.upload_blob(
                name=img_blob_name,
                data=img_bytes,
                overwrite=True,
                content_settings=ContentSettings(content_type=mime),
            )

        # --- Step 5: Set status to "completed" with metadata ---
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        try:
            status_service.set_status(
                blob_service,
                document_id,
                "completed",
                page_count=str(len(pages)),
                pages_processed=str(len(pages)),
                processing_time_ms=str(elapsed_ms),
                is_compliant=str(is_compliant),
                has_review_flags=str(has_review_flags),
                review_pages=str(review_pages),
                output_path=f"{_OUTPUT_CONTAINER}/{html_blob_name}",
            )
        except Exception:
            logger.exception("Could not update completed status for %s", document_id)

        logger.info(
            "Done. Uploaded %d image(s) for '%s' in %dms (compliant=%s, review_pages=%s)",
            len(image_files),
            blob_name,
            elapsed_ms,
            is_compliant,
            review_pages,
        )

    except Exception:
        # --- On error: set status to "failed" ---
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.exception("Conversion failed for %s", blob_name)
        try:
            if blob_service is None:
                blob_service = _get_blob_service_client()
            status_service.set_status(
                blob_service,
                document_id,
                "failed",
                error_message=f"Conversion failed after {elapsed_ms}ms",
                processing_time_ms=str(elapsed_ms),
            )
        except Exception:
            logger.exception("Could not set failed status for %s", document_id)


# ---------------------------------------------------------------------------
# T017: SAS token generation for browser-direct uploads
# ---------------------------------------------------------------------------

@app.route(route="upload/sas-token", methods=["POST"])
def generate_sas_token(req: func.HttpRequest) -> func.HttpResponse:
    """Generate a short-lived SAS token for direct browser-to-blob upload.

    Accepts JSON body: { filename, content_type, size_bytes }
    Returns JSON: { document_id, upload_url, expires_at }
    """
    # --- Parse & validate request body ------------------------------------
    try:
        body = req.get_json()
    except ValueError:
        return _json_error("Invalid JSON body", 400)

    filename = body.get("filename", "")
    content_type = body.get("content_type", "")
    size_bytes = body.get("size_bytes", 0)

    if not filename or not isinstance(filename, str):
        return _json_error("filename is required", 400)

    # Validate extension
    ext = _file_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        return _json_error(
            "Unsupported format. Accepted: .pdf, .docx, .pptx", 400
        )

    # Validate content type matches extension
    expected_ct = EXTENSION_CONTENT_TYPES.get(ext, "")
    if content_type != expected_ct:
        return _json_error(
            f"content_type must be '{expected_ct}' for {ext} files", 400
        )

    # Validate size
    if not isinstance(size_bytes, int) or size_bytes <= 0:
        return _json_error("size_bytes must be a positive integer", 400)
    if size_bytes > MAX_FILE_SIZE_BYTES:
        return _json_error("File exceeds 100MB limit", 400)

    # --- Generate document ID & SAS token ---------------------------------
    try:
        blob_service = _get_blob_service_client()
        document_id = str(uuid.uuid4())
        doc_format = ALLOWED_EXTENSIONS[ext].value
        doc_name = filename.rsplit(".", 1)[0] if "." in filename else filename
        blob_name = f"{document_id}{ext}"

        # Ensure the input container exists
        container_client = blob_service.get_container_client(_INPUT_CONTAINER)
        try:
            container_client.create_container()
        except Exception:
            pass  # already exists

        # Pre-create the blob with initial metadata so status tracking works
        # even before the upload completes.  Upload an empty placeholder;
        # the real content arrives via the SAS URL.
        initial_metadata = {
            "document_id": document_id,
            "name": doc_name,
            "format": doc_format,
            "size_bytes": str(size_bytes),
            "upload_timestamp": datetime.now(timezone.utc).isoformat(),
            "status": DocumentStatus.PENDING.value,
            "error_message": "",
            "page_count": "",
            "pages_processed": "0",
            "has_review_flags": "False",
            "blob_path": f"{_INPUT_CONTAINER}/{blob_name}",
            "output_path": "",
            "review_pages": "[]",
            "processing_time_ms": "",
            "is_compliant": "",
        }

        # Create blob placeholder (will be overwritten by browser upload)
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(b"", overwrite=True, metadata=initial_metadata)

        # Generate SAS token
        expiry = datetime.now(timezone.utc) + timedelta(
            minutes=_SAS_UPLOAD_EXPIRY_MINUTES
        )
        account_name = blob_service.account_name
        # Extract account key from connection string
        account_key = _extract_account_key(
            os.environ["AzureWebJobsStorage"]
        )

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=_INPUT_CONTAINER,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(write=True, create=True),
            expiry=expiry,
        )

        upload_url = f"https://{account_name}.blob.core.windows.net/{_INPUT_CONTAINER}/{blob_name}?{sas_token}"

        return func.HttpResponse(
            json.dumps({
                "document_id": document_id,
                "upload_url": upload_url,
                "expires_at": expiry.isoformat(),
            }),
            status_code=200,
            mimetype="application/json",
        )

    except Exception:
        logger.exception("Failed to generate SAS token")
        return _json_error("Storage service unavailable. Please retry.", 500)


# ---------------------------------------------------------------------------
# T018: Document status query
# ---------------------------------------------------------------------------

@app.route(route="documents/status", methods=["GET"])
def get_document_status(req: func.HttpRequest) -> func.HttpResponse:
    """Return processing status for a single document or all documents.

    Query params:
        document_id (optional): Return status for a single document.

    Returns JSON matching the status API contract.
    """
    try:
        blob_service = _get_blob_service_client()
        document_id = req.params.get("document_id")

        if document_id:
            doc = status_service.get_status(blob_service, document_id)
            if doc is None:
                return _json_error("Document not found", 404)
            return func.HttpResponse(
                json.dumps(doc.to_dict(), default=str),
                status_code=200,
                mimetype="application/json",
            )

        # List all documents with batch summary (single blob scan)
        documents = status_service.list_documents(blob_service)
        batch_summary = status_service.get_batch_summary(
            blob_service, documents=documents
        )

        return func.HttpResponse(
            json.dumps(
                {
                    "documents": [d.to_dict() for d in documents],
                    "summary": batch_summary,
                    "batch_summary": batch_summary,
                },
                default=str,
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception:
        logger.exception("Failed to query document status")
        return _json_error("Failed to retrieve document status", 500)


# ---------------------------------------------------------------------------
# T019: Download URL generation
# ---------------------------------------------------------------------------

@app.route(route="documents/{document_id}/download", methods=["GET"])
def get_download_url(req: func.HttpRequest) -> func.HttpResponse:
    """Generate time-limited download URLs for a completed conversion.

    Path param: document_id
    Returns JSON with html_url, preview_url, assets, zip_url, etc.
    """
    document_id = req.route_params.get("document_id", "")
    if not document_id:
        return _json_error("document_id is required", 400)

    try:
        blob_service = _get_blob_service_client()
        doc = status_service.get_status(blob_service, document_id)

        if doc is None:
            return _json_error("Document not found", 404)

        if doc.status == DocumentStatus.PROCESSING.value:
            return func.HttpResponse(
                json.dumps({
                    "error": "Document is still processing",
                    "status": "processing",
                }),
                status_code=409,
                mimetype="application/json",
            )

        if doc.status == DocumentStatus.PENDING.value:
            return func.HttpResponse(
                json.dumps({
                    "error": "Document is still processing",
                    "status": "pending",
                }),
                status_code=409,
                mimetype="application/json",
            )

        if doc.status == DocumentStatus.FAILED.value:
            return _json_error(
                f"Document conversion failed: {doc.error_message or 'unknown error'}",
                404,
            )

        # --- Document is completed — build download URLs ------------------
        account_name = blob_service.account_name
        account_key = _extract_account_key(os.environ["AzureWebJobsStorage"])
        expiry = datetime.now(timezone.utc) + timedelta(
            minutes=_SAS_DOWNLOAD_EXPIRY_MINUTES
        )

        base_name = doc.name
        html_blob = f"{base_name}/{base_name}.html"
        zip_blob = f"{base_name}/{base_name}.zip"

        html_url = _generate_download_sas_url(
            account_name, account_key, _OUTPUT_CONTAINER, html_blob, expiry
        )
        preview_url = html_url  # Same URL — contract specifies this

        # Discover image assets in the output container
        container_client = blob_service.get_container_client(_OUTPUT_CONTAINER)
        assets: list[dict] = []
        images_prefix = f"{base_name}/images/"
        try:
            for blob in container_client.list_blobs(name_starts_with=images_prefix):
                asset_url = _generate_download_sas_url(
                    account_name, account_key, _OUTPUT_CONTAINER, blob.name, expiry
                )
                assets.append({
                    "filename": blob.name.split("/")[-1],
                    "url": asset_url,
                    "size_bytes": blob.size or 0,
                })
        except Exception:
            logger.warning("Could not enumerate image assets for %s", document_id)

        # Zip URL (may not exist yet; URL is still valid per contract)
        zip_url = _generate_download_sas_url(
            account_name, account_key, _OUTPUT_CONTAINER, zip_blob, expiry
        )

        return func.HttpResponse(
            json.dumps({
                "document_id": document_id,
                "name": doc.name,
                "html_url": html_url,
                "preview_url": preview_url,
                "assets": assets,
                "zip_url": zip_url,
                "wcag_compliant": doc.is_compliant if doc.is_compliant is not None else True,
                "review_pages": doc.review_pages,
                "expires_at": expiry.isoformat(),
            }),
            status_code=200,
            mimetype="application/json",
        )

    except Exception:
        logger.exception("Failed to generate download URLs for %s", document_id)
        return _json_error("Failed to generate download URLs", 500)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _json_error(message: str, status_code: int) -> func.HttpResponse:
    """Return a JSON error response."""
    return func.HttpResponse(
        json.dumps({"error": message}),
        status_code=status_code,
        mimetype="application/json",
    )


def _file_extension(filename: str) -> str:
    """Extract the lowercase file extension including the dot."""
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


def _extract_account_key(connection_string: str) -> str:
    """Parse AccountKey from an Azure Storage connection string."""
    for part in connection_string.split(";"):
        part = part.strip()
        if part.lower().startswith("accountkey="):
            return part.split("=", 1)[1]
    raise ValueError("AccountKey not found in connection string")


def _generate_download_sas_url(
    account_name: str,
    account_key: str,
    container: str,
    blob_name: str,
    expiry: datetime,
) -> str:
    """Generate a read-only SAS URL for downloading a blob."""
    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=expiry,
    )
    return f"https://{account_name}.blob.core.windows.net/{container}/{blob_name}?{sas_token}"
