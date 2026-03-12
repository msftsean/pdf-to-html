'use client';

/**
 * NCHeader — NC.gov-style Page Header
 *
 * Displays the NC.gov branding, department label (NCDIT),
 * and service name (Document Converter).
 *
 * Accessibility:
 * - role="banner" on outer element
 * - Semantic <header> element
 * - Responsive: stacks on mobile
 * - Sufficient color contrast for all text
 */
export default function NCHeader() {
  return (
    <header role="banner" className="nc-header">
      <div className="container">
        <div className="d-flex align-items-center justify-content-between py-3 flex-wrap">
          {/* Logo + Branding Area */}
          <div className="d-flex align-items-center">
            {/* Placeholder: NC.gov logo will be replaced with SVG/image */}
            <a
              href="https://www.nc.gov"
              className="nc-header__logo text-decoration-none d-flex align-items-center"
              aria-label="NC.gov - State of North Carolina"
            >
              <span className="nc-header__logo-mark me-2" aria-hidden="true">
                NC
              </span>
              <span className="nc-header__logo-text">.gov</span>
            </a>

            <span
              className="nc-header__divider mx-3"
              aria-hidden="true"
            />

            <div className="nc-header__service">
              <span className="nc-header__dept">NCDIT</span>
              <span className="nc-header__service-name d-none d-sm-inline">
                Document Converter
              </span>
            </div>
          </div>

          {/* Navigation area */}
          <nav aria-label="Service navigation" className="nc-header__nav">
            <a
              href="/"
              className="nc-header__nav-link"
            >
              Upload
            </a>
            <a
              href="/dashboard"
              className="nc-header__nav-link"
            >
              Dashboard
            </a>
          </nav>
        </div>
      </div>

      <style jsx>{`
        .nc-header {
          background-color: var(--nc-white, #ffffff);
          border-bottom: 3px solid var(--nc-navy, #003366);
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
        }
        .nc-header__logo-mark {
          font-size: 1.75rem;
          font-weight: bold;
          color: var(--nc-navy, #003366);
          line-height: 1;
        }
        .nc-header__logo-text {
          font-size: 1.75rem;
          font-weight: normal;
          color: var(--nc-action-blue, #1e79c8);
          line-height: 1;
        }
        .nc-header__divider {
          width: 1px;
          height: 2rem;
          background-color: var(--nc-border-gray, #dee2e6);
        }
        .nc-header__dept {
          display: block;
          font-size: 0.75rem;
          font-weight: bold;
          color: var(--nc-medium-gray, #6c757d);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          line-height: 1.2;
        }
        .nc-header__service-name {
          display: block;
          font-size: 1.125rem;
          font-weight: bold;
          color: var(--nc-navy, #003366);
          line-height: 1.3;
        }
        .nc-header__nav {
          display: flex;
          gap: 0.25rem;
        }
        .nc-header__nav-link {
          color: var(--nc-navy, #003366);
          text-decoration: none;
          font-size: 0.9375rem;
          font-weight: 600;
          padding: 0.25rem 0.5rem;
          border-radius: var(--nc-radius-sm, 0.25rem);
          transition: background-color var(--nc-transition-fast, 150ms ease-in-out);
        }
        .nc-header__nav-link:hover {
          background-color: var(--nc-light-gray, #f5f5f5);
          color: var(--nc-action-blue, #1e79c8);
        }

        @media (max-width: 575.98px) {
          .nc-header__logo-mark,
          .nc-header__logo-text {
            font-size: 1.25rem;
          }
          .nc-header__divider {
            height: 1.5rem;
          }
          .nc-header__service-name {
            font-size: 0.9375rem;
          }
        }
      `}</style>
    </header>
  );
}
