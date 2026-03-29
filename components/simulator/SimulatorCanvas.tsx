'use client';

import { Canvas, useFrame } from '@react-three/fiber';
import { useEffect, useMemo, useRef, useState } from 'react';

import { CameraRig } from '@/components/simulator/CameraRig';
import { LidarLayer } from '@/components/simulator/LidarLayer';
import { Vehicle } from '@/components/simulator/Vehicle';
import { World } from '@/components/simulator/World';
import type { LidarPoint } from '@/lib/sim/lidar/sensor';
import type { ChunkData } from '@/lib/sim/world/generator';
import { sampleLidarPoints } from '@/lib/sim/lidar/sensor';
import { ObstacleSpatialIndex } from '@/lib/sim/lidar/spatial-index';
import { computeHazards } from '@/lib/sim/lidar/hazards';
import { clamp } from '@/lib/sim/math';
import { scenarioFromId, weatherFromId } from '@/lib/sim/scenarios';
import { getStore, setSettings, setTelemetry, subscribe } from '@/lib/sim/store';
import { createInputState } from '@/lib/sim/vehicle/controller';
import { defaultVehicleState, stepVehicle, type VehicleState } from '@/lib/sim/vehicle/dynamics';
import { ChunkManager } from '@/lib/sim/world/chunks';
import { sampleTerrainHeight, sampleTerrainSurface } from '@/lib/sim/world/terrain';
import type { CameraMode, PointColorMode } from '@/lib/sim/config';

const cameraModes: CameraMode[] = ['chase', 'hood', 'cinematic', 'top', 'lidar'];
const lidarModes: PointColorMode[] = ['hazard', 'depth', 'class'];
const viewModes = ['hybrid', 'pointcloud', 'world', 'bev', 'depth'] as const;

export function SimulatorCanvas() {
  const [settingsVersion, setSettingsVersion] = useState(0);

  useEffect(() => subscribe(() => setSettingsVersion((v) => v + 1)), []);

  return (
    <div className="h-full w-full" data-settings-version={settingsVersion}>
      <Canvas shadows camera={{ position: [0, 8, -15], fov: 58 }}>
        <SimulationScene />
      </Canvas>
    </div>
  );
}

