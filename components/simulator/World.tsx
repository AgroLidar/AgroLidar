'use client';

import { useMemo } from 'react';

import type { ChunkData } from '@/lib/sim/world/generator';
import { sampleTerrainHeight, sampleTerrainSurface } from '@/lib/sim/world/terrain';

interface WorldProps {
  chunks: ChunkData[];
  weatherSky: string;
  seed: number;
  terrainRoughness: number;
  wetness: number;
  viewMode: 'world' | 'pointcloud' | 'hybrid' | 'bev' | 'depth' | 'hazard';
}

export function World({ chunks, weatherSky, seed, terrainRoughness, wetness, viewMode }: WorldProps) {
  const obstacles = useMemo(() => chunks.flatMap((chunk) => chunk.obstacles), [chunks]);
  const dimmed = viewMode === 'pointcloud' || viewMode === 'bev' || viewMode === 'hazard';

  return (
    <>
      <color attach="background" args={[weatherSky]} />
      <fog attach="fog" args={[weatherSky, 28, 190]} />
      <ambientLight intensity={dimmed ? 0.2 : 0.45} />
      <directionalLight castShadow intensity={dimmed ? 0.35 : 1.02} position={[45, 55, 12]} shadow-mapSize={[1024, 1024]} />

      <Ground seed={seed} terrainRoughness={terrainRoughness} wetness={wetness} dimmed={dimmed} />
      {obstacles.map((obstacle) => (
        <ObstacleMesh key={obstacle.id} obstacle={obstacle} muted={dimmed} />
      ))}
    </>
  );
}

function Ground({ seed, terrainRoughness, wetness, dimmed }: { seed: number; terrainRoughness: number; wetness: number; dimmed: boolean }) {
  const tileSize = 22;
  const tiles = useMemo(() => {
    const list: Array<{ x: number; z: number; y: number; color: string }> = [];
    for (let x = -18; x <= 18; x += 1) {
      for (let z = -18; z <= 18; z += 1) {
        const wx = x * tileSize;
        const wz = z * tileSize;
        const y = sampleTerrainHeight(wx, wz, seed, terrainRoughness);
        const surface = sampleTerrainSurface(wx, wz, seed);
        const color =
          surface === 'mud' ? '#5a4334' :
          surface === 'wet' ? '#4a5842' :
          surface === 'dirt' ? '#6f5a39' : '#3d6a3d';
        list.push({ x: wx, z: wz, y, color });
      }
    }
    return list;
  }, [seed, terrainRoughness]);

  return (
    <group>
      {tiles.map((tile, idx) => (
        <mesh key={idx} position={[tile.x, tile.y - 0.25, tile.z]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[tileSize + 1.2, tileSize + 1.2, 1, 1]} />
          <meshStandardMaterial color={dimmed ? '#1f2937' : tile.color} roughness={0.95 - wetness * 0.25} metalness={wetness * 0.14} />
        </mesh>
      ))}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.8, 0]}>
        <planeGeometry args={[1800, 1800]} />
        <meshStandardMaterial color={dimmed ? '#0b1320' : '#1f3925'} roughness={1} />
      </mesh>
    </group>
  );
}

function ObstacleMesh({ obstacle, muted }: { obstacle: ChunkData['obstacles'][number]; muted: boolean }) {
  const color =
    obstacle.cls === 'human' ? '#fca5a5' :
    obstacle.cls === 'animal' ? '#fcd34d' :
    obstacle.cls === 'tree' ? '#3ba56a' :
    obstacle.cls === 'post' || obstacle.cls === 'pole' ? '#d4d4d4' :
    obstacle.cls === 'fence-line' || obstacle.cls === 'field-boundary' ? '#d946ef' :
    obstacle.cls === 'hay-bale' ? '#dcbf58' :
    obstacle.cls === 'vehicle' || obstacle.cls === 'tractor' || obstacle.cls === 'machinery' ? '#38bdf8' : '#a8a29e';

  const material = <meshStandardMaterial color={muted ? '#1f2937' : color} roughness={0.72} metalness={obstacle.cls === 'vehicle' || obstacle.cls === 'tractor' || obstacle.cls === 'machinery' ? 0.22 : 0.06} />;

  if (obstacle.cls === 'post' || obstacle.cls === 'pole') {
    return <mesh position={[obstacle.x, obstacle.y + 0.55, obstacle.z]} castShadow><cylinderGeometry args={[0.1, 0.12, 1.2, 8]} />{material}</mesh>;
  }
  if (obstacle.cls === 'tree') {
    return (
      <group position={[obstacle.x, obstacle.y + 1.6, obstacle.z]}>
        <mesh castShadow position={[0, -0.7, 0]}><cylinderGeometry args={[0.16, 0.22, 1.4, 8]} /><meshStandardMaterial color={muted ? '#1f2937' : '#7c4a22'} /></mesh>
        <mesh castShadow><coneGeometry args={[obstacle.radius * 1.2, obstacle.radius * 2.6, 10]} />{material}</mesh>
      </group>
    );
  }
  if (obstacle.cls === 'hay-bale') {
    return <mesh position={[obstacle.x, obstacle.y + 0.7, obstacle.z]} castShadow rotation={[0, Math.PI * 0.2, 0]}><cylinderGeometry args={[0.7, 0.7, 1.4, 14]} />{material}</mesh>;
  }
  if (obstacle.cls === 'human' || obstacle.cls === 'animal') {
    return <mesh position={[obstacle.x, obstacle.y + 0.8, obstacle.z]} castShadow><capsuleGeometry args={[0.28, obstacle.cls === 'human' ? 1.1 : 0.75, 8, 12]} />{material}</mesh>;
  }
  return <mesh position={[obstacle.x, obstacle.y + obstacle.radius * 0.6, obstacle.z]} castShadow><boxGeometry args={[obstacle.radius * 1.4, obstacle.radius * 1.2, obstacle.radius * 1.8]} />{material}</mesh>;
}
