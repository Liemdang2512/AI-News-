'use client';

import { Article } from '@/lib/types';
import { useState, useMemo } from 'react';
import { ExternalLink, Clock, ChevronDown, ChevronUp, CheckCircle2, Copy } from 'lucide-react';

interface ArticleListProps {
    articles: Article[];
    onSelectArticles: (urls: string[]) => void;
}

const MAX_ARTICLES = 20;

export default function ArticleList({ articles, onSelectArticles }: ArticleListProps) {
    const [selectedUrls, setSelectedUrls] = useState<string[]>([]);
    const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
    const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
    const [filterDuplicates, setFilterDuplicates] = useState(true);

    const hasDuplicates = articles.some(a => a.is_master === false);

    // Group articles by category, then by duplicate group
    const groupedArticles = useMemo(() => {
        const groups: Record<string, Article[]> = {};

        // When filterDuplicates is ON: show only master articles; OFF: show all
        const masterArticles = filterDuplicates
            ? articles.filter(article => article.is_master !== false)
            : articles;

        masterArticles.forEach(article => {
            const category = article.category;
            if (!groups[category]) {
                groups[category] = [];
            }
            groups[category].push(article);
        });

        // Initialize all categories as expanded
        const initialExpanded: Record<string, boolean> = {};
        Object.keys(groups).forEach(cat => {
            initialExpanded[cat] = true;
        });
        setExpandedCategories(prev => ({ ...initialExpanded, ...prev }));
        return groups;
    }, [articles, filterDuplicates]);

    const toggleCategory = (category: string) => {
        setExpandedCategories(prev => ({
            ...prev,
            [category]: !prev[category]
        }));
    };

    const toggleGroup = (groupId: string) => {
        setExpandedGroups(prev => ({
            ...prev,
            [groupId]: !prev[groupId]
        }));
    };

    // Get duplicate articles for a group
    const getDuplicateArticles = (groupId: string) => {
        return articles.filter(article =>
            article.group_id === groupId && article.is_master === false
        );
    };

    const handleToggle = (url: string) => {
        setSelectedUrls((prev) => {
            if (prev.includes(url)) return prev.filter((u) => u !== url);
            if (prev.length >= MAX_ARTICLES) return prev;
            return [...prev, url];
        });
    };

    const visibleArticles = filterDuplicates
        ? articles.filter(a => a.is_master !== false)
        : articles;

    const handleSelectAll = () => {
        if (selectedUrls.length === visibleArticles.length || selectedUrls.length >= MAX_ARTICLES) {
            setSelectedUrls([]);
        } else {
            setSelectedUrls(visibleArticles.slice(0, MAX_ARTICLES).map((a) => a.url));
        }
    };

    const handleSummarize = () => {
        if (selectedUrls.length > 0) {
            onSelectArticles(selectedUrls);
        }
    };

    if (articles.length === 0) {
        return (
            <div className="bg-white rounded-2xl shadow-xl p-12 text-center border border-gray-100">
                <p className="text-gray-500 text-lg">Không tìm thấy bài viết nào trong khoảng thời gian này.</p>
            </div>
        );
    }

    // Get source badge color
    const getSourceColor = (source: string) => {
        const colors: Record<string, string> = {
            'LÃO ĐỘNG': 'bg-blue-100 text-blue-700 border-blue-200',
            'VTV NEWS': 'bg-red-100 text-red-700 border-red-200',
            'VNS EXPRESS': 'bg-purple-100 text-purple-700 border-purple-200',
            'CAFEF': 'bg-orange-100 text-orange-700 border-orange-200',
            'TUỔI TRẺ': 'bg-green-100 text-green-700 border-green-200',
            'DÂN TRÍ': 'bg-indigo-100 text-indigo-700 border-indigo-200',
        };
        return colors[source] || 'bg-slate-100 text-slate-700 border-slate-200';
    };

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                <h2 className="text-lg font-bold text-slate-800">
                    Danh sách bài viết
                </h2>
                {hasDuplicates && (
                    <label className={`flex items-center gap-2 cursor-pointer select-none px-3 py-2 rounded-lg border transition-all ${
                        filterDuplicates
                            ? 'bg-amber-50 border-amber-300 text-amber-800'
                            : 'bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300'
                    }`}>
                        <input
                            type="checkbox"
                            checked={filterDuplicates}
                            onChange={(e) => {
                                setFilterDuplicates(e.target.checked);
                                setSelectedUrls([]);
                            }}
                            className="w-4 h-4 text-amber-500 border-slate-300 rounded focus:ring-amber-400"
                        />
                        <span className="text-sm font-semibold">
                            Lọc trùng lặp
                        </span>
                        <span className="text-xs font-normal opacity-70">
                            ({articles.length} bài trước lọc)
                        </span>
                    </label>
                )}
            </div>

            {/* Selection Actions */}
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm text-slate-600">
                        Đã chọn <span className={`font-semibold ${selectedUrls.length >= MAX_ARTICLES ? 'text-amber-600' : 'text-blue-600'}`}>{selectedUrls.length}</span>
                        {' / '}<span className="font-semibold text-slate-700">{visibleArticles.length}</span> bài viết
                        <span className="ml-2 text-xs text-slate-400">(tối đa {MAX_ARTICLES} bài/lần)</span>
                    </p>
                    {selectedUrls.length >= MAX_ARTICLES && (
                        <p className="text-xs text-amber-600 mt-1">Đã đạt giới hạn {MAX_ARTICLES} bài. Bỏ chọn bài khác để thêm.</p>
                    )}
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleSelectAll}
                        className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
                    >
                        {selectedUrls.length === visibleArticles.length && visibleArticles.length > 0 ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
                    </button>
                    <button
                        onClick={handleSummarize}
                        disabled={selectedUrls.length === 0}
                        className="px-6 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        Tóm tắt bài viết đã chọn
                    </button>
                </div>
            </div>

            {/* Articles grouped by category */}
            <div className="space-y-6">
                {Object.entries(groupedArticles).map(([category, categoryArticles]) => (
                    <div key={category} className="space-y-3">
                        {/* Category Header - Clickable */}
                        <button
                            onClick={() => toggleCategory(category)}
                            className="w-full flex items-center justify-between gap-2 p-3 bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
                        >
                            <div className="flex items-center gap-2">
                                <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center">
                                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                                    </svg>
                                </div>
                                <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wide">
                                    Chuyên mục: {category}
                                </h3>
                                <span className="text-xs text-slate-500 font-medium">
                                    ({categoryArticles.length} bài)
                                </span>
                            </div>
                            {expandedCategories[category] ? (
                                <ChevronUp className="w-5 h-5 text-slate-600" />
                            ) : (
                                <ChevronDown className="w-5 h-5 text-slate-600" />
                            )}
                        </button>

                        {/* Articles in this category - Collapsible */}
                        {expandedCategories[category] && (
                            <div className="space-y-3 animate-slide-up">
                                {categoryArticles.map((article, index) => (
                                    <div
                                        key={index}
                                        className={`flex items-start gap-4 p-4 border rounded-xl transition-all cursor-pointer hover:shadow-md ${selectedUrls.includes(article.url)
                                            ? 'border-blue-500 bg-blue-50'
                                            : 'border-slate-200 bg-white hover:border-blue-300'
                                            }`}
                                        onClick={() => handleToggle(article.url)}
                                    >
                                        {/* Checkbox */}
                                        <input
                                            type="checkbox"
                                            checked={selectedUrls.includes(article.url)}
                                            onChange={() => handleToggle(article.url)}
                                            className="mt-1 w-5 h-5 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                                            onClick={(e) => e.stopPropagation()}
                                        />

                                        {/* Content */}
                                        <div className="flex-1 min-w-0 space-y-2">
                                            {/* Source, Time, and Badges */}
                                            <div className="flex items-center gap-2 text-xs flex-wrap">
                                                <span className={`px-2 py-1 rounded border font-semibold ${getSourceColor(article.source)}`}>
                                                    {article.source}
                                                </span>
                                                <span className="flex items-center gap-1 text-slate-500">
                                                    <Clock className="w-3 h-3" />
                                                    {article.published_at}
                                                </span>

                                                {/* Nhan Dan Verification Badge */}
                                                {article.official_source_link && (
                                                    <a
                                                        href={article.official_source_link}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        onClick={(e) => e.stopPropagation()}
                                                        className="flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 border border-green-200 rounded font-semibold hover:bg-green-100 transition-colors"
                                                        title="Đã có trên Báo Nhân Dân"
                                                    >
                                                        <CheckCircle2 className="w-3 h-3" />
                                                        Báo Nhân Dân
                                                    </a>
                                                )}

                                                {/* Duplicate Count Badge */}
                                                {article.duplicate_count && article.duplicate_count > 0 && (
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            toggleGroup(article.group_id || '');
                                                        }}
                                                        className="flex items-center gap-1 px-2 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded font-semibold hover:bg-amber-100 transition-colors"
                                                    >
                                                        <Copy className="w-3 h-3" />
                                                        +{article.duplicate_count} nguồn khác
                                                    </button>
                                                )}
                                            </div>

                                            {/* Title */}
                                            <h4 className="font-semibold text-slate-900 leading-tight line-clamp-2">
                                                {article.title}
                                            </h4>

                                            {/* Event Summary (if available) */}
                                            {article.event_summary && article.event_summary !== article.title && (
                                                <p className="text-xs text-blue-600 italic">
                                                    📌 {article.event_summary}
                                                </p>
                                            )}

                                            {/* Description */}
                                            <p className="text-sm text-slate-600 line-clamp-2">
                                                {article.description.replace(/<[^>]*>/g, '')}
                                            </p>

                                            {/* Link */}
                                            <a
                                                href={article.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
                                                onClick={(e) => e.stopPropagation()}
                                            >
                                                Xem bài viết
                                                <ExternalLink className="w-3 h-3" />
                                            </a>

                                            {/* Duplicate Articles (Expandable) */}
                                            {article.group_id && expandedGroups[article.group_id] && (
                                                <div className="mt-3 pt-3 border-t border-slate-200 space-y-2">
                                                    <p className="text-xs font-semibold text-slate-600 uppercase">
                                                        Các nguồn khác cùng tin:
                                                    </p>
                                                    {getDuplicateArticles(article.group_id).map((dupArticle, dupIdx) => (
                                                        <div key={dupIdx} className="flex items-center gap-2 text-xs">
                                                            {/* Checkbox for duplicate article */}
                                                            <input
                                                                type="checkbox"
                                                                checked={selectedUrls.includes(dupArticle.url)}
                                                                onChange={() => handleToggle(dupArticle.url)}
                                                                className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                                                                onClick={(e) => e.stopPropagation()}
                                                            />
                                                            <span className={`px-2 py-0.5 rounded border text-xs ${getSourceColor(dupArticle.source)}`}>
                                                                {dupArticle.source}
                                                            </span>
                                                            <a
                                                                href={dupArticle.url}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="text-blue-600 hover:text-blue-800 truncate flex-1"
                                                                onClick={(e) => e.stopPropagation()}
                                                            >
                                                                {dupArticle.title}
                                                            </a>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>

                                        {/* Thumbnail */}
                                        {article.thumbnail && (
                                            <div className="flex-shrink-0 w-24 h-24 rounded-lg overflow-hidden bg-slate-100">
                                                <img
                                                    src={article.thumbnail}
                                                    alt={article.title}
                                                    className="w-full h-full object-cover"
                                                    referrerPolicy="no-referrer"
                                                    onError={(e) => {
                                                        e.currentTarget.style.display = 'none';
                                                    }}
                                                />
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
