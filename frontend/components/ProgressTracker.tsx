'use client';

import { useCallback } from 'react';
import type { DocumentStatus } from '@/services/statusService';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ProgressTrackerProps {
  /** Array of documents with their current processing status. */
  documents: DocumentStatus[];
  /** Callback fired when the user clicks the retry button on a failed doc. */
  onRetry?: (documentId: string) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Human-readable label for each status. */
function statusLabel(status: DocumentStatus['status']): string {
  switch (status) {
    case 'pending':
      return 'Pending';
    case 'processing':
      return 'Processing';
    case 'completed':
      return 'Completed';
    case 'failed':
      return 'Failed';
    default:
      return 'Unknown';
  }
}

/** Bootstrap badge class variant per status. */
function badgeClass(status: DocumentStatus['status']): string {
  switch (status) {
    case 'pending':
      return 'bg-secondary';
    case 'processing':
      return 'bg-primary';
    case 'completed':
      return 'bg-success';
    case 'failed':
      return 'bg-danger';
    default:
      return 'bg-secondary';
  }
}

/** Status icon (decorative). */
function statusIcon(status: DocumentStatus['status']): string {
  switch (status) {
    case 'pending':
      return '⏳';
    case 'processing':
      return '🔄';
    case 'completed':
      return '✅';
    case 'failed':
      return '❌';
    default:
      return '❓';
  }
}

/** Calculate processing percentage for a document. */
function progressPercent(doc: DocumentStatus): number {
  if (doc.status === 'completed') return 100;
  if (doc.status === 'failed') return 0;
  if (doc.status === 'pending') return 0;
  if (doc.page_count && doc.page_count > 0) {
    return Math.round((doc.pages_processed / doc.page_count) * 100);
  }
  // Indeterminate — show a pulsing bar via CSS animation class
  return -1;
}

/** Format a timestamp string into a user-friendly date/time. */
function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-US', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * ProgressTracker — Real-time document conversion status list.
 *
 * Shows each document with:
 * - Color-coded status badge (pending=gray, processing=blue, completed=green, failed=red)
 * - Progress bar for in-progress documents (Bootstrap progress component)
 * - Error message for failed documents
 * - Retry button for failed documents
 *
 * Accessibility:
 * - aria-live="polite" region announces status changes to screen readers
 * - Keyboard-navigable list items & retry buttons
 * - All color badges include text labels (not color-only)
 * - Progress bars have aria-valuenow/aria-valuemin/aria-valuemax
 * - Sufficient color contrast (WCAG 2.1 AA)
 */
export default function ProgressTracker({
  documents,
  onRetry,
}: ProgressTrackerProps) {
  const handleRetry = useCallback(
    (documentId: string) => {
      onRetry?.(documentId);
    },
    [onRetry]
  );

  if (documents.length === 0) {
    return (
      <div className="progress-tracker" data-testid="progress-tracker">
        <div className="text-center py-5">
          <p className="text-muted mb-0" style={{ fontFamily: 'var(--nc-font-body, Georgia, serif)' }}>
            No documents uploaded yet. Upload documents to track their
            conversion progress.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="progress-tracker" data-testid="progress-tracker">
      {/* Screen reader live region — announces status changes */}
      <div className="visually-hidden" aria-live="polite" aria-atomic="true">
        {documents.map((doc) => (
          <span key={doc.document_id}>
            {doc.name}: {statusLabel(doc.status)}.{' '}
          </span>
        ))}
      </div>

      <ul
        className="progress-tracker__list list-unstyled mb-0"
        aria-label="Document conversion progress"
        role="list"
      >
        {documents.map((doc) => {
          const pct = progressPercent(doc);
          const isIndeterminate = pct === -1;

          return (
            <li
              key={doc.document_id}
              className="progress-tracker__item card mb-3 border-0 shadow-sm"
              data-testid={`document-item-${doc.document_id}`}
            >
              <div className="card-body p-3">
                {/* Header row: icon + filename + badge */}
                <div className="d-flex align-items-center justify-content-between flex-wrap gap-2">
                  <div className="d-flex align-items-center gap-2 min-w-0">
                    <span aria-hidden="true" className="progress-tracker__icon">
                      {statusIcon(doc.status)}
                    </span>
                    <div className="min-w-0">
                      <h3
                        className="progress-tracker__filename h6 mb-0 text-truncate"
                        title={doc.name}
                      >
                        {doc.name}
                      </h3>
                      <small className="text-muted">
                        Uploaded {formatTimestamp(doc.upload_timestamp)}
                      </small>
                    </div>
                  </div>

                  <span
                    className={`badge ${badgeClass(doc.status)} progress-tracker__badge`}
                    data-testid={`status-badge-${doc.document_id}`}
                  >
                    {doc.status === 'processing' && (
                      <span
                        className="spinner-border spinner-border-sm me-1"
                        role="status"
                        aria-hidden="true"
                      />
                    )}
                    {statusLabel(doc.status)}
                  </span>
                </div>

                {/* Progress bar — only for processing & pending */}
                {(doc.status === 'processing' || doc.status === 'pending') && (
                  <div className="mt-3">
                    <div className="d-flex justify-content-between mb-1">
                      <small className="text-muted">
                        {doc.status === 'pending'
                          ? 'Waiting to start…'
                          : isIndeterminate
                            ? 'Processing…'
                            : `${doc.pages_processed} of ${doc.page_count} pages`}
                      </small>
                      {!isIndeterminate && doc.status === 'processing' && (
                        <small className="fw-semibold">{pct}%</small>
                      )}
                    </div>
                    <div
                      className="progress"
                      role="progressbar"
                      aria-valuenow={isIndeterminate ? undefined : pct}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`${doc.name} conversion progress`}
                      style={{ height: '0.5rem' }}
                    >
                      <div
                        className={`progress-bar ${
                          doc.status === 'pending'
                            ? 'bg-secondary'
                            : 'progress-tracker__bar--active'
                        } ${isIndeterminate ? 'progress-bar-striped progress-bar-animated' : ''}`}
                        style={{
                          width: isIndeterminate
                            ? '100%'
                            : `${Math.max(pct, doc.status === 'pending' ? 0 : 5)}%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Completed details */}
                {doc.status === 'completed' && (
                  <div className="mt-2">
                    <small className="text-muted">
                      {doc.page_count} page{doc.page_count !== 1 ? 's' : ''}{' '}
                      converted
                      {doc.processing_time_ms != null && (
                        <> in {(doc.processing_time_ms / 1000).toFixed(1)}s</>
                      )}
                      {doc.has_review_flags && (
                        <span className="text-warning ms-2">
                          ⚠️ {doc.review_pages.length} page
                          {doc.review_pages.length !== 1 ? 's' : ''} flagged for
                          review
                        </span>
                      )}
                    </small>
                  </div>
                )}

                {/* Error state with retry */}
                {doc.status === 'failed' && (
                  <div className="mt-2" data-testid={`error-${doc.document_id}`}>
                    <div
                      className="alert alert-danger py-2 px-3 mb-2 d-flex align-items-start gap-2"
                      role="alert"
                    >
                      <span aria-hidden="true">⚠️</span>
                      <span>
                        {doc.error_message || 'An unexpected error occurred.'}
                      </span>
                    </div>
                    {onRetry && (
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-danger progress-tracker__retry-btn"
                        onClick={() => handleRetry(doc.document_id)}
                        aria-label={`Retry conversion of ${doc.name}`}
                        data-testid={`retry-btn-${doc.document_id}`}
                      >
                        🔄 Retry
                      </button>
                    )}
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ul>

      <style jsx>{`
        .progress-tracker__icon {
          font-size: 1.25rem;
          flex-shrink: 0;
        }
        .progress-tracker__filename {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          color: var(--nc-navy, #003366);
        }
        .progress-tracker__badge {
          font-size: 0.8125rem;
          font-weight: 600;
          padding: 0.35em 0.75em;
          white-space: nowrap;
        }
        .progress-tracker__bar--active {
          background-color: var(--nc-action-blue, #1e79c8);
        }
        .progress-tracker__retry-btn {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          font-size: 0.8125rem;
          font-weight: 600;
          border-color: var(--nc-danger, #dc3545);
          color: var(--nc-danger, #dc3545);
        }
        .progress-tracker__retry-btn:hover,
        .progress-tracker__retry-btn:focus-visible {
          background-color: var(--nc-danger, #dc3545);
          color: var(--nc-white, #ffffff);
        }
        .min-w-0 {
          min-width: 0;
        }
      `}</style>
    </div>
  );
}
