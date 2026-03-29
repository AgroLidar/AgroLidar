import * as THREE from 'three';

import type { PointColorMode } from '@/lib/sim/config';
import type { LidarPoint } from '@/lib/sim/lidar/sensor';

function classColor(cls: LidarPoint['cls']): [number, number, number] {
  switch (cls) {
    case 'human': return [1, 0.26, 0.3];
    case 'animal': return [1, 0.72, 0.18];
    case 'vehicle':
    case 'machinery': return [0.44, 0.92, 1];
    case 'post': return [0.75, 0.9, 0.3];
    case 'tree': return [0.3, 0.88, 0.45];
    case 'hay-bale': return [0.93, 0.84, 0.35];
    case 'rock': return [0.82, 0.82, 0.88];
    default: return [0.35, 0.9, 1];
  }
}

export function pointsToBuffer(points: LidarPoint[], mode: PointColorMode): THREE.BufferGeometry {
  const positions = new Float32Array(points.length * 3);
  const colors = new Float32Array(points.length * 3);

  points.forEach((point, idx) => {
    const i = idx * 3;
    positions[i] = point.x;
    positions[i + 1] = point.y;
    positions[i + 2] = point.z;

    let r = 0.24;
    let g = 0.92;
    let b = 1;

    if (mode === 'class') {
      [r, g, b] = classColor(point.cls);
    } else if (mode === 'depth') {
      const t = Math.min(1, point.distance / 80);
      r = 0.2 + 0.8 * t;
      g = 1 - t * 0.55;
      b = 1 - t * 0.82;
    } else {
      r = point.hazard ? 1 : 0.22;
      g = point.hazard ? 0.34 : 0.85;
      b = point.hazard ? 0.12 : 1;
    }

    const boost = 0.7 + point.intensity * 0.6;
    colors[i] = Math.min(1, r * boost);
    colors[i + 1] = Math.min(1, g * boost);
    colors[i + 2] = Math.min(1, b * boost);
  });

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  return geometry;
}
