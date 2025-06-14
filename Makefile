.PHONY: format serve

all: format

format:
	@echo "Formatting..."
	pre-commit run --all-files
	@echo "Formatting complete."

serve:
	@echo "Starting TRMNL serve..."
	cd TRMNL && make serve
