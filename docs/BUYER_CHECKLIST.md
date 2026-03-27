# Buyer Checklist

## Before Purchase
- [ ] Target platform class identified (tractor/combine/sprayer/etc.).
- [ ] Power architecture (12V/24V) documented.
- [ ] Environmental envelope understood (dust/rain/mud/vibration).
- [ ] Integration owner assigned (OEM, dealer, integrator, or in-house engineering).

## Before Installation
- [ ] Mounting location and cable route defined.
- [ ] Compute enclosure and thermal strategy selected.
- [ ] Network/security plan agreed (especially for API exposure).

## Before Pilot
- [ ] Commissioning plan and acceptance criteria documented.
- [ ] Operator SOP and incident escalation workflow prepared.
- [ ] Data logging and review process staffed.

## Before Production
- [ ] Regulatory and product liability review completed.
- [ ] Fail-safe strategy integrated outside AgroLidar perception layer.
- [ ] Security hardening (authn/authz, network segmentation, key management).

## Site Readiness
- [ ] Field connectivity expectations documented (including offline operation).
- [ ] Service/support process defined for maintenance windows.

## Hardware Readiness
- [ ] Ruggedized sensor + compute selected.
- [ ] Rated connectors and harnesses selected.

## Software Readiness
- [ ] Baseline configs locked and versioned.
- [ ] Model registry and rollback procedure tested.

## Data Readiness
- [ ] Data schema compliance verified.
- [ ] Human review loop available for hard cases.

## Safety Readiness
- [ ] Safety gate policy aligned with operational risk tolerance.
- [ ] Operator response behavior for risk levels trained.

## Integration Readiness (OEM/Integrator)
- [ ] ECU/HMI mapping for `collision_risk` defined.
- [ ] Health watchdog behavior (`/health`, `/ready`, `/live`) implemented.
- [ ] Fallback behavior defined for server 503 and degraded operation.
