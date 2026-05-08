# Contributing

Thank you for taking the time to improve pypi-playground.

## Development setup

This repository is a Python package workspace managed with
[uv](https://docs.astral.sh/uv/) and [Poe the Poet](https://poethepoet.natn.io/).
Packages live under `packages/`, and the root Poe tasks run the matching task
for each package.

```sh
uv sync
```

## Checks

Run formatting before opening a pull request:

```sh
uv run poe format
```

Run lint and type checks:

```sh
uv run poe check
```

Run the test suite:

```sh
uv run poe test
```

Build all packages when changing packaging metadata or release inputs:

```sh
uv run poe build
```

## Pull requests

Before opening a pull request, please make sure that:

- the change is focused on one topic;
- relevant checks pass locally;
- README or package documentation updates are included when behavior changes.

When reporting a failing check, include the command you ran and the relevant
error output.
