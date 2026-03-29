import { hashStringToSeed } from '@/lib/sim/rng';

export type ScenarioId =
  | 'farm-road'
  | 'crop-corridor'
  | 'orchard-rows'
  | 'rough-field-edge'
  | 'hazard-dense'
  | 'mud-rain'
  | 'sunset-test'
  | 'wet-stability';
export type WeatherId = 'clear' | 'dusty' | 'wet-ground' | 'light-rain' | 'sunset' | 'dawn-haze';
export type VehicleType = 'tractor' | 'drone';
export type DroneMissionMode = 'spray' | 'spread' | 'lift' | 'survey';
export type QualityPreset = 'low' | 'medium' | 'high' | 'ultra';
export type ViewMode = 'world' | 'pointcloud' | 'hybrid' | 'bev' | 'depth' | 'hazard';
export type PointColorMode = 'hazard' | 'depth' | 'class' | 'coverage';
export type LidarMode = 'spin-360' | 'sector-sweep' | 'forward-static' | 'survey-grid' | 'bev-hazard';
export type LidarRigPreset = 'hazard-short-range' | 'survey-rig' | 'dense-edge-rig' | 'wide-fov-rig' | 'performance-safe';
export type CameraMode =
  | 'chase'
  | 'hood'
  | 'cinematic'
  | 'top'
  | 'lidar'
  | 'debug-dynamics'
  | 'sensor-inspect'
  | 'drone-follow'
  | 'drone-mission'
  | 'drone-survey';

export interface SimulatorSettings {
  seedText: string;
  seed: number;
  scenario: ScenarioId;
  weather: WeatherId;
  vehicle: VehicleType;
  droneMission: DroneMissionMode;
  quality: QualityPreset;
  presentationMode: boolean;
  renderScale: number;
  hazardDensity: number;
  lidarRange: number;
  lidarDensity: number;
  lidarMode: LidarMode;
  lidarRigPreset: LidarRigPreset;
  paused: boolean;
  autopilot: boolean;
  terrainFollow: boolean;
  semanticColoring: boolean;
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
  vehicle: 'tractor',
  droneMission: 'survey',
  quality: 'high',
  presentationMode: false,
  renderScale: 1,
  hazardDensity: 0.5,
  lidarRange: 70,
  lidarDensity: 0.68,
  lidarMode: 'sector-sweep',
  lidarRigPreset: 'dense-edge-rig',
  paused: false,
  autopilot: false,
  terrainFollow: true,
  semanticColoring: true,
  viewMode: 'hybrid',
  pointColorMode: 'hazard',
  hudVisible: true,
  minimapVisible: true,
  controlsOpen: false,
  cameraMode: 'chase',
};

export function cameraModesForVehicle(vehicle: VehicleType): CameraMode[] {
  return vehicle === 'tractor'
    ? ['chase', 'hood', 'cinematic', 'top', 'lidar', 'debug-dynamics', 'sensor-inspect']
    : ['drone-follow', 'drone-mission', 'drone-survey', 'top', 'lidar', 'cinematic'];
}
