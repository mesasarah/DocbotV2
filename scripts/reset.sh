#!/usr/bin/env bash
# Destroys all DOCBOT data: database, uploaded files, vector store, and
# downloaded Ollama models. Use when you want a completely clean slate.
set -euo pipefail
cd "$(dirname "$0")/.."

read -p "This deletes ALL documents, chat history, and downloaded models. Continue? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted."
    exit 0
fi

docker-compose down -v
echo "All DOCBOT containers and volumes removed."
