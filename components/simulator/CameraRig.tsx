'use client';

import { useFrame } from '@react-three/fiber';
import type { MutableRefObject } from 'react';
import { Vector3 } from 'three';

import type { CameraMode } from '@/lib/sim/config';
import { damp } from '@/lib/sim/math';
import type { VehicleState } from '@/lib/sim/vehicle/dynamics';

const temp = new Vector3();
const look = new Vector3();
const up = new Vector3(0, 1, 0);

const offsets: Record<CameraMode, Vector3> = {
  chase: new Vector3(0, 5.3, -11.9),
  hood: new Vector3(0, 2.7, 2.95),
  cinematic: new Vector3(-8.9, 7.2, -9.2),
  top: new Vector3(0, 32, -0.1),
  lidar: new Vector3(0, 3.45, 0.9),
  'debug-dynamics': new Vector3(5.5, 4.2, -2.2),
  'sensor-inspect': new Vector3(-2.2, 4.5, 1.4),
  'drone-follow': new Vector3(0, 5.8, -13),
  'drone-mission': new Vector3(0, 8, -5),
  'drone-survey': new Vector3(0, 24, 0),
};

export function CameraRig({ stateRef, mode }: { stateRef: MutableRefObject<VehicleState>; mode: CameraMode }): null {
  useFrame((renderState, dt) => {
    const { camera, clock } = renderState;
    const state = stateRef.current;
    const offset = offsets[mode].clone().applyAxisAngle(up, state.heading);

    const vibration = state.kind === 'tractor' ? (1 - state.stability) * 0.18 + state.suspensionActivity * 0.06 : 0;
    const shakeX = Math.sin(clock.elapsedTime * 26) * vibration;
    const shakeY = Math.cos(clock.elapsedTime * 29) * vibration * 0.7;

    temp.set(state.x + offset.x + shakeX, state.y + offset.y + shakeY, state.z + offset.z);

    const responsiveness = mode === 'cinematic' ? 2.2 : mode === 'top' ? 3.8 : 5.1;
    camera.position.x = damp(camera.position.x, temp.x, responsiveness, dt);
    camera.position.y = damp(camera.position.y, temp.y, responsiveness, dt);
    camera.position.z = damp(camera.position.z, temp.z, responsiveness, dt);

    const lookHeight = mode === 'top' || mode === 'drone-survey' ? 0 : 1.7;
    const lookForward = mode === 'hood' ? 30 : mode === 'cinematic' ? 9 : mode === 'sensor-inspect' ? 4 : 0;
    look.set(state.x, state.y + lookHeight, state.z + lookForward);
    camera.lookAt(look);
  });

  return null;
}
