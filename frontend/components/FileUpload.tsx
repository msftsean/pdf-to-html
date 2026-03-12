'use client';

import { useState, useRef, useCallback } from 'react';
import { uploadDocument, type UploadProgress } from '@/services/uploadService';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Allowed MIME types and their user-friendly labels */
const ACCEPTED_TYPES: Record<string, string> = {
  'application/pdf': 'PDF',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
    'Word (.docx)',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation':
    'PowerPoint (.pptx)',
};

/** Accept attribute for the file input */
const ACCEPT_ATTR = '.pdf,.docx,.pptx';

/** Maximum file size in bytes (100 MB) */
const MAX_FILE_SIZE = 100 * 1024 * 1024;

type FileStatus = 'pending' | 'uploading' | 'complete' | 'error';

interface TrackedFile {
  id: string;
  file: File;
  status: FileStatus;
  progress: number; // 0–100
  documentId?: string;
  errorMessage?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function fileIcon(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'pdf':
      return '📄';
    case 'docx':
      return '📝';
    case 'pptx':
      return '📊';
    default:
      return '📁';
  }
}

let fileIdCounter = 0;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * FileUpload — Drag-and-drop file upload with NCDIT Digital Commons styling.
 *
 * Accessibility:
 * - Drop zone is keyboard-focusable (tabindex="0")
 * - Enter / Space triggers the hidden file input
 * - Screen reader announcements via aria-live region
 * - Error messages use role="alert"
 * - Progress bars have aria-valuenow/aria-valuemin/aria-valuemax
 */
