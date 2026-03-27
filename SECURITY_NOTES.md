# Security Notes

## Python dependency audit exceptions

The security workflow intentionally applies **narrow, temporary exceptions** for two advisories:

- `CVE-2026-28500` (`onnx`)
- `CVE-2026-4539` (`pygments`)

At the time of this update, `pip-audit` reports these advisories without a published fixed version, so there is no actionable upgrade path yet. Once upstream releases fixes, remove these ignores and upgrade immediately.

## Runtime vs audit requirements alignment

- `requirements.txt` is the runtime dependency source of truth.
- `requirements.audit.txt` intentionally mirrors the same direct dependencies and versions, with one exception: `torch`.
- `torch` is excluded from `requirements.audit.txt` only because CI installs PyTorch CPU wheels from the PyTorch index and `pip-audit` cannot consistently resolve local-version wheel identifiers from that index.

## Torch CPU wheels and audit behavior

Project CI installs CPU-only PyTorch wheels from the official PyTorch package index:

- `https://download.pytorch.org/whl/cpu`

Those wheels may resolve to local-version identifiers (for example `2.2.2+cpu`) that PyPI-backed audit resolution cannot map reliably. To avoid suppressing unrelated findings, the security workflow uses `requirements.audit.txt` (which excludes **only** `torch`) as the `pip-audit` input instead of disabling the audit entirely.

## Open3D compatibility note

`open3d` remains pinned but is guarded with `python_version < "3.12"` in runtime and audit requirements to reflect Python-version compatibility constraints directly rather than platform-only markers.
