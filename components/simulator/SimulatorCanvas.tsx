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
import { computeHazards } from '@/lib/sim/lidar/hazards';
import { clamp } from '@/lib/sim/math';
import { scenarioFromId, weatherFromId } from '@/lib/sim/scenarios';
import { getStore, setSettings, setTelemetry, subscribe } from '@/lib/sim/store';
import { createInputState } from '@/lib/sim/vehicle/controller';
import { defaultVehicleState, stepVehicle, type VehicleState } from '@/lib/sim/vehicle/dynamics';
import { ChunkManager } from '@/lib/sim/world/chunks';
import { sampleTerrainHeight } from '@/lib/sim/world/terrain';

type CameraMode = 'chase' | 'hood' | 'top' | 'lidar';
const cameraModes: CameraMode[] = ['chase', 'hood', 'top', 'lidar'];

export function SimulatorCanvas() {
  const [settingsVersion, setSettingsVersion] = useState(0);

  useEffect(() => subscribe(() => setSettingsVersion((v) => v + 1)), []);

  return (
    <div className="h-full w-full" data-settings-version={settingsVersion}>
      <Canvas shadows camera={{ position: [0, 8, -15], fov: 60 }}>
        <ambientLight intensity={0.48} />
        <directionalLight castShadow intensity={1.05} position={[35, 60, 18]} shadow-mapSize={[1024, 1024]} />
        <SimulationScene />
      </Canvas>
    </div>
  );
}

function SimulationScene() {
  const vehicleStateRef = useRef<VehicleState>(defaultVehicleState());
  const chunkManager = useMemo(() => new ChunkManager(44, 2), []);
  const inputRef = useRef(createInputState());
  const [points, setPoints] = useState<LidarPoint[]>([]);
  const [chunks, setChunks] = useState<ChunkData[]>([]);
  const [cameraModeIndex, setCameraModeIndex] = useState(0);
  const scanPhase = useRef(0);

  useEffect(() => {
    const onKey = (event: KeyboardEvent, down: boolean): void => {
      if (event.key === 'w' || event.key === 'ArrowUp') inputRef.current.throttle = down ? 1 : 0;
      if (event.key === 's' || event.key === 'ArrowDown') inputRef.current.brake = down ? 1 : 0;
      if (event.key === 'a' || event.key === 'ArrowLeft') inputRef.current.steer = down ? -1 : inputRef.current.steer === -1 ? 0 : inputRef.current.steer;
      if (event.key === 'd' || event.key === 'ArrowRight') inputRef.current.steer = down ? 1 : inputRef.current.steer === 1 ? 0 : inputRef.current.steer;
      if (event.key === ' ') inputRef.current.handbrake = down;
      if (down && event.key.toLowerCase() === 'c') setCameraModeIndex((prev) => (prev + 1) % cameraModes.length);
      if (down && event.key.toLowerCase() === 'p') {
        const paused = getStore().settings.paused;
        setSettings({ paused: !paused });
      }
      if (down && event.key.toLowerCase() === 'r') {
        vehicleStateRef.current = defaultVehicleState();
      }
    };

    const down = (event: KeyboardEvent) => onKey(event, true);
    const up = (event: KeyboardEvent) => onKey(event, false);
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
    };
  }, []);

  useFrame((_, dt) => {
    const { settings } = getStore();
    const scenario = scenarioFromId(settings.scenario);
    const weather = weatherFromId(settings.weather);

    if (settings.paused) return;

    const terrainPitch = Math.sin(vehicleStateRef.current.x * 0.03) * scenario.terrainRoughness * 0.3;
    const terrainRoll = Math.cos(vehicleStateRef.current.z * 0.025) * scenario.terrainRoughness * 0.24;
    if (settings.autopilot) {
      inputRef.current.throttle = 0.72;
      inputRef.current.steer = Math.sin(performance.now() * 0.0003) * 0.35;
      inputRef.current.brake = 0;
    }

    vehicleStateRef.current = stepVehicle(vehicleStateRef.current, inputRef.current, dt, weather.gripPenalty, terrainPitch, terrainRoll);
    vehicleStateRef.current.y = sampleTerrainHeight(vehicleStateRef.current.x, vehicleStateRef.current.z, settings.seed, scenario.terrainRoughness);

    const activeChunks = chunkManager.getActiveChunks(settings.seed, vehicleStateRef.current.x, vehicleStateRef.current.z, scenario, settings.hazardDensity);
    const hazards = computeHazards(activeChunks.flatMap((chunk) => chunk.obstacles), vehicleStateRef.current.x, vehicleStateRef.current.z, settings.lidarRange);
    scanPhase.current += dt;

    const nextPoints = sampleLidarPoints(
      hazards,
      {
        range: settings.lidarRange,
        horizontalFovDeg: 120,
        channels: settings.quality === 'high' ? 32 : settings.quality === 'medium' ? 16 : 8,
        pointBudget: Math.floor((settings.quality === 'high' ? 12000 : settings.quality === 'medium' ? 8000 : 4500) * settings.lidarDensity),
        dropout: clamp(0.02 + (1 - settings.lidarDensity) * 0.18, 0.02, 0.2),
      },
      scanPhase.current,
      weather,
    );

    if (Math.floor(scanPhase.current * 14) % 2 === 0) {
      setPoints(nextPoints);
      setChunks(activeChunks);
    }

    const nearest = hazards[0]?.distance ?? Infinity;
    const risk = nearest < 8 ? 'CRITICAL' : nearest < 18 ? 'CAUTION' : 'SAFE';
    const classes = Array.from(new Set(hazards.slice(0, 5).map((h) => h.obstacle.cls)));
    setTelemetry({
      speed: vehicleStateRef.current.speed,
      nearestHazard: nearest,
      risk,
      pointCount: nextPoints.length,
      latencyMs: 14 + nextPoints.length * 0.0017,
      classes,
      seed: settings.seed,
      scenarioLabel: scenario.label,
    });
  });

  const settings = getStore().settings;
  const weather = weatherFromId(settings.weather);

  return (
    <>
      <World chunks={chunks} weatherSky={weather.sky} />
      <Vehicle stateRef={vehicleStateRef} />
      <LidarLayer points={points} visible={settings.viewMode !== 'raw'} />
      <CameraRig stateRef={vehicleStateRef} mode={cameraModes[cameraModeIndex]} />
    </>
  );
}
