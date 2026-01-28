import React from 'react';
import { Loader2, CheckCircle, FileText, Zap } from 'lucide-react';

interface SummarizationProgressProps {
    completed: number;
    total: number;
    currentArticle: string;
    status: string; // 'processing' | 'completed' | 'error'
}

export default function SummarizationProgress({
    completed,
    total,
    currentArticle,
    status
}: SummarizationProgressProps) {
    const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

    // Ensure percentage doesn't exceed 100
    const visualPercentage = Math.min(Math.max(percentage, 5), 100);

    return (
        <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-lg border border-blue-100 p-8 space-y-8 animate-fade-in-up">
            <div className="text-center space-y-3">
                <div className="relative inline-block">
                    <div className="absolute inset-0 bg-blue-100 rounded-full animate-ping opacity-75"></div>
                    <div className="relative inline-flex items-center justify-center p-4 bg-blue-50 rounded-full">
                        <Zap className="w-8 h-8 text-blue-600 animate-pulse" />
                    </div>
                </div>

                <h2 className="text-2xl font-bold text-slate-800">
                    {completed === total && total > 0 ? "Hoàn tất tổng hợp!" : "AI đang làm việc..."}
                </h2>
                <p className="text-slate-500">
                    {completed === total && total > 0
                        ? "Đã xử lý xong tất cả bài viết. Đang hiển thị kết quả..."
                        : "Đang đọc hiểu, trích xuất và tóm tắt các bài báo cho bạn"}
                </p>
            </div>

            <div className="space-y-3">
                <div className="flex justify-between text-sm font-semibold text-slate-700">
                    <span className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                        Tiến độ xử lý
                    </span>
                    <span className="text-blue-700">{completed}/{total} bài</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-4 overflow-hidden shadow-inner">
                    <div
                        className="bg-gradient-to-r from-blue-500 to-indigo-600 h-full rounded-full transition-all duration-700 ease-out flex items-center justify-end pr-2"
                        style={{ width: `${visualPercentage}%` }}
                    >
                        {percentage >= 10 && <span className="text-[10px] text-white font-bold">{percentage}%</span>}
                    </div>
                </div>
            </div>

            <div className="bg-slate-50 rounded-xl p-5 border border-slate-100 shadow-sm transition-all duration-300">
                <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm border border-slate-100 shrink-0">
                        <FileText className="w-5 h-5 text-blue-500" />
                    </div>

                    <div className="space-y-1 overflow-hidden min-w-0 flex-1">
                        <p className="text-xs font-bold text-blue-600 uppercase tracking-wider flex items-center gap-1">
                            {status === 'processing' ? (
                                <>
                                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></span>
                                    Đang xử lý
                                </>
                            ) : (
                                <>
                                    <CheckCircle className="w-3 h-3" />
                                    Hoàn tất
                                </>
                            )}
                        </p>
                        <p className="text-sm text-slate-700 truncate font-medium" title={currentArticle}>
                            {currentArticle || 'Đang chuẩn bị dữ liệu...'}
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-6 text-center pt-2">
                <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-2xl font-bold text-slate-800">{completed}</p>
                    <p className="text-xs text-slate-500 uppercase font-medium tracking-wide mt-1">Đã xong</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-2xl font-bold text-slate-800">{Math.max(0, total - completed)}</p>
                    <p className="text-xs text-slate-500 uppercase font-medium tracking-wide mt-1">Còn lại</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-600">{percentage}%</p>
                    <p className="text-xs text-slate-500 uppercase font-medium tracking-wide mt-1">Hoàn thành</p>
                </div>
            </div>
        </div>
    );
}
