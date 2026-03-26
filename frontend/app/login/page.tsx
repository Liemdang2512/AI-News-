'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { LogIn, Mail, Lock } from 'lucide-react';
import { getMe, login } from '@/lib/auth';

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleLogin = async () => {
        setLoading(true);
        setError('');
        try {
            await login(email, password);
            // In dev mode, cookie propagation can race with immediate navigation.
            // Retry /auth/me briefly before redirecting to avoid bouncing back to /login.
            let verified = false;
            // Give the browser a moment to persist Set-Cookie before the first check.
            await new Promise((resolve) => setTimeout(resolve, 250));
            for (let i = 0; i < 12; i += 1) {
                try {
                    await getMe();
                    verified = true;
                    break;
                } catch {
                    await new Promise((resolve) => setTimeout(resolve, 200));
                }
            }
            if (!verified) {
                throw new Error('Đăng nhập thành công nhưng chưa xác nhận được session. Vui lòng F5 và thử lại.');
            }
            router.replace('/');
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Đăng nhập thất bại');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
            <div className="w-full max-w-md bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <LogIn className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold text-slate-800">Đăng nhập</h1>
                        <p className="text-sm text-slate-500">Bạn cần đăng nhập để sử dụng ứng dụng.</p>
                    </div>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">Email</label>
                        <div className="relative">
                            <div className="absolute left-3 top-1/2 -translate-y-1/2">
                                <Mail className="w-4 h-4 text-slate-400" />
                            </div>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="admin@example.com"
                                className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">Mật khẩu</label>
                        <div className="relative">
                            <div className="absolute left-3 top-1/2 -translate-y-1/2">
                                <Lock className="w-4 h-4 text-slate-400" />
                            </div>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            />
                        </div>
                    </div>

                    {error ? (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                            <p className="text-sm text-red-800 font-medium">{error}</p>
                        </div>
                    ) : null}

                    <button
                        onClick={handleLogin}
                        disabled={loading || !email.trim() || !password}
                        className="w-full px-4 py-2.5 rounded-lg transition-all font-medium flex items-center justify-center gap-2 bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
                    >
                        <LogIn className="w-4 h-4" />
                        {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
                    </button>
                </div>
            </div>
        </div>
    );
}

