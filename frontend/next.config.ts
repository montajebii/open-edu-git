import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required by the Dockerfile runner stage (.next/standalone + server.js).
  output: "standalone",
};

export default nextConfig;
