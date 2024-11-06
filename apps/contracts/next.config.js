/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  transpilePackages: ["@repo/ui"],
  // async redirects() {
  //   return [
  //     {
  //       destination: "/homepage",
  //       source: "/",
  //       permanent: false,
  //     },
  //   ];
  // },
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
  // experimental: {
  //   serverActions: {
  //     allowedOrigins: ["elevaite.com"],
  //   },
  // },
  sassOptions: {
    includePaths: ["./app/ui"],
    prependData: `@use "@repo/sass-config/mainSass.scss" as *;`,
    silenceDeprecations: ['legacy-js-api', "mixed-decls"],
  },
};

module.exports = nextConfig;
