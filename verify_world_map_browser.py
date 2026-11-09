#!/usr/bin/env python3
"""Backward-compatible alias for the current GPU-independent Explore experience.

The old orbital globe was intentionally removed from the landing page. Explore now
uses a bundled illustrated atlas with clickable destination pins, so WebGL is not a
requirement. This alias delegates to the current cinematic UI browser acceptance suite.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshot", help="Accepted for compatibility; the current suite writes standard previews")
    parser.add_argument("--require-webgl", action="store_true", help="Deprecated: this UI intentionally no longer requires a WebGL globe")
    args = parser.parse_args()
    if args.require_webgl:
        print("WebGL-only verification is no longer applicable: the black orbital globe was removed. "
              "Explore uses a clickable illustrated atlas and the landing page uses destination photography.")
    target = Path(__file__).with_name("verify_cinematic_refresh_browser.py")
    return subprocess.run([sys.executable, str(target)], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
