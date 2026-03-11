import type { Metadata } from 'next';
import '@/styles/globals.css';
import GovBanner from '@/components/GovBanner';
import NCHeader from '@/components/NCHeader';
import NCFooter from '@/components/NCFooter';

export const metadata: Metadata = {
  title: 'NCDIT Document Converter',
  description:
    'Convert PDF, DOCX, and PPTX documents to WCAG 2.1 AA compliant HTML. ' +
    'A service of the North Carolina Department of Information Technology.',
  keywords: [
    'NCDIT',
    'document converter',
    'WCAG',
    'accessibility',
    'PDF to HTML',
    'North Carolina',
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {/* Skip navigation — WCAG 2.1 AA requirement */}
        <a href="#main-content" className="skip-nav">
          Skip to main content
        </a>

        {/* Government trust banner */}
        <GovBanner />

        {/* Site header with NC.gov branding */}
        <NCHeader />

        {/* Main content area */}
        <main id="main-content" tabIndex={-1}>
          {children}
        </main>

        {/* Site footer */}
        <NCFooter />
      </body>
    </html>
  );
}
