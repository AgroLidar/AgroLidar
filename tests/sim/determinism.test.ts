import test from 'node:test';
import assert from 'node:assert/strict';

import { hashStringToSeed } from '../../lib/sim/rng';
import { SCENARIOS, WEATHER_PRESETS } from '../../lib/sim/scenarios';
import { generateChunk } from '../../lib/sim/world/generator';
import { computeHazards } from '../../lib/sim/lidar/hazards';
import { sampleLidarPoints } from '../../lib/sim/lidar/sensor';
import { ObstacleSpatialIndex } from '../../lib/sim/lidar/spatial-index';

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

test('scenario presets produce distinct composition', () => {
  const seed = 91231;
  const orchardChunk = generateChunk(seed, 1, 1, 44, SCENARIOS['orchard-rows'], 0.45);
  const roughChunk = generateChunk(seed, 1, 1, 44, SCENARIOS['rough-field-edge'], 0.45);
  assert.notDeepEqual(orchardChunk.obstacles, roughChunk.obstacles);
  assert.notEqual(SCENARIOS['orchard-rows'].cropRows, SCENARIOS['rough-field-edge'].cropRows);
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

test('lidar sensor sampling is deterministic for fixed scan phase', () => {
  const spatial = new ObstacleSpatialIndex(10);
  const obstacles = [
    { id: 'h1', cls: 'human' as const, x: 8, y: 0, z: 2, radius: 0.6, hazard: true },
    { id: 't1', cls: 'tree' as const, x: 18, y: 0, z: -1, radius: 1.3, hazard: false },
  ];

  const run = () => sampleLidarPoints(
    obstacles,
    {
      range: 40,
      horizontalFovDeg: 120,
      channels: 12,
      pointBudget: 1400,
      dropout: 0.01,
      verticalFovDeg: 24,
      rotationRateHz: 15,
      mode: 'sector-sweep',
      semanticColoring: true,
    },
    0.35,
    WEATHER_PRESETS.clear,
    { x: 0, y: 2, z: 0, heading: 0, pitch: 0, roll: 0 },
    1337,
    spatial,
  );

  assert.deepEqual(run(), run());
});
