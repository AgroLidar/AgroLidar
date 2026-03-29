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
  const azimuthCount = Math.max(110, Math.floor(config.pointBudget / Math.max(4, config.channels)));

  for (let az = 0; az < azimuthCount; az += 1) {
    const sweep = (az / azimuthCount + scanPhase * 0.22) % 1;
    const yaw = (sweep - 0.5) * (config.horizontalFovDeg * Math.PI / 180) + pose.heading;
    const dirX = Math.sin(yaw);
    const dirZ = Math.cos(yaw);
    const candidates = spatialIndex.queryCircle(pose.x + dirX * config.range * 0.45, pose.z + dirZ * config.range * 0.45, config.range * 0.72);

    for (let ch = 0; ch < config.channels; ch += 1) {
      if (points.length >= config.pointBudget) return points;
      const beamVertical = verticalSpread[ch % verticalSpread.length] + Math.floor(ch / verticalSpread.length) * 0.01 + pose.pitch * 0.45;
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
      const intensity = clamp(1 - distance / config.range + (hitClass === 'ground' ? 0.06 : 0.18), 0.06, 1);
      points.push({ x: px, y: hitY, z: pz, hazard, distance, cls: hitClass, intensity });
    }
  }

  return points;
}
