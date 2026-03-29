'use client';

import { useFrame } from '@react-three/fiber';
import type { MutableRefObject } from 'react';
import { Vector3 } from 'three';

import { damp } from '@/lib/sim/math';
import type { CameraMode } from '@/lib/sim/config';
import type { VehicleState } from '@/lib/sim/vehicle/dynamics';

const temp = new Vector3();
const look = new Vector3();
const up = new Vector3(0, 1, 0);

const offsets: Record<CameraMode, Vector3> = {
  chase: new Vector3(0, 4.8, -11),
  hood: new Vector3(0, 2.35, 2.5),
  cinematic: new Vector3(-7, 6.2, -8),
  top: new Vector3(0, 28, -0.1),
  lidar: new Vector3(0, 3.1, 0.2),
};

export function CameraRig({ stateRef, mode }: { stateRef: MutableRefObject<VehicleState>; mode: CameraMode }): null {
  useFrame((renderState, dt) => {
    const { camera } = renderState;
    const state = stateRef.current;
    const offset = offsets[mode].clone().applyAxisAngle(up, state.heading);

    temp.set(state.x + offset.x, state.y + offset.y, state.z + offset.z);
    camera.position.x = damp(camera.position.x, temp.x, 4.8, dt);
    camera.position.y = damp(camera.position.y, temp.y, 4.8, dt);
    camera.position.z = damp(camera.position.z, temp.z, 4.8, dt);

    look.set(state.x, state.y + (mode === 'top' ? 0 : 1.5), state.z + (mode === 'hood' ? 24 : mode === 'cinematic' ? 8 : 0));
    camera.lookAt(look);
  });

  return null;
}
