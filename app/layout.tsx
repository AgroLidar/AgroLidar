import type { Metadata } from 'next';
import './globals.css';

import { Providers } from '@/app/providers';

export const metadata: Metadata = {
  title: 'AgroLidar — Flagship LiDAR Simulator',
  description: 'Premium browser-native tractor and agricultural LiDAR hazard simulator for field safety demos.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="scroll-smooth">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
