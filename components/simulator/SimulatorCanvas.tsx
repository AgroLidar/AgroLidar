'use client';

import { Canvas, useFrame } from '@react-three/fiber';
import { useEffect, useMemo, useRef, useState } from 'react';

import { CameraRig } from '@/components/simulator/CameraRig';
import { LidarLayer } from '@/components/simulator/LidarLayer';
import { Vehicle } from '@/components/simulator/Vehicle';
import { World } from '@/components/simulator/World';
import type { CameraMode, DroneMissionMode, LidarMode, PointColorMode, VehicleType, ViewMode } from '@/lib/sim/config';
import { cameraModesForVehicle } from '@/lib/sim/config';
import { computeHazards } from '@/lib/sim/lidar/hazards';
import { ObstacleSpatialIndex } from '@/lib/sim/lidar/spatial-index';
import type { LidarPoint } from '@/lib/sim/lidar/sensor';
import { sampleLidarPoints } from '@/lib/sim/lidar/sensor';
import { clamp } from '@/lib/sim/math';
import { scenarioFromId, weatherFromId } from '@/lib/sim/scenarios';
import { getStore, setSettings, setTelemetry, subscribe } from '@/lib/sim/store';
import { createInputState } from '@/lib/sim/vehicle/controller';
import { defaultVehicleState, stepDrone, stepVehicle, type VehicleState } from '@/lib/sim/vehicle/dynamics';
import { ChunkManager } from '@/lib/sim/world/chunks';
import type { ChunkData } from '@/lib/sim/world/generator';
import { sampleTerrainHeight, sampleTerrainSurface } from '@/lib/sim/world/terrain';

const lidarModes: PointColorMode[] = ['hazard', 'depth', 'class', 'coverage'];
const viewModes: ViewMode[] = ['hybrid', 'pointcloud', 'world', 'bev', 'depth', 'hazard'];
const missionModes: DroneMissionMode[] = ['spray', 'spread', 'lift', 'survey'];
const lidarSensorModes: LidarMode[] = ['sector-sweep', 'spin-360', 'forward-static', 'survey-grid', 'bev-hazard'];

const qualityProfiles = {
  low: { channels: 12, budget: 7600, shadows: false },
  medium: { channels: 18, budget: 12600, shadows: true },
  high: { channels: 28, budget: 19800, shadows: true },
  ultra: { channels: 40, budget: 30000, shadows: true },
} as const;

const lidarRigTuning = {
  'hazard-short-range': { rangeMul: 0.72, densityMul: 1.16, verticalFov: 22, rotationRate: 18 },
  'survey-rig': { rangeMul: 1.2, densityMul: 1.05, verticalFov: 30, rotationRate: 12 },
  'dense-edge-rig': { rangeMul: 1, densityMul: 1.28, verticalFov: 26, rotationRate: 16 },
  'wide-fov-rig': { rangeMul: 0.94, densityMul: 1.1, verticalFov: 34, rotationRate: 15 },
  'performance-safe': { rangeMul: 0.84, densityMul: 0.75, verticalFov: 20, rotationRate: 10 },
} as const;

function resolveVehicleCollisions(state: VehicleState, obstacles: { x: number; z: number; radius: number }[], dt: number): VehicleState {
  let nx = state.x;
  let nz = state.z;
  let speed = state.speed;
  let stability = state.stability;
  for (const obstacle of obstacles) {
    const dx = nx - obstacle.x;
    const dz = nz - obstacle.z;
    const distance = Math.hypot(dx, dz);
    const minDistance = obstacle.radius + 1.9;
    if (distance <= 0 || distance >= minDistance) continue;
    const penetration = minDistance - distance;
    const push = Math.min(0.45, penetration * 0.66);
    nx += (dx / distance) * push;
    nz += (dz / distance) * push;
    speed *= Math.max(0.22, 1 - penetration * (1 + dt));
    stability = clamp(stability - penetration * 0.1, 0.2, 1);
  }
  return { ...state, x: nx, z: nz, speed, stability };
}

