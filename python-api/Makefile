.PHONY: test lint format clean

# Run unit tests with pytest
test:
	@echo "🔍 Running tests..."
	pytest app/integrations/openrouter/tests/ -v

# Lint Python code using flake8
lint:
	@echo "🧹 Running flake8 linter..."
	flake8 app/integrations/openrouter --max-line-length=88 --exclude=__init__.py

# Format code using black
format:
	@echo "🎨 Formatting code with black..."
	black app/integrations/openrouter

# Clean cache and temporary files
clean:
	@echo "🧼 Cleaning up temporary files..."
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache