#!/usr/bin/env bash
# Pulls the Ollama model DOCBOT uses by default. Run this once after
# `docker-compose up` -- the ollama container has no models baked in
# (that would make the image enormous), so this step is required before
# chat will work.
set -euo pipefail

MODEL="${1:-llama3}"

echo "Pulling '$MODEL' into the running ollama container..."
docker exec docbot-ollama ollama pull "$MODEL"
echo "Done. '$MODEL' is ready to use."
