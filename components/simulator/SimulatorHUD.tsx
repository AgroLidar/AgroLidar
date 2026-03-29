'use client';

import { Minimap } from '@/components/simulator/Minimap';
import { useSimStore } from '@/lib/sim/store';

export function SimulatorHUD() {
  const telemetry = useSimStore((s) => s.telemetry);
  const settings = useSimStore((s) => s.settings);

  if (!settings.hudVisible) return null;

  return (
    <section className="pointer-events-none absolute inset-0 p-3 sm:p-5">
      <div className="flex items-start justify-between gap-2 sm:gap-4">
        <div className="max-w-[74vw] rounded-2xl border border-white/20 bg-black/45 px-3 py-2 shadow-xl backdrop-blur-md sm:max-w-none sm:px-4 sm:py-3">
          <p className="text-[10px] uppercase tracking-[0.16em] text-white/65">AgroLidar Sim Ops · {telemetry.vehicle.toUpperCase()} · {telemetry.scenarioLabel}</p>
          <div className="mt-1 grid grid-cols-2 gap-x-3 gap-y-0.5 text-[11px] text-white/85 sm:grid-cols-3 sm:text-xs">
            <span className="font-semibold" style={{ color: telemetry.risk === 'CRITICAL' ? '#f87171' : telemetry.risk === 'CAUTION' ? '#fbbf24' : '#4ade80' }}>Risk: {telemetry.risk}</span>
            <span>Nearest: {Number.isFinite(telemetry.nearestHazard) ? `${telemetry.nearestHazard.toFixed(1)}m` : '—'}</span>
            <span>Speed: {Math.max(0, telemetry.speed).toFixed(1)} m/s</span>
            <span>Steer: {telemetry.steeringDeg.toFixed(1)}°</span>
            <span>Roll/Pitch: {telemetry.rollDeg.toFixed(1)}° / {telemetry.pitchDeg.toFixed(1)}°</span>
            <span>Surface: {telemetry.surfaceType}</span>
            <span>Traction: {telemetry.tractionPct.toFixed(0)}%</span>
            <span>Slip: {(telemetry.slipRatio * 100).toFixed(0)}%</span>
            <span>Suspension: {telemetry.suspensionActivityPct.toFixed(0)}%</span>
            <span>Stability: {telemetry.stabilityPct.toFixed(0)}%</span>
            <span>Points: {telemetry.pointCount.toLocaleString()}</span>
            <span>Latency: {telemetry.latencyMs.toFixed(1)} ms</span>
            <span>Scan hit ratio: {telemetry.scanCoveragePct.toFixed(0)}%</span>
            <span>LiDAR mode: {telemetry.lidarMode}</span>
            <span>Rig: {telemetry.lidarRigPreset}</span>
            <span>Camera: {telemetry.cameraMode}</span>
            <span>FPS: {telemetry.frameRate.toFixed(0)}</span>
            <span>Seed: {telemetry.seed}</span>
            {telemetry.vehicle === 'drone' && (
              <>
                <span>Mission: {telemetry.droneMission}</span>
                <span>Payload: {telemetry.payloadPct.toFixed(0)}%</span>
                <span>Coverage: {telemetry.coveragePct.toFixed(0)}%</span>
              </>
            )}
            <span className="col-span-2 sm:col-span-3 truncate">Classes: {telemetry.classes.join(', ') || 'none'}</span>
          </div>
        </div>
        <Minimap />
      </div>

      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full border border-white/15 bg-black/45 px-3 py-1 text-[10px] text-white/75 backdrop-blur sm:text-xs">
        W/S motion · A/D steer · Space ascend · Shift descend · Q/E yaw · V vehicle · C camera · L view · X LiDAR mode · H/M/P/R
      </div>
    </section>
  );
}
