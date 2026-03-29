import { clamp, damp, wrapAngle } from '@/lib/sim/math';
import type { DriverInput } from '@/lib/sim/vehicle/controller';

export interface VehicleState {
  x: number;
  y: number;
  z: number;
  heading: number;
  speed: number;
  steerAngle: number;
  roll: number;
  pitch: number;
}

export function defaultVehicleState(): VehicleState {
  return { x: 0, y: 0, z: 0, heading: 0, speed: 0, steerAngle: 0, roll: 0, pitch: 0 };
}

export function stepVehicle(
  state: VehicleState,
  input: DriverInput,
  dt: number,
  gripPenalty: number,
  terrainPitch: number,
  terrainRoll: number,
): VehicleState {
  const traction = 1 - gripPenalty;
  const accel = input.throttle * 12 * traction;
  const braking = input.brake * 18;
  const drag = 1.6 + Math.abs(state.speed) * 0.14;
  const emergency = input.handbrake ? 24 : 0;
  const targetSteer = input.steer * 0.56;
  const steerAngle = damp(state.steerAngle, targetSteer, 10, dt);
  const speed = clamp(state.speed + (accel - braking - emergency - drag * Math.sign(state.speed)) * dt, -8, 26);
  const turnRate = steerAngle * (0.25 + Math.min(Math.abs(speed), 10) / 16);
  const heading = wrapAngle(state.heading + turnRate * dt);
  const dx = Math.sin(heading) * speed * dt;
  const dz = Math.cos(heading) * speed * dt;

  return {
    ...state,
    x: state.x + dx,
    z: state.z + dz,
    heading,
    speed,
    steerAngle,
    pitch: damp(state.pitch, terrainPitch, 7, dt),
    roll: damp(state.roll, terrainRoll + steerAngle * speed * -0.03, 6, dt),
  };
}
