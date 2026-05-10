#!/bin/bash
set -e

cd "$(dirname "$0")/.."

if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

if [ ! -f docker-compose.yml ]; then
    echo "Error: docker-compose.yml not found"
    exit 1
fi

if [ ! -d config ]; then
    echo "Creating config directory..."
    mkdir -p config
    cat > config/configuration.yaml << 'EOF'
# Home Assistant minimal configuration for MEL Collecte testing
homeassistant:
  name: MEL Local Test
  unit_system: metric
  time_zone: Europe/Paris

http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 127.0.0.1

logger:
  default: info
  logs:
    custom_components.mel_collecte: debug

# Enable the config flow UI
config:
EOF
    echo "Created minimal config directory"
fi

echo "Starting Home Assistant with your component..."
docker-compose up -d

echo ""
echo "Home Assistant is starting at http://localhost:8123"
echo ""
echo "To configure MEL Collecte:"
echo "  1. Go to Settings > Devices & Services"
echo "  2. Click 'Add Integration'"
echo "  3. Search for 'MEL'"
echo ""
echo "Your component at $(pwd)/custom_components/mel_collecte is mounted read-only"
echo "Any changes to the component will be reflected after restarting the container"
echo ""
echo "Use 'make test-local-stop' to stop the container"