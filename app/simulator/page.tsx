import type { Metadata } from 'next';

import { SimulatorApp } from '@/components/simulator/SimulatorApp';

export const metadata: Metadata = {
  title: 'AgroLidar Flagship Simulator',
  description: 'Browser-native tractor and agricultural field LiDAR simulator with hazard-focused telemetry.',
};

export default function SimulatorPage() {
  return <SimulatorApp />;
}
