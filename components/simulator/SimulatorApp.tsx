'use client';

import { useEffect } from 'react';

import { ControlPanel } from '@/components/simulator/ControlPanel';
import { SimulatorCanvas } from '@/components/simulator/SimulatorCanvas';
import { SimulatorHUD } from '@/components/simulator/SimulatorHUD';

export function SimulatorApp() {
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  return (
    <main className="relative h-screen w-screen bg-black text-white">
      <SimulatorCanvas />
      <SimulatorHUD />
      <ControlPanel />
    </main>
  );
}
