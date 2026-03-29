'use client';

import { useMemo, useRef, type MutableRefObject } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import { BufferGeometry, Group, Vector3 } from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import { mergeVertices } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

import type { VehicleState } from '@/lib/sim/vehicle/dynamics';

const TRACTOR_STL_PATH = '/assets/models/tractors/John_Deere_6195M_primary.stl';
const targetBodySize = new Vector3(2.6, 2.85, 4.8);

function prepareTractorGeometry(rawGeometry: BufferGeometry): BufferGeometry {
  const geometry = mergeVertices(rawGeometry.clone(), 1e-4);
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();

  const bbox = geometry.boundingBox;
  if (!bbox) return geometry;

  const size = new Vector3();
  const center = new Vector3();
  bbox.getSize(size);
  bbox.getCenter(center);

  geometry.translate(-center.x, -(bbox.min.y + size.y * 0.5), -center.z);

  const sx = targetBodySize.x / Math.max(0.001, size.x);
  const sy = targetBodySize.y / Math.max(0.001, size.y);
  const sz = targetBodySize.z / Math.max(0.001, size.z);
  const scale = Math.min(sx, sy, sz);
  geometry.scale(scale, scale, scale);
  geometry.rotateY(Math.PI);
  geometry.computeBoundingSphere();
  return geometry;
}

export function TractorVehicle({ stateRef }: { stateRef: MutableRefObject<VehicleState> }) {
  const rootRef = useRef<Group | null>(null);
  const wheelRefs = useRef<Group[]>([]);
  const steerRefs = useRef<Group[]>([]);
  const rawGeometry = useLoader(STLLoader, TRACTOR_STL_PATH);
  const tractorGeometry = useMemo(() => prepareTractorGeometry(rawGeometry), [rawGeometry]);

  useFrame(() => {
    const group = rootRef.current;
    if (!group) return;

    const state = stateRef.current;
    group.position.set(state.x, state.y + 1.15 + state.suspensionTravel, state.z);
    group.rotation.set(state.pitch, state.heading, state.roll);

    for (const wheel of wheelRefs.current) wheel.rotation.x = state.wheelSpin;
    for (const steer of steerRefs.current) steer.rotation.y = state.steerAngle;
  });

  return (
    <group ref={rootRef}>
      <group position={[0, 1.2, -0.18]}>
        <mesh castShadow receiveShadow geometry={tractorGeometry}>
          <meshStandardMaterial color="#1f7a2f" metalness={0.18} roughness={0.5} />
        </mesh>

        <mesh castShadow position={[0, 0.34, 0.28]}>
          <boxGeometry args={[2.4, 0.45, 3.1]} />
          <meshStandardMaterial color="#2a9d3a" metalness={0.24} roughness={0.44} />
        </mesh>

        <mesh castShadow position={[0, 1.05, -0.66]}>
          <boxGeometry args={[1.55, 0.95, 1.68]} />
          <meshStandardMaterial color="#222c34" metalness={0.32} roughness={0.28} />
        </mesh>

        <mesh castShadow position={[0, 1.09, -0.64]}>
          <boxGeometry args={[1.35, 0.82, 1.44]} />
          <meshStandardMaterial color="#7f9ead" metalness={0.08} roughness={0.12} transparent opacity={0.46} />
        </mesh>
      </group>

      <group position={[0, 2.4, 0.82]}>
        <mesh castShadow>
          <cylinderGeometry args={[0.05, 0.05, 0.42, 10]} />
          <meshStandardMaterial color="#f6cc2f" roughness={0.34} metalness={0.58} />
        </mesh>
        <mesh castShadow position={[0, 0.22, 0]}>
          <sphereGeometry args={[0.08, 12, 12]} />
          <meshStandardMaterial color="#66e3ff" emissive="#3ecbff" emissiveIntensity={0.75} roughness={0.12} metalness={0.42} />
        </mesh>
      </group>

      <WheelSet wheelRefs={wheelRefs} steerRefs={steerRefs} />
    </group>
  );
}

function WheelSet({ wheelRefs, steerRefs }: { wheelRefs: MutableRefObject<Group[]>; steerRefs: MutableRefObject<Group[]> }) {
  const rearScale: [number, number, number] = [1.36, 1.36, 0.78];
  const frontScale: [number, number, number] = [0.88, 0.88, 0.58];

  return (
    <>
      <Wheel position={[-1.52, 0.74, -1.48]} scale={rearScale} wheelRefs={wheelRefs} />
      <Wheel position={[1.52, 0.74, -1.48]} scale={rearScale} wheelRefs={wheelRefs} />
      <SteerWheel position={[-1.26, 0.66, 1.58]} scale={frontScale} wheelRefs={wheelRefs} steerRefs={steerRefs} />
      <SteerWheel position={[1.26, 0.66, 1.58]} scale={frontScale} wheelRefs={wheelRefs} steerRefs={steerRefs} />
    </>
  );
}

function Wheel({ position, scale, wheelRefs }: { position: [number, number, number]; scale: [number, number, number]; wheelRefs: MutableRefObject<Group[]> }) {
  return (
    <group
      position={position}
      ref={(node) => {
        if (node && !wheelRefs.current.includes(node)) wheelRefs.current.push(node);
      }}
    >
      <mesh castShadow rotation={[0, 0, Math.PI / 2]} scale={scale}>
        <cylinderGeometry args={[0.5, 0.5, 0.5, 20]} />
        <meshStandardMaterial color="#141b22" roughness={0.92} metalness={0.06} />
      </mesh>
      <mesh castShadow rotation={[0, 0, Math.PI / 2]} scale={[scale[0] * 0.35, scale[1] * 0.35, scale[2] * 0.54]}>
        <cylinderGeometry args={[0.5, 0.5, 0.5, 16]} />
        <meshStandardMaterial color="#f3c623" roughness={0.35} metalness={0.72} />
      </mesh>
    </group>
  );
}

function SteerWheel({ position, scale, wheelRefs, steerRefs }: { position: [number, number, number]; scale: [number, number, number]; wheelRefs: MutableRefObject<Group[]>; steerRefs: MutableRefObject<Group[]> }) {
  return (
    <group
      position={position}
      ref={(node) => {
        if (!node) return;
        if (!wheelRefs.current.includes(node)) wheelRefs.current.push(node);
        if (!steerRefs.current.includes(node)) steerRefs.current.push(node);
      }}
    >
      <mesh castShadow rotation={[0, 0, Math.PI / 2]} scale={scale}>
        <cylinderGeometry args={[0.5, 0.5, 0.4, 18]} />
        <meshStandardMaterial color="#111827" roughness={0.9} metalness={0.04} />
      </mesh>
      <mesh castShadow rotation={[0, 0, Math.PI / 2]} scale={[scale[0] * 0.36, scale[1] * 0.36, scale[2] * 0.54]}>
        <cylinderGeometry args={[0.5, 0.5, 0.4, 14]} />
        <meshStandardMaterial color="#f3c623" roughness={0.34} metalness={0.7} />
      </mesh>
    </group>
  );
}
