import { NextRequest, NextResponse } from 'next/server';

/**
 * Preview Proxy — serves converted HTML through the Next.js server.
 *
 * In Codespaces the browser cannot reach Azurite blob storage at
 * 127.0.0.1:10000.  This route fetches the download URL from the backend
 * and streams the HTML content back to the browser, all server-side.
 */

const BACKEND_URL =
  process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ documentId: string }> }
) {
  const { documentId } = await params;

  if (!documentId) {
    return NextResponse.json(
      { error: 'Document ID is required.' },
      { status: 400 }
    );
  }

  try {
    // 1. Ask the backend for the download URL
    const metaRes = await fetch(
      `${BACKEND_URL}/api/documents/${encodeURIComponent(documentId)}/download`,
      {
        method: 'GET',
        headers: { Accept: 'application/json' },
        cache: 'no-store',
      }
    );

    if (metaRes.status === 404) {
      return NextResponse.json(
        { error: `Document not found: ${documentId}` },
        { status: 404 }
      );
    }

    if (metaRes.status === 409) {
      return NextResponse.json(
        { error: 'Document conversion is not yet complete.' },
        { status: 409 }
      );
    }

    if (!metaRes.ok) {
      const body = await metaRes.text();
      return NextResponse.json(
        { error: `Backend error (HTTP ${metaRes.status}): ${body}` },
        { status: 502 }
      );
    }

    const meta = await metaRes.json();
    const htmlUrl: string | undefined = meta.download_url ?? meta.html_url;

    if (!htmlUrl) {
      return NextResponse.json(
        { error: 'No download URL returned by backend.' },
        { status: 502 }
      );
    }

    // 2. Fetch the actual HTML content server-side
    const htmlRes = await fetch(htmlUrl, { cache: 'no-store' });

    if (!htmlRes.ok) {
      return NextResponse.json(
        { error: `Failed to fetch HTML content (HTTP ${htmlRes.status}).` },
        { status: 502 }
      );
    }

    const html = await htmlRes.text();

    // 3. Return HTML to the browser
    return new NextResponse(html, {
      status: 200,
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-store',
      },
    });
  } catch (err) {
    console.error('[preview proxy]', err);
    return NextResponse.json(
      { error: 'Internal server error while fetching preview.' },
      { status: 500 }
    );
  }
}
