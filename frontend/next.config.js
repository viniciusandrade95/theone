/** @type {import('next').NextConfig} */
const APP_BASE = process.env.NEXT_PUBLIC_APP_BASE_PATH || "";

const nextConfig = {
  basePath: APP_BASE,
  assetPrefix: APP_BASE,
};

module.exports = nextConfig;
