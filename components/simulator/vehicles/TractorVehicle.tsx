'use client';

import { useMemo, useRef, type MutableRefObject } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import { BufferGeometry, Group, Vector3 } from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import { mergeVertices } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

import type { VehicleState } from '@/lib/sim/vehicle/dynamics';

const TRACTOR_STL_PATH = '/assets/models/tractors/John_Deere_6195M_primary.stl';
const targetBodySize = new Vector3(2.95, 2.78, 5.35);

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
    group.position.set(state.x, state.y + 1.02 + state.suspensionTravel, state.z);
    group.rotation.set(state.pitch, state.heading, state.roll);

    for (const wheel of wheelRefs.current) wheel.rotation.x = state.wheelSpin;
    for (const steer of steerRefs.current) steer.rotation.y = state.steerAngle;
  });

  return (
    <group ref={rootRef}>
      <group position={[0, 1.02, -0.06]}>
        <mesh castShadow receiveShadow geometry={tractorGeometry}>
          <meshStandardMaterial color="#1d7f33" metalness={0.2} roughness={0.4} />
        </mesh>

        <mesh castShadow position={[0.62, 1.42, 0.34]} rotation={[0, 0, 0.08]}>
          <cylinderGeometry args={[0.07, 0.1, 1.06, 12]} />
          <meshStandardMaterial color="#27323b" roughness={0.52} metalness={0.45} />
        </mesh>
      </group>

      <group position={[0.04, 2.16, 0.98]}>
        <mesh castShadow>
          <cylinderGeometry args={[0.048, 0.048, 0.5, 10]} />
          <meshStandardMaterial color="#e9bf2e" roughness={0.3} metalness={0.64} />
        </mesh>
        <mesh castShadow position={[0, 0.29, 0]}>
          <sphereGeometry args={[0.09, 12, 12]} />
          <meshStandardMaterial color="#5ce3ff" emissive="#43c4ff" emissiveIntensity={0.9} roughness={0.1} metalness={0.42} />
        </mesh>
      </group>

      <group position={[0, 0.9, -2.18]}>
        <mesh castShadow>
          <boxGeometry args={[0.68, 0.18, 0.28]} />
          <meshStandardMaterial color="#454a51" roughness={0.66} metalness={0.3} />
        </mesh>
      </group>

      <WheelSet wheelRefs={wheelRefs} steerRefs={steerRefs} />
    </group>
  );
}

function WheelSet({ wheelRefs, steerRefs }: { wheelRefs: MutableRefObject<Group[]>; steerRefs: MutableRefObject<Group[]> }) {
  const rearScale: [number, number, number] = [1.42, 1.42, 0.82];
  const frontScale: [number, number, number] = [0.92, 0.92, 0.62];

  return (
    <>
      <Wheel position={[-1.58, 0.64, -1.53]} scale={rearScale} wheelRefs={wheelRefs} />
      <Wheel position={[1.58, 0.64, -1.53]} scale={rearScale} wheelRefs={wheelRefs} />
      <SteerWheel position={[-1.3, 0.55, 1.65]} scale={frontScale} wheelRefs={wheelRefs} steerRefs={steerRefs} />
      <SteerWheel position={[1.3, 0.55, 1.65]} scale={frontScale} wheelRefs={wheelRefs} steerRefs={steerRefs} />
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
        <cylinderGeometry args={[0.5, 0.5, 0.5, 24]} />
        <meshStandardMaterial color="#11161b" roughness={0.93} metalness={0.04} />
      </mesh>
      <mesh castShadow rotation={[0, 0, Math.PI / 2]} scale={[scale[0] * 0.38, scale[1] * 0.38, scale[2] * 0.5]}>
        <cylinderGeometry args={[0.5, 0.5, 0.5, 16]} />
        <meshStandardMaterial color="#e7b81f" roughness={0.34} metalness={0.74} />
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
        <cylinderGeometry args={[0.5, 0.5, 0.4, 20]} />
        <meshStandardMaterial color="#10151c" roughness={0.9} metalness={0.05} />
      </mesh>
      <mesh castShadow rotation={[0, 0, Math.PI / 2]} scale={[scale[0] * 0.38, scale[1] * 0.38, scale[2] * 0.56]}>
        <cylinderGeometry args={[0.5, 0.5, 0.4, 14]} />
        <meshStandardMaterial color="#ebb924" roughness={0.32} metalness={0.72} />
      </mesh>
    </group>
  );
}
