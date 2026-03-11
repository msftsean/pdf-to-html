'use client';

import { useState, useCallback } from 'react';

/**
 * GovBanner — Government Trust Banner
 *
 * Displays an official government website indicator at the top of every page.
 * Follows the U.S. Web Design System (USWDS) pattern adapted for NC.gov.
 *
 * Accessibility:
 * - aria-expanded on toggle button
 * - Keyboard-navigable expand/collapse
 * - Sufficient color contrast (white on navy = 11.8:1 ratio)
 */
export default function GovBanner() {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleToggle = useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, []);

  return (
    <section
      className="gov-banner"
      aria-label="Official government website"
    >
      <div className="container">
        <div className="d-flex align-items-center justify-content-between py-1">
          <p className="gov-banner__text mb-0">
            <span className="gov-banner__icon me-2" aria-hidden="true">
              🏛️
            </span>
            An official website of the State of North Carolina
          </p>
          <button
            type="button"
            className="gov-banner__toggle btn btn-link text-white text-decoration-none p-0 ms-2"
            aria-expanded={isExpanded}
            aria-controls="gov-banner-details"
            onClick={handleToggle}
          >
            <small>
              How you know{' '}
              <span aria-hidden="true">{isExpanded ? '▲' : '▼'}</span>
            </small>
          </button>
        </div>

        {isExpanded && (
          <div
            id="gov-banner-details"
            className="gov-banner__details pb-3"
            role="region"
            aria-label="How to verify this is an official NC government website"
          >
            <div className="row g-3">
              <div className="col-md-6">
                <div className="d-flex align-items-start">
                  <span className="me-2 mt-1" aria-hidden="true">🔒</span>
                  <div>
                    <p className="mb-1">
                      <strong>Official websites use nc.gov</strong>
                    </p>
                    <p className="mb-0" style={{ fontSize: '0.85rem' }}>
                      A <strong>.nc.gov</strong> website belongs to an official
                      government organization in the State of North Carolina.
                    </p>
                  </div>
                </div>
              </div>
              <div className="col-md-6">
                <div className="d-flex align-items-start">
                  <span className="me-2 mt-1" aria-hidden="true">🛡️</span>
                  <div>
                    <p className="mb-1">
                      <strong>Secure websites use HTTPS</strong>
                    </p>
                    <p className="mb-0" style={{ fontSize: '0.85rem' }}>
                      A <strong>lock icon</strong> or <strong>https://</strong>{' '}
                      means you&apos;ve safely connected to a .nc.gov website.
                      Share sensitive information only on official, secure
                      websites.
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
          background-color: var(--nc-navy, #003366);
          color: var(--nc-white, #ffffff);
          font-family: var(--nc-font-body, Georgia, serif);
          font-size: 0.8125rem;
        }
        .gov-banner__text {
          font-size: 0.8125rem;
          line-height: 1.4;
        }
        .gov-banner__toggle:focus-visible {
          outline: 2px solid var(--nc-white, #ffffff);
          outline-offset: 2px;
        }
        .gov-banner__details {
          border-top: 1px solid rgba(255, 255, 255, 0.2);
          margin-top: 0.5rem;
          padding-top: 0.75rem;
        }
      `}</style>
    </section>
  );
}
