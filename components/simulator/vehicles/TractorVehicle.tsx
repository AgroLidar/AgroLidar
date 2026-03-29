'use client';

import { useMemo, useRef, type MutableRefObject } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import { BufferGeometry, Group, MathUtils, Vector3 } from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import { mergeVertices } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

import type { VehicleState } from '@/lib/sim/vehicle/dynamics';

const TRACTOR_STL_PATH = '/assets/models/tractors/John_Deere_6195M_primary.stl';
const targetBodySize = new Vector3(3.2, 2.9, 5.8);

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
  const dustRef = useRef<Group | null>(null);
  const rawGeometry = useLoader(STLLoader, TRACTOR_STL_PATH);
  const tractorGeometry = useMemo(() => prepareTractorGeometry(rawGeometry), [rawGeometry]);

  useFrame((_, dt) => {
    const group = rootRef.current;
    if (!group) return;

    const state = stateRef.current;
    group.position.set(state.x, state.y + 1.03 + state.suspensionTravel, state.z);
    group.rotation.set(state.pitch, state.heading, state.roll);

    for (const wheel of wheelRefs.current) wheel.rotation.x = state.wheelSpin;
    for (const steer of steerRefs.current) steer.rotation.y = state.steerAngle;

    if (dustRef.current) {
      const moving = Math.abs(state.speed) > 0.7;
      const target = moving ? MathUtils.clamp(Math.abs(state.speed) * 0.095, 0, 0.52) : 0;
      dustRef.current.position.set(0, 0.36, -2.65);
      dustRef.current.visible = target > 0.02;
      dustRef.current.children.forEach((child, idx) => {
        child.position.x = Math.sin((state.wheelSpin * 0.32) + idx * 0.95) * (0.3 + idx * 0.012);
        child.position.y = 0.1 + (idx % 6) * 0.06 + Math.sin(state.wheelSpin * 0.2 + idx) * 0.03;
        child.position.z = -idx * 0.16;
        child.scale.setScalar(0.52 + idx * 0.018 + target * 0.28);
        const mat = (child as { material?: { opacity?: number } }).material;
        if (mat) mat.opacity = Math.max(0, target - idx * 0.012);
      });
      dustRef.current.rotation.y = Math.sin(state.wheelSpin * 0.02) * 0.18;
      dustRef.current.position.y += dt * 0.18;
    }
  });

  return (
    <group ref={rootRef}>
      <group position={[0, 1.0, -0.02]}>
        <mesh castShadow receiveShadow geometry={tractorGeometry}>
          <meshStandardMaterial color="#1f6f36" metalness={0.28} roughness={0.34} />
        </mesh>

        <mesh castShadow position={[0, 1.74, 0.32]}>
          <boxGeometry args={[1.6, 0.95, 1.4]} />
          <meshStandardMaterial color="#2d343d" roughness={0.72} metalness={0.2} transparent opacity={0.2} />
        </mesh>

        <mesh castShadow position={[0.84, 1.44, 2.03]} rotation={[0, 0, -0.05]}>
          <cylinderGeometry args={[0.07, 0.095, 1.22, 18]} />
          <meshStandardMaterial color="#252d34" roughness={0.45} metalness={0.55} />
        </mesh>

        <mesh castShadow position={[0.95, 1.76, 2.51]} rotation={[0, 0, -0.1]}>
          <cylinderGeometry args={[0.058, 0.058, 0.33, 12]} />
          <meshStandardMaterial color="#1d2328" roughness={0.38} metalness={0.7} />
        </mesh>

        <mesh castShadow position={[0.92, 1.92, 0.56]}>
          <boxGeometry args={[0.06, 0.36, 0.22]} />
          <meshStandardMaterial color="#232a31" roughness={0.48} metalness={0.44} />
        </mesh>
        <mesh castShadow position={[-0.92, 1.92, 0.56]}>
          <boxGeometry args={[0.06, 0.36, 0.22]} />
          <meshStandardMaterial color="#232a31" roughness={0.48} metalness={0.44} />
        </mesh>

        <mesh castShadow position={[0.84, 1.56, 2.53]}>
          <sphereGeometry args={[0.11, 18, 18]} />
          <meshStandardMaterial color="#f8d46b" emissive="#fdc85f" emissiveIntensity={0.45} roughness={0.22} metalness={0.3} />
        </mesh>
        <mesh castShadow position={[-0.84, 1.56, 2.53]}>
          <sphereGeometry args={[0.11, 18, 18]} />
          <meshStandardMaterial color="#f8d46b" emissive="#fdc85f" emissiveIntensity={0.45} roughness={0.22} metalness={0.3} />
        </mesh>

        <mesh castShadow position={[0, 0.74, -2.24]}>
          <boxGeometry args={[0.74, 0.2, 0.4]} />
          <meshStandardMaterial color="#4b5058" roughness={0.76} metalness={0.24} />
        </mesh>

        <mesh castShadow position={[1.06, 0.9, -1.24]} rotation={[0, 0, -0.2]}>
          <boxGeometry args={[0.14, 0.7, 0.98]} />
          <meshStandardMaterial color="#244c2a" roughness={0.6} metalness={0.16} />
        </mesh>
        <mesh castShadow position={[-1.06, 0.9, -1.24]} rotation={[0, 0, 0.2]}>
          <boxGeometry args={[0.14, 0.7, 0.98]} />
          <meshStandardMaterial color="#244c2a" roughness={0.6} metalness={0.16} />
        </mesh>
      </group>

      <WheelSet wheelRefs={wheelRefs} steerRefs={steerRefs} />

      <group ref={dustRef}>
        {Array.from({ length: 20 }).map((_, idx) => (
          <mesh key={idx} castShadow={false}>
            <sphereGeometry args={[0.2, 8, 8]} />
            <meshStandardMaterial color="#c19f74" transparent opacity={0} roughness={1} metalness={0} depthWrite={false} />
          </mesh>
        ))}
      </group>
    </group>
  );
}

