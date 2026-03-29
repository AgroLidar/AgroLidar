import * as THREE from 'three';
import type { LidarPoint } from '@/lib/sim/lidar/sensor';

export function pointsToBuffer(points: LidarPoint[]): THREE.BufferGeometry {
  const positions = new Float32Array(points.length * 3);
  const colors = new Float32Array(points.length * 3);
  points.forEach((point, idx) => {
    const i = idx * 3;
    positions[i] = point.x;
    positions[i + 1] = point.y;
    positions[i + 2] = point.z;
    colors[i] = point.hazard ? 1 : 0.2;
    colors[i + 1] = point.hazard ? 0.35 : 0.9;
    colors[i + 2] = point.hazard ? 0.1 : 1;
  });
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  return geometry;
}
