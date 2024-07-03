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

# monorepo

This repository is a monorepo that contains multiple packages.
Packaging namespace packages are used to manage them.
https://packaging.python.org/en/latest/guides/packaging-namespace-packages/

Each package is managed in the `src` directory. And the packages are published to PyPI separately.

# Usage

## Install dependencies

Install dependencies with [poetry](https://python-poetry.org/).
If you don't have poetry installed, you can install it with the following command.

### Install poetry

#### Install pipx

If you don't have pipx installed, you can install it with the following command in macOS

```bash
brew install pipx
```

#### Install poetry

```bash
pipx install poetry
```

## Install dependencies

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

## Lint

```bash
poetry poe check
```

# LICENSE

BSD 3-Clause License
