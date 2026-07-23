#!/usr/bin/env bash
# One-time setup: creates backend/.env if it doesn't exist yet, so
# `docker-compose up` doesn't fail on a missing env_file.
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Install Docker Desktop (or Docker Engine + Compose plugin) first: https://docs.docker.com/get-docker/"
    exit 1
fi

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "Created backend/.env from backend/.env.example"
    echo "IMPORTANT: edit backend/.env and set a real SECRET_KEY before deploying beyond local testing."
else
    echo "backend/.env already exists, leaving it as-is."
fi

echo ""
echo "Setup complete. Next steps:"
echo "  1. docker-compose up --build -d"
echo "  2. ./scripts/pull-model.sh        # pulls the default Ollama model (llama3)"
echo "  3. Open http://localhost"
