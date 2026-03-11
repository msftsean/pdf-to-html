/**
 * Home Page — NCDIT Document Converter
 *
 * Landing page with a brief description of the service.
 * Upload functionality will be integrated in a later phase.
 */
export default function Home() {
  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-lg-8 text-center">
          <h1 className="mb-4">Document Converter</h1>
          <p className="lead mb-4" style={{ fontSize: '1.125rem' }}>
            Convert your PDF, Word, and PowerPoint documents into
            accessible, WCAG 2.1 AA compliant HTML — ready for the web.
          </p>

          <div
            className="card border-0 shadow-sm p-4 p-md-5 mb-4"
            style={{ backgroundColor: 'var(--nc-light-gray)' }}
          >
            <div className="text-center">
              <span
                style={{ fontSize: '3rem' }}
                role="img"
                aria-label="Document icon"
              >
                📄
              </span>
              <h2 className="h4 mt-3 mb-2">Upload Coming Soon</h2>
              <p className="text-muted mb-0">
                Drag-and-drop file upload will be available in the next release.
                <br />
                Supported formats: PDF, DOCX, PPTX (up to 50 MB).
              </p>
            </div>
          </div>

          <div className="row g-4 mt-2">
            <div className="col-md-4">
              <div className="p-3">
                <span
                  style={{ fontSize: '2rem' }}
                  role="img"
                  aria-label="Accessibility"
                >
                  ♿
                </span>
                <h3 className="h6 mt-2">WCAG 2.1 AA</h3>
                <p className="small text-muted mb-0">
                  Output meets federal and state accessibility standards.
                </p>
              </div>
            </div>
            <div className="col-md-4">
              <div className="p-3">
                <span
                  style={{ fontSize: '2rem' }}
                  role="img"
                  aria-label="Speed"
                >
                  ⚡
                </span>
                <h3 className="h6 mt-2">Fast Processing</h3>
                <p className="small text-muted mb-0">
                  Real-time progress tracking with page-by-page conversion.
                </p>
              </div>
            </div>
            <div className="col-md-4">
              <div className="p-3">
                <span
                  style={{ fontSize: '2rem' }}
                  role="img"
                  aria-label="Quality"
                >
                  ✅
                </span>
                <h3 className="h6 mt-2">Quality Review</h3>
                <p className="small text-muted mb-0">
                  Flagged pages requiring human review for OCR confidence.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
