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
  chase: new Vector3(0, 4.7, -10.8),
  hood: new Vector3(0, 2.2, 2.2),
  cinematic: new Vector3(-9.2, 6.3, -8.2),
  top: new Vector3(0, 30, -0.1),
  lidar: new Vector3(0.65, 3.55, 1.2),
  'drone-follow': new Vector3(0, 5.8, -13),
  'drone-mission': new Vector3(0, 8, -5),
  'drone-survey': new Vector3(0, 24, 0),
};

export function CameraRig({ stateRef, mode }: { stateRef: MutableRefObject<VehicleState>; mode: CameraMode }): null {
  useFrame((renderState, dt) => {
    const { camera } = renderState;
    const state = stateRef.current;
    const followLag = mode === 'cinematic' ? 2.8 : mode === 'hood' ? 8.5 : 5.6;
    const offset = offsets[mode].clone().applyAxisAngle(up, state.heading);

    temp.set(state.x + offset.x, state.y + offset.y, state.z + offset.z);
    camera.position.x = damp(camera.position.x, temp.x, followLag, dt);
    camera.position.y = damp(camera.position.y, temp.y, followLag, dt);
    camera.position.z = damp(camera.position.z, temp.z, followLag, dt);

    const lookAhead = mode === 'hood' ? 30 : mode === 'cinematic' ? 11 : mode === 'lidar' ? 18 : 6;
    const lookYOffset = mode === 'top' || mode === 'drone-survey' ? 0 : mode === 'lidar' ? 2.2 : 1.5;
    look.set(
      state.x + Math.sin(state.heading) * lookAhead,
      state.y + lookYOffset,
      state.z + Math.cos(state.heading) * lookAhead,
    );
    camera.lookAt(look);
  });

  return null;
}
