'use client';

import { useState, useEffect } from 'react';
import { Newspaper, Sparkles, Settings, X, Save } from 'lucide-react';
import InputForm from '@/components/InputForm';
import ArticleList from '@/components/ArticleList';
import SummaryReport from '@/components/SummaryReport';
import LoadingSpinner from '@/components/LoadingSpinner';
import CategoryStats from '@/components/CategoryStats';
import { api } from '@/lib/api';
import { Article } from '@/lib/types';

export default function Home() {
    const [loading, setLoading] = useState(false);
    const [articles, setArticles] = useState<Article[]>([]);
    const [summary, setSummary] = useState('');
    const [error, setError] = useState('');
    const [currentStep, setCurrentStep] = useState('');
    const [searchMetadata, setSearchMetadata] = useState<{
        date: string;
        timeRange: string;
        totalArticles: number;
    } | null>(null);

    // API Key Settings
    const [showSettings, setShowSettings] = useState(false);
    const [apiKey, setApiKey] = useState('');

    useEffect(() => {
        const storedKey = localStorage.getItem('gemini_api_key');
        if (storedKey) setApiKey(storedKey);
    }, []);

    const handleSaveApiKey = () => {
        localStorage.setItem('gemini_api_key', apiKey);
        setShowSettings(false);
    };

    const handleSearch = async (data: { newspapers: string; date: string; timeRange: string }) => {
        setLoading(true);
        setError('');
        setArticles([]);
        setSummary('');
        setSearchMetadata(null);

        try {
            // Step 1: Match RSS feeds
            setCurrentStep('Đang khớp nguồn RSS...');
            const matchResponse = await api.matchRSS(data.newspapers);

            if (matchResponse.rss_feeds.length === 0) {
                setError('Không tìm thấy nguồn RSS phù hợp. Vui lòng kiểm tra tên các đầu báo.');
                setLoading(false);
                return;
            }

            // Step 2: Fetch and filter articles
            setCurrentStep('Đang tải và lọc bài viết...');
            const fetchResponse = await api.fetchArticles(
                matchResponse.rss_feeds,
                data.date,
                data.timeRange
            );

            setArticles(fetchResponse.articles);
            setSearchMetadata({
                date: data.date,
                timeRange: data.timeRange,
                totalArticles: fetchResponse.articles.length
            });
            setLoading(false);
            setCurrentStep('');

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Đã xảy ra lỗi không xác định');
            setLoading(false);
            setCurrentStep('');
        }
    };

    const handleSummarize = async (urls: string[]) => {
        setLoading(true);
        setError('');
        setSummary('');

        try {
            setCurrentStep('Đang tóm tắt bài viết...');
            // Pass the API key to the summarize function
            const response = await api.summarizeArticles(urls, apiKey);
            setSummary(response.summary);
            setLoading(false);
            setCurrentStep('');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Đã xảy ra lỗi khi tóm tắt');
            setLoading(false);
            setCurrentStep('');
        }
    };

    const handleBackFromSummary = () => {
        setSummary(''); // Clear summary to return to article list
    };

    // If we have a summary, show the full-page report
    if (summary && !loading) {
        return (
            <SummaryReport
                summary={summary}
                metadata={searchMetadata || undefined}
                onBack={handleBackFromSummary}
            />
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col relative">
            {/* Settings Modal */}
            {showSettings && (
                <div className="fixed inset-0 bg-black/50 z-[60] flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl p-6 animate-scale-up">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                                <Settings className="w-5 h-5 text-slate-500" />
                                Cài đặt API Key
                            </h3>
                            <button onClick={() => setShowSettings(false)} className="text-slate-400 hover:text-slate-600 transition-colors">
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="space-y-4">
                            <p className="text-sm text-slate-600">
                                Nhập Google Gemini API Key của bạn để sử dụng các tính năng cao cấp mà không bị giới hạn.
                                <br />
                                <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                    Lấy API Key tại đây &rarr;
                                </a>
                            </p>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">API Key</label>
                                <input
                                    type="password"
                                    value={apiKey}
                                    onChange={(e) => setApiKey(e.target.value)}
                                    placeholder="AIzaSy..."
                                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                />
                            </div>
                            <div className="flex justify-end pt-2">
                                <button
                                    onClick={handleSaveApiKey}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 font-medium"
                                >
                                    <Save className="w-4 h-4" />
                                    Lưu cài đặt
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Header */}
            <header className="bg-[#1e3a5f] text-white shadow-md sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 lg:px-12 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-white rounded flex items-center justify-center">
                            <Newspaper className="w-5 h-5 text-[#1e3a5f]" />
                        </div>
                        <h1 className="text-white text-lg font-bold">AI News Assistant</h1>
                    </div>
                    <button
                        onClick={() => setShowSettings(true)}
                        className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-all text-white/90 hover:text-white"
                        title="Cài đặt API"
                    >
                        <Settings className="w-5 h-5" />
                    </button>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 w-full flex-1">
                {/* Intelligence Search Section */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                    <h2 className="text-2xl font-bold text-slate-800 mb-2">Intelligence Search</h2>
                    <p className="text-slate-500 text-sm mb-6">
                        Tìm kiếm và phân tích tin tức từ các nguồn báo chính thống
                    </p>

                    {/* Input Form */}
                    <InputForm onSubmit={handleSearch} loading={loading} />
                </div>

                {/* Error Message */}
                {error && (
                    <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6 animate-slide-up">
                        <p className="text-red-800 font-medium">{error}</p>
                    </div>
                )}

                {/* Loading State */}
                {loading && (
                    <div className="animate-slide-up">
                        <LoadingSpinner text={currentStep} />
                    </div>
                )}

                {/* Category Stats */}
                {!loading && articles.length > 0 && (
                    <div className="animate-slide-up">
                        <CategoryStats articles={articles} />
                    </div>
                )}

                {/* Articles List */}
                {!loading && articles.length > 0 && (
                    <div className="animate-slide-up">
                        <ArticleList articles={articles} onSelectArticles={handleSummarize} />
                    </div>
                )}

                {/* Empty State */}
                {!loading && !error && articles.length === 0 && !summary && (
                    <div className="flex-1 flex flex-col items-center justify-center py-12 md:py-24">
                        <div className="relative mb-8">
                            <div className="absolute inset-0 bg-vibrant-blue/10 rounded-full blur-2xl transform scale-150"></div>
                            <div className="relative z-10 w-32 h-32 bg-gradient-to-br from-white to-slate-50 rounded-full shadow-soft border border-slate-100 flex items-center justify-center">
                                <div className="absolute inset-2 border border-slate-100 rounded-full"></div>
                                <Sparkles className="w-16 h-16 text-corporate-navy" />
                            </div>
                        </div>
                        <div className="text-center max-w-2xl px-4 animate-fade-in-up">
                            <h3 className="text-corporate-blue-text text-2xl md:text-3xl font-bold tracking-tight mb-4">
                                Khởi tạo bản tin của bạn
                            </h3>
                            <p className="text-slate-500 text-base md:text-lg leading-relaxed font-light">
                                Hãy chọn nguồn tin, thời gian và từ khóa phía trên để bắt đầu tổng hợp thông tin thông minh.
                            </p>
                        </div>
                    </div>
                )}
            </main>

            {/* Footer */}
            <footer className="bg-white border-t border-slate-200 py-8 mt-auto">
                <div className="max-w-7xl mx-auto px-6 lg:px-12 flex flex-col md:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-2 text-slate-400">
                        <Newspaper className="w-5 h-5" />
                        <span className="text-sm font-medium">© 2024 AI News Assistant. All rights reserved.</span>
                    </div>
                    <div className="flex gap-6">
                        <span className="text-slate-500 text-sm">Powered by Google Gemini AI</span>
                    </div>
                </div>
            </footer>
        </div>
    );
}
