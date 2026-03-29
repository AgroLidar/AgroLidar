'use client';

import { useRef, type MutableRefObject } from 'react';
import { useFrame } from '@react-three/fiber';
import { Group } from 'three';

import type { VehicleState } from '@/lib/sim/vehicle/dynamics';

export function TractorVehicle({ stateRef }: { stateRef: MutableRefObject<VehicleState> }) {
  const rootRef = useRef<Group | null>(null);
  const wheelRefs = useRef<Group[]>([]);
  const steerRefs = useRef<Group[]>([]);

  useFrame(() => {
    const group = rootRef.current;
    if (!group) return;

    const state = stateRef.current;
    group.position.set(state.x, state.y + 1.05 + state.suspensionTravel, state.z);
    group.rotation.set(state.pitch, state.heading, state.roll);

    for (const wheel of wheelRefs.current) wheel.rotation.x = state.wheelSpin;
    for (const steer of steerRefs.current) steer.rotation.y = state.steerAngle;
  });

  return (
    <group ref={rootRef}>
      <group position={[0, 0.85, -0.1]}>
        <mesh castShadow>
          <boxGeometry args={[2.2, 1.2, 4.2]} />
          <meshStandardMaterial color="#2a98a6" metalness={0.2} roughness={0.48} />
        </mesh>
        <mesh position={[0, 0.8, -0.4]} castShadow>
          <boxGeometry args={[1.45, 0.95, 1.8]} />
          <meshStandardMaterial color="#0f172a" metalness={0.3} roughness={0.25} />
        </mesh>
      </group>

      <group position={[0, 2.08, -0.25]}>
        <mesh castShadow>
          <cylinderGeometry args={[0.07, 0.07, 1.45]} />
          <meshStandardMaterial color="#e2e8f0" roughness={0.45} />
        </mesh>
        <mesh castShadow rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.06, 0.06, 1.5]} />
          <meshStandardMaterial color="#e2e8f0" roughness={0.45} />
        </mesh>
      </group>

      <WheelSet wheelRefs={wheelRefs} steerRefs={steerRefs} />
    </group>
  );
}

function WheelSet({ wheelRefs, steerRefs }: { wheelRefs: MutableRefObject<Group[]>; steerRefs: MutableRefObject<Group[]> }) {
  const rearScale: [number, number, number] = [1.28, 1.28, 0.72];
  const frontScale: [number, number, number] = [0.82, 0.82, 0.58];

  return (
    <>
      <Wheel position={[-1.4, 0.7, -1.4]} scale={rearScale} wheelRefs={wheelRefs} />
      <Wheel position={[1.4, 0.7, -1.4]} scale={rearScale} wheelRefs={wheelRefs} />
      <SteerWheel position={[-1.18, 0.64, 1.42]} scale={frontScale} wheelRefs={wheelRefs} steerRefs={steerRefs} />
      <SteerWheel position={[1.18, 0.64, 1.42]} scale={frontScale} wheelRefs={wheelRefs} steerRefs={steerRefs} />
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
        <cylinderGeometry args={[0.5, 0.5, 0.42, 18]} />
        <meshStandardMaterial color="#101828" roughness={0.9} metalness={0.05} />
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
        <cylinderGeometry args={[0.5, 0.5, 0.4, 16]} />
        <meshStandardMaterial color="#111827" roughness={0.9} />
      </mesh>
    </group>
  );
}
