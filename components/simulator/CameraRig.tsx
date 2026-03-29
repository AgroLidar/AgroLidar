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
  chase: new Vector3(0, 5.1, -11.6),
  hood: new Vector3(0, 2.6, 2.9),
  cinematic: new Vector3(-8.4, 6.8, -8.6),
  top: new Vector3(0, 30, -0.1),
  lidar: new Vector3(0, 3.45, 0.9),
  'drone-follow': new Vector3(0, 5.8, -13),
  'drone-mission': new Vector3(0, 8, -5),
  'drone-survey': new Vector3(0, 24, 0),
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

    look.set(state.x, state.y + (mode === 'top' || mode === 'drone-survey' ? 0 : 1.7), state.z + (mode === 'hood' ? 28 : mode === 'cinematic' ? 9 : 0));
    camera.lookAt(look);
  });

  return null;
}
