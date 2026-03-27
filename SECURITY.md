# Security Policy

AgroLidar includes safety-critical perception components. We treat security and model integrity issues as high-priority defects.

## Supported Versions

| Version | Supported | Notes |
| --- | --- | --- |
| 0.9.x | ✅ | Current stable line |
| `< 0.9.0` | ❌ | Upgrade to latest 0.9.x |

## Reporting a Vulnerability

Please report vulnerabilities privately by emailing **security@agro-lidar.com**.

Include, when possible:

- affected component(s)
- impact summary
- reproduction steps or proof-of-concept
- potential mitigations

> Do **not** disclose vulnerabilities publicly before a fix is available.

## Response Expectations

- **Acknowledgement:** within 72 hours
- **Initial triage:** within 7 calendar days
- **Status updates:** at least every 14 days until resolution
- **Coordinated disclosure target:** after patch availability and downstream notice window

## Security Scope Priorities

- inference server authentication/authorization gaps
- model checkpoint integrity and registry tampering
- API abuse, rate limiting bypass, or denial-of-service vectors
- unsafe deserialization / untrusted input execution paths
- secrets handling and credential exposure

## Out of Scope

- social engineering attacks without a software defect
- physical attacks against customer hardware
- known vulnerabilities in unsupported versions
- vulnerabilities in third-party packages without AgroLidar-specific exploit path (please report upstream as well)
