/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  transpilePackages: ["@repo/ui", "@repo/sass-config", "@repo/lib"],
  async redirects() {
    return [
      {
        destination: "/homepage",
        source: "/",
        permanent: false,
      },
    ];
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",
        port: "",
        pathname: "/a/**",
      },
    ],
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
    prependData: `@use "@repo/sass-config/mainSass.scss" as *;`,
  },
};

module.exports = nextConfig;
