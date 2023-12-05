/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        destination: "/appDrawer",
        source: "/",
      },
    ];
  },
};

module.exports = nextConfig;
