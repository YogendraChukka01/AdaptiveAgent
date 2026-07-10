import type { Metadata, Viewport } from "next";
import { StrictMode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "SafeAgent",
  description: "Secure, Explainable, and Trustworthy Agentic RAG Platform",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="min-h-screen">
        <StrictMode>{children}</StrictMode>
      </body>
    </html>
  );
}
