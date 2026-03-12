# Quickstart: WCAG Document-to-HTML Converter

## Prerequisites

- Python 3.12+
- Node.js 20+
- Azure Functions Core Tools v4
- Azure Storage Emulator or Azurite (for local dev)
- An Azure Document Intelligence resource (for OCR)

## Backend Setup

```bash
# Clone and enter project
cd /workspaces/pdf-to-html

# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export AzureWebJobsStorage="UseDevelopmentStorage=true"
export DOCUMENT_INTELLIGENCE_ENDPOINT="https://<your-resource>.cognitiveservices.azure.com/"
export OUTPUT_CONTAINER="converted"

# Start Azurite (local blob storage)
azurite-blob --silent &

# Create input/output containers
az storage container create -n files --connection-string "UseDevelopmentStorage=true"
az storage container create -n converted --connection-string "UseDevelopmentStorage=true"

# Start Azure Functions locally
func start
```

## Frontend Setup

```bash
# Enter frontend directory
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local with your Azure Functions URL

# Start dev server
npm run dev
```

Open http://localhost:3000 to see the upload interface.

## Testing

### Backend Tests

```bash
# Run all backend tests
pytest tests/ -v

# Run with WCAG validation
pytest tests/ -v -k "wcag"
```

### Frontend Tests

```bash
cd frontend

# Unit + component tests
npm test

# Accessibility tests
npm run test:a11y

# E2E tests (requires backend running)
npx playwright test
```

## Converting a Document

### Via Web UI

1. Open http://localhost:3000
2. Drag a PDF, DOCX, or PPTX onto the upload area
3. Watch progress in the dashboard
4. Preview the HTML output
5. Download the converted package

### Via Direct Upload (CLI)

```bash
# Upload a PDF to the files container
az storage blob upload \
  --container-name files \
  --file my-document.pdf \
  --name my-document.pdf \
  --connection-string "UseDevelopmentStorage=true"

# The blob trigger fires automatically
# Check output in the converted container
az storage blob list \
  --container-name converted \
  --connection-string "UseDevelopmentStorage=true" \
  --output table
```

## Project Structure Overview

| File | Purpose |
|------|---------|
| `function_app.py` | Azure Functions orchestrator |
| `pdf_extractor.py` | PDF text/image/table extraction |
| `ocr_service.py` | Azure Document Intelligence OCR |
| `html_builder.py` | WCAG-compliant HTML generation |
| `docx_extractor.py` | Word document extraction (new) |
| `pptx_extractor.py` | PowerPoint extraction (new) |
| `wcag_validator.py` | axe-core validation wrapper (new) |
| `status_service.py` | Processing status tracking (new) |
| `frontend/` | React/Next.js web interface (new) |
