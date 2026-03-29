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

  const materialSize = colorMode === 'hazard' ? 0.24 : colorMode === 'class' ? 0.2 : 0.18;
  const opacity = colorMode === 'hazard' ? 0.98 : colorMode === 'depth' ? 0.9 : 0.94;

  return (
    <points geometry={geometry} frustumCulled={false}>
      <pointsMaterial
        size={materialSize}
        vertexColors
        blending={colorMode === 'hazard' ? THREE.AdditiveBlending : THREE.NormalBlending}
        transparent
        opacity={opacity}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  );
}
