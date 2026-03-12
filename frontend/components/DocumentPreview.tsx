'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DocumentPreviewProps {
  /** Signed URL for the converted HTML document. */
  previewUrl: string;
  /** Document name displayed in the header. */
  documentName: string;
  /** Page numbers flagged for manual review (low OCR confidence). */
  flaggedPages?: number[];
  /** Optional callback when the user closes the preview. */
  onClose?: () => void;
}

type PreviewState = 'loading' | 'ready' | 'error';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * DocumentPreview — Accessible iframe preview of converted HTML output.
 *
 * Renders the converted HTML document inside a sandboxed iframe with:
 * - Loading skeleton while the HTML loads
 * - OCR confidence warning banner for flagged pages
 * - Error state with retry button if the preview fails
 * - Full WCAG compliance: iframe title, keyboard navigation, aria-live
 *
 * Accessibility:
 * - iframe has descriptive title for screen readers
 * - aria-live region announces state transitions
 * - Keyboard-accessible close and retry buttons
 * - Proper focus management
 * - NCDIT Digital Commons card styling
 */
export default function DocumentPreview({
  previewUrl,
  documentName,
  flaggedPages = [],
  onClose,
}: DocumentPreviewProps) {
  const [state, setState] = useState<PreviewState>('loading');
  const [announcement, setAnnouncement] = useState('');
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // -------------------------------------------------------------------------
  // Load timeout — if iframe doesn't load within 30s, show error
  // -------------------------------------------------------------------------

  useEffect(() => {
    setState('loading');
    setAnnouncement(`Loading preview of ${documentName}`);

    timeoutRef.current = setTimeout(() => {
      if (state === 'loading') {
        setState('error');
        setAnnouncement('Preview failed to load. Please try again.');
      }
    }, 30000);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
    // Only reset when URL changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [previewUrl, documentName]);

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  const handleIframeLoad = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setState('ready');
    setAnnouncement(`Preview of ${documentName} loaded successfully.`);
  }, [documentName]);

  const handleIframeError = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setState('error');
    setAnnouncement('Preview failed to load. Please try again.');
  }, []);

  // Attach error listener via ref — iframe error events don't bubble in all
  // environments (notably jsdom), so we use addEventListener directly.
  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;

    iframe.addEventListener('error', handleIframeError);
    return () => {
      iframe.removeEventListener('error', handleIframeError);
    };
  }, [handleIframeError]);

  const handleRetry = useCallback(() => {
    setState('loading');
    setAnnouncement(`Retrying preview of ${documentName}`);

    // Force iframe reload by toggling src
    if (iframeRef.current) {
      const src = iframeRef.current.src;
      iframeRef.current.src = '';
      requestAnimationFrame(() => {
        if (iframeRef.current) {
          iframeRef.current.src = src;
        }
      });
    }

    timeoutRef.current = setTimeout(() => {
      setState('error');
      setAnnouncement('Preview failed to load. Please try again.');
    }, 30000);
  }, [documentName]);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  const hasFlaggedPages = flaggedPages.length > 0;

  return (
    <div
      className="document-preview card border-0 shadow-sm"
      data-testid="document-preview"
      role="region"
      aria-label={`Preview of ${documentName}`}
    >
      {/* Screen reader announcements */}
      <div className="visually-hidden" aria-live="polite" aria-atomic="true">
        {announcement}
      </div>

      {/* ----------------------------------------------------------------
          Card Header
          ---------------------------------------------------------------- */}
      <div className="card-header document-preview__header d-flex align-items-center justify-content-between">
        <h3 className="document-preview__title h6 mb-0 text-truncate" title={documentName}>
          <span aria-hidden="true" className="me-2">📄</span>
          {documentName}
        </h3>
        {onClose && (
          <button
            type="button"
            className="btn-close btn-close-white"
            onClick={onClose}
            aria-label={`Close preview of ${documentName}`}
            data-testid="preview-close-btn"
          />
        )}
      </div>

      {/* ----------------------------------------------------------------
          OCR Confidence Warning Banner
          ---------------------------------------------------------------- */}
      {hasFlaggedPages && (
        <div
          className="document-preview__warning alert alert-warning mb-0 rounded-0 py-2 px-3 d-flex align-items-start gap-2"
          role="alert"
          data-testid="confidence-warning"
        >
          <span aria-hidden="true">⚠️</span>
          <div>
            <strong>Quality Review Needed:</strong>{' '}
            {flaggedPages.length} page{flaggedPages.length !== 1 ? 's' : ''}{' '}
            flagged for manual review due to low OCR confidence
            (page{flaggedPages.length !== 1 ? 's' : ''}{' '}
            {flaggedPages.join(', ')}).
          </div>
        </div>
      )}

      {/* ----------------------------------------------------------------
          Preview Body
          ---------------------------------------------------------------- */}
      <div className="card-body p-0 position-relative">
        {/* Loading skeleton */}
        {state === 'loading' && (
          <div
            className="document-preview__loading d-flex flex-column align-items-center justify-content-center"
            data-testid="preview-loading"
            role="status"
          >
            <div className="spinner-border text-primary mb-3" aria-hidden="true" />
            <p className="text-muted mb-0">Loading preview…</p>
          </div>
        )}

        {/* Error state */}
        {state === 'error' && (
          <div
            className="document-preview__error d-flex flex-column align-items-center justify-content-center"
            data-testid="preview-error"
          >
            <span className="document-preview__error-icon mb-3" aria-hidden="true">⚠️</span>
            <p className="fw-semibold mb-2">Unable to load preview</p>
            <p className="text-muted small mb-3">
              The document preview could not be loaded. Please check your
              connection and try again.
            </p>
            <button
              type="button"
              className="btn btn-outline-primary btn-sm document-preview__retry-btn"
              onClick={handleRetry}
              data-testid="preview-retry-btn"
              aria-label={`Retry loading preview of ${documentName}`}
            >
              🔄 Retry
            </button>
          </div>
        )}

        {/* iframe preview */}
        <iframe
          ref={iframeRef}
          src={previewUrl}
          title={`Preview of converted document: ${documentName}`}
          className={`document-preview__iframe ${state !== 'ready' ? 'document-preview__iframe--hidden' : ''}`}
          sandbox="allow-same-origin"
          loading="lazy"
          onLoad={handleIframeLoad}
          onError={handleIframeError}
          data-testid="preview-iframe"
          tabIndex={0}
        />
      </div>

      {/* ----------------------------------------------------------------
          Styles
          ---------------------------------------------------------------- */}
      <style jsx>{`
        .document-preview {
          border-radius: var(--nc-radius-md, 0.375rem);
          overflow: hidden;
        }
        .document-preview__header {
          background-color: var(--nc-navy, #003366);
          color: var(--nc-white, #ffffff);
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          padding: 0.75rem 1rem;
          border-bottom: none;
        }
        .document-preview__title {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          color: var(--nc-white, #ffffff);
        }
        .document-preview__loading,
        .document-preview__error {
          min-height: 400px;
          background-color: var(--nc-light-gray, #f5f5f5);
          font-family: var(--nc-font-body, Georgia, serif);
        }
        .document-preview__error-icon {
          font-size: 2.5rem;
        }
        .document-preview__retry-btn {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          font-weight: 600;
          font-size: 0.8125rem;
          border-color: var(--nc-action-blue, #1e79c8);
          color: var(--nc-action-blue, #1e79c8);
        }
        .document-preview__retry-btn:hover,
        .document-preview__retry-btn:focus-visible {
          background-color: var(--nc-action-blue, #1e79c8);
          border-color: var(--nc-action-blue, #1e79c8);
          color: var(--nc-white, #ffffff);
        }
        .document-preview__iframe {
          width: 100%;
          min-height: 500px;
          border: none;
          display: block;
        }
        .document-preview__iframe--hidden {
          position: absolute;
          width: 1px;
          height: 1px;
          overflow: hidden;
          clip: rect(0, 0, 0, 0);
        }
      `}</style>
    </div>
  );
}
