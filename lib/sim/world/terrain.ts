import { smoothstep } from '@/lib/sim/math';
import { createRng } from '@/lib/sim/rng';

export function noise2d(x: number, z: number, seed: number): number {
  const xi = Math.floor(x);
  const zi = Math.floor(z);
  const xf = x - xi;
  const zf = z - zi;

  const corner = (cx: number, cz: number): number => {
    const rng = createRng((seed ^ (cx * 374761393) ^ (cz * 668265263)) >>> 0);
    return rng() * 2 - 1;
  };

  const n00 = corner(xi, zi);
  const n10 = corner(xi + 1, zi);
  const n01 = corner(xi, zi + 1);
  const n11 = corner(xi + 1, zi + 1);
  const u = smoothstep(xf);
  const v = smoothstep(zf);
  const nx0 = n00 + (n10 - n00) * u;
  const nx1 = n01 + (n11 - n01) * u;
  return nx0 + (nx1 - nx0) * v;
}

export function sampleTerrainHeight(x: number, z: number, seed: number, roughness: number): number {
  const base = noise2d(x * 0.05, z * 0.05, seed) * 1.8;
  const detail = noise2d(x * 0.21, z * 0.21, seed ^ 0x9e3779b9) * 0.45;
  return (base + detail) * roughness * 4;
}
