export interface DriverInput {
  throttle: number;
  brake: number;
  steer: number;
  handbrake: boolean;
  ascend: number;
  descend: number;
  yaw: number;
}

export function createInputState(): DriverInput {
  return { throttle: 0, brake: 0, steer: 0, handbrake: false, ascend: 0, descend: 0, yaw: 0 };
}
