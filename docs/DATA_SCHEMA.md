# AgroLidar Data Schema

Este documento define el contrato de datos usado por `scripts/train.py`, `scripts/evaluate.py` y utilidades de mining.

## 1) Estructura de directorios

```text
data/
  train/
    frames/          # .npy (1 archivo por frame)
    labels/          # .json (1 archivo por frame, mismo nombre)
  val/
    frames/
    labels/
  hard_cases/        # mismo formato que train/ y val/
    frames/
    labels/
  review_queue/
    queue.json
    queue_summary.md
```

Regla de correspondencia: `data/train/frames/train_00001.npy` debe tener `data/train/labels/train_00001.json`.

## 2) Formato de frame (`.npy`)

- `shape`: `(C, H, W)`
- `C = 4` canales: `[x, y, z, intensity]`
- `H = 512`, `W = 512`
- `dtype = float32`
- valores normalizados en rango `[0, 1]`

## 3) Formato de label (`.json`)

```json
{
  "frame_id": "string",
  "timestamp": "ISO8601",
  "objects": [
    {
      "class": "human|animal|rock|post|vehicle",
      "bbox_bev": [cx, cy, w, h, angle],
      "distance_m": 12.3,
      "confidence_gt": 1.0
    }
  ]
}
```

Notas:
- `bbox_bev` está en coordenadas de píxel BEV.
- `angle` está en radianes.
- `distance_m` es la distancia al objeto en metros.

## 4) Formato de inferencia para hard-case mining (`.json`)

`scripts/mine_hard_cases.py` consume un formato de inferencia compatible con:

```json
{
  "frame_id": "string",
  "timestamp": "ISO8601",
  "detections": [
    {
      "class": "human|animal|rock|post|vehicle",
      "confidence": 0.92,
      "bbox": [cx, cy, w, h, angle],
      "distance": 9.7
    }
  ],
  "ground_truth": [
    {
      "class": "string",
      "bbox": [cx, cy, w, h, angle],
      "distance": 10.1
    }
  ]
}
```

## 5) Convención de clases

Clases oficiales:
- `human`
- `animal`
- `rock`
- `post`
- `vehicle`

Si llegan etiquetas fuera de esta taxonomía, deben mapearse o descartarse antes de entrenar.
