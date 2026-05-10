#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "Stopping Home Assistant local instance..."
docker-compose down

echo "Container stopped."