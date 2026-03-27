# Next Iteration Prompt

## Highest-value next gap
Implement a **real sensor ingest adapter** that converts ROS bag or PCAP LiDAR streams into AgroLidar BEVFrameInput payloads compatible with `POST /predict`.

## Why this first
The current system is strong in offline pipeline, safety gating, and API serving, but still depends on synthetic BEV generation. Real-world pilot progress is blocked without ingesting native LiDAR captures.

## Suggested scope
1. Add `scripts/ingest_pcap_to_bev.py` (and/or ROS bag variant).
2. Implement transform + projection mapping from sensor frame to BEV tensor contract in `docs/DATA_SCHEMA.md`.
3. Add calibration parameter ingestion from `configs/platforms/*.yaml`.
4. Add integration tests with fixture packets/bags.
5. Add ingestion troubleshooting docs and sample replay command.

## Follow-on iterations
- Jetson Orin edge deployment hardening.
- API authentication layer (mTLS/API key).
- ROS 2 perception node with health and diagnostics topics.
