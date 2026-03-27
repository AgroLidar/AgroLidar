# Next Iteration Prompt — Public-Facing Upgrade

## Recommended Focus
Implement **release automation** as the next highest-value upgrade after repository identity/credibility improvements.

## Goal
Automate versioned releases so every tagged version publishes consistent artifacts and public notes with minimal manual effort.

## Scope
1. Add a GitHub Actions workflow that triggers on `v*` tags.
2. Validate repository health before release (lint/test/smoke checks already present can be reused).
3. Create a GitHub Release automatically with notes sourced from `RELEASE_NOTES.md` (or generated changelog fallback).
4. Attach key build artifacts where applicable (model/report bundles if available in pipeline outputs).
5. Ensure release workflow fails clearly if required files are missing.
6. Document release process in `docs/README.md` and/or root `README.md`.

## Acceptance Criteria
- Pushing tag `vX.Y.Z` creates a GitHub Release automatically.
- Release title/body is professional and deterministic.
- Workflow permissions are least-privilege.
- Manual release effort is reduced to tag creation + push.
- Documentation includes a short “How to cut a release” section.

## Constraints
- Do not alter core model logic.
- Keep CI signal clean and avoid duplicating existing jobs.
- Preserve deployment-readiness narrative for external visitors.
