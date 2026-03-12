'use client';

import { useCallback } from 'react';
import type { DocumentStatus } from '@/services/statusService';
import DownloadButton from '@/components/DownloadButton';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ProgressTrackerProps {
  documents: DocumentStatus[];
  onRetry?: (documentId: string) => void;
  onPreview?: (doc: DocumentStatus) => void;
  onDelete?: (documentId: string, documentName: string) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function statusLabel(status: DocumentStatus['status']): string {
  switch (status) {
    case 'pending': return 'Pending';
    case 'processing': return 'Processing';
    case 'completed': return 'Completed';
    case 'failed': return 'Failed';
    default: return 'Unknown';
  }
}

function badgeVariant(status: DocumentStatus['status']): string {
  switch (status) {
    case 'pending': return 'bg-secondary';
    case 'processing': return 'bg-primary';
    case 'completed': return 'bg-success';
    case 'failed': return 'bg-danger';
    default: return 'bg-secondary';
  }
}

function statusBorderClass(status: DocumentStatus['status']): string {
  switch (status) {
    case 'pending': return 'doc-card--pending';
    case 'processing': return 'doc-card--processing';
    case 'completed': return 'doc-card--completed';
    case 'failed': return 'doc-card--failed';
    default: return '';
  }
}

function statusIcon(status: DocumentStatus['status']): string {
  switch (status) {
    case 'pending': return '⏳';
    case 'processing': return '🔄';
    case 'completed': return '✅';
    case 'failed': return '❌';
    default: return '❓';
  }
}

function progressPercent(doc: DocumentStatus): number {
  if (doc.status === 'completed') return 100;
  if (doc.status === 'failed') return 0;
  if (doc.status === 'pending') return 0;
  if (doc.page_count && doc.page_count > 0) {
    return Math.round((doc.pages_processed / doc.page_count) * 100);
  }
  return -1;
}

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
 * Each document renders as a card with status-colored left border,
 * badge pill, progress bar, and action buttons.
 *
 * Accessibility:
 * - aria-live="polite" region announces status changes
 * - Keyboard-navigable list items & buttons
 * - All color badges include text labels
 * - Progress bars have ARIA attributes
 */
export default function ProgressTracker({
  documents,
  onRetry,
  onPreview,
  onDelete,
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
        <div className="empty-state">
          <p className="text-muted mb-0">
            No documents uploaded yet. Upload documents to track their
            conversion progress.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="progress-tracker" data-testid="progress-tracker">
      {/* Screen reader live region */}
      <div className="visually-hidden" aria-live="polite" aria-atomic="true">
        {documents.map((doc) => (
          <span key={doc.document_id}>
            {doc.name}: {statusLabel(doc.status)}.{' '}
          </span>
        ))}
      </div>

      <ul className="doc-list" aria-label="Document conversion progress" role="list">
        {documents.map((doc, i) => {
          const pct = progressPercent(doc);
          const isIndeterminate = pct === -1;

          return (
            <li
              key={doc.document_id}
              className={`doc-card ${statusBorderClass(doc.status)} animate-fadeInUp delay-${Math.min(i + 1, 4)}`}
              data-testid={`document-item-${doc.document_id}`}
            >
              <div className="doc-card__body">
                {/* Header: icon + filename + badge */}
                <div className="doc-card__header">
                  <div className="doc-card__info">
                    <span aria-hidden="true" className="doc-card__icon">
                      {statusIcon(doc.status)}
                    </span>
                    <div className="doc-card__meta">
                      <h3 className="doc-card__filename" title={doc.name}>
                        {doc.name}
                      </h3>
                      <span className="doc-card__timestamp">
                        Uploaded {formatTimestamp(doc.upload_timestamp)}
                      </span>
                    </div>
                  </div>

                  <span
                    className={`badge ${badgeVariant(doc.status)}`}
                    data-testid={`status-badge-${doc.document_id}`}
                  >
                    {doc.status === 'processing' && (
                      <span className="spinner-grow spinner-grow-sm" role="status" aria-hidden="true" />
                    )}
                    {statusLabel(doc.status)}
                  </span>
                </div>

                {/* Progress bar */}
                {(doc.status === 'processing' || doc.status === 'pending') && (
                  <div className="doc-card__progress">
                    <div className="doc-card__progress-label">
                      <span className="text-muted">
                        {doc.status === 'pending'
                          ? 'Waiting to start…'
                          : isIndeterminate
                            ? 'Processing…'
                            : `${doc.pages_processed} of ${doc.page_count} pages`}
                      </span>
                      {!isIndeterminate && doc.status === 'processing' && (
                        <span className="fw-semibold">{pct}%</span>
                      )}
                    </div>
                    <div
                      className="progress"
                      role="progressbar"
                      aria-valuenow={isIndeterminate ? undefined : pct}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`${doc.name} conversion progress`}
                    >
                      <div
                        className={`progress-bar ${isIndeterminate ? 'progress-bar-striped progress-bar-animated' : ''}`}
                        style={{
                          width: isIndeterminate
                            ? '100%'
                            : `${Math.max(pct, doc.status === 'pending' ? 0 : 5)}%`,
                          background: doc.status === 'pending' ? 'var(--text-muted)' : undefined,
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Completed details */}
                {doc.status === 'completed' && (
                  <div className="doc-card__completed">
                    <span className="doc-card__completed-info">
                      {doc.page_count} page{doc.page_count !== 1 ? 's' : ''}{' '}
                      converted
                      {doc.processing_time_ms != null && (
                        <> in {(doc.processing_time_ms / 1000).toFixed(1)}s</>
                      )}
                      {doc.has_review_flags && (
                        <span className="text-warning ms-2">
                          ⚠️ {doc.review_pages.length} page
                          {doc.review_pages.length !== 1 ? 's' : ''} flagged for review
                        </span>
                      )}
                    </span>

                    <div className="doc-card__actions" data-testid={`actions-${doc.document_id}`}>
                      {onPreview && (
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => onPreview(doc)}
                          aria-label={`Preview converted output of ${doc.name}`}
                          data-testid={`preview-btn-${doc.document_id}`}
                        >
                          <span aria-hidden="true">👁️</span> Preview
                        </button>
                      )}
                      <DownloadButton
                        documentId={doc.document_id}
                        documentName={doc.name}
                        format="html"
                        variant="primary"
                      />
                      <DownloadButton
                        documentId={doc.document_id}
                        documentName={doc.name}
                        format="zip"
                        variant="outline"
                      />
                      {onDelete && (
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-danger ms-auto"
                          onClick={() => onDelete(doc.document_id, doc.name)}
                          aria-label={`Delete ${doc.name}`}
                          data-testid={`delete-btn-${doc.document_id}`}
                        >
                          <span aria-hidden="true">🗑️</span> Delete
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Error state */}
                {doc.status === 'failed' && (
                  <div className="doc-card__error" data-testid={`error-${doc.document_id}`}>
                    <div className="alert alert-danger" role="alert">
                      <span aria-hidden="true">⚠️</span>{' '}
                      {doc.error_message || 'An unexpected error occurred.'}
                    </div>
                    <div className="doc-card__actions">
                      {onRetry && (
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-danger"
                          onClick={() => handleRetry(doc.document_id)}
                          aria-label={`Retry conversion of ${doc.name}`}
                          data-testid={`retry-btn-${doc.document_id}`}
                        >
                          🔄 Retry
                        </button>
                      )}
                      {onDelete && (
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-danger"
                          onClick={() => onDelete(doc.document_id, doc.name)}
                          aria-label={`Delete ${doc.name}`}
                          data-testid={`delete-btn-${doc.document_id}`}
                        >
                          <span aria-hidden="true">🗑️</span> Delete
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {/* Delete for pending */}
                {doc.status === 'pending' && onDelete && (
                  <div className="mt-2">
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => onDelete(doc.document_id, doc.name)}
                      aria-label={`Delete ${doc.name}`}
                      data-testid={`delete-btn-${doc.document_id}`}
                    >
                      <span aria-hidden="true">🗑️</span> Delete
                    </button>
                  </div>
                )}

                {/* Delete for processing (disabled) */}
                {doc.status === 'processing' && onDelete && (
                  <div className="mt-2">
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-danger"
                      disabled
                      aria-disabled="true"
                      title="Cannot delete while processing"
                      aria-label={`Delete ${doc.name} — cannot delete while processing`}
                      data-testid={`delete-btn-${doc.document_id}`}
                    >
                      <span aria-hidden="true">🗑️</span> Delete
                    </button>
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ul>

      <style jsx>{`
        .empty-state {
          text-align: center;
          padding: 3rem 1rem;
          font-family: var(--font-body);
        }

        .doc-list {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .doc-card {
          background: var(--card-bg);
          border: 1px solid var(--border);
          border-radius: var(--radius-lg);
          border-left: 4px solid var(--text-muted);
          transition: all var(--transition-fast);
        }

        .doc-card:hover {
          border-color: var(--border-hover);
        }

        .doc-card--pending { border-left-color: var(--text-muted); }
        .doc-card--processing { border-left-color: var(--accent-sky); }
        .doc-card--completed { border-left-color: var(--accent-emerald); }
        .doc-card--failed { border-left-color: var(--accent-red); }

        .doc-card__body {
          padding: 1rem 1.25rem;
        }

        .doc-card__header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .doc-card__info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          min-width: 0;
          flex: 1;
        }

        .doc-card__icon {
          font-size: 1.25rem;
          flex-shrink: 0;
        }

        .doc-card__meta {
          min-width: 0;
        }

        .doc-card__filename {
          font-family: var(--font-heading);
          font-size: 1rem;
          font-weight: 600;
          color: var(--text-primary);
          margin: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .doc-card__timestamp {
          font-size: 0.8125rem;
          color: var(--text-muted);
        }

        .doc-card__progress {
          margin-top: 0.75rem;
        }

        .doc-card__progress-label {
          display: flex;
          justify-content: space-between;
          margin-bottom: 0.35rem;
          font-size: 0.8125rem;
        }

        .doc-card__completed {
          margin-top: 0.5rem;
        }

        .doc-card__completed-info {
          font-size: 0.8125rem;
          color: var(--text-muted);
          display: block;
          margin-bottom: 0.5rem;
        }

        .doc-card__actions {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .doc-card__error {
          margin-top: 0.5rem;
        }
      `}</style>
    </div>
  );
}
