'use client';

import { useFrame } from '@react-three/fiber';
import type { MutableRefObject } from 'react';
import { Vector3 } from 'three';

import { damp } from '@/lib/sim/math';
import type { VehicleState } from '@/lib/sim/vehicle/dynamics';

const temp = new Vector3();

type CameraMode = 'chase' | 'hood' | 'top' | 'lidar';

const offsets: Record<CameraMode, Vector3> = {
  chase: new Vector3(0, 5.5, -10),
  hood: new Vector3(0, 1.9, 1.5),
  top: new Vector3(0, 24, -0.1),
  lidar: new Vector3(0, 3.2, 0),
};

export function CameraRig({ stateRef, mode }: { stateRef: MutableRefObject<VehicleState>; mode: CameraMode }): null {
  useFrame((renderState, dt) => {
    const { camera } = renderState;
    const state = stateRef.current;
    const offset = offsets[mode].clone().applyAxisAngle(new Vector3(0, 1, 0), state.heading);
    temp.set(state.x + offset.x, state.y + offset.y, state.z + offset.z);
    camera.position.x = damp(camera.position.x, temp.x, 6, dt);
    camera.position.y = damp(camera.position.y, temp.y, 6, dt);
    camera.position.z = damp(camera.position.z, temp.z, 6, dt);
    camera.lookAt(state.x, state.y + (mode === 'top' ? 0 : 1.2), state.z + (mode === 'hood' ? 15 : 0));
  });

  return null;
}
