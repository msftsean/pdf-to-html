'use client';

/**
 * NCFooter — NC.gov Standard Footer
 *
 * Government-standard footer with required links:
 * NC.gov, Accessibility, Privacy Policy, Contact.
 *
 * Accessibility:
 * - role="contentinfo" on <footer> element
 * - All links are keyboard-navigable
 * - White text on navy: 11.8:1 contrast ratio (exceeds AA)
 * - Social media placeholder area for future integration
 */
export default function NCFooter() {
  const currentYear = new Date().getFullYear();

  return (
    <footer role="contentinfo" className="nc-footer">
      <div className="container py-4">
        <div className="row g-4">
          {/* Branding Column */}
          <div className="col-md-4">
            <div className="nc-footer__brand mb-3">
              <span className="nc-footer__logo" aria-hidden="true">
                NC
              </span>
              <span className="nc-footer__logo-accent">.gov</span>
            </div>
            <p className="nc-footer__tagline mb-0">
              An official website of the State of North Carolina
            </p>
          </div>

          {/* Links Column */}
          <div className="col-md-4">
            <h2 className="nc-footer__heading">Resources</h2>
            <nav aria-label="Footer navigation">
              <ul className="nc-footer__links list-unstyled mb-0">
                <li>
                  <a
                    href="https://www.nc.gov"
                    className="nc-footer__link"
                    rel="noopener noreferrer"
                  >
                    NC.gov
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.nc.gov/accessibility"
                    className="nc-footer__link"
                  >
                    Accessibility
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.nc.gov/privacy-policy"
                    className="nc-footer__link"
                  >
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a
                    href="https://it.nc.gov/contact"
                    className="nc-footer__link"
                  >
                    Contact NCDIT
                  </a>
                </li>
              </ul>
            </nav>
          </div>

          {/* Social + Contact Column */}
          <div className="col-md-4">
            <h2 className="nc-footer__heading">Connect</h2>
            {/* Social media icons — placeholder for future integration */}
            <div
              className="nc-footer__social d-flex gap-3 mb-3"
              aria-label="Social media links"
            >
              <a
                href="https://twitter.com/NCDITgov"
                className="nc-footer__social-link"
                aria-label="NCDIT on Twitter"
                rel="noopener noreferrer"
              >
                𝕏
              </a>
              <a
                href="https://www.facebook.com/ncaboret"
                className="nc-footer__social-link"
                aria-label="North Carolina on Facebook"
                rel="noopener noreferrer"
              >
                f
              </a>
              <a
                href="https://www.youtube.com/@NCDITgov"
                className="nc-footer__social-link"
                aria-label="NCDIT on YouTube"
                rel="noopener noreferrer"
              >
                ▶
              </a>
            </div>
          </div>
        </div>

        {/* Copyright Bar */}
        <div className="nc-footer__copyright border-top border-secondary pt-3 mt-4">
          <p className="mb-0 text-center" style={{ fontSize: '0.8125rem' }}>
            © {currentYear} State of North Carolina. All rights reserved.
          </p>
        </div>
      </div>

      <style jsx>{`
        .nc-footer {
          background-color: var(--nc-navy, #003366);
          color: var(--nc-white, #ffffff);
          font-family: var(--nc-font-body, Georgia, serif);
        }
        .nc-footer__logo {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          font-size: 1.5rem;
          font-weight: bold;
          color: var(--nc-white, #ffffff);
        }
        .nc-footer__logo-accent {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          font-size: 1.5rem;
          color: rgba(255, 255, 255, 0.7);
        }
        .nc-footer__tagline {
          font-size: 0.875rem;
          color: rgba(255, 255, 255, 0.8);
        }
        .nc-footer__heading {
          font-family: var(--nc-font-heading, 'Century Gothic', sans-serif);
          font-size: 0.9375rem;
          font-weight: bold;
          color: var(--nc-white, #ffffff);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 0.75rem;
        }
        .nc-footer__link {
          color: rgba(255, 255, 255, 0.85);
          text-decoration: none;
          font-size: 0.9375rem;
          display: inline-block;
          padding: 0.25rem 0;
          transition: color var(--nc-transition-fast, 150ms ease-in-out);
        }
        .nc-footer__link:hover,
        .nc-footer__link:focus {
          color: var(--nc-white, #ffffff);
          text-decoration: underline;
        }
        .nc-footer__social-link {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 2.25rem;
          height: 2.25rem;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.15);
          color: var(--nc-white, #ffffff);
          text-decoration: none;
          font-size: 1rem;
          transition: background-color var(--nc-transition-fast, 150ms ease-in-out);
        }
        .nc-footer__social-link:hover,
        .nc-footer__social-link:focus {
          background: rgba(255, 255, 255, 0.3);
          color: var(--nc-white, #ffffff);
        }
        .nc-footer__copyright {
          border-color: rgba(255, 255, 255, 0.2) !important;
        }
      `}</style>
    </footer>
  );
}
