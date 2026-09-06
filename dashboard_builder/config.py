import os

REPO_ROOT = r"c:\Users\USER\AppData\Roaming\MetaQuotes\Terminal\3F2C3A2F8B221C9D88E569F2FD1D3E97\MQL5"
FILES_DIR = os.path.join(REPO_ROOT, "Files")

CSV_PATH_PRIMARY = os.path.join(FILES_DIR, "flagpro_trades_EURUSD.csv")
CSV_PATH_FALLBACK = os.path.join(FILES_DIR, "flagpro_trades_export.csv")

OUT_PATHS = [
    os.path.join(FILES_DIR, "eurusd_performance_report.html"),
    os.path.join(FILES_DIR, "flagpro_performance_dashboard.html"),
    r"C:\Users\USER\Desktop\FlagPro_Dashboard.html"
]

FRICTION_04_PER_TRADE = 0.48
