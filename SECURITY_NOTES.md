# Security Notes

## Python dependency audit exceptions

The security workflow intentionally applies **narrow, temporary exceptions** for two advisories:

- `CVE-2026-28500` (`onnx`)
- `CVE-2026-4539` (`pygments`)

At the time of this update, `pip-audit` reports these advisories without a published fixed version, so there is no actionable upgrade path yet. Once upstream releases fixes, remove these ignores and upgrade immediately.

## Torch CPU wheels and audit behavior

Project CI installs CPU-only PyTorch wheels from the official PyTorch package index:

- `https://download.pytorch.org/whl/cpu`

Those wheels may resolve to local-version identifiers (for example `2.2.2+cpu`) that PyPI-backed audit resolution cannot map reliably. To avoid suppressing unrelated findings, the security workflow excludes **only** `torch` from the `pip-audit` requirements input instead of disabling the audit entirely.
