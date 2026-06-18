export const runtime = 'edge';

const BACKEND_URL = process.env.BACKEND_URL || (
    process.env.VERCEL_ENV === 'preview'
        ? 'https://ai-news-backend-staging.up.railway.app'
        : 'https://ai-news-production-7cfe.up.railway.app'
);

export async function POST(request: Request) {
    const body = await request.text();

    const upstream = await fetch(`${BACKEND_URL}/api/rss/fetch_stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Cookie': request.headers.get('cookie') || '',
        },
        body,
    });

    return new Response(upstream.body, {
        status: upstream.status,
        headers: {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        },
    });
}
