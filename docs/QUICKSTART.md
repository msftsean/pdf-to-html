# 🚀 Quick Start Guide

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20+-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![Azure Functions v4](https://img.shields.io/badge/Azure_Functions-v4-0078D4?style=flat-square&logo=azure-functions&logoColor=white)](https://azure.microsoft.com/en-us/products/functions)

Welcome to **NCDIT Document Converter**, a WCAG 2.1 AA compliant PDF/DOCX/PPTX-to-HTML converter built for North Carolina state government.

This guide gets you from zero to converting your first document in **~10 minutes**.

---

## 📋 Prerequisites

| Tool | Version | Installed | Why |
|------|---------|-----------|-----|
| **🐍 Python** | 3.12+ | `python3 --version` | Backend runtime |
| **🟢 Node.js** | 20+ | `node --version` | Frontend development |
| **📦 npm** | 9+ | `npm --version` | Frontend package manager |
| **⚡ Azure Functions Core Tools** | 4.x | `func --version` | Local function runtime |
| **💾 Azurite** | latest | `npx azurite --version` | Local blob storage emulator |

### Install Prerequisites

**macOS (Homebrew):**
```bash
brew install python@3.12 node azure-functions-core-tools@4
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv nodejs npm
npm install -g azure-functions-core-tools@4
```

**Windows (PowerShell - Admin):**
```powershell
choco install python nodejs azure-functions-core-tools
# or use winget:
winget install Python.Python.3.12 OpenJS.NodeJS Microsoft.AzureFunctionsCoreTools
```

---

## 🔧 Development Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/NCDIT/pdf-to-html.git
cd pdf-to-html
```

### Step 2: Validate Your Setup

Run the quickstart validation script to ensure all prerequisites are installed:

```bash
bash scripts/quickstart-check.sh
```

This checks:
- ✅ Python, Node, npm, func CLI versions
- ✅ Backend dependencies (Azure SDK, PyMuPDF, etc.)
- ✅ Frontend dependencies (Next.js, React, etc.)
- ✅ Backend unit tests pass
- ✅ Frontend builds successfully

**All green?** Skip ahead to "Start the Services". **Got failures?** See [Troubleshooting](#troubleshooting).

### Step 3: Install Backend Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Azure Functions SDK
- PyMuPDF (PDF text/image extraction)
- Azure Document Intelligence (OCR)
- python-docx, python-pptx (document extraction)
- pytest, pytest-asyncio (testing)

### Step 4: Configure Environment

Copy the example environment file:

```bash
cp .env.example .env.local
```

Edit `.env.local` to configure:

```bash
# Azure Storage — use Azurite for local development
AzureWebJobsStorage=UseDevelopmentStorage=true

# Azure Document Intelligence — required for OCR on scanned PDFs
# Get your endpoint from Azure Portal → Document Intelligence resource
DOCUMENT_INTELLIGENCE_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/

# Output container for converted HTML and images
OUTPUT_CONTAINER=converted

# Frontend API URL (for Next.js)
NEXT_PUBLIC_API_URL=http://localhost:7071/api
```

**Note:** For local development without Azure, the backend handles PDFs with embedded text without OCR. Scanned PDFs require `DOCUMENT_INTELLIGENCE_ENDPOINT`.

### Step 5: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## ▶️ Start the Services

### Terminal 1: Blob Storage Emulator (Azurite)

```bash
npx azurite-blob --silent
```

This starts a local Azure Blob Storage emulator on port 10000. Your local Azure Functions will use this for file uploads/downloads.

**Verify it's running:**
```bash
curl -I http://localhost:10000
# Should return: 400 Bad Request (expected)
```

### Terminal 2: Backend (Azure Functions)

```bash
func start
```

This starts the Azure Functions runtime on `http://localhost:7071`. The functions will:
- 🔍 Watch the `files/` blob container for uploads
- 📄 Extract text, images, tables from documents
- 🤖 Run OCR on scanned PDFs (if configured)
- 🎨 Generate WCAG-compliant HTML
- 💾 Save output to the `converted/` container

**Verify it's running:**
```bash
curl http://localhost:7071/api/documents/status
# Should return a JSON response (confirms Azure Functions is listening)
```

### Terminal 3: Frontend (Next.js Dev Server)

```bash
cd frontend
npm run dev
```

This starts the Next.js development server on `http://localhost:3000`. Hot-reloading is enabled — save a file and the browser refreshes automatically.

**Verify it's running:**
```bash
curl http://localhost:3000
# Should return HTML
```

---

## 📄 Convert Your First Document

### Option A: Web UI (Recommended)

1. Open **http://localhost:3000** in your browser
2. You'll see the **Upload Interface** with a drag-and-drop zone
3. Drag any PDF, DOCX, or PPTX file onto the zone
4. Watch the **Progress Dashboard** show real-time conversion status:
   - 📥 Uploaded
   - 🔄 Extracting text/images
   - 🤖 Running OCR (if needed)
   - 🎨 Building HTML
   - ✅ Complete
5. **Preview** the output in the browser
6. **Download** the converted package (HTML + assets + metadata)

### Option B: CLI / Direct Blob Upload

Upload a document directly to the `files/` container:

```bash
# Using Azure CLI
az storage blob upload \
  --account-name 127.0.0.1:10000 \
  --container-name files \
  --file my-document.pdf \
  --name my-document.pdf \
  --connection-string "UseDevelopmentStorage=true"
```

Or with `curl`:

```bash
curl -X PUT \
  -H "x-ms-blob-type: BlockBlob" \
  --data-binary @my-document.pdf \
  http://127.0.0.1:10000/devstoreaccount1/files/my-document.pdf
```

The backend's blob trigger fires automatically. Check the output:

```bash
az storage blob list \
  --account-name 127.0.0.1:10000 \
  --container-name converted \
  --connection-string "UseDevelopmentStorage=true" \
  --output table
```

---

## 🧪 Run Tests

### Backend Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ -v --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_wcag_validator.py -v

# Run only WCAG validation tests
pytest tests/ -k "wcag" -v
```

### Frontend Tests

```bash
cd frontend

# Run Next.js linter
npm run lint

# Build frontend (catches TypeScript errors)
npm run build
```

### Integration Tests

```bash
# Requires backend and Azurite running
pytest tests/integration/ -v
```

---

## 🏗️ Project Structure

```
pdf-to-html/
├── function_app.py           # Azure Functions orchestrator
├── requirements.txt          # Python dependencies
├── host.json                 # Azure Functions config
│
├── backend/                  # Python backend package
│   ├── pdf_extractor.py      # PDF → text/images/tables (PyMuPDF)
│   ├── docx_extractor.py     # Word document → structured content (python-docx)
│   ├── pptx_extractor.py     # PowerPoint → slide-by-slide content (python-pptx)
│   ├── ocr_service.py        # Azure Document Intelligence OCR client
│   ├── html_builder.py       # WCAG-compliant HTML generation
│   ├── wcag_validator.py     # Server-side WCAG 2.1 AA validation (7 Python rules)
│   ├── status_service.py     # Processing status tracking via blob metadata
│   └── models.py             # Pydantic data models
│
├── frontend/                 # Next.js 14 React app
│   ├── app/                  # App Router (Next.js 13+)
│   ├── components/           # React components (GovBanner, NCHeader, UploadZone, etc.)
│   ├── services/             # API client services (upload, status, download)
│   └── styles/               # NCDIT Bootstrap styles
│
├── tests/
│   ├── unit/                 # Backend unit tests (174 tests)
│   ├── integration/          # End-to-end tests
│   ├── eval/                 # WCAG evaluation suite
│   └── conftest.py           # Pytest fixtures
│
├── docs/                     # Project documentation
│   ├── QUICKSTART.md         # This file
│   ├── DEPLOYMENT.md         # Azure deployment guide
│   └── runbook/              # Operations runbook
│
├── scripts/
│   ├── quickstart-check.sh   # Setup validation script
│   ├── run_evals.py          # WCAG evaluation runner
│   └── render_report.py      # Evaluation report generator
│
├── specs/
│   └── 001-sean/
│       ├── spec.md           # Feature specification
│       ├── plan.md           # Architecture & design
│       ├── tasks.md          # 79 implementation tasks
│       └── contracts/        # API contracts (upload, status, download)
│
├── .env.example              # Environment variables template
└── README.md                 # Project overview
```

---

## 🔗 API Contracts

### 📤 Upload SAS Token

```bash
POST http://localhost:7071/api/upload/sas-token
Content-Type: application/json

{
  "filename": "my-document.pdf"
}
```

Response:
```json
{
  "sas_url": "http://127.0.0.1:10000/devstoreaccount1/files/my-document.pdf?sv=...",
  "document_id": "my-document.pdf"
}
```

### 📊 Document Conversion Status

```bash
GET http://localhost:7071/api/documents/status?document_id=my-document.pdf
```

Response:
```json
{
  "document_id": "my-document.pdf",
  "status": "completed",
  "progress": 100,
  "message": "Conversion complete"
}
```

### 📥 Download Converted Document

```bash
GET http://localhost:7071/api/documents/my-document.pdf/download
```

Response:
```json
{
  "download_url": "http://127.0.0.1:10000/devstoreaccount1/converted/my-document/output.html?sv=...",
  "document_id": "my-document.pdf"
}
```

> ⚠️ **Note:** There is no dedicated `/api/health` endpoint. To verify the backend is running, use the status endpoint or check the Azure Functions runtime output in your terminal.

---

## 🔗 Important Links

- **Specification:** [specs/001-sean/spec.md](specs/001-sean/spec.md) — Feature requirements and acceptance criteria
- **Architecture:** [specs/001-sean/plan.md](specs/001-sean/plan.md) — Design decisions and system architecture
- **Original Quickstart:** [specs/001-sean/quickstart.md](specs/001-sean/quickstart.md) — Detailed service setup guide
- **WCAG Compliance:** Built for WCAG 2.1 AA; run `pytest tests/ -k wcag` to validate
- **Azure Functions Docs:** https://learn.microsoft.com/azure/azure-functions/
- **Next.js Docs:** https://nextjs.org/docs

---

## ❓ Troubleshooting

### Python 3.12 Not Found

**Error:** `python3: command not found` or version is 3.9 or 3.10

**Fix:**
```bash
# macOS
brew install python@3.12

# Ubuntu
sudo apt install python3.12 python3.12-venv

# Verify
python3.12 --version
pip3.12 install -r requirements.txt
```

### Node.js Version Too Old

**Error:** `npm ERR! The engine "node" is incompatible with this module`

**Fix:**
```bash
# Using nvm (recommended)
nvm install 20
nvm use 20
node --version  # Should be v20.x.x

# Or using Homebrew
brew install node@20
brew link node@20 --force
```

### Azurite Won't Start

**Error:** `Port 10000 already in use` or `EADDRINUSE`

**Fix:**
```bash
# Kill existing process
lsof -i :10000
kill -9 <PID>

# Or use a different port
npx azurite-blob --blobPort 10001 --silent

# Update AzureWebJobsStorage in .env.local:
# AzureWebJobsStorage=UseDevelopmentStorage=true;BlobEndpoint=http://127.0.0.1:10001/devstoreaccount1
```

### `func start` Fails with Missing Python Bindings

**Error:** `No Python interpreter found` or `Worker runtime 'python' not found`

**Fix:**
```bash
# Install Azure Functions Core Tools v4 (not v3)
npm uninstall -g azure-functions-core-tools
npm install -g azure-functions-core-tools@4

# Verify
func --version  # Should be 4.x.x

# Re-run
func start
```

### Environment Variables Not Loaded

**Error:** `DOCUMENT_INTELLIGENCE_ENDPOINT not set` or missing in function

**Fix:**
```bash
# Ensure .env.local exists (not .env!)
cp .env.example .env.local
cat .env.local  # Verify values

# Load into shell (Azure Functions reads these automatically)
export $(cat .env.local | xargs)

# Verify
echo $AzureWebJobsStorage
```

### Frontend Can't Connect to Backend

**Error:** Browser console: `GET http://localhost:7071/api/... 404 Not Found`

**Fix:**
1. Verify backend is running: `curl http://localhost:7071/api/health`
2. Verify frontend API URL in `frontend/.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:7071/api
   ```
3. Rebuild frontend: `cd frontend && npm run build`

### "Cannot find module" Errors in Frontend

**Error:** `Module not found: Can't resolve 'next/image'`

**Fix:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Tests Fail with Import Errors

**Error:** `ModuleNotFoundError: No module named 'azure'`

**Fix:**
```bash
pip install -r requirements.txt --force-reinstall
python3 -m pytest tests/unit/test_models.py -v  # Run a single test
```

### Still Stuck?

1. Run the validation script: `bash scripts/quickstart-check.sh`
2. Check Azure Functions logs: `func --verbose` when running `func start`
3. Check frontend build output: `cd frontend && npm run build --verbose`
4. Open an issue: Include output from `scripts/quickstart-check.sh` and relevant error logs

---

## 📊 What's Next?

- **Explore the code:** Start with `function_app.py` to understand the Azure Functions flow
- **Review the spec:** [specs/001-sean/spec.md](specs/001-sean/spec.md) for full feature requirements
- **Read the architecture:** [specs/001-sean/plan.md](specs/001-sean/plan.md) for design decisions
- **Run the tests:** `pytest tests/ -v` to see the full test suite
- **Deploy to Azure:** Follow the [Operations Runbook](docs/runbook/README.md) for deployment guidance

---

## 📌 Version Matrix

> Versions required for local development — verified against current `requirements.txt` and `package.json`

| Category | Dependency | Version | Required |
|----------|-----------|---------|----------|
| 🐍 **Backend** | Python | 3.12+ | ✅ Yes |
| ⚡ **Runtime** | Azure Functions Core Tools | 4.x | ✅ Yes |
| ⚡ **Runtime** | Azure Functions SDK | 1.24.0 | Auto-installed |
| 📄 **PDF** | PyMuPDF | 1.27.2 | Auto-installed |
| 🔍 **OCR** | Azure AI Document Intelligence | 1.0.2 | Auto-installed |
| 📝 **DOCX** | python-docx | 1.2.0 | Auto-installed |
| 📊 **PPTX** | python-pptx | 1.0.2 | Auto-installed |
| 🌐 **Frontend** | Node.js | 20+ | ✅ Yes |
| 🌐 **Frontend** | Next.js | 14.2.35 | Auto-installed |
| ⚛️ **Frontend** | React | ^18 | Auto-installed |
| 🎨 **Frontend** | Bootstrap | ^5.3.8 | Auto-installed |
| 💾 **Storage** | Azurite | latest | ✅ Yes |

---

**Happy converting! 🎉**

---

<sub>📅 Last Updated: 2025-07-24 · Maintained by 🦇 Batman (Tech Lead)</sub>
