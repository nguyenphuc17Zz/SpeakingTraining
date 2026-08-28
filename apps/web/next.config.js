/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@speaking-training/ai-contracts"],
  eslint: {
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;
