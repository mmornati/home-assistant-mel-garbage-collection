#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "Restarting Home Assistant with latest changes..."
docker-compose restart

echo "Container restarted. Your component changes are now loaded."