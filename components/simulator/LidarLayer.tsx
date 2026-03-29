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

  const materialSize = colorMode === 'hazard' ? 0.19 : colorMode === 'class' ? 0.17 : 0.14;
  const opacity = colorMode === 'hazard' ? 0.96 : colorMode === 'depth' ? 0.88 : 0.92;

  return (
    <points geometry={geometry} frustumCulled={false}>
      <pointsMaterial
        size={materialSize}
        vertexColors
        blending={THREE.AdditiveBlending}
        transparent
        opacity={opacity}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  );
}
