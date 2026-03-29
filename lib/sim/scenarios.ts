import type { CameraMode, LidarMode, LidarRigPreset, ScenarioId, WeatherId } from '@/lib/sim/config';

export interface ScenarioConfig {
  id: ScenarioId;
  label: string;
  terrainRoughness: number;
  pathWidth: number;
  cropRows: number;
  obstacleWeight: number;
  hazardWeight: number;
  mud: number;
  slopeBias: number;
  surfaceMix: {
    dirt: number;
    grass: number;
    mud: number;
    wet: number;
  };
  defaults: {
    weather: WeatherId;
    lidarMode: LidarMode;
    lidarRigPreset: LidarRigPreset;
    cameraMode: CameraMode;
  };
}

export interface WeatherConfig {
  id: WeatherId;
  label: string;
  fog: number;
  sky: string;
  groundWetness: number;
  lidarNoise: number;
  gripPenalty: number;
  ambient: number;
  sun: number;
}

export const SCENARIOS: Record<ScenarioId, ScenarioConfig> = {
  'farm-road': {
    id: 'farm-road',
    label: 'Farm Road Evaluation',
    terrainRoughness: 0.12,
    pathWidth: 11,
    cropRows: 5,
    obstacleWeight: 0.55,
    hazardWeight: 0.35,
    mud: 0.15,
    slopeBias: 0.18,
    surfaceMix: { dirt: 0.45, grass: 0.35, mud: 0.1, wet: 0.1 },
    defaults: { weather: 'clear', lidarMode: 'sector-sweep', lidarRigPreset: 'dense-edge-rig', cameraMode: 'chase' },
  },
  'crop-corridor': {
    id: 'crop-corridor',
    label: 'Crop Corridor Hazard Detection',
    terrainRoughness: 0.16,
    pathWidth: 7,
    cropRows: 12,
    obstacleWeight: 0.48,
    hazardWeight: 0.38,
    mud: 0.25,
    slopeBias: 0.25,
    surfaceMix: { dirt: 0.28, grass: 0.42, mud: 0.18, wet: 0.12 },
    defaults: { weather: 'dusty', lidarMode: 'forward-static', lidarRigPreset: 'hazard-short-range', cameraMode: 'hood' },
  },
  'orchard-rows': {
    id: 'orchard-rows',
    label: 'Orchard Post Detection',
    terrainRoughness: 0.18,
    pathWidth: 8,
    cropRows: 10,
    obstacleWeight: 0.62,
    hazardWeight: 0.46,
    mud: 0.2,
    slopeBias: 0.22,
    surfaceMix: { dirt: 0.36, grass: 0.38, mud: 0.14, wet: 0.12 },
    defaults: { weather: 'clear', lidarMode: 'spin-360', lidarRigPreset: 'wide-fov-rig', cameraMode: 'sensor-inspect' },
  },
  'rough-field-edge': {
    id: 'rough-field-edge',
    label: 'Rough Terrain Dynamics Test',
    terrainRoughness: 0.42,
    pathWidth: 8,
    cropRows: 4,
    obstacleWeight: 0.8,
    hazardWeight: 0.62,
    mud: 0.35,
    slopeBias: 0.45,
    surfaceMix: { dirt: 0.2, grass: 0.26, mud: 0.32, wet: 0.22 },
    defaults: { weather: 'dawn-haze', lidarMode: 'sector-sweep', lidarRigPreset: 'performance-safe', cameraMode: 'debug-dynamics' },
  },
  'hazard-dense': {
    id: 'hazard-dense',
    label: 'Dense Hazard Validation',
    terrainRoughness: 0.24,
    pathWidth: 9,
    cropRows: 8,
    obstacleWeight: 1,
    hazardWeight: 1,
    mud: 0.3,
    slopeBias: 0.3,
    surfaceMix: { dirt: 0.24, grass: 0.36, mud: 0.22, wet: 0.18 },
    defaults: { weather: 'dusty', lidarMode: 'spin-360', lidarRigPreset: 'dense-edge-rig', cameraMode: 'top' },
  },
  'mud-rain': {
    id: 'mud-rain',
    label: 'Mud / Rain Stability Test',
    terrainRoughness: 0.28,
    pathWidth: 10,
    cropRows: 6,
    obstacleWeight: 0.74,
    hazardWeight: 0.58,
    mud: 0.82,
    slopeBias: 0.36,
    surfaceMix: { dirt: 0.08, grass: 0.18, mud: 0.44, wet: 0.3 },
    defaults: { weather: 'light-rain', lidarMode: 'forward-static', lidarRigPreset: 'hazard-short-range', cameraMode: 'chase' },
  },
  'sunset-test': {
    id: 'sunset-test',
    label: 'Sunset Visibility LiDAR Test',
    terrainRoughness: 0.14,
    pathWidth: 10,
    cropRows: 9,
    obstacleWeight: 0.58,
    hazardWeight: 0.42,
    mud: 0.18,
    slopeBias: 0.2,
    surfaceMix: { dirt: 0.34, grass: 0.34, mud: 0.12, wet: 0.2 },
    defaults: { weather: 'sunset', lidarMode: 'survey-grid', lidarRigPreset: 'survey-rig', cameraMode: 'cinematic' },
  },
  'wet-stability': {
    id: 'wet-stability',
    label: 'Wet Ground Stability Benchmark',
    terrainRoughness: 0.2,
    pathWidth: 9,
    cropRows: 6,
    obstacleWeight: 0.66,
    hazardWeight: 0.5,
    mud: 0.62,
    slopeBias: 0.28,
    surfaceMix: { dirt: 0.18, grass: 0.22, mud: 0.24, wet: 0.36 },
    defaults: { weather: 'wet-ground', lidarMode: 'bev-hazard', lidarRigPreset: 'hazard-short-range', cameraMode: 'debug-dynamics' },
  },
};

export const WEATHER_PRESETS: Record<WeatherId, WeatherConfig> = {
  clear: { id: 'clear', label: 'Clear', fog: 0.0014, sky: '#8dc1ff', groundWetness: 0.02, lidarNoise: 0.01, gripPenalty: 0, ambient: 0.48, sun: 1.1 },
  dusty: { id: 'dusty', label: 'Dusty', fog: 0.0058, sky: '#cfb38c', groundWetness: 0.1, lidarNoise: 0.07, gripPenalty: 0.05, ambient: 0.43, sun: 1.0 },
  'wet-ground': { id: 'wet-ground', label: 'Wet Ground', fog: 0.0026, sky: '#9ab4c7', groundWetness: 0.38, lidarNoise: 0.04, gripPenalty: 0.12, ambient: 0.44, sun: 0.92 },
  'light-rain': { id: 'light-rain', label: 'Light Rain', fog: 0.0042, sky: '#8398ad', groundWetness: 0.58, lidarNoise: 0.09, gripPenalty: 0.18, ambient: 0.36, sun: 0.76 },
  sunset: { id: 'sunset', label: 'Sunset', fog: 0.0032, sky: '#ec9f5e', groundWetness: 0.14, lidarNoise: 0.05, gripPenalty: 0.04, ambient: 0.4, sun: 0.88 },
  'dawn-haze': { id: 'dawn-haze', label: 'Dawn Haze', fog: 0.0045, sky: '#b6b2c8', groundWetness: 0.26, lidarNoise: 0.06, gripPenalty: 0.08, ambient: 0.4, sun: 0.82 },
};

export function scenarioFromId(id: ScenarioId): ScenarioConfig {
  return SCENARIOS[id];
}

export function weatherFromId(id: WeatherId): WeatherConfig {
  return WEATHER_PRESETS[id];
}
