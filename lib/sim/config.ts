import { hashStringToSeed } from '@/lib/sim/rng';

export type ScenarioId =
  | 'farm-road'
  | 'crop-corridor'
  | 'orchard-rows'
  | 'rough-field-edge'
  | 'hazard-dense'
  | 'mud-rain'
  | 'sunset-test';
export type WeatherId = 'clear' | 'dusty' | 'wet-ground' | 'light-rain' | 'sunset' | 'dawn-haze';
export type QualityPreset = 'low' | 'medium' | 'high';
export type ViewMode = 'world' | 'pointcloud' | 'hybrid' | 'bev' | 'depth';
export type PointColorMode = 'hazard' | 'depth' | 'class';
export type CameraMode = 'chase' | 'hood' | 'cinematic' | 'top' | 'lidar';

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
  pointColorMode: PointColorMode;
  hudVisible: boolean;
  minimapVisible: boolean;
  controlsOpen: boolean;
  cameraMode: CameraMode;
}

export const defaultSettings: SimulatorSettings = {
  seedText: 'agrolidar-flagship',
  seed: hashStringToSeed('agrolidar-flagship'),
  scenario: 'farm-road',
  weather: 'clear',
  quality: 'high',
  hazardDensity: 0.5,
  lidarRange: 70,
  lidarDensity: 0.68,
  paused: false,
  autopilot: false,
  viewMode: 'hybrid',
  pointColorMode: 'hazard',
  hudVisible: true,
  minimapVisible: true,
  controlsOpen: false,
  cameraMode: 'chase',
};
