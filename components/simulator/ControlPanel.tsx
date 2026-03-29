'use client';

import { hashStringToSeed } from '@/lib/sim/rng';
import { SCENARIOS, WEATHER_PRESETS } from '@/lib/sim/scenarios';
import { getStore, setSettings, useSimStore } from '@/lib/sim/store';

export function ControlPanel() {
  const settings = useSimStore((s) => s.settings);

  return (
    <>
      <div className="pointer-events-auto absolute bottom-3 left-1/2 z-30 flex -translate-x-1/2 items-center gap-2 rounded-full border border-white/20 bg-black/50 px-2 py-2 backdrop-blur-md sm:left-5 sm:translate-x-0">
        <QuickButton label="Reset" onClick={() => setSettings({ paused: false })} extraAction={() => window.dispatchEvent(new CustomEvent('sim-reset'))} />
        <QuickButton label="Camera" onClick={() => window.dispatchEvent(new CustomEvent('sim-camera-cycle'))} />
        <QuickButton label="LiDAR" onClick={() => window.dispatchEvent(new CustomEvent('sim-lidar-cycle'))} />
        <QuickButton label={settings.presentationMode ? '4K On' : '4K'} onClick={() => setSettings({ presentationMode: !settings.presentationMode, quality: !settings.presentationMode ? 'ultra' : 'high' })} />
        <QuickButton label={settings.hudVisible ? 'Hide HUD' : 'Show HUD'} onClick={() => setSettings({ hudVisible: !settings.hudVisible })} />
        <QuickButton label={settings.controlsOpen ? 'Close' : 'Controls'} onClick={() => setSettings({ controlsOpen: !settings.controlsOpen })} />
      </div>

      <aside className={`pointer-events-auto absolute right-3 top-14 z-30 w-[min(24rem,calc(100vw-1.5rem))] rounded-2xl border border-white/20 bg-black/55 p-3 text-xs shadow-2xl backdrop-blur-md transition-all duration-300 sm:top-5 sm:w-80 ${settings.controlsOpen ? 'max-h-[80vh] opacity-100' : 'max-h-11 overflow-hidden opacity-85'}`}>
        <button
          className="mb-2 flex w-full items-center justify-between text-left text-[11px] uppercase tracking-[0.14em] text-white/80"
          onClick={() => setSettings({ controlsOpen: !settings.controlsOpen })}
        >
          <span>Simulation Controls</span>
          <span>{settings.controlsOpen ? '−' : '+'}</span>
        </button>

        <div className="grid gap-2">
          <label className="text-[11px] text-white/70">Seed</label>
          <div className="flex gap-2">
            <input value={settings.seedText} onChange={(event) => setSettings({ seedText: event.target.value })} className="w-full rounded bg-black/45 px-2 py-1" />
            <button
              onClick={() => {
                const seed = hashStringToSeed(getStore().settings.seedText);
                setSettings({ seed, paused: false });
                window.dispatchEvent(new CustomEvent('sim-reset-world'));
              }}
              className="rounded bg-emerald-400 px-2 py-1 font-semibold text-black"
            >
              Regen
            </button>
          </div>
          <Select label="Scenario" value={settings.scenario} onChange={(value) => setSettings({ scenario: value as keyof typeof SCENARIOS })} options={Object.values(SCENARIOS).map((item) => ({ value: item.id, label: item.label }))} />
          <Select label="Weather" value={settings.weather} onChange={(value) => setSettings({ weather: value as keyof typeof WEATHER_PRESETS })} options={Object.values(WEATHER_PRESETS).map((item) => ({ value: item.id, label: item.label }))} />
          {settings.vehicle === 'drone' && <Select label="Mission" value={settings.droneMission} onChange={(value) => setSettings({ droneMission: value as 'spray' | 'spread' | 'lift' | 'survey' })} options={[{ value: 'spray', label: 'Spray' }, { value: 'spread', label: 'Spread' }, { value: 'lift', label: 'Lift' }, { value: 'survey', label: 'LiDAR Survey' }]} />}
          <Select label="Quality" value={settings.quality} onChange={(value) => setSettings({ quality: value as 'low' | 'medium' | 'high' | 'ultra' })} options={[{ value: 'low', label: 'Low' }, { value: 'medium', label: 'Medium' }, { value: 'high', label: 'High' }, { value: 'ultra', label: 'Ultra / Presentation' }]} />
          <Slider label="Render scale" min={0.65} max={1.25} step={0.05} value={settings.renderScale} onChange={(value) => setSettings({ renderScale: value })} />
          <Slider label="Hazard density" min={0} max={1} step={0.05} value={settings.hazardDensity} onChange={(value) => setSettings({ hazardDensity: value })} />
          <Slider label="LiDAR range" min={30} max={120} step={1} value={settings.lidarRange} onChange={(value) => setSettings({ lidarRange: value })} />
          <Slider label="LiDAR density" min={0.2} max={1} step={0.05} value={settings.lidarDensity} onChange={(value) => setSettings({ lidarDensity: value })} />
          <label className="mt-1 flex items-center gap-2 text-white/85">
            <input type="checkbox" checked={settings.autopilot} onChange={(event) => setSettings({ autopilot: event.target.checked })} />
            Autopilot
          </label>
          {settings.vehicle === 'drone' && <label className="mt-1 flex items-center gap-2 text-white/85"><input type="checkbox" checked={settings.terrainFollow} onChange={(event) => setSettings({ terrainFollow: event.target.checked })} />Terrain-follow</label>}
        </div>
      </aside>
    </>
  );
}

function QuickButton({ label, onClick, extraAction }: { label: string; onClick: () => void; extraAction?: () => void }) {
  return (
    <button
      onClick={() => {
        onClick();
        extraAction?.();
      }}
      className="rounded-full border border-white/20 bg-white/5 px-3 py-1 text-[10px] text-white/90 sm:text-xs"
    >
      {label}
    </button>
  );
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: Array<{ value: string; label: string }> }) {
  return (
    <label className="block text-white/70">
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)} className="mt-1 w-full rounded bg-black/45 px-2 py-1">
        {options.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </label>
  );
}

function Slider({ label, value, onChange, min, max, step }: { label: string; value: number; onChange: (value: number) => void; min: number; max: number; step: number }) {
  return (
    <label className="block text-white/70">
      {label}: {value.toFixed(2)}
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} className="mt-1 w-full" />
    </label>
  );
}
