'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DocumentPreviewProps {
  previewUrl: string;
  documentName: string;
  flaggedPages?: number[];
  onClose?: () => void;
}

type PreviewState = 'loading' | 'ready' | 'error';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * DocumentPreview — Accessible iframe preview of converted HTML output.
 *
 * Renders inside a sandboxed iframe with:
 * - Loading spinner
 * - OCR confidence warning banner
 * - Error state with retry
 * - Frosted glass card styling
 *
 * Accessibility:
 * - iframe has descriptive title
 * - aria-live region announces state transitions
 * - Keyboard-accessible controls
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

  // Load timeout
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
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [previewUrl, documentName]);

  const handleIframeLoad = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setState('ready');
    setAnnouncement(`Preview of ${documentName} loaded successfully.`);
  }, [documentName]);

  const handleIframeError = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setState('error');
    setAnnouncement('Preview failed to load. Please try again.');
  }, []);

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

  const hasFlaggedPages = flaggedPages.length > 0;

  return (
    <div
      className="preview-card"
      data-testid="document-preview"
      role="region"
      aria-label={`Preview of ${documentName}`}
    >
      {/* Screen reader announcements */}
      <div className="visually-hidden" aria-live="polite" aria-atomic="true">
        {announcement}
      </div>

      {/* Header */}
      <div className="preview-header">
        <h3 className="preview-title" title={documentName}>
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

      {/* OCR Warning */}
      {hasFlaggedPages && (
        <div className="preview-warning" role="alert" data-testid="confidence-warning">
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

      {/* Preview Body */}
      <div className="preview-body">
        {/* Loading */}
        {state === 'loading' && (
          <div className="preview-loading" data-testid="preview-loading" role="status">
            <div className="spinner-border mb-3" aria-hidden="true" />
            <p className="text-muted mb-0">Loading preview…</p>
          </div>
        )}

        {/* Error */}
        {state === 'error' && (
          <div className="preview-error" data-testid="preview-error">
            <span className="preview-error__icon" aria-hidden="true">⚠️</span>
            <p className="fw-semibold mb-2">Unable to load preview</p>
            <p className="text-muted mb-3" style={{ fontSize: '0.875rem' }}>
              The document preview could not be loaded. Please check your
              connection and try again.
            </p>
            <button
              type="button"
              className="btn btn-sm btn-outline-primary"
              onClick={handleRetry}
              data-testid="preview-retry-btn"
              aria-label={`Retry loading preview of ${documentName}`}
            >
              🔄 Retry
            </button>
          </div>
        )}

        {/* iframe */}
        <iframe
          ref={iframeRef}
          src={previewUrl}
          title={`Preview of converted document: ${documentName}`}
          className={`preview-iframe ${state !== 'ready' ? 'preview-iframe--hidden' : ''}`}
          sandbox="allow-same-origin"
          onLoad={handleIframeLoad}
          onError={handleIframeError}
          data-testid="preview-iframe"
          tabIndex={0}
        />
      </div>

      <style jsx>{`
        .preview-card {
          border-radius: var(--radius-lg);
          overflow: hidden;
          border: 1px solid var(--border);
          background: var(--card-bg);
        }

        .preview-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.75rem 1rem;
          background: var(--surface);
          border-bottom: 1px solid var(--border);
        }

        .preview-title {
          font-family: var(--font-heading);
          font-size: 1rem;
          font-weight: 600;
          color: var(--text-primary);
          margin: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .preview-warning {
          display: flex;
          align-items: flex-start;
          gap: 0.5rem;
          padding: 0.75rem 1rem;
          background: rgba(245, 158, 11, 0.08);
          border-bottom: 1px solid var(--border);
          border-left: 4px solid var(--accent-amber);
          font-size: 0.875rem;
          color: var(--text-primary);
        }

        .preview-body {
          position: relative;
        }

        .preview-loading,
        .preview-error {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 400px;
          background: var(--surface);
          font-family: var(--font-body);
        }

        .preview-error__icon {
          font-size: 2.5rem;
          margin-bottom: 0.75rem;
        }

        .preview-iframe {
          width: 100%;
          min-height: 500px;
          border: none;
          display: block;
          background: #fff;
        }

        .preview-iframe--hidden {
          position: absolute;
          opacity: 0;
          pointer-events: none;
        }
      `}</style>
    </div>
  );
}
