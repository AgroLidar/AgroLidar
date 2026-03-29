import type { WorldObstacle } from '@/lib/sim/world/props';

export type RiskLevel = 'SAFE' | 'CAUTION' | 'CRITICAL';

export interface HazardInfo {
  obstacle: WorldObstacle;
  distance: number;
  forwardDistance: number;
  lateralOffset: number;
  inForwardZone: boolean;
  risk: RiskLevel;
}

export function classifyRisk(distance: number, inForwardZone: boolean): RiskLevel {
  const critical = inForwardZone ? 10 : 7;
  const caution = inForwardZone ? 22 : 16;
  if (distance < critical) return 'CRITICAL';
  if (distance < caution) return 'CAUTION';
  return 'SAFE';
}

export function computeHazards(obstacles: WorldObstacle[], px: number, pz: number, range: number, heading = 0): HazardInfo[] {
  const fx = Math.sin(heading);
  const fz = Math.cos(heading);
  return obstacles
    .map((obstacle) => {
      const ox = obstacle.x - px;
      const oz = obstacle.z - pz;
      const distance = Math.hypot(ox, oz);
      const forwardDistance = ox * fx + oz * fz;
      const lateralOffset = Math.abs(ox * fz - oz * fx);
      const inForwardZone = forwardDistance > -1 && forwardDistance < range * 0.75 && lateralOffset < Math.max(2.5, obstacle.radius + 2);
      return { obstacle, distance, forwardDistance, lateralOffset, inForwardZone, risk: classifyRisk(distance, inForwardZone) };
    })
    .filter((item) => item.distance <= range)
    .sort((a, b) => {
      if (a.inForwardZone !== b.inForwardZone) return a.inForwardZone ? -1 : 1;
      return a.distance - b.distance;
    });
}
