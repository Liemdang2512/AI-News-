export interface Article {
    url: string;
    title: string;
    category: string;
    published_at: string;
    description: string;
    source: string;  // Newspaper name (e.g., "LÃO ĐỘNG", "VTV NEWS")
    thumbnail?: string;  // Article thumbnail/image URL
}

export interface CategorizedArticles {
    [category: string]: Article[];
}

export interface MatchRSSResponse {
    rss_feeds: string[];
}

export interface FetchArticlesResponse {
    articles: Article[];
}

export interface CategorizeResponse {
    categorized_text: string;
}

export interface SummarizeResponse {
    summary: string;
}
