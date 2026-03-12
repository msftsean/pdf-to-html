'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import ProgressTracker from '@/components/ProgressTracker';
import DocumentPreview from '@/components/DocumentPreview';
import ConfirmDialog from '@/components/ConfirmDialog';
import {
  startPolling,
  type StatusResponse,
  type StatusSummary,
  type DocumentStatus,
} from '@/services/statusService';
import { deleteDocument, deleteAllDocuments } from '@/services/deleteService';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SummaryCard {
  label: string;
  value: number;
  variant: string; // Bootstrap color class
  icon: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Check if all documents have reached a terminal state
 * (completed or failed). Returns false if there are no documents.
 */
function allTerminal(documents: DocumentStatus[]): boolean {
  if (documents.length === 0) return false;
  return documents.every(
    (d) => d.status === 'completed' || d.status === 'failed'
  );
}

// ---------------------------------------------------------------------------
// Dashboard Page
// ---------------------------------------------------------------------------

/**
 * Dashboard Page — Real-time conversion progress tracking.
 *
 * US7 — Track Conversion Progress in Real-Time
 *
 * Features:
 * - Batch summary stats (total/pending/processing/completed/failed)
 * - ProgressTracker list showing each document
 * - Auto-refresh via statusService polling (3s default)
 * - Auto-stop polling when all documents reach terminal state
 * - Network error handling with retry
 *
 * Accessibility:
 * - Semantic heading hierarchy (h1 > h2)
 * - aria-live region for summary changes
 * - Keyboard-navigable cards and controls
 * - NCDIT Digital Commons styling
 */
export default function DashboardPage() {
  // -----------------------------------------------------------------------
  // State
  // -----------------------------------------------------------------------

  const [documents, setDocuments] = useState<DocumentStatus[]>([]);
  const [summary, setSummary] = useState<StatusSummary>({
    total: 0,
    pending: 0,
    processing: 0,
    completed: 0,
    failed: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const stopPollingRef = useRef<(() => void) | null>(null);

  // Preview modal state (T063)
  const [previewDoc, setPreviewDoc] = useState<DocumentStatus | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  // Delete state (T008 — individual delete)
  const [deleteTarget, setDeleteTarget] = useState<{id: string; name: string} | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const deleteTriggerRef = useRef<HTMLButtonElement | null>(null);

  // Clear All state (T009 — bulk delete)
  const [showClearAll, setShowClearAll] = useState(false);
  const [isClearingAll, setIsClearingAll] = useState(false);
  const clearAllTriggerRef = useRef<HTMLButtonElement | null>(null);

  // aria-live announcement (T010)
  const [announcement, setAnnouncement] = useState('');

  // -----------------------------------------------------------------------
  // Polling lifecycle (T052)
  // -----------------------------------------------------------------------

  const handleUpdate = useCallback((response: StatusResponse) => {
    setDocuments(response.documents);
    setSummary(response.summary);
    setIsLoading(false);
    setError(null);
  }, []);

  useEffect(() => {
    if (!isPolling) return;

    const stopFn = startPolling((response) => {
      handleUpdate(response);

      // Auto-stop when all documents are terminal
      if (allTerminal(response.documents)) {
        setIsPolling(false);
      }
    }, 3000);

    stopPollingRef.current = stopFn;

    return () => {
      stopFn();
      stopPollingRef.current = null;
    };
  }, [isPolling, handleUpdate]);

  // -----------------------------------------------------------------------
  // Error handling: patch the startPolling error path
  // We listen for failed fetches by wrapping the service's console.error
  // -----------------------------------------------------------------------

  useEffect(() => {
    const origConsoleError = console.error;
    console.error = (...args: unknown[]) => {
      const msg = args.join(' ');
      if (msg.includes('[statusService] Polling error')) {
        setError('Unable to reach the server. Retrying…');
        setIsLoading(false);
      }
      origConsoleError.apply(console, args);
    };

    return () => {
      console.error = origConsoleError;
    };
  }, []);

  // -----------------------------------------------------------------------
  // Retry handler (re-upload would need the original file — here we just
  // restart polling so the backend can re-process)
  // -----------------------------------------------------------------------

  const handleRetry = useCallback((documentId: string) => {
    // In a full implementation this would call the backend to re-trigger
    // processing. For now we restart polling so the user sees updates.
    setIsPolling(true);
    console.info(`[Dashboard] Retry requested for document: ${documentId}`);
  }, []);

  const handleManualRefresh = useCallback(() => {
    setIsPolling(true);
    setError(null);
  }, []);

  // -----------------------------------------------------------------------
  // Preview handler (T063)
  // -----------------------------------------------------------------------

  const handlePreview = useCallback((doc: DocumentStatus) => {
    setPreviewDoc(doc);
    setPreviewError(null);
    setPreviewLoading(false);
    // Use the server-side proxy so the browser never hits Azurite directly
    setPreviewUrl(`/api/preview/${doc.document_id}`);
  }, []);

  const handleClosePreview = useCallback(() => {
    setPreviewDoc(null);
    setPreviewUrl(null);
    setPreviewError(null);
    setPreviewLoading(false);
  }, []);

  // -----------------------------------------------------------------------
  // Announce helper (T010) — sets aria-live text, clears after 5s
  // -----------------------------------------------------------------------

  const announce = useCallback((text: string) => {
    setAnnouncement(text);
    const timer = setTimeout(() => setAnnouncement(''), 5000);
    return () => clearTimeout(timer);
  }, []);

  // -----------------------------------------------------------------------
  // Individual delete handlers (T008)
  // -----------------------------------------------------------------------

  const handleDeleteRequest = useCallback(
    (documentId: string, name: string) => {
      // Capture the trigger element for focus return (T012)
      const activeEl = document.activeElement;
      if (activeEl instanceof HTMLButtonElement) {
        deleteTriggerRef.current = activeEl;
      }
      setDeleteTarget({ id: documentId, name });
      setDeleteError(null);
    },
    []
  );

  const handleDeleteConfirm = useCallback(async () => {
    if (!deleteTarget) return;

    setIsDeleting(true);
    setDeleteError(null);

    try {
      await deleteDocument(deleteTarget.id);

      // Optimistically remove from state
      setDocuments((prev) =>
        prev.filter((d) => d.document_id !== deleteTarget.id)
      );
      setSummary((prev) => {
        const doc = documents.find((d) => d.document_id === deleteTarget.id);
        if (!doc) return prev;
        return {
          ...prev,
          total: Math.max(0, prev.total - 1),
          [doc.status]: Math.max(0, (prev[doc.status] || 0) - 1),
        };
      });

      announce(`${deleteTarget.name} has been deleted.`);
      setDeleteTarget(null);

      // Return focus to trigger (T012)
      setTimeout(() => {
        deleteTriggerRef.current?.focus();
        deleteTriggerRef.current = null;
      }, 100);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : 'Failed to delete document. Please try again.';
      setDeleteError(message);
      announce('Failed to delete document. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  }, [deleteTarget, documents, announce]);

  const handleDeleteCancel = useCallback(() => {
    setDeleteTarget(null);
    setDeleteError(null);

    // Return focus to trigger (T012)
    setTimeout(() => {
      deleteTriggerRef.current?.focus();
      deleteTriggerRef.current = null;
    }, 100);
  }, []);

  // -----------------------------------------------------------------------
  // Clear All handlers (T009)
  // -----------------------------------------------------------------------

  const handleClearAllRequest = useCallback(() => {
    const activeEl = document.activeElement;
    if (activeEl instanceof HTMLButtonElement) {
      clearAllTriggerRef.current = activeEl;
    }
    setShowClearAll(true);
    setDeleteError(null);
  }, []);

  const handleClearAllConfirm = useCallback(async () => {
    setIsClearingAll(true);
    setDeleteError(null);

    try {
      await deleteAllDocuments();

      // Clear all documents from state
      setDocuments([]);
      setSummary({
        total: 0,
        pending: 0,
        processing: 0,
        completed: 0,
        failed: 0,
      });

      // Stop polling — nothing to track
      setIsPolling(false);

      announce('All documents have been deleted.');
      setShowClearAll(false);

      // Return focus to trigger (T012)
      setTimeout(() => {
        clearAllTriggerRef.current?.focus();
        clearAllTriggerRef.current = null;
      }, 100);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : 'Failed to delete all documents. Please try again.';
      setDeleteError(message);
      announce('Failed to delete all documents. Please try again.');
    } finally {
      setIsClearingAll(false);
    }
  }, [announce]);

  const handleClearAllCancel = useCallback(() => {
    setShowClearAll(false);

    // Return focus to trigger (T012)
    setTimeout(() => {
      clearAllTriggerRef.current?.focus();
      clearAllTriggerRef.current = null;
    }, 100);
  }, []);

  // -----------------------------------------------------------------------
  // Summary cards config
  // -----------------------------------------------------------------------

  const summaryCards: SummaryCard[] = [
    { label: 'Total', value: summary.total, variant: 'nc-navy', icon: '📋' },
    {
      label: 'Pending',
      value: summary.pending,
      variant: 'secondary',
      icon: '⏳',
    },
    {
      label: 'Processing',
      value: summary.processing,
      variant: 'primary',
      icon: '🔄',
    },
    {
      label: 'Completed',
      value: summary.completed,
      variant: 'success',
      icon: '✅',
    },
    { label: 'Failed', value: summary.failed, variant: 'danger', icon: '❌' },
  ];

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  return (
    <>
      {/* ----------------------------------------------------------------
          Page Header
          ---------------------------------------------------------------- */}
      <section className="dashboard-hero" aria-labelledby="dashboard-heading">
        <div className="container py-4">
          <div className="d-flex align-items-center justify-content-between flex-wrap gap-3">
            <div>
              <h1
                id="dashboard-heading"
                className="dashboard-hero__title h3 mb-1"
              >
                Conversion Dashboard
              </h1>
              <p className="dashboard-hero__subtitle mb-0">
                Track your document conversions in real time.
              </p>
            </div>
            <Link
              href="/"
              className="btn btn-outline-light btn-sm dashboard-hero__link"
            >
              ← Upload More
            </Link>
          </div>
        </div>
      </section>

      <div className="container py-4">
        {/* ----------------------------------------------------------------
            Batch Summary Stats
            ---------------------------------------------------------------- */}
        <section aria-labelledby="summary-heading" className="mb-4">
          <h2 id="summary-heading" className="visually-hidden">
            Batch Summary
          </h2>

          {/* Live region for screen reader updates */}
          <div className="visually-hidden" aria-live="polite" aria-atomic="true">
            {`${summary.total} documents: ${summary.completed} completed, ${summary.processing} processing, ${summary.pending} pending, ${summary.failed} failed.`}
          </div>

          <div className="row g-3" data-testid="summary-cards">
            {summaryCards.map((card) => (
              <div key={card.label} className="col-6 col-md">
                <div
                  className={`card border-0 shadow-sm dashboard-summary-card ${
                    card.variant === 'nc-navy'
                      ? 'dashboard-summary-card--navy'
                      : ''
                  }`}
                  data-testid={`summary-card-${card.label.toLowerCase()}`}
                >
                  <div className="card-body text-center py-3 px-2">
                    <span
                      className="d-block mb-1"
                      style={{ fontSize: '1.25rem' }}
                      aria-hidden="true"
                    >
                      {card.icon}
                    </span>
                    <span
                      className={`d-block dashboard-summary-card__value ${
                        card.variant === 'nc-navy'
                          ? ''
                          : `text-${card.variant}`
                      }`}
                    >
                      {card.value}
                    </span>
                    <span className="d-block dashboard-summary-card__label">
                      {card.label}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ----------------------------------------------------------------
            aria-live announcements for delete outcomes (T010)
            ---------------------------------------------------------------- */}
        <div
          className="visually-hidden"
          aria-live="assertive"
          aria-atomic="true"
          data-testid="delete-announcement"
        >
          {announcement}
        </div>

        {/* ----------------------------------------------------------------
            Polling Status Indicator + Clear All (T009)
            ---------------------------------------------------------------- */}
        <div className="d-flex align-items-center justify-content-between mb-3">
          <h2 className="h5 mb-0">Documents</h2>
          <div className="d-flex align-items-center gap-2">
            {isPolling && (
              <span className="badge bg-info text-dark" data-testid="polling-badge">
                <span
                  className="spinner-grow spinner-grow-sm me-1"
                  role="status"
                  aria-hidden="true"
                />
                Auto-refreshing
              </span>
            )}
            {!isPolling && documents.length > 0 && (
              <button
                type="button"
                className="btn btn-sm btn-outline-secondary"
                onClick={handleManualRefresh}
                data-testid="refresh-btn"
              >
                🔄 Refresh
              </button>
            )}
            {documents.length > 0 && (
              <button
                type="button"
                className="btn btn-sm btn-outline-danger"
                onClick={handleClearAllRequest}
                aria-label="Delete all documents"
                data-testid="clear-all-btn"
              >
                🗑️ Clear All
              </button>
            )}
          </div>
        </div>

        {/* ----------------------------------------------------------------
            Error Banner
            ---------------------------------------------------------------- */}
        {error && (
          <div
            className="alert alert-warning d-flex align-items-center gap-2 mb-3"
            role="alert"
            data-testid="network-error"
          >
            <span aria-hidden="true">⚠️</span>
            <span>{error}</span>
            <button
              type="button"
              className="btn btn-sm btn-outline-warning ms-auto"
              onClick={handleManualRefresh}
            >
              Retry Now
            </button>
          </div>
        )}

        {/* ----------------------------------------------------------------
            Delete Error Banner (T008)
            ---------------------------------------------------------------- */}
        {deleteError && (
          <div
            className="alert alert-danger d-flex align-items-center gap-2 mb-3"
            role="alert"
            data-testid="delete-error"
          >
            <span aria-hidden="true">⚠️</span>
            <span>{deleteError}</span>
            <button
              type="button"
              className="btn-close ms-auto"
              aria-label="Dismiss error"
              onClick={() => setDeleteError(null)}
            />
          </div>
        )}

        {/* ----------------------------------------------------------------
            Loading Skeleton
            ---------------------------------------------------------------- */}
        {isLoading && (
          <div
            className="text-center py-5"
            data-testid="loading-state"
            role="status"
          >
            <div className="spinner-border text-primary mb-3" aria-hidden="true">
              <span className="visually-hidden">Loading…</span>
            </div>
            <p className="text-muted mb-0">Loading document statuses…</p>
          </div>
        )}

        {/* ----------------------------------------------------------------
            Document Progress List
            ---------------------------------------------------------------- */}
        {!isLoading && (
          <ProgressTracker
            documents={documents}
            onRetry={handleRetry}
            onPreview={handlePreview}
            onDelete={handleDeleteRequest}
          />
        )}

        {/* ----------------------------------------------------------------
            Preview Panel (T063)
            ---------------------------------------------------------------- */}
        {previewDoc && (
          <div
            className="dashboard-preview-overlay"
            data-testid="preview-overlay"
            role="dialog"
            aria-modal="true"
            aria-label={`Preview of ${previewDoc.name}`}
          >
            <div className="dashboard-preview-panel">
              {previewLoading && (
                <div
                  className="text-center py-5"
                  data-testid="preview-panel-loading"
                  role="status"
                >
                  <div className="spinner-border text-primary mb-3" aria-hidden="true" />
                  <p className="text-muted mb-0">Loading preview…</p>
                </div>
              )}

              {previewError && (
                <div
                  className="alert alert-danger m-4"
                  role="alert"
                  data-testid="preview-panel-error"
                >
                  <p className="mb-2">{previewError}</p>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-danger"
                    onClick={() => handlePreview(previewDoc)}
                  >
                    🔄 Retry
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary ms-2"
                    onClick={handleClosePreview}
                  >
                    Close
                  </button>
                </div>
              )}

              {previewUrl && !previewLoading && !previewError && (
                <DocumentPreview
                  previewUrl={previewUrl}
                  documentName={previewDoc.name}
                  flaggedPages={
                    previewDoc.has_review_flags ? previewDoc.review_pages : []
                  }
                  onClose={handleClosePreview}
                />
              )}
            </div>
          </div>
        )}
        {/* ----------------------------------------------------------------
            Individual Delete Confirmation Dialog (T008)
            ---------------------------------------------------------------- */}
        <ConfirmDialog
          isOpen={deleteTarget !== null}
          title="Delete Document"
          message={
            deleteTarget
              ? `Are you sure you want to permanently delete "${deleteTarget.name}"? This will remove the original file and all converted output. This action cannot be undone.`
              : ''
          }
          confirmLabel="Delete"
          cancelLabel="Cancel"
          variant="danger"
          onConfirm={handleDeleteConfirm}
          onCancel={handleDeleteCancel}
          isLoading={isDeleting}
        />

        {/* ----------------------------------------------------------------
            Clear All Confirmation Dialog (T009)
            ---------------------------------------------------------------- */}
        <ConfirmDialog
          isOpen={showClearAll}
          title="Clear All Documents"
          message={`Are you sure you want to permanently delete all ${documents.length} document(s)? This will remove all uploaded files and converted output. This action cannot be undone.`}
          confirmLabel="Delete All"
          cancelLabel="Cancel"
          variant="danger"
          onConfirm={handleClearAllConfirm}
          onCancel={handleClearAllCancel}
          isLoading={isClearingAll}
        />
      </div>

      {/* ----------------------------------------------------------------
          Styles
          ---------------------------------------------------------------- */}
      <style jsx>{`
        .dashboard-hero {
          background: linear-gradient(
            135deg,
            var(--nc-navy, #003366) 0%,
            var(--nc-navy-dark, #002244) 100%
          );
          color: var(--nc-white, #ffffff);
        }
        .dashboard-hero__title {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          color: var(--nc-white, #ffffff);
        }
        .dashboard-hero__subtitle {
          font-family: var(--nc-font-body, Georgia, serif);
          color: rgba(255, 255, 255, 0.85);
          font-size: 0.9375rem;
        }
        .dashboard-hero__link {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          font-weight: 600;
          font-size: 0.875rem;
          border-color: rgba(255, 255, 255, 0.5);
          color: var(--nc-white, #ffffff);
        }
        .dashboard-hero__link:hover,
        .dashboard-hero__link:focus-visible {
          background-color: rgba(255, 255, 255, 0.15);
          border-color: var(--nc-white, #ffffff);
          color: var(--nc-white, #ffffff);
        }

        .dashboard-summary-card {
          border-radius: var(--nc-radius-md, 0.375rem);
          transition: transform var(--nc-transition-fast, 150ms ease-in-out);
        }
        .dashboard-summary-card:hover {
          transform: translateY(-2px);
        }
        .dashboard-summary-card--navy {
          background-color: var(--nc-navy, #003366);
          color: var(--nc-white, #ffffff);
        }
        .dashboard-summary-card__value {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          font-size: 1.75rem;
          font-weight: bold;
          line-height: 1.2;
        }
        .dashboard-summary-card--navy .dashboard-summary-card__value {
          color: var(--nc-white, #ffffff);
        }
        .dashboard-summary-card__label {
          font-family: var(--nc-font-body, Georgia, serif);
          font-size: 0.8125rem;
          color: var(--nc-medium-gray, #6c757d);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .dashboard-summary-card--navy .dashboard-summary-card__label {
          color: rgba(255, 255, 255, 0.8);
        }

        .dashboard-preview-overlay {
          position: fixed;
          inset: 0;
          z-index: 1050;
          background-color: rgba(0, 0, 0, 0.6);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 1rem;
        }
        .dashboard-preview-panel {
          width: 100%;
          max-width: 960px;
          max-height: 90vh;
          overflow-y: auto;
          border-radius: var(--nc-radius-lg, 0.5rem);
          background-color: var(--nc-white, #ffffff);
          box-shadow: var(--nc-shadow-lg, 0 10px 30px rgba(0, 0, 0, 0.2));
        }
      `}</style>
    </>
  );
}
