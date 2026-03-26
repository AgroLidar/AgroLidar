import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgroLidar | Perception for the Field",
  description:
    "AgroLidar is a LiDAR perception platform built specifically for agricultural machines operating in harsh real-world field conditions."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
