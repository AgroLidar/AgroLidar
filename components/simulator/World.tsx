'use client';

import { useEffect, useMemo, useRef } from 'react';
import { BackSide, Color, InstancedMesh, Object3D } from 'three';

import type { ChunkData } from '@/lib/sim/world/generator';
import type { WorldObstacle } from '@/lib/sim/world/props';
import { sampleTerrainHeight } from '@/lib/sim/world/terrain';

interface WorldProps {
  chunks: ChunkData[];
  weatherSky: string;
  seed: number;
  terrainRoughness: number;
  wetness: number;
  viewMode: 'world' | 'pointcloud' | 'hybrid' | 'bev' | 'depth' | 'hazard';
}

interface CropInstance {
  x: number;
  y: number;
  z: number;
  sx: number;
  sy: number;
  sz: number;
  rotY: number;
  color: string;
}

export function World({ chunks, weatherSky, seed, terrainRoughness, wetness, viewMode }: WorldProps) {
  const obstacles = useMemo(() => chunks.flatMap((chunk) => chunk.obstacles), [chunks]);
  const dimmed = viewMode === 'pointcloud' || viewMode === 'bev' || viewMode === 'hazard';

  return (
    <>
      <color attach="background" args={[weatherSky]} />
      <fog attach="fog" args={[dimmed ? '#405066' : '#d3a670', 58, 460]} />
      <hemisphereLight intensity={dimmed ? 0.24 : 0.42} groundColor="#35291c" color="#ffe9d1" />
      <directionalLight castShadow intensity={dimmed ? 0.44 : 1.38} color="#ffcb85" position={[-96, 48, -36]} shadow-mapSize={[2048, 2048]} shadow-bias={-0.00012} />
      <directionalLight intensity={0.24} color="#9ab8d8" position={[70, 26, 130]} />

      <Ground seed={seed} terrainRoughness={terrainRoughness} wetness={wetness} dimmed={dimmed} />
      <AtmosphereBackdrop dimmed={dimmed} />
      {obstacles.map((obstacle) => (
        <ObstacleMesh key={obstacle.id} obstacle={obstacle} muted={dimmed} />
      ))}
    </>
  );
}

function Ground({ seed, terrainRoughness, wetness, dimmed }: { seed: number; terrainRoughness: number; wetness: number; dimmed: boolean }) {
  const rowInstances = useMemo<CropInstance[]>(() => {
    const list: CropInstance[] = [];
    for (let lane = -54; lane <= 54; lane += 1) {
      const laneOffset = lane * 1.95;
      for (let segment = -90; segment <= 90; segment += 1) {
        if ((segment + lane + seed) % 3 === 0) continue;
        const z = segment * 3.9;
        const x = laneOffset + Math.sin((segment + seed) * 0.08) * 0.28;
        const y = sampleTerrainHeight(x, z, seed, terrainRoughness) - 0.16;
        const cropTone = 86 + ((lane * 3 + segment * 5 + seed) % 24);
        list.push({
          x,
          y,
          z,
          sx: 1.4,
          sy: 0.1 + (((segment + seed) % 5) * 0.02),
          sz: 3.0,
          rotY: Math.sin(lane * 0.02) * 0.08,
          color: `rgb(${Math.max(36, cropTone - 28)} ${cropTone} ${Math.max(26, cropTone - 46)})`,
        });
      }
    }
    return list;
  }, [seed, terrainRoughness]);

  const furrowInstances = useMemo<CropInstance[]>(() => {
    const list: CropInstance[] = [];
    for (let lane = -60; lane <= 60; lane += 1) {
      const x = lane * 1.95;
      for (let segment = -95; segment <= 95; segment += 1) {
        const z = segment * 3.8;
        const y = sampleTerrainHeight(x, z, seed, terrainRoughness) - 0.2;
        list.push({ x, y, z, sx: 0.72, sy: 0.05, sz: 3.35, rotY: 0, color: '#6a4a2c' });
      }
    }
    return list;
  }, [seed, terrainRoughness]);

  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.88, 0]} receiveShadow>
        <planeGeometry args={[2600, 2600]} />
        <meshStandardMaterial color={dimmed ? '#131f2b' : '#5a3f29'} roughness={1} metalness={0} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.62, 0]} receiveShadow>
        <planeGeometry args={[1220, 1220]} />
        <meshStandardMaterial color={dimmed ? '#1b2a3b' : '#7a5a36'} roughness={0.95 - wetness * 0.1} metalness={wetness * 0.1} />
      </mesh>
      <InstancedRows rows={furrowInstances} dimmed={dimmed} metalness={wetness * 0.12} roughness={0.92} />
      <InstancedRows rows={rowInstances} dimmed={dimmed} metalness={0.04} roughness={0.76} />
      <CropClumps seed={seed} terrainRoughness={terrainRoughness} dimmed={dimmed} />
    </group>
  );
}

