/** @type {import('next').NextConfig} */
const isElectron = process.env.NEXT_OUTPUT === 'export'
const BACKEND_URL = process.env.BACKEND_URL || 'https://ai-news-production-7cfe.up.railway.app'

const nextConfig = {
    reactStrictMode: true,

    // Nén response HTTP (gzip/brotli) cho tất cả assets
    compress: true,

    // Tắt X-Powered-By header — nhỏ nhưng giảm overhead
    poweredByHeader: false,

    // Tối ưu package imports: tree-shake chỉ lấy icon được dùng
    experimental: {
        optimizePackageImports: ['lucide-react'],
    },

    ...(isElectron
        ? {
            output: 'export',
            assetPrefix: './',
            trailingSlash: true,
        }
        : {
            // Proxy /api/* to Railway backend (avoids cross-domain cookie issues)
            async rewrites() {
                return [
                    {
                        source: '/api/:path*',
                        destination: `${BACKEND_URL}/api/:path*`,
                    },
                ]
            },
        }),
}

module.exports = nextConfig
