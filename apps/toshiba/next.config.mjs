/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  transpilePackages: ["@repo/ui"],
  sassOptions: {
    includePaths: ["./app/ui"],
    prependData: `@use "@repo/sass-config/mainSass.scss" as *;`,
    silenceDeprecations: ["legacy-js-api", "mixed-decls"],
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
};

export default nextConfig;
