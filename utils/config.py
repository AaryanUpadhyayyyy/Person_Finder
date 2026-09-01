"""Centralised configuration loader.

Reads .env once at import time, validates required keys, and exposes a
single ``get_config()`` accessor so every other module stays decoupled
from dotenv / os.environ details.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# ── locate .env relative to *this* file (works even when cwd differs) ──
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

if _ENV_PATH.is_file():
    load_dotenv(_ENV_PATH, override=False)

# ── required vs optional keys ──────────────────────────────────────────
_REQUIRED: tuple[str, ...] = (
    "SERPAPI_API_KEY",
    "ETH_RPC_URL",
    "ETH_PRIVATE_KEY",
)

_OPTIONAL_DEFAULTS: Dict[str, str] = {
    "IMGBB_API_KEY": "",
    "CONTRACT_ADDRESS": "",
    "SIMILARITY_THRESHOLD": "0.4",
}

# ── cached singleton ───────────────────────────────────────────────────
_config: Dict[str, str] | None = None


def get_config(*, skip_validation: bool = False) -> Dict[str, str]:
    """Return a dict of all pipeline configuration values.

    Parameters
    ----------
    skip_validation:
        When *True* missing required keys are silently set to ``""``.
        Useful for offline / partial testing.

    Raises
    ------
    SystemExit
        If a required key is missing and *skip_validation* is False.
    """
    global _config
    if _config is not None:
        return _config

    cfg: Dict[str, str] = {}

    # required
    missing: list[str] = []
    for key in _REQUIRED:
        val = os.environ.get(key, "").strip()
        if not val and not skip_validation:
            missing.append(key)
        cfg[key] = val

    if missing:
        print("\n✗ Missing required environment variables:", file=sys.stderr)
        for k in missing:
            print(f"   • {k}", file=sys.stderr)
        print(f"\n  Copy .env.example → .env and fill in the values.\n"
              f"  Path: {_ENV_PATH}\n", file=sys.stderr)
        sys.exit(1)

    # optional (with defaults)
    for key, default in _OPTIONAL_DEFAULTS.items():
        cfg[key] = os.environ.get(key, default).strip() or default

    _config = cfg
    return _config


def get_output_dir() -> Path:
    """Return (and create) the ``output/`` directory under project root."""
    out = _PROJECT_ROOT / "output"
    out.mkdir(exist_ok=True)
    return out
