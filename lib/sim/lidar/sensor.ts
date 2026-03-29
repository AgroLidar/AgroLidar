import type { LidarMode } from '@/lib/sim/config';
import { clamp } from '@/lib/sim/math';
import type { WeatherConfig } from '@/lib/sim/scenarios';
import { ObstacleSpatialIndex } from '@/lib/sim/lidar/spatial-index';
import { sampleTerrainHeight } from '@/lib/sim/world/terrain';
import type { ObstacleClass, WorldObstacle } from '@/lib/sim/world/props';

export interface LidarConfig {
  range: number;
  horizontalFovDeg: number;
  channels: number;
  pointBudget: number;
  dropout: number;
  verticalFovDeg: number;
  rotationRateHz: number;
  mode: LidarMode;
  semanticColoring: boolean;
}

export interface LidarPoint {
  x: number;
  y: number;
  z: number;
  hazard: boolean;
  distance: number;
  cls: ObstacleClass | 'ground';
  intensity: number;
}

export interface LidarSampleResult {
  points: LidarPoint[];
  scanCoveragePct: number;
}

export interface LidarPose {
  x: number;
  y: number;
  z: number;
  heading: number;
  pitch: number;
  roll: number;
}

const verticalSpread = [-0.24, -0.2, -0.16, -0.12, -0.08, -0.04, -0.02, 0.01, 0.04, 0.08, 0.11, 0.15];

function intersectObstacleRay(ox: number, oz: number, dx: number, dz: number, obstacle: WorldObstacle): number | null {
  const cx = obstacle.x - ox;
  const cz = obstacle.z - oz;
  const proj = cx * dx + cz * dz;
  if (proj < 0) return null;
  const perpSq = cx * cx + cz * cz - proj * proj;
  const radiusSq = obstacle.radius * obstacle.radius;
  if (perpSq > radiusSq) return null;
  const hit = proj - Math.sqrt(Math.max(0, radiusSq - perpSq));
  return hit >= 0 ? hit : null;
}

function modeFov(config: LidarConfig): number {
  if (config.mode === 'spin-360') return 360;
  if (config.mode === 'forward-static') return Math.min(110, config.horizontalFovDeg);
  if (config.mode === 'survey-grid') return Math.max(220, config.horizontalFovDeg);
  if (config.mode === 'bev-hazard') return 180;
  return config.horizontalFovDeg;
}

export function sampleLidarPoints(
  nearbyObstacles: WorldObstacle[],
  config: LidarConfig,
  scanPhase: number,
  weather: WeatherConfig,
  pose: LidarPose,
  seed: number,
  spatialIndex: ObstacleSpatialIndex,
): LidarSampleResult {
  const points: LidarPoint[] = [];
  spatialIndex.reset(nearbyObstacles);

  const effectiveFov = modeFov(config);
  const densityBias = config.mode === 'survey-grid' ? 1.2 : config.mode === 'bev-hazard' ? 0.82 : 1;
  const azimuthCount = Math.max(110, Math.floor((config.pointBudget * densityBias) / Math.max(4, config.channels)));

  let raysCast = 0;
  let raysHit = 0;

  for (let az = 0; az < azimuthCount; az += 1) {
    const sweepOffset = scanPhase * config.rotationRateHz * 0.14;
    const sweep = (az / azimuthCount + sweepOffset) % 1;
    const yaw = (sweep - 0.5) * ((effectiveFov * Math.PI) / 180) + pose.heading;
    const dirX = Math.sin(yaw);
    const dirZ = Math.cos(yaw);
    const candidates = spatialIndex.queryCircle(pose.x + dirX * config.range * 0.45, pose.z + dirZ * config.range * 0.45, config.range * 0.72);

    for (let ch = 0; ch < config.channels; ch += 1) {
      if (points.length >= config.pointBudget) {
        return { points, scanCoveragePct: (raysHit / Math.max(1, raysCast)) * 100 };
      }

      const channelPitchScale = clamp(config.verticalFovDeg / 30, 0.4, 1.8);
      const beamVertical =
        verticalSpread[ch % verticalSpread.length] * channelPitchScale +
        Math.floor(ch / verticalSpread.length) * 0.01 +
        pose.pitch * 0.45;

      let hitDistance = config.range;
      let hitClass: LidarPoint['cls'] = 'ground';
      let hazard = false;
      let hitY = sampleTerrainHeight(pose.x + dirX * hitDistance, pose.z + dirZ * hitDistance, seed, 0.2);

      for (const obstacle of candidates) {
        const hit = intersectObstacleRay(pose.x, pose.z, dirX, dirZ, obstacle);
        if (hit === null || hit > hitDistance || hit > config.range) continue;
        const heightAtRay = pose.y + hit * beamVertical;
        const maxHeight = obstacle.y + obstacle.radius * (obstacle.cls === 'post' || obstacle.cls === 'pole' ? 3.3 : obstacle.cls === 'tree' ? 2.7 : 2.1);
        if (heightAtRay < obstacle.y - 0.45 || heightAtRay > maxHeight) continue;
        hitDistance = hit;
        hitClass = obstacle.cls;
        hazard = obstacle.hazard;
        hitY = clamp(heightAtRay, obstacle.y - 0.35, maxHeight);
      }

      if (hitClass === 'ground') {
        const step = config.range > 40 ? 2.8 : 2.2;
        for (let d = 4; d <= config.range; d += step) {
          const tx = pose.x + dirX * d;
          const tz = pose.z + dirZ * d;
          const terrainY = sampleTerrainHeight(tx, tz, seed, 0.24);
          const rayY = pose.y + d * beamVertical;
          if (rayY <= terrainY + 0.05) {
            hitDistance = d;
            hitY = terrainY;
            break;
          }
        }
      }

      const dropoutPhase = Math.sin((az + 1) * 0.19 + ch * 0.33 + scanPhase * 6.1) * 0.5 + 0.5;
      if (dropoutPhase < config.dropout + weather.lidarNoise * 0.9) continue;

      const wobble = Math.sin(az * 0.72 + ch * 1.13 + scanPhase * 10.5 + pose.roll) * 0.08;
      const distance = hitDistance + wobble;
      const px = pose.x + dirX * distance;
      const pz = pose.z + dirZ * distance;
      const intensityBoost = config.semanticColoring && hitClass !== 'ground' ? 0.25 : 0.12;
      const intensity = clamp(1 - distance / config.range + (hitClass === 'ground' ? 0.06 : intensityBoost), 0.06, 1);
      points.push({ x: px, y: hitY, z: pz, hazard, distance, cls: hitClass, intensity });
      raysCast += 1;
      if (hitClass !== 'ground') raysHit += 1;
    }
  }

  return { points, scanCoveragePct: (raysHit / Math.max(1, raysCast)) * 100 };
}
