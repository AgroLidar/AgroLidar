'use client';

import { useEffect, useMemo } from 'react';
import * as THREE from 'three';

import type { PointColorMode } from '@/lib/sim/config';
import type { LidarPoint } from '@/lib/sim/lidar/sensor';
import { pointsToBuffer } from '@/lib/sim/lidar/pointcloud';

export function LidarLayer({ points, visible, colorMode }: { points: LidarPoint[]; visible: boolean; colorMode: PointColorMode }) {
  const geometry = useMemo(() => pointsToBuffer(points, colorMode), [points, colorMode]);

  useEffect(() => () => geometry.dispose(), [geometry]);

  if (!visible) return null;

  return (
    <points geometry={geometry} frustumCulled={false}>
      <pointsMaterial
        size={0.15}
        vertexColors
        blending={THREE.AdditiveBlending}
        transparent
        opacity={0.92}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  );
}
