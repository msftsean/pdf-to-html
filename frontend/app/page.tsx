import FileUpload from '@/components/FileUpload';

/**
 * Home Page — NCDIT Document Converter
 *
 * Landing page with hero section, drag-and-drop file upload,
 * supported formats card, and "How It Works" steps.
 *
 * US6 — Web Upload Interface
 */
export default function Home() {
  return (
    <>
      {/* ----------------------------------------------------------------
          Hero Section
          ---------------------------------------------------------------- */}
      <section className="nc-hero" aria-labelledby="hero-heading">
        <div className="container py-5">
          <div className="row justify-content-center">
            <div className="col-lg-8 text-center">
              <h1 id="hero-heading" className="nc-hero__title mb-3">
                NCDIT Document Converter
              </h1>
              <p className="nc-hero__subtitle mb-0">
                Convert your PDF, Word, and PowerPoint documents into
                accessible, WCAG&nbsp;2.1&nbsp;AA compliant HTML — ready for
                the web.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------
          Upload Section
          ---------------------------------------------------------------- */}
      <section aria-labelledby="upload-heading" className="py-5">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-lg-8">
              <h2 id="upload-heading" className="visually-hidden">
                Upload Documents
              </h2>
              <FileUpload />
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------
          Supported Formats
          ---------------------------------------------------------------- */}
      <section
        className="nc-formats nc-bg-light py-5"
        aria-labelledby="formats-heading"
      >
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-lg-8">
              <div className="card border-0 shadow-sm p-4">
                <h2
                  id="formats-heading"
                  className="h5 text-center mb-4"
                >
                  Supported Formats
                </h2>
                <div className="row g-3 text-center">
                  <div className="col-sm-4">
                    <div className="nc-format-card p-3">
                      <span
                        className="nc-format-card__icon"
                        aria-hidden="true"
                      >
                        📄
                      </span>
                      <h3 className="h6 mt-2 mb-1">PDF</h3>
                      <p className="small text-muted mb-0">
                        Adobe Portable Document Format
                      </p>
                    </div>
                  </div>
                  <div className="col-sm-4">
                    <div className="nc-format-card p-3">
                      <span
                        className="nc-format-card__icon"
                        aria-hidden="true"
                      >
                        📝
                      </span>
                      <h3 className="h6 mt-2 mb-1">Word (.docx)</h3>
                      <p className="small text-muted mb-0">
                        Microsoft Word documents
                      </p>
                    </div>
                  </div>
                  <div className="col-sm-4">
                    <div className="nc-format-card p-3">
                      <span
                        className="nc-format-card__icon"
                        aria-hidden="true"
                      >
                        📊
                      </span>
                      <h3 className="h6 mt-2 mb-1">PowerPoint (.pptx)</h3>
                      <p className="small text-muted mb-0">
                        Microsoft PowerPoint presentations
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------
          How It Works — 3 Steps
          ---------------------------------------------------------------- */}
      <section className="nc-steps py-5" aria-labelledby="steps-heading">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-lg-8 text-center">
              <h2 id="steps-heading" className="h4 mb-4">
                How It Works
              </h2>
              <div className="row g-4">
                {/* Step 1 */}
                <div className="col-md-4">
                  <div className="nc-step p-3">
                    <span
                      className="nc-step__number"
                      aria-hidden="true"
                    >
                      1
                    </span>
                    <span
                      className="nc-step__icon"
                      aria-hidden="true"
                    >
                      ⬆️
                    </span>
                    <h3 className="h6 mt-2 mb-1">Upload</h3>
                    <p className="small text-muted mb-0">
                      Drag and drop your document or click to browse.
                      Supports PDF, DOCX, and PPTX up to 100&nbsp;MB.
                    </p>
                  </div>
                </div>

                {/* Step 2 */}
                <div className="col-md-4">
                  <div className="nc-step p-3">
                    <span
                      className="nc-step__number"
                      aria-hidden="true"
                    >
                      2
                    </span>
                    <span
                      className="nc-step__icon"
                      aria-hidden="true"
                    >
                      ⚙️
                    </span>
                    <h3 className="h6 mt-2 mb-1">Convert</h3>
                    <p className="small text-muted mb-0">
                      Our service extracts content, runs OCR where needed,
                      and builds semantic, accessible HTML.
                    </p>
                  </div>
                </div>

                {/* Step 3 */}
                <div className="col-md-4">
                  <div className="nc-step p-3">
                    <span
                      className="nc-step__number"
                      aria-hidden="true"
                    >
                      3
                    </span>
                    <span
                      className="nc-step__icon"
                      aria-hidden="true"
                    >
                      ⬇️
                    </span>
                    <h3 className="h6 mt-2 mb-1">Download</h3>
                    <p className="small text-muted mb-0">
                      Preview the WCAG-compliant HTML output and download
                      it — ready to publish on the web.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------
          Feature Highlights
          ---------------------------------------------------------------- */}
      <section
        className="nc-bg-light py-5"
        aria-labelledby="features-heading"
      >
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-lg-8">
              <h2 id="features-heading" className="visually-hidden">
                Features
              </h2>
              <div className="row g-4 text-center">
                <div className="col-md-4">
                  <div className="p-3">
                    <span
                      className="d-block mb-2"
                      style={{ fontSize: '2rem' }}
                      aria-hidden="true"
                    >
                      ♿
                    </span>
                    <h3 className="h6 mt-1">WCAG 2.1 AA</h3>
                    <p className="small text-muted mb-0">
                      Output meets federal and state accessibility standards.
                    </p>
                  </div>
                </div>
                <div className="col-md-4">
                  <div className="p-3">
                    <span
                      className="d-block mb-2"
                      style={{ fontSize: '2rem' }}
                      aria-hidden="true"
                    >
                      ⚡
                    </span>
                    <h3 className="h6 mt-1">Fast Processing</h3>
                    <p className="small text-muted mb-0">
                      Real-time progress tracking with page-by-page conversion.
                    </p>
                  </div>
                </div>
                <div className="col-md-4">
                  <div className="p-3">
                    <span
                      className="d-block mb-2"
                      style={{ fontSize: '2rem' }}
                      aria-hidden="true"
                    >
                      ✅
                    </span>
                    <h3 className="h6 mt-1">Quality Review</h3>
                    <p className="small text-muted mb-0">
                      Flagged pages requiring human review for OCR confidence.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
