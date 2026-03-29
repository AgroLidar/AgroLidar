import type { WeatherConfig } from '@/lib/sim/scenarios';
import type { HazardInfo } from '@/lib/sim/lidar/hazards';

export interface LidarConfig {
  range: number;
  horizontalFovDeg: number;
  channels: number;
  pointBudget: number;
  dropout: number;
}

export interface LidarPoint {
  x: number;
  y: number;
  z: number;
  hazard: boolean;
}

export function sampleLidarPoints(
  hazards: HazardInfo[],
  config: LidarConfig,
  scanPhase: number,
  weather: WeatherConfig,
): LidarPoint[] {
  const points: LidarPoint[] = [];
  const stride = Math.max(1, Math.floor(1 / (config.pointBudget / 10000)));
  for (let i = 0; i < hazards.length; i += stride) {
    const hazard = hazards[i];
    const repeats = hazard.obstacle.cls === 'human' || hazard.obstacle.cls === 'animal' ? 18 : 11;
    for (let p = 0; p < repeats; p += 1) {
      const jitter = (Math.sin(scanPhase * 6 + p) + Math.cos(i + p * 0.7)) * 0.05;
      const dropout = (Math.sin(i * 12.13 + p * 8.7 + scanPhase * 8) * 0.5 + 0.5) < config.dropout + weather.lidarNoise;
      if (dropout) continue;
      points.push({
        x: hazard.obstacle.x + Math.sin(p) * (hazard.obstacle.radius + jitter),
        y: hazard.obstacle.y + (p % config.channels) * 0.06,
        z: hazard.obstacle.z + Math.cos(p) * (hazard.obstacle.radius + jitter),
        hazard: hazard.risk !== 'SAFE',
      });
      if (points.length >= config.pointBudget) return points;
    }
  }
  return points;
}
