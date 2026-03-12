import type { Metadata } from 'next';
import { Outfit, Literata, JetBrains_Mono } from 'next/font/google';
import '@/styles/globals.css';
import GovBanner from '@/components/GovBanner';
import NCHeader from '@/components/NCHeader';
import NCFooter from '@/components/NCFooter';

/* --------------------------------------------------------------------------
   Google Fonts — loaded via next/font for optimal performance
   -------------------------------------------------------------------------- */

const outfit = Outfit({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-heading',
  display: 'swap',
});

const literata = Literata({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  style: ['normal', 'italic'],
  variable: '--font-body',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '600'],
  variable: '--font-mono',
  display: 'swap',
});

/* --------------------------------------------------------------------------
   Metadata
   -------------------------------------------------------------------------- */

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

/* --------------------------------------------------------------------------
   Root Layout
   -------------------------------------------------------------------------- */

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      data-theme="dark"
      className={`${outfit.variable} ${literata.variable} ${jetbrainsMono.variable}`}
    >
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
