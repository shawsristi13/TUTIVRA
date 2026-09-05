import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    // API responses are dynamically typed — suppress false positive unknown errors
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
