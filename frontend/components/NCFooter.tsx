'use client';

/**
 * NCFooter — Runbook-styled Footer
 *
 * Dark surface background, clean minimal layout.
 * NC.gov links, copyright, social media placeholders.
 *
 * Accessibility:
 * - role="contentinfo" on <footer>
 * - All links keyboard-navigable
 * - Sufficient contrast in both themes
 */
export default function NCFooter() {
  const currentYear = new Date().getFullYear();

  return (
    <footer role="contentinfo" className="nc-footer">
      <div className="container py-4">
        <div className="footer-grid">
          {/* Branding Column */}
          <div className="footer-brand">
            <div className="footer-logo-row">
              <span className="footer-logo" aria-hidden="true">NC</span>
              <span className="footer-logo-accent">.gov</span>
            </div>
            <p className="footer-tagline">
              An official website of the State of North Carolina
            </p>
          </div>

          {/* Links Column */}
          <div>
            <h2 className="footer-heading">Resources</h2>
            <nav aria-label="Footer navigation">
              <ul className="footer-links">
                <li>
                  <a href="https://www.nc.gov" className="footer-link" rel="noopener noreferrer">
                    NC.gov
                  </a>
                </li>
                <li>
                  <a href="https://www.nc.gov/accessibility" className="footer-link">
                    Accessibility
                  </a>
                </li>
                <li>
                  <a href="https://www.nc.gov/privacy-policy" className="footer-link">
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a href="https://it.nc.gov/contact" className="footer-link">
                    Contact NCDIT
                  </a>
                </li>
              </ul>
            </nav>
          </div>

          {/* Social + Connect Column */}
          <div>
            <h2 className="footer-heading">Connect</h2>
            <div className="footer-social" aria-label="Social media links">
              <a
                href="https://twitter.com/NCDITgov"
                className="footer-social-link"
                aria-label="NCDIT on Twitter"
                rel="noopener noreferrer"
              >
                𝕏
              </a>
              <a
                href="https://www.facebook.com/ncaboret"
                className="footer-social-link"
                aria-label="North Carolina on Facebook"
                rel="noopener noreferrer"
              >
                f
              </a>
              <a
                href="https://www.youtube.com/@NCDITgov"
                className="footer-social-link"
                aria-label="NCDIT on YouTube"
                rel="noopener noreferrer"
              >
                ▶
              </a>
            </div>
          </div>
        </div>

        {/* Copyright */}
        <div className="footer-copyright">
          <p>© {currentYear} State of North Carolina. All rights reserved.</p>
        </div>
      </div>

      <style jsx>{`
        .footer-grid {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 2rem;
        }

        @media (max-width: 767.98px) {
          .footer-grid {
            grid-template-columns: 1fr;
            gap: 1.5rem;
          }
        }

        .footer-brand {
          display: flex;
          flex-direction: column;
        }

        .footer-logo-row {
          display: flex;
          align-items: baseline;
          margin-bottom: 0.5rem;
        }

        .footer-logo {
          font-family: var(--font-heading);
          font-size: 1.5rem;
          font-weight: 800;
          color: var(--text-primary);
        }

        .footer-logo-accent {
          font-family: var(--font-heading);
          font-size: 1.5rem;
          font-weight: 400;
          color: var(--accent-sky);
        }

        .footer-tagline {
          font-size: 0.875rem;
          color: var(--text-muted);
          margin-bottom: 0;
        }

        .footer-heading {
          font-family: var(--font-heading);
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--text-muted);
          margin-bottom: 0.75rem;
        }

        .footer-links {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .footer-link {
          color: var(--text-secondary);
          text-decoration: none;
          font-size: 0.9375rem;
          display: inline-block;
          padding: 0.2rem 0;
          transition: color var(--transition-fast);
        }

        .footer-link:hover,
        .footer-link:focus {
          color: var(--accent-sky);
        }

        .footer-social {
          display: flex;
          gap: 0.75rem;
        }

        .footer-social-link {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 2.25rem;
          height: 2.25rem;
          border-radius: 50%;
          background: var(--surface);
          border: 1px solid var(--border);
          color: var(--text-secondary);
          text-decoration: none;
          font-size: 0.9rem;
          transition: all var(--transition-fast);
        }

        .footer-social-link:hover,
        .footer-social-link:focus {
          background: var(--surface-hover);
          color: var(--accent-sky);
          border-color: var(--border-hover);
        }

        .footer-copyright {
          border-top: 1px solid var(--border);
          padding-top: 1rem;
          margin-top: 2rem;
          text-align: center;
        }

        .footer-copyright p {
          font-size: 0.8125rem;
          color: var(--text-muted);
          margin: 0;
        }
      `}</style>
    </footer>
  );
}
