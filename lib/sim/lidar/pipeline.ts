import type { WeatherConfig } from '@/lib/sim/scenarios';
import { computeHazards, type HazardInfo } from '@/lib/sim/lidar/hazards';
import { sampleLidarPoints, type LidarPoint, type LidarPose } from '@/lib/sim/lidar/sensor';
import type { ObstacleSpatialIndex } from '@/lib/sim/lidar/spatial-index';
import { blendPresetRange, SENSOR_MOUNTS, SENSOR_PRESETS, type SensorMountId, type SensorPresetId } from '@/lib/sim/lidar/presets';
import type { WorldObstacle } from '@/lib/sim/world/props';

export interface GroundEstimate {
  minY: number;
  maxY: number;
  avgY: number;
  roughness: number;
}

export interface LidarPipelineInput {
  obstacles: WorldObstacle[];
  weather: WeatherConfig;
  basePose: LidarPose;
  scanPhase: number;
  seed: number;
  rangeOverride: number;
  densityOverride: number;
  viewMode: 'world' | 'pointcloud' | 'hybrid' | 'bev' | 'depth' | 'hazard';
  vehicle: 'tractor' | 'drone';
  spatialIndex: ObstacleSpatialIndex;
  presetId: SensorPresetId;
  mountId: SensorMountId;
}

export interface LidarPipelineOutput {
  raw: LidarPoint[];
  filtered: LidarPoint[];
  hazards: HazardInfo[];
  nearestHazardM: number;
  ground: GroundEstimate;
  classHistogram: Record<string, number>;
  mapTrace: Array<{ x: number; z: number; cls: LidarPoint['cls']; hazard: boolean }>;
}

function estimateGround(points: LidarPoint[]): GroundEstimate {
  const ground = points.filter((point) => point.cls === 'ground');
  if (!ground.length) {
    return { minY: 0, maxY: 0, avgY: 0, roughness: 0 };
  }
  let minY = Number.POSITIVE_INFINITY;
  let maxY = Number.NEGATIVE_INFINITY;
  let sum = 0;
  for (const point of ground) {
    minY = Math.min(minY, point.y);
    maxY = Math.max(maxY, point.y);
    sum += point.y;
  }
  const avgY = sum / ground.length;
  return {
    minY,
    maxY,
    avgY,
    roughness: maxY - minY,
  };
}

function prefilterScan(points: LidarPoint[], weather: WeatherConfig): LidarPoint[] {
  const verticalReject = weather.lidarNoise > 0.06 ? 0.4 : 0.55;
  return points.filter((point) => point.intensity > 0.08 && point.y > -7 && point.y < 12 && (point.cls !== 'ground' || point.intensity > verticalReject * 0.1));
}

function buildClassHistogram(points: LidarPoint[]): Record<string, number> {
  const histogram: Record<string, number> = {};
  for (const point of points) {
    histogram[point.cls] = (histogram[point.cls] ?? 0) + 1;
  }
  return histogram;
}

export function runLidarPipeline(input: LidarPipelineInput): LidarPipelineOutput {
  const preset = blendPresetRange(SENSOR_PRESETS[input.presetId], input.rangeOverride, input.densityOverride);
  const mount = SENSOR_MOUNTS[input.mountId];
  const pose: LidarPose = {
    ...input.basePose,
    x: input.basePose.x + Math.sin(input.basePose.heading) * mount.forwardOffset + Math.cos(input.basePose.heading) * mount.lateralOffset,
    z: input.basePose.z + Math.cos(input.basePose.heading) * mount.forwardOffset - Math.sin(input.basePose.heading) * mount.lateralOffset,
    y: input.basePose.y + mount.heightOffset,
    pitch: (input.basePose.pitch ?? 0) + mount.tilt,
    heading: input.basePose.heading + mount.yawBias,
  };

  const raw = sampleLidarPoints(
    input.obstacles,
    {
      range: preset.range,
      horizontalFovDeg: input.viewMode === 'bev' ? Math.min(220, preset.horizontalFovDeg + 30) : preset.horizontalFovDeg,
      channels: preset.channels,
      pointBudget: preset.pointBudget,
      dropout: preset.dropout + input.weather.lidarNoise * 0.25,
    },
    input.scanPhase,
    input.weather,
    pose,
    input.seed,
    input.spatialIndex,
  );

  const filtered = prefilterScan(raw, input.weather);
  const hazards = computeHazards(input.obstacles, input.basePose.x, input.basePose.z, preset.range * (input.vehicle === 'drone' ? 1.3 : 1), input.basePose.heading);

  const mapTrace = filtered
    .filter((point) => point.cls !== 'ground' || point.distance < preset.range * 0.45)
    .slice(0, 1800)
    .map((point) => ({ x: point.x, z: point.z, cls: point.cls, hazard: point.hazard }));

  return {
    raw,
    filtered,
    hazards,
    nearestHazardM: hazards[0]?.distance ?? Number.POSITIVE_INFINITY,
    ground: estimateGround(filtered),
    classHistogram: buildClassHistogram(filtered),
    mapTrace,
  };
}
