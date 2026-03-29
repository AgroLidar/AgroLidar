export type ObstacleClass =
  | 'human'
  | 'animal'
  | 'rock'
  | 'post'
  | 'pole'
  | 'vehicle'
  | 'tractor'
  | 'hay-bale'
  | 'tree'
  | 'machinery'
  | 'fence-line'
  | 'field-boundary';

export type CollisionProfile = 'solid' | 'soft' | 'ghost';

export interface WorldObstacle {
  id: string;
  cls: ObstacleClass;
  x: number;
  y: number;
  z: number;
  radius: number;
  sensingRadius?: number;
  hazard: boolean;
  height?: number;
  variant?: number;
  collision?: CollisionProfile;
}
