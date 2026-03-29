export interface DriverInput {
  throttle: number;
  brake: number;
  steer: number;
  handbrake: boolean;
}

export function createInputState(): DriverInput {
  return { throttle: 0, brake: 0, steer: 0, handbrake: false };
}
