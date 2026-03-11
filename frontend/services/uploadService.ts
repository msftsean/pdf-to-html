/**
 * uploadService.ts — Document Upload Service
 *
 * Handles the two-step upload flow:
 * 1. Request a SAS token from the backend API
 * 2. Upload the file directly to Azure Blob Storage using the SAS URL
 *
 * Uses XMLHttpRequest for upload progress tracking (fetch API does not
 * support upload progress events).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SasTokenResponse {
  document_id: string;
  upload_url: string;
  expires_at: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

// ---------------------------------------------------------------------------
// Allowed file types
// ---------------------------------------------------------------------------

const ALLOWED_TYPES = new Set([
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  'application/vnd.openxmlformats-officedocument.presentationml.presentation', // .pptx
]);

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100 MB

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function validateFile(file: File): void {
  if (!ALLOWED_TYPES.has(file.type)) {
    throw new Error(
      `Unsupported file type: "${file.type || 'unknown'}". ` +
        'Please upload a PDF, DOCX, or PPTX file.'
    );
  }
  if (file.size > MAX_FILE_SIZE) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
    throw new Error(
      `File size (${sizeMB} MB) exceeds the 100 MB limit. ` +
        'Please upload a smaller file.'
    );
  }
}

// ---------------------------------------------------------------------------
// API Calls
// ---------------------------------------------------------------------------

/**
 * Request a SAS token from the backend for direct-to-blob upload.
 */
export async function requestSasToken(file: File): Promise<SasTokenResponse> {
  validateFile(file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename: file.name,
      content_type: file.type,
      file_size: file.size,
    }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(
      `Failed to request upload token (HTTP ${response.status}): ${errorBody}`
    );
  }

  return response.json();
}

/**
 * Upload a file directly to Azure Blob Storage using a SAS URL.
 *
 * Uses XMLHttpRequest for upload progress events — the Fetch API does not
 * support the `upload.onprogress` event needed for real-time progress bars.
 */
export function uploadFile(
  file: File,
  sasUrl: string,
  onProgress?: (progress: UploadProgress) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // Progress tracking
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress({
          loaded: event.loaded,
          total: event.total,
          percentage: Math.round((event.loaded / event.total) * 100),
        });
      }
    });

    // Completion
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(
          new Error(
            `Upload failed with status ${xhr.status}: ${xhr.statusText}`
          )
        );
      }
    });

    // Network error
    xhr.addEventListener('error', () => {
      reject(new Error('Upload failed due to a network error. Please check your connection and try again.'));
    });

    // Timeout
    xhr.addEventListener('timeout', () => {
      reject(new Error('Upload timed out. Please try again with a smaller file or better connection.'));
    });

    // Abort
    xhr.addEventListener('abort', () => {
      reject(new Error('Upload was cancelled.'));
    });

    // Azure Blob requires PUT with the correct content type header
    xhr.open('PUT', sasUrl);
    xhr.setRequestHeader('x-ms-blob-type', 'BlockBlob');
    xhr.setRequestHeader('Content-Type', file.type);
    xhr.timeout = 5 * 60 * 1000; // 5-minute timeout
    xhr.send(file);
  });
}

/**
 * Convenience function: request a SAS token, then upload the file.
 *
 * @returns The document_id assigned by the backend.
 */
export async function uploadDocument(
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<string> {
  // Step 1 — get SAS token
  const { document_id, upload_url } = await requestSasToken(file);

  // Step 2 — upload to blob storage
  await uploadFile(file, upload_url, onProgress);

  return document_id;
}
