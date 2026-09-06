"""
FlagPro Dashboard Builder Package
Modularized system for processing trade history CSVs, computing multi-period
consistency, metrics, SSR HTML generation, smart preset generation, and dashboard deployment.
"""

from .config import (
    REPO_ROOT,
    FILES_DIR,
    CSV_PATH_PRIMARY,
    CSV_PATH_FALLBACK,
    FRICTION_04_PER_TRADE,
)
from .filters import evaluate_trade_filters, compute_latency_stats
from .metrics import calc_scaleout_pnl, calc_pattern_metrics, calc_tf_metrics, calc_scaleout_comparison
from .consistency import calc_weekly_consistency, calc_multi_period_consistency
from .presets import optimize_smart_presets, export_preset_set_files
from .processor import process_symbol_dataset
from .pipeline import build_dashboard

__all__ = [
    "REPO_ROOT",
    "FILES_DIR",
    "CSV_PATH_PRIMARY",
    "CSV_PATH_FALLBACK",
    "FRICTION_04_PER_TRADE",
    "evaluate_trade_filters",
    "compute_latency_stats",
    "calc_scaleout_pnl",
    "calc_pattern_metrics",
    "calc_tf_metrics",
    "calc_scaleout_comparison",
    "calc_weekly_consistency",
    "calc_multi_period_consistency",
    "optimize_smart_presets",
    "export_preset_set_files",
    "process_symbol_dataset",
    "build_dashboard",
]
