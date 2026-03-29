'use client';

import type { MutableRefObject } from 'react';

import { DroneVehicle } from '@/components/simulator/vehicles/DroneVehicle';
import { TractorVehicle } from '@/components/simulator/vehicles/TractorVehicle';
import type { DroneMissionMode, VehicleType } from '@/lib/sim/config';
import type { VehicleState } from '@/lib/sim/vehicle/dynamics';

export function Vehicle({ stateRef, type, mission }: { stateRef: MutableRefObject<VehicleState>; type: VehicleType; mission: DroneMissionMode }) {
  return type === 'drone' ? <DroneVehicle stateRef={stateRef} mission={mission} /> : <TractorVehicle stateRef={stateRef} />;
}
