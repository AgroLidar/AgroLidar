'use client';

import { Canvas, useFrame } from '@react-three/fiber';
import { useEffect, useMemo, useRef, useState } from 'react';

import { CameraRig } from '@/components/simulator/CameraRig';
import { LidarLayer } from '@/components/simulator/LidarLayer';
import { Vehicle } from '@/components/simulator/Vehicle';
import { World } from '@/components/simulator/World';
import { cameraModesForVehicle, type CameraMode, type DroneMissionMode, type PointColorMode, type VehicleType, type ViewMode } from '@/lib/sim/config';
import { createRunExport, downloadRunExport } from '@/lib/sim/export/run-export';
import { runLidarPipeline } from '@/lib/sim/lidar/pipeline';
import { ObstacleSpatialIndex } from '@/lib/sim/lidar/spatial-index';
import type { LidarPoint } from '@/lib/sim/lidar/sensor';
import { clamp } from '@/lib/sim/math';
import { FIELD_PARCELS, MISSION_PROFILES } from '@/lib/sim/ops/missions';
import { scenarioFromId, weatherFromId } from '@/lib/sim/scenarios';
import { getStore, setSettings, setTelemetry, subscribe } from '@/lib/sim/store';
import { sampleTerrainAnalytics } from '@/lib/sim/terrain/analytics';
import { createInputState } from '@/lib/sim/vehicle/controller';
import { defaultVehicleState, stepDrone, stepVehicle, type VehicleState } from '@/lib/sim/vehicle/dynamics';
import { ChunkManager } from '@/lib/sim/world/chunks';
import type { ChunkData } from '@/lib/sim/world/generator';
import { sampleTerrainHeight, sampleTerrainSurface } from '@/lib/sim/world/terrain';

const lidarModes: PointColorMode[] = ['hazard', 'depth', 'class', 'coverage'];
const viewModes: ViewMode[] = ['hybrid', 'pointcloud', 'world', 'bev', 'depth', 'hazard'];
const missionModes: DroneMissionMode[] = ['spray', 'spread', 'lift', 'survey'];

const qualityProfiles = {
  low: { shadows: false },
  medium: { shadows: true },
  high: { shadows: true },
  ultra: { shadows: true },
} as const;

