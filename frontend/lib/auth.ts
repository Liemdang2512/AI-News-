import { API_BASE_URL } from '@/lib/api';

export type UserPublic = {
    id: number | string;
    email: string;
    is_admin: boolean;
};

export async function getMe(): Promise<UserPublic> {
    const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
        method: 'GET',
        credentials: 'include',
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        throw new Error(data?.detail || 'Unauthorized');
    }
    return data as UserPublic;
}

export async function login(email: string, password: string): Promise<UserPublic> {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data?.ok) {
        throw new Error(data?.detail || 'Đăng nhập thất bại');
    }
    return data.user as UserPublic;
}

export async function logout(): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include',
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data?.ok) {
        throw new Error(data?.detail || 'Đăng xuất thất bại');
    }
}

export async function createUserByAdmin(payload: {
    email: string;
    password: string;
    is_admin?: boolean;
}): Promise<UserPublic> {
    const res = await fetch(`${API_BASE_URL}/api/admin/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
            email: payload.email,
            password: payload.password,
            is_admin: Boolean(payload.is_admin),
        }),
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data?.ok) {
        throw new Error(data?.detail || 'Tạo tài khoản thất bại');
    }
    return data.user as UserPublic;
}

