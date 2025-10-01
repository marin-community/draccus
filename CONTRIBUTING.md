# Contributing to Draccus

Thank you for your interest in contributing to Draccus!

## Development Setup

This project uses [uv](https://github.com/astral-sh/uv) for Python package management.

### Installing Dependencies

```bash
# Install uv if you haven't already, other options: https://docs.astral.sh/uv/getting-started/installation/
pip install uv
```

## Running Tests

We use [pytest](https://pytest.org/) for testing:

```bash
# Run all tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_base.py
```

### Snapshot Testing with Syrupy

We use [syrupy](https://github.com/syrupy-project/syrupy) for testing CLI output.

When you first run tests that use snapshots, syrupy will create snapshot files in `__snapshots__` directories. These files should be committed to the repository.

```bash
# Update snapshots when output intentionally changes
uv run pytest --snapshot-update
```

## Code Style

We use `black`, `ruff`, and `mypy` to maintain code quality. Run pre-commit hooks:

```bash
# One time, to run on each commit
uvx pre-commit install

# As desired, by hand on all files
uvx pre-commit run --all-files
```
