import FileUpload from '@/components/FileUpload';

/**
 * Home Page — NCDIT Document Converter
 *
 * Landing page with hero section, drag-and-drop file upload,
 * supported formats, and "How It Works" steps.
 * Redesigned with runbook aesthetic.
 *
 * US6 — Web Upload Interface
 */
export default function Home() {
  return (
    <>
      {/* ----------------------------------------------------------------
          Hero Section
          ---------------------------------------------------------------- */}
      <section className="hero" aria-labelledby="hero-heading">
        <div className="container py-5">
          <div className="hero__inner">
            <h1 id="hero-heading" className="hero__title">
              NCDIT Document Converter
            </h1>
            <p className="hero__subtitle">
              Convert your PDF, Word, and PowerPoint documents into
              accessible, WCAG&nbsp;2.1&nbsp;AA compliant HTML — ready for
              the web.
            </p>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------
          Upload Section
          ---------------------------------------------------------------- */}
      <section aria-labelledby="upload-heading" className="py-4">
        <div className="container">
          <div className="upload-wrapper">
            <h2 id="upload-heading" className="visually-hidden">
              Upload Documents
            </h2>
            <FileUpload />

            <div className="text-center mt-4">
              <a href="/dashboard" className="btn btn-outline-primary">
                📊 View Conversion Dashboard
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------
          Supported Formats
          ---------------------------------------------------------------- */}
      <section aria-labelledby="formats-heading" className="py-4">
        <div className="container">
          <div className="upload-wrapper">
            <div className="formats-card">
              <h2 id="formats-heading" className="formats-card__heading">
                Supported Formats
              </h2>
              <div className="formats-grid">
                <div className="format-item">
                  <span className="format-item__icon" aria-hidden="true">📄</span>
                  <h3 className="format-item__name">PDF</h3>
                  <p className="format-item__desc">Adobe Portable Document Format</p>
                </div>
                <div className="format-item">
                  <span className="format-item__icon" aria-hidden="true">📝</span>
                  <h3 className="format-item__name">Word (.docx)</h3>
                  <p className="format-item__desc">Microsoft Word documents</p>
                </div>
                <div className="format-item">
                  <span className="format-item__icon" aria-hidden="true">📊</span>
                  <h3 className="format-item__name">PowerPoint (.pptx)</h3>
                  <p className="format-item__desc">Microsoft PowerPoint presentations</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------
          How It Works
          ---------------------------------------------------------------- */}
      <section aria-labelledby="steps-heading" className="py-4">
        <div className="container">
          <div className="upload-wrapper text-center">
            <h2 id="steps-heading" className="section-heading">
              How It Works
            </h2>
            <div className="steps-grid">
              <div className="step-card">
                <span className="step-card__number" aria-hidden="true">1</span>
                <span className="step-card__icon" aria-hidden="true">⬆️</span>
                <h3 className="step-card__title">Upload</h3>
                <p className="step-card__desc">
                  Drag and drop your document or click to browse.
                  Supports PDF, DOCX, and PPTX up to 100&nbsp;MB.
                </p>
              </div>
              <div className="step-card">
                <span className="step-card__number" aria-hidden="true">2</span>
                <span className="step-card__icon" aria-hidden="true">⚙️</span>
                <h3 className="step-card__title">Convert</h3>
                <p className="step-card__desc">
                  Our service extracts content, runs OCR where needed,
                  and builds semantic, accessible HTML.
                </p>
              </div>
              <div className="step-card">
                <span className="step-card__number" aria-hidden="true">3</span>
                <span className="step-card__icon" aria-hidden="true">⬇️</span>
                <h3 className="step-card__title">Download</h3>
                <p className="step-card__desc">
                  Preview the WCAG-compliant HTML output and download
                  it — ready to publish on the web.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------
          Feature Highlights
          ---------------------------------------------------------------- */}
      <section aria-labelledby="features-heading" className="py-4 mb-3">
        <div className="container">
          <div className="upload-wrapper">
            <h2 id="features-heading" className="visually-hidden">Features</h2>
            <div className="features-grid">
              <div className="feature-card">
                <span className="feature-card__icon" aria-hidden="true">♿</span>
                <h3 className="feature-card__title">WCAG 2.1 AA</h3>
                <p className="feature-card__desc">
                  Output meets federal and state accessibility standards.
                </p>
              </div>
              <div className="feature-card">
                <span className="feature-card__icon" aria-hidden="true">⚡</span>
                <h3 className="feature-card__title">Fast Processing</h3>
                <p className="feature-card__desc">
                  Real-time progress tracking with page-by-page conversion.
                </p>
              </div>
              <div className="feature-card">
                <span className="feature-card__icon" aria-hidden="true">✅</span>
                <h3 className="feature-card__title">Quality Review</h3>
                <p className="feature-card__desc">
                  Flagged pages requiring human review for OCR confidence.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Scoped styles for the home page */}
      <style>{`
        .hero {
          background: linear-gradient(135deg, #0c1a30 0%, #0a1628 50%, #0f2340 100%);
          border-bottom: 1px solid var(--border);
          text-align: center;
        }

        [data-theme="light"] .hero {
          background: linear-gradient(135deg, var(--nc-navy) 0%, var(--nc-navy-dark) 100%);
        }

        .hero__inner {
          max-width: 700px;
          margin: 0 auto;
        }

        .hero__title {
          font-family: var(--font-heading);
          font-size: 2.5rem;
          font-weight: 800;
          color: #fff;
          margin-bottom: 0.75rem;
          background: linear-gradient(135deg, #e2e8f0, #38bdf8);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .hero__subtitle {
          font-family: var(--font-body);
          font-size: 1.125rem;
          color: rgba(255, 255, 255, 0.8);
          line-height: 1.6;
          margin-bottom: 0;
        }

        .upload-wrapper {
          max-width: 720px;
          margin: 0 auto;
        }

        /* Formats card */
        .formats-card {
          background: var(--card-bg);
          border: 1px solid var(--border);
          border-radius: var(--radius-lg);
          padding: 2rem;
        }

        .formats-card__heading {
          font-family: var(--font-heading);
          font-size: 1.15rem;
          font-weight: 700;
          text-align: center;
          color: var(--text-primary);
          margin-bottom: 1.5rem;
        }

        .formats-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1rem;
          text-align: center;
        }

        .format-item__icon {
          font-size: 2.5rem;
          display: block;
          margin-bottom: 0.5rem;
        }

        .format-item__name {
          font-family: var(--font-heading);
          font-size: 1rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 0.25rem;
        }

        .format-item__desc {
          font-size: 0.85rem;
          color: var(--text-muted);
          margin-bottom: 0;
        }

        /* Section heading */
        .section-heading {
          font-family: var(--font-heading);
          font-size: 1.35rem;
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: 1.5rem;
        }

        /* Steps */
        .steps-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1.5rem;
        }

        .step-card {
          background: var(--card-bg);
          border: 1px solid var(--border);
          border-radius: var(--radius-lg);
          padding: 1.5rem;
          transition: transform var(--transition-fast);
        }

        .step-card:hover {
          transform: translateY(-2px);
        }

        .step-card__number {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 2rem;
          height: 2rem;
          border-radius: 50%;
          background: var(--accent-sky);
          color: var(--deep-bg);
          font-family: var(--font-heading);
          font-weight: 800;
          font-size: 0.9rem;
          margin-bottom: 0.5rem;
        }

        .step-card__icon {
          display: block;
          font-size: 2rem;
          margin-bottom: 0.5rem;
        }

        .step-card__title {
          font-family: var(--font-heading);
          font-size: 1rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 0.25rem;
        }

        .step-card__desc {
          font-size: 0.85rem;
          color: var(--text-muted);
          margin-bottom: 0;
        }

        /* Features */
        .features-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1.5rem;
          text-align: center;
        }

        .feature-card {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: var(--radius-lg);
          padding: 1.5rem;
        }

        .feature-card__icon {
          font-size: 2rem;
          display: block;
          margin-bottom: 0.5rem;
        }

        .feature-card__title {
          font-family: var(--font-heading);
          font-size: 1rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 0.25rem;
        }

        .feature-card__desc {
          font-size: 0.85rem;
          color: var(--text-muted);
          margin-bottom: 0;
        }

        @media (max-width: 575.98px) {
          .hero__title { font-size: 1.75rem; }
          .hero__subtitle { font-size: 1rem; }
          .formats-grid, .steps-grid, .features-grid {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 767.98px) and (min-width: 576px) {
          .formats-grid, .steps-grid, .features-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }
      `}</style>
    </>
  );
}
