'use client';

import { Article } from '@/lib/types';
import { useMemo } from 'react';

interface CategoryStatsProps {
    articles: Article[];
}

export default function CategoryStats({ articles }: CategoryStatsProps) {
    const categoryStats = useMemo(() => {
        const stats: Record<string, number> = {};
        articles.forEach(article => {
            const category = article.category;
            stats[category] = (stats[category] || 0) + 1;
        });
        return stats;
    }, [articles]);

    const categories = Object.entries(categoryStats);

    if (categories.length === 0) {
        return null;
    }

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
                    <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                </div>
                <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                    Thống kê phân loại
                </h3>
            </div>
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
