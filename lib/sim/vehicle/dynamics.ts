import { clamp, damp, wrapAngle } from '@/lib/sim/math';
import type { DroneMissionMode, VehicleType } from '@/lib/sim/config';
import type { DriverInput } from '@/lib/sim/vehicle/controller';

export interface VehicleState {
  kind: VehicleType;
  x: number;
  y: number;
  z: number;
  heading: number;
  speed: number;
  forwardSpeed: number;
  lateralSpeed: number;
  verticalSpeed: number;
  steerAngle: number;
  roll: number;
  pitch: number;
  wheelSpin: number;
  suspensionTravel: number;
  payload: number;
}

export function defaultVehicleState(kind: VehicleType = 'tractor'): VehicleState {
  return {
    kind,
    x: 0,
    y: kind === 'drone' ? 2.5 : 0,
    z: 0,
    heading: 0,
    speed: 0,
    forwardSpeed: 0,
    lateralSpeed: 0,
    verticalSpeed: 0,
    steerAngle: 0,
    roll: 0,
    pitch: 0,
    wheelSpin: 0,
    suspensionTravel: 0,
    payload: 1,
  };
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
  if (state.kind === 'drone') return state;
  const traction = clamp((1 - gripPenalty) * surfaceTraction, 0.28, 1);
  const heavyMassFactor = 1.18 + (1 - traction) * 0.5;
  const accel = (input.throttle * 7.2 * traction) / heavyMassFactor;
  const reverseAccel = (input.brake * 4.2) / heavyMassFactor;
  const rollingResistance = 2.4 + Math.abs(state.speed) * 0.22;
  const emergency = input.handbrake ? 14 : 0;
  const targetSteer = input.steer * clamp(0.5 - Math.abs(state.speed) * 0.011, 0.16, 0.5);
  const steerAngle = damp(state.steerAngle, targetSteer, 4.2, dt);
  const forwardForce = accel - (input.throttle > 0 ? rollingResistance * 0.25 : rollingResistance * Math.sign(state.speed));
  const brakingForce = input.brake > 0 ? 10.8 * input.brake : 0;
  const speed = clamp(state.speed + (forwardForce - brakingForce - emergency - reverseAccel * (state.speed > 0 ? 0.35 : -1)) * dt, -4.2, 14.8);

  const steeringDamping = clamp(Math.abs(speed) / 11, 0.16, 1);
  const turnRate = steerAngle * steeringDamping * (0.14 + traction * 0.18);
  const heading = wrapAngle(state.heading + turnRate * dt);
  const dx = Math.sin(heading) * speed * dt;
  const dz = Math.cos(heading) * speed * dt;

  const suspensionTarget = clamp((Math.abs(terrainPitch) + Math.abs(terrainRoll)) * 0.42 + Math.abs(speed) * 0.006, 0.02, 0.19);

  return {
    ...state,
    x: state.x + dx,
    z: state.z + dz,
    heading,
    speed,
    steerAngle,
    pitch: damp(state.pitch, terrainPitch, 4.2, dt),
    roll: damp(state.roll, terrainRoll + steerAngle * speed * -0.026 * (2 - traction), 3.2, dt),
    wheelSpin: state.wheelSpin + speed * dt * 1.7,
    suspensionTravel: damp(state.suspensionTravel, suspensionTarget, 8, dt),
  };
}

export function stepDrone(
  state: VehicleState,
  input: DriverInput,
  dt: number,
  terrainHeight: number,
  mission: DroneMissionMode,
  terrainFollow: boolean,
  wind: number,
): VehicleState {
  const missionMass = mission === 'lift' ? 1.2 : mission === 'spread' ? 1.08 : mission === 'spray' ? 1.12 : 1;
  const maxForward = 11 / missionMass;
  const maxStrafe = 7.5 / missionMass;
  const maxClimb = 4.8 / missionMass;
  const targetForward = clamp((input.throttle - input.brake) * maxForward, -maxForward * 0.55, maxForward);
  const targetLateral = clamp(input.steer * maxStrafe, -maxStrafe, maxStrafe);
  const targetVertical = clamp((input.ascend - input.descend) * maxClimb, -maxClimb, maxClimb);

  const payloadDrain = mission === 'survey' ? 0.01 : mission === 'lift' ? 0.018 : 0.025;
  const payload = clamp(state.payload - payloadDrain * dt * (Math.abs(targetForward) * 0.06 + 0.22), 0.1, 1);
  const payloadFactor = 1 + (1 - payload) * 0.18;

  const forwardSpeed = damp(state.forwardSpeed, targetForward / payloadFactor, 2.5, dt);
  const lateralSpeed = damp(state.lateralSpeed, targetLateral / payloadFactor, 2.4, dt);
  const verticalSpeed = damp(state.verticalSpeed, targetVertical, 2.1, dt);

  const yawRate = input.yaw * (mission === 'lift' ? 0.7 : 1) * 1.2;
  const heading = wrapAngle(state.heading + yawRate * dt);

  const cosH = Math.cos(heading);
  const sinH = Math.sin(heading);
  const worldX = sinH * forwardSpeed + cosH * lateralSpeed + wind * 0.16;
  const worldZ = cosH * forwardSpeed - sinH * lateralSpeed + wind * 0.08;

  let y = state.y + verticalSpeed * dt;
  const followTarget = terrainHeight + (mission === 'survey' ? 8.5 : 4.2);
  if (terrainFollow && input.ascend === 0 && input.descend === 0) {
    y = damp(y, followTarget, 1.8, dt);
  }
  y = Math.max(terrainHeight + 1.1, y);

  return {
    ...state,
    x: state.x + worldX * dt,
    z: state.z + worldZ * dt,
    y,
    heading,
    forwardSpeed,
    lateralSpeed,
    verticalSpeed,
    speed: Math.hypot(forwardSpeed, lateralSpeed),
    roll: damp(state.roll, clamp(-lateralSpeed * 0.05, -0.3, 0.3), 3.4, dt),
    pitch: damp(state.pitch, clamp(-forwardSpeed * 0.04, -0.32, 0.32), 3.4, dt),
    payload,
  };
}
