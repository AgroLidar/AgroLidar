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
  suspensionActivity: number;
  payload: number;
  slipRatio: number;
  traction: number;
  wheelLoadFront: number;
  wheelLoadRear: number;
  stability: number;
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
    suspensionActivity: 0,
    payload: 1,
    slipRatio: 0,
    traction: 1,
    wheelLoadFront: 0.5,
    wheelLoadRear: 0.5,
    stability: 1,
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

  const speedSign = state.speed >= 0 ? 1 : -1;
  const targetSteer = input.steer * clamp(0.56 - Math.abs(state.speed) * 0.015, 0.16, 0.56);
  const steerAngle = damp(state.steerAngle, targetSteer, 5.2, dt);

  const loadTransferLong = clamp((input.throttle - input.brake) * 0.16 + terrainPitch * 0.5, -0.2, 0.2);
  const loadTransferLat = clamp(steerAngle * Math.abs(state.speed) * 0.07 + terrainRoll * 0.34, -0.22, 0.22);
  const wheelLoadFront = clamp(0.5 - loadTransferLong, 0.32, 0.68);
  const wheelLoadRear = clamp(1 - wheelLoadFront, 0.32, 0.68);

  const baseTraction = clamp((1 - gripPenalty) * surfaceTraction, 0.26, 1);
  const tractionFromSlip = clamp(1 - Math.abs(state.slipRatio) * 0.9, 0.4, 1);
  const traction = clamp(baseTraction * tractionFromSlip, 0.24, 1);

  const engineTorque = (10.8 + (Math.abs(state.speed) < 4 ? 4.8 : 0)) * input.throttle * (0.72 + wheelLoadRear * 0.55);
  const brakeTorque = (9.6 + (input.handbrake ? 8 : 0)) * input.brake * (0.7 + wheelLoadFront * 0.6);
  const slopeDrag = terrainPitch * 8.2;
  const rollingResistance = 2.5 + Math.abs(state.speed) * 0.38 + Math.abs(loadTransferLat) * 2.4;

  const accelForce = engineTorque * traction - rollingResistance * speedSign - slopeDrag;
  const brakeForce = brakeTorque * (state.speed > 0 ? 1 : -0.8);
  const reverseAssist = input.brake > 0.1 && state.speed < 0.2 ? input.brake * 5.2 : 0;

  let speed = state.speed + (accelForce - brakeForce - reverseAssist) * dt * 0.6;
  speed = clamp(speed, -5.5, 18.8);

  const yawAuthority = clamp(0.1 + traction * 0.22, 0.08, 0.28);
  const yawDamping = clamp(1 - Math.abs(state.speed) / 28, 0.38, 1);
  const turnRate = steerAngle * (0.4 + Math.abs(speed) * 0.11) * yawAuthority * yawDamping;
  const heading = wrapAngle(state.heading + turnRate * dt);

  const dx = Math.sin(heading) * speed * dt;
  const dz = Math.cos(heading) * speed * dt;

  const desiredSlip = clamp((engineTorque - traction * 8) / 12 + Math.abs(loadTransferLat) * 0.4, -0.7, 0.7);
  const slipRatio = damp(state.slipRatio, desiredSlip, 4.8, dt);

  const bodyRollTarget = terrainRoll + loadTransferLat * (1.6 - traction * 0.75);
  const bodyPitchTarget = terrainPitch - loadTransferLong * 1.2;
  const suspensionTarget = clamp(0.025 + Math.abs(loadTransferLat) * 0.15 + Math.abs(terrainPitch) * 0.12 + Math.abs(speed) * 0.005, 0.02, 0.24);
  const suspensionTravel = damp(state.suspensionTravel, suspensionTarget, 8.2, dt);
  const suspensionActivity = clamp(Math.abs(suspensionTravel - state.suspensionTravel) * 35 + Math.abs(terrainRoll) * 0.9, 0, 1);

  const instability = clamp(Math.abs(slipRatio) * 0.45 + Math.abs(loadTransferLat) * 0.6 + suspensionActivity * 0.4, 0, 1);
  const stability = clamp(1 - instability, 0.2, 1);

  return {
    ...state,
    x: state.x + dx,
    z: state.z + dz,
    heading,
    speed,
    steerAngle,
    pitch: damp(state.pitch, bodyPitchTarget, 4.2, dt),
    roll: damp(state.roll, bodyRollTarget, 3.4, dt),
    wheelSpin: state.wheelSpin + speed * dt * 2.2,
    suspensionTravel,
    suspensionActivity,
    slipRatio,
    traction,
    wheelLoadFront,
    wheelLoadRear,
    stability,
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
