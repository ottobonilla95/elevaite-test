/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    transpilePackages: ["@repo/ui"],    
    env: {
        NEXTAUTH_URL_INTERNAL: process.env.NEXTAUTH_URL_INTERNAL || "https://elevaite.iopex.ai",
      },
    sassOptions: {
        includePaths: ["./app/ui"],
        prependData: `@import "@repo/sass-config/mainSass.scss";`,
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
