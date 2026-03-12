/**
 * DocumentPreview.test.tsx — Unit tests for the DocumentPreview component.
 *
 * Tests cover:
 * - iframe rendering with the correct URL and sandbox attributes
 * - Confidence warning display for flagged pages
 * - Loading state (skeleton + spinner)
 * - Error state when preview fails to load
 * - Retry functionality
 * - Accessibility: iframe title, aria-live announcements, close button
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import DocumentPreview from '@/components/DocumentPreview';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const DEFAULT_PROPS = {
  previewUrl: 'https://storage.blob.core.windows.net/documents/test-doc.html?sig=abc',
  documentName: 'Annual Report 2024.pdf',
};

function renderPreview(overrides: Partial<React.ComponentProps<typeof DocumentPreview>> = {}) {
  return render(<DocumentPreview {...DEFAULT_PROPS} {...overrides} />);
}

/**
 * Simulate an iframe error by dispatching a native DOM error event.
 * React's synthetic event system doesn't reliably propagate non-bubbling
 * events like 'error' on iframes in jsdom, so we use native dispatch
 * which our component handles via addEventListener.
 */
function simulateIframeError(iframe: HTMLElement) {
  act(() => {
    const event = new Event('error');
    iframe.dispatchEvent(event);
  });
}

/**
 * Simulate an iframe load by firing the load event inside act()
 * and then flushing any pending state updates.
 */
