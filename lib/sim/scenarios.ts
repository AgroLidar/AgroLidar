import type { ScenarioId, WeatherId } from '@/lib/sim/config';

export interface ScenarioConfig {
  id: ScenarioId;
  label: string;
  terrainRoughness: number;
  pathWidth: number;
  cropRows: number;
  obstacleWeight: number;
  hazardWeight: number;
}

export interface WeatherConfig {
  id: WeatherId;
  label: string;
  fog: number;
  sky: string;
  groundWetness: number;
  lidarNoise: number;
  gripPenalty: number;
}

export const SCENARIOS: Record<ScenarioId, ScenarioConfig> = {
  'farm-road': { id: 'farm-road', label: 'Farm Road', terrainRoughness: 0.12, pathWidth: 10, cropRows: 4, obstacleWeight: 0.5, hazardWeight: 0.35 },
  'field-edge': { id: 'field-edge', label: 'Open Field Edge', terrainRoughness: 0.2, pathWidth: 12, cropRows: 6, obstacleWeight: 0.4, hazardWeight: 0.3 },
  orchard: { id: 'orchard', label: 'Orchard Rows', terrainRoughness: 0.15, pathWidth: 8, cropRows: 11, obstacleWeight: 0.55, hazardWeight: 0.45 },
  'rough-terrain': { id: 'rough-terrain', label: 'Rough Terrain', terrainRoughness: 0.4, pathWidth: 7, cropRows: 2, obstacleWeight: 0.8, hazardWeight: 0.6 },
  'hazard-dense': { id: 'hazard-dense', label: 'Hazard Dense Demo', terrainRoughness: 0.22, pathWidth: 9, cropRows: 5, obstacleWeight: 1.0, hazardWeight: 1.0 },
};

export const WEATHER_PRESETS: Record<WeatherId, WeatherConfig> = {
  clear: { id: 'clear', label: 'Clear', fog: 0.0015, sky: '#87b8ff', groundWetness: 0, lidarNoise: 0.02, gripPenalty: 0 },
  dusty: { id: 'dusty', label: 'Dusty', fog: 0.006, sky: '#c9b18d', groundWetness: 0.05, lidarNoise: 0.06, gripPenalty: 0.04 },
  rain: { id: 'rain', label: 'Light Rain / Wet Ground', fog: 0.004, sky: '#8ba0b6', groundWetness: 0.22, lidarNoise: 0.08, gripPenalty: 0.12 },
  sunset: { id: 'sunset', label: 'Sunset / Low Visibility', fog: 0.0035, sky: '#f0a366', groundWetness: 0.04, lidarNoise: 0.05, gripPenalty: 0.03 },
};

export function scenarioFromId(id: ScenarioId): ScenarioConfig {
  return SCENARIOS[id];
}

export function weatherFromId(id: WeatherId): WeatherConfig {
  return WEATHER_PRESETS[id];
}
