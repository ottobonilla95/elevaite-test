/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  transpilePackages: ["@repo/ui"],
  // async rewrites() {
  //   return [
  //     {
  //       destination: "/appDrawer",
  //       source: "/",
  //     },
  //   ];
  // },
};

module.exports = nextConfig;
