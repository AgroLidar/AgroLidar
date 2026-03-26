# AgroLidar Evaluation Report

## Core Metrics

| Metric | Value |
|---|---:|
| mAP | 0.040892 |
| precision | 0.416058 |
| recall | 0.083090 |
| dangerous_fnr | 1.000000 |
| dangerous_class_aggregate_score | 0.000000 |
| segmentation_iou | 0.303171 |
| distance_mae | 0.131914 |
| latency_ms | 470.466561 |
| fps | 2.125550 |
| robustness_gap | 0.011873 |

## Safety-Critical Per-Class Metrics

| Class | Recall | FNR | Precision | Distance Error |
|---|---:|---:|---:|---:|
| human | 0.000000 | 1.000000 | 0.000000 | inf |
| animal | 0.000000 | 1.000000 | 0.000000 | inf |
| rock | 0.000000 | 1.000000 | 0.000000 | inf |
| post | 0.000000 | 1.000000 | 0.000000 | inf |
| vehicle | 0.431818 | 0.568182 | 0.416058 | 0.886583 |
