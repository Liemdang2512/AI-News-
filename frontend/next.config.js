/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    output: 'export',  // Generate static files for Electron desktop app
    assetPrefix: './',  // Use relative paths for assets (required for Electron file:// protocol)
    trailingSlash: true,  // Ensure proper path resolution in static export
}

module.exports = nextConfig
