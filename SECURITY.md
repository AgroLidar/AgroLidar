# Security Policy

AgroLidar includes safety-critical perception components. Security, model integrity, and promotion-governance flaws are treated as high-priority defects.

## Supported Versions

| Version | Supported | Notes |
| --- | --- | --- |
| 0.9.x | ✅ | Current stable line |
| `< 0.9.0` | ❌ | Upgrade to latest 0.9.x |

## Reporting a Vulnerability

Report vulnerabilities privately to **security@agro-lidar.com**.

Please include:

- affected component(s)
- impact summary (confidentiality / integrity / availability / safety)
- reproduction steps or proof-of-concept
- mitigations or containment actions attempted

> Do **not** disclose vulnerabilities publicly before a fix is available.

## Response SLO

- **Acknowledgement:** within 72 hours
- **Initial triage:** within 7 calendar days
- **Status updates:** at least every 14 days until resolution
- **Disclosure target:** coordinated disclosure after patch availability and downstream notice window

## Scope Priorities

- inference server authentication/authorization gaps
- model checkpoint integrity and registry tampering
- API abuse, rate-limit bypass, or denial-of-service vectors
- unsafe deserialization / untrusted input execution paths
- secrets handling and credential exposure
- CI/CD supply-chain compromise (actions, dependencies, build pipeline)

## Out of Scope

- social engineering attacks without a software defect
- physical attacks against customer hardware
- known vulnerabilities in unsupported versions
- vulnerabilities in third-party packages without AgroLidar-specific exploit path (report upstream as well)
