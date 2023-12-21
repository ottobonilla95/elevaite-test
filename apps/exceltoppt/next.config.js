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
