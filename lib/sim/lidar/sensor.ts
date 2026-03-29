import type { WeatherConfig } from '@/lib/sim/scenarios';
import type { ObstacleClass, WorldObstacle } from '@/lib/sim/world/props';
import { clamp } from '@/lib/sim/math';
import { sampleTerrainHeight } from '@/lib/sim/world/terrain';
import { ObstacleSpatialIndex } from '@/lib/sim/lidar/spatial-index';

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
  distance: number;
  cls: ObstacleClass | 'ground';
  intensity: number;
}

export interface LidarPose {
  x: number;
  y: number;
  z: number;
  heading: number;
  pitch?: number;
  roll?: number;
}

const verticalSpread = [-0.29, -0.24, -0.2, -0.16, -0.12, -0.08, -0.04, -0.01, 0.02, 0.06, 0.1, 0.14, 0.18];

interface HitResult {
  distance: number;
  cls: LidarPoint['cls'];
  y: number;
  hazard: boolean;
}

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

function resolveObstacleHit(pose: LidarPose, beamVertical: number, hit: number, obstacle: WorldObstacle): HitResult | null {
  const hitY = pose.y + hit * beamVertical;
  const obstacleTop = obstacle.y + (obstacle.height ?? obstacle.radius * 2.2);
  if (hitY < obstacle.y - 0.2 || hitY > obstacleTop + 0.1) return null;

  return {
    distance: hit,
    cls: obstacle.cls,
    hazard: obstacle.hazard,
    y: clamp(hitY, obstacle.y, obstacleTop),
  };
}

function resolveGroundHit(
  pose: LidarPose,
  dirX: number,
  dirZ: number,
  seed: number,
  range: number,
  beamVertical: number,
): HitResult {
  const stride = range > 65 ? 2.6 : 1.8;
  for (let d = 3.2; d <= range; d += stride) {
    const tx = pose.x + dirX * d;
    const tz = pose.z + dirZ * d;
    const terrainY = sampleTerrainHeight(tx, tz, seed, 0.24);
    const rayY = pose.y + d * beamVertical;
    if (rayY <= terrainY + 0.06) {
      return { distance: d, y: terrainY, cls: 'ground', hazard: false };
    }
  }

  const edgeX = pose.x + dirX * range;
  const edgeZ = pose.z + dirZ * range;
  return {
    distance: range,
    y: sampleTerrainHeight(edgeX, edgeZ, seed, 0.24),
    cls: 'ground',
    hazard: false,
  };
}

export function sampleLidarPoints(
  nearbyObstacles: WorldObstacle[],
  config: LidarConfig,
  scanPhase: number,
  weather: WeatherConfig,
  pose: LidarPose,
  seed: number,
  spatialIndex: ObstacleSpatialIndex,
): LidarPoint[] {
  const points: LidarPoint[] = [];
  spatialIndex.reset(nearbyObstacles);
  const channels = Math.max(8, config.channels);
  const azimuthCount = Math.max(140, Math.floor(config.pointBudget / Math.max(6, channels)));

  for (let az = 0; az < azimuthCount; az += 1) {
    const sweep = (az / azimuthCount + scanPhase * 0.26) % 1;
    const yaw = (sweep - 0.5) * (config.horizontalFovDeg * Math.PI / 180) + pose.heading;
    const dirX = Math.sin(yaw);
    const dirZ = Math.cos(yaw);

    const aheadBias = 0.45 + Math.abs(sweep - 0.5) * 0.35;
    const candidates = spatialIndex.queryCircle(
      pose.x + dirX * config.range * aheadBias,
      pose.z + dirZ * config.range * aheadBias,
      config.range * 0.7,
    );

    for (let ch = 0; ch < channels; ch += 1) {
      if (points.length >= config.pointBudget) return points;
      const channelBand = ch % verticalSpread.length;
      const upperBank = Math.floor(ch / verticalSpread.length);
      const beamVertical = verticalSpread[channelBand] + upperBank * 0.015 + (pose.pitch ?? 0) * 0.42;

      let bestHit: HitResult = resolveGroundHit(pose, dirX, dirZ, seed, config.range, beamVertical);

      for (const obstacle of candidates) {
        const hitDistance = intersectObstacleRay(pose.x, pose.z, dirX, dirZ, obstacle);
        if (hitDistance === null || hitDistance > bestHit.distance || hitDistance > config.range) continue;

        const candidate = resolveObstacleHit(pose, beamVertical, hitDistance, obstacle);
        if (!candidate) continue;
        bestHit = candidate;
      }

      const dropoutPhase = Math.sin((az + 1) * 0.2 + ch * 0.35 + scanPhase * 6.4) * 0.5 + 0.5;
      if (dropoutPhase < config.dropout + weather.lidarNoise * (bestHit.cls === 'ground' ? 0.65 : 1.05)) continue;

      const jitter = Math.sin(az * 0.74 + ch * 1.21 + scanPhase * 11.2 + (pose.roll ?? 0)) * 0.05;
      const distance = clamp(bestHit.distance + jitter, 0, config.range);
      const px = pose.x + dirX * distance;
      const pz = pose.z + dirZ * distance;
      const intensityBase = bestHit.cls === 'ground' ? 0.06 : bestHit.hazard ? 0.24 : 0.16;
      const intensity = clamp(1 - distance / config.range + intensityBase, 0.06, 1);

      points.push({
        x: px,
        y: bestHit.y,
        z: pz,
        hazard: bestHit.hazard,
        distance,
        cls: bestHit.cls,
        intensity,
      });
    }
  }

  return points;
}
