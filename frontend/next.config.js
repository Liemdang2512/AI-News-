/** @type {import('next').NextConfig} */
const isElectron = process.env.NEXT_OUTPUT === 'export'

const nextConfig = {
    reactStrictMode: true,
    // Static export only for Electron desktop build (set NEXT_OUTPUT=export)
    // Vercel deployment uses Next.js server mode for rewrites/proxy support
    ...(isElectron
        ? {
            output: 'export',
            assetPrefix: './',
            trailingSlash: true,
        }
        : {}),
}

module.exports = nextConfig
