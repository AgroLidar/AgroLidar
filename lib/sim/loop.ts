export interface SimClock {
  now: number;
  dt: number;
  frame: number;
}

export function makeClock(): SimClock {
  return { now: 0, dt: 0, frame: 0 };
}

export function tickClock(clock: SimClock, dt: number): SimClock {
  clock.now += dt;
  clock.dt = dt;
  clock.frame += 1;
  return clock;
}
