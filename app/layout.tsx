import type { Metadata } from "next";
import "./globals.css";

import { Providers } from "@/app/providers";

export const metadata: Metadata = {
  title: "AgroLidar — Perception for the Field",
  description: "LiDAR-based safety perception system for agricultural machines."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="scroll-smooth">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
