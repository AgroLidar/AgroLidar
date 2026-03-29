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

const hazardClasses: WorldObstacle['cls'][] = ['human', 'animal', 'rock', 'post', 'pole', 'vehicle', 'tractor', 'field-boundary'];
const propClasses: WorldObstacle['cls'][] = ['hay-bale', 'tree', 'rock', 'fence-line', 'machinery'];

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
  const corridorBias = Math.sin((cx + cz) * 0.35 + seed * 0.00001) * 0.5 + 0.5;
  const count = Math.floor(sampleRange(rng, 10, 38) * (0.45 + scenario.obstacleWeight * 0.65 + hazardDensity * 0.55));
  const obstacles: WorldObstacle[] = [];

  for (let i = 0; i < count; i += 1) {
    const rowSnap = Math.floor(rng() * Math.max(2, scenario.cropRows));
    const rowSpacing = 4 + 1.8 * (1 - scenario.terrainRoughness);
    const x = cx * chunkSize + rng() * chunkSize;
    const rowAlignedZ = cz * chunkSize + rowSnap * rowSpacing + (rng() - 0.5) * 0.9;
    const freeZ = cz * chunkSize + rng() * chunkSize;
    const pathWeight = Math.abs((x % (scenario.pathWidth * 1.8)) - scenario.pathWidth * 0.9) / (scenario.pathWidth * 0.9);
    const z = pathWeight < 0.28 || corridorBias > 0.78 ? freeZ : rowAlignedZ;

    const isHazard = rng() < scenario.hazardWeight * (0.28 + hazardDensity * 0.8);
    const cls = isHazard ? hazardClasses[Math.floor(rng() * hazardClasses.length)] : propClasses[Math.floor(rng() * propClasses.length)];
    const radius =
      cls === 'vehicle' || cls === 'tractor' || cls === 'machinery' ? 2.4 :
      cls === 'human' ? 0.55 :
      cls === 'animal' ? 0.9 :
      cls === 'post' || cls === 'pole' ? 0.35 :
      cls === 'fence-line' || cls === 'field-boundary' ? 1.8 :
      cls === 'hay-bale' ? 1.15 :
      cls === 'tree' ? 1.65 :
      1.0;

    obstacles.push({
      id: `${cx}:${cz}:${i}`,
      cls,
      x,
      z,
      y: sampleTerrainHeight(x, z, seed, scenario.terrainRoughness) + (cls === 'post' || cls === 'pole' ? 0.6 : 0.2),
      radius,
      hazard: isHazard,
    });
  }

  return { key: `${cx}:${cz}`, cx, cz, obstacles };
}
