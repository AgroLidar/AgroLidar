'use client';

import { setSettings, useSimStore } from '@/lib/sim/store';
import type { VehicleType } from '@/lib/sim/config';

const vehicles: Array<{ id: VehicleType; label: string }> = [
  { id: 'tractor', label: 'Tractor' },
  { id: 'drone', label: 'Agro Drone' },
];

export function VehicleSelector() {
  const current = useSimStore((s) => s.settings.vehicle);

  return (
    <div className="pointer-events-auto absolute left-1/2 top-3 z-40 -translate-x-1/2 rounded-full border border-white/25 bg-black/55 p-1 backdrop-blur-md sm:top-5">
      <div className="flex items-center gap-1">
        {vehicles.map((vehicle) => (
          <button
            key={vehicle.id}
            onClick={() => setSettings({ vehicle: vehicle.id, cameraMode: vehicle.id === 'drone' ? 'drone-follow' : 'chase' })}
            className={`rounded-full px-3 py-1 text-[11px] sm:text-xs ${current === vehicle.id ? 'bg-emerald-400 text-black' : 'bg-white/10 text-white/85'}`}
          >
            {vehicle.label}
          </button>
        ))}
      </div>
    </div>
  );
}