function InstancedRows({ rows, dimmed, roughness, metalness }: { rows: CropInstance[]; dimmed: boolean; roughness: number; metalness: number }) {
  const meshRef = useRef<InstancedMesh>(null);
  const temp = useMemo(() => new Object3D(), []);

  useEffect(() => {
    if (!meshRef.current) return;
    rows.forEach((row, idx) => {
      temp.position.set(row.x, row.y, row.z);
      temp.rotation.set(0, row.rotY, 0);
      temp.scale.set(row.sx, row.sy, row.sz);
      temp.updateMatrix();
      meshRef.current?.setMatrixAt(idx, temp.matrix);
      meshRef.current?.setColorAt(idx, new Color(dimmed ? '#1f2d3f' : row.color));
    });
    meshRef.current.instanceMatrix.needsUpdate = true;
    if (meshRef.current.instanceColor) meshRef.current.instanceColor.needsUpdate = true;
  }, [dimmed, rows, temp]);

  return (
    <instancedMesh ref={meshRef} args={[undefined, undefined, rows.length]} receiveShadow castShadow={false}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial vertexColors roughness={roughness} metalness={metalness} />
    </instancedMesh>
  );
}

function CropClumps({ seed, terrainRoughness, dimmed }: { seed: number; terrainRoughness: number; dimmed: boolean }) {
  const clumps = useMemo<CropInstance[]>(() => {
    const list: CropInstance[] = [];
    for (let lane = -42; lane <= 42; lane += 3) {
      for (let segment = -56; segment <= 56; segment += 2) {
        const x = lane * 2.5 + Math.sin((seed + segment) * 0.17) * 0.45;
        const z = segment * 6.2;
        const y = sampleTerrainHeight(x, z, seed, terrainRoughness) - 0.05;
        list.push({
          x,
          y,
          z,
          sx: 0.5,
          sy: 0.65 + Math.abs(Math.sin((segment + seed) * 0.2)) * 0.45,
          sz: 0.5,
          rotY: (segment % 7) * 0.25,
          color: '#6a9a41',
        });
      }
    }
    return list;
  }, [seed, terrainRoughness]);

  const meshRef = useRef<InstancedMesh>(null);
  const temp = useMemo(() => new Object3D(), []);

  useEffect(() => {
    if (!meshRef.current) return;
    clumps.forEach((clump, idx) => {
      temp.position.set(clump.x, clump.y, clump.z);
      temp.rotation.set(0, clump.rotY, 0);
      temp.scale.set(clump.sx, clump.sy, clump.sz);
      temp.updateMatrix();
      meshRef.current?.setMatrixAt(idx, temp.matrix);
      meshRef.current?.setColorAt(idx, new Color(dimmed ? '#223041' : '#6a9a41'));
    });
    meshRef.current.instanceMatrix.needsUpdate = true;
    if (meshRef.current.instanceColor) meshRef.current.instanceColor.needsUpdate = true;
  }, [clumps, dimmed, temp]);

  return (
    <instancedMesh ref={meshRef} args={[undefined, undefined, clumps.length]} castShadow={false} receiveShadow>
      <coneGeometry args={[0.45, 1, 5]} />
      <meshStandardMaterial vertexColors roughness={0.88} metalness={0.02} />
    </instancedMesh>
  );
}

function AtmosphereBackdrop({ dimmed }: { dimmed: boolean }) {
  return (
    <group>
      <mesh position={[0, 30, -380]} rotation={[0, 0, 0]}>
        <planeGeometry args={[1200, 280]} />
        <meshBasicMaterial color={dimmed ? '#394960' : '#f0bf86'} transparent opacity={0.22} depthWrite={false} />
      </mesh>
      <mesh position={[0, 18, -460]}>
        <cylinderGeometry args={[420, 520, 78, 48, 1, true]} />
        <meshStandardMaterial color={dimmed ? '#25364a' : '#6a7b5c'} roughness={1} metalness={0} side={BackSide} />
      </mesh>
    </group>
  );
}

function ObstacleMesh({ obstacle, muted }: { obstacle: WorldObstacle; muted: boolean }) {
  const visualRadius = obstacle.sensingRadius ?? obstacle.radius;
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
    const crown = visualRadius * (1.4 + ((obstacle.variant ?? 0) % 3) * 0.22);
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
    <mesh position={[obstacle.x, obstacle.y + visualRadius * 0.5, obstacle.z]} castShadow>
      <dodecahedronGeometry args={[visualRadius, 0]} />
      {material}
    </mesh>
  );
}
