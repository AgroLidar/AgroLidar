import test from 'node:test';
import assert from 'node:assert/strict';

import { hashStringToSeed } from '../../lib/sim/rng';
import { SCENARIOS } from '../../lib/sim/scenarios';
import { generateChunk } from '../../lib/sim/world/generator';
import { computeHazards } from '../../lib/sim/lidar/hazards';

test('seed hash is deterministic', () => {
  const a = hashStringToSeed('seed-alpha');
  const b = hashStringToSeed('seed-alpha');
  const c = hashStringToSeed('seed-beta');
  assert.equal(a, b);
  assert.notEqual(a, c);
});

test('chunk generation is deterministic for same seed and scenario', () => {
  const scenario = SCENARIOS['farm-road'];
  const first = generateChunk(1234, 2, -1, 44, scenario, 0.5);
  const second = generateChunk(1234, 2, -1, 44, scenario, 0.5);
  assert.deepEqual(first, second);
});

test('hazard scoring sorts by nearest distance', () => {
  const hazards = computeHazards(
    [
      { id: 'a', cls: 'rock', x: 20, y: 0, z: 0, radius: 1, hazard: true },
      { id: 'b', cls: 'human', x: 4, y: 0, z: 0, radius: 1, hazard: true },
    ],
    0,
    0,
    50,
  );
  assert.equal(hazards[0]?.obstacle.id, 'b');
  assert.equal(hazards[0]?.risk, 'CRITICAL');
});
