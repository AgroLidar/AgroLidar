'use client';

import { useSimStore } from '@/lib/sim/store';

export function Minimap() {
  const telemetry = useSimStore((s) => s.telemetry);
  const settings = useSimStore((s) => s.settings);

  if (!settings.minimapVisible) return null;

  const riskColor = telemetry.risk === 'CRITICAL' ? '#ef4444' : telemetry.risk === 'CAUTION' ? '#f59e0b' : '#22c55e';

  return (
    <div className="pointer-events-auto rounded-2xl border border-white/20 bg-black/50 p-2 shadow-xl backdrop-blur-md">
      <p className="px-1 text-[10px] uppercase tracking-[0.15em] text-white/65">{settings.vehicle === 'drone' ? 'Mission Map' : 'BEV'}</p>
      <svg viewBox="0 0 100 100" className="h-24 w-24 rounded-lg bg-[#0a1220] sm:h-28 sm:w-28">
        <rect x="45" y="74" width="10" height="16" fill={settings.vehicle === 'drone' ? '#60a5fa' : '#3dd6d0'} />
        <path d="M50 76 L24 18 L76 18 Z" fill="url(#scan)" fillOpacity="0.32" />
        <circle cx="50" cy="46" r="8" fill={riskColor} fillOpacity="0.25" />
        <circle cx="50" cy="46" r="2.3" fill="#f8fafc" />
        {settings.vehicle === 'drone' && <rect x="24" y="24" width="52" height="52" fill="none" stroke="#38bdf8" strokeDasharray="2 2" opacity="0.7" />}
        <defs>
          <linearGradient id="scan" x1="50" y1="76" x2="50" y2="20">
            <stop offset="0" stopColor="#34d399" stopOpacity="0.6" />
            <stop offset="1" stopColor="#34d399" stopOpacity="0.06" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
}
