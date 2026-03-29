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

function classRiskWeight(obstacle: WorldObstacle): number {
  switch (obstacle.cls) {
    case 'human':
    case 'animal':
      return 1.35;
    case 'vehicle':
    case 'tractor':
    case 'machinery':
      return 1.2;
    case 'tree':
    case 'rock':
    case 'post':
    case 'pole':
      return 1.05;
    default:
      return 0.92;
  }
}

export function classifyRisk(distance: number, inForwardZone: boolean, obstacle: WorldObstacle): RiskLevel {
  const weight = classRiskWeight(obstacle);
  const critical = (inForwardZone ? 11 : 7.5) * weight;
  const caution = (inForwardZone ? 25 : 17) * weight;
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
      const sensingRadius = obstacle.sensingRadius ?? obstacle.radius;
      const distance = Math.hypot(ox, oz);
      const forwardDistance = ox * fx + oz * fz;
      const lateralOffset = Math.abs(ox * fz - oz * fx);
      const inForwardZone = forwardDistance > -2 && forwardDistance < range * 0.85 && lateralOffset < Math.max(2.6, sensingRadius + 1.8);
      return { obstacle, distance, forwardDistance, lateralOffset, inForwardZone, risk: classifyRisk(distance, inForwardZone, obstacle) };
    })
    .filter((item) => item.distance <= range)
    .sort((a, b) => {
      if (a.inForwardZone !== b.inForwardZone) return a.inForwardZone ? -1 : 1;
      return a.distance - b.distance;
    });
}
