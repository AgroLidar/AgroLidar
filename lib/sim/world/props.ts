export type ObstacleClass = 'human' | 'animal' | 'rock' | 'post' | 'vehicle' | 'hay-bale' | 'tree' | 'machinery';

export interface WorldObstacle {
  id: string;
  cls: ObstacleClass;
  x: number;
  y: number;
  z: number;
  radius: number;
  hazard: boolean;
}
