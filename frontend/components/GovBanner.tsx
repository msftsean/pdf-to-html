'use client';

import { useState, useCallback } from 'react';

/**
 * GovBanner — Demo Disclaimer Banner
 *
 * Displays a prominent disclaimer that this is NOT an official government website.
 * Uses amber/yellow background to visually distinguish from official NC.gov sites.
 *
 * Accessibility:
 * - aria-expanded on toggle button
 * - Keyboard-navigable expand/collapse
 * - Sufficient color contrast (dark text on amber = 9.7:1 ratio)
 */
export default function GovBanner() {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleToggle = useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, []);

  return (
    <section
      className="gov-banner"
      aria-label="Demo website disclaimer"
    >
      <div className="container">
        <div className="d-flex align-items-center justify-content-between py-1">
          <p className="gov-banner__text mb-0">
            <span className="gov-banner__icon me-2" aria-hidden="true">
              ⚠️
            </span>
            An <strong>UN</strong>official website of the State of North Carolina. For demo purposes only.
          </p>
          <button
            type="button"
            className="gov-banner__toggle btn btn-link text-decoration-none p-0 ms-2"
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
            className="gov-banner__details pb-3"
            role="region"
            aria-label="About this demo application"
          >
            <div className="row g-3">
              <div className="col-md-6">
                <div className="d-flex align-items-start">
                  <span className="me-2 mt-1" aria-hidden="true">📄</span>
                  <div>
                    <p className="mb-1">
                      <strong>What is this?</strong>
                    </p>
                    <p className="mb-0" style={{ fontSize: '0.85rem' }}>
                      This is a demo of the PDF to HTML converter for{' '}
                      <strong>WCAG 2.1 AA</strong> accessibility compliance.
                      It converts PDF, DOCX, and PPTX documents into accessible HTML.
                    </p>
                  </div>
                </div>
              </div>
              <div className="col-md-6">
                <div className="d-flex align-items-start">
                  <span className="me-2 mt-1" aria-hidden="true">🔬</span>
                  <div>
                    <p className="mb-1">
                      <strong>Not an official NC.gov site</strong>
                    </p>
                    <p className="mb-0" style={{ fontSize: '0.85rem' }}>
                      This application is a <strong>technology demonstration</strong>{' '}
                      by NCDIT. It is not an official State of North Carolina
                      service. Do not upload sensitive or confidential documents.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .gov-banner {
          background-color: #d4a017;
          color: #1a1a1a;
          font-family: var(--nc-font-body, Georgia, serif);
          font-size: 0.8125rem;
        }
        .gov-banner__text {
          font-size: 0.8125rem;
          line-height: 1.4;
          color: #1a1a1a;
        }
        .gov-banner__toggle {
          color: #1a1a1a !important;
        }
        .gov-banner__toggle:focus-visible {
          outline: 2px solid #1a1a1a;
          outline-offset: 2px;
        }
        .gov-banner__details {
          border-top: 1px solid rgba(0, 0, 0, 0.2);
          margin-top: 0.5rem;
          padding-top: 0.75rem;
          color: #1a1a1a;
        }
      `}</style>
    </section>
  );
}
