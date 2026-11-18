#!/usr/bin/env python3
"""Import every integration module against the installed Home Assistant.

This is the meaningful check of a HA release for mel_collecte: the unit tests
replace the whole ``homeassistant`` package with stubs (tests/conftest.py), so
only this script runs the integration against the real HA. It works on HA betas
too and needs no test harness.

Two passes, exits non-zero if either fails:

1. import ``custom_components.mel_collecte`` and every module in it (platforms
   sensor, binary_sensor, calendar, the config flow, coordinator, api, dashboard,
   blueprints, ...). Catches removed HA APIs and Python packages HA no longer
   ships.
2. resolve every ``from homeassistant... import name`` written anywhere in the
   integration, including imports inside functions and ``try`` blocks that
   pass 1 never runs: dashboard.py imports websocket_api, frontend, http and
   entity_registry lazily, and __init__.py falls back to a dummy when
   ``homeassistant.helpers.aiohttp_client`` cannot be imported.
"""

import ast
import importlib
import pkgutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from homeassistant.const import __version__ as ha_version  # noqa: E402

PACKAGE = "custom_components.mel_collecte"


def ha_imports(package_path):
    """Yield (file, line, module, name) for each HA import in the integration.

    ``name`` is None for a plain ``import homeassistant.x``.
    """
    for file in sorted(package_path.rglob("*.py")):
        tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and (node.module or "").startswith("homeassistant"):
                for alias in node.names:
                    yield file.relative_to(ROOT), node.lineno, node.module, alias.name
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("homeassistant"):
                        yield file.relative_to(ROOT), node.lineno, alias.name, None


def resolve(module, name):
    """Import ``module`` and check ``name`` is an attribute or a submodule of it."""
    mod = importlib.import_module(module)
    if name is None or hasattr(mod, name):
        return
    importlib.import_module(f"{module}.{name}")


def main():
    package_path = ROOT / PACKAGE.replace(".", "/")
    modules = [PACKAGE] + [f"{PACKAGE}.{m.name}" for m in pkgutil.iter_modules([str(package_path)])]

    failed = []
    for name in modules:
        try:
            importlib.import_module(name)
            print(f"ok   {name}")
        except Exception as err:  # pylint: disable=broad-except
            print(f"FAIL {name}: {type(err).__name__}: {err}")
            failed.append(name)

    print()
    checked = set()
    for file, line, module, name in ha_imports(package_path):
        label = f"{module}.{name}" if name else module
        if label in checked:
            continue
        checked.add(label)
        try:
            resolve(module, name)
            print(f"ok   {label}")
        except Exception as err:  # pylint: disable=broad-except
            print(f"FAIL {label} ({file}:{line}): {type(err).__name__}: {err}")
            failed.append(label)

    if failed:
        print(f"\n{len(failed)} import(s) failed on Home Assistant {ha_version}")
        sys.exit(1)
    print(f"\nAll {len(modules)} modules and {len(checked)} Home Assistant names import on Home Assistant {ha_version}")


if __name__ == "__main__":
    main()
