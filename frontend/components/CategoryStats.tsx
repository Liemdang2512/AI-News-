'use client';

import { Article } from '@/lib/types';
import { useMemo } from 'react';

interface CategoryStatsProps {
    articles: Article[];
}

export default function CategoryStats({ articles }: CategoryStatsProps) {
    const { categoryStats, dedupStats } = useMemo(() => {
        const stats: Record<string, number> = {};
        // Count only master articles (or articles without dedup info) per category
        const masterArticles = articles.filter(a => a.is_master !== false);
        masterArticles.forEach(article => {
            const category = article.category;
            stats[category] = (stats[category] || 0) + 1;
        });

        const totalFetched = articles.length;
        const duplicatesRemoved = articles.filter(a => a.is_master === false).length;
        const uniqueEvents = masterArticles.filter(a => (a.duplicate_count ?? 0) > 0).length;

        return {
            categoryStats: stats,
            dedupStats: { totalFetched, duplicatesRemoved, uniqueEvents },
        };
    }, [articles]);

    const categories = Object.entries(categoryStats);

    if (categories.length === 0) {
        return null;
    }

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-4">
            <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
                    <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                </div>
                <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                    Thống kê phân loại
                </h3>
            </div>

            {/* Dedup stats row */}
            {dedupStats.duplicatesRemoved > 0 && (
                <div className="flex flex-wrap gap-3 pb-3 border-b border-slate-100">
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg">
                        <span className="text-xs text-slate-500">Tổng lấy về:</span>
                        <span className="text-sm font-bold text-slate-700">{dedupStats.totalFetched} bài</span>
                    </div>
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-lg">
                        <svg className="w-3.5 h-3.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        <span className="text-xs text-amber-700">Trùng lặp phát hiện:</span>
                        <span className="text-sm font-bold text-amber-700">{dedupStats.duplicatesRemoved} bài</span>
                    </div>
                </div>
            )}

            <div className="flex flex-wrap gap-3">
                {categories.map(([category, count]) => (
                    <div
                        key={category}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg"
                    >
                        <span className="text-sm font-medium text-blue-900">
                            {category}:
                        </span>
                        <span className="text-sm font-bold text-blue-700">
                            {count} bài
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}
