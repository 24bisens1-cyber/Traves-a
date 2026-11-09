#!/usr/bin/env python3
"""Report local TRAVESÍA runtime/test prerequisites with actionable fixes."""
from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verification", action="store_true", help="also require pytest, Playwright and Node.js")
    args = parser.parse_args()
    checks: list[tuple[str, bool, str]] = []
    checks.append(("Python 3.11+", sys.version_info >= (3, 11), sys.version.split()[0]))
    required = {"flask": "Flask", "werkzeug": "Werkzeug"}
    if args.verification:
        required.update({"pytest": "pytest", "playwright": "Playwright"})
    for module, label in required.items():
        checks.append((label, importlib.util.find_spec(module) is not None, "installed" if importlib.util.find_spec(module) else "missing"))
    if args.verification:
        node = shutil.which("node")
        checks.append(("Node.js", bool(node), node or "missing — install Node.js 20 LTS or newer"))
    print("TRAVESÍA environment check")
    for label, ok, detail in checks:
        print(f"{'[OK]' if ok else '[MISSING]'} {label}: {detail}")
    missing = [label for label, ok, _ in checks if not ok]
    if missing:
        print("\nSetup required:")
        if any(name in missing for name in ("Flask", "Werkzeug", "pytest", "Playwright")):
            print("  python -m pip install -r requirements-dev.txt")
        if "Node.js" in missing:
            print("  Install Node.js 20 LTS or newer, reopen the terminal, and retry.")
        if "Python 3.11+" in missing:
            print("  Install Python 3.11 or newer and recreate the .venv environment.")
        return 2
    print("\nAll required dependencies are available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
