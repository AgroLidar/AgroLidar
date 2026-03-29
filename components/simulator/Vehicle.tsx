'use client';

import type { MutableRefObject } from 'react';
import { useFrame } from '@react-three/fiber';
import { Group } from 'three';

import type { VehicleState } from '@/lib/sim/vehicle/dynamics';

export function Vehicle({ stateRef }: { stateRef: MutableRefObject<VehicleState> }) {
  useFrame((_, dt) => {
    const group = (stateRef as MutableRefObject<VehicleState & { node?: Group }>).current.node;
    if (!group) return;
    const state = stateRef.current;
    group.position.set(state.x, state.y + 0.8, state.z);
    group.rotation.set(state.pitch, state.heading, state.roll);
    const bob = Math.sin(performance.now() * 0.01) * 0.01 * Math.min(1, Math.abs(state.speed) / 10) * dt * 60;
    group.position.set(group.position.x, group.position.y + bob, group.position.z);
  });

  return (
    <group ref={(node) => { (stateRef as MutableRefObject<VehicleState & { node?: Group }>).current.node = node ?? undefined; }}>
      <mesh castShadow>
        <boxGeometry args={[1.9, 0.9, 3.6]} />
        <meshStandardMaterial color="#14b8a6" metalness={0.15} roughness={0.45} />
      </mesh>
      <mesh position={[0, 0.7, -0.4]} castShadow>
        <boxGeometry args={[1.2, 0.6, 1.6]} />
        <meshStandardMaterial color="#0f172a" metalness={0.4} roughness={0.2} />
      </mesh>
    </group>
  );
}
