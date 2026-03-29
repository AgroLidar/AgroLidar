import type { SensorMountId, SensorPresetId } from '@/lib/sim/lidar/presets';
import type { MissionType } from '@/lib/sim/ops/missions';
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
export type VehicleType = 'tractor' | 'drone';
export type DroneMissionMode = 'spray' | 'spread' | 'lift' | 'survey';
export type QualityPreset = 'low' | 'medium' | 'high' | 'ultra';
export type ViewMode = 'world' | 'pointcloud' | 'hybrid' | 'bev' | 'depth' | 'hazard';
export type PointColorMode = 'hazard' | 'depth' | 'class' | 'coverage';
export type CameraMode =
  | 'chase'
  | 'hood'
  | 'cinematic'
  | 'top'
  | 'lidar'
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
  sensorPreset: SensorPresetId;
  sensorMount: SensorMountId;
  missionType: MissionType;
  fieldParcelId: string;
  paused: boolean;
  autopilot: boolean;
  terrainFollow: boolean;
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
  hazardDensity: 0.34,
  lidarRange: 70,
  lidarDensity: 0.68,
  sensorPreset: 'hazard-sweep',
  sensorMount: 'tractor-mast',
  missionType: 'hazard-sweep',
  fieldParcelId: 'north-40',
  paused: false,
  autopilot: false,
  terrainFollow: true,
  viewMode: 'hybrid',
  pointColorMode: 'hazard',
  hudVisible: true,
  minimapVisible: true,
  controlsOpen: false,
  cameraMode: 'chase',
};

export function cameraModesForVehicle(vehicle: VehicleType): CameraMode[] {
  return vehicle === 'tractor'
    ? ['chase', 'hood', 'cinematic', 'top', 'lidar']
    : ['drone-follow', 'drone-mission', 'drone-survey', 'top', 'lidar', 'cinematic'];
}
