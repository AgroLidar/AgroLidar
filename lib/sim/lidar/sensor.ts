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
}

const verticalSpread = [-0.2, -0.15, -0.11, -0.08, -0.05, -0.02, 0.02, 0.06, 0.1, 0.14, 0.18];

function intersectObstacleRay(
  ox: number,
  oz: number,
  dx: number,
  dz: number,
  obstacle: WorldObstacle,
): number | null {
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
  const azimuthCount = Math.max(80, Math.floor(config.pointBudget / Math.max(4, config.channels)));

  for (let az = 0; az < azimuthCount; az += 1) {
    const progress = (az / azimuthCount + scanPhase * 0.18) % 1;
    const yaw = (progress - 0.5) * (config.horizontalFovDeg * Math.PI / 180) + pose.heading;
    const dirX = Math.sin(yaw);
    const dirZ = Math.cos(yaw);
    const candidates = spatialIndex.queryCircle(pose.x + dirX * config.range * 0.5, pose.z + dirZ * config.range * 0.5, config.range * 0.6);

    for (let ch = 0; ch < config.channels; ch += 1) {
      if (points.length >= config.pointBudget) return points;
      const vertical = verticalSpread[ch % verticalSpread.length] + (Math.floor(ch / verticalSpread.length) * 0.01);
      let hitDistance = config.range;
      let hitClass: LidarPoint['cls'] = 'ground';
      let hazard = false;
      let hitY = sampleTerrainHeight(pose.x + dirX * hitDistance, pose.z + dirZ * hitDistance, seed, 0.2);

      for (const obstacle of candidates) {
        const hit = intersectObstacleRay(pose.x, pose.z, dirX, dirZ, obstacle);
        if (hit === null || hit > hitDistance || hit > config.range) continue;
        const heightAtRay = pose.y + hit * vertical;
        const maxHeight = obstacle.y + obstacle.radius * (obstacle.cls === 'post' ? 3.2 : 1.8);
        if (heightAtRay < obstacle.y - 0.4 || heightAtRay > maxHeight) continue;
        hitDistance = hit;
        hitClass = obstacle.cls;
        hazard = obstacle.hazard;
        hitY = clamp(heightAtRay, obstacle.y - 0.3, maxHeight);
      }

      if (hitClass === 'ground') {
        for (let d = 6; d <= config.range; d += 3.8) {
          const tx = pose.x + dirX * d;
          const tz = pose.z + dirZ * d;
          const terrainY = sampleTerrainHeight(tx, tz, seed, 0.24);
          const rayY = pose.y + d * vertical;
          if (rayY <= terrainY + 0.05) {
            hitDistance = d;
            hitY = terrainY;
            break;
          }
        }
      }

      const dropoutPhase = Math.sin((az + 1) * 0.23 + ch * 0.37 + scanPhase * 5.8) * 0.5 + 0.5;
      if (dropoutPhase < config.dropout + weather.lidarNoise * 0.9) continue;

      const depthJitter = (Math.sin((az + ch) * 1.37 + scanPhase * 11) * 0.5 + 0.5) * 0.18;
      const distance = hitDistance + depthJitter;
      const px = pose.x + dirX * distance;
      const pz = pose.z + dirZ * distance;
      const intensity = clamp(1 - distance / config.range + (hitClass === 'ground' ? 0.04 : 0.12), 0.08, 1);
      points.push({ x: px, y: hitY, z: pz, hazard, distance, cls: hitClass, intensity });
    }
  }

  return points;
}
