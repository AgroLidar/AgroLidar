'use client';

import { useMemo } from 'react';

import type { ChunkData } from '@/lib/sim/world/generator';
import type { WorldObstacle } from '@/lib/sim/world/props';
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
      <fog attach="fog" args={[weatherSky, 34, 250]} />
      <hemisphereLight intensity={dimmed ? 0.28 : 0.54} groundColor="#283528" color="#cfdef6" />
      <directionalLight castShadow intensity={dimmed ? 0.44 : 1.08} position={[52, 58, 24]} shadow-mapSize={[1536, 1536]} shadow-bias={-0.0002} />

      <Ground seed={seed} terrainRoughness={terrainRoughness} wetness={wetness} dimmed={dimmed} />
      {obstacles.map((obstacle) => (
        <ObstacleMesh key={obstacle.id} obstacle={obstacle} muted={dimmed} />
      ))}
    </>
  );
}

function Ground({ seed, terrainRoughness, wetness, dimmed }: { seed: number; terrainRoughness: number; wetness: number; dimmed: boolean }) {
  const tileSize = 18;
  const tiles = useMemo(() => {
    const list: Array<{ x: number; z: number; y: number; color: string; cropTint: string; rough: number }> = [];
    for (let x = -21; x <= 21; x += 1) {
      for (let z = -21; z <= 21; z += 1) {
        const wx = x * tileSize;
        const wz = z * tileSize;
        const y = sampleTerrainHeight(wx, wz, seed, terrainRoughness);
        const surface = sampleTerrainSurface(wx, wz, seed);
        const color =
          surface === 'mud' ? '#604734' :
          surface === 'wet' ? '#495945' :
          surface === 'dirt' ? '#7a603c' : '#3f6d3f';
        const cropTint = surface === 'grass' ? '#5e8f3f' : '#5f7e35';
        const rough = 0.8 + ((x + z + seed) % 5) * 0.04;
        list.push({ x: wx, z: wz, y, color, cropTint, rough });
      }
    }
    return list;
  }, [seed, terrainRoughness]);

  return (
    <group>
      {tiles.map((tile, idx) => (
        <group key={idx} position={[tile.x, tile.y, tile.z]}>
          <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[0, -0.3, 0]}>
            <planeGeometry args={[tileSize + 0.9, tileSize + 0.9]} />
            <meshStandardMaterial color={dimmed ? '#1f2937' : tile.color} roughness={tile.rough - wetness * 0.16} metalness={wetness * 0.16} />
          </mesh>
          <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[0, -0.28, 0]}>
            <ringGeometry args={[tileSize * 0.1, tileSize * 0.5, 6]} />
            <meshStandardMaterial color={dimmed ? '#1e293b' : tile.cropTint} roughness={0.96} metalness={0.02} transparent opacity={0.34} />
          </mesh>
        </group>
      ))}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.84, 0]} receiveShadow>
        <planeGeometry args={[2200, 2200]} />
        <meshStandardMaterial color={dimmed ? '#0a1320' : '#213c27'} roughness={1} />
      </mesh>
    </group>
  );
}

