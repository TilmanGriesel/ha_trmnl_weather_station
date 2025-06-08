.PHONY: format

all: format

format:
	@echo "Formatting..."
	pre-commit run --all-files
	@echo "Formatting complete."
