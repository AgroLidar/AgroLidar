# Repository Admin TODO (GitHub UI)

These settings require GitHub repository admin permissions and cannot be fully enforced from code.

## 1) Repository metadata

- **Description:** `Safety-first LiDAR perception and model-governance stack for agricultural machines.`
- **Homepage URL:** `https://agrolidar.github.io/AgroLidar/`
- **Topics:** `lidar`, `agritech`, `perception`, `autonomous-systems`, `pytorch`, `fastapi`, `onnx`, `safety-critical`, `mlops`
- **Social preview image:** use `assets/logo.png` (or a 1280x640 derivative with subtitle)

## 2) GitHub Pages

- In **Settings → Pages**, ensure source is **GitHub Actions**.
- Confirm first successful run of workflow **Docs Pages Deployment** publishes site URL.

## 3) Branch protection for `main`

Recommended required checks:

- `Python Quality (3.11)`
- `Landing Build (Node 20)`
- `MkDocs Strict Build`
- `Secret Scan (Gitleaks)`
- `Dependency Audit`
- `Repository Hygiene / hygiene`

Recommended rule settings:

- Require pull request before merging (>=1 review)
- Require status checks to pass before merging
- Require branches to be up to date
- Restrict force pushes and deletions
- Require conversation resolution before merge

## 4) Merge strategy

- Enable **Squash merge** (default)
- Optionally enable **Rebase merge**
- Disable merge commits for linear history
- Optionally enable auto-merge after required checks pass

## 5) Releases

- Enforce tag naming convention: `vMAJOR.MINOR.PATCH`
- Use release title format: `AgroLidar vMAJOR.MINOR.PATCH`
