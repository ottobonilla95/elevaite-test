/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    transpilePackages: ["@repo/ui"],    
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
