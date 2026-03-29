import type { TelemetrySnapshot } from '@/lib/sim/store';
import type { MissionType } from '@/lib/sim/ops/missions';
import type { SensorPresetId } from '@/lib/sim/lidar/presets';
import type { LidarPoint } from '@/lib/sim/lidar/sensor';

export interface ExportPayload {
  version: 'sim-export-v1';
  timestamp: string;
  seed: number;
  scenario: string;
  weather: string;
  vehicle: string;
  mission: MissionType;
  fieldParcel: string;
  sensorPreset: SensorPresetId;
  telemetry: TelemetrySnapshot;
  points: Array<Pick<LidarPoint, 'x' | 'y' | 'z' | 'cls' | 'hazard' | 'distance'>>;
  eventLog: string[];
}

export function createRunExport(payload: Omit<ExportPayload, 'version' | 'timestamp'>): string {
  const documentPayload: ExportPayload = {
    ...payload,
    version: 'sim-export-v1',
    timestamp: new Date().toISOString(),
  };
  return JSON.stringify(documentPayload, null, 2);
}

export function downloadRunExport(filename: string, json: string): void {
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
