# Platform Adaptation Matrix

| Platform category | Example families/models | AgroLidar fit level | Preferred LiDAR position | Optional camera position | Compute mounting zone | Power source notes | Network/integration notes | Key risks | Tier | Commissioning steps | Platform profile |
|---|---|---|---|---|---|---|---|---|---:|---|---|
| Tractor (compact) | Kubota/Yanmar/LS class | Good | ROPS/front | Cab crossbar | Under-seat/cab box | 12V common | Ethernet local, offline logs | vibration + dust | 2 | mount check, pitch verify, health probe | `tractor_compact.yaml` |
| Tractor (>150hp) | Pauny, Zanello, JD 8R | Excellent | Roof centerline | Windshield top | Cab rear panel | 24V typical | ECU gateway often needed | EMI, wide turn occlusion | 1-2 | power transient test + risk mapping | `tractor_high_horsepower.yaml` |
| Combine (cab) | JD S, Case Axial-Flow | Good | Cab roof | Cab front | Cab service bay | 24V | segmented network preferred | header occlusion, residue | 2 | header occlusion survey + dry run | `combine_generic.yaml` |
| Combine (header) | Header-mounted variants | Moderate | Header center | Header frame | Sealed external box | 24V + filtering | short harness + bridge | shock, contamination | 3 | isolation tuning + recalibration | `combine_header_sensor.yaml` |
| Sprayer (chassis) | Jacto/PLA/Stara | Good | Front chassis | Cab mirror boom | Cab side bay | 24V | telemetry optional | spray droplets | 2 | nozzle contamination test | `sprayer_generic.yaml` |
| Sprayer (boom) | Boom-mounted custom | Complex | Boom arm | Boom arm | External rugged box | 24V | local buffering essential | oscillation, cable fatigue | 3 | dynamic boom sweep validation | `sprayer_boom_mounted.yaml` |
| Telehandler | JCB/Manitou/Merlo | Moderate | Roof/boom base | Cabin frame | Cabin rear | 12V common | local-only acceptable | articulation blind spots | 2 | articulation path validation | `telehandler_generic.yaml` |
| UTV | Polaris/Can-Am | Moderate | Front rack/roof | Windshield bar | Rear cargo enclosure | 12V | lightweight network stack | high vibration | 2 | rough-road soak + thermal test | `utv_generic.yaml` |
| Drone spray | Agricultural UAV class | Complex | central frame | optional gimbal | airborne compute pod | custom | future ROS2/CAN bridge | airborne dynamics | 3 | dedicated flight envelope validation | `drone_spray.yaml` |
