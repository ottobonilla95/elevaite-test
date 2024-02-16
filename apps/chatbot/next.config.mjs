/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    transpilePackages: ["@repo/ui"],    
    sassOptions: {
        includePaths: ["./app/ui"],
        prependData: `@import "@repo/sass-config/mainSass.scss";`,
    },
};

export default nextConfig;
