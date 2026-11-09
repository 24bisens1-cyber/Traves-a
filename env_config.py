"""Small, dependency-free .env reader for local TRAVESÍA configuration."""
from __future__ import annotations

import os
import re
from pathlib import Path

_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_env_file(path: str | Path) -> set[str]:
    """Load missing environment values from a simple KEY=value file.

    Existing process environment values always win. Blank lines, comments,
    optional ``export`` prefixes, and single/double quoted values are supported.
    The function intentionally avoids shell evaluation and never executes code.
    """
    env_path = Path(path).expanduser()
    if not env_path.is_file():
        return set()
    loaded: set[str] = set()
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not _KEY.fullmatch(key) or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        else:
            # Only a whitespace-delimited hash starts an unquoted comment.
            value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
        if os.environ.setdefault(key, value) == value:
            loaded.add(key)
    return loaded
