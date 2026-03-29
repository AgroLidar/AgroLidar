import type { WorldObstacle } from '@/lib/sim/world/props';

interface CellMap {
  [key: string]: WorldObstacle[];
}

export class ObstacleSpatialIndex {
  private readonly cells: CellMap = {};

  constructor(private readonly cellSize: number) {}

  reset(obstacles: WorldObstacle[]): void {
    for (const key of Object.keys(this.cells)) {
      delete this.cells[key];
    }
    for (const obstacle of obstacles) {
      const cx = Math.floor(obstacle.x / this.cellSize);
      const cz = Math.floor(obstacle.z / this.cellSize);
      const key = `${cx}:${cz}`;
      if (!this.cells[key]) this.cells[key] = [];
      this.cells[key].push(obstacle);
    }
  }

  queryCircle(x: number, z: number, radius: number): WorldObstacle[] {
    const minX = Math.floor((x - radius) / this.cellSize);
    const maxX = Math.floor((x + radius) / this.cellSize);
    const minZ = Math.floor((z - radius) / this.cellSize);
    const maxZ = Math.floor((z + radius) / this.cellSize);
    const result: WorldObstacle[] = [];
    for (let cz = minZ; cz <= maxZ; cz += 1) {
      for (let cx = minX; cx <= maxX; cx += 1) {
        const key = `${cx}:${cz}`;
        const bucket = this.cells[key];
        if (bucket) result.push(...bucket);
      }
    }
    return result;
  }
}
