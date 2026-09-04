#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlagPro Dashboard - Modular Builder & Bundler
1. Generates data/default_symbols.js from Files/flagpro_trades_*.csv
2. Inlines all modular CSS and JS into a standalone single-file Desktop/FlagPro_Dashboard.html
"""

import os
import re
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
MQL5_DIR = os.path.dirname(PROJECT_DIR)
FILES_DIR = os.path.join(MQL5_DIR, "Files")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
DESKTOP_DIR = os.path.join(os.path.expanduser("~"), "Desktop")

def build_default_symbols():
    """Generates data/default_symbols.js by reading initial CSVs."""
    print("📦 در حال استخراج داده‌های پیش‌فرض برای data/default_symbols.js...")
    # Find CSV files
    target_symbols = ["EURUSD", "GBPUSD"]
    embedded_data = {}

    for sym in target_symbols:
        csv_path = os.path.join(FILES_DIR, f"flagpro_trades_{sym}.csv")
        if not os.path.exists(csv_path):
            # Fallback to any matching CSV
            for f in os.listdir(FILES_DIR):
                if f.startswith(f"flagpro_trades_{sym}") and f.endswith(".csv"):
                    csv_path = os.path.join(FILES_DIR, f)
                    break

        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            embedded_data[sym] = content
            print(f"  ✅ نماد {sym} افزوده شد ({len(content.splitlines())} سطر)")

    # Save to data/default_csv_raw.js
    out_js = os.path.join(DATA_DIR, "default_symbols.js")
    with open(out_js, "w", encoding="utf-8") as f:
        f.write("// Preloaded Default Symbols CSVs for Offline Mode\n")
        f.write("window.DEFAULT_CSV_TEXTS = " + json.dumps(embedded_data, ensure_ascii=False) + ";\n")
        f.write("""
(function() {
    if (!window.DEFAULT_DATA) window.DEFAULT_DATA = {};
    if (window.DEFAULT_CSV_TEXTS && typeof DataEngine !== 'undefined') {
        Object.keys(window.DEFAULT_CSV_TEXTS).forEach(function(sym) {
            try {
                window.DEFAULT_DATA[sym] = DataEngine.processCSVData(window.DEFAULT_CSV_TEXTS[sym], sym + '.csv');
            } catch(e) { console.error('Error pre-processing', sym, e); }
        });
    }
})();
""")
    print(f"✅ فایل {out_js} با موفقیت ایجاد گردید.")

def bundle_to_single_html():
    """Bundles all modular files into a standalone HTML for Desktop."""
    print("🔨 در حال تولید نسخه تک‌فایلی مستقل (Standalone Bundle)...")
    index_path = os.path.join(PROJECT_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Inline CSS
    css_pattern = re.compile(r'<link\s+rel=["\']stylesheet["\']\s+href=["\']([^"\']+)["\']\s*/?>')
    def replace_css(match):
        rel_path = match.group(1)
        full_path = os.path.normpath(os.path.join(PROJECT_DIR, rel_path))
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as cf:
                return f"<style>\n/* Inlined: {rel_path} */\n{cf.read()}\n</style>"
        return match.group(0)

    html = css_pattern.sub(replace_css, html)

    # Inline JS
    js_pattern = re.compile(r'<script\s+src=["\']([^"\']+)["\']\s*></script>')
    def replace_js(match):
        rel_path = match.group(1)
        full_path = os.path.normpath(os.path.join(PROJECT_DIR, rel_path))
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as jf:
                return f"<script>\n// Inlined: {rel_path}\n{jf.read()}\n</script>"
        return match.group(0)

    html = js_pattern.sub(replace_js, html)

    # Write output to Desktop and MQL5/Files
    out_targets = [
        os.path.join(DESKTOP_DIR, "FlagPro_Dashboard.html"),
        os.path.join(MQL5_DIR, "FlagPro_Master_Dashboard.html"),
        os.path.join(FILES_DIR, "flagpro_performance_dashboard.html")
    ]

    for target in out_targets:
        try:
            with open(target, "w", encoding="utf-8") as out_f:
                out_f.write(html)
            print(f"  ✅ خروجی نوشته شد: {target}")
        except Exception as e:
            print(f"  ❌ خطا در نوشتن {target}: {e}")

if __name__ == "__main__":
    build_default_symbols()
    bundle_to_single_html()
    print("🎉 پروسه بیلد ماژولار با موفقیت به پایان رسید!")