function WheelSet({ wheelRefs, steerRefs }: { wheelRefs: MutableRefObject<Group[]>; steerRefs: MutableRefObject<Group[]> }) {
  const rearScale: [number, number, number] = [1.5, 1.5, 0.92];
  const frontScale: [number, number, number] = [0.98, 0.98, 0.68];

  return (
    <>
      <Wheel position={[-1.62, 0.66, -1.56]} scale={rearScale} wheelRefs={wheelRefs} />
      <Wheel position={[1.62, 0.66, -1.56]} scale={rearScale} wheelRefs={wheelRefs} />
      <SteerWheel position={[-1.32, 0.57, 1.72]} scale={frontScale} wheelRefs={wheelRefs} steerRefs={steerRefs} />
      <SteerWheel position={[1.32, 0.57, 1.72]} scale={frontScale} wheelRefs={wheelRefs} steerRefs={steerRefs} />
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
        <cylinderGeometry args={[0.5, 0.5, 0.56, 28]} />
        <meshStandardMaterial color="#0f1419" roughness={0.96} metalness={0.03} />
      </mesh>
      <mesh castShadow rotation={[0, 0, Math.PI / 2]} scale={[scale[0] * 0.86, scale[1] * 0.86, scale[2] * 0.72]}>
        <cylinderGeometry args={[0.5, 0.5, 0.55, 20]} />
        <meshStandardMaterial color="#151d22" roughness={0.84} metalness={0.07} />
      </mesh>
      <mesh castShadow rotation={[0, 0, Math.PI / 2]} scale={[scale[0] * 0.38, scale[1] * 0.38, scale[2] * 0.58]}>
        <cylinderGeometry args={[0.5, 0.5, 0.5, 18]} />
        <meshStandardMaterial color="#e2b924" roughness={0.33} metalness={0.76} />
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
        <cylinderGeometry args={[0.5, 0.5, 0.46, 24]} />
        <meshStandardMaterial color="#10161b" roughness={0.94} metalness={0.04} />
      </mesh>
      <mesh castShadow rotation={[0, 0, Math.PI / 2]} scale={[scale[0] * 0.82, scale[1] * 0.82, scale[2] * 0.7]}>
        <cylinderGeometry args={[0.5, 0.5, 0.42, 18]} />
        <meshStandardMaterial color="#151c22" roughness={0.85} metalness={0.06} />
      </mesh>
      <mesh castShadow rotation={[0, 0, Math.PI / 2]} scale={[scale[0] * 0.36, scale[1] * 0.36, scale[2] * 0.56]}>
        <cylinderGeometry args={[0.5, 0.5, 0.42, 14]} />
        <meshStandardMaterial color="#e8bd2a" roughness={0.34} metalness={0.74} />
      </mesh>
    </group>
  );
}
