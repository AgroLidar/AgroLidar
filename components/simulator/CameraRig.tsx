'use client';

import { useFrame } from '@react-three/fiber';
import type { MutableRefObject } from 'react';
import { MathUtils, Vector3 } from 'three';

import { damp } from '@/lib/sim/math';
import type { CameraMode } from '@/lib/sim/config';
import type { VehicleState } from '@/lib/sim/vehicle/dynamics';

const temp = new Vector3();
const look = new Vector3();
const up = new Vector3(0, 1, 0);

const offsets: Record<CameraMode, Vector3> = {
  chase: new Vector3(0, 3.8, -11.9),
  hood: new Vector3(0, 2.25, 2.4),
  cinematic: new Vector3(-6.8, 3.1, -9.8),
  top: new Vector3(0, 30, -0.1),
  lidar: new Vector3(0.7, 3.3, 1.22),
  'drone-follow': new Vector3(0, 5.8, -13),
  'drone-mission': new Vector3(0, 8, -5),
  'drone-survey': new Vector3(0, 24, 0),
};

export function CameraRig({ stateRef, mode }: { stateRef: MutableRefObject<VehicleState>; mode: CameraMode }): null {
  useFrame((renderState, dt) => {
    const { camera } = renderState;
    const state = stateRef.current;
    const speedAbs = Math.abs(state.speed);
    const followLag = mode === 'cinematic' ? 3.4 : mode === 'hood' ? 9 : 6.3;
    const offset = offsets[mode].clone().applyAxisAngle(up, state.heading);
    if (mode === 'chase' || mode === 'cinematic') {
      offset.y += MathUtils.clamp(speedAbs * 0.03, 0, 0.9);
      offset.z -= MathUtils.clamp(speedAbs * 0.04, 0, 1.1);
    }

    temp.set(state.x + offset.x, state.y + offset.y, state.z + offset.z);
    camera.position.x = damp(camera.position.x, temp.x, followLag, dt);
    camera.position.y = damp(camera.position.y, temp.y, followLag, dt);
    camera.position.z = damp(camera.position.z, temp.z, followLag, dt);

    const lookAhead = mode === 'hood' ? 34 : mode === 'cinematic' ? 18 : mode === 'lidar' ? 21 : 9;
    const lookYOffset = mode === 'top' || mode === 'drone-survey' ? 0 : mode === 'lidar' ? 2.2 : mode === 'cinematic' ? 1.35 : 1.45;
    look.set(
      state.x + Math.sin(state.heading) * (lookAhead + speedAbs * 0.5),
      state.y + lookYOffset,
      state.z + Math.cos(state.heading) * (lookAhead + speedAbs * 0.5),
    );
    camera.lookAt(look);
  });

  return null;
}
