/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  transpilePackages: ["@repo/ui"],
  experimental: {
    serverActions: {
      allowedOrigins: ["auth.elevaite.com"],
    },
  },
};

module.exports = nextConfig;
