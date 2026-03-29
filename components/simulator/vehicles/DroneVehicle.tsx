'use client';

import { useFrame } from '@react-three/fiber';
import { useMemo, useRef, type MutableRefObject } from 'react';
import { Group } from 'three';

import type { DroneMissionMode } from '@/lib/sim/config';
import type { VehicleState } from '@/lib/sim/vehicle/dynamics';

export function DroneVehicle({ stateRef, mission }: { stateRef: MutableRefObject<VehicleState>; mission: DroneMissionMode }) {
  const root = useRef<Group | null>(null);
  const rotorRefs = useRef<Group[]>([]);
  const armOffsets = useMemo(() => [[-2.2, 0, -2], [2.2, 0, -2], [-2.2, 0, 2], [2.2, 0, 2], [0, 0, -2.7], [0, 0, 2.7], [-2.9, 0, 0], [2.9, 0, 0]] as const, []);

  useFrame((_, dt) => {
    if (!root.current) return;
    const state = stateRef.current;
    root.current.position.set(state.x, state.y, state.z);
    root.current.rotation.set(state.pitch * 0.6, state.heading, state.roll * 0.6);

    const rotorSpeed = 18 + Math.max(0, state.speed * 2.8 + state.verticalSpeed * 4.2);
    for (const rotor of rotorRefs.current) rotor.rotation.y += rotorSpeed * dt;
  });

  return (
    <group ref={root}>
      <mesh castShadow position={[0, 0, 0]}>
        <cylinderGeometry args={[1.25, 1.45, 0.9, 18]} />
        <meshStandardMaterial color="#162033" metalness={0.45} roughness={0.3} />
      </mesh>
      <mesh castShadow position={[0, -0.55, 0]}>
        <boxGeometry args={[2.2, 0.5, 1.8]} />
        <meshStandardMaterial color="#0f172a" metalness={0.25} roughness={0.4} />
      </mesh>

      <mesh castShadow position={[0, -0.8, 0.75]}>
        <boxGeometry args={[1.2, 0.7, 1.1]} />
        <meshStandardMaterial color={mission === 'spray' ? '#16a34a' : mission === 'spread' ? '#a16207' : mission === 'lift' ? '#475569' : '#2563eb'} roughness={0.45} metalness={0.2} />
      </mesh>

      {armOffsets.map((offset, index) => (
        <group key={index} position={offset}>
          <mesh castShadow rotation={[Math.PI / 2, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.12, 0.12, index > 5 ? 2 : 1.8]} />
            <meshStandardMaterial color="#94a3b8" roughness={0.35} metalness={0.4} />
          </mesh>
          <group ref={(node) => { if (node && !rotorRefs.current.includes(node)) rotorRefs.current.push(node); }} position={[0, 0.05, 0]}>
            <mesh castShadow>
              <cylinderGeometry args={[0.22, 0.22, 0.24, 12]} />
              <meshStandardMaterial color="#1e293b" />
            </mesh>
            <mesh rotation={[0, 0, Math.PI / 4]}>
              <boxGeometry args={[1.6, 0.03, 0.12]} />
              <meshStandardMaterial color="#dbeafe" metalness={0.15} roughness={0.2} />
            </mesh>
          </group>
        </group>
      ))}

      <mesh castShadow position={[0, -1.2, 1.8]}>
        <boxGeometry args={[4.4, 0.12, 0.14]} />
        <meshStandardMaterial color={mission === 'spray' ? '#22c55e' : '#64748b'} />
      </mesh>

      {mission === 'lift' && (
        <group position={[0, -1.4, 0]}>
          <mesh castShadow>
            <cylinderGeometry args={[0.03, 0.03, 1.8]} />
            <meshStandardMaterial color="#f8fafc" />
          </mesh>
          <mesh castShadow position={[0, -1.05, 0]}>
            <boxGeometry args={[0.9, 0.55, 0.9]} />
            <meshStandardMaterial color="#334155" />
          </mesh>
        </group>
      )}

      <mesh castShadow position={[-1.8, -1.75, -1.8]}>
        <boxGeometry args={[0.18, 0.18, 2.7]} />
        <meshStandardMaterial color="#94a3b8" />
      </mesh>
      <mesh castShadow position={[1.8, -1.75, -1.8]}>
        <boxGeometry args={[0.18, 0.18, 2.7]} />
        <meshStandardMaterial color="#94a3b8" />
      </mesh>
    </group>
  );
}
