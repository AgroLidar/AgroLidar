import type { ScenarioConfig } from '@/lib/sim/scenarios';
import { createRng, sampleRange } from '@/lib/sim/rng';
import { sampleTerrainHeight } from '@/lib/sim/world/terrain';
import type { WorldObstacle } from '@/lib/sim/world/props';

export interface ChunkData {
  key: string;
  cx: number;
  cz: number;
  obstacles: WorldObstacle[];
}

const hazardClasses: WorldObstacle['cls'][] = ['human', 'animal', 'rock', 'post', 'vehicle'];

export function generateChunk(
  seed: number,
  cx: number,
  cz: number,
  chunkSize: number,
  scenario: ScenarioConfig,
  hazardDensity: number,
): ChunkData {
  const combined = (seed ^ (cx * 92837111) ^ (cz * 689287499)) >>> 0;
  const rng = createRng(combined || 1);
  const count = Math.floor(sampleRange(rng, 6, 24) * (0.4 + scenario.obstacleWeight * 0.7 + hazardDensity));
  const obstacles: WorldObstacle[] = [];

  for (let i = 0; i < count; i += 1) {
    const x = cx * chunkSize + rng() * chunkSize;
    const z = cz * chunkSize + rng() * chunkSize;
    const isHazard = rng() < scenario.hazardWeight * (0.35 + hazardDensity * 0.75);
    const cls = isHazard
      ? hazardClasses[Math.floor(rng() * hazardClasses.length)]
      : (['hay', 'tree', 'rock', 'post'] as const)[Math.floor(rng() * 4)];
    const radius = cls === 'vehicle' ? 2.2 : cls === 'human' ? 0.7 : cls === 'animal' ? 1.1 : 1.4;
    obstacles.push({
      id: `${cx}:${cz}:${i}`,
      cls,
      x,
      z,
      y: sampleTerrainHeight(x, z, seed, scenario.terrainRoughness) + 0.2,
      radius,
      hazard: isHazard,
    });
  }

  return { key: `${cx}:${cz}`, cx, cz, obstacles };
}
