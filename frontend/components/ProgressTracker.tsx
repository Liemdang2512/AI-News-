'use client';

import { CheckCircle2, Loader2, XCircle, Circle } from 'lucide-react';

interface ProcessStep {
    id: string;
    label: string;
    status: 'pending' | 'running' | 'done' | 'skipped' | 'error';
    message?: string;
}

interface ProgressTrackerProps {
    steps: ProcessStep[];
}

export default function ProgressTracker({ steps }: ProgressTrackerProps) {
    // Calculate overall progress percentage
    const calculateProgress = () => {
        const totalSteps = steps.length;
        const completedSteps = steps.filter(s => s.status === 'done' || s.status === 'skipped').length;
        const runningSteps = steps.filter(s => s.status === 'running').length;

        // Each completed step = 100/totalSteps %
        // Running step = 50% of its portion
        const progress = ((completedSteps + (runningSteps * 0.5)) / totalSteps) * 100;
        return Math.round(progress);
    };

    const progressPercentage = calculateProgress();

    return (
        <div className="bg-white border border-slate-200 rounded-lg p-6 space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-800">Tiến trình xử lý</h3>
                <span className="text-2xl font-bold text-blue-600">{progressPercentage}%</span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                <div
                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-full rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${progressPercentage}%` }}
                />
            </div>

            <div className="space-y-3">
                {steps.map((step, index) => (
                    <div key={step.id} className="flex items-start gap-3">
                        {/* Icon */}
                        <div className="mt-0.5">
                            {step.status === 'done' && (
                                <CheckCircle2 className="w-5 h-5 text-green-600" />
                            )}
                            {step.status === 'running' && (
                                <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                            )}
                            {step.status === 'error' && (
                                <XCircle className="w-5 h-5 text-red-600" />
                            )}
                            {step.status === 'skipped' && (
                                <Circle className="w-5 h-5 text-slate-300" />
                            )}
                            {step.status === 'pending' && (
                                <Circle className="w-5 h-5 text-slate-300" />
                            )}
                        </div>

                        {/* Content */}
                        <div className="flex-1">
                            <div className="flex items-center gap-2">
                                <span className={`font-medium ${step.status === 'done' ? 'text-green-700' :
                                    step.status === 'running' ? 'text-blue-700' :
                                        step.status === 'error' ? 'text-red-700' :
                                            step.status === 'skipped' ? 'text-slate-400' :
                                                'text-slate-500'
                                    }`}>
                                    {step.label}
                                </span>
                                {step.status === 'running' && (
                                    <span className="text-xs text-slate-500 animate-pulse">
                                        Đang xử lý...
                                    </span>
                                )}
                            </div>
                            {step.message && (
                                <p className="text-sm text-slate-600 mt-1">
                                    {step.message}
                                </p>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
