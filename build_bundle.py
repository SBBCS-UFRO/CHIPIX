#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run with ChimeraX's Python, or use `devel build` inside ChimeraX."""
import logging
from pathlib import Path

if __name__ == "__main__":
    try:
        from chimerax.bundle_builder import BundleBuilder
    except ImportError:
        raise SystemExit("Use ChimeraX Python, or run inside ChimeraX: devel build /PATH/CHIPIX-1.0.0")
    logging.basicConfig(level=logging.INFO)
    BundleBuilder(logging.getLogger("CHIPIX"),bundle_path=str(Path(__file__).resolve().parent)).make_wheel()
