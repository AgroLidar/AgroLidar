# Development Guide

## Local quality gates

Run before opening a pull request:

```bash
make lint
make test
pre-commit run --all-files
```

## Working on the landing page (Next.js)

```bash
npm ci
npm run dev
npm run typecheck
```

## CI expectations

GitHub Actions validates:

- Python lint and tests
- Next.js build (landing page)
- docs structure consistency and markdown quality checks
- release note readiness for tags

## Release checklist

Before tagging a release:

1. Update `CHANGELOG.md` and `CITATION.cff` version/date.
2. Confirm all CI workflows pass on `main`.
3. Verify safety policy thresholds and evaluation reports.
4. Validate inference API health and sample prediction.
5. Tag with semantic version (e.g., `v0.10.0`).
6. Publish GitHub release notes using changelog sections.

## Commit and branch discipline

- Use short-lived branches from `main`.
- Keep PRs focused and reviewable.
- For safety-critical changes, request explicit maintainer review.
