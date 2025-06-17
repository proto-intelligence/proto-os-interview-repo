.PHONY: test lint format clean

#execute tests with pytest
test:
	pytest integrations/openrouter/tests/ -v

# verify lint with flake8
lint:
	flake8 integrations/openrouter --max-line-length=88 --exclude=__init__.py

# format with black
format:
	black integrations/openrouter

# clean temp files and cache
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache
