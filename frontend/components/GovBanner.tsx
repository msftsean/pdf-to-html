'use client';

import { useState, useCallback } from 'react';

/**
 * GovBanner — Demo Disclaimer Banner
 *
 * Prominent disclaimer: NOT an official government website.
 * Amber accent in dark mode, stays visible in light mode.
 *
 * Accessibility:
 * - aria-expanded on toggle button
 * - Keyboard-navigable expand/collapse
 * - Sufficient contrast: dark text on amber (9.7:1)
 */
export default function GovBanner() {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleToggle = useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, []);

  return (
    <section className="gov-banner" aria-label="Demo website disclaimer">
      <div className="container">
        <div className="banner-row">
          <p className="gov-banner__text mb-0">
            <span className="banner-icon" aria-hidden="true">⚠️</span>
            An <strong>UN</strong>official website of the State of North Carolina. For demo purposes only.
          </p>
          <button
            type="button"
            className="gov-banner__toggle"
            aria-expanded={isExpanded}
            aria-controls="gov-banner-details"
            onClick={handleToggle}
          >
            <small>
              Learn more{' '}
              <span aria-hidden="true">{isExpanded ? '▲' : '▼'}</span>
            </small>
          </button>
        </div>

        {isExpanded && (
          <div
            id="gov-banner-details"
            className="gov-banner__details"
            role="region"
            aria-label="About this demo application"
          >
            <div className="banner-details-grid">
              <div className="banner-detail-item">
                <span className="banner-detail-icon" aria-hidden="true">📄</span>
                <div>
                  <p className="mb-1"><strong>What is this?</strong></p>
                  <p className="mb-0 banner-detail-text">
                    This is a demo of the PDF to HTML converter for{' '}
                    <strong>WCAG 2.1 AA</strong> accessibility compliance.
                    It converts PDF, DOCX, and PPTX documents into accessible HTML.
                  </p>
                </div>
              </div>
              <div className="banner-detail-item">
                <span className="banner-detail-icon" aria-hidden="true">🔬</span>
                <div>
                  <p className="mb-1"><strong>Not an official NC.gov site</strong></p>
                  <p className="mb-0 banner-detail-text">
                    This application is a <strong>technology demonstration</strong>{' '}
                    by NCDIT. It is not an official State of North Carolina
                    service. Do not upload sensitive or confidential documents.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .banner-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.35rem 0;
          gap: 0.75rem;
        }

        .banner-icon {
          margin-right: 0.5rem;
        }

        .gov-banner__toggle {
          background: none;
          border: none;
          cursor: pointer;
          padding: 0.25rem 0.5rem;
          border-radius: var(--radius-sm);
          font-family: var(--font-body);
          white-space: nowrap;
          color: #1a1a1a !important;
        }

        .gov-banner__toggle:focus-visible {
          outline: 2px solid #1a1a1a;
          outline-offset: 2px;
        }

        .banner-details-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
        }

        @media (max-width: 767.98px) {
          .banner-details-grid {
            grid-template-columns: 1fr;
          }
        }

        .banner-detail-item {
          display: flex;
          align-items: flex-start;
          gap: 0.5rem;
        }

        .banner-detail-icon {
          margin-top: 0.2rem;
          flex-shrink: 0;
        }

        .banner-detail-text {
          font-size: 0.85rem;
        }
      `}</style>
    </section>
  );
}
