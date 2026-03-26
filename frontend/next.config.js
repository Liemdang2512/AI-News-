/** @type {import('next').NextConfig} */
const isProd = process.env.NODE_ENV === 'production'

const nextConfig = {
    reactStrictMode: true,
    output: 'export', // Generate static files for Electron desktop app
    // Only use relative asset paths for production static export.
    // In dev, this breaks CSS/JS loading on nested routes like /login.
    ...(isProd
        ? {
            assetPrefix: './',
            trailingSlash: true,
        }
        : {}),
}

module.exports = nextConfig
