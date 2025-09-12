/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/visa/:path*',
        destination: 'http://localhost:2024/:path*',
      },
    ];
  },
};

module.exports = nextConfig;