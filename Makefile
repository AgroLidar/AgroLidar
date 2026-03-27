.PHONY: install lint test train retrain evaluate compare promote pipeline

install:
	pip install -r requirements.txt

lint:
	@command -v ruff >/dev/null 2>&1 || pip install ruff
	ruff check .

test:
	python -m pytest tests/ -v

train:
	python scripts/train.py --config configs/train.yaml

retrain:
	python scripts/retrain.py --config configs/retrain.yaml

evaluate:
	python scripts/evaluate.py --config configs/base.yaml

compare:
	python scripts/compare_models.py \
		--production-metrics outputs/reports/production_eval.json \
		--candidate-metrics outputs/reports/eval_report.json

promote:
	python scripts/promote_model.py \
		--candidate-model outputs/candidates/latest/checkpoints/best.pt \
		--production-model outputs/checkpoints/best.pt \
		--comparison-report outputs/reports/model_comparison.json

pipeline: train retrain evaluate compare promote
