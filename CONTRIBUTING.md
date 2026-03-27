# Contributing to AgroLidar

Thanks for contributing to AgroLidar. This project is safety-oriented software for LiDAR perception in agricultural environments, so we value reproducibility, reviewability, and conservative change management.

## Code of Conduct

By participating, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Project Setup

### 1. Prerequisites

- Python 3.11+
- `pip`
- GNU Make
- (Optional) Docker for inference server validation
- (Optional) Node.js 20+ for the Next.js landing page

### 2. Clone and bootstrap

```bash
git clone https://github.com/AgroLidar/AgroLidar.git
cd AgroLidar
python -m venv .venv
source .venv/bin/activate
make setup
```

### 3. Verify installation

```bash
make check-install
```

## Development Workflow

1. Open an issue (or comment on an existing issue) before large changes.
2. Create a short-lived feature branch from `main`.
3. Keep commits focused and descriptive.
4. Run local quality checks before pushing.
5. Open a pull request using the PR template.

### Branch naming suggestions

- `feat/<short-description>`
- `fix/<short-description>`
- `docs/<short-description>`
- `chore/<short-description>`
- `ci/<short-description>`

## Coding Standards

- Follow existing project structure and naming conventions.
- Python code should pass `ruff check .` and `ruff format`.
- Prefer typed interfaces and explicit configuration over implicit behavior.
- Keep safety-critical logic readable and test-covered.
- Do not commit model checkpoints (`*.pt`) or secrets.

## Test Expectations

Minimum before opening a PR:

```bash
make lint
make test
pre-commit run --all-files
```

For model, inference, or safety-policy changes, also run:

```bash
make generate-data
make evaluate
make safety-check
```

If your change affects model quality or promotion logic, include relevant artifacts from `outputs/reports/` in the PR description.

## Pull Request Expectations

A quality PR should include:

- clear problem statement and solution summary
- linked issue (`Closes #...`) when applicable
- updated docs and/or configs for behavior changes
- tests added or updated for changed behavior
- notes on backward compatibility and migration impact
- screenshots/logs when UI or API output changes

## Issue Reporting Guidance

- Use issue templates to keep reports actionable.
- Include environment details and reproducible steps.
- For security issues, **do not open a public issue**. Follow [SECURITY.md](SECURITY.md).
- For safety incidents, use the dedicated safety template and include mitigation details.

## Commit Hygiene

- Use concise imperative commit messages (e.g., `docs: add architecture guide`).
- Avoid mixed-purpose commits.
- Squash fixup/noise commits before merge when possible.
- Ensure generated or local-only artifacts are not committed.

## Release and Compatibility Notes

- AgroLidar follows Semantic Versioning.
- Any breaking change must be clearly marked in PR title/body and documented in `CHANGELOG.md`.
- For release prep, follow the release checklist in `docs/development.md`.

We appreciate thoughtful contributions that improve safety, reliability, and operator trust.
