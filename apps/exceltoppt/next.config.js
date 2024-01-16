/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  transpilePackages: ["@repo/ui", "@repo/sass-config"],
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
  sassOptions: {
    includePaths: ["./app/ui"],
    prependData: `@import "@repo/sass-config/mainSass.scss";`,
  },
};

module.exports = nextConfig;