function resolveVehicleCollisions(
  state: VehicleState,
  obstacles: { x: number; z: number; radius: number; hazard: boolean; collision?: 'solid' | 'soft' | 'ghost' }[],
  dt: number,
): VehicleState {
  let nx = state.x;
  let nz = state.z;
  let speed = state.speed;
  let heading = state.heading;
  for (const obstacle of obstacles) {
    if (obstacle.collision === 'ghost') continue;
    const dx = nx - obstacle.x;
    const dz = nz - obstacle.z;
    const distance = Math.hypot(dx, dz);
    const vehicleRadius = 1.08;
    const buffer = obstacle.collision === 'soft' ? 0.02 : 0.08;
    const minDistance = obstacle.radius + vehicleRadius + buffer;
    if (distance <= 0 || distance >= minDistance) continue;
    const penetration = minDistance - distance;
    const contactWindow = obstacle.collision === 'soft' ? 0.06 : 0.12;
    if (penetration < contactWindow) continue;
    const resolvedPenetration = penetration - contactWindow;
    const pushStrength = obstacle.collision === 'soft' ? 0.18 : 0.34;
    const push = Math.min(obstacle.collision === 'soft' ? 0.1 : 0.22, resolvedPenetration * pushStrength);
    nx += (dx / distance) * push;
    nz += (dz / distance) * push;
    const speedLoss =
      obstacle.collision === 'soft' ? 0.04 : obstacle.hazard ? 0.18 : 0.12;
    speed *= Math.max(0.62, 1 - resolvedPenetration * speedLoss * (0.8 + dt));
    heading += (dx * 0.007 - dz * 0.007) * resolvedPenetration;
  }
  return { ...state, x: nx, z: nz, speed, heading };
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
  const eventLogRef = useRef<string[]>([]);

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

    const onExportRun = () => {
      const { settings, telemetry } = getStore();
      const payload = createRunExport({
        seed: settings.seed,
        scenario: settings.scenario,
        weather: settings.weather,
        vehicle: settings.vehicle,
        mission: settings.missionType,
        fieldParcel: settings.fieldParcelId,
        sensorPreset: settings.sensorPreset,
        telemetry,
        points: points.slice(0, 4200).map((point) => ({ x: point.x, y: point.y, z: point.z, cls: point.cls, hazard: point.hazard, distance: point.distance })),
        eventLog: eventLogRef.current.slice(-80),
      });
      downloadRunExport(`agrolidar-run-${Date.now()}.json`, payload);
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
    window.addEventListener('sim-export-run', onExportRun as EventListener);

    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
      window.removeEventListener('sim-reset', onReset as EventListener);
      window.removeEventListener('sim-camera-cycle', onCycleCamera as EventListener);
      window.removeEventListener('sim-lidar-cycle', onCycleLidar as EventListener);
      window.removeEventListener('sim-reset-world', onResetWorld as EventListener);
      window.removeEventListener('sim-export-run', onExportRun as EventListener);
    };
  }, [chunkManager, points]);

  useFrame((_, dt) => {
    const { settings } = getStore();
    const scenario = scenarioFromId(settings.scenario);
    const weather = weatherFromId(settings.weather);
    const mission = MISSION_PROFILES[settings.missionType];

    if (settings.vehicle !== lastVehicle.current) {
      const next = defaultVehicleState(settings.vehicle);
      next.x = vehicleStateRef.current.x;
      next.z = vehicleStateRef.current.z;
      next.heading = vehicleStateRef.current.heading;
      next.y = settings.vehicle === 'drone' ? vehicleStateRef.current.y + 3.4 : sampleTerrainHeight(vehicleStateRef.current.x, vehicleStateRef.current.z, settings.seed, scenario.terrainRoughness);
      vehicleStateRef.current = next;
      lastVehicle.current = settings.vehicle;
      eventLogRef.current.push(`vehicle_switch:${settings.vehicle}`);
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
      const speedTarget = Math.min(0.88, mission.targetSpeed / 7.2);
      inputRef.current.throttle = settings.vehicle === 'drone' ? 0.58 : speedTarget;
      inputRef.current.steer = Math.sin(performance.now() * 0.00025) * 0.28;
      inputRef.current.brake = 0;
      inputRef.current.yaw = Math.sin(performance.now() * 0.00016) * 0.55;
    }

    const activeChunks = chunkManager.getActiveChunks(settings.seed, vehicleStateRef.current.x, vehicleStateRef.current.z, scenario, settings.hazardDensity);
    const obstacles = activeChunks.flatMap((chunk) => chunk.obstacles);

    const terrain = sampleTerrainAnalytics(vehicleStateRef.current.x, vehicleStateRef.current.z, settings.seed, scenario.terrainRoughness);
    if (settings.vehicle === 'tractor') {
      const surface = sampleTerrainSurface(vehicleStateRef.current.x, vehicleStateRef.current.z, settings.seed);
      const surfaceTraction = surface === 'mud' ? 0.52 : surface === 'wet' ? 0.68 : surface === 'grass' ? 0.84 : 0.78;
      const terrainPenalty = terrain.mudPocket ? 0.11 : terrain.puddleRisk > 0.72 ? 0.06 : 0;
      const stepped = stepVehicle(vehicleStateRef.current, inputRef.current, dt, weather.gripPenalty + scenario.mud * 0.08 + terrainPenalty, terrainPitch, terrainRoll, surfaceTraction);
      vehicleStateRef.current = resolveVehicleCollisions(stepped, obstacles, dt);
      vehicleStateRef.current.y = terrain.elevation;
    } else {
      const wind = Math.sin(scanPhase.current * 0.4 + settings.seed * 0.001) * (weather.id === 'light-rain' ? 1.4 : 0.8);
      vehicleStateRef.current = stepDrone(vehicleStateRef.current, inputRef.current, dt, terrain.elevation, settings.droneMission, settings.terrainFollow, wind);
      missionProgress.current = (missionProgress.current + dt * (settings.droneMission === 'lift' ? 1.8 : 3.2)) % 100;
    }

    scanPhase.current += dt;
    const pipeline = runLidarPipeline({
      obstacles,
      weather,
      basePose: {
        x: vehicleStateRef.current.x,
        y: vehicleStateRef.current.y,
        z: vehicleStateRef.current.z,
        heading: vehicleStateRef.current.heading,
        pitch: vehicleStateRef.current.pitch,
        roll: vehicleStateRef.current.roll,
      },
      scanPhase: scanPhase.current,
      seed: settings.seed,
      rangeOverride: settings.lidarRange,
      densityOverride: settings.lidarDensity,
      viewMode: settings.viewMode,
      vehicle: settings.vehicle,
      spatialIndex: lidarIndex,
      presetId: settings.sensorPreset,
      mountId: settings.sensorMount,
    });

    if (Math.floor(scanPhase.current * (settings.vehicle === 'drone' ? 16 : 22)) % 2 === 0) {
      setPoints(pipeline.filtered);
      setChunks(activeChunks);
    }

    const classes = Array.from(new Set(pipeline.hazards.slice(0, 8).map((hazard) => hazard.obstacle.cls)));
    const coverageRate = settings.vehicle === 'drone' ? missionProgress.current : 0;
    const fieldParcel = FIELD_PARCELS.find((item) => item.id === settings.fieldParcelId);

    if (pipeline.hazards[0] && pipeline.hazards[0].risk === 'CRITICAL' && Math.floor(scanPhase.current * 2) % 4 === 0) {
      eventLogRef.current.push(`critical:${pipeline.hazards[0].obstacle.cls}:${pipeline.hazards[0].distance.toFixed(1)}m`);
    }

    setTelemetry({
      speed: vehicleStateRef.current.speed,
      altitude: Math.max(0, vehicleStateRef.current.y - terrain.elevation),
      headingDeg: ((vehicleStateRef.current.heading * 180) / Math.PI + 360) % 360,
      nearestHazard: pipeline.nearestHazardM,
      risk: pipeline.hazards[0]?.risk ?? 'SAFE',
      pointCount: pipeline.raw.length,
      filteredPointCount: pipeline.filtered.length,
      latencyMs: (settings.vehicle === 'drone' ? 13 : 11) + pipeline.filtered.length * 0.0014,
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
      missionType: settings.missionType,
      fieldParcel: fieldParcel?.label ?? settings.fieldParcelId,
      terrainRoughness: pipeline.ground.roughness,
      depressionRisk: terrain.depressionIndex,
      puddleRisk: terrain.puddleRisk,
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
