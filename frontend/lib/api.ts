// In production (Vercel), we use relative paths routed via vercel.json
// In local development, we use http://localhost:8000
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

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

    async categorizeArticles(articles_text: string) {
        const response = await fetch(`${API_BASE_URL}/api/articles/categorize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ articles_text }),
        });

        if (!response.ok) {
            throw new Error('Failed to categorize articles');
        }

        return response.json();
    },

    async summarizeArticles(urls: string[]) {
        const response = await fetch(`${API_BASE_URL}/api/articles/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ urls }),
        });

        if (!response.ok) {
            throw new Error('Failed to summarize articles');
        }

        return response.json();
    },
};
