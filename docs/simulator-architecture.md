# Simulator Architecture (Flagship Refactor)

AgroLidar's browser simulator is organized as a layered runtime intended to feel like a serious perception platform, not a graphics toy.

## Runtime Layers

1. **Simulation loop** (`components/simulator/SimulatorCanvas.tsx`)
2. **Vehicle dynamics** (`lib/sim/vehicle/dynamics.ts`)
3. **Sensor core** (`lib/sim/lidar/sensor.ts`, `lib/sim/lidar/presets.ts`)
4. **Perception/hazard pipeline** (`lib/sim/lidar/pipeline.ts`, `lib/sim/lidar/hazards.ts`)
5. **World generation** (`lib/sim/world/*`)
6. **Terrain analytics** (`lib/sim/terrain/analytics.ts`)
7. **Operations layer** (`lib/sim/ops/missions.ts`)
8. **UX/HUD controls** (`components/simulator/*`)
9. **Export/report layer** (`lib/sim/export/run-export.ts`)

## Sensor Pipeline Stages

The LiDAR pipeline is intentionally modular and replay-friendly:

- **Prefilter stage**: reject weak/noisy points.
- **Raw scan stage**: preserve unfiltered points for diagnostics.
- **Hazard interpretation stage**: nearest hazard/risk sorting.
- **Ground estimation stage**: compute min/max/roughness from ground returns.
- **Map trace stage**: compact BEV-friendly scan snapshot.
- **Export stage**: mission summary + points + event log as JSON.

## Hardware Realism Modes

Sensor presets approximate field hardware classes:

- Hazard Sweep
- Survey
- Fast Performance
- Dense Precision
- Low-Cost / OpenSimple

Mount presets:

- Tractor Mast
- Hood Forward

Each preset controls range, channels, point budget, dropout, scan cadence, and FOV envelope.

## Operations Layer

Mission metadata is first-class in runtime telemetry:

- Field parcels (e.g., North 40, Orchard East)
- Mission types (scouting, hazard sweep, route validation, LiDAR survey)
- Parcel + mission summary in HUD and exports

## Export Contract

`sim-export-v1` bundles:

- scenario + weather + sensor preset
- telemetry snapshot
- point cloud sample (class + hazard labels)
- event log

This keeps AgroLidar ready for future synthetic dataset and replay workflows.
