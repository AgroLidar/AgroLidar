import { useSyncExternalStore } from 'react';

import { defaultSettings, type SimulatorSettings } from '@/lib/sim/config';
import type { ObstacleClass } from '@/lib/sim/world/props';
import type { RiskLevel } from '@/lib/sim/lidar/hazards';

export interface TelemetrySnapshot {
  speed: number;
  nearestHazard: number;
  risk: RiskLevel;
  pointCount: number;
  latencyMs: number;
  classes: ObstacleClass[];
  seed: number;
  scenarioLabel: string;
  cameraMode: string;
  frameRate: number;
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
    cameraMode: defaultSettings.cameraMode,
    frameRate: 0,
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
