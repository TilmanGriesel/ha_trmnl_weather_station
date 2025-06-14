.PHONY: format serve test

all: format

format:
	@echo "Formatting..."
	pre-commit run --all-files
	@echo "Formatting complete."

serve:
	@echo "Starting TRMNL serve..."
	cd TRMNL && make serve

test:
	@echo "Running tests in Docker..."
	docker run --rm -v $(PWD):/workspace -w /workspace python:3.11-slim bash -c "\
		apt-get update && apt-get install -y gcc && \
		pip install -r requirements-test.txt && \
		python -m pytest tests/ -v"
	@echo "Tests complete."
