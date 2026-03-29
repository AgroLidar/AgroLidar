'use client';

import { useSimStore } from '@/lib/sim/store';

export function Minimap() {
  const telemetry = useSimStore((s) => s.telemetry);

  return (
    <div className="rounded-lg border border-white/20 bg-black/60 p-3">
      <p className="mb-2 text-xs uppercase tracking-[0.12em] text-white/65">BEV Hazard</p>
      <svg viewBox="0 0 100 100" className="h-36 w-36 rounded bg-[#0b1118]">
        <rect x="44" y="72" width="12" height="18" fill="#14b8a6" />
        <circle cx="50" cy="48" r="7" fill={telemetry.risk === 'CRITICAL' ? '#ef4444' : telemetry.risk === 'CAUTION' ? '#f59e0b' : '#22c55e'} fillOpacity="0.25" />
        <circle cx="50" cy="48" r="2" fill="#f8fafc" />
      </svg>
    </div>
  );
}
