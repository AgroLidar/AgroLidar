.PHONY: install setup pre-commit-install pre-commit-run pre-commit-update lint test generate-data train train-smoke mine queue full-loop retrain evaluate compare promote pipeline mlflow-ui mlflow-list serve serve-dev serve-docker export-onnx validate-onnx full-export safety-check regression-report registry-status check-install

install:
	pip install -r requirements.txt

setup: install pre-commit-install

pre-commit-install:
	pip install pre-commit && pre-commit install && pre-commit install --hook-type pre-push

pre-commit-run:
	pre-commit run --all-files

pre-commit-update:
	pre-commit autoupdate

lint:
	@command -v ruff >/dev/null 2>&1 || pip install ruff
	ruff check .

test:
	python -m pytest tests/ -v

train:
	python scripts/train.py --config configs/train.yaml

generate-data:
	python scripts/generate_synthetic_data.py

train-smoke:
	python scripts/generate_synthetic_data.py --train-samples 20 --val-samples 5
	python scripts/train.py --config configs/train.yaml
	python scripts/evaluate.py --config configs/base.yaml


mine:
	python scripts/mine_hard_cases.py --inference-dir outputs/inference/

queue:
	python scripts/build_review_queue.py

full-loop: mine queue retrain evaluate compare promote

retrain:
	python scripts/retrain.py --config configs/retrain.yaml

evaluate:
	python scripts/evaluate.py --config configs/base.yaml

compare:
	python scripts/compare_models.py \
		--production-metrics outputs/reports/production_eval.json \
		--candidate-metrics outputs/reports/eval_report.json

safety-check:
	python scripts/safety_gate.py \
		--candidate-report outputs/reports/eval_report.json \
		--production-report outputs/reports/production_eval.json \
		--output outputs/reports/gate_report.json

regression-report:
	python scripts/regression_report.py

promote:
	python scripts/promote_model.py \
		--candidate-model outputs/candidates/latest/checkpoints/best.pt \
		--production-model outputs/checkpoints/best.pt \
		--comparison-report outputs/reports/model_comparison.json

pipeline: train retrain evaluate safety-check compare promote

mlflow-ui:
	bash scripts/mlflow_ui.sh

mlflow-list:
	mlflow runs list --experiment-name agrolidar-bev-detection

serve:
	uvicorn inference_server.main:app --host 0.0.0.0 --port 8000

serve-dev:
	uvicorn inference_server.main:app --reload --port 8000

serve-docker:
	docker build -f Dockerfile.server -t agrolidar-server . && \
	docker run -p 8000:8000 -v $(pwd)/outputs:/app/outputs agrolidar-server


export-onnx:
	python scripts/export_onnx.py --validate --benchmark

validate-onnx:
	python scripts/validate_onnx.py \
		--onnx-path outputs/onnx/model.onnx \
		--checkpoint outputs/checkpoints/best.pt

full-export: export-onnx validate-onnx

registry-status:
	python scripts/registry_status.py

check-install:
	python scripts/check_installation.py
