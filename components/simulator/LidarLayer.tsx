'use client';

import { useEffect, useMemo } from 'react';
import * as THREE from 'three';

import type { LidarPoint } from '@/lib/sim/lidar/sensor';
import { pointsToBuffer } from '@/lib/sim/lidar/pointcloud';

export function LidarLayer({ points, visible }: { points: LidarPoint[]; visible: boolean }) {
  const geometry = useMemo(() => pointsToBuffer(points), [points]);

  useEffect(() => () => geometry.dispose(), [geometry]);

  if (!visible) return null;

  return (
    <points geometry={geometry}>
      <pointsMaterial size={0.22} vertexColors blending={THREE.AdditiveBlending} transparent opacity={0.9} />
    </points>
  );
}
