import { useSyncExternalStore } from 'react';

import {
  defaultSettings,
  type DroneMissionMode,
  type LidarMode,
  type LidarRigPreset,
  type VehicleType,
} from '@/lib/sim/config';
import type { RiskLevel } from '@/lib/sim/lidar/hazards';
import type { ObstacleClass } from '@/lib/sim/world/props';

export interface TelemetrySnapshot {
  speed: number;
  altitude: number;
  headingDeg: number;
  steeringDeg: number;
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
  surfaceType: string;
  slipRatio: number;
  tractionPct: number;
  rollDeg: number;
  pitchDeg: number;
  suspensionActivityPct: number;
  stabilityPct: number;
  lidarMode: LidarMode;
  lidarRigPreset: LidarRigPreset;
  scanCoveragePct: number;
}

interface SimStore {
  settings: typeof defaultSettings;
  telemetry: TelemetrySnapshot;
}

type Listener = () => void;

const state: SimStore = {
  settings: defaultSettings,
  telemetry: {
    speed: 0,
    altitude: 0,
    headingDeg: 0,
    steeringDeg: 0,
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
    surfaceType: 'dirt',
    slipRatio: 0,
    tractionPct: 100,
    rollDeg: 0,
    pitchDeg: 0,
    suspensionActivityPct: 0,
    stabilityPct: 100,
    lidarMode: defaultSettings.lidarMode,
    lidarRigPreset: defaultSettings.lidarRigPreset,
    scanCoveragePct: 0,
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

export function setSettings(next: Partial<typeof defaultSettings>): void {
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
