import test from 'node:test';
import assert from 'node:assert/strict';

import { cameraModesForVehicle, defaultSettings } from '../../lib/sim/config';
import { createInputState } from '../../lib/sim/vehicle/controller';
import { defaultVehicleState, stepDrone } from '../../lib/sim/vehicle/dynamics';

test('vehicle camera mode presets are deterministic', () => {
  assert.deepEqual(cameraModesForVehicle('tractor'), ['chase', 'hood', 'cinematic', 'top', 'lidar', 'debug-dynamics', 'sensor-inspect']);
  assert.deepEqual(cameraModesForVehicle('drone'), ['drone-follow', 'drone-mission', 'drone-survey', 'top', 'lidar', 'cinematic']);
});

test('default simulator starts with tractor + survey-ready drone profile', () => {
  assert.equal(defaultSettings.vehicle, 'tractor');
  assert.equal(defaultSettings.droneMission, 'survey');
  assert.equal(defaultSettings.presentationMode, false);
  assert.equal(defaultSettings.lidarMode, 'sector-sweep');
});

test('drone mission profile affects forward speed envelope', () => {
  const base = defaultVehicleState('drone');
  const input = createInputState();
  input.throttle = 1;

  const spray = stepDrone(base, input, 1 / 60, 0, 'spray', true, 0);
  const lift = stepDrone(base, input, 1 / 60, 0, 'lift', true, 0);

  assert.ok(spray.forwardSpeed > lift.forwardSpeed, 'spray mission should be less sluggish than lift');
});

test('drone terrain-follow maintains minimum safety altitude', () => {
  const base = defaultVehicleState('drone');
  const input = createInputState();
  const next = stepDrone(base, input, 0.5, 2.2, 'survey', true, 0);
  assert.ok(next.y >= 3.3);
});
