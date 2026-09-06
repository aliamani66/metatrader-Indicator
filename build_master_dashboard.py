"""
FlagPro Master Dashboard Entrypoint.
Delegates core processing to the modular dashboard_builder package.
Maintains 100% backward compatibility with Update_Dashboard.bat and flagpro_bridge_server.py.
"""
import sys
import os

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Ensure package import resolution
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from dashboard_builder import (
    build_dashboard,
    process_symbol_dataset,
    export_preset_set_files,
    optimize_smart_presets,
    REPO_ROOT,
    FILES_DIR,
    CSV_PATH_PRIMARY,
    CSV_PATH_FALLBACK,
    FRICTION_04_PER_TRADE,
)

if __name__ == "__main__":
    build_dashboard()
