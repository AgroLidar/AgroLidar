'use client';

import { hashStringToSeed } from '@/lib/sim/rng';
import { SCENARIOS, WEATHER_PRESETS } from '@/lib/sim/scenarios';
import { getStore, setSettings, useSimStore } from '@/lib/sim/store';

export function ControlPanel() {
  const settings = useSimStore((s) => s.settings);

  return (
    <aside className="absolute bottom-5 right-5 w-80 rounded-xl border border-white/20 bg-black/65 p-4 text-sm backdrop-blur">
      <h2 className="mb-3 text-xs uppercase tracking-[0.12em] text-white/70">Simulation Controls</h2>
      <label className="mb-2 block text-xs text-white/70">Seed</label>
      <div className="mb-3 flex gap-2">
        <input
          value={settings.seedText}
          onChange={(event) => setSettings({ seedText: event.target.value })}
          className="w-full rounded bg-black/50 px-2 py-1 text-xs"
        />
        <button
          onClick={() => {
            const seed = hashStringToSeed(getStore().settings.seedText);
            setSettings({ seed, paused: false });
          }}
          className="rounded bg-emerald-400 px-2 py-1 text-xs font-semibold text-black"
        >
          Regen
        </button>
      </div>
      <Select label="Scenario" value={settings.scenario} onChange={(value) => setSettings({ scenario: value as keyof typeof SCENARIOS })} options={Object.values(SCENARIOS).map((item) => ({ value: item.id, label: item.label }))} />
      <Select label="Weather" value={settings.weather} onChange={(value) => setSettings({ weather: value as keyof typeof WEATHER_PRESETS })} options={Object.values(WEATHER_PRESETS).map((item) => ({ value: item.id, label: item.label }))} />
      <Select label="Quality" value={settings.quality} onChange={(value) => setSettings({ quality: value as 'low' | 'medium' | 'high' })} options={[{ value: 'low', label: 'Low' }, { value: 'medium', label: 'Medium' }, { value: 'high', label: 'High' }]} />
      <Slider label="Hazard density" min={0} max={1} step={0.05} value={settings.hazardDensity} onChange={(value) => setSettings({ hazardDensity: value })} />
      <Slider label="LiDAR range" min={25} max={100} step={1} value={settings.lidarRange} onChange={(value) => setSettings({ lidarRange: value })} />
      <Slider label="LiDAR density" min={0.2} max={1} step={0.05} value={settings.lidarDensity} onChange={(value) => setSettings({ lidarDensity: value })} />
      <label className="mt-3 flex items-center gap-2 text-xs text-white/80">
        <input type="checkbox" checked={settings.autopilot} onChange={(event) => setSettings({ autopilot: event.target.checked })} />
        Autopilot / cruise mode
      </label>
    </aside>
  );
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: Array<{ value: string; label: string }> }) {
  return (
    <label className="mb-2 block text-xs text-white/70">
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)} className="mt-1 w-full rounded bg-black/50 px-2 py-1 text-xs">
        {options.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </label>
  );
}

function Slider({ label, value, onChange, min, max, step }: { label: string; value: number; onChange: (value: number) => void; min: number; max: number; step: number }) {
  return (
    <label className="mb-2 block text-xs text-white/70">
      {label}: {value.toFixed(2)}
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} className="mt-1 w-full" />
    </label>
  );
}
