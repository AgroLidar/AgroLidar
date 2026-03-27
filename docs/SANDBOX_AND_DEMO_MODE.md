# Sandbox and Demo Mode

## 1. Run Full Pipeline with Synthetic Data
```bash
make generate-data
make train
make evaluate
```
Synthetic generation is performed by `scripts/generate_synthetic_data.py`.

## 2. Run Inference Server in Demo Mode
```bash
make serve
```
Use checkpoint from smoke training or local training outputs.

## 3. Send Test Frame to `/predict`
```python
import base64
from datetime import datetime, timezone

import numpy as np
import requests

frame = np.random.rand(4, 512, 512).astype('float32')
payload = {
    'frame_data': base64.b64encode(frame.tobytes()).decode('utf-8'),
    'frame_id': 'sandbox_frame_001',
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'metadata': {'mode': 'sandbox'}
}
response = requests.post('http://127.0.0.1:8000/predict', json=payload, timeout=2)
print(response.status_code, response.json())
```

## 4. View MLflow Results
```bash
make mlflow-ui
```
Then open `http://localhost:5000`.

## 5. Trigger Safety Gate
```bash
make safety-check
```

## 6. Expected Outputs from Sandbox Cycle
- `outputs/checkpoints/best.pt`
- `outputs/onnx/model.onnx`
- `outputs/reports/eval_report.json`
- `outputs/reports/gate_report.json`
- `mlruns/`

## 7. Synthetic vs Real Data Gap
Synthetic data is useful for validation of pipeline mechanics and API behavior, not final field performance claims.
