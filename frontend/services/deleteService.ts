/**
 * deleteService.ts — Document Deletion API Client
 *
 * Provides functions to delete individual documents or clear all documents
 * from the conversion dashboard. Communicates with the backend DELETE
 * endpoints via native fetch.
 *
 * Uses the same API_BASE pattern as statusService.ts for consistency.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DeleteResponse {
  message: string;
  document_id: string;
}

export interface DeleteAllResponse {
  message: string;
  deleted_input: number;
  deleted_output: number;
}

// ---------------------------------------------------------------------------
// API Calls
// ---------------------------------------------------------------------------

/**
 * Delete a single document by ID.
 *
 * Sends DELETE to /api/documents/{documentId}. Removes the input blob,
 * converted HTML output, and all associated image assets from storage.
 *
 * @param documentId  The unique identifier of the document to delete.
 * @returns Parsed JSON response with confirmation message and document ID.
 * @throws Error with user-friendly message on failure (404, 409, 500).
 */
export async function deleteDocument(
  documentId: string
): Promise<DeleteResponse> {
  if (!documentId) {
    throw new Error('Document ID is required.');
  }

  const response = await fetch(
    `${API_BASE}/documents/${encodeURIComponent(documentId)}`,
    {
      method: 'DELETE',
      headers: { 'Accept': 'application/json' },
    }
  );

  if (response.status === 404) {
    throw new Error('Document not found. It may have already been deleted.');
  }

  if (response.status === 409) {
    throw new Error(
      'Cannot delete a document while it is being processed. Please wait for processing to complete.'
    );
  }

  if (!response.ok) {
    let errorDetail = '';
    try {
      const body = await response.json();
      errorDetail = body.error || body.message || '';
    } catch {
      errorDetail = await response.text().catch(() => '');
    }
    throw new Error(
      errorDetail || `Failed to delete document (HTTP ${response.status}).`
    );
  }

  return response.json();
}

/**
 * Delete all documents (clear all).
 *
 * Sends DELETE to /api/documents. Removes all input blobs and all
 * converted output from storage.
 *
 * @returns Parsed JSON response with deletion counts.
 * @throws Error with user-friendly message on failure.
 */
export async function deleteAllDocuments(): Promise<DeleteAllResponse> {
  const response = await fetch(`${API_BASE}/documents`, {
    method: 'DELETE',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    let errorDetail = '';
    try {
      const body = await response.json();
      errorDetail = body.error || body.message || '';
    } catch {
      errorDetail = await response.text().catch(() => '');
    }
    throw new Error(
      errorDetail || `Failed to delete all documents (HTTP ${response.status}).`
    );
  }

  return response.json();
}
