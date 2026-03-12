<div align="center">

# 🌐 NCDIT Document Converter — Frontend

**WCAG 2.1 AA Accessible Web Interface for Document-to-HTML Conversion**

[![Next.js 14](https://img.shields.io/badge/Next.js-14.2.35-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Bootstrap 5](https://img.shields.io/badge/Bootstrap-5.3.8-7952B3?style=flat-square&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![axe-core](https://img.shields.io/badge/axe--core-4.11.1-663399?style=flat-square)](https://www.deque.com/axe/)
[![TypeScript 5](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

</div>

---

## ✨ Features

| Feature | Status | Description |
|---------|--------|-------------|
| 📤 **Drag-and-Drop Upload** | ✅ Implemented | Upload PDF, DOCX, PPTX files via accessible drop zone |
| 📊 **Live Progress Dashboard** | ✅ Implemented | Real-time conversion status with polling |
| 👁️ **HTML Preview** | ✅ Implemented | In-browser preview of converted output |
| 📥 **Download Packages** | ✅ Implemented | Download HTML + images as zip package |
| 🏛️ **NCDIT Digital Commons** | ✅ Implemented | NC.gov branding, GovBanner, NCHeader components |
| ♿ **WCAG 2.1 AA** | ✅ Implemented | Keyboard nav, screen reader support, color contrast |
| 📦 **Batch Upload** | ✅ Implemented | Process multiple documents concurrently |

## 🚀 Getting Started

### Prerequisites

- **Node.js** 20+ (`node --version`)
- **npm** 9+ (`npm --version`)
- Backend running on `http://localhost:7071` (see [root QUICKSTART](../QUICKSTART.md))

### Install & Run

```bash
# Install dependencies
npm install

# Start development server (http://localhost:3000)
npm run dev
```

### 🔧 Environment Configuration

Create `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:7071/api
```

## 🧪 Testing

```bash
# Run all tests (Jest + React Testing Library)
npm test

# Watch mode
npm run test:watch

# Lint (ESLint + Next.js rules)
npm run lint

# Build (catches TypeScript errors)
npm run build
```

**Test stack:** Jest ^30.3.0 · React Testing Library ^16.3.2 · jest-axe ^10.0.0 (accessibility assertions)

## 📁 Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx          # Root layout (GovBanner, NCHeader, footer)
│   ├── page.tsx            # Home page (upload interface)
│   └── globals.css         # Global styles
├── components/             # React components
│   ├── GovBanner.tsx       # US government website banner
│   ├── NCHeader.tsx        # NCDIT header with logo
│   ├── UploadZone.tsx      # Drag-and-drop file upload
│   ├── ProgressDashboard.tsx # Live conversion progress
│   ├── DocumentPreview.tsx # HTML preview panel
│   └── DownloadButton.tsx  # Package download
├── services/               # API client services
│   ├── uploadService.ts    # SAS token upload flow
│   ├── statusService.ts    # Polling for conversion status
│   └── downloadService.ts  # Download URL generation
├── styles/                 # NCDIT Digital Commons tokens
├── __tests__/              # Test files
├── package.json            # Dependencies & scripts
├── tsconfig.json           # TypeScript config
└── next.config.mjs         # Next.js configuration
```

## 📌 Version Matrix

> Pulled from `package.json` — exact versions used in this project

| Category | Package | Version |
|----------|---------|---------|
| 🌐 **Framework** | Next.js | `14.2.35` |
| ⚛️ **UI** | React | `^18` |
| ⚛️ **UI** | React DOM | `^18` |
| 🎨 **Styling** | Bootstrap | `^5.3.8` |
| ♿ **Accessibility** | axe-core | `^4.11.1` |
| ♿ **Accessibility** | @axe-core/react | `^4.11.1` |
| 📦 **Archive** | JSZip | `^3.10.1` |
| 🔧 **Language** | TypeScript | `^5` |
| 🧪 **Testing** | Jest | `^30.3.0` |
| 🧪 **Testing** | jest-axe | `^10.0.0` |
| 🧪 **Testing** | @testing-library/react | `^16.3.2` |
| 🔍 **Lint** | ESLint | `8.57.1` |
| 🔍 **Lint** | eslint-config-next | `^14.2.35` |

## 📚 Learn More

- [Next.js Documentation](https://nextjs.org/docs) — Framework features and API
- [React Documentation](https://react.dev/) — Component patterns
- [NCDIT Digital Commons](https://it.nc.gov) — NC.gov design system
- [axe-core Rules](https://dequeuniversity.com/rules/axe/) — WCAG testing rules

---

<sub>📅 Last Updated: 2025-07-24 · Maintained by ⚡ Flash (Frontend Developer)</sub>
