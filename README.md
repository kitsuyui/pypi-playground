# pypi-playground

![Coverage](https://raw.githubusercontent.com/kitsuyui/octocov-central/main/badges/kitsuyui/pypi-playground/coverage.svg)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

## What is this?

This repository contains sample code for publishing Python packages to PyPI.
I manage multiple Python projects, and the configurations for publishing them to PyPI are almost identical.
In this playground, I experiment with different configurations to optimize CI processes and streamline project management.

<details>
  <summary>List of Spun-off Repositories</summary>

  - [python-richset](https://github.com/kitsuyui/python-richset): A rich set implementation for Python.
  - [dict_zip](https://github.com/kitsuyui/dict_zip): A utility for zipping and unzipping dictionaries.
  - [python-throttle-controller](https://github.com/kitsuyui/python-throttle-controller): A Python library for rate-limiting and throttling control.
  - [cachepot](https://github.com/kitsuyui/cachepot): A caching utility to simplify working with in-memory caches.
  - [python-template-analysis](https://github.com/kitsuyui/python-template-analysis): A template analysis tool for Python projects.
  - [python-timevec](https://github.com/kitsuyui/python-timevec): A library for time vector manipulations in Python.

</details>

# Spinning-off and Incubation

I have various code snippets and boilerplate code in private repositories or local directories.
I plan to spin them off and place them in this repository.
I will also use this repository to incubate these codes until they are mature enough to become independent repositories.
During this process, I will add tests, CI, documentation, and other improvements.

# Monorepo

This repository is a monorepo containing multiple packages.
To manage these packages, namespace packages are used.
For more information, refer to the [official Python packaging guide on namespace packages](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/).

Each package is organized within the src directory, and the packages are published to PyPI independently.


# Usage

## Install dependencies

Install dependencies with [uv](https://docs.astral.sh/uv/) 
If you don't have uv installed, you can install it with the following command.

### Install uv run

#### Install pipx

If you don't have pipx installed, you can install it with the following command in macOS

```bash
brew install pipx
```

#### Install uv

```bash
pipx install uv
```

## Install dependencies

```bash
uv sync
```

## Run tests

```bash
uv run poe test
```

## Format

```bash
uv run poe format
```

## Lint

```bash
uv run poe check
```

## Development

This repository uses [lefthook](https://lefthook.dev/) to run the same checks as CI
locally, so problems surface before they reach CI.

```sh
# Install dependencies
uv sync

# Install the Git hooks (once; requires lefthook on your PATH)
lefthook install
```

Once installed, the hooks run automatically:

- **pre-commit**: `uv run poe check` and `./scripts/check-spelling.sh`
- **pre-push**: the same checks, `uv run poe test`, `uv run poe build`,
  and `./scripts/check-dependencies.sh`

The spelling and dependency checks use the same scripts in CI and in the hooks.
The first run downloads the pinned `typos` tool and `pip-audit` via `uv`.
The dependency audit checks locked direct and transitive dependencies for the
current Python version and platform without resolving them again. CI runs the
same command in its own environment; a local audit does not cover every
platform. The audit queries an online vulnerability database, so it needs
network access. A failed check prevents the commit or push.

The hooks check the working tree, not a snapshot of staged or pushed content.
Before committing partially staged files, make sure their working-tree contents
match what you intend to commit. Run the pre-push checks with a clean working
tree to check the content being pushed.

You can also run the checks manually:

```sh
uv run poe check
uv run poe test
uv run poe build
./scripts/check-spelling.sh
./scripts/check-dependencies.sh
```

CI still runs the full matrix (see `.github/workflows/`); the hooks only bring that
feedback earlier on your machine.

# LICENSE

BSD 3-Clause License
