// Cloudflare Worker — proxy hanoimoi.vn and vov.vn HTML pages
// Free tier: 100,000 requests/day

const ALLOWED_HOSTS = ['hanoimoi.vn', 'vov.vn'];

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const target = url.searchParams.get('url');

    if (!target) {
      return new Response('Missing ?url= parameter', { status: 400 });
    }

    let targetUrl;
    try {
      targetUrl = new URL(target);
    } catch {
      return new Response('Invalid URL', { status: 400 });
    }

    const allowed = ALLOWED_HOSTS.some(h => targetUrl.hostname.endsWith(h));
    if (!allowed) {
      return new Response('Host not allowed', { status: 403 });
    }

    const response = await fetch(target, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
      },
      cf: { cacheTtl: 300 },
    });

    const content = await response.text();
    const contentType = response.headers.get('Content-Type') || 'text/html; charset=utf-8';

    return new Response(content, {
      status: response.status,
      headers: {
        'Content-Type': contentType,
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'public, max-age=300',
      },
    });
  },
};
