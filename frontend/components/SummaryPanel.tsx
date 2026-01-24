'use client';

import ReactMarkdown from 'react-markdown';
import { FileText } from 'lucide-react';

interface SummaryPanelProps {
    summary: string;
}

export default function SummaryPanel({ summary }: SummaryPanelProps) {
    return (
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
            <div className="flex items-center gap-3 mb-6">
                <FileText className="w-6 h-6 text-accent-600" />
                <h2 className="text-2xl font-bold text-gray-800">Tóm tắt bài viết</h2>
            </div>

            <div className="prose prose-lg max-w-none">
                <ReactMarkdown
                    components={{
                        h1: ({ children }) => (
                            <h1 className="text-2xl font-bold text-gray-900 mb-4">{children}</h1>
                        ),
                        h2: ({ children }) => (
                            <h2 className="text-xl font-bold text-gray-900 mb-3">{children}</h2>
                        ),
                        p: ({ children }) => (
                            <p className="text-gray-700 mb-4 leading-relaxed">{children}</p>
                        ),
                        strong: ({ children }) => (
                            <strong className="font-bold text-gray-900">{children}</strong>
                        ),
                        hr: () => (
                            <hr className="my-6 border-t-2 border-gray-200" />
                        ),
                        a: ({ href, children }) => (
                            <a
                                href={href}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary-600 hover:text-primary-800 underline"
                            >
                                {children}
                            </a>
                        ),
                    }}
                >
                    {summary}
                </ReactMarkdown>
            </div>
        </div>
    );
}
