/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Personal Learning OS frontend (Next.js) proxies /api/* and /ws/* to the FastAPI backend on :8001.
  // When running standalone against a real Personal Learning OS backend, rewrites forward API calls.
  async rewrites() {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (base && process.env.NEXT_PUBLIC_USE_MOCK !== "true") {
      return [
        { source: "/api/:path*", destination: `${base}/api/:path*` },
        { source: "/ws/:path*", destination: `${base}/ws/:path*` },
      ];
    }
    return [];
  },
};

export default nextConfig;
