export type MissionType = 'scouting' | 'hazard-sweep' | 'field-edge-inspection' | 'route-validation' | 'lidar-survey';

export interface FieldParcel {
  id: string;
  label: string;
  crop: string;
  hectares: number;
}

export interface MissionProfile {
  id: MissionType;
  label: string;
  objective: string;
  targetSpeed: number;
}

export const FIELD_PARCELS: FieldParcel[] = [
  { id: 'north-40', label: 'North 40', crop: 'Corn', hectares: 16.2 },
  { id: 'orchard-east', label: 'Orchard East', crop: 'Apple', hectares: 8.9 },
  { id: 'pasture-west', label: 'Pasture West', crop: 'Mixed forage', hectares: 13.4 },
];

export const MISSION_PROFILES: Record<MissionType, MissionProfile> = {
  scouting: { id: 'scouting', label: 'Scouting', objective: 'General field health and obstacle awareness', targetSpeed: 5.8 },
  'hazard-sweep': { id: 'hazard-sweep', label: 'Hazard Sweep', objective: 'Find near-term collision hazards before operations', targetSpeed: 4.4 },
  'field-edge-inspection': { id: 'field-edge-inspection', label: 'Field Edge Inspection', objective: 'Validate boundaries, fence lines, and crop edge continuity', targetSpeed: 3.8 },
  'route-validation': { id: 'route-validation', label: 'Route Validation', objective: 'Verify passable routes and traction zones', targetSpeed: 5.1 },
  'lidar-survey': { id: 'lidar-survey', label: 'LiDAR Survey', objective: 'Collect dense scan traces for replay/export', targetSpeed: 3.2 },
};
