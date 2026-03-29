import { useSyncExternalStore } from 'react';

import { defaultSettings, type SimulatorSettings, type VehicleType, type DroneMissionMode } from '@/lib/sim/config';
import type { ObstacleClass } from '@/lib/sim/world/props';
import type { RiskLevel } from '@/lib/sim/lidar/hazards';
import type { MissionType } from '@/lib/sim/ops/missions';

export interface TelemetrySnapshot {
  speed: number;
  altitude: number;
  headingDeg: number;
  nearestHazard: number;
  risk: RiskLevel;
  pointCount: number;
  latencyMs: number;
  classes: ObstacleClass[];
  seed: number;
  scenarioLabel: string;
  cameraMode: string;
  frameRate: number;
  vehicle: VehicleType;
  droneMission: DroneMissionMode;
  payloadPct: number;
  coveragePct: number;
  routeProgressPct: number;
  missionType: MissionType;
  fieldParcel: string;
  terrainRoughness: number;
  depressionRisk: number;
  puddleRisk: number;
  filteredPointCount: number;
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
    altitude: 0,
    headingDeg: 0,
    nearestHazard: Infinity,
    risk: 'SAFE',
    pointCount: 0,
    latencyMs: 0,
    classes: [],
    seed: defaultSettings.seed,
    scenarioLabel: 'Farm Road',
    cameraMode: defaultSettings.cameraMode,
    frameRate: 0,
    vehicle: defaultSettings.vehicle,
    droneMission: defaultSettings.droneMission,
    payloadPct: 100,
    coveragePct: 0,
    routeProgressPct: 0,
    missionType: defaultSettings.missionType,
    fieldParcel: defaultSettings.fieldParcelId,
    terrainRoughness: 0,
    depressionRisk: 0,
    puddleRisk: 0,
    filteredPointCount: 0,
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
