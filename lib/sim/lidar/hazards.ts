import type { WorldObstacle } from '@/lib/sim/world/props';

export type RiskLevel = 'SAFE' | 'CAUTION' | 'CRITICAL';

export interface HazardInfo {
  obstacle: WorldObstacle;
  distance: number;
  risk: RiskLevel;
}

export function classifyRisk(distance: number): RiskLevel {
  if (distance < 8) return 'CRITICAL';
  if (distance < 18) return 'CAUTION';
  return 'SAFE';
}

export function computeHazards(obstacles: WorldObstacle[], px: number, pz: number, range: number): HazardInfo[] {
  return obstacles
    .map((obstacle) => {
      const distance = Math.hypot(obstacle.x - px, obstacle.z - pz);
      return { obstacle, distance, risk: classifyRisk(distance) };
    })
    .filter((item) => item.distance <= range)
    .sort((a, b) => a.distance - b.distance);
}
