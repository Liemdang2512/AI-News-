'use client';

import { useState } from 'react';
import { UserPlus } from 'lucide-react';
import { createUserByAdmin } from '@/lib/auth';

export default function AdminCreateUserPanel() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isAdmin, setIsAdmin] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleCreate = async () => {
        setLoading(true);
        setError('');
        setSuccess('');
        if (!email.trim() || !password) {
            setError('Vui lòng nhập đầy đủ email và mật khẩu.');
            setLoading(false);
            return;
        }
        try {
            const user = await createUserByAdmin({
                email: email.trim(),
                password,
                is_admin: isAdmin,
            });
            setSuccess(`Đã tạo tài khoản: ${user.email}`);
            setEmail('');
            setPassword('');
            setIsAdmin(false);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Đã xảy ra lỗi');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 relative z-30">
            <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <UserPlus className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                    <h2 className="text-lg font-bold text-slate-800">Admin tạo tài khoản</h2>
                    <p className="text-sm text-slate-500">Tạo user mới để đăng nhập vào hệ thống.</p>
                </div>
            </div>

            <div className="space-y-3">
                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="user@example.com"
                        className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Mật khẩu</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                    />
                </div>

                <label className="inline-flex items-center gap-2 text-sm text-slate-700">
                    <input
                        type="checkbox"
                        checked={isAdmin}
                        onChange={(e) => setIsAdmin(e.target.checked)}
                    />
                    Tạo tài khoản admin
                </label>

                {error ? (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>
                ) : null}
                {success ? (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-700">{success}</div>
                ) : null}

                <button
                    onClick={handleCreate}
                    disabled={loading}
                    className="px-4 py-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60 font-medium"
                >
                    {loading ? 'Đang tạo...' : 'Tạo tài khoản'}
                </button>
            </div>
        </div>
    );
}

