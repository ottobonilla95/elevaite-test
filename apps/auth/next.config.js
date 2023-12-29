/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  transpilePackages: ["@repo/ui"],
  // experimental: {
  //   serverActions: {
  //     allowedOrigins: ["auth.elevaite.com"],
  //   },
  // },
  // async rewrites() {
  //   return [
  //     {
  //       destination: "/login",
  //       source: "/",
  //     },
  //   ];
  // },
};

module.exports = nextConfig;
