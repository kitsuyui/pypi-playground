#!/bin/sh
set -eu

requirements=$(mktemp "${TMPDIR:-/tmp}/pypi-playground-requirements.XXXXXX")
trap 'rm -f "$requirements"' EXIT HUP INT TERM
uv export --quiet --locked --format requirements-txt --all-packages --no-dev \
  --no-emit-project --no-emit-workspace --output-file "$requirements"
# uv exports locked direct and transitive dependencies at exact versions.
# pip-audit evaluates environment markers for the current Python and platform;
# CI audits its own environment. No second dependency resolution is performed.
uv tool run pip-audit --disable-pip --no-deps -r "$requirements"