export default function FileUpload() {
  const [files, setFiles] = useState<TrackedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [announcement, setAnnouncement] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const dragCounter = useRef(0);

  // -----------------------------------------------------------------------
  // Validation
  // -----------------------------------------------------------------------

  const validateFiles = useCallback(
    (incoming: File[]): { valid: File[]; errors: string[] } => {
      const valid: File[] = [];
      const errors: string[] = [];

      for (const file of incoming) {
        if (!ACCEPTED_TYPES[file.type]) {
          errors.push(
            `❌ ${file.name} is not supported. Accepted formats: PDF, Word (.docx), PowerPoint (.pptx)`
          );
        } else if (file.size > MAX_FILE_SIZE) {
          const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
          errors.push(
            `❌ ${file.name} is too large (${sizeMB}MB). Maximum file size is 100MB.`
          );
        } else {
          valid.push(file);
        }
      }

      return { valid, errors };
    },
    []
  );

  // -----------------------------------------------------------------------
  // Upload a single file
  // -----------------------------------------------------------------------

  const uploadSingleFile = useCallback(
    async (tracked: TrackedFile) => {
      // Mark as uploading
      setFiles((prev) =>
        prev.map((f) =>
          f.id === tracked.id ? { ...f, status: 'uploading' as FileStatus } : f
        )
      );
      setAnnouncement(`Uploading ${tracked.file.name}…`);

      try {
        const documentId = await uploadDocument(
          tracked.file,
          (progress: UploadProgress) => {
            setFiles((prev) =>
              prev.map((f) =>
                f.id === tracked.id
                  ? { ...f, progress: progress.percentage }
                  : f
              )
            );
          }
        );

        setFiles((prev) =>
          prev.map((f) =>
            f.id === tracked.id
              ? {
                  ...f,
                  status: 'complete' as FileStatus,
                  progress: 100,
                  documentId,
                }
              : f
          )
        );
        setAnnouncement(`${tracked.file.name} uploaded successfully.`);
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : 'An unexpected error occurred. Please try again.';

        // Friendly error mapping
        let friendlyMessage = message;
        if (
          message.includes('network error') ||
          message.includes('Failed to fetch') ||
          message.includes('ERR_CONNECTION_REFUSED')
        ) {
          friendlyMessage =
            'Cannot reach the conversion service. Please try again shortly.';
        } else if (message.includes('Failed to request upload token')) {
          friendlyMessage =
            'Could not authorize upload — the service may be unavailable. Please try again.';
        } else if (message.includes('status 403')) {
          friendlyMessage =
            'Upload authorization expired. Please try uploading again.';
        } else if (message.includes('timed out')) {
          friendlyMessage =
            'Upload timed out. Please try again with a better connection.';
        }

        setFiles((prev) =>
          prev.map((f) =>
            f.id === tracked.id
              ? {
                  ...f,
                  status: 'error' as FileStatus,
                  errorMessage: friendlyMessage,
                }
              : f
          )
        );
        setAnnouncement(`Error uploading ${tracked.file.name}: ${friendlyMessage}`);
      }
    },
    []
  );

  // -----------------------------------------------------------------------
  // Process incoming files
  // -----------------------------------------------------------------------

  const handleFiles = useCallback(
    (incoming: FileList | File[]) => {
      const fileArray = Array.from(incoming);
      const { valid, errors } = validateFiles(fileArray);

      // Clear old validation errors when new valid files arrive
      if (valid.length > 0) {
        setValidationErrors(errors);
      } else {
        setValidationErrors((prev) => [...prev, ...errors]);
      }

      if (valid.length === 0) return;

      const tracked: TrackedFile[] = valid.map((file) => ({
        id: `file-${++fileIdCounter}`,
        file,
        status: 'pending',
        progress: 0,
      }));

      setFiles((prev) => [...prev, ...tracked]);

      // Announce to screen readers
      setAnnouncement(
        `${valid.length} file${valid.length > 1 ? 's' : ''} added. Starting upload.`
      );

      // Start uploads
      tracked.forEach((t) => uploadSingleFile(t));
    },
    [validateFiles, uploadSingleFile]
  );

  // -----------------------------------------------------------------------
  // Drag & Drop handlers
  // -----------------------------------------------------------------------

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current++;
    if (dragCounter.current === 1) {
      setIsDragOver(true);
      setAnnouncement('File detected. Drop to upload.');
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setIsDragOver(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter.current = 0;
      setIsDragOver(false);

      if (e.dataTransfer.files.length > 0) {
        handleFiles(e.dataTransfer.files);
      }
    },
    [handleFiles]
  );

  // -----------------------------------------------------------------------
  // Click / Keyboard handlers
  // -----------------------------------------------------------------------

  const openFilePicker = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openFilePicker();
      }
    },
    [openFilePicker]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFiles(e.target.files);
        // Reset input so same file can be re-uploaded
        e.target.value = '';
      }
    },
    [handleFiles]
  );

  // -----------------------------------------------------------------------
  // Retry handler
  // -----------------------------------------------------------------------

  const retryUpload = useCallback(
    (id: string) => {
      const tracked = files.find((f) => f.id === id);
      if (tracked) {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === id
              ? { ...f, status: 'pending' as FileStatus, progress: 0, errorMessage: undefined }
              : f
          )
        );
        uploadSingleFile({ ...tracked, status: 'pending', progress: 0 });
      }
    },
    [files, uploadSingleFile]
  );

  // -----------------------------------------------------------------------
  // Remove file from list
  // -----------------------------------------------------------------------

  const removeFile = useCallback((id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  return (
    <div className="file-upload">
      {/* Screen reader announcement region */}
      <div className="visually-hidden" aria-live="polite" aria-atomic="true">
        {announcement}
      </div>

      {/* Drop zone */}
      <div
        className={`file-upload__zone ${isDragOver ? 'file-upload__zone--active' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={openFilePicker}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        aria-label="Upload files. Drag and drop or press Enter to browse. Accepted formats: PDF, DOCX, PPTX. Maximum 100 MB per file."
      >
        <div className="file-upload__zone-content">
          <span className="file-upload__icon" aria-hidden="true">
            ☁️
          </span>
          <p className="file-upload__title">
            Drag &amp; drop files here
          </p>
          <p className="file-upload__subtitle">
            or <span className="file-upload__browse-link">browse your computer</span>
          </p>
          <p className="file-upload__hint">
            PDF, Word (.docx), PowerPoint (.pptx) — up to 100 MB
          </p>
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        className="visually-hidden"
        accept={ACCEPT_ATTR}
        multiple
        onChange={handleInputChange}
        aria-hidden="true"
        tabIndex={-1}
      />

      {/* Validation errors */}
      {validationErrors.length > 0 && (
        <div className="file-upload__errors mt-3" role="alert" aria-live="polite">
          {validationErrors.map((error, i) => (
            <p key={i} className="file-upload__error mb-1">
              {error}
            </p>
          ))}
        </div>
      )}

      {/* File list with progress */}
      {files.length > 0 && (
        <ul className="file-upload__list mt-3" aria-label="Uploaded files">
          {files.map((tracked) => (
            <li key={tracked.id} className="file-upload__item">
              <div className="file-upload__item-header">
                <span className="file-upload__file-icon" aria-hidden="true">
                  {fileIcon(tracked.file.name)}
                </span>
                <span className="file-upload__file-info">
                  <span className="file-upload__file-name">
                    {tracked.file.name}
                  </span>
                  <span className="file-upload__file-size">
                    {formatFileSize(tracked.file.size)}
                  </span>
                </span>
                <span className="file-upload__status-badge">
                  {tracked.status === 'uploading' && (
                    <span className="file-upload__status file-upload__status--uploading">
                      Uploading {tracked.progress}%
                    </span>
                  )}
                  {tracked.status === 'complete' && (
                    <span className="file-upload__status file-upload__status--complete">
                      ✅ Complete
                    </span>
                  )}
                  {tracked.status === 'error' && (
                    <span className="file-upload__status file-upload__status--error">
                      ⚠️ Error
                    </span>
                  )}
                  {tracked.status === 'pending' && (
                    <span className="file-upload__status file-upload__status--pending">
                      Queued
                    </span>
                  )}
                </span>
                <button
                  type="button"
                  className="file-upload__remove btn-close btn-close-sm"
                  aria-label={`Remove ${tracked.file.name}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(tracked.id);
                  }}
                />
              </div>

              {/* Progress bar */}
              {(tracked.status === 'uploading' || tracked.status === 'pending') && (
                <div
                  className="progress file-upload__progress mt-2"
                  role="progressbar"
                  aria-valuenow={tracked.progress}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${tracked.file.name} upload progress`}
                >
                  <div
                    className="progress-bar file-upload__progress-bar"
                    style={{ width: `${tracked.progress}%` }}
                  />
                </div>
              )}

              {/* Completed indicator with document ID */}
              {tracked.status === 'complete' && tracked.documentId && (
                <p className="file-upload__doc-id mt-1 mb-0">
                  <small>
                    Document ID: <code>{tracked.documentId}</code>
                  </small>
                </p>
              )}

              {/* Error message + retry */}
              {tracked.status === 'error' && (
                <div className="file-upload__error-detail mt-1">
                  <p className="mb-1" role="alert">
                    {tracked.errorMessage}
                  </p>
                  <button
                    type="button"
                    className="btn btn-sm file-upload__retry-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      retryUpload(tracked.id);
                    }}
                  >
                    Retry
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      <style jsx>{`
        .file-upload__zone {
          border: 2px dashed var(--nc-navy, #003366);
          border-radius: var(--nc-radius-lg, 0.5rem);
          padding: 2.5rem 1.5rem;
          text-align: center;
          cursor: pointer;
          transition:
            border-color var(--nc-transition-normal, 250ms ease-in-out),
            background-color var(--nc-transition-normal, 250ms ease-in-out),
            box-shadow var(--nc-transition-normal, 250ms ease-in-out);
          background-color: var(--nc-white, #ffffff);
        }

        .file-upload__zone:hover,
        .file-upload__zone:focus-visible {
          border-color: var(--nc-action-blue, #1e79c8);
          background-color: rgba(30, 121, 200, 0.04);
          box-shadow: 0 0 0 3px rgba(30, 121, 200, 0.15);
        }

        .file-upload__zone--active {
          border-color: var(--nc-action-blue, #1e79c8);
          background-color: rgba(30, 121, 200, 0.08);
          border-style: solid;
          box-shadow: 0 0 0 4px rgba(30, 121, 200, 0.25);
        }

        .file-upload__icon {
          font-size: 3rem;
          display: block;
          margin-bottom: 0.75rem;
        }

        .file-upload__title {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          font-weight: bold;
          font-size: 1.25rem;
          color: var(--nc-navy, #003366);
          margin-bottom: 0.25rem;
        }

        .file-upload__subtitle {
          font-family: var(--nc-font-body, Georgia, serif);
          color: var(--nc-medium-gray, #6c757d);
          margin-bottom: 0.5rem;
        }

        .file-upload__browse-link {
          color: var(--nc-action-blue, #1e79c8);
          text-decoration: underline;
          font-weight: 600;
        }

        .file-upload__hint {
          font-family: var(--nc-font-body, Georgia, serif);
          font-size: 0.85rem;
          color: var(--nc-medium-gray, #6c757d);
          margin-bottom: 0;
        }

        /* Validation errors */
        .file-upload__error {
          font-family: var(--nc-font-body, Georgia, serif);
          color: var(--nc-danger, #dc3545);
          font-size: 0.9rem;
          padding: 0.5rem 0.75rem;
          background-color: #fdf0f0;
          border-left: 3px solid var(--nc-danger, #dc3545);
          border-radius: var(--nc-radius-sm, 0.25rem);
        }

        /* File list */
        .file-upload__list {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .file-upload__item {
          padding: 0.75rem 1rem;
          border: 1px solid var(--nc-border-gray, #dee2e6);
          border-radius: var(--nc-radius-md, 0.375rem);
          margin-bottom: 0.5rem;
          background-color: var(--nc-white, #ffffff);
        }

        .file-upload__item-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .file-upload__file-icon {
          font-size: 1.5rem;
          flex-shrink: 0;
        }

        .file-upload__file-info {
          flex: 1;
          min-width: 0;
        }

        .file-upload__file-name {
          display: block;
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          font-weight: 600;
          font-size: 0.95rem;
          color: var(--nc-navy, #003366);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .file-upload__file-size {
          display: block;
          font-family: var(--nc-font-body, Georgia, serif);
          font-size: 0.8rem;
          color: var(--nc-medium-gray, #6c757d);
        }

        .file-upload__status {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          font-size: 0.8rem;
          font-weight: 600;
          white-space: nowrap;
        }

        .file-upload__status--uploading {
          color: var(--nc-action-blue, #1e79c8);
        }

        .file-upload__status--complete {
          color: var(--nc-success, #28a745);
        }

        .file-upload__status--error {
          color: var(--nc-danger, #dc3545);
        }

        .file-upload__status--pending {
          color: var(--nc-medium-gray, #6c757d);
        }

        .file-upload__remove {
          flex-shrink: 0;
        }

        /* Progress bar */
        .file-upload__progress {
          height: 6px;
          border-radius: 3px;
          background-color: var(--nc-light-gray, #f5f5f5);
          overflow: hidden;
        }

        .file-upload__progress-bar {
          background-color: var(--nc-action-blue, #1e79c8);
          transition: width 200ms ease;
          border-radius: 3px;
        }

        /* Document ID */
        .file-upload__doc-id {
          font-family: var(--nc-font-body, Georgia, serif);
          font-size: 0.8rem;
          color: var(--nc-medium-gray, #6c757d);
        }

        .file-upload__doc-id code {
          font-family: var(--nc-font-mono, 'Courier New', monospace);
          background-color: var(--nc-light-gray, #f5f5f5);
          padding: 0.125rem 0.375rem;
          border-radius: var(--nc-radius-sm, 0.25rem);
          font-size: 0.8rem;
        }

        /* Error detail */
        .file-upload__error-detail {
          font-family: var(--nc-font-body, Georgia, serif);
          font-size: 0.85rem;
          color: var(--nc-danger, #dc3545);
        }

        .file-upload__retry-btn {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--nc-action-blue, #1e79c8);
          border: 1px solid var(--nc-action-blue, #1e79c8);
          background: transparent;
          border-radius: var(--nc-radius-sm, 0.25rem);
          padding: 0.2rem 0.75rem;
        }

        .file-upload__retry-btn:hover {
          background-color: var(--nc-action-blue, #1e79c8);
          color: var(--nc-white, #ffffff);
        }

        /* Responsive */
        @media (max-width: 575.98px) {
          .file-upload__zone {
            padding: 1.5rem 1rem;
          }

          .file-upload__icon {
            font-size: 2rem;
          }

          .file-upload__title {
            font-size: 1.1rem;
          }

          .file-upload__item-header {
            flex-wrap: wrap;
            gap: 0.5rem;
          }

          .file-upload__status-badge {
            order: 4;
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}
