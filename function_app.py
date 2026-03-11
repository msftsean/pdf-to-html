import io
import logging
import os

import azure.functions as func
from azure.storage.blob import BlobServiceClient, ContentSettings

from pdf_extractor import extract_pdf
from ocr_service import ocr_pdf_pages
from html_builder import build_html

app = func.FunctionApp()

logger = logging.getLogger(__name__)

# Output container for converted HTML and images
_OUTPUT_CONTAINER = os.environ.get("OUTPUT_CONTAINER", "converted")


def _get_blob_service_client() -> BlobServiceClient:
    conn_str = os.environ["AzureWebJobsStorage"]
    return BlobServiceClient.from_connection_string(conn_str)


@app.blob_trigger(arg_name="myblob", path="files/{name}",
                               connection="AzureWebJobsStorage")
def file_upload(myblob: func.InputStream):
    blob_name = myblob.name or "unknown"
    logger.info("Processing PDF: %s (%d bytes)", blob_name, myblob.length or 0)

    # Read the full PDF into memory
    pdf_data = myblob.read()

    # --- Step 1: Extract content with PyMuPDF ---
    pages, metadata = extract_pdf(pdf_data)
    logger.info("Extracted %d pages. Metadata: %s", len(pages), metadata.get("title", "N/A"))

    # --- Step 2: Identify scanned pages that need OCR ---
    scanned_pages = [p.page_number for p in pages if p.is_scanned]
    ocr_results = {}

    if scanned_pages:
        logger.info("Sending %d scanned page(s) to Document Intelligence for OCR", len(scanned_pages))
        try:
            ocr_results = ocr_pdf_pages(pdf_data, scanned_pages)
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

    # --- Step 4: Upload results to blob storage ---
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
    if base_name.lower().endswith(".pdf"):
        base_name = base_name[:-4]

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

    logger.info(
        "Done. Uploaded %d image(s) for '%s'",
        len(image_files),
        blob_name,
    )
