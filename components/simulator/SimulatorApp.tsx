'use client';

import { useEffect } from 'react';

import { ControlPanel } from '@/components/simulator/ControlPanel';
import { DroneMissionOverlay } from '@/components/simulator/missions/DroneMissionOverlay';
import { SimulatorCanvas } from '@/components/simulator/SimulatorCanvas';
import { SimulatorHUD } from '@/components/simulator/SimulatorHUD';
import { VehicleSelector } from '@/components/simulator/VehicleSelector';
import { useSimStore } from '@/lib/sim/store';

export function SimulatorApp() {
  const vehicle = useSimStore((s) => s.settings.vehicle);
  const mission = useSimStore((s) => s.settings.droneMission);
  const coverage = useSimStore((s) => s.telemetry.coveragePct);

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  return (
    <main className="relative h-screen w-screen bg-black text-white">
      <SimulatorCanvas />
      <VehicleSelector />
      {vehicle === 'drone' && <DroneMissionOverlay mode={mission} coverage={coverage} />}
      <SimulatorHUD />
      <ControlPanel />
    </main>
  );
}