function simulateIframeLoad(iframe: HTMLElement) {
  act(() => {
    fireEvent.load(iframe);
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('DocumentPreview', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  // -----------------------------------------------------------------------
  // iframe rendering
  // -----------------------------------------------------------------------

  describe('iframe rendering', () => {
    it('renders an iframe with the correct src URL', () => {
      renderPreview();

      const iframe = screen.getByTestId('preview-iframe');
      expect(iframe).toBeInTheDocument();
      expect(iframe).toHaveAttribute('src', DEFAULT_PROPS.previewUrl);
    });

    it('applies sandbox attribute for security', () => {
      renderPreview();

      const iframe = screen.getByTestId('preview-iframe');
      expect(iframe).toHaveAttribute('sandbox', 'allow-same-origin');
    });

    it('sets a descriptive title on the iframe for screen readers', () => {
      renderPreview();

      const iframe = screen.getByTestId('preview-iframe');
      expect(iframe).toHaveAttribute(
        'title',
        `Preview of converted document: ${DEFAULT_PROPS.documentName}`
      );
    });

    it('shows the iframe when loaded successfully', () => {
      renderPreview();

      const iframe = screen.getByTestId('preview-iframe');
      simulateIframeLoad(iframe);

      // Should not have the hidden class
      expect(iframe.className).not.toContain('document-preview__iframe--hidden');
    });
  });

  // -----------------------------------------------------------------------
  // Loading state
  // -----------------------------------------------------------------------

  describe('loading state', () => {
    it('shows loading indicator before iframe loads', () => {
      renderPreview();

      expect(screen.getByTestId('preview-loading')).toBeInTheDocument();
      expect(screen.getByText('Loading preview…')).toBeInTheDocument();
    });

    it('displays a spinner with role="status"', () => {
      renderPreview();

      const loadingContainer = screen.getByTestId('preview-loading');
      expect(loadingContainer).toHaveAttribute('role', 'status');
    });

    it('hides loading state after iframe loads', () => {
      renderPreview();

      const iframe = screen.getByTestId('preview-iframe');
      simulateIframeLoad(iframe);

      expect(screen.queryByTestId('preview-loading')).not.toBeInTheDocument();
    });

    it('announces loading state to screen readers', () => {
      renderPreview();

      // Check the aria-live region for announcement
      const liveRegion = screen.getByText(
        `Loading preview of ${DEFAULT_PROPS.documentName}`
      );
      expect(liveRegion).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // Error state
  // -----------------------------------------------------------------------

  describe('error state', () => {
    it('shows error state when iframe fails to load', () => {
      renderPreview();

      const iframe = screen.getByTestId('preview-iframe');
      simulateIframeError(iframe);

      expect(screen.getByTestId('preview-error')).toBeInTheDocument();
      expect(screen.getByText('Unable to load preview')).toBeInTheDocument();
    });

    it('shows error state when loading times out', () => {
      renderPreview();

      // Advance past the 30-second timeout
      act(() => {
        jest.advanceTimersByTime(31000);
      });

      expect(screen.getByTestId('preview-error')).toBeInTheDocument();
    });

    it('provides a retry button in error state', () => {
      renderPreview();

      const iframe = screen.getByTestId('preview-iframe');
      simulateIframeError(iframe);

      const retryButton = screen.getByTestId('preview-retry-btn');
      expect(retryButton).toBeInTheDocument();
      expect(retryButton).toHaveAccessibleName(
        `Retry loading preview of ${DEFAULT_PROPS.documentName}`
      );
    });

    it('retries loading when retry button is clicked', () => {
      renderPreview();

      const iframe = screen.getByTestId('preview-iframe');
      simulateIframeError(iframe);

      const retryButton = screen.getByTestId('preview-retry-btn');
      act(() => {
        fireEvent.click(retryButton);
      });

      // Should show loading state again
      expect(screen.getByTestId('preview-loading')).toBeInTheDocument();
    });

    it('announces error state to screen readers', () => {
      renderPreview();

      const iframe = screen.getByTestId('preview-iframe');
      simulateIframeError(iframe);

      expect(
        screen.getByText('Preview failed to load. Please try again.')
      ).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // Confidence warning for flagged pages
  // -----------------------------------------------------------------------

  describe('confidence warning', () => {
    it('displays a warning banner when pages are flagged', () => {
      renderPreview({ flaggedPages: [3, 7, 12] });

      const warning = screen.getByTestId('confidence-warning');
      expect(warning).toBeInTheDocument();
      expect(warning).toHaveAttribute('role', 'alert');
    });

    it('lists the flagged page numbers', () => {
      renderPreview({ flaggedPages: [3, 7, 12] });

      expect(screen.getByText(/3, 7, 12/)).toBeInTheDocument();
    });

    it('uses correct plural for multiple flagged pages', () => {
      renderPreview({ flaggedPages: [3, 7] });

      expect(screen.getByText(/2 pages flagged/)).toBeInTheDocument();
    });

    it('uses correct singular for one flagged page', () => {
      renderPreview({ flaggedPages: [5] });

      expect(screen.getByText(/1 page flagged/)).toBeInTheDocument();
    });

    it('does not display warning when no pages are flagged', () => {
      renderPreview({ flaggedPages: [] });

      expect(screen.queryByTestId('confidence-warning')).not.toBeInTheDocument();
    });

    it('does not display warning when flaggedPages prop is omitted', () => {
      renderPreview();

      expect(screen.queryByTestId('confidence-warning')).not.toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // Close button
  // -----------------------------------------------------------------------

  describe('close button', () => {
    it('renders a close button when onClose is provided', () => {
      const onClose = jest.fn();
      renderPreview({ onClose });

      const closeBtn = screen.getByTestId('preview-close-btn');
      expect(closeBtn).toBeInTheDocument();
      expect(closeBtn).toHaveAccessibleName(
        `Close preview of ${DEFAULT_PROPS.documentName}`
      );
    });

    it('calls onClose when close button is clicked', () => {
      const onClose = jest.fn();
      renderPreview({ onClose });

      act(() => {
        fireEvent.click(screen.getByTestId('preview-close-btn'));
      });
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('does not render close button when onClose is not provided', () => {
      renderPreview();

      expect(screen.queryByTestId('preview-close-btn')).not.toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // Accessibility
  // -----------------------------------------------------------------------

  describe('accessibility', () => {
    it('has role="region" with proper aria-label on the container', () => {
      renderPreview();

      const region = screen.getByTestId('document-preview');
      expect(region).toHaveAttribute('role', 'region');
      expect(region).toHaveAttribute(
        'aria-label',
        `Preview of ${DEFAULT_PROPS.documentName}`
      );
    });

    it('renders document name in the header', () => {
      renderPreview();

      expect(screen.getByText(DEFAULT_PROPS.documentName)).toBeInTheDocument();
    });

    it('iframe is keyboard-focusable', () => {
      renderPreview();

      const iframe = screen.getByTestId('preview-iframe');
      expect(iframe).toHaveAttribute('tabIndex', '0');
    });
  });
});
