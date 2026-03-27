import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgroLidar — Perception for the Field",
  description: "LiDAR-based safety perception system for agricultural machines."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
