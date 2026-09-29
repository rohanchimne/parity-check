.PHONY: demo test clean

demo:
	@echo "demo: not built yet"

test:
	python -m pytest

clean:
	rm -rf data results .pytest_cache