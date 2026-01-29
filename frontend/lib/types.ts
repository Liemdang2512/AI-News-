export interface Article {
    url: string;
    title: string;
    category: string;
    published_at: string;
    description: string;
    source: string;  // Newspaper name (e.g., "LÃO ĐỘNG", "VTV NEWS")
    thumbnail?: string;  // Article thumbnail/image URL
    // Phase 2: Duplicate Detection
    group_id?: string;  // ID nhóm bài viết trùng lặp
    is_master?: boolean;  // Bài chính trong nhóm
    duplicate_count?: number;  // Số bài trùng lặp
    event_summary?: string;  // Tóm tắt sự kiện
    // Phase 2: Official Source Verification
    official_source_link?: string | null;  // Link Báo Nhân Dân
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
