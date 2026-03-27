# Repository Admin TODO (GitHub UI)

These settings cannot be fully configured from code and should be applied in the GitHub repository settings.

## Recommended repository description

`Safety-first LiDAR perception and model governance stack for agricultural machines.`

## Recommended homepage

- GitHub Pages docs (after enabling Pages): `https://agrolidar.github.io/AgroLidar/`

## Suggested topics

- lidar
- agritech
- perception
- autonomous-systems
- pytorch
- fastapi
- onnx
- machine-learning
- safety-critical
- mlops

## Social preview suggestion

Use `assets/logo.png` with a neutral dark background and subtitle:
`AgroLidar · Safety-first field perception`.

## Branch protection

- Protect `main`
- Require PR reviews (>=1)
- Require status checks:
  - CI
  - Docs
  - Repository Hygiene
- Require up-to-date branches before merge
- Restrict force pushes and deletions

## Merge strategy recommendation

- Allow squash merge (default)
- Disable merge commits for cleaner history
- Optionally allow rebase merge for advanced contributors

## Release naming convention

- Tags: `vMAJOR.MINOR.PATCH` (e.g., `v1.0.0`)
- GitHub release title: `AgroLidar vMAJOR.MINOR.PATCH`
