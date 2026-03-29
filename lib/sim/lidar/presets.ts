import { clamp } from '@/lib/sim/math';

export type SensorPresetId =
  | 'hazard-sweep'
  | 'survey'
  | 'fast-performance'
  | 'dense-precision'
  | 'low-cost-open-simple';

export type SensorMountId = 'tractor-mast' | 'hood-forward';

export interface SensorPreset {
  id: SensorPresetId;
  label: string;
  range: number;
  channels: number;
  pointBudget: number;
  dropout: number;
  scanRateHz: number;
  horizontalFovDeg: number;
  verticalSpreadScale: number;
}

export interface SensorMount {
  id: SensorMountId;
  label: string;
  forwardOffset: number;
  heightOffset: number;
  lateralOffset: number;
  tilt: number;
  yawBias: number;
}

export const SENSOR_PRESETS: Record<SensorPresetId, SensorPreset> = {
  'hazard-sweep': { id: 'hazard-sweep', label: 'Hazard Sweep', range: 70, channels: 30, pointBudget: 22000, dropout: 0.02, scanRateHz: 14, horizontalFovDeg: 140, verticalSpreadScale: 1 },
  survey: { id: 'survey', label: 'Survey', range: 95, channels: 36, pointBudget: 30000, dropout: 0.028, scanRateHz: 11, horizontalFovDeg: 170, verticalSpreadScale: 1.1 },
  'fast-performance': { id: 'fast-performance', label: 'Fast Performance', range: 60, channels: 16, pointBudget: 12000, dropout: 0.04, scanRateHz: 18, horizontalFovDeg: 120, verticalSpreadScale: 0.92 },
  'dense-precision': { id: 'dense-precision', label: 'Dense Precision', range: 85, channels: 48, pointBudget: 42000, dropout: 0.014, scanRateHz: 9, horizontalFovDeg: 150, verticalSpreadScale: 1.18 },
  'low-cost-open-simple': {
    id: 'low-cost-open-simple',
    label: 'Low-Cost / OpenSimple',
    range: 45,
    channels: 12,
    pointBudget: 7600,
    dropout: 0.08,
    scanRateHz: 20,
    horizontalFovDeg: 110,
    verticalSpreadScale: 0.76,
  },
};

export const SENSOR_MOUNTS: Record<SensorMountId, SensorMount> = {
  'tractor-mast': { id: 'tractor-mast', label: 'Tractor Mast', forwardOffset: 1.18, heightOffset: 2.55, lateralOffset: 0, tilt: -0.015, yawBias: 0 },
  'hood-forward': { id: 'hood-forward', label: 'Hood Forward', forwardOffset: 1.54, heightOffset: 2.12, lateralOffset: 0.04, tilt: -0.03, yawBias: 0.006 },
};

export function blendPresetRange(base: SensorPreset, overrideRange: number, density: number): SensorPreset {
  const blended = clamp(overrideRange, 30, 140);
  const densityScale = clamp(density, 0.2, 1);
  return {
    ...base,
    range: blended,
    pointBudget: Math.floor(base.pointBudget * densityScale),
    dropout: clamp(base.dropout + (1 - densityScale) * 0.06, 0.01, 0.18),
  };
}
