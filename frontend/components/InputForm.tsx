'use client';

import { useState, useEffect, useRef } from 'react';
import { Search, X, ChevronDown, Check } from 'lucide-react';

interface InputFormProps {
    onSubmit: (data: { newspapers: string; date: string; timeRange: string }) => void;
    loading: boolean;
}

const availableNewspapers = [
    // 'Lao Động',
    'Dân Trí',
    'VTV',
    'Hà Nội Mới',
    'Sài Gòn Giải Phóng',
    'VietnamPlus',
    'Tiền Phong'
];

export default function InputForm({ onSubmit, loading }: InputFormProps) {
    const [selectedNewspapers, setSelectedNewspapers] = useState<string[]>(['Dân Trí', 'VTV']);
    const [showDropdown, setShowDropdown] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const [date, setDate] = useState(() => {
        const today = new Date();
        const day = String(today.getDate()).padStart(2, '0');
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const year = today.getFullYear();
        return `${day}/${month}/${year}`;
    });
    const [timeRange, setTimeRange] = useState('0h00 đến 23h59');

    const timeRanges = [
        '0h00 đến 23h59',
        '6h00 đến 8h00',
        '8h00 đến 11h00',
        '11h00 đến 14h00',
        '14h00 đến 17h00',
        '17h00 đến 21h00',
    ];

    // Click outside to close dropdown
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setShowDropdown(false);
            }
        };

        if (showDropdown) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [showDropdown]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({
            newspapers: selectedNewspapers.join(', '),
            date,
            timeRange
        });
    };

    const toggleNewspaper = (newspaper: string) => {
        setSelectedNewspapers(prev =>
            prev.includes(newspaper)
                ? prev.filter(n => n !== newspaper)
                : [...prev, newspaper]
        );
    };

    const selectAll = () => {
        setSelectedNewspapers(availableNewspapers);
    };

    const deselectAll = () => {
        setSelectedNewspapers([]);
    };

    const isAllSelected = selectedNewspapers.length === availableNewspapers.length;

    return (
        <div className="bg-white rounded-2xl shadow-soft p-6 lg:p-8 border border-slate-100 transition-all duration-300 hover:shadow-lg">
            <div className="space-y-6">
                {/* Search Bar Row */}
                <form onSubmit={handleSubmit}>
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="flex-1 relative" ref={dropdownRef}>
                            {/* Search Input with Dropdown */}
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none z-10">
                                    <Search className="w-5 h-5 text-slate-400 group-focus-within:text-vibrant-blue transition-colors duration-200" />
                                </div>
                                <button
                                    type="button"
                                    onClick={() => setShowDropdown(!showDropdown)}
                                    className="w-full h-12 pl-11 pr-32 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-left focus:ring-2 focus:ring-vibrant-blue/20 focus:border-vibrant-blue transition-all duration-200 outline-none hover:bg-slate-100 truncate"
                                >
                                    {selectedNewspapers.length > 0
                                        ? selectedNewspapers.join(', ')
                                        : 'Tìm kiếm đầu báo...'}
                                </button>
                                <div className="absolute inset-y-0 right-0 pr-2 flex items-center gap-1 z-10">
                                    <button
                                        type="button"
                                        onClick={isAllSelected ? deselectAll : selectAll}
                                        className="text-xs font-semibold text-vibrant-blue hover:text-corporate-navy px-3 py-1.5 rounded-lg hover:bg-vibrant-blue/10 transition-all duration-200 flex items-center gap-1"
                                    >
                                        <Check className="w-4 h-4" />
                                        {isAllSelected ? 'Bỏ chọn' : 'Chọn tất cả'}
                                    </button>
                                    <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform duration-300 ${showDropdown ? 'rotate-180' : ''}`} />
                                </div>
                            </div>

                            {/* Dropdown Menu */}
                            {showDropdown && (
                                <div className="absolute z-20 w-full mt-2 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden animate-slide-up">
                                    <div className="max-h-64 overflow-y-auto">
                                        {availableNewspapers.map((newspaper) => (
                                            <button
                                                key={newspaper}
                                                type="button"
                                                onClick={() => toggleNewspaper(newspaper)}
                                                className="w-full px-4 py-3 text-left hover:bg-slate-50 transition-colors duration-150 flex items-center justify-between group"
                                            >
                                                <span className="text-sm text-slate-700 group-hover:text-vibrant-blue transition-colors duration-150">
                                                    {newspaper}
                                                </span>
                                                {selectedNewspapers.includes(newspaper) && (
                                                    <Check className="w-5 h-5 text-vibrant-blue animate-fade-in" />
                                                )}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        <button
                            type="submit"
                            disabled={loading || selectedNewspapers.length === 0}
                            className="glossy-button h-12 px-8 rounded-xl text-white font-semibold text-sm tracking-wide shadow-lg flex items-center justify-center gap-2 hover:shadow-glow transition-all duration-300 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <span>{loading ? 'Đang tìm kiếm...' : 'Tìm kiếm'}</span>
                            <span className="text-[18px] transition-transform duration-300 group-hover:translate-x-1">→</span>
                        </button>
                    </div>
                </form>

                {/* Date and Time Range Row */}
                <div className="flex flex-col xl:flex-row items-start xl:items-center justify-between gap-6 pt-2 border-t border-slate-100">
                    {/* Date Picker */}
                    <div className="w-full xl:w-auto flex flex-col sm:flex-row items-start sm:items-center gap-2">
                        <div className="flex items-center gap-2 mb-2 sm:mb-0">
                            <span className="text-[20px] text-vibrant-blue">📅</span>
                            <span className="text-corporate-blue-text font-semibold text-sm">Ngày</span>
                        </div>
                        <div className="relative w-full sm:w-64">
                            <input
                                type="text"
                                value={date}
                                onChange={(e) => setDate(e.target.value)}
                                placeholder="DD/MM/YYYY"
                                className="w-full h-10 pl-3 pr-3 text-left bg-white border border-vibrant-blue rounded-lg text-sm text-vibrant-blue font-medium focus:outline-none focus:ring-2 focus:ring-vibrant-blue/20 shadow-sm transition-all duration-200 hover:shadow-md"
                            />
                        </div>
                    </div>

                    {/* Time Range */}
                    <div className="w-full xl:w-auto flex flex-col sm:flex-row items-start sm:items-center gap-2">
                        <div className="flex items-center gap-2 mb-2 sm:mb-0">
                            <span className="text-[20px] text-vibrant-blue">🕐</span>
                            <span className="text-corporate-blue-text font-semibold text-sm">Khoảng thời gian</span>
                        </div>
                        <div className="relative w-full sm:w-64">
                            <select
                                value={timeRange}
                                onChange={(e) => setTimeRange(e.target.value)}
                                className="w-full h-10 pl-3 pr-10 text-left bg-white border border-vibrant-blue rounded-lg text-sm text-vibrant-blue font-medium focus:outline-none focus:ring-2 focus:ring-vibrant-blue/20 shadow-sm appearance-none cursor-pointer transition-all duration-200 hover:shadow-md"
                            >
                                {timeRanges.map((range) => (
                                    <option key={range} value={range}>
                                        {range}
                                    </option>
                                ))}
                            </select>
                            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                                <ChevronDown className="w-4 h-4 text-vibrant-blue" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
