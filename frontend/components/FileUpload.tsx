'use client';

import { useState, useRef, useCallback } from 'react';
import { uploadDocument, type UploadProgress } from '@/services/uploadService';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

const ACCEPTED_TYPES: Record<string, string> = {
  'application/pdf': 'PDF',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
    'Word (.docx)',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation':
    'PowerPoint (.pptx)',
};

const ACCEPT_ATTR = '.pdf,.docx,.pptx';
const MAX_FILE_SIZE = 100 * 1024 * 1024;

type FileStatus = 'pending' | 'uploading' | 'complete' | 'error';

interface TrackedFile {
  id: string;
  file: File;
  status: FileStatus;
  progress: number;
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
    case 'pdf': return '📄';
    case 'docx': return '📝';
    case 'pptx': return '📊';
    default: return '📁';
  }
}

let fileIdCounter = 0;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * FileUpload — Drag-and-drop file upload with runbook aesthetics.
 *
 * Accessibility:
 * - Drop zone is keyboard-focusable (tabindex="0")
 * - Enter / Space triggers the hidden file input
 * - Screen reader announcements via aria-live region
 * - Error messages use role="alert"
 * - Progress bars have ARIA attributes
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
              ? { ...f, status: 'complete' as FileStatus, progress: 100, documentId }
              : f
          )
        );
        setAnnouncement(`${tracked.file.name} uploaded successfully.`);
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : 'An unexpected error occurred. Please try again.';

        let friendlyMessage = message;
        if (
          message.includes('network error') ||
          message.includes('Failed to fetch') ||
          message.includes('ERR_CONNECTION_REFUSED')
        ) {
          friendlyMessage = 'Cannot reach the conversion service. Please try again shortly.';
        } else if (message.includes('Failed to request upload token')) {
          friendlyMessage = 'Could not authorize upload — the service may be unavailable. Please try again.';
        } else if (message.includes('status 403')) {
          friendlyMessage = 'Upload authorization expired. Please try uploading again.';
        } else if (message.includes('timed out')) {
          friendlyMessage = 'Upload timed out. Please try again with a better connection.';
        }

        setFiles((prev) =>
          prev.map((f) =>
            f.id === tracked.id
              ? { ...f, status: 'error' as FileStatus, errorMessage: friendlyMessage }
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
      setAnnouncement(
        `${valid.length} file${valid.length > 1 ? 's' : ''} added. Starting upload.`
      );

      tracked.forEach((t) => uploadSingleFile(t));
    },
    [validateFiles, uploadSingleFile]
  );

  // -----------------------------------------------------------------------
  // Drag & Drop
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
  // Click / Keyboard
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
        e.target.value = '';
      }
    },
    [handleFiles]
  );

  // -----------------------------------------------------------------------
  // Retry / Remove
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

  const removeFile = useCallback((id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  return (
    <div className="file-upload">
      {/* Screen reader announcement */}
      <div className="visually-hidden" aria-live="polite" aria-atomic="true">
        {announcement}
      </div>

      {/* Drop zone */}
      <div
        className={`upload-zone ${isDragOver ? 'upload-zone--active' : ''}`}
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
        <div className="upload-zone__content">
          <span className="upload-zone__icon" aria-hidden="true">☁️</span>
          <p className="upload-zone__title">Drag &amp; drop files here</p>
          <p className="upload-zone__subtitle">
            or <span className="upload-zone__link">browse your computer</span>
          </p>
          <p className="upload-zone__hint">
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
        <div className="upload-errors" role="alert" aria-live="polite">
          {validationErrors.map((error, i) => (
            <p key={i} className="upload-error-msg">{error}</p>
          ))}
        </div>
      )}

      {/* File list */}
      {files.length > 0 && (
        <ul className="upload-list" aria-label="Uploaded files">
          {files.map((tracked) => (
            <li key={tracked.id} className="upload-item">
              <div className="upload-item__header">
                <span className="upload-item__icon" aria-hidden="true">
                  {fileIcon(tracked.file.name)}
                </span>
                <span className="upload-item__info">
                  <span className="upload-item__name">{tracked.file.name}</span>
                  <span className="upload-item__size">{formatFileSize(tracked.file.size)}</span>
                </span>
                <span className="upload-item__badge">
                  {tracked.status === 'uploading' && (
                    <span className="upload-status upload-status--uploading">
                      Uploading {tracked.progress}%
                    </span>
                  )}
                  {tracked.status === 'complete' && (
                    <span className="upload-status upload-status--complete">✅ Complete</span>
                  )}
                  {tracked.status === 'error' && (
                    <span className="upload-status upload-status--error">⚠️ Error</span>
                  )}
                  {tracked.status === 'pending' && (
                    <span className="upload-status upload-status--pending">Queued</span>
                  )}
                </span>
                <button
                  type="button"
                  className="btn-close btn-close-sm"
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
                  className="progress upload-progress"
                  role="progressbar"
                  aria-valuenow={tracked.progress}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${tracked.file.name} upload progress`}
                >
                  <div
                    className="progress-bar"
                    style={{ width: `${tracked.progress}%` }}
                  />
                </div>
              )}

              {/* Completed — document ID */}
              {tracked.status === 'complete' && tracked.documentId && (
                <p className="upload-doc-id">
                  <small>
                    Document ID: <code>{tracked.documentId}</code>
                  </small>
                </p>
              )}

              {/* Error + retry */}
              {tracked.status === 'error' && (
                <div className="upload-error-detail">
                  <p className="mb-1" role="alert">{tracked.errorMessage}</p>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-primary"
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
        .upload-zone {
          border: 2px dashed var(--border-hover);
          border-radius: var(--radius-lg);
          padding: 3rem 1.5rem;
          text-align: center;
          cursor: pointer;
          transition: all var(--transition-normal);
          background: var(--card-bg);
        }

        .upload-zone:hover,
        .upload-zone:focus-visible {
          border-color: var(--accent-sky);
          background: rgba(56, 189, 248, 0.04);
          box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.1);
        }

        .upload-zone--active {
          border-color: var(--accent-sky);
          background: rgba(56, 189, 248, 0.08);
          border-style: solid;
          box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.15);
        }

        .upload-zone__icon {
          font-size: 3rem;
          display: block;
          margin-bottom: 0.75rem;
        }

        .upload-zone__title {
          font-family: var(--font-heading);
          font-weight: 700;
          font-size: 1.25rem;
          color: var(--text-primary);
          margin-bottom: 0.25rem;
        }

        .upload-zone__subtitle {
          font-family: var(--font-body);
          color: var(--text-secondary);
          margin-bottom: 0.5rem;
        }

        .upload-zone__link {
          color: var(--accent-sky);
          text-decoration: underline;
          font-weight: 600;
        }

        .upload-zone__hint {
          font-family: var(--font-body);
          font-size: 0.85rem;
          color: var(--text-muted);
          margin-bottom: 0;
        }

        /* Validation errors */
        .upload-errors {
          margin-top: 1rem;
        }

        .upload-error-msg {
          font-family: var(--font-body);
          color: var(--accent-red);
          font-size: 0.9rem;
          padding: 0.5rem 0.75rem;
          background: rgba(239, 68, 68, 0.08);
          border-left: 3px solid var(--accent-red);
          border-radius: var(--radius-sm);
          margin-bottom: 0.5rem;
        }

        /* File list */
        .upload-list {
          list-style: none;
          padding: 0;
          margin: 1rem 0 0;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .upload-item {
          padding: 0.75rem 1rem;
          border: 1px solid var(--border);
          border-radius: var(--radius-md);
          background: var(--card-bg);
          transition: border-color var(--transition-fast);
        }

        .upload-item:hover {
          border-color: var(--border-hover);
        }

        .upload-item__header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .upload-item__icon {
          font-size: 1.5rem;
          flex-shrink: 0;
        }

        .upload-item__info {
          flex: 1;
          min-width: 0;
        }

        .upload-item__name {
          display: block;
          font-family: var(--font-heading);
          font-weight: 600;
          font-size: 0.95rem;
          color: var(--text-primary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .upload-item__size {
          display: block;
          font-family: var(--font-body);
          font-size: 0.8rem;
          color: var(--text-muted);
        }

        .upload-status {
          font-family: var(--font-heading);
          font-size: 0.8rem;
          font-weight: 600;
          white-space: nowrap;
        }

        .upload-status--uploading { color: var(--accent-sky); }
        .upload-status--complete { color: var(--accent-emerald); }
        .upload-status--error { color: var(--accent-red); }
        .upload-status--pending { color: var(--text-muted); }

        .upload-progress {
          margin-top: 0.5rem;
          height: 6px;
        }

        .upload-doc-id {
          margin: 0.25rem 0 0;
          font-size: 0.8rem;
          color: var(--text-muted);
        }

        .upload-error-detail {
          margin-top: 0.5rem;
          font-family: var(--font-body);
          font-size: 0.85rem;
          color: var(--accent-red);
        }

        @media (max-width: 575.98px) {
          .upload-zone {
            padding: 2rem 1rem;
          }

          .upload-zone__icon {
            font-size: 2rem;
          }

          .upload-zone__title {
            font-size: 1.1rem;
          }

          .upload-item__header {
            flex-wrap: wrap;
            gap: 0.5rem;
          }

          .upload-item__badge {
            order: 4;
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}
