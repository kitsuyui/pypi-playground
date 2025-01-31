# pypi-playground

[![codecov](https://codecov.io/gh/kitsuyui/pypi-playground/graph/badge.svg?token=CACIMSLMTV)](https://codecov.io/gh/kitsuyui/pypi-playground)
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

# LICENSE

BSD 3-Clause License
