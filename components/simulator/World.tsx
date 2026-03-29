'use client';

import { useMemo } from 'react';
import { InstancedMesh, Object3D } from 'three';

import type { ChunkData } from '@/lib/sim/world/generator';

interface WorldProps {
  chunks: ChunkData[];
  weatherSky: string;
}

const dummy = new Object3D();

export function World({ chunks, weatherSky }: WorldProps) {
  const obstacles = useMemo(() => chunks.flatMap((chunk) => chunk.obstacles), [chunks]);

  return (
    <>
      <color attach="background" args={[weatherSky]} />
      <fog attach="fog" args={[weatherSky, 35, 170]} />
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[5000, 5000]} />
        <meshStandardMaterial color="#2f3c2a" roughness={1} metalness={0} />
      </mesh>
      <instancedMesh
        ref={(mesh) => {
          if (!mesh) return;
          obstacles.forEach((obstacle, index) => {
            dummy.position.set(obstacle.x, obstacle.y + obstacle.radius * 0.4, obstacle.z);
            dummy.scale.set(obstacle.radius, obstacle.radius * 1.2, obstacle.radius);
            dummy.updateMatrix();
            (mesh as InstancedMesh).setMatrixAt(index, dummy.matrix);
          });
          (mesh as InstancedMesh).instanceMatrix.needsUpdate = true;
        }}
        args={[undefined, undefined, obstacles.length]}
        castShadow
      >
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color="#9ca3af" />
      </instancedMesh>
    </>
  );
}