function SimulationScene() {
  const vehicleStateRef = useRef<VehicleState>(defaultVehicleState());
  const chunkManager = useMemo(() => new ChunkManager(44, 2), []);
  const lidarIndex = useMemo(() => new ObstacleSpatialIndex(10), []);
  const inputRef = useRef(createInputState());
  const [points, setPoints] = useState<LidarPoint[]>([]);
  const [chunks, setChunks] = useState<ChunkData[]>([]);
  const scanPhase = useRef(0);
  const fpsAccum = useRef({ frames: 0, t: 0, fps: 0 });

  useEffect(() => {
    const onKey = (event: KeyboardEvent, down: boolean): void => {
      if (event.key === 'w' || event.key === 'ArrowUp') inputRef.current.throttle = down ? 1 : 0;
      if (event.key === 's' || event.key === 'ArrowDown') inputRef.current.brake = down ? 1 : 0;
      if (event.key === 'a' || event.key === 'ArrowLeft') inputRef.current.steer = down ? -1 : inputRef.current.steer === -1 ? 0 : inputRef.current.steer;
      if (event.key === 'd' || event.key === 'ArrowRight') inputRef.current.steer = down ? 1 : inputRef.current.steer === 1 ? 0 : inputRef.current.steer;
      if (event.key === ' ') inputRef.current.handbrake = down;
      if (down && event.key.toLowerCase() === 'c') cycleCamera();
      if (down && event.key.toLowerCase() === 'l') cycleLidar();
      if (down && event.key.toLowerCase() === 'm') setSettings({ minimapVisible: !getStore().settings.minimapVisible, viewMode: getStore().settings.viewMode === 'bev' ? 'hybrid' : 'bev' });
      if (down && event.key.toLowerCase() === 'h') setSettings({ hudVisible: !getStore().settings.hudVisible });
      if (down && event.key.toLowerCase() === 'p') setSettings({ paused: !getStore().settings.paused });
      if (down && event.key.toLowerCase() === 'r') vehicleStateRef.current = defaultVehicleState();
    };

    const cycleCamera = () => {
      const current = getStore().settings.cameraMode;
      const idx = cameraModes.indexOf(current);
      const next = cameraModes[(idx + 1) % cameraModes.length];
      setSettings({ cameraMode: next });
    };

    const cycleLidar = () => {
      const current = getStore().settings.pointColorMode;
      const idx = lidarModes.indexOf(current);
      const next = lidarModes[(idx + 1) % lidarModes.length];
      const nextView = viewModes[(viewModes.indexOf(getStore().settings.viewMode) + 1) % viewModes.length];
      setSettings({ pointColorMode: next, viewMode: nextView });
    };

    const down = (event: KeyboardEvent) => onKey(event, true);
    const up = (event: KeyboardEvent) => onKey(event, false);
    const onReset = () => { vehicleStateRef.current = defaultVehicleState(); };
    const onCycleCamera = () => cycleCamera();
    const onCycleLidar = () => cycleLidar();
    const onResetWorld = () => chunkManager.reset();

    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    window.addEventListener('sim-reset', onReset as EventListener);
    window.addEventListener('sim-camera-cycle', onCycleCamera as EventListener);
    window.addEventListener('sim-lidar-cycle', onCycleLidar as EventListener);
    window.addEventListener('sim-reset-world', onResetWorld as EventListener);

    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
      window.removeEventListener('sim-reset', onReset as EventListener);
      window.removeEventListener('sim-camera-cycle', onCycleCamera as EventListener);
      window.removeEventListener('sim-lidar-cycle', onCycleLidar as EventListener);
      window.removeEventListener('sim-reset-world', onResetWorld as EventListener);
    };
  }, [chunkManager]);

  useFrame((_, dt) => {
    const { settings } = getStore();
    const scenario = scenarioFromId(settings.scenario);
    const weather = weatherFromId(settings.weather);

    fpsAccum.current.frames += 1;
    fpsAccum.current.t += dt;
    if (fpsAccum.current.t >= 0.5) {
      fpsAccum.current.fps = fpsAccum.current.frames / fpsAccum.current.t;
      fpsAccum.current.frames = 0;
      fpsAccum.current.t = 0;
    }

    if (settings.paused) return;

    const terrainPitch = Math.sin(vehicleStateRef.current.x * 0.035) * scenario.terrainRoughness * (0.36 + scenario.slopeBias);
    const terrainRoll = Math.cos(vehicleStateRef.current.z * 0.028) * scenario.terrainRoughness * (0.28 + scenario.slopeBias * 0.6);
    if (settings.autopilot) {
      inputRef.current.throttle = 0.76;
      inputRef.current.steer = Math.sin(performance.now() * 0.00025) * 0.28;
      inputRef.current.brake = 0;
    }

    const surface = sampleTerrainSurface(vehicleStateRef.current.x, vehicleStateRef.current.z, settings.seed);
    const surfaceTraction = surface === 'mud' ? 0.52 : surface === 'wet' ? 0.68 : surface === 'grass' ? 0.84 : 0.78;

    vehicleStateRef.current = stepVehicle(vehicleStateRef.current, inputRef.current, dt, weather.gripPenalty + scenario.mud * 0.08, terrainPitch, terrainRoll, surfaceTraction);
    vehicleStateRef.current.y = sampleTerrainHeight(vehicleStateRef.current.x, vehicleStateRef.current.z, settings.seed, scenario.terrainRoughness);

    const activeChunks = chunkManager.getActiveChunks(settings.seed, vehicleStateRef.current.x, vehicleStateRef.current.z, scenario, settings.hazardDensity);
    const obstacles = activeChunks.flatMap((chunk) => chunk.obstacles);
    const hazards = computeHazards(obstacles, vehicleStateRef.current.x, vehicleStateRef.current.z, settings.lidarRange);
    scanPhase.current += dt;

    const nextPoints = sampleLidarPoints(
      obstacles,
      {
        range: settings.lidarRange,
        horizontalFovDeg: settings.viewMode === 'bev' ? 170 : 130,
        channels: settings.quality === 'high' ? 28 : settings.quality === 'medium' ? 16 : 10,
        pointBudget: Math.floor((settings.quality === 'high' ? 19000 : settings.quality === 'medium' ? 12000 : 7000) * settings.lidarDensity),
        dropout: clamp(0.01 + (1 - settings.lidarDensity) * 0.12, 0.01, 0.15),
      },
      scanPhase.current,
      weather,
      {
        x: vehicleStateRef.current.x,
        y: vehicleStateRef.current.y + 2,
        z: vehicleStateRef.current.z,
        heading: vehicleStateRef.current.heading,
      },
      settings.seed,
      lidarIndex,
    );

    if (Math.floor(scanPhase.current * 22) % 2 === 0) {
      setPoints(nextPoints);
      setChunks(activeChunks);
    }

    const nearest = hazards[0]?.distance ?? Infinity;
    const classes = Array.from(new Set(hazards.slice(0, 8).map((h) => h.obstacle.cls)));
    setTelemetry({
      speed: vehicleStateRef.current.speed,
      nearestHazard: nearest,
      risk: nearest < 8 ? 'CRITICAL' : nearest < 18 ? 'CAUTION' : 'SAFE',
      pointCount: nextPoints.length,
      latencyMs: 11 + nextPoints.length * 0.0013,
      classes,
      seed: settings.seed,
      scenarioLabel: scenario.label,
      cameraMode: settings.cameraMode,
      frameRate: fpsAccum.current.fps,
    });
  });

  const settings = getStore().settings;
  const weather = weatherFromId(settings.weather);
  const scenario = scenarioFromId(settings.scenario);

  return (
    <>
      <World
        chunks={chunks}
        weatherSky={weather.sky}
        seed={settings.seed}
        terrainRoughness={scenario.terrainRoughness}
        wetness={weather.groundWetness}
        viewMode={settings.viewMode}
      />
      <Vehicle stateRef={vehicleStateRef} />
      <LidarLayer
        points={points}
        visible={settings.viewMode !== 'world'}
        colorMode={settings.viewMode === 'depth' ? 'depth' : settings.pointColorMode}
      />
      <CameraRig stateRef={vehicleStateRef} mode={settings.cameraMode} />
    </>
  );
}
