# Release Checklist

Use this checklist for every public release tag (`vMAJOR.MINOR.PATCH`).

## 1) Pre-release readiness

- [ ] Branch is up to date with `main` and all required checks are green.
- [ ] Scope and release type are confirmed (patch/minor/major).
- [ ] `VERSION`, `lidar_perception.__version__`, and `package.json` version are aligned.
- [ ] Open high-severity bugs or security issues are triaged for this release.

## 2) Quality gates (required)

Run from repository root:

```bash
make lint
make test
npm run lint
npm run build
mkdocs build --strict
```

For safety-sensitive changes, also run:

```bash
make generate-data
make evaluate
make safety-check
```

## 3) Documentation and release notes

- [ ] `CHANGELOG.md` includes a fully written section for the target version.
- [ ] README links, quickstart commands, and badge targets are valid.
- [ ] New config/API/safety policy changes are documented in `docs/`.
- [ ] `RELEASE_NOTES.md` has been updated for the release (or generated and reviewed).

## 4) Tagging and publishing

1. Create a signed or annotated tag:
   ```bash
   git tag -a vX.Y.Z -m "AgroLidar vX.Y.Z"
   ```
2. Push commits and tag:
   ```bash
   git push origin main --follow-tags
   ```
3. Verify the `Release` workflow runs successfully.
4. Confirm the GitHub Release includes release notes and assets.

## 5) Post-release validation

- [ ] Verify docs deployment completed and Pages site is live.
- [ ] Verify release artifact integrity and reproducibility.
- [ ] Confirm no regressions in smoke inference and training flow.
- [ ] Announce release and link migration/breaking-change guidance if needed.
