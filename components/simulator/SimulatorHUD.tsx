'use client';

import { Minimap } from '@/components/simulator/Minimap';
import { useSimStore } from '@/lib/sim/store';

export function SimulatorHUD() {
  const telemetry = useSimStore((s) => s.telemetry);

  return (
    <section className="pointer-events-none absolute inset-0 flex flex-col justify-between p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="rounded-xl border border-white/20 bg-black/55 px-4 py-3 backdrop-blur">
          <p className="text-xs uppercase tracking-[0.14em] text-white/65">AgroLidar Perception</p>
          <p className="mt-1 text-lg font-semibold">{telemetry.risk}</p>
          <p className="text-xs text-white/70">Nearest hazard: {Number.isFinite(telemetry.nearestHazard) ? `${telemetry.nearestHazard.toFixed(1)}m` : '—'}</p>
          <p className="text-xs text-white/70">Speed: {Math.max(0, telemetry.speed).toFixed(1)} m/s</p>
          <p className="text-xs text-white/70">Points: {telemetry.pointCount.toLocaleString()}</p>
          <p className="text-xs text-white/70">Latency: {telemetry.latencyMs.toFixed(1)} ms</p>
          <p className="text-xs text-white/70">Seed: {telemetry.seed}</p>
          <p className="text-xs text-white/70">Scenario: {telemetry.scenarioLabel}</p>
          <p className="text-xs text-white/70">Classes: {telemetry.classes.join(', ') || 'none'}</p>
        </div>
        <Minimap />
      </div>
      <div className="self-center rounded-full border border-white/20 bg-black/45 px-4 py-2 text-xs text-white/75">
        W/S accelerate • A/D steer • Space stop • C camera • P pause • R reset
      </div>
    </section>
  );
}
