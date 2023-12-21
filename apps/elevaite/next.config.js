/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  transpilePackages: ["@repo/ui"],
  async redirects() {
    return [
      {
        destination: "/homepage",
        source: "/",
        permanent: false,
      },
    ];
  },
  experimental: {
    serverActions: {
      allowedOrigins: ["elevaite.com"],
    },
  },
  // async rewrites() {
  //   return [
  //     {
  //       destination: "https://login.iopex.ai/login/google",
  //       source: "/login/google",
  //       basePath: false,
  //     },
  //   ];
  // },
};

module.exports = nextConfig;
