import type { ScenarioConfig } from '@/lib/sim/scenarios';
import type { ChunkData } from '@/lib/sim/world/generator';
import { generateChunk } from '@/lib/sim/world/generator';

export class ChunkManager {
  private chunks = new Map<string, ChunkData>();

  constructor(private readonly chunkSize: number, private readonly radius: number) {}

  getActiveChunks(seed: number, px: number, pz: number, scenario: ScenarioConfig, hazardDensity: number): ChunkData[] {
    const centerX = Math.floor(px / this.chunkSize);
    const centerZ = Math.floor(pz / this.chunkSize);
    const required = new Set<string>();

    for (let dz = -this.radius; dz <= this.radius; dz += 1) {
      for (let dx = -this.radius; dx <= this.radius; dx += 1) {
        const cx = centerX + dx;
        const cz = centerZ + dz;
        const key = `${cx}:${cz}`;
        required.add(key);
        if (!this.chunks.has(key)) {
          this.chunks.set(key, generateChunk(seed, cx, cz, this.chunkSize, scenario, hazardDensity));
        }
      }
    }

    for (const existing of this.chunks.keys()) {
      if (!required.has(existing)) {
        this.chunks.delete(existing);
      }
    }

    return Array.from(this.chunks.values());
  }

  reset(): void {
    this.chunks.clear();
  }
}
