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
  documentId: string;
  documentName: string;
  format?: DownloadFormat;
  variant?: 'primary' | 'outline';
  className?: string;
}

type DownloadState = 'idle' | 'loading' | 'success' | 'error';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * DownloadButton — Accessible download trigger for converted documents.
 *
 * Accessibility:
 * - Proper button labeling with document name
 * - aria-busy during loading state
 * - Keyboard activation
 * - Focus management after state changes
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

  const handleDownload = useCallback(async () => {
    if (state === 'loading') return;

    setState('loading');
    setErrorMessage('');

    try {
      const filename = await downloadDocument(documentId, format);
      setDownloadedFilename(filename);
      setState('success');
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

  const btnClass = variant === 'outline'
    ? 'btn btn-sm btn-outline-primary'
    : 'btn btn-sm btn-primary';

  const stateClass =
    state === 'error' ? 'dl-btn--error' : state === 'success' ? 'dl-btn--success' : '';

  return (
    <div className={`dl-wrapper ${className}`} data-testid="download-button-wrapper">
      <button
        type="button"
        className={`${btnClass} dl-btn ${stateClass}`}
        onClick={handleDownload}
        disabled={state === 'loading'}
        aria-label={ariaLabel}
        aria-busy={state === 'loading'}
        data-testid="download-button"
      >
        {state === 'loading' ? (
          <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true" />
        ) : (
          buttonIcon && <span aria-hidden="true">{buttonIcon}</span>
        )}
        {buttonText}
      </button>

      {state === 'error' && errorMessage && (
        <div className="dl-error" role="alert" data-testid="download-error">
          {errorMessage}
        </div>
      )}

      <div className="visually-hidden" aria-live="assertive" aria-atomic="true">
        {state === 'loading' && `Preparing download of ${documentName}.`}
        {state === 'success' && `${downloadedFilename} downloaded successfully.`}
        {state === 'error' && `Download failed: ${errorMessage}`}
      </div>

      <style jsx>{`
        .dl-wrapper {
          display: inline-block;
        }

        .dl-btn {
          white-space: nowrap;
        }

        .dl-btn--success {
          background-color: var(--accent-emerald) !important;
          border-color: var(--accent-emerald) !important;
          color: #fff !important;
        }

        .dl-btn--error {
          background-color: var(--accent-red) !important;
          border-color: var(--accent-red) !important;
          color: #fff !important;
        }

        .dl-error {
          color: var(--accent-red);
          font-family: var(--font-body);
          font-size: 0.8125rem;
          margin-top: 0.25rem;
          max-width: 250px;
        }
      `}</style>
    </div>
  );
}
