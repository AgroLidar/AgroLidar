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
  wheelSpin: number;
  suspensionTravel: number;
}

export function defaultVehicleState(): VehicleState {
  return { x: 0, y: 0, z: 0, heading: 0, speed: 0, steerAngle: 0, roll: 0, pitch: 0, wheelSpin: 0, suspensionTravel: 0 };
}

export function stepVehicle(
  state: VehicleState,
  input: DriverInput,
  dt: number,
  gripPenalty: number,
  terrainPitch: number,
  terrainRoll: number,
  surfaceTraction: number,
): VehicleState {
  const traction = clamp((1 - gripPenalty) * surfaceTraction, 0.35, 1);
  const accel = input.throttle * 8.4 * traction;
  const reverseAccel = input.brake * 5.2;
  const rollingResistance = 1.9 + Math.abs(state.speed) * 0.18;
  const emergency = input.handbrake ? 16 : 0;
  const targetSteer = input.steer * 0.48;
  const steerAngle = damp(state.steerAngle, targetSteer, 5.8, dt);
  const forwardForce = accel - (input.throttle > 0 ? 0 : rollingResistance * Math.sign(state.speed));
  const brakingForce = input.brake > 0 ? 11.5 * input.brake : 0;
  const speed = clamp(state.speed + (forwardForce - brakingForce - emergency - reverseAccel * (state.speed > 0 ? 0.35 : -1)) * dt, -5.5, 17);

  const steeringDamping = clamp(Math.abs(speed) / 10, 0.2, 1);
  const turnRate = steerAngle * steeringDamping * (0.18 + traction * 0.2);
  const heading = wrapAngle(state.heading + turnRate * dt);
  const dx = Math.sin(heading) * speed * dt;
  const dz = Math.cos(heading) * speed * dt;

  const suspensionTarget = clamp((Math.abs(terrainPitch) + Math.abs(terrainRoll)) * 0.4 + Math.abs(speed) * 0.004, 0.02, 0.16);

  return {
    ...state,
    x: state.x + dx,
    z: state.z + dz,
    heading,
    speed,
    steerAngle,
    pitch: damp(state.pitch, terrainPitch, 4.2, dt),
    roll: damp(state.roll, terrainRoll + steerAngle * speed * -0.02 * (2 - traction), 4, dt),
    wheelSpin: state.wheelSpin + speed * dt * 1.7,
    suspensionTravel: damp(state.suspensionTravel, suspensionTarget, 8, dt),
  };
}
