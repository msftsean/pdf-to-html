'use client';

import { useEffect, useRef, useCallback } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning';
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * ConfirmDialog — WCAG 2.1 AA accessible confirmation modal.
 *
 * Frosted glass dialog with smooth animations.
 *
 * Accessibility:
 * - Focus trap (Tab cycles within the dialog)
 * - Escape key closes the dialog
 * - Backdrop overlay click closes the dialog
 * - role="dialog", aria-modal="true", aria-labelledby
 * - Focus management: cancel button focused on open
 */
export default function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = 'Delete',
  cancelLabel = 'Cancel',
  variant = 'danger',
  onConfirm,
  onCancel,
  isLoading = false,
}: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const cancelBtnRef = useRef<HTMLButtonElement>(null);
  const confirmBtnRef = useRef<HTMLButtonElement>(null);

  // Focus cancel button on open
  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        cancelBtnRef.current?.focus();
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  // Body scroll lock
  useEffect(() => {
    if (isOpen) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [isOpen]);

  // Keyboard: Escape + Tab trap
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape' && !isLoading) {
        e.preventDefault();
        onCancel();
        return;
      }

      if (e.key === 'Tab') {
        const focusableElements = dialogRef.current?.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );

        if (!focusableElements || focusableElements.length === 0) return;

        const firstEl = focusableElements[0];
        const lastEl = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstEl) {
            e.preventDefault();
            lastEl.focus();
          }
        } else {
          if (document.activeElement === lastEl) {
            e.preventDefault();
            firstEl.focus();
          }
        }
      }
    },
    [isLoading, onCancel]
  );

  // Backdrop click
  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget && !isLoading) {
        onCancel();
      }
    },
    [isLoading, onCancel]
  );

  if (!isOpen) return null;

  const confirmBtnClass =
    variant === 'warning' ? 'btn btn-warning' : 'btn btn-danger';

  const titleId = 'confirm-dialog-title';

  return (
    <div
      className="dialog-backdrop"
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      data-testid="confirm-dialog"
    >
      <div
        ref={dialogRef}
        className="dialog-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        {/* Header */}
        <div className="dialog-header">
          <h2 id={titleId} className="dialog-title">
            {title}
          </h2>
          <button
            type="button"
            className="btn-close"
            aria-label="Close dialog"
            onClick={onCancel}
            disabled={isLoading}
          />
        </div>

        {/* Body */}
        <div className="dialog-body">
          <p className="mb-0">{message}</p>
        </div>

        {/* Footer */}
        <div className="dialog-footer">
          <button
            ref={cancelBtnRef}
            type="button"
            className="btn btn-outline-secondary"
            onClick={onCancel}
            disabled={isLoading}
            data-testid="cancel-btn"
          >
            {cancelLabel}
          </button>
          <button
            ref={confirmBtnRef}
            type="button"
            className={confirmBtnClass}
            onClick={onConfirm}
            disabled={isLoading}
            data-testid="confirm-btn"
          >
            {isLoading && (
              <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" />
            )}
            {isLoading ? 'Deleting…' : confirmLabel}
          </button>
        </div>
      </div>

      <style jsx>{`
        .dialog-backdrop {
          position: fixed;
          inset: 0;
          z-index: 1060;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 1rem;
          background: var(--overlay);
          backdrop-filter: blur(8px);
          -webkit-backdrop-filter: blur(8px);
          animation: fadeIn 150ms ease-out;
        }

        .dialog-card {
          width: 100%;
          max-width: 480px;
          border-radius: var(--radius-lg);
          background: var(--card-bg);
          border: 1px solid var(--border);
          box-shadow: var(--shadow-lg);
          overflow: hidden;
          animation: fadeInUp 200ms ease-out;
        }

        .dialog-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 1rem 1.25rem;
          border-bottom: 1px solid var(--border);
        }

        .dialog-title {
          font-family: var(--font-heading);
          font-size: 1.15rem;
          font-weight: 700;
          color: var(--text-primary);
          margin: 0;
        }

        .dialog-body {
          padding: 1.25rem;
          font-family: var(--font-body);
          color: var(--text-secondary);
          line-height: 1.6;
        }

        .dialog-footer {
          display: flex;
          justify-content: flex-end;
          gap: 0.75rem;
          padding: 1rem 1.25rem;
          border-top: 1px solid var(--border);
          background: var(--surface);
        }
      `}</style>
    </div>
  );
}
