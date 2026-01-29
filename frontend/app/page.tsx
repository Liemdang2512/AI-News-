'use client';

import { useState, useEffect } from 'react';
import { Newspaper, Sparkles, Key, CheckCircle, Search, FileText, Zap } from 'lucide-react';
import InputForm from '@/components/InputForm';
import ArticleList from '@/components/ArticleList';
import SummaryReport from '@/components/SummaryReport';
import LoadingSpinner from '@/components/LoadingSpinner';
import CategoryStats from '@/components/CategoryStats';
import ProgressTracker from '@/components/ProgressTracker';
import { api, API_BASE_URL } from '@/lib/api';
import { Article } from '@/lib/types';
import SummarizationProgress from '@/components/SummarizationProgress';

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

    // Progress tracking: 0=initial, 1=searched, 2=articles loaded, 3=generating summary, 4=complete
    const [currentProgressStep, setCurrentProgressStep] = useState(0);

    // Process steps for real-time tracking
    const [processSteps, setProcessSteps] = useState([
        { id: 'fetch_rss', label: 'Tải dữ liệu RSS', status: 'pending' as const, message: '' },
        { id: 'dedup', label: 'Phân tích trùng lặp', status: 'pending' as const, message: '' },
        { id: 'verification', label: 'Xác thực Báo Nhân Dân', status: 'pending' as const, message: '' },
    ]);

    // API Key Settings
    const [apiKey, setApiKey] = useState('');
    const [tempApiKey, setTempApiKey] = useState('');
    const [apiKeySaved, setApiKeySaved] = useState(false);
    const [showApiConfig, setShowApiConfig] = useState(true); // Show by default, hide after save

    // Progress for summarization
    const [progressData, setProgressData] = useState({
        completed: 0,
        total: 0,
        currentArticle: '',
        status: 'processing'
    });

    useEffect(() => {
        const storedKey = localStorage.getItem('gemini_api_key');
        if (storedKey) {
            setApiKey(storedKey);
            setTempApiKey(storedKey);
            setApiKeySaved(true);
            setShowApiConfig(false); // Auto-collapse if key exists
        }
    }, []);

    const handleSaveApiKey = () => {
        console.log('=== SAVE API KEY CLICKED ===');
        console.log('Current tempApiKey:', tempApiKey ? '***' + tempApiKey.slice(-4) : 'EMPTY');
        console.log('Current apiKey:', apiKey ? '***' + apiKey.slice(-4) : 'EMPTY');

        if (!tempApiKey || tempApiKey.trim() === '') {
            console.error('API Key is empty!');
            alert('Vui lòng nhập API Key');
            return;
        }

        try {
            const trimmedKey = tempApiKey.trim();
            console.log('Trimmed key:', '***' + trimmedKey.slice(-4));

            // Save to localStorage
            localStorage.setItem('gemini_api_key', trimmedKey);
            console.log('Saved to localStorage');

            // Verify it was saved
            const savedKey = localStorage.getItem('gemini_api_key');
            console.log('Verification - Read from localStorage:', savedKey ? '***' + savedKey.slice(-4) : 'NOT FOUND');

            if (savedKey !== trimmedKey) {
                throw new Error('localStorage verification failed!');
            }

            // Update state
            setApiKey(trimmedKey);
            setApiKeySaved(true);
            console.log('State updated successfully');
            console.log('=== SAVE COMPLETE ===');

            // Collapse the API config section after save
            setTimeout(() => {
                setShowApiConfig(false);
                setApiKeySaved(false);
            }, 1500);
        } catch (error) {
            console.error('Failed to save API key:', error);
            alert('Không thể lưu API Key. Vui lòng thử lại.\nLỗi: ' + error);
        }
    };

    const handleSearch = async (data: { newspapers: string; date: string; timeRange: string }) => {
        setLoading(true);
        setError('');
        setArticles([]);
        setSummary('');
        setSearchMetadata(null);
        setCurrentProgressStep(1); // Step 1: Searching

        // Reset process steps
        setProcessSteps([
            { id: 'fetch_rss', label: 'Tải dữ liệu RSS', status: 'pending', message: '' },
            { id: 'dedup', label: 'Phân tích trùng lặp', status: 'pending', message: '' },
            { id: 'verification', label: 'Xác thực Báo Nhân Dân', status: 'pending', message: '' },
        ]);

        try {
            setCurrentStep('Đang khớp nguồn RSS...');
            const matchResponse = await api.matchRSS(data.newspapers);

            if (matchResponse.rss_feeds.length === 0) {
                setError('Không tìm thấy nguồn RSS phù hợp. Vui lòng kiểm tra tên các đầu báo.');
                setLoading(false);
                setCurrentProgressStep(0);
                return;
            }

            // Use streaming endpoint
            setCurrentStep('Đang xử lý...');
            const response = await fetch(`${API_BASE_URL}/api/rss/fetch_stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(apiKey ? { 'X-Gemini-API-Key': apiKey } : {})
                },
                body: JSON.stringify({
                    rss_urls: matchResponse.rss_feeds,
                    date: data.date,
                    time_range: data.timeRange
                })
            });

            if (!response.ok) {
                throw new Error('Failed to fetch articles');
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) {
                throw new Error('No response body');
            }

            let buffer = ''; // Buffer for incomplete chunks
            let articlesReceived = false;

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    console.log('Stream ended. Articles received:', articlesReceived);
                    break;
                }

                // Decode and add to buffer
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');

                // Keep the last incomplete line in buffer
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonData = line.slice(6);
                        try {
                            const event = JSON.parse(jsonData);

                            console.log('SSE Event:', event.step, event.status, event.message?.substring(0, 50));

                            // Update process steps
                            setProcessSteps(prev => prev.map(step => {
                                if (step.id === event.step) {
                                    return {
                                        ...step,
                                        status: event.status,
                                        message: event.message || ''
                                    };
                                }
                                return step;
                            }));

                            // Handle complete event
                            if (event.step === 'complete' && event.articles) {
                                console.log('✅ Received articles:', event.articles.length);
                                articlesReceived = true;
                                setArticles(event.articles);
                                setSearchMetadata({
                                    date: data.date,
                                    timeRange: data.timeRange,
                                    totalArticles: event.articles.length
                                });
                                setCurrentProgressStep(2);
                                setLoading(false); // Clear loading immediately
                                setCurrentStep('');
                            }

                            // Handle error
                            if (event.step === 'error') {
                                console.error('❌ SSE Error:', event.message);
                                setError(event.message);
                                setLoading(false);
                                setCurrentStep('');
                            }

                        } catch (e) {
                            console.error('Failed to parse SSE event:', e, 'Line:', line.substring(0, 100));
                        }
                    }
                }
            }

            // Ensure loading is cleared even if no complete event
            if (!articlesReceived) {
                console.warn('⚠️ Stream ended without receiving articles');
            }
            setLoading(false);
            setCurrentStep('');

        } catch (err) {
            console.error('Search error:', err);
            setError(err instanceof Error ? err.message : 'Đã xảy ra lỗi không xác định');
            setLoading(false);
            setCurrentStep('');
            setCurrentProgressStep(0);
        }
    };

    const handleSummarize = async (urls: string[]) => {
        setLoading(true);
        setError('');
        setSummary('');
        setCurrentProgressStep(3); // Step 3: Generating summary

        // Reset progress
        setProgressData({
            completed: 0,
            total: urls.length,
            currentArticle: 'Đang khởi tạo...',
            status: 'processing'
        });

        // Determined selected articles
        const selectedArticles = articles.filter(article => urls.includes(article.url));
        // Update metadata with selected count
        if (searchMetadata) {
            setSearchMetadata({ ...searchMetadata, totalArticles: selectedArticles.length });
        }

        try {
            setCurrentStep('Đang tóm tắt bài viết...');

            setCurrentStep('Đang tóm tắt bài viết...');

            // Use streaming fetch instead of WebSocket (better for Vercel)
            const response = await fetch(`${API_BASE_URL}/api/articles/summarize_stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Gemini-API-Key': apiKey || '',
                    'Accept': 'application/x-ndjson'
                },
                body: JSON.stringify({
                    urls,
                    articles: selectedArticles
                })
            });

            // Handle stream
            const reader = response.body?.getReader();
            if (!reader) throw new Error('Không thể đọc stream từ server');

            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');

                // Process all complete lines
                buffer = lines.pop() || ''; // Keep the last incomplete line in buffer

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const data = JSON.parse(line);

                        if (data.type === 'progress') {
                            setProgressData({
                                completed: data.completed,
                                total: data.total,
                                currentArticle: data.current_article,
                                status: data.status
                            });
                        } else if (data.type === 'complete') {
                            setSummary(data.summary);
                            setCurrentProgressStep(4);
                            setLoading(false);
                            setCurrentStep('');
                        } else if (data.type === 'error') {
                            throw new Error(data.message);
                        }
                    } catch (e) {
                        console.error('Error parsing stream line:', line, e);
                    }
                }
            }

            // Final check on buffer
            if (buffer.trim()) {
                try {
                    const data = JSON.parse(buffer);
                    if (data.type === 'complete') {
                        setSummary(data.summary);
                        setCurrentProgressStep(4);
                        setLoading(false);
                    }
                } catch (e) { }
            }

        } catch (err) {
            console.error('Summarize error:', err);
            setError(err instanceof Error ? err.message : 'Đã xảy ra lỗi khi tóm tắt');
            setLoading(false);
            setCurrentStep('');
            setCurrentProgressStep(2);
        }
    };

    const handleBackFromSummary = () => {
        setSummary('');
    };

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
        <div className="min-h-screen bg-slate-50 flex flex-col">
            {/* Header */}
            <header className="bg-navy-darkest text-white shadow-md sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 lg:px-12 py-4 flex items-center justify-center">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-white rounded flex items-center justify-center">
                            <Newspaper className="w-5 h-5 text-navy-darkest" />
                        </div>
                        <h1 className="text-white text-lg font-bold">AI News Assistant</h1>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 w-full flex-1">
                {/* API Configuration Section - Collapsible */}
                <div className="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
                    {!showApiConfig && apiKey ? (
                        // Collapsed view - Show compact banner
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                                    <CheckCircle className="w-5 h-5 text-green-600" />
                                </div>
                                <div>
                                    <h3 className="text-sm font-semibold text-slate-800">Đã cấu hình API Key</h3>
                                    <p className="text-xs text-slate-500">Key: •••{apiKey.slice(-4)}</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setShowApiConfig(true)}
                                className="px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors font-medium"
                            >
                                Chỉnh sửa
                            </button>
                        </div>
                    ) : (
                        // Expanded view - Full configuration
                        <>
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                    <Key className="w-5 h-5 text-blue-600" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold text-slate-800">Cấu hình API</h2>
                                    <p className="text-sm text-slate-500">
                                        Nhập API key của bạn để kích hoạt tính năng tổng hợp tin tức và tóm tắt bằng AI.
                                    </p>
                                </div>
                            </div>

                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-2">
                                        API KEY
                                    </label>
                                    <div className="flex gap-3">
                                        <div className="flex-1 relative">
                                            <div className="absolute left-3 top-1/2 -translate-y-1/2">
                                                <Key className="w-4 h-4 text-slate-400" />
                                            </div>
                                            <input
                                                type="password"
                                                value={tempApiKey}
                                                onChange={(e) => setTempApiKey(e.target.value)}
                                                placeholder="sk-••••••••••••••••••••"
                                                className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                            />
                                        </div>
                                        <button
                                            onClick={handleSaveApiKey}
                                            className={`px-6 py-2.5 rounded-lg transition-all font-medium flex items-center gap-2 ${apiKeySaved
                                                ? 'bg-green-600 text-white'
                                                : 'bg-blue-600 text-white hover:bg-blue-700'
                                                }`}
                                        >
                                            {apiKeySaved ? (
                                                <>
                                                    <CheckCircle className="w-4 h-4" />
                                                    Saved!
                                                </>
                                            ) : (
                                                'Lưu Key'
                                            )}
                                        </button>
                                    </div>
                                </div>
                                {apiKey && (
                                    <div className="flex items-center gap-2 text-sm text-green-600">
                                        <CheckCircle className="w-4 h-4" />
                                        <span>API Key đã lưu: •••{apiKey.slice(-4)}</span>
                                    </div>
                                )}
                                <a
                                    href="https://aistudio.google.com/app/apikey"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 font-medium"
                                >
                                    <span className="w-4 h-4 bg-blue-100 rounded-full flex items-center justify-center text-xs">?</span>
                                    Hướng dẫn lấy API Key?
                                </a>
                            </div>
                        </>
                    )}
                </div>

                {/* Progress Stepper */}
                {currentProgressStep > 0 && (
                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                        <div className="flex items-center justify-between max-w-4xl mx-auto">
                            {/* Step 1: Search */}
                            <div className="flex flex-col items-center flex-1">
                                <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 transition-all ${currentProgressStep >= 1 ? 'bg-navy-dark text-white' : 'bg-slate-200 text-slate-400'
                                    }`}>
                                    {currentProgressStep > 1 ? (
                                        <CheckCircle className="w-6 h-6" />
                                    ) : (
                                        <Search className="w-6 h-6" />
                                    )}
                                </div>
                                <p className={`text-sm font-medium ${currentProgressStep >= 1 ? 'text-slate-800' : 'text-slate-400'}`}>
                                    1. Tìm kiếm & Lọc
                                </p>
                            </div>

                            {/* Connector Line */}
                            <div className={`h-1 flex-1 mx-2 ${currentProgressStep >= 2 ? 'bg-navy-dark' : 'bg-slate-200'}`}></div>

                            {/* Step 2: Select */}
                            <div className="flex flex-col items-center flex-1">
                                <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 transition-all ${currentProgressStep >= 2 ? 'bg-navy-dark text-white' : 'bg-slate-200 text-slate-400'
                                    }`}>
                                    {currentProgressStep > 2 ? (
                                        <CheckCircle className="w-6 h-6" />
                                    ) : (
                                        <FileText className="w-6 h-6" />
                                    )}
                                </div>
                                <p className={`text-sm font-medium ${currentProgressStep >= 2 ? 'text-slate-800' : 'text-slate-400'}`}>
                                    2. Chọn bài viết
                                </p>
                            </div>

                            {/* Connector Line */}
                            <div className={`h-1 flex-1 mx-2 ${currentProgressStep >= 3 ? 'bg-navy-dark' : 'bg-slate-200'}`}></div>

                            {/* Step 3: Generate */}
                            <div className="flex flex-col items-center flex-1">
                                <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 transition-all ${currentProgressStep >= 3 ? (currentProgressStep === 3 ? 'bg-navy-dark text-white animate-pulse' : 'bg-navy-dark text-white') : 'bg-slate-200 text-slate-400'
                                    }`}>
                                    {currentProgressStep > 3 ? (
                                        <CheckCircle className="w-6 h-6" />
                                    ) : (
                                        <Zap className="w-6 h-6" />
                                    )}
                                </div>
                                <p className={`text-sm font-medium ${currentProgressStep >= 3 ? 'text-slate-800' : 'text-slate-400'}`}>
                                    3. Tạo tóm tắt
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Form tìm kiếm */}
                <InputForm onSubmit={handleSearch} loading={loading} />

                {/* Error Message */}
                {error && (
                    <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6 animate-slide-up">
                        <p className="text-red-800 font-medium">{error}</p>
                    </div>
                )}

                {/* Loading State */}
                {loading && (
                    <div className="animate-slide-up">
                        {currentProgressStep === 3 ? (
                            <SummarizationProgress
                                completed={progressData.completed}
                                total={progressData.total}
                                currentArticle={progressData.currentArticle}
                                status={progressData.status}
                            />
                        ) : currentProgressStep === 1 ? (
                            <ProgressTracker steps={processSteps} />
                        ) : (
                            <LoadingSpinner text={currentStep} />
                        )}
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
                </div>
            </footer>
        </div>
    );
}
