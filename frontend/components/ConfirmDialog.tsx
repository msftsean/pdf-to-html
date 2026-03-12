'use client';

import { useEffect, useRef, useCallback } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ConfirmDialogProps {
  /** Whether the dialog is currently open/visible. */
  isOpen: boolean;
  /** Title displayed at the top of the dialog. */
  title: string;
  /** Descriptive message body. */
  message: string;
  /** Label for the confirm button (default: "Delete"). */
  confirmLabel?: string;
  /** Label for the cancel button (default: "Cancel"). */
  cancelLabel?: string;
  /** Visual variant controlling the confirm button color (default: "danger"). */
  variant?: 'danger' | 'warning';
  /** Called when the user confirms the action. */
  onConfirm: () => void;
  /** Called when the user cancels (button click, Escape, or backdrop click). */
  onCancel: () => void;
  /** When true, the confirm button shows a spinner and is disabled. */
  isLoading?: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * ConfirmDialog — WCAG 2.1 AA accessible confirmation modal.
 *
 * Uses Bootstrap 5 modal markup with:
 * - Focus trap (Tab cycles within the dialog)
 * - Escape key closes the dialog
 * - Backdrop overlay click closes the dialog
 * - role="dialog", aria-modal="true", aria-labelledby
 * - Confirm button shows spinner when isLoading
 * - NCDIT Digital Commons CSS variables
 * - data-testid attributes for testing
 *
 * Focus management:
 * - On open: focuses the cancel button (safe default)
 * - On close: the parent component should return focus to the trigger element
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

  // -----------------------------------------------------------------------
  // Focus management: focus cancel button on open
  // -----------------------------------------------------------------------
  useEffect(() => {
    if (isOpen) {
      // Small delay to ensure the DOM has rendered
      const timer = setTimeout(() => {
        cancelBtnRef.current?.focus();
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  // -----------------------------------------------------------------------
  // Body scroll lock when dialog is open
  // -----------------------------------------------------------------------
  useEffect(() => {
    if (isOpen) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [isOpen]);

  // -----------------------------------------------------------------------
  // Keyboard handlers: Escape to close, Tab trap
  // -----------------------------------------------------------------------
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
          // Shift+Tab: if focus is on first element, wrap to last
          if (document.activeElement === firstEl) {
            e.preventDefault();
            lastEl.focus();
          }
        } else {
          // Tab: if focus is on last element, wrap to first
          if (document.activeElement === lastEl) {
            e.preventDefault();
            firstEl.focus();
          }
        }
      }
    },
    [isLoading, onCancel]
  );

  // -----------------------------------------------------------------------
  // Backdrop click handler
  // -----------------------------------------------------------------------
  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      // Only close if clicking the backdrop itself, not the dialog content
      if (e.target === e.currentTarget && !isLoading) {
        onCancel();
      }
    },
    [isLoading, onCancel]
  );

  // -----------------------------------------------------------------------
  // Don't render anything when closed
  // -----------------------------------------------------------------------
  if (!isOpen) return null;

  const btnVariantClass =
    variant === 'warning' ? 'btn-warning' : 'btn-danger';

  const titleId = 'confirm-dialog-title';

  return (
    <div
      className="confirm-dialog-backdrop"
      onClick={handleBackdropClick}
      onKeyDown={handleKeyDown}
      data-testid="confirm-dialog"
    >
      <div
        ref={dialogRef}
        className="confirm-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        {/* Header */}
        <div className="confirm-dialog__header">
          <h2
            id={titleId}
            className="confirm-dialog__title h5 mb-0"
          >
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
        <div className="confirm-dialog__body">
          <p className="mb-0">{message}</p>
        </div>

        {/* Footer */}
        <div className="confirm-dialog__footer">
          <button
            ref={cancelBtnRef}
            type="button"
            className="btn btn-outline-secondary confirm-dialog__cancel-btn"
            onClick={onCancel}
            disabled={isLoading}
            data-testid="cancel-btn"
          >
            {cancelLabel}
          </button>
          <button
            ref={confirmBtnRef}
            type="button"
            className={`btn ${btnVariantClass} confirm-dialog__confirm-btn`}
            onClick={onConfirm}
            disabled={isLoading}
            data-testid="confirm-btn"
          >
            {isLoading && (
              <span
                className="spinner-border spinner-border-sm me-2"
                role="status"
                aria-hidden="true"
              />
            )}
            {isLoading ? 'Deleting…' : confirmLabel}
          </button>
        </div>
      </div>

      <style jsx>{`
        .confirm-dialog-backdrop {
          position: fixed;
          inset: 0;
          z-index: 1060;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 1rem;
          background-color: rgba(0, 0, 0, 0.5);
          animation: confirmFadeIn 150ms ease-out;
        }

        @keyframes confirmFadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        .confirm-dialog {
          width: 100%;
          max-width: 480px;
          border-radius: var(--nc-radius-md, 0.375rem);
          background-color: var(--nc-white, #ffffff);
          box-shadow: var(
            --nc-shadow-lg,
            0 10px 30px rgba(0, 0, 0, 0.2)
          );
          animation: confirmSlideUp 150ms ease-out;
          overflow: hidden;
        }

        @keyframes confirmSlideUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .confirm-dialog__header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 1rem 1.25rem;
          border-bottom: 1px solid var(--nc-border, #dee2e6);
        }

        .confirm-dialog__title {
          font-family: var(
            --nc-font-heading,
            'Century Gothic',
            sans-serif
          );
          color: var(--nc-navy, #003366);
        }

        .confirm-dialog__body {
          padding: 1.25rem;
          font-family: var(--nc-font-body, Georgia, serif);
          color: var(--nc-dark-gray, #333333);
          line-height: 1.6;
        }

        .confirm-dialog__footer {
          display: flex;
          justify-content: flex-end;
          gap: 0.75rem;
          padding: 1rem 1.25rem;
          border-top: 1px solid var(--nc-border, #dee2e6);
          background-color: var(--nc-bg-light, #f8f9fa);
        }

        .confirm-dialog__cancel-btn,
        .confirm-dialog__confirm-btn {
          font-family: var(
            --nc-font-heading,
            'Century Gothic',
            sans-serif
          );
          font-weight: 600;
          font-size: 0.875rem;
          padding: 0.5rem 1.25rem;
        }

        .confirm-dialog__cancel-btn:focus-visible,
        .confirm-dialog__confirm-btn:focus-visible {
          outline: 2px solid var(--nc-action-blue, #1e79c8);
          outline-offset: 2px;
        }
      `}</style>
    </div>
  );
}
