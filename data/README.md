# Data Layout

Recommended local structure:

```text
data/
  raw/
    public_road/
    tractor_logs/
  processed/
  labels/
```

## Notes

- Use `public_road/` for initial KITTI, nuScenes, or Waymo-format prototyping.
- Use `tractor_logs/` for field-collected agricultural LiDAR once available.
- Keep calibration, weather metadata, and machine state alongside future field data to support robustness analysis.
