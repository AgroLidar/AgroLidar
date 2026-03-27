# Release Process

This repository uses **Semantic Versioning** and **changelog-driven releases**.

## Versioning policy

- `MAJOR`: breaking API or behavior changes.
- `MINOR`: backward-compatible feature delivery.
- `PATCH`: backward-compatible fixes, docs, or CI hardening.

Canonical release version references:

- `VERSION`
- `lidar_perception/__init__.py` (`__version__`)
- `package.json` (`version` for the landing app metadata)

## Release flow

1. Complete [release checklist](release-checklist.md).
2. Move release content from `Unreleased` in `CHANGELOG.md` to a new version section.
3. Update `RELEASE_NOTES.md` with final operator-facing highlights and known limitations.
4. Create tag `vX.Y.Z` from `main`.
5. Push tag to trigger `.github/workflows/release.yml`.
6. Validate published release and docs deployment.

## Conventions

- Tags must match regex: `v*.*.*`.
- Release titles should use `AgroLidar vX.Y.Z`.
- Keep release notes factual and evidence-based (no roadmap promises in release notes).
