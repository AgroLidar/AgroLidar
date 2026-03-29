import { hashStringToSeed } from '@/lib/sim/rng';

export type ScenarioId = 'farm-road' | 'field-edge' | 'orchard' | 'rough-terrain' | 'hazard-dense';
export type WeatherId = 'clear' | 'dusty' | 'rain' | 'sunset';
export type QualityPreset = 'low' | 'medium' | 'high';
export type ViewMode = 'raw' | 'pointcloud' | 'hybrid' | 'bev';

export interface SimulatorSettings {
  seedText: string;
  seed: number;
  scenario: ScenarioId;
  weather: WeatherId;
  quality: QualityPreset;
  hazardDensity: number;
  lidarRange: number;
  lidarDensity: number;
  paused: boolean;
  autopilot: boolean;
  viewMode: ViewMode;
}

export const defaultSettings: SimulatorSettings = {
  seedText: 'agrolidar-001',
  seed: hashStringToSeed('agrolidar-001'),
  scenario: 'farm-road',
  weather: 'clear',
  quality: 'high',
  hazardDensity: 0.5,
  lidarRange: 55,
  lidarDensity: 0.6,
  paused: false,
  autopilot: false,
  viewMode: 'hybrid',
};
