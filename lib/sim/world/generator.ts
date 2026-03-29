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

const hazardClasses: WorldObstacle['cls'][] = ['human', 'animal', 'rock', 'post', 'pole', 'vehicle', 'tractor'];
const propClasses: WorldObstacle['cls'][] = ['hay-bale', 'tree', 'rock', 'fence-line', 'machinery', 'field-boundary'];

function corridorCenterX(cz: number, seed: number, chunkSize: number): number {
  const bendA = Math.sin(cz * 0.72 + seed * 0.00021) * chunkSize * 0.18;
  const bendB = Math.sin(cz * 0.31 + seed * 0.00011) * chunkSize * 0.12;
  return bendA + bendB;
}

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
  const corridorCenter = corridorCenterX(cz, seed, chunkSize);
  const corridorWidth = Math.max(8.4, scenario.pathWidth * 1.08);
  const corridorClearance = corridorWidth * 0.72;
  const obstacleBudget = Math.floor(sampleRange(rng, 9, 24) * (0.52 + scenario.obstacleWeight * 0.36 + hazardDensity * 0.42));
  const obstacles: WorldObstacle[] = [];
  let hardHazardCount = 0;

  for (let i = 0; i < obstacleBudget; i += 1) {
    const x = cx * chunkSize + rng() * chunkSize;
    const chunkBaseZ = cz * chunkSize;
    const rowSnap = Math.floor(rng() * Math.max(2, scenario.cropRows));
    const rowSpacing = 3.4 + 1.5 * (1 - scenario.terrainRoughness);
    const rowAlignedZ = chunkBaseZ + rowSnap * rowSpacing + (rng() - 0.5) * 0.65;
    const freeZ = chunkBaseZ + rng() * chunkSize;

    const relativeX = x - (cx * chunkSize + chunkSize * 0.5 + corridorCenter);
    const corridorDistance = Math.abs(relativeX);
    const prefersCorridor = corridorDistance < corridorWidth * (0.36 + rng() * 0.22);
    const z = prefersCorridor ? freeZ : rowAlignedZ;

    if (corridorDistance < corridorClearance) {
      const corridorNoise = rng();
      if (corridorNoise < 0.84) continue;
    }

    const isHazard = rng() < scenario.hazardWeight * (0.14 + hazardDensity * 0.52);
    const cls = isHazard ? hazardClasses[Math.floor(rng() * hazardClasses.length)] : propClasses[Math.floor(rng() * propClasses.length)];

    if ((cls === 'vehicle' || cls === 'tractor' || cls === 'tree' || cls === 'rock') && hardHazardCount >= 3 && rng() < 0.82) continue;
    if (cls === 'vehicle' || cls === 'tractor' || cls === 'tree' || cls === 'rock') hardHazardCount += 1;

    const visualRadius =
      cls === 'vehicle' || cls === 'tractor' || cls === 'machinery' ? sampleRange(rng, 1.45, 2.15) :
      cls === 'human' ? sampleRange(rng, 0.28, 0.36) :
      cls === 'animal' ? sampleRange(rng, 0.38, 0.62) :
      cls === 'post' || cls === 'pole' ? sampleRange(rng, 0.09, 0.14) :
      cls === 'fence-line' || cls === 'field-boundary' ? sampleRange(rng, 0.62, 1.1) :
      cls === 'hay-bale' ? sampleRange(rng, 0.52, 0.8) :
      cls === 'tree' ? sampleRange(rng, 0.88, 1.5) :
      sampleRange(rng, 0.42, 0.95);

    const collisionRadius =
      cls === 'human' || cls === 'animal' ? visualRadius * 0.78 :
      cls === 'hay-bale' || cls === 'fence-line' || cls === 'field-boundary' ? visualRadius * 0.64 :
      cls === 'post' || cls === 'pole' ? visualRadius * 0.7 :
      cls === 'tree' || cls === 'rock' ? visualRadius * 0.8 :
      visualRadius * 0.86;

    const height =
      cls === 'human' ? sampleRange(rng, 1.55, 1.88) :
      cls === 'animal' ? sampleRange(rng, 0.95, 1.35) :
      cls === 'tree' ? sampleRange(rng, 4.8, 8.2) :
      cls === 'post' || cls === 'pole' ? sampleRange(rng, 1.2, 2.1) :
      cls === 'hay-bale' ? sampleRange(rng, 1, 1.5) :
      cls === 'vehicle' || cls === 'tractor' || cls === 'machinery' ? sampleRange(rng, 1.8, 2.8) :
      cls === 'fence-line' || cls === 'field-boundary' ? sampleRange(rng, 0.55, 0.9) :
      sampleRange(rng, 0.8, 1.5);

    const baseY = sampleTerrainHeight(x, z, seed, scenario.terrainRoughness);
    const collision =
      cls === 'fence-line' || cls === 'field-boundary' ? 'ghost' :
      cls === 'hay-bale' ? 'soft' :
      cls === 'human' || cls === 'animal' ? 'soft' :
      cls === 'post' || cls === 'pole' || cls === 'tree' || cls === 'rock' ? 'solid' : 'solid';

    obstacles.push({
      id: `${cx}:${cz}:${i}`,
      cls,
      x,
      z,
      y: baseY,
      radius: collisionRadius,
      sensingRadius: visualRadius,
      height,
      hazard: isHazard,
      variant: Math.floor(rng() * 4),
      collision,
    });
  }

  return { key: `${cx}:${cz}`, cx, cz, obstacles };
}
