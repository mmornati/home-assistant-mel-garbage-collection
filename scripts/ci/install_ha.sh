#!/usr/bin/env bash
# Install an exact Home Assistant version for CI and fail if pip picked another.
#
# Usage: scripts/ci/install_ha.sh <ha_version> [runtime|tests]
#
#   runtime  HA plus the integration's manifest requirements, as HA would
#            install them when loading mel_collecte. Enough for the import
#            smoke test and to read the HA source. Default.
#   tests    runtime, plus requirements-dev.txt for the unit tests.
#
# No pytest-homeassistant-custom-component: tests/conftest.py replaces the whole
# `homeassistant` package with stubs in sys.modules, so the unit tests never
# touch the installed HA and do not need that harness (its pytest plugin would
# import the real HA before the stubs and break them). The real-HA check is
# scripts/ci/import_smoke.py.

set -euo pipefail

HA_VERSION="${1:?usage: install_ha.sh <ha_version> [runtime|tests]}"
MODE="${2:-runtime}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MANIFEST="${ROOT}/custom_components/mel_collecte/manifest.json"

python -m pip install --upgrade pip

# One resolver run, so the manifest requirements must fit HA's own pins.
mapfile -t REQUIREMENTS < <(python -c \
  'import json, sys; [print(r) for r in json.load(open(sys.argv[1], encoding="utf-8")).get("requirements", [])]' \
  "$MANIFEST")
python -m pip install "homeassistant==${HA_VERSION}" "${REQUIREMENTS[@]}"

if [ "$MODE" = "tests" ]; then
  # Pin HA so the dev requirements cannot move it.
  CONSTRAINTS=$(mktemp)
  echo "homeassistant==${HA_VERSION}" > "$CONSTRAINTS"
  python -m pip install -r "${ROOT}/requirements-dev.txt" -c "$CONSTRAINTS"
  rm -f "$CONSTRAINTS"
fi

INSTALLED=$(python -c 'from homeassistant.const import __version__; print(__version__)')
if [ "$INSTALLED" != "$HA_VERSION" ]; then
  echo "::error::Requested Home Assistant ${HA_VERSION} but ${INSTALLED} is installed"
  exit 1
fi
echo "Installed Home Assistant ${INSTALLED}"
