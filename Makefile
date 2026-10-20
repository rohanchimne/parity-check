.PHONY: demo test clean

demo:
	python scripts/generate_data.py
	python -m parity run configs/orders.yaml
	python scripts/generate_data.py --inject timezone
	-python -m parity run configs/orders.yaml
	python scripts/generate_data.py

test:
	python -m pytest

clean:
	rm -rf data results .pytest_cache