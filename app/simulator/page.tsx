import type { Metadata } from 'next';

import { SimulatorApp } from '@/components/simulator/SimulatorApp';

export const metadata: Metadata = {
  title: 'AgroLidar Simulator',
  description: 'Procedural agricultural LiDAR driving simulator.',
};

export default function SimulatorPage() {
  return <SimulatorApp />;
}
