import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL;

const nextConfig: NextConfig = {
  async rewrites() {
    // When BACKEND_URL is set, proxy /api/* to the backend (works both in
    // local dev and on Vercel).  When unset (e.g. first Vercel build before
    // env vars are configured), return no rewrites — the frontend will fall
    // back to calling the backend directly via NEXT_PUBLIC_API_URL.
    if (!backendUrl) return [];
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
