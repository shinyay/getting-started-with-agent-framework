#!/usr/bin/env bash
set -euo pipefail

cd /workspaces

# Create .env from example if missing (no secrets included)
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
fi

echo "✅ Dev Container ready."
echo "Next:"
echo "  1) az login --use-device-code   # if you use AzureCliCredential"
echo "  2) Run exercises: see workshop/README.md"
echo "  3) DevUI: devui ./entities --host 0.0.0.0 --port 8080"

