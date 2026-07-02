export const runtime = 'edge';

const BACKEND_URL = 'https://api-news.meetingminutes.ai.vn';

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
