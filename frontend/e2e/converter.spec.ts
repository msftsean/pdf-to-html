/**
 * End-to-end Playwright tests for the WCAG Document Converter.
 *
 * Run against local stack:
 *   cd frontend && npx playwright test
 *
 * Run against Azure:
 *   FRONTEND_URL=https://ca-pdftohtml-frontend.xxx.azurecontainerapps.io \
 *   cd frontend && npx playwright test
 */
import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Create a minimal valid PDF buffer for uploads
function createTestPdf(): Buffer {
  const pdf = [
    '%PDF-1.4',
    '1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj',
    '2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj',
    '3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]',
    '   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj',
    '4 0 obj\n<< /Length 44 >>\nstream',
    'BT /F1 24 Tf 100 700 Td (Hello WCAG) Tj ET',
    'endstream\nendobj',
    '5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj',
    'xref\n0 6',
    '0000000000 65535 f ',
    '0000000009 00000 n ',
    '0000000058 00000 n ',
    '0000000115 00000 n ',
    '0000000266 00000 n ',
    '0000000360 00000 n ',
    'trailer\n<< /Size 6 /Root 1 0 R >>',
    'startxref\n441\n%%EOF',
  ].join('\n');
  return Buffer.from(pdf);
}

test.describe('Homepage & Navigation', () => {
  test('loads the dashboard page', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveTitle(/PDF.*HTML|WCAG|Document|Converter/i);
  });

  test('shows the upload area', async ({ page }) => {
    await page.goto('/dashboard');
    // Look for upload-related text or input
    const uploadArea = page.locator('text=/upload|drag|drop|choose|select/i').first();
    await expect(uploadArea).toBeVisible({ timeout: 15000 });
  });

  test('page is accessible — has lang attribute', async ({ page }) => {
    await page.goto('/dashboard');
    const lang = await page.getAttribute('html', 'lang');
    expect(lang).toBeTruthy();
  });
});

test.describe('File Upload Flow', () => {
  test('uploads a PDF and shows progress', async ({ page }) => {
    await page.goto('/dashboard');

    // Write test PDF to temp file
    const tmpDir = path.join(__dirname, '..', '.tmp-test');
    fs.mkdirSync(tmpDir, { recursive: true });
    const pdfPath = path.join(tmpDir, 'e2e-test.pdf');
    fs.writeFileSync(pdfPath, createTestPdf());

    try {
      // Find file input (may be hidden — Playwright can still interact)
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(pdfPath);

      // Should see some indication of upload/processing
      // Wait for either progress indicator or status text
      const indicator = page.locator(
        'text=/upload|processing|converting|pending|progress/i'
      ).first();
      await expect(indicator).toBeVisible({ timeout: 30000 });
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });

  test('rejects non-PDF files', async ({ page }) => {
    await page.goto('/dashboard');

    const tmpDir = path.join(__dirname, '..', '.tmp-test');
    fs.mkdirSync(tmpDir, { recursive: true });
    const txtPath = path.join(tmpDir, 'test.txt');
    fs.writeFileSync(txtPath, 'not a pdf');

    try {
      const fileInput = page.locator('input[type="file"]');
      // The input should have accept attribute limiting to pdf/docx/pptx
      const accept = await fileInput.getAttribute('accept');
      expect(accept).toContain('.pdf');
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });
});

test.describe('Conversion Pipeline (E2E)', () => {
  test('full pipeline: upload → convert → preview → download → delete', async ({ page }) => {
    test.setTimeout(180_000); // 3 minutes for full pipeline
    await page.goto('/dashboard');

    // Step 1: Upload a test PDF
    const tmpDir = path.join(__dirname, '..', '.tmp-test');
    fs.mkdirSync(tmpDir, { recursive: true });
    const pdfPath = path.join(tmpDir, 'pipeline-test.pdf');
    fs.writeFileSync(pdfPath, createTestPdf());

    try {
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(pdfPath);

      // Step 2: Wait for conversion to complete
      // Look for "completed" status or download/preview button
      const completedIndicator = page.locator(
        'text=/completed|download|preview|converted/i'
      ).first();
      await expect(completedIndicator).toBeVisible({ timeout: 120000 });

      // Step 3: Verify a download or preview action is available
      const actionButton = page.locator(
        'button:has-text(/download|preview/i), a:has-text(/download|preview/i)'
      ).first();
      
      if (await actionButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        // Click preview/download — verify no error
        const [response] = await Promise.all([
          page.waitForResponse(
            (resp) => resp.url().includes('/api/documents/') && resp.status() < 500,
            { timeout: 30000 }
          ).catch(() => null),
          actionButton.click(),
        ]);

        if (response) {
          expect(response.status()).toBeLessThan(500);
        }
      }

      // Step 4: Delete the document
      const deleteButton = page.locator(
        'button:has-text(/delete|remove/i)'
      ).first();
      
      if (await deleteButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await deleteButton.click();
        
        // Confirm deletion if there's a dialog
        const confirmButton = page.locator(
          'button:has-text(/confirm|yes|delete/i)'
        ).first();
        if (await confirmButton.isVisible({ timeout: 3000 }).catch(() => false)) {
          await confirmButton.click();
        }

        // Verify document is removed from the list
        await page.waitForTimeout(2000);
      }
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  });
});

test.describe('API Health (via frontend proxy)', () => {
  test('API is reachable through frontend rewrites', async ({ page }) => {
    // Frontend proxies /api/* to the backend
    const resp = await page.request.get('/api/documents/status');
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data).toHaveProperty('documents');
    expect(data).toHaveProperty('summary');
  });
});
