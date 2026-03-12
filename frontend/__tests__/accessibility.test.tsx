/**
 * WCAG 2.1 AA Accessibility Tests
 * 
 * Comprehensive accessibility audit for all frontend components.
 * Uses jest-axe for automated WCAG testing.
 */

import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import FileUpload from '@/components/FileUpload';
import ProgressTracker from '@/components/ProgressTracker';
import DocumentPreview from '@/components/DocumentPreview';
import DownloadButton from '@/components/DownloadButton';
import GovBanner from '@/components/GovBanner';
import NCHeader from '@/components/NCHeader';
import NCFooter from '@/components/NCFooter';

expect.extend(toHaveNoViolations);

describe('WCAG 2.1 AA Accessibility Audit', () => {
  describe('FileUpload', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(<FileUpload />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('ProgressTracker', () => {
    it('should have no accessibility violations - empty state', async () => {
      const { container } = render(
        <ProgressTracker documents={[]} />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have no accessibility violations - with documents', async () => {
      const { container } = render(
        <ProgressTracker
          documents={[
            {
              document_id: 'doc1',
              name: 'test.pdf',
              status: 'completed',
              upload_timestamp: '2024-01-01T00:00:00Z',
              page_count: 5,
              pages_processed: 5,
              has_review_flags: false,
              review_pages: [],
            },
            {
              document_id: 'doc2',
              name: 'test2.pdf',
              status: 'processing',
              upload_timestamp: '2024-01-01T00:00:00Z',
              page_count: 10,
              pages_processed: 3,
              has_review_flags: false,
              review_pages: [],
            },
            {
              document_id: 'doc3',
              name: 'test3.pdf',
              status: 'failed',
              upload_timestamp: '2024-01-01T00:00:00Z',
              page_count: 0,
              pages_processed: 0,
              has_review_flags: false,
              review_pages: [],
              error_message: 'Upload failed',
            },
          ]}
          onRetry={() => {}}
          onPreview={() => {}}
        />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('DocumentPreview', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(
        <DocumentPreview
          previewUrl="https://example.com/test.html"
          documentName="test.pdf"
          flaggedPages={[1, 3]}
          onClose={() => {}}
        />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have no accessibility violations - no flagged pages', async () => {
      const { container } = render(
        <DocumentPreview
          previewUrl="https://example.com/test.html"
          documentName="test.pdf"
          onClose={() => {}}
        />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('DownloadButton', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(
        <DownloadButton
          documentId="doc1"
          documentName="test.pdf"
          format="html"
        />
      );
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('GovBanner', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(<GovBanner />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('NCHeader', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(<NCHeader />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('NCFooter', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(<NCFooter />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });
});
