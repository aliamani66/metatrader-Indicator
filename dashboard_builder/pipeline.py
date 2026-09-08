import os
import sys
import re
import json
import subprocess
from datetime import datetime

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

from .config import REPO_ROOT, FILES_DIR, CSV_PATH_PRIMARY, CSV_PATH_FALLBACK
from .processor import process_symbol_dataset
from .presets import export_preset_set_files

# Ensure repo root is in sys.path so tester_compare_module is importable
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    import tester_compare_module
except ImportError:
    tester_compare_module = None


def peek_symbol_from_csv(csv_path):
    try:
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            f.readline()
            line = f.readline()
            if line:
                sym = line.split(',')[0].strip().replace('!', '').replace('#', '')
                if sym and not sym.startswith('FLAG_') and not sym.startswith('BOX_'):
                    return sym
    except Exception:
        pass
    return None


def build_dashboard(custom_csv=None):
    files_dir = FILES_DIR
    repo_root = REPO_ROOT
    cands = []
    if custom_csv and os.path.exists(custom_csv):
        cands = [custom_csv]
    elif len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        cands = [sys.argv[1]]
    else:
        if os.path.exists(files_dir):
            for f in os.listdir(files_dir):
                if (f.startswith('flagpro_trades') or f.startswith('flag_trades')) and f.endswith('.csv'):
                    cands.append(os.path.join(files_dir, f))

    if not cands:
        if os.path.exists(CSV_PATH_PRIMARY):
            cands.append(CSV_PATH_PRIMARY)
        elif os.path.exists(CSV_PATH_FALLBACK):
            cands.append(CSV_PATH_FALLBACK)

    # Sort files by modification time (newest first) so user's latest test is always picked
    cands.sort(key=lambda f: os.path.getmtime(f) if os.path.exists(f) else 0, reverse=True)

    symbols_data = {}
    for c_file in cands:
        try:
            peeked_sym = peek_symbol_from_csv(c_file)
            if peeked_sym and peeked_sym in symbols_data:
                continue

            res = process_symbol_dataset(c_file)
            if res and res.get('closed_count', 0) > 0:
                s_name = res.get('clean_symbol', res.get('symbol', 'UNKNOWN'))
                if s_name not in symbols_data:
                    symbols_data[s_name] = res
                    print(f"✅ نماد {s_name} با {res['closed_count']} معامله از فایل {os.path.basename(c_file)} ثبت شد.")
        except Exception as e:
            print(f"⚠️ رد کردن فایل {os.path.basename(c_file)}: {e}")

    if not symbols_data:
        init_data_path = os.path.join(repo_root, "FlagPro_Modular_App", "data", "initial_data.js")
        if os.path.exists(init_data_path):
            try:
                with open(init_data_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                s_idx = content.find("window.ALL_SYMBOLS_DATA = ") + len("window.ALL_SYMBOLS_DATA = ")
                e_idx = content.find("window.TESTER_REPORTS", s_idx)
                if e_idx > s_idx:
                    json_str = content[s_idx:e_idx].strip().rstrip(';')
                    cached = json.loads(json_str)
                    if cached:
                        symbols_data = cached
                        print(f"ℹ️ داده‌های نمادها از حافظه کش بازیابی شدند ({len(symbols_data)} نماد: {', '.join(symbols_data.keys())}).")
            except Exception as e:
                print(f"⚠️ خطا در خواندن حافظه کش: {e}")

    if not symbols_data:
        print("❌ هیچ داده معتبری برای تولید داشبورد یافت نشد!")
        return

    # Auto-export smart preset .set files to Experts/تنظیمات and Profiles/Tester
    export_preset_set_files(symbols_data)

    default_sym = 'GBPUSD' if 'GBPUSD' in symbols_data else max(symbols_data.keys(), key=lambda s: len(symbols_data[s].get('trades_json_list', [])))
    default_data = symbols_data[default_sym]
    print(f"🌟 نماد پیش‌فرض هدر داشبورد: {default_sym} ({default_data['tfs_str']})")

    # Build options for symbol selector
    symbol_options_list = []
    for s_name, s_info in sorted(symbols_data.items()):
        sel_attr = 'selected' if s_name == default_sym else ''
        c_count = s_info.get("closed_count", len(s_info.get("trades_json_list", [])))
        k_count = s_info.get("tot_k_cnt", 0)
        symbol_options_list.append(f'<option value="{s_name}" {sel_attr}>{s_name} ({s_info["tfs_str"]}) - کل: {c_count} | سلاطین: {k_count} معامله</option>')
    symbol_options_html = "\n".join(symbol_options_list)

    # Client payload for all symbols
    client_symbols_payload = {}
    for s_name, s_data in symbols_data.items():
        client_symbols_payload[s_name] = {
            'symbol': s_data['symbol'],
            'min_date': s_data['min_date'],
            'max_date': s_data['max_date'],
            'tfs_str': s_data['tfs_str'],
            'date_start_str': s_data['date_start_str'],
            'date_end_str': s_data['date_end_str'],
            'bal_initial': s_data['bal_initial'],
            'tot_k_cnt': s_data.get('tot_k_cnt', 0),
            'closed_count': s_data.get('closed_count', 0),
            'pending': s_data.get('pending', 0),
            'total_setups': s_data.get('total_setups', 0),
            'kings_sim_list': s_data['kings_sim_list'],
            'top3_sl_cnt_keys': s_data['top3_sl_cnt_keys'],
            'top3_sl_usd_keys': s_data['top3_sl_usd_keys'],
            'top5_sl_usd_keys': s_data['top5_sl_usd_keys'],
            'top3_sl_pct_keys': s_data['top3_sl_pct_keys'],
            'trades_sim_list': s_data['trades_sim_list'],
            'smart_presets': s_data['smart_presets'],
            'weekly_bar_data': s_data['weekly_bar_data'],
            'trades_json_list': s_data['trades_json_list'],
            'latency_all': s_data.get('latency_all', {}),
            'latency_kings': s_data.get('latency_kings', {}),
            'latency_tfs': s_data.get('latency_tfs', {}),
            'mp_intersection_list': s_data.get('mp_intersection_list', []),
            'sl_battle_matrix': s_data.get('sl_battle_matrix', {}),
        }

    # 1. Update FlagPro_Modular_App initial data (merging existing symbols so none are lost)
    modular_dir = os.path.join(repo_root, "FlagPro_Modular_App")
    modular_data_file = os.path.join(modular_dir, "data", "initial_data.js")
    os.makedirs(os.path.dirname(modular_data_file), exist_ok=True)
    if os.path.exists(modular_data_file):
        try:
            with open(modular_data_file, 'r', encoding='utf-8') as mf:
                old_content = mf.read()
            old_prefix = 'window.ALL_SYMBOLS_DATA = '
            if old_prefix in old_content:
                old_json_str = old_content[len(old_prefix):old_content.find(';\nwindow.TESTER_REPORTS')]
                existing_symbols = json.loads(old_json_str)
                for sym_k, sym_v in existing_symbols.items():
                    if sym_k not in client_symbols_payload:
                        for bad_k in ['tab_equity_html', 'tab_kings_html', 'tab_scaleout_html', 'tab_timeframes_html', 'tab_filters_html', 'tab_loss_intel_html', 'tab_weekly_html', 'smart_presets_rows_html']:
                            sym_v.pop(bad_k, None)
                        client_symbols_payload[sym_k] = sym_v
        except Exception as ex:
            print(f"Notice: Could not merge existing symbols: {ex}")

    json_symbols_payload = json.dumps(client_symbols_payload, separators=(',', ':'))

    # Load MT5 Strategy Tester Reports
    tester_reports = {}
    if tester_compare_module:
        tester_reports_dir = os.path.join(files_dir, "FlagPro_TesterReports")
        tester_reports = tester_compare_module.load_tester_reports(tester_reports_dir)
    json_tester_reports_payload = json.dumps(tester_reports, separators=(',', ':'))

    with open(modular_data_file, mode='w', encoding='utf-8') as f:
        f.write(f"window.ALL_SYMBOLS_DATA = {json_symbols_payload};\nwindow.TESTER_REPORTS = {json_tester_reports_payload};\n")
    print(f"✅ داده‌های پروژه ماژولار به‌روزرسانی شد: {modular_data_file}")

    # 2. Run bundler to generate standalone single-file distribution
    bundler_script = os.path.join(modular_dir, "tools", "bundler.py")
    if os.path.exists(bundler_script):
        subprocess.run([sys.executable, bundler_script], check=True)

    # 3. Read generated bundled distribution, pre-render default views (SSR), and deploy to targets
    dist_html_file = os.path.join(modular_dir, "dist", "FlagPro_Modular_App.html")
    with open(dist_html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    if default_data.get('min_date'):
        html = html.replace('<b id="headerMinDate">-</b>', f'<b id="headerMinDate">{default_data["min_date"]}</b>')
    if default_data.get('max_date'):
        html = html.replace('<b id="headerMaxDate">-</b>', f'<b id="headerMaxDate">{default_data["max_date"]}</b>')

    # Update symbolSelector with dynamic options generated from symbols_data
    html = re.sub(
        r'<select id="symbolSelector"[^>]*>[\s\S]*?</select>',
        lambda m: f'<select id="symbolSelector" onchange="switchDashboardSymbol(this.value)" style="background:#0f172a;border:1px solid #334155;color:#38bdf8;font-weight:bold;padding:4px 8px;border-radius:6px;font-size:12px;outline:none;cursor:pointer;">\n{symbol_options_html}\n</select>',
        html,
        count=1
    )

    with open(dist_html_file, 'w', encoding='utf-8') as f:
        f.write(html)

    clean_sym_name = default_data.get('clean_symbol', default_sym)
    out_paths = [
        os.path.join(files_dir, "flagpro_performance_dashboard.html"),
        os.path.join(files_dir, "eurusd_performance_report.html"),
        os.path.join(files_dir, "gbpusd_performance_report.html"),
        os.path.join(files_dir, f"{clean_sym_name.lower()}_performance_report.html"),
        os.path.join(repo_root, "FlagPro_Master_Dashboard.html"),
        r"C:\Users\USER\Desktop\FlagPro_Dashboard.html"
    ]

    for out_path in out_paths:
        try:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, mode='w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ داشبورد ماژولار با موفقیت مستقر شد: {out_path}")
        except Exception as e:
            print(f"❌ خطا در نوشتن {out_path}: {e}")
