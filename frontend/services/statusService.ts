/**
 * statusService.ts — Document Status Polling Service
 *
 * Provides real-time document processing status by polling the backend API.
 * Supports both single-document queries and batch status retrieval.
 *
 * Polling interval defaults to 3 seconds for active processing, with
 * automatic cleanup via a returned stop function.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DocumentStatus {
  document_id: string;
  name: string;
  format: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  page_count: number | null;
  pages_processed: number;
  has_review_flags: boolean;
  review_pages: number[];
  processing_time_ms: number | null;
  is_compliant: boolean | null;
  error_message: string | null;
  upload_timestamp: string;
}

export interface StatusSummary {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
}

export interface StatusResponse {
  documents: DocumentStatus[];
  summary: StatusSummary;
}

// ---------------------------------------------------------------------------
// API Calls
// ---------------------------------------------------------------------------

/**
 * Fetch status of all documents for the current session.
 */
export async function getDocumentStatuses(): Promise<StatusResponse> {
  const response = await fetch(`${API_BASE}/documents/status`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(
      `Failed to fetch document statuses (HTTP ${response.status}): ${errorBody}`
    );
  }

  return response.json();
}

/**
 * Fetch status of a single document by ID.
 */
export async function getDocumentStatus(
  documentId: string
): Promise<DocumentStatus> {
  if (!documentId) {
    throw new Error('Document ID is required.');
  }

  const response = await fetch(
    `${API_BASE}/documents/status?document_id=${encodeURIComponent(documentId)}`,
    {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    }
  );

  if (response.status === 404) {
    throw new Error(`Document not found: ${documentId}`);
  }

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(
      `Failed to fetch document status (HTTP ${response.status}): ${errorBody}`
    );
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Polling
// ---------------------------------------------------------------------------

/**
 * Start polling for document status updates.
 *
 * Calls the backend at a regular interval (default 3 seconds) and invokes
 * the `onUpdate` callback with fresh status data on each tick.
 *
 * @param onUpdate  Callback invoked with each status response.
 * @param intervalMs  Polling interval in milliseconds (default: 3000).
 * @returns A cleanup function that stops polling when called.
 *
 * @example
 * ```ts
 * const stopPolling = startPolling((response) => {
 *   setDocuments(response.documents);
 *   setSummary(response.summary);
 * });
 *
 * // Later — stop polling when component unmounts
 * stopPolling();
 * ```
 */
export function startPolling(
  onUpdate: (response: StatusResponse) => void,
  intervalMs: number = 3000
): () => void {
  // Guard: minimum interval of 1 second to avoid server overload
  const safeInterval = Math.max(intervalMs, 1000);
  let isActive = true;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  async function poll() {
    if (!isActive) return;

    try {
      const response = await getDocumentStatuses();
      if (isActive) {
        onUpdate(response);
      }
    } catch (error) {
      // Log but don't crash — next poll will retry
      console.error('[statusService] Polling error:', error);
    }

    // Schedule next poll only if still active
    if (isActive) {
      timeoutId = setTimeout(poll, safeInterval);
    }
  }

  // Start the first poll immediately
  poll();

  // Return cleanup function
  return () => {
    isActive = false;
    if (timeoutId !== null) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };
}
