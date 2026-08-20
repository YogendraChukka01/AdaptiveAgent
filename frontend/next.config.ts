import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV === "development";

const nextConfig: NextConfig = {
  output: "standalone",
  headers: async () => [
    {
      source: "/(.*)",
      headers: [
        { key: "X-Frame-Options", value: "DENY" },
        { key: "X-Content-Type-Options", value: "nosniff" },
        { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        {
          key: "Content-Security-Policy",
          value: [
            "default-src 'self'",
            `script-src 'self'${isDev ? " 'unsafe-inline' 'unsafe-eval'" : " 'unsafe-inline'"}`,
            "style-src 'self' 'unsafe-inline'",
            `connect-src 'self' http://localhost:* https://localhost:*${isDev ? " ws://localhost:*" : ""}`,
            "img-src 'self' data: blob:",
            "font-src 'self' data:",
            "worker-src 'self' blob:",
          ].join("; "),
        },
      ],
    },
  ],
};

export default nextConfig;
