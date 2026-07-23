#!/usr/bin/env bash
# Convenience wrapper: tails logs from all DOCBOT containers.
set -euo pipefail
cd "$(dirname "$0")/.."
docker-compose logs -f "$@"
