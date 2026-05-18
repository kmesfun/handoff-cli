.PHONY: install dev lint format typecheck test test-cov build clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"
	pip install pytest pytest-mock mypy ruff coverage

lint:
	ruff check handoff/ tests/

format:
	ruff format handoff/ tests/

typecheck:
	mypy handoff/

test:
	pytest tests/

test-cov:
	coverage run -m pytest tests/
	coverage report -m
	coverage html

build:
	pip install build
	python -m build

clean:
	rm -rf dist/ build/ *.egg-info .mypy_cache .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