export function SimulatorCanvas() {
  const [settingsVersion, setSettingsVersion] = useState(0);
  const settings = getStore().settings;
  const dpr = useMemo(() => {
    const native = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
    const cap = settings.presentationMode ? 2 : 1.6;
    return clamp(native * settings.renderScale, 0.75, cap);
  }, [settings.presentationMode, settings.renderScale]);

  useEffect(() => subscribe(() => setSettingsVersion((v) => v + 1)), []);

  return (
    <div className="h-full w-full" data-settings-version={settingsVersion}>
      <Canvas dpr={dpr} shadows={qualityProfiles[settings.quality].shadows} camera={{ position: [0, 8, -15], fov: settings.presentationMode ? 52 : 58 }} gl={{ antialias: true, powerPreference: settings.presentationMode ? 'high-performance' : 'default' }}>
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
  const missionProgress = useRef(0);
  const lastVehicle = useRef<VehicleType>('tractor');

  useEffect(() => {
    const onKey = (event: KeyboardEvent, down: boolean): void => {
      const k = event.key.toLowerCase();
      if (k === 'w' || event.key === 'ArrowUp') inputRef.current.throttle = down ? 1 : 0;
      if (k === 's' || event.key === 'ArrowDown') inputRef.current.brake = down ? 1 : 0;
      if (k === 'a' || event.key === 'ArrowLeft') inputRef.current.steer = down ? -1 : inputRef.current.steer === -1 ? 0 : inputRef.current.steer;
      if (k === 'd' || event.key === 'ArrowRight') inputRef.current.steer = down ? 1 : inputRef.current.steer === 1 ? 0 : inputRef.current.steer;
      if (event.key === ' ') inputRef.current.ascend = down ? 1 : 0;
      if (k === 'shift') inputRef.current.descend = down ? 1 : 0;
      if (k === 'q') inputRef.current.yaw = down ? -1 : inputRef.current.yaw === -1 ? 0 : inputRef.current.yaw;
      if (k === 'e') inputRef.current.yaw = down ? 1 : inputRef.current.yaw === 1 ? 0 : inputRef.current.yaw;
      if (down && k === 'c') cycleCamera();
      if (down && k === 'l') cycleLidar();
      if (down && k === 'x') cycleLidarMode();
      if (down && k === 'm') setSettings({ minimapVisible: !getStore().settings.minimapVisible, viewMode: getStore().settings.viewMode === 'bev' ? 'hybrid' : 'bev' });
      if (down && k === 'h') setSettings({ hudVisible: !getStore().settings.hudVisible });
      if (down && k === 'p') setSettings({ paused: !getStore().settings.paused });
      if (down && k === 'r') vehicleStateRef.current = defaultVehicleState(getStore().settings.vehicle);
      if (down && k === 'v') switchVehicle(getStore().settings.vehicle === 'tractor' ? 'drone' : 'tractor');
      if (down && ['1', '2', '3', '4'].includes(event.key)) {
        const idx = Number(event.key) - 1;
        setSettings({ droneMission: missionModes[idx] });
      }
    };

    const cycleCamera = () => {
      const settings = getStore().settings;
      const modes = cameraModesForVehicle(settings.vehicle);
      const idx = Math.max(0, modes.indexOf(settings.cameraMode));
      setSettings({ cameraMode: modes[(idx + 1) % modes.length] });
    };

    const cycleLidar = () => {
      const current = getStore().settings.pointColorMode;
      const idx = lidarModes.indexOf(current);
      const next = lidarModes[(idx + 1) % lidarModes.length];
      const nextView = viewModes[(viewModes.indexOf(getStore().settings.viewMode) + 1) % viewModes.length];
      setSettings({ pointColorMode: next, viewMode: nextView });
    };

    const cycleLidarMode = () => {
      const current = getStore().settings.lidarMode;
      const idx = lidarSensorModes.indexOf(current);
      setSettings({ lidarMode: lidarSensorModes[(idx + 1) % lidarSensorModes.length] });
    };

    const switchVehicle = (nextVehicle: VehicleType) => {
      const current = vehicleStateRef.current;
      const swapped = defaultVehicleState(nextVehicle);
      swapped.x = current.x;
      swapped.z = current.z;
      swapped.heading = current.heading;
      swapped.y = nextVehicle === 'drone' ? current.y + 3.4 : current.y;
      vehicleStateRef.current = swapped;
      setSettings({ vehicle: nextVehicle, cameraMode: nextVehicle === 'drone' ? 'drone-follow' : 'chase' });
    };

    const down = (event: KeyboardEvent) => onKey(event, true);
    const up = (event: KeyboardEvent) => onKey(event, false);
    const onReset = () => { vehicleStateRef.current = defaultVehicleState(getStore().settings.vehicle); };
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

    if (settings.vehicle !== lastVehicle.current) {
      const next = defaultVehicleState(settings.vehicle);
      next.x = vehicleStateRef.current.x;
      next.z = vehicleStateRef.current.z;
      next.heading = vehicleStateRef.current.heading;
      next.y = settings.vehicle === 'drone' ? vehicleStateRef.current.y + 3.4 : sampleTerrainHeight(vehicleStateRef.current.x, vehicleStateRef.current.z, settings.seed, scenario.terrainRoughness);
      vehicleStateRef.current = next;
      lastVehicle.current = settings.vehicle;
    }

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
      inputRef.current.throttle = settings.vehicle === 'drone' ? 0.58 : 0.74;
      inputRef.current.steer = Math.sin(performance.now() * 0.00025) * 0.3;
      inputRef.current.brake = 0;
      inputRef.current.yaw = Math.sin(performance.now() * 0.00016) * 0.55;
    }

    const activeChunks = chunkManager.getActiveChunks(settings.seed, vehicleStateRef.current.x, vehicleStateRef.current.z, scenario, settings.hazardDensity);
    const obstacles = activeChunks.flatMap((chunk) => chunk.obstacles);

    const terrainY = sampleTerrainHeight(vehicleStateRef.current.x, vehicleStateRef.current.z, settings.seed, scenario.terrainRoughness);
    const surface = sampleTerrainSurface(vehicleStateRef.current.x, vehicleStateRef.current.z, settings.seed);

    if (settings.vehicle === 'tractor') {
      const surfaceTraction =
        surface === 'mud' ? 0.46 :
        surface === 'wet' ? 0.62 :
        surface === 'grass' ? 0.8 : 0.86;
      const stepped = stepVehicle(vehicleStateRef.current, inputRef.current, dt, weather.gripPenalty + scenario.mud * 0.09, terrainPitch, terrainRoll, surfaceTraction);
      vehicleStateRef.current = resolveVehicleCollisions(stepped, obstacles, dt);
      vehicleStateRef.current.y = terrainY;
    } else {
      const wind = Math.sin(scanPhase.current * 0.4 + settings.seed * 0.001) * (weather.id === 'light-rain' ? 1.4 : 0.8);
      vehicleStateRef.current = stepDrone(vehicleStateRef.current, inputRef.current, dt, terrainY, settings.droneMission, settings.terrainFollow, wind);
      missionProgress.current = (missionProgress.current + dt * (settings.droneMission === 'lift' ? 1.8 : 3.2)) % 100;
    }

    const rig = lidarRigTuning[settings.lidarRigPreset];
    const baseRange = settings.vehicle === 'drone' ? settings.lidarRange * 1.3 : settings.lidarRange;
    const hazardRange = baseRange * rig.rangeMul;
    const hazards = computeHazards(obstacles, vehicleStateRef.current.x, vehicleStateRef.current.z, hazardRange, vehicleStateRef.current.heading);
    scanPhase.current += dt;

    const quality = qualityProfiles[settings.quality];
    const fovByMode =
      settings.lidarMode === 'spin-360' ? 360 :
      settings.lidarMode === 'forward-static' ? 105 :
      settings.lidarMode === 'survey-grid' ? 240 :
      settings.lidarMode === 'bev-hazard' ? 180 :
      settings.vehicle === 'drone' ? 170 : 130;

    const sampleResult = sampleLidarPoints(
      obstacles,
      {
        range: hazardRange,
        horizontalFovDeg: fovByMode,
        channels: quality.channels,
        pointBudget: Math.floor(quality.budget * settings.lidarDensity * rig.densityMul),
        dropout: clamp(0.01 + (1 - settings.lidarDensity) * 0.12 + (settings.vehicle === 'drone' ? 0.02 : 0), 0.01, 0.18),
        verticalFovDeg: rig.verticalFov,
        rotationRateHz: rig.rotationRate,
        mode: settings.lidarMode,
        semanticColoring: settings.semanticColoring,
      },
      scanPhase.current,
      weather,
      {
        x: vehicleStateRef.current.x + Math.sin(vehicleStateRef.current.heading) * 0.25,
        y: vehicleStateRef.current.y + (settings.vehicle === 'drone' ? 0 : 2.45),
        z: vehicleStateRef.current.z + Math.cos(vehicleStateRef.current.heading) * 0.82,
        heading: vehicleStateRef.current.heading,
        pitch: vehicleStateRef.current.pitch,
        roll: vehicleStateRef.current.roll,
      },
      settings.seed,
      lidarIndex,
    );

    if (Math.floor(scanPhase.current * (settings.vehicle === 'drone' ? 16 : 22)) % 2 === 0) {
      setPoints(sampleResult.points);
      setChunks(activeChunks);
    }

    const nearest = hazards[0]?.distance ?? Infinity;
    const classes = Array.from(new Set(hazards.slice(0, 8).map((h) => h.obstacle.cls)));
    const coverageRate = settings.vehicle === 'drone' ? missionProgress.current : 0;
    setTelemetry({
      speed: vehicleStateRef.current.speed,
      altitude: Math.max(0, vehicleStateRef.current.y - terrainY),
      headingDeg: ((vehicleStateRef.current.heading * 180) / Math.PI + 360) % 360,
      steeringDeg: (vehicleStateRef.current.steerAngle * 180) / Math.PI,
      nearestHazard: nearest,
      risk: hazards[0]?.risk ?? 'SAFE',
      pointCount: sampleResult.points.length,
      latencyMs: (settings.vehicle === 'drone' ? 14 : 10) + sampleResult.points.length * 0.0016 + (100 - vehicleStateRef.current.stability * 100) * 0.04,
      classes,
      seed: settings.seed,
      scenarioLabel: scenario.label,
      cameraMode: settings.cameraMode,
      frameRate: fpsAccum.current.fps,
      vehicle: settings.vehicle,
      droneMission: settings.droneMission,
      payloadPct: vehicleStateRef.current.payload * 100,
      coveragePct: coverageRate,
      routeProgressPct: coverageRate,
      surfaceType: surface,
      slipRatio: vehicleStateRef.current.slipRatio,
      tractionPct: vehicleStateRef.current.traction * 100,
      rollDeg: (vehicleStateRef.current.roll * 180) / Math.PI,
      pitchDeg: (vehicleStateRef.current.pitch * 180) / Math.PI,
      suspensionActivityPct: vehicleStateRef.current.suspensionActivity * 100,
      stabilityPct: vehicleStateRef.current.stability * 100,
      lidarMode: settings.lidarMode,
      lidarRigPreset: settings.lidarRigPreset,
      scanCoveragePct: sampleResult.scanCoveragePct,
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
      <Vehicle stateRef={vehicleStateRef} type={settings.vehicle} mission={settings.droneMission} />
      <LidarLayer
        points={points}
        visible={settings.viewMode !== 'world'}
        colorMode={settings.viewMode === 'depth' ? 'depth' : settings.pointColorMode}
      />
      <CameraRig stateRef={vehicleStateRef} mode={settings.cameraMode as CameraMode} />
    </>
  );
}
