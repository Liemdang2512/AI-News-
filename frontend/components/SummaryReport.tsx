'use client';

import { Download, Share2, Calendar, Clock } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Document, Paragraph, TextRun, HeadingLevel, AlignmentType, Packer } from 'docx';
import { saveAs } from 'file-saver';

interface SummaryReportProps {
    summary: string;
    metadata?: {
        date?: string;
        timeRange?: string;
        totalArticles?: number;
    };
    onBack?: () => void;
}

export default function SummaryReport({ summary, metadata, onBack }: SummaryReportProps) {
    const handleDownload = async () => {
        try {
            const lines = summary.split('\n');
            const paragraphs: Paragraph[] = [];

            // Add title
            paragraphs.push(
                new Paragraph({
                    text: 'Bản tóm tắt các bài báo',
                    heading: HeadingLevel.TITLE,
                    alignment: AlignmentType.CENTER,
                    spacing: { after: 200 },
                })
            );

            // Add metadata
            if (metadata?.date) {
                paragraphs.push(
                    new Paragraph({
                        children: [new TextRun({ text: `Ngày: ${metadata.date}`, size: 20 })],
                        spacing: { after: 100 },
                    })
                );
            }

            if (metadata?.timeRange) {
                paragraphs.push(
                    new Paragraph({
                        children: [new TextRun({ text: `Khung giờ: ${metadata.timeRange}`, size: 20 })],
                        spacing: { after: 100 },
                    })
                );
            }

            if (metadata?.totalArticles) {
                paragraphs.push(
                    new Paragraph({
                        children: [new TextRun({ text: `Tóm tắt từ ${metadata.totalArticles} bài viết`, size: 20 })],
                        spacing: { after: 300 },
                    })
                );
            }

            // Process content
            for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed) {
                    paragraphs.push(new Paragraph({ text: '', spacing: { after: 100 } }));
                } else if (trimmed === '---') {
                    paragraphs.push(new Paragraph({ text: '', spacing: { after: 200 } }));
                } else if (trimmed.includes('|') && trimmed === trimmed.toUpperCase()) {
                    // Source | Category (uppercase)
                    paragraphs.push(
                        new Paragraph({
                            children: [new TextRun({ text: trimmed, size: 28, color: '333333', bold: true })],
                            spacing: { before: 200, after: 100 },
                        })
                    );
                } else if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
                    // Bold title
                    const title = trimmed.replace(/\*\*/g, '');
                    paragraphs.push(
                        new Paragraph({
                            children: [new TextRun({ text: title, bold: true, size: 24 })],
                            spacing: { after: 100 },
                        })
                    );
                } else if (trimmed.match(/^\[(.+?)\]\((.+?)\)$/)) {
                    // Markdown link: [text](url)
                    const match = trimmed.match(/^\[(.+?)\]\((.+?)\)$/);
                    if (match) {
                        const linkText = match[1];
                        const url = match[2];
                        paragraphs.push(
                            new Paragraph({
                                children: [
                                    new TextRun({
                                        text: url,
                                        size: 20,
                                        color: '0066CC',
                                        underline: {},
                                    })
                                ],
                                spacing: { after: 150 },
                            })
                        );
                    }
                } else if (trimmed.startsWith('-')) {
                    // Bullet point
                    const text = trimmed.substring(1).trim();
                    paragraphs.push(
                        new Paragraph({
                            children: [new TextRun({ text: `• ${text}`, size: 22 })],
                            spacing: { after: 150 },
                        })
                    );
                } else {
                    // Regular text
                    paragraphs.push(
                        new Paragraph({
                            children: [new TextRun({ text: trimmed, size: 22 })],
                            spacing: { after: 150 },
                        })
                    );
                }
            }

            const doc = new Document({ sections: [{ properties: {}, children: paragraphs }] });
            const blob = await Packer.toBlob(doc);
            saveAs(blob, `ban-tin-thong-minh-${new Date().toISOString().split('T')[0]}.docx`);
        } catch (error) {
            console.error('Error:', error);
            alert('Không thể tạo file Word. Vui lòng thử lại.');
        }
    };

    const handleShare = () => {
        if (navigator.share) {
            navigator.share({
                title: 'Bản tin thông minh',
                text: summary,
            }).catch(console.error);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Breadcrumb */}
            <div className="bg-white border-b border-slate-200">
                <div className="max-w-4xl mx-auto px-6 py-4">
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                        <button
                            onClick={onBack}
                            className="hover:text-vibrant-blue transition-colors"
                        >
                            ← Quay lại danh sách
                        </button>
                        <span>/</span>
                        <span className="text-slate-900 font-medium">Báo cáo chi tiết</span>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-4xl mx-auto px-6 py-8">
                {/* Header Card */}
                <div className="bg-white rounded-2xl shadow-soft border border-slate-100 p-8 mb-6">
                    <div className="flex items-start justify-between mb-6">
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <span className="text-xs font-semibold text-vibrant-blue uppercase tracking-wider">
                                    Bản tóm tắt các bài báo
                                </span>
                            </div>
                            <h1 className="text-3xl font-bold text-corporate-blue-text mb-4">
                                Bản tóm tắt các bài báo
                            </h1>

                            {/* Metadata */}
                            <div className="flex flex-wrap gap-4 text-sm text-slate-600">
                                {metadata?.date && (
                                    <div className="flex items-center gap-2">
                                        <Calendar className="w-4 h-4 text-vibrant-blue" />
                                        <span>Thứ Hai, {metadata.date}</span>
                                    </div>
                                )}
                                {metadata?.timeRange && (
                                    <div className="flex items-center gap-2">
                                        <Clock className="w-4 h-4 text-vibrant-blue" />
                                        <span>Khung giờ: {metadata.timeRange}</span>
                                    </div>
                                )}
                                {metadata?.totalArticles && (
                                    <div className="flex items-center gap-2">
                                        <span className="text-vibrant-blue">📰</span>
                                        <span>Tóm tắt từ {metadata.totalArticles} bài viết</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-6 border-t border-slate-100">
                        <button
                            onClick={handleDownload}
                            className="flex items-center gap-2 px-6 py-3 bg-vibrant-blue hover:bg-corporate-navy text-white font-semibold rounded-xl transition-all duration-200 shadow-md hover:shadow-lg"
                        >
                            <Download className="w-5 h-5" />
                            Tải xuống
                        </button>
                        <button
                            onClick={handleShare}
                            className="flex items-center gap-2 px-6 py-3 bg-white hover:bg-slate-50 text-slate-700 font-semibold rounded-xl border border-slate-200 transition-all duration-200"
                        >
                            <Share2 className="w-5 h-5" />
                            Chia sẻ
                        </button>
                    </div>
                </div>

                {/* Summary Content */}
                <div className="bg-white rounded-2xl shadow-soft border border-slate-100 p-8">
                    <div className="prose prose-slate max-w-none">
                        <ReactMarkdown
                            components={{
                                h1: ({ children }) => (
                                    <h2 className="flex items-center gap-3 text-xl font-bold text-corporate-blue-text mb-4 pb-3 border-b border-slate-200">
                                        <span className="w-2 h-2 bg-vibrant-blue rounded-full"></span>
                                        {children}
                                    </h2>
                                ),
                                h2: ({ children }) => (
                                    <h3 className="text-lg font-bold text-slate-800 mt-6 mb-3">
                                        {children}
                                    </h3>
                                ),
                                p: ({ children }) => (
                                    <p className="text-slate-700 leading-relaxed mb-4">
                                        {children}
                                    </p>
                                ),
                                ul: ({ children }) => (
                                    <ul className="space-y-2 mb-4">
                                        {children}
                                    </ul>
                                ),
                                li: ({ children }) => (
                                    <li className="flex items-start gap-2 text-slate-700">
                                        <span className="text-vibrant-blue mt-1.5">•</span>
                                        <span className="flex-1">{children}</span>
                                    </li>
                                ),
                                strong: ({ children }) => (
                                    <strong className="font-bold text-corporate-blue-text">
                                        {children}
                                    </strong>
                                ),
                                blockquote: ({ children }) => (
                                    <blockquote className="border-l-4 border-vibrant-blue bg-blue-50 pl-4 py-3 my-4 italic text-slate-600">
                                        {children}
                                    </blockquote>
                                ),
                                hr: () => (
                                    <hr className="my-8 border-slate-200" />
                                ),
                            }}
                        >
                            {summary}
                        </ReactMarkdown>
                    </div>
                </div>

                {/* Footer Note */}
                <div className="mt-6 text-center text-sm text-slate-500">
                    <p>Báo cáo này được tạo tự động bởi AI News Assistant. Vui lòng kiểm tra thông tin trước khi sử dụng.</p>
                </div>
            </div>
        </div>
    );
}
