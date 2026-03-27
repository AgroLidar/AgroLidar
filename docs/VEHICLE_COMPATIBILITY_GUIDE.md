# Vehicle Compatibility Guide

> AgroLidar supports **target platform classes**; validated integration depth varies by project and hardware stack.

## Family A — Row-crop and utility tractors
Examples: John Deere 5E/6M/7R/8R, Case IH Puma/Magnum, New Holland T7/T8, Pauny, Zanello, Agrale, Deutz-Fahr Argentina variants.
- Mounting constraints: hood and exhaust occlusion, variable cab heights.
- Sensor positions: front bumper, cab roof, ROPS frame.
- Compute enclosure: cab interior or external weatherproof box.
- Power: 12V or 24V; older LATAM fleets often 12V-only.
- Environmental risk: dust and vibration on unpaved campo roads.
- Integration tier: Tier 1 (modern prewired) to Tier 2 (custom harnessing).
- Profile references: `tractor_generic.yaml`, `tractor_high_horsepower.yaml`, `tractor_compact.yaml`.

## Family B — Combines and harvesters
Examples: John Deere S-series, Case IH Axial-Flow, New Holland CR/CX, Metalfor harvest platforms.
- Mounting constraints: high cab, header occlusion, crop residue contamination.
- Sensor positions: cab roof or header mount.
- Compute enclosure: sealed cabin compartment or external box.
- Power: usually 24V; verify harness and alternator load.
- Integration tier: Tier 2 to Tier 3 when header-mounted.
- Profile references: `combine_generic.yaml`, `combine_header_sensor.yaml`.

## Family C — Sprayers (self-propelled/trailed)
Examples: Jacto, PLA, Stara, Metalfor sprayers, Ombú platforms.
- Mounting constraints: boom oscillation and spray contamination.
- Sensor positions: chassis front or boom arm.
- Compute enclosure: cab side service bay + filtered intake.
- Power: mostly 24V, but check mixed fleets.
- Integration tier: Tier 2 (chassis mount) / Tier 3 (boom mount).
- Profile references: `sprayer_generic.yaml`, `sprayer_boom_mounted.yaml`.

## Family D — Telehandlers and material handlers
Examples: JCB, Manitou, Merlo, local agricultural handlers.
- Mounting constraints: boom articulation and blind spots.
- Sensor positions: roofline or boom base.
- Compute enclosure: cabin-backed enclosure.
- Power: often 12V, with noisy electrical environments.
- Integration tier: Tier 2.
- Profile reference: `telehandler_generic.yaml`.

## Family E — UTVs and specialty platforms (including spray drones)
Examples: Polaris Ranger, Can-Am Defender, utility OEM variants, drone spray platforms.
- Mounting constraints: compact frame, severe vibration.
- Sensor positions: front rack, roof frame; drone central frame mount.
- Compute enclosure: compact sealed box.
- Power: typically 12V for UTV; drone-specific power architecture.
- Integration tier: Tier 2 (UTV) to Tier 3 (airborne/drone).
- Profile references: `utv_generic.yaml`, `drone_spray.yaml`.

## LATAM-Specific Deployment Considerations
- Frequent 12V-only electrical systems in legacy fleets.
- High dust loads (Pampas/Chaco) requiring frequent sensor cleaning.
- Limited field connectivity; design for offline-first logging and deferred upload.
- High vibration on unpaved roads requires reinforced mounts and connector retention.
