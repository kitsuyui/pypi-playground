# pypi-playground

## What is this?

This is a repository for creating sample code for publishing to PyPI.
I manage multiple Python projects, but the configuration for publishing them to PyPI is almost the same.
In this playground, I experiment with them, and configure them to speed up CI and make project management easier.

- https://github.com/kitsuyui/python-richset
- https://github.com/kitsuyui/dict_zip
- https://github.com/kitsuyui/python-throttle-controller
- https://github.com/kitsuyui/cachepot
- https://github.com/kitsuyui/python-template-analysis
- https://github.com/kitsuyui/python-timevec

# Usage

## Install dependencies

Install dependencies with [poetry](https://python-poetry.org/).

```bash
poetry install
```

## Run tests

```bash
poetry poe test
```

## Format

```bash
poetry poe format
```

- [isort](https://pycqa.github.io/isort/) for import sorting
- [black](https://black.readthedocs.io/en/stable/) for formatting
- [pyupgrade](https://github.com/asottile/pyupgrade) for upgrading syntax to the latest version of Python

## Lint

```bash
poetry poe check
```

- [mypy](https://mypy.readthedocs.io/en/stable/) for static type checking
- [flake8](https://flake8.pycqa.org/en/latest/) for linting
- [black](https://black.readthedocs.io/en/stable/) for formatting check
- [isort](https://pycqa.github.io/isort/) for import sorting check

# LICENSE

MIT License
