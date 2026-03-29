import { useSyncExternalStore } from 'react';

import { defaultSettings, type SimulatorSettings } from '@/lib/sim/config';
import type { RiskLevel } from '@/lib/sim/lidar/hazards';

export interface TelemetrySnapshot {
  speed: number;
  nearestHazard: number;
  risk: RiskLevel;
  pointCount: number;
  latencyMs: number;
  classes: string[];
  seed: number;
  scenarioLabel: string;
}

interface SimStore {
  settings: SimulatorSettings;
  telemetry: TelemetrySnapshot;
}

type Listener = () => void;

const state: SimStore = {
  settings: defaultSettings,
  telemetry: {
    speed: 0,
    nearestHazard: Infinity,
    risk: 'SAFE',
    pointCount: 0,
    latencyMs: 0,
    classes: [],
    seed: defaultSettings.seed,
    scenarioLabel: 'Farm Road',
  },
};

const listeners = new Set<Listener>();

function emit(): void {
  listeners.forEach((listener) => listener());
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getStore(): SimStore {
  return state;
}

export function setSettings(next: Partial<SimulatorSettings>): void {
  state.settings = { ...state.settings, ...next };
  emit();
}

export function setTelemetry(next: Partial<TelemetrySnapshot>): void {
  state.telemetry = { ...state.telemetry, ...next };
  emit();
}

export function useSimStore<T>(selector: (snapshot: SimStore) => T): T {
  return useSyncExternalStore(subscribe, () => selector(state), () => selector(state));
}