function ObstacleMesh({ obstacle, muted }: { obstacle: WorldObstacle; muted: boolean }) {
  const color =
    obstacle.cls === 'human' ? '#ffb2a4' :
    obstacle.cls === 'animal' ? '#f7c45c' :
    obstacle.cls === 'tree' ? '#3ba56a' :
    obstacle.cls === 'post' || obstacle.cls === 'pole' ? '#d4d4d4' :
    obstacle.cls === 'fence-line' || obstacle.cls === 'field-boundary' ? '#cb90db' :
    obstacle.cls === 'hay-bale' ? '#dcbf58' :
    obstacle.cls === 'vehicle' || obstacle.cls === 'tractor' || obstacle.cls === 'machinery' ? '#43b4f7' : '#a8a29e';

  const material = (
    <meshStandardMaterial
      color={muted ? '#1f2937' : color}
      roughness={0.72}
      metalness={obstacle.cls === 'vehicle' || obstacle.cls === 'tractor' || obstacle.cls === 'machinery' ? 0.28 : 0.08}
    />
  );

  if (obstacle.cls === 'tree') {
    const treeHeight = obstacle.height ?? 6.2;
    const crown = obstacle.radius * (1.4 + ((obstacle.variant ?? 0) % 3) * 0.22);
    return (
      <group position={[obstacle.x, obstacle.y, obstacle.z]}>
        <mesh castShadow position={[0, treeHeight * 0.22, 0]}>
          <cylinderGeometry args={[0.14 + obstacle.radius * 0.05, 0.22 + obstacle.radius * 0.1, treeHeight * 0.44, 8]} />
          <meshStandardMaterial color={muted ? '#1f2937' : '#6f4320'} roughness={0.9} />
        </mesh>
        <mesh castShadow position={[0, treeHeight * 0.57, 0]}>
          <coneGeometry args={[crown, treeHeight * 0.72, 12]} />
          {material}
        </mesh>
        <mesh castShadow position={[0, treeHeight * 0.78, 0]}>
          <sphereGeometry args={[crown * 0.65, 10, 10]} />
          <meshStandardMaterial color={muted ? '#1f2937' : '#4e9f53'} roughness={0.84} />
        </mesh>
      </group>
    );
  }

  if (obstacle.cls === 'human') {
    return (
      <group position={[obstacle.x, obstacle.y + 0.02, obstacle.z]}>
        <mesh castShadow position={[0, 1.02, 0]}>
          <capsuleGeometry args={[0.24, 0.92, 8, 10]} />
          {material}
        </mesh>
        <mesh castShadow position={[0, 1.68, 0]}>
          <sphereGeometry args={[0.22, 10, 10]} />
          <meshStandardMaterial color={muted ? '#1f2937' : '#f2d2b0'} roughness={0.7} />
        </mesh>
      </group>
    );
  }

  if (obstacle.cls === 'animal') {
    return (
      <group position={[obstacle.x, obstacle.y + 0.3, obstacle.z]}>
        <mesh castShadow>
          <boxGeometry args={[0.8, 0.54, 1.2]} />
          {material}
        </mesh>
        <mesh castShadow position={[0, 0.26, 0.52]}>
          <boxGeometry args={[0.46, 0.38, 0.42]} />
          {material}
        </mesh>
      </group>
    );
  }

  if (obstacle.cls === 'post' || obstacle.cls === 'pole') {
    return (
      <mesh position={[obstacle.x, obstacle.y + (obstacle.height ?? 1.4) * 0.5, obstacle.z]} castShadow>
        <cylinderGeometry args={[0.08, 0.1, obstacle.height ?? 1.4, 8]} />
        {material}
      </mesh>
    );
  }

  if (obstacle.cls === 'hay-bale') {
    return (
      <mesh position={[obstacle.x, obstacle.y + 0.56, obstacle.z]} castShadow rotation={[0, Math.PI * 0.2, Math.PI / 2]}>
        <cylinderGeometry args={[0.58, 0.58, 1.15, 16]} />
        {material}
      </mesh>
    );
  }

  if (obstacle.cls === 'fence-line' || obstacle.cls === 'field-boundary') {
    return (
      <group position={[obstacle.x, obstacle.y + 0.28, obstacle.z]} rotation={[0, (obstacle.variant ?? 0) * 0.6, 0]}>
        <mesh castShadow>
          <boxGeometry args={[2.1, 0.16, 0.16]} />
          {material}
        </mesh>
        <mesh castShadow position={[-0.95, -0.16, 0]}>
          <cylinderGeometry args={[0.06, 0.07, 0.56, 6]} />
          <meshStandardMaterial color={muted ? '#1f2937' : '#8d7456'} />
        </mesh>
        <mesh castShadow position={[0.95, -0.16, 0]}>
          <cylinderGeometry args={[0.06, 0.07, 0.56, 6]} />
          <meshStandardMaterial color={muted ? '#1f2937' : '#8d7456'} />
        </mesh>
      </group>
    );
  }

  if (obstacle.cls === 'vehicle' || obstacle.cls === 'tractor' || obstacle.cls === 'machinery') {
    return (
      <group position={[obstacle.x, obstacle.y + 0.8, obstacle.z]} rotation={[0, (obstacle.variant ?? 0) * 0.5, 0]}>
        <mesh castShadow>
          <boxGeometry args={[2.1, 1.15, 1.6]} />
          {material}
        </mesh>
        <mesh castShadow position={[0, 0.58, -0.15]}>
          <boxGeometry args={[1.1, 0.72, 1]} />
          <meshStandardMaterial color={muted ? '#1f2937' : '#3c4a54'} roughness={0.36} metalness={0.32} />
        </mesh>
      </group>
    );
  }

  return (
    <mesh position={[obstacle.x, obstacle.y + obstacle.radius * 0.5, obstacle.z]} castShadow>
      <dodecahedronGeometry args={[obstacle.radius, 0]} />
      {material}
    </mesh>
  );
}
