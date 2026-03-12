/**
 * DownloadButton.test.tsx — Unit tests for the DownloadButton component.
 *
 * Tests cover:
 * - Download button click triggers download API call
 * - Loading state during download preparation
 * - Error handling when download fails
 * - Success state with downloaded filename
 * - Accessibility: aria labels, keyboard activation, aria-busy
 * - Format selection (HTML vs ZIP)
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DownloadButton from '@/components/DownloadButton';

// ---------------------------------------------------------------------------
// Mock the download service
// ---------------------------------------------------------------------------

jest.mock('@/services/downloadService', () => ({
  downloadDocument: jest.fn(),
}));

import { downloadDocument } from '@/services/downloadService';

const mockDownloadDocument = downloadDocument as jest.MockedFunction<
  typeof downloadDocument
>;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const DEFAULT_PROPS = {
  documentId: 'doc-123-abc',
  documentName: 'Annual Report 2024.pdf',
};

function renderButton(overrides: Partial<React.ComponentProps<typeof DownloadButton>> = {}) {
  return render(<DownloadButton {...DEFAULT_PROPS} {...overrides} />);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('DownloadButton', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockDownloadDocument.mockResolvedValue('Annual Report 2024.html');
  });

  // -----------------------------------------------------------------------
  // Default rendering
  // -----------------------------------------------------------------------

  describe('default rendering', () => {
    it('renders a download button', () => {
      renderButton();

      const button = screen.getByTestId('download-button');
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('type', 'button');
    });

    it('displays "Download HTML" text by default', () => {
      renderButton();

      expect(screen.getByText('Download HTML')).toBeInTheDocument();
    });

    it('displays "Download ZIP" text when format is zip', () => {
      renderButton({ format: 'zip' });

      expect(screen.getByText('Download ZIP')).toBeInTheDocument();
    });

    it('button is not disabled in idle state', () => {
      renderButton();

      expect(screen.getByTestId('download-button')).not.toBeDisabled();
    });
  });

  // -----------------------------------------------------------------------
  // Download trigger
  // -----------------------------------------------------------------------

  describe('download trigger', () => {
    it('calls downloadDocument with correct document ID on click', async () => {
      renderButton();

      fireEvent.click(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(mockDownloadDocument).toHaveBeenCalledWith('doc-123-abc', 'html');
      });
    });

    it('calls downloadDocument with zip format when specified', async () => {
      renderButton({ format: 'zip' });

      fireEvent.click(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(mockDownloadDocument).toHaveBeenCalledWith('doc-123-abc', 'zip');
      });
    });

    it('shows success state after successful download', async () => {
      mockDownloadDocument.mockResolvedValue('Annual Report 2024.html');
      renderButton();

      fireEvent.click(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(
          screen.getByText('Downloaded Annual Report 2024.html')
        ).toBeInTheDocument();
      });
    });
  });

  // -----------------------------------------------------------------------
  // Loading state
  // -----------------------------------------------------------------------

  describe('loading state', () => {
    it('shows loading text during download', async () => {
      // Make downloadDocument hang indefinitely
      mockDownloadDocument.mockImplementation(
        () => new Promise(() => {}) // never resolves
      );

      renderButton();
      fireEvent.click(screen.getByTestId('download-button'));

      expect(
        screen.getByText('Preparing download…')
      ).toBeInTheDocument();
    });

    it('disables button during loading', async () => {
      mockDownloadDocument.mockImplementation(
        () => new Promise(() => {})
      );

      renderButton();
      fireEvent.click(screen.getByTestId('download-button'));

      expect(screen.getByTestId('download-button')).toBeDisabled();
    });

    it('sets aria-busy during loading', async () => {
      mockDownloadDocument.mockImplementation(
        () => new Promise(() => {})
      );

      renderButton();
      fireEvent.click(screen.getByTestId('download-button'));

      expect(screen.getByTestId('download-button')).toHaveAttribute(
        'aria-busy',
        'true'
      );
    });

    it('shows a spinner during loading', async () => {
      mockDownloadDocument.mockImplementation(
        () => new Promise(() => {})
      );

      renderButton();
      fireEvent.click(screen.getByTestId('download-button'));

      // Spinner has aria-hidden="true" (decorative within button),
      // so query by class instead of role
      const button = screen.getByTestId('download-button');
      const spinner = button.querySelector('.spinner-border');
      expect(spinner).toBeInTheDocument();
    });
  });

  // -----------------------------------------------------------------------
  // Error handling
  // -----------------------------------------------------------------------

  describe('error handling', () => {
    it('shows error message when download fails', async () => {
      mockDownloadDocument.mockRejectedValue(
        new Error('Document not found: doc-123-abc')
      );

      renderButton();
      fireEvent.click(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(screen.getByTestId('download-error')).toBeInTheDocument();
        expect(
          screen.getByText('Document not found: doc-123-abc')
        ).toBeInTheDocument();
      });
    });

    it('shows retry button text after error', async () => {
      mockDownloadDocument.mockRejectedValue(new Error('Network error'));

      renderButton();
      fireEvent.click(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(screen.getByText('Retry download')).toBeInTheDocument();
      });
    });

    it('renders error message with role="alert"', async () => {
      mockDownloadDocument.mockRejectedValue(new Error('Server error'));

      renderButton();
      fireEvent.click(screen.getByTestId('download-button'));

      await waitFor(() => {
        const errorEl = screen.getByTestId('download-error');
        expect(errorEl).toHaveAttribute('role', 'alert');
      });
    });

    it('allows retry after error', async () => {
      mockDownloadDocument
        .mockRejectedValueOnce(new Error('Temporary failure'))
        .mockResolvedValueOnce('Annual Report 2024.html');

      renderButton();

      // First click — fails
      fireEvent.click(screen.getByTestId('download-button'));
      await waitFor(() => {
        expect(screen.getByText('Retry download')).toBeInTheDocument();
      });

      // Second click — succeeds
      fireEvent.click(screen.getByTestId('download-button'));
      await waitFor(() => {
        expect(
          screen.getByText('Downloaded Annual Report 2024.html')
        ).toBeInTheDocument();
      });
    });

    it('handles non-Error exceptions gracefully', async () => {
      mockDownloadDocument.mockRejectedValue('some string error');

      renderButton();
      fireEvent.click(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(
          screen.getByText('An unexpected error occurred during download.')
        ).toBeInTheDocument();
      });
    });
  });

  // -----------------------------------------------------------------------
  // Accessibility
  // -----------------------------------------------------------------------

  describe('accessibility', () => {
    it('has proper aria-label with document name', () => {
      renderButton();

      const button = screen.getByTestId('download-button');
      expect(button).toHaveAccessibleName(
        `Download ${DEFAULT_PROPS.documentName} as HTML`
      );
    });

    it('updates aria-label for ZIP format', () => {
      renderButton({ format: 'zip' });

      const button = screen.getByTestId('download-button');
      expect(button).toHaveAccessibleName(
        `Download ${DEFAULT_PROPS.documentName} as ZIP`
      );
    });

    it('is activatable via keyboard (Enter)', async () => {
      const user = userEvent.setup();
      renderButton();

      const button = screen.getByTestId('download-button');
      button.focus();
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockDownloadDocument).toHaveBeenCalled();
      });
    });

    it('is activatable via keyboard (Space)', async () => {
      const user = userEvent.setup();
      renderButton();

      const button = screen.getByTestId('download-button');
      button.focus();
      await user.keyboard(' ');

      await waitFor(() => {
        expect(mockDownloadDocument).toHaveBeenCalled();
      });
    });

    it('has aria-busy="false" when idle', () => {
      renderButton();

      const button = screen.getByTestId('download-button');
      expect(button).toHaveAttribute('aria-busy', 'false');
    });

    it('announces download status to screen readers', async () => {
      mockDownloadDocument.mockResolvedValue('Report.html');
      renderButton();

      fireEvent.click(screen.getByTestId('download-button'));

      await waitFor(() => {
        expect(
          screen.getByText('Report.html downloaded successfully.')
        ).toBeInTheDocument();
      });
    });
  });

  // -----------------------------------------------------------------------
  // Variant styling
  // -----------------------------------------------------------------------

  describe('variants', () => {
    it('applies primary button classes by default', () => {
      renderButton();

      const button = screen.getByTestId('download-button');
      expect(button.className).toContain('btn-primary');
    });

    it('applies outline button classes when variant is outline', () => {
      renderButton({ variant: 'outline' });

      const button = screen.getByTestId('download-button');
      expect(button.className).toContain('btn-outline-primary');
    });
  });
});
