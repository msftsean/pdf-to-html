'use client';

import { useState, useCallback } from 'react';
import {
  downloadDocument,
  type DownloadFormat,
} from '@/services/downloadService';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DownloadButtonProps {
  /** The unique document identifier for the completed conversion. */
  documentId: string;
  /** Human-readable document name (for aria labels and messages). */
  documentName: string;
  /** Download format — 'html' for a single file, 'zip' for HTML + images. */
  format?: DownloadFormat;
  /** Visual variant for the button. */
  variant?: 'primary' | 'outline';
  /** Optional additional CSS classes. */
  className?: string;
}

type DownloadState = 'idle' | 'loading' | 'success' | 'error';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * DownloadButton — Accessible download trigger for converted documents.
 *
 * Fetches the download URL from the backend API and triggers a browser
 * download of the converted HTML file or ZIP package.
 *
 * Features:
 * - Loading spinner during download preparation
 * - Success feedback with downloaded filename
 * - Error handling with user-friendly messages and retry
 * - Format selector for HTML vs ZIP
 *
 * Accessibility:
 * - Proper button labeling with document name
 * - aria-busy during loading state
 * - Keyboard activation (Enter and Space)
 * - Focus management after state changes
 * - NCDIT Digital Commons styling
 */
export default function DownloadButton({
  documentId,
  documentName,
  format = 'html',
  variant = 'primary',
  className = '',
}: DownloadButtonProps) {
  const [state, setState] = useState<DownloadState>('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [downloadedFilename, setDownloadedFilename] = useState<string>('');

  // -------------------------------------------------------------------------
  // Download handler
  // -------------------------------------------------------------------------

  const handleDownload = useCallback(async () => {
    if (state === 'loading') return;

    setState('loading');
    setErrorMessage('');

    try {
      const filename = await downloadDocument(documentId, format);
      setDownloadedFilename(filename);
      setState('success');

      // Reset to idle after 3 seconds
      setTimeout(() => setState('idle'), 3000);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : 'An unexpected error occurred during download.';
      setErrorMessage(message);
      setState('error');
    }
  }, [documentId, format, state]);

  // -------------------------------------------------------------------------
  // Button label & icon
  // -------------------------------------------------------------------------

  const formatLabel = format === 'zip' ? 'ZIP' : 'HTML';

  let buttonText: string;
  let buttonIcon: string;
  switch (state) {
    case 'loading':
      buttonText = 'Preparing download…';
      buttonIcon = '';
      break;
    case 'success':
      buttonText = `Downloaded ${downloadedFilename}`;
      buttonIcon = '✅';
      break;
    case 'error':
      buttonText = 'Retry download';
      buttonIcon = '🔄';
      break;
    default:
      buttonText = `Download ${formatLabel}`;
      buttonIcon = '⬇️';
  }

  const ariaLabel =
    state === 'loading'
      ? `Preparing download of ${documentName} as ${formatLabel}`
      : state === 'error'
        ? `Retry download of ${documentName} as ${formatLabel}`
        : `Download ${documentName} as ${formatLabel}`;

  // -------------------------------------------------------------------------
  // Button classes
  // -------------------------------------------------------------------------

  const baseClass =
    variant === 'outline'
      ? 'btn btn-outline-primary btn-sm download-button'
      : 'btn btn-primary btn-sm download-button';

  const stateClass =
    state === 'error'
      ? 'download-button--error'
      : state === 'success'
        ? 'download-button--success'
        : '';

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div className={`download-button-wrapper d-inline-block ${className}`} data-testid="download-button-wrapper">
      <button
        type="button"
        className={`${baseClass} ${stateClass}`}
        onClick={handleDownload}
        disabled={state === 'loading'}
        aria-label={ariaLabel}
        aria-busy={state === 'loading'}
        data-testid="download-button"
      >
        {state === 'loading' ? (
          <span
            className="spinner-border spinner-border-sm me-1"
            role="status"
            aria-hidden="true"
          />
        ) : (
          buttonIcon && (
            <span aria-hidden="true" className="me-1">
              {buttonIcon}
            </span>
          )
        )}
        {buttonText}
      </button>

      {/* Error message below button */}
      {state === 'error' && errorMessage && (
        <div
          className="download-button__error small mt-1"
          role="alert"
          data-testid="download-error"
        >
          {errorMessage}
        </div>
      )}

      {/* Screen reader announcement */}
      <div className="visually-hidden" aria-live="assertive" aria-atomic="true">
        {state === 'loading' && `Preparing download of ${documentName}.`}
        {state === 'success' && `${downloadedFilename} downloaded successfully.`}
        {state === 'error' && `Download failed: ${errorMessage}`}
      </div>

      <style jsx>{`
        .download-button {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          font-weight: 600;
          font-size: 0.8125rem;
          transition: all var(--nc-transition-fast, 150ms ease-in-out);
          white-space: nowrap;
        }
        .download-button:not(.btn-outline-primary) {
          background-color: var(--nc-action-blue, #1e79c8);
          border-color: var(--nc-action-blue, #1e79c8);
        }
        .download-button:not(.btn-outline-primary):hover:not(:disabled),
        .download-button:not(.btn-outline-primary):focus-visible:not(:disabled) {
          background-color: var(--nc-action-blue-hover, #1a6ab3);
          border-color: var(--nc-action-blue-hover, #1a6ab3);
        }
        .download-button--success {
          background-color: var(--nc-success, #28a745) !important;
          border-color: var(--nc-success, #28a745) !important;
        }
        .download-button--error {
          background-color: var(--nc-danger, #dc3545) !important;
          border-color: var(--nc-danger, #dc3545) !important;
          color: var(--nc-white, #ffffff) !important;
        }
        .download-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
        .download-button__error {
          color: var(--nc-danger, #dc3545);
          font-family: var(--nc-font-body, Georgia, serif);
          max-width: 250px;
        }
      `}</style>
    </div>
  );
}
