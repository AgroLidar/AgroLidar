---
layout: default
title: AgroLidar Docs
---

# AgroLidar Documentation

**LiDAR perception system for agricultural machines.**

> Field-first. Safety-gated. Deployment-ready.

## Quick Links

| Document | Description |
|----------|-------------|
| [Hardware Guide](HARDWARE_DEPLOYMENT_GUIDE.md) | BOM, tiers, wiring |
| [Installation](INSTALLATION_AND_COMMISSIONING.md) | Setup & commissioning |
| [Sandbox & Demo](SANDBOX_AND_DEMO_MODE.md) | Try without hardware |
| [API Integration](API_INTEGRATION_GUIDE.md) | OEM/integrator guide |
| [Buyer Checklist](BUYER_CHECKLIST.md) | Decision checklist |
| [Safety & Limits](SAFETY_AND_LIMITATIONS.md) | Critical reading |
| [Platform Matrix](PLATFORM_ADAPTATION_MATRIX.md) | Vehicle compatibility |
| [Configuration](CONFIGURATION_REFERENCE.md) | All config knobs |
| [Data & Retraining](DATA_COLLECTION_AND_RETRAINING.md) | Continuous learning |
| [Regulatory](REGULATORY_AND_COMPLIANCE.md) | CE, ANATEL, ENACOM |

## Get Started

```bash
git clone https://github.com/AgroLidar/AgroLidar
cd AgroLidar
make setup
make generate-data && make train && make serve
```

Then visit: http://localhost:8000/docs for the live API.
