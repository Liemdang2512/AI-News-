import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ text = "Đang xử lý..." }: { text?: string }) {
    return (
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <Loader2 className="w-12 h-12 text-primary-600 animate-spin" />
            <p className="text-gray-600 text-lg font-medium">{text}</p>
        </div>
    );
}
