#!/bin/sh
set -eu

# Keep the spelling rules identical on developer machines and in CI.
exec uv tool run --from typos==1.46.1 typos .
