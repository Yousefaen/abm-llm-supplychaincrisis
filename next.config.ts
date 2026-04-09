import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        // Match backend default PORT=8010 (8000 often fails on Windows with WinError 10013).
        destination: `${process.env.BACKEND_URL || "http://localhost:8010"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
