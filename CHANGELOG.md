# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Release checklist (`docs/release-checklist.md`) and release process guide (`docs/release-process.md`).
- GitHub Pages deployment workflow for MkDocs (`.github/workflows/docs-pages.yml`).
- Expanded community templates and issue form governance for support routing and higher quality reports.
- Security hardening workflow with gitleaks and dependency audits.

### Changed
- Standardized version metadata (`VERSION`, `lidar_perception.__version__`, `package.json`).
- Hardened CI workflows with explicit permissions, concurrency controls, and clearer workflow names.
- Improved release automation with changelog/release-note validation and immutable release checks.

## [0.9.0] - 2026-03-27

### Added
- Safety-gated model promotion flow with evaluation and comparison reports.
- Inference server and ML pipeline scripts for training, retraining, ONNX export, and validation.
- Operations and deployment documentation for field and enterprise integration.

[Unreleased]: https://github.com/AgroLidar/AgroLidar/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/AgroLidar/AgroLidar/releases/tag/v0.9.0
