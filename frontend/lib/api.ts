// In production (Vercel), we use relative paths routed via vercel.json
// For desktop/Electron usage, we default to a local backend on 127.0.0.1:8000
const getApiBaseUrl = () => {
    // Highest priority: explicit env override
    if (process.env.NEXT_PUBLIC_API_URL && process.env.NEXT_PUBLIC_API_URL.trim() !== '') {
        return process.env.NEXT_PUBLIC_API_URL;
    }

    // If running inside a desktop shell (file:// or custom protocol),
    // default to local backend
    if (typeof window !== 'undefined') {
        const protocol = window.location.protocol;
        if (protocol === 'file:' || protocol === 'app:' || protocol === 'capacitor:') {
            return 'http://127.0.0.1:8000';
        }
    }

    // Fallback: empty string -> use relative paths (Vercel routing)
    return '';
};

export const API_BASE_URL = getApiBaseUrl();

export const api = {
    async matchRSS(newspapers: string) {
        const response = await fetch(`${API_BASE_URL}/api/rss/match`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ newspapers }),
        });

        if (!response.ok) {
            throw new Error('Failed to match RSS feeds');
        }

        return response.json();
    },

    async fetchArticles(rss_urls: string[], date: string, time_range: string) {
        const response = await fetch(`${API_BASE_URL}/api/rss/fetch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rss_urls, date, time_range }),
        });

        if (!response.ok) {
            throw new Error('Failed to fetch articles');
        }

        return response.json();
    },

    async categorizeArticles(articles_text: string, api_key?: string) {
        const headers: Record<string, string> = { 'Content-Type': 'application/json' };
        if (api_key) {
            headers['x-gemini-api-key'] = api_key;
        }

        const response = await fetch(`${API_BASE_URL}/api/articles/categorize`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ articles_text }),
        });

        if (!response.ok) {
            throw new Error('Failed to categorize articles');
        }

        return response.json();
    },

    async summarizeArticles(urls: string[], api_key?: string, articles?: any[]) {
        const headers: Record<string, string> = { 'Content-Type': 'application/json' };
        if (api_key) {
            headers['x-gemini-api-key'] = api_key;
        }

        const response = await fetch(`${API_BASE_URL}/api/articles/summarize`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ urls, articles: articles || [] }),
        });

        if (!response.ok) {
            throw new Error('Failed to summarize articles');
        }

        return response.json();
    },
};
