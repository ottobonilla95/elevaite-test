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
  sassOptions: {
    includePaths: ["./app/ui"],
    prependData: `@use "@repo/sass-config/mainSass.scss" as *;`,
  },
};

module.exports = nextConfig;
