'use client';

import { useMemo } from 'react';

import type { DroneMissionMode } from '@/lib/sim/config';

export function DroneMissionOverlay({ mode, coverage }: { mode: DroneMissionMode; coverage: number }) {
  const tone = useMemo(() => {
    if (mode === 'spray') return 'from-emerald-300/40 to-emerald-600/5';
    if (mode === 'spread') return 'from-amber-300/40 to-amber-600/5';
    if (mode === 'lift') return 'from-slate-300/35 to-slate-700/5';
    return 'from-cyan-300/35 to-cyan-700/5';
  }, [mode]);

  return (
    <div className="pointer-events-none absolute inset-x-0 bottom-16 z-20 flex justify-center sm:bottom-20">
      <div className={`w-[min(70vw,28rem)] rounded-xl border border-white/20 bg-gradient-to-b ${tone} p-2 text-[11px] text-white/85 backdrop-blur-md`}>
        <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-[0.14em]">
          <span>Drone Mission</span>
          <span>{mode}</span>
        </div>
        <div className="h-2 rounded bg-white/10">
          <div className="h-2 rounded bg-cyan-300" style={{ width: `${coverage.toFixed(1)}%` }} />
        </div>
      </div>
    </div>
  );
}
