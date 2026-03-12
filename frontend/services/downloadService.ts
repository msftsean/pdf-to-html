/**
 * downloadService.ts — Document Download Service
 *
 * Handles fetching download URLs and triggering browser downloads for
 * converted HTML documents. Supports both single-file HTML download and
 * ZIP packaging (HTML + embedded images).
 *
 * Flow:
 * 1. Request a time-limited SAS download URL from the backend API.
 * 2. Fetch the HTML content from the SAS URL.
 * 3. Trigger a browser download (as .html or .zip).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DownloadUrlResponse {
  /** Signed URL for accessing the converted HTML file. */
  download_url: string;
  /** When the signed URL expires (ISO 8601). */
  expires_at: string;
  /** Original filename of the uploaded document. */
  filename: string;
  /** URLs for any images extracted alongside the HTML. */
  image_urls?: string[];
}

export type DownloadFormat = 'html' | 'zip';

// ---------------------------------------------------------------------------
// API Calls
// ---------------------------------------------------------------------------

/**
 * Fetch the download URL for a completed document.
 *
 * @param documentId  The unique document identifier returned at upload time.
 * @returns  The signed download URL and metadata.
 * @throws   If the document is not found, not yet completed, or the request fails.
 */
export async function getDownloadUrl(
  documentId: string
): Promise<DownloadUrlResponse> {
  if (!documentId) {
    throw new Error('Document ID is required.');
  }

  const response = await fetch(
    `${API_BASE}/documents/${encodeURIComponent(documentId)}/download`,
    {
      method: 'GET',
      headers: { Accept: 'application/json' },
    }
  );

  if (response.status === 404) {
    throw new Error(`Document not found: ${documentId}`);
  }

  if (response.status === 409) {
    throw new Error(
      'Document conversion is not yet complete. Please wait for processing to finish.'
    );
  }

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(
      `Failed to get download URL (HTTP ${response.status}): ${errorBody}`
    );
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Download Helpers
// ---------------------------------------------------------------------------

/**
 * Fetch content from a URL as a Blob.
 *
 * @param url  The URL to fetch content from.
 * @returns    The content as a Blob.
 */
async function fetchAsBlob(url: string): Promise<Blob> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch content (HTTP ${response.status})`);
  }
  return response.blob();
}

/**
 * Trigger a browser download for a Blob.
 *
 * Creates a temporary anchor element, sets the download attribute, clicks
 * it, and cleans up the object URL.
 *
 * @param blob      The Blob to download.
 * @param filename  The suggested filename for the download.
 */
export function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.style.display = 'none';
  document.body.appendChild(anchor);
  anchor.click();

  // Cleanup
  setTimeout(() => {
    URL.revokeObjectURL(url);
    document.body.removeChild(anchor);
  }, 100);
}

/**
 * Download a completed document as an HTML file.
 *
 * @param documentId  The unique document identifier.
 * @returns           The filename that was downloaded.
 */
export async function downloadAsHtml(documentId: string): Promise<string> {
  const { download_url, filename } = await getDownloadUrl(documentId);

  const blob = await fetchAsBlob(download_url);

  // Derive .html filename from the original
  const htmlFilename = filename.replace(/\.[^.]+$/, '.html');
  triggerBlobDownload(blob, htmlFilename);

  return htmlFilename;
}

/**
 * Download a completed document as a ZIP package (HTML + images).
 *
 * Uses the JSZip library if available, otherwise falls back to a simple
 * HTML-only download with a console warning.
 *
 * @param documentId  The unique document identifier.
 * @returns           The filename that was downloaded.
 */
export async function downloadAsZip(documentId: string): Promise<string> {
  const { download_url, filename, image_urls } =
    await getDownloadUrl(documentId);

  const htmlBlob = await fetchAsBlob(download_url);

  // If no images, just download as HTML
  if (!image_urls || image_urls.length === 0) {
    const htmlFilename = filename.replace(/\.[^.]+$/, '.html');
    triggerBlobDownload(htmlBlob, htmlFilename);
    return htmlFilename;
  }

  // Try dynamic import of JSZip for ZIP packaging
  try {
    const JSZip = (await import('jszip')).default;
    const zip = new JSZip();

    // Add HTML file
    const htmlFilename = filename.replace(/\.[^.]+$/, '.html');
    zip.file(htmlFilename, htmlBlob);

    // Add images in an images/ subdirectory
    const imagesFolder = zip.folder('images');
    if (imagesFolder) {
      const imagePromises = image_urls.map(async (imageUrl, index) => {
        try {
          const imageBlob = await fetchAsBlob(imageUrl);
          // Extract filename from URL, or generate one
          const urlParts = new URL(imageUrl).pathname.split('/');
          const imageName =
            urlParts[urlParts.length - 1] || `image-${index + 1}.png`;
          imagesFolder.file(imageName, imageBlob);
        } catch (err) {
          console.warn(`[downloadService] Failed to fetch image: ${imageUrl}`, err);
        }
      });
      await Promise.all(imagePromises);
    }

    const zipBlob = await zip.generateAsync({ type: 'blob' });
    const zipFilename = filename.replace(/\.[^.]+$/, '.zip');
    triggerBlobDownload(zipBlob, zipFilename);

    return zipFilename;
  } catch {
    // JSZip not available — fall back to HTML-only download
    console.warn(
      '[downloadService] JSZip not available. Downloading HTML only.'
    );
    const htmlFilename = filename.replace(/\.[^.]+$/, '.html');
    triggerBlobDownload(htmlBlob, htmlFilename);
    return htmlFilename;
  }
}

/**
 * Download a document in the specified format.
 *
 * Convenience wrapper that dispatches to the appropriate download function.
 *
 * @param documentId  The unique document identifier.
 * @param format      The desired download format ('html' or 'zip').
 * @returns           The filename that was downloaded.
 */
export async function downloadDocument(
  documentId: string,
  format: DownloadFormat = 'html'
): Promise<string> {
  if (format === 'zip') {
    return downloadAsZip(documentId);
  }
  return downloadAsHtml(documentId);
}
