import { noise2d, sampleTerrainHeight, sampleTerrainSurface } from '@/lib/sim/world/terrain';

export interface TerrainAnalytics {
  elevation: number;
  slopeMagnitude: number;
  depressionIndex: number;
  moistureIndex: number;
  puddleRisk: number;
  mudPocket: boolean;
}

export function sampleTerrainAnalytics(x: number, z: number, seed: number, roughness: number): TerrainAnalytics {
  const c = sampleTerrainHeight(x, z, seed, roughness);
  const ex = sampleTerrainHeight(x + 0.8, z, seed, roughness);
  const ez = sampleTerrainHeight(x, z + 0.8, seed, roughness);
  const slopeMagnitude = Math.hypot(ex - c, ez - c);

  const basinNoise = noise2d(x * 0.03, z * 0.03, seed ^ 0x44aa11cc) * 0.5 + 0.5;
  const depressionIndex = Math.max(0, (0.48 - basinNoise) * 2.4 + (0.32 - c) * 0.15);
  const moistureIndex = noise2d(x * 0.06, z * 0.06, seed ^ 0x12aa89cd) * 0.5 + 0.5;
  const surface = sampleTerrainSurface(x, z, seed);
  const puddleRisk = Math.min(1, depressionIndex * 0.72 + moistureIndex * 0.35 + (surface === 'wet' || surface === 'mud' ? 0.2 : 0));

  return {
    elevation: c,
    slopeMagnitude,
    depressionIndex,
    moistureIndex,
    puddleRisk,
    mudPocket: surface === 'mud' || puddleRisk > 0.76,
  };
}
