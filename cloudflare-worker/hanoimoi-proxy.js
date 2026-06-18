// Cloudflare Worker — proxy hanoimoi.vn and vov.vn HTML pages
// Free tier: 100,000 requests/day
//
// Handles:
// - vov.vn: nginx CDN với cookie-based session redirect (302 + Set-Cookie → same URL)
// - hanoimoi.vn: Cloudflare-protected site (returns CF challenge, bypass attempted)

const ALLOWED_HOSTS = ['hanoimoi.vn', 'vov.vn'];

const BROWSER_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
  'Accept-Encoding': 'gzip, deflate, br',
  'Connection': 'keep-alive',
  'Upgrade-Insecure-Requests': '1',
};

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

    try {
      // Cookie jar: accumulate Set-Cookie headers across all redirect hops
      const cookieJar = {};

      function parseCookies(setCookieHeader) {
        if (!setCookieHeader) return;
        // Multiple cookies can appear as comma-separated values, each may have commas in Expires
        // Split by semicolon-terminated pairs carefully
        setCookieHeader.split(/,(?=[^;]+=)/).forEach(part => {
          const kv = part.split(';')[0].trim();
          const eqIdx = kv.indexOf('=');
          if (eqIdx > 0) {
            cookieJar[kv.slice(0, eqIdx).trim()] = kv.slice(eqIdx + 1).trim();
          }
        });
      }

      function cookieString() {
        return Object.entries(cookieJar).map(([k, v]) => `${k}=${v}`).join('; ');
      }

      async function fetchWithCookies(url) {
        const headers = { ...BROWSER_HEADERS };
        const jar = cookieString();
        if (jar) headers['Cookie'] = jar;
        const resp = await fetch(url, { headers, redirect: 'manual', cf: { cacheTtl: 0 } });
        parseCookies(resp.headers.get('set-cookie'));
        return resp;
      }

      // Step 1: initial fetch
      let response = await fetchWithCookies(target);

      // Step 2: follow HTTP redirect (302/301) max 3 times
      let redirectCount = 0;
      while (response.status >= 300 && response.status < 400 && redirectCount < 3) {
        const location = response.headers.get('location');
        if (!location) break;
        const nextUrl = new URL(location, target).href;
        const nextHost = new URL(nextUrl).hostname;
        if (!ALLOWED_HOSTS.some(h => nextHost.endsWith(h))) break;
        response = await fetchWithCookies(nextUrl);
        redirectCount++;
      }

      let content = await response.text();
      const contentType = response.headers.get('Content-Type') || 'text/html; charset=utf-8';

      // Step 3: follow JS redirect (vov.vn window.location.href với jskey) — same cookie jar
      if (response.status === 200 && content.length < 5000) {
        const jsRedirect = content.match(/window\.location\.href\s*=\s*["']([^"']+)["']/);
        if (jsRedirect) {
          const jsUrl = new URL(jsRedirect[1], target).href;
          const jsHost = new URL(jsUrl).hostname;
          if (ALLOWED_HOSTS.some(h => jsHost.endsWith(h))) {
            // Follow JS redirect with accumulated cookies, allow HTTP redirects after
            const headers = { ...BROWSER_HEADERS };
            const jar = cookieString();
            if (jar) headers['Cookie'] = jar;
            const jsResponse = await fetch(jsUrl, { headers, cf: { cacheTtl: 300 } });
            content = await jsResponse.text();
          }
        }
      }

      return new Response(content, {
        status: response.status,
        headers: {
          'Content-Type': contentType,
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'public, max-age=300',
          'X-Proxy-Status': `${response.status}`,
        },
      });
    } catch (err) {
      return new Response(`Proxy error: ${err.message}`, { status: 502 });
    }
  },
};
