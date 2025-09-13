/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/visa/:path*',
        destination: 'https://visa-agent-1.onrender.com/:path*',
      },
    ];
  },
};

module.exports = nextConfig;