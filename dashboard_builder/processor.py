import os
import csv
import re
import math
import json
from collections import defaultdict
from datetime import datetime

from dashboard_builder.config import FRICTION_04_PER_TRADE
from dashboard_builder.filters import (
    is_single_ls, is_night_session, is_pre_london, is_toxic_pattern, is_pure_flag,
    get_box_wait_time_minutes, format_duration_short, format_duration_persian,
    compute_latency_stats, evaluate_trade_filters
)
from dashboard_builder.metrics import (
    calc_scaleout_pnl, calc_pattern_metrics, calc_tf_metrics, calc_scaleout_comparison
)
from dashboard_builder.consistency import (
    calc_weekly_consistency, calc_multi_period_consistency
)
from dashboard_builder.presets import (
    optimize_smart_presets
)

def process_symbol_dataset(csv_file):
    print(f"📂 در حال پردازش داده‌های فایل: {csv_file}")
    if not os.path.exists(csv_file):
        return None

    all_raw_rows = []
    with open(csv_file, mode='r', encoding='utf-8-sig', errors='ignore') as f:
        for r in csv.DictReader(f):
            all_raw_rows.append(r)

    symbol = 'EURUSD'
    if all_raw_rows and all_raw_rows[0].get('Symbol'):
        symbol = all_raw_rows[0].get('Symbol').strip()
    else:
        m = re.search(r'flagpro_trades_([A-Za-z0-9_]+)[.]csv', os.path.basename(csv_file))
        if m: symbol = m.group(1).upper()

    clean_symbol = re.sub(r'[^A-Za-z0-9]', '', symbol) or 'EURUSD'

    available_tfs = sorted(list(set(r.get('Timeframe') for r in all_raw_rows if r.get('Timeframe'))))
    if not available_tfs: available_tfs = ['M1', 'M5', 'M15']
    tfs_str = ', '.join(available_tfs)

    rows = [r for r in all_raw_rows if r.get('Timeframe') in available_tfs]
    total_setups = len(rows)
    pending = [r for r in rows if r.get('Outcome') == 'Pending']
    entered = [r for r in rows if r.get('Outcome') != 'Pending']
    closed = [r for r in entered if r.get('IsClosed') == 'True']
    if not closed:
        return None
    in_trade = [r for r in entered if r.get('IsClosed') != 'True']

    dates = [r.get('BoxTimeStart') for r in rows if r.get('BoxTimeStart') and r.get('BoxTimeStart') != 'None']
    min_date = min(dates) if dates else 'نامشخص'
    max_date = max(dates) if dates else 'نامشخص'
    entry_dates = [r.get('EntryTime', '') for r in closed if r.get('EntryTime')]
    date_start_str = min(entry_dates)[:10] if entry_dates else min_date
    date_end_str = max(entry_dates)[:10] if entry_dates else max_date

    try:
        dt_s = datetime.strptime(date_start_str[:10], "%Y.%m.%d")
        dt_e = datetime.strptime(date_end_str[:10], "%Y.%m.%d")
        span_months = (dt_e.year - dt_s.year) * 12 + (dt_e.month - dt_s.month) + 1
        span_years = round((dt_e - dt_s).days / 365.25, 1)
        if span_years >= 1.8:
            history_span_title = f"{span_years} ساله ({span_months} ماهه)"
        else:
            history_span_title = f"{span_months} ماهه"
        base_yr = dt_s.year
    except:
        history_span_title = "کل تاریخچه"
        base_yr = 2025

    # Filter evaluation
    f_res = evaluate_trade_filters(closed)
    accepted_trades = f_res['accepted_trades']
    rejected_trades = f_res['rejected_trades']
    f1_rej, f1_sl = f_res['f1_rej'], f_res['f1_sl']
    f2_rej, f2_sl = f_res['f2_rej'], f_res['f2_sl']
    f3_rej, f3_sl = f_res['f3_rej'], f_res['f3_sl']
    f4_rej, f4_sl = f_res['f4_rej'], f_res['f4_sl']
    f5_rej, f5_sl = f_res['f5_rej'], f_res['f5_sl']
    f7_rej, f7_sl = f_res['f7_rej'], f_res['f7_sl']
    w1_cnt_b, w2_cnt_b, sl_cnt_b = f_res['w1_cnt_b'], f_res['w2_cnt_b'], f_res['sl_cnt_b']
    w1_rate_b, w2_rate_b, sl_rate_b = f_res['w1_rate_b'], f_res['w2_rate_b'], f_res['sl_rate_b']
    ev_b = f_res['ev_b']
    w1_cnt_a, w2_cnt_a, sl_cnt_a = f_res['w1_cnt_a'], f_res['w2_cnt_a'], f_res['sl_cnt_a']
    w1_rate_a, w2_rate_a, sl_rate_a = f_res['w1_rate_a'], f_res['w2_rate_a'], f_res['sl_rate_a']
    ev_a = f_res['ev_a']
    sl_in_rej = f_res['sl_in_rej']
    rej_accuracy = f_res['rej_accuracy']

    # Dynamic Kings Selection
    tf_role_map_raw = defaultdict(list)
    for r in closed:
        tf_role_map_raw[(r.get('Timeframe', 'M1'), r.get('Role', 'Unknown'))].append(r)

    qualified_kings = []
    for (tf, role), t_list in tf_role_map_raw.items():
        m = calc_pattern_metrics(t_list, tf, role, FRICTION_04_PER_TRADE)
        if m['is_king_eligible']:
            qualified_kings.append(m)

    # Fallback: if no pattern qualified, include all available patterns with closed trades
    if not qualified_kings:
        for (tf, role), t_list in tf_role_map_raw.items():
            m = calc_pattern_metrics(t_list, tf, role, FRICTION_04_PER_TRADE)
            if m and m.get('cnt', 0) > 0:
                qualified_kings.append(m)

    qualified_kings.sort(key=lambda x: (x['score'], x['cnt']), reverse=True)

    kings_trades = []
    for k in qualified_kings:
        kings_trades.extend(k['trades'])

    tot_k_cnt = len(kings_trades)
    tot_k_fric = tot_k_cnt * FRICTION_04_PER_TRADE
    tot_k_gross = sum(k['gross'] for k in qualified_kings)
    tot_k_net = sum(k['net'] for k in qualified_kings)
    king_keys = {(k['role'], k['tf']) for k in qualified_kings}

    # Scaleout comparison
    sc_res = calc_scaleout_comparison(kings_trades, FRICTION_04_PER_TRADE)
    s1_net = sc_res['s1_net']
    s1_pf = sc_res['s1_pf']
    s2_net = sc_res['s2_net']
    s2_pf = sc_res['s2_pf']
    s2_diff_dollar = sc_res['s2_diff_dollar']
    s2_diff_pct = sc_res['s2_diff_pct']
    s3_net = sc_res['s3_net']
    s3_pf = sc_res['s3_pf']
    s3_diff_dollar = sc_res['s3_diff_dollar']
    s3_diff_pct = sc_res['s3_diff_pct']
    sl_direct = sc_res['sl_direct']
    tp1_only = sc_res['tp1_only']
    tp2_only = sc_res['tp2_only']
    tp3_4 = sc_res['tp3_4']
    sl_direct_pct = sc_res['sl_direct_pct']
    tp1_only_pct = sc_res['tp1_only_pct']
    tp2_only_pct = sc_res['tp2_only_pct']
    tp3_4_pct = sc_res['tp3_4_pct']
    m1_net = sc_res['m1_net']
    m2_net = sc_res['m2_net']
    be_diff = sc_res['be_diff']

    # Timeframe breakdown
    tf_map = defaultdict(list)
    for r in closed:
        tf_map[r.get('Timeframe', 'Unknown')].append(r)

    symbol_latency_all = compute_latency_stats(entered)
    symbol_latency_kings = compute_latency_stats(kings_trades)
    symbol_latency_tfs = {tf: compute_latency_stats([r for r in entered if r.get('Timeframe') == tf]) for tf in available_tfs}
    for tf_key in ['M1', 'M5', 'M15']:
        if tf_key not in symbol_latency_tfs:
            symbol_latency_tfs[tf_key] = compute_latency_stats([])

    tf_kings_rows = []
    for tf_name in available_tfs:
        t_sub = [r for r in kings_trades if r.get('Timeframe') == tf_name]
        d = calc_tf_metrics(t_sub, FRICTION_04_PER_TRADE)
        if not d: continue
        col = "#00e676" if d['net'] >= 0 else "#ef4444"
        tf_kings_rows.append(f"""
        <tr>
            <td style="color:#38bdf8;font-weight:bold;font-size:14px;">{tf_name}</td>
            <td style="text-align:center;font-weight:bold;">{d['cnt']} معامله</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{d['w1_p']:.1f}%</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{d['w2_p']:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;">{d['w3_p']:.1f}%</td>
            <td style="text-align:center;color:#c084fc;">{d['w4_p']:.1f}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{d['sl_p']:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">${d['gross']:+.2f}</td>
            <td style="text-align:center;color:#f87171;font-weight:bold;">${d['fric']:.2f}-</td>
            <td style="text-align:center;color:{col};font-weight:bold;font-size:15px;background:#064e3b22;">${d['net']:+.2f} دلار</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;background:#0369a118;">⏱️ {d['wait_avg_fmt']}</td>
            <td style="text-align:center;color:#94a3b8;font-size:11px;font-family:monospace;direction:ltr;">{d['wait_range_fmt']}</td>
        </tr>
        """)

    d_tot_kings = calc_tf_metrics(kings_trades, FRICTION_04_PER_TRADE) or {
        'cnt': 0, 'w1_p': 0.0, 'w2_p': 0.0, 'w3_p': 0.0, 'w4_p': 0.0, 'sl_p': 0.0, 'gross': 0.0, 'fric': 0.0, 'net': 0.0,
        'wait_avg_fmt': '-', 'wait_range_fmt': '-', 'wait_avg_short': '-'
    }
    tot_kings_col = "#00e676" if d_tot_kings['net'] >= 0 else "#ef4444"
    tf_kings_rows.append(f"""
    <tr style="background:#1e293b;border-top:2px solid #38bdf8;">
        <td style="color:#facc15;font-weight:bold;font-size:15px;">👑 مجموع کل سلاطین برگزیده</td>
        <td style="text-align:center;font-weight:bold;color:#facc15;font-size:14px;">{d_tot_kings['cnt']} معامله</td>
        <td style="text-align:center;color:#00e676;font-weight:bold;">{d_tot_kings['w1_p']:.1f}%</td>
        <td style="text-align:center;color:#00e676;font-weight:bold;">{d_tot_kings['w2_p']:.1f}%</td>
        <td style="text-align:center;color:#38bdf8;">{d_tot_kings['w3_p']:.1f}%</td>
        <td style="text-align:center;color:#c084fc;">{d_tot_kings['w4_p']:.1f}%</td>
        <td style="text-align:center;color:#ef4444;font-weight:bold;">{d_tot_kings['sl_p']:.1f}%</td>
        <td style="text-align:center;color:#38bdf8;font-weight:bold;font-size:15px;">${d_tot_kings['gross']:+.2f}</td>
        <td style="text-align:center;color:#f87171;font-weight:bold;font-size:15px;">${d_tot_kings['fric']:.2f}-</td>
        <td style="text-align:center;color:{tot_kings_col};font-weight:bold;font-size:16px;background:#064e3b;">${d_tot_kings['net']:+.2f} دلار نقد</td>
        <td style="text-align:center;color:#38bdf8;font-weight:bold;font-size:14px;background:#0369a125;">⏱️ {d_tot_kings['wait_avg_fmt']}</td>
        <td style="text-align:center;color:#facc15;font-size:12px;font-family:monospace;direction:ltr;">{d_tot_kings['wait_range_fmt']}</td>
    </tr>
    """)

    tf_raw_rows = []
    for tf_name in available_tfs:
        t_sub = [r for r in closed if r.get('Timeframe') == tf_name]
        d = calc_tf_metrics(t_sub, FRICTION_04_PER_TRADE)
        if not d: continue
        col = "#00e676" if d['net'] >= 0 else "#ef4444"
        tf_raw_rows.append(f"""
        <tr style="opacity:0.85;">
            <td style="color:#94a3b8;font-weight:bold;">{tf_name} (خام)</td>
            <td style="text-align:center;">{d['cnt']} معامله</td>
            <td style="text-align:center;">{d['w1_p']:.1f}%</td>
            <td style="text-align:center;">{d['w2_p']:.1f}%</td>
            <td style="text-align:center;">{d['w3_p']:.1f}%</td>
            <td style="text-align:center;">{d['w4_p']:.1f}%</td>
            <td style="text-align:center;color:#ef4444;">{d['sl_p']:.1f}%</td>
            <td style="text-align:center;color:{col};font-weight:bold;">${d['net']:+.2f} دلار</td>
            <td style="text-align:center;color:#38bdf8;">{d['wait_avg_fmt']}</td>
            <td style="text-align:center;color:#94a3b8;font-size:11px;font-family:monospace;direction:ltr;">{d['wait_range_fmt']}</td>
        </tr>
        """)

    d_tot_raw = calc_tf_metrics(closed, FRICTION_04_PER_TRADE) or {
        'cnt': 0, 'w1_p': 0.0, 'w2_p': 0.0, 'w3_p': 0.0, 'w4_p': 0.0, 'sl_p': 0.0, 'gross': 0.0, 'fric': 0.0, 'net': 0.0,
        'wait_avg_fmt': '-', 'wait_range_fmt': '-', 'wait_avg_short': '-'
    }
    tot_raw_col = "#00e676" if d_tot_raw['net'] >= 0 else "#ef4444"
    tf_raw_rows.append(f"""
    <tr style="background:#1c1917;border-top:1px solid #44403c;">
        <td style="color:#f87171;font-weight:bold;">❌ مجموع کل بازار خام</td>
        <td style="text-align:center;font-weight:bold;">{d_tot_raw['cnt']} معامله</td>
        <td style="text-align:center;">{d_tot_raw['w1_p']:.1f}%</td>
        <td style="text-align:center;">{d_tot_raw['w2_p']:.1f}%</td>
        <td style="text-align:center;">{d_tot_raw['w3_p']:.1f}%</td>
        <td style="text-align:center;">{d_tot_raw['w4_p']:.1f}%</td>
        <td style="text-align:center;color:#ef4444;font-weight:bold;">{d_tot_raw['sl_p']:.1f}%</td>
        <td style="text-align:center;color:{tot_raw_col};font-weight:bold;font-size:15px;">${d_tot_raw['net']:+.2f} دلار</td>
        <td style="text-align:center;color:#38bdf8;">{d_tot_raw['wait_avg_fmt']}</td>
        <td style="text-align:center;color:#94a3b8;font-size:11px;font-family:monospace;direction:ltr;">{d_tot_raw['wait_range_fmt']}</td>
    </tr>
    """)

    # Interactive Timeframe-Role Table: Scored by King Quality Score (KQS)
    tf_role_map = defaultdict(list)
    for r in closed:
        tf_role_map[(r.get('Timeframe', 'M1'), r.get('Role', 'Unknown'))].append(r)

    computed_tf_roles = []
    for (tf, role), t_list in tf_role_map.items():
        pm = calc_pattern_metrics(t_list, tf, role, FRICTION_04_PER_TRADE)
        is_king = (role, tf) in king_keys
        computed_tf_roles.append({
            'tf': tf, 'role': role, 'cnt': pm['cnt'],
            'w1': pm['w1'], 'w2': pm['w2'], 'w3': pm['w3'], 'w4': pm['w4'], 'sl': pm['sl'],
            'w1_p': pm['w1_p'], 'w2_p': pm['w2_p'], 'w3_p': pm['w3_p'], 'w4_p': pm['w4_p'], 'sl_p': pm['sl_p'],
            'score': pm['score'], 'is_perfect': pm['is_perfect'], 'is_runner': pm['is_runner'],
            'min_sl': pm['min_sl'], 'max_sl': pm['max_sl'], 'avg_sl': pm['avg_sl'],
            'gross': pm['gross'], 'fric': pm['fric'], 'net': pm['net'],
            'max_dd': pm['max_dd'], 'pf': pm['pf'], 'ret_dd': pm['ret_dd'],
            'is_king': is_king, 'trades': t_list
        })

    computed_tf_roles.sort(key=lambda x: (x['is_king'], x['score'], x['cnt']), reverse=True)

    tf_role_rows = []
    for idx, c in enumerate(computed_tf_roles, 1):
        k_tag = "👑 سلطان" if c['is_king'] else "سایر"
        k_color = "#facc15" if c['is_king'] else "#94a3b8"
        pnl_col = "#00e676" if c['net'] >= 0 else "#ef4444"
        badge_html = ""
        if c['is_perfect']: badge_html = " <span style='background:#064e3b;color:#34d399;font-size:10px;padding:2px 4px;border-radius:3px;'>💎 قطعی</span>"
        elif c['is_runner']: badge_html = " <span style='background:#312e81;color:#a5b4fc;font-size:10px;padding:2px 4px;border-radius:3px;'>🚀 دونده</span>"

        pf = c['pf']
        pf_str = "<span style='color:#00e676;'>MAX</span>" if pf >= 90 else f"{pf:.2f}"
        max_dd = c['max_dd']
        dd_col = "#00e676" if max_dd == 0 else ("#fbbf24" if max_dd <= 25 else "#f87171")
        dd_str = f"<span style='color:{dd_col};'>${max_dd:.1f}</span>"
        ret_dd = c['ret_dd']
        ret_str = f"{ret_dd:.1f}x" if ret_dd < 90 else "<span style='color:#00e676;'>MAX</span>"

        score = c['score']
        if score >= 600: score_html = f"<span style='color:#facc15;font-weight:bold;font-size:15px;'>{score:.1f} 👑</span>"
        elif score >= 400: score_html = f"<span style='color:#38bdf8;font-weight:bold;font-size:14px;'>{score:.1f} ⭐</span>"
        elif score > 0: score_html = f"<span style='color:#00e676;font-weight:bold;font-size:13px;'>{score:.1f}</span>"
        else: score_html = f"<span style='color:#ef4444;font-size:13px;'>{score:.1f}</span>"

        tf_role_rows.append(f"""
        <tr class="tf-row tf-role-row" data-tf="{c['tf']}" data-role="{c['role']}" data-king="{'1' if c['is_king'] else '0'}" data-cnt="{c['cnt']}" data-w1="{c['w1_p']:.2f}" data-w2="{c['w2_p']:.2f}" data-w3="{c['w3_p']:.2f}" data-w4="{c['w4_p']:.2f}" data-sl="{c['sl_p']:.2f}" data-net="{c['net']:.2f}" data-pf="{c['pf']:.2f}" data-dd="{c['max_dd']:.2f}" data-retdd="{c['ret_dd']:.2f}" data-score="{c['score']:.2f}">
            <td style="text-align:center;font-weight:bold;color:#94a3b8;">#{idx}</td>
            <td style="color:#38bdf8;font-weight:bold;text-align:center;">{c['tf']}</td>
            <td style="font-weight:bold;color:{k_color};">{c['role']}{badge_html}</td>
            <td style="text-align:center;"><span style="background:{'#854d0e' if c['is_king'] else '#1e293b'};color:{k_color};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">{k_tag}</span></td>
            <td style="text-align:center;font-weight:bold;">{c['cnt']}</td>
            <td style="text-align:center;color:#00e676;">{c['w1_p']:.1f}%</td>
            <td style="text-align:center;color:#00e676;">{c['w2_p']:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;">{c['w3_p']:.1f}%</td>
            <td style="text-align:center;color:#c084fc;">{c['w4_p']:.1f}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{c['sl_p']:.1f}%</td>
            <td style="text-align:center;font-weight:bold;color:{pnl_col};">${c['net']:+.2f}</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">{pf_str}</td>
            <td style="text-align:center;font-weight:bold;">{dd_str}</td>
            <td style="text-align:center;font-weight:bold;">{ret_str}</td>
            <td style="text-align:center;">{score_html}</td>
        </tr>
        """)

    # Loss pattern intelligence
    sl_trades = [r for r in closed if int(r.get('HitTargetRatio', 0)) == 0]
    total_losses = len(sl_trades)
    night_losses = len([r for r in sl_trades if is_night_session(r.get('EntryTime', ''))])
    single_ls_losses = len([r for r in sl_trades if is_single_ls(r.get('Role', ''))])
    toxic_losses = len([r for r in sl_trades if is_toxic_pattern(r.get('Role', ''))])
    pure_flag_losses = len([r for r in sl_trades if is_pure_flag(r.get('Role', ''))])

    # Weekly consistency
    wk_res = calc_weekly_consistency(closed, qualified_kings, FRICTION_04_PER_TRADE)
    weekly_data = wk_res['weekly_data']
    sorted_wk_keys = wk_res['sorted_wk_keys']
    total_weeks = wk_res['total_weeks']
    consistency_list = wk_res['consistency_list']
    weekly_bar_data = wk_res['weekly_bar_data']
    top_consistent_box = wk_res['top_consistent_box']
    top_consistent_pct = consistency_list[0]['cons_pct'] if consistency_list else 0.0

    weekly_consistency_rows_html = []
    for idx, c in enumerate(consistency_list, 1):
        k_tag = "👑 سلطان" if c['is_king'] else "سایر"
        k_color = "#facc15" if c['is_king'] else "#94a3b8"
        pnl_col = "#00e676" if c['net_usd'] >= 0 else "#ef4444"
        badge = "💎 افسانه‌ای" if c['cons_pct'] >= 80 else ("⭐ عالی" if c['cons_pct'] >= 70 else ("🟢 خوب" if c['cons_pct'] >= 60 else "⚠️ نوسانی"))
        badge_bg = "#064e3b" if c['cons_pct'] >= 70 else ("#1e3a8a" if c['cons_pct'] >= 60 else "#451a03")
        badge_col = "#34d399" if c['cons_pct'] >= 70 else ("#93c5fd" if c['cons_pct'] >= 60 else "#fca5a5")

        weekly_consistency_rows_html.append(f"""
        <tr style="border-bottom:1px solid #1e293b;">
            <td style="text-align:center;font-weight:bold;color:#94a3b8;">#{idx}</td>
            <td style="font-weight:bold;color:{k_color};">{c['box']}</td>
            <td style="text-align:center;"><span style="background:{'#854d0e' if c['is_king'] else '#1e293b'};color:{k_color};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">{k_tag}</span></td>
            <td style="text-align:center;font-weight:bold;">{c['trades']}</td>
            <td style="text-align:center;">{c['weeks']} هفته</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{c['green']} 🟢</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{c['red']} 🔴</td>
            <td style="text-align:center;font-weight:bold;color:#38bdf8;">{c['cons_pct']:.1f}%</td>
            <td style="text-align:center;color:#00e676;">{c['w1_pct']:.1f}%</td>
            <td style="text-align:center;color:#ef4444;">{c['sl_pct']:.1f}%</td>
            <td style="text-align:center;font-weight:bold;color:{pnl_col};">${c['net_usd']:+.2f}</td>
            <td style="text-align:center;"><span style="background:{badge_bg};color:{badge_col};padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">{badge}</span></td>
        </tr>
        """)

    weekly_timeline_rows_html = []
    weekly_details_cards_html = []
    weekly_dropdown_options = []

    tot_kings_green_wks = 0
    tot_kings_red_wks = 0
    tot_kings_6m_pnl = 0.0

    for yr, wk in sorted_wk_keys:
        w_data = weekly_data[(yr, wk)]
        t_all = w_data['trades_all']
        t_kings = w_data['trades_kings']

        k_cnt = len(t_kings)
        k_wins = len([r for r in t_kings if int(r.get('HitTargetRatio', 0)) >= 1])
        k_losses = len([r for r in t_kings if int(r.get('HitTargetRatio', 0)) == 0])
        k_wr = (k_wins / k_cnt * 100) if k_cnt else 0
        k_loss_r = (k_losses / k_cnt * 100) if k_cnt else 0
        k_pnl = sum(calc_scaleout_pnl(r, FRICTION_04_PER_TRADE) for r in t_kings)
        tot_kings_6m_pnl += k_pnl
        if k_pnl >= 0: tot_kings_green_wks += 1
        else: tot_kings_red_wks += 1

        all_cnt = len(t_all)
        all_wins = len([r for r in t_all if int(r.get('HitTargetRatio', 0)) >= 1])
        all_losses = len([r for r in t_all if int(r.get('HitTargetRatio', 0)) == 0])
        all_wr = (all_wins / all_cnt * 100) if all_cnt else 0
        all_loss_r = (all_losses / all_cnt * 100) if all_cnt else 0
        all_pnl = sum(calc_scaleout_pnl(r, FRICTION_04_PER_TRADE) for r in t_all)

        dts = [datetime.strptime(r['EntryTime'], '%Y.%m.%d %H:%M') for r in t_all]
        date_range = f"{min(dts).strftime('%Y.%m.%d')} تا {max(dts).strftime('%m.%d')}"

        best_k_name = "---"
        best_k_pnl = -999999
        for b_name, b_trades in w_data['boxes_kings'].items():
            bp = sum(calc_scaleout_pnl(r, FRICTION_04_PER_TRADE) for r in b_trades)
            if bp > best_k_pnl:
                best_k_pnl = bp
                best_k_name = f"{b_name} (+${bp:.2f})"
        if best_k_pnl == -999999 or best_k_pnl <= 0:
            best_k_name = "---"

        best_all_name = "---"
        best_all_pnl = -999999
        for b_name, b_trades in w_data['boxes_all'].items():
            bp = sum(calc_scaleout_pnl(r, FRICTION_04_PER_TRADE) for r in b_trades)
            if bp > best_all_pnl:
                best_all_pnl = bp
                best_all_name = f"{b_name} (+${bp:.2f})"

        k_stat_badge = "🟢 سبز" if k_pnl >= 0 else "🔴 قرمز"
        k_stat_col = "#00e676" if k_pnl >= 0 else "#ef4444"
        all_stat_badge = "🟢 سبز" if all_pnl >= 0 else "🔴 قرمز"
        all_stat_col = "#00e676" if all_pnl >= 0 else "#ef4444"

        weekly_timeline_rows_html.append(f"""
        <tr class="wk-row wk-row-kings" style="border-bottom:1px solid #1e293b;">
            <td style="text-align:center;font-weight:bold;color:#facc15;">هفته {wk}</td>
            <td style="text-align:center;direction:ltr;font-family:monospace;font-size:12px;color:#94a3b8;">{date_range}</td>
            <td style="text-align:center;font-weight:bold;">{k_cnt}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{k_wins}</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{k_losses}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{k_wr:.1f}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{k_loss_r:.1f}%</td>
            <td style="text-align:center;font-weight:bold;color:{k_stat_col};">${k_pnl:+.2f}</td>
            <td style="text-align:center;"><span style="color:{k_stat_col};font-weight:bold;">{k_stat_badge}</span></td>
            <td style="text-align:center;color:#facc15;font-weight:bold;">{best_k_name}</td>
            <td style="text-align:center;"><button class="sort-btn" style="padding:3px 10px;font-size:11px;" onclick="selectWeeklyDetail('wk-card-{yr}-{wk}')">👁️ کالبدشکافی باکس‌ها</button></td>
        </tr>
        <tr class="wk-row wk-row-all" style="border-bottom:1px solid #1e293b;display:none;">
            <td style="text-align:center;font-weight:bold;color:#38bdf8;">هفته {wk}</td>
            <td style="text-align:center;direction:ltr;font-family:monospace;font-size:12px;color:#94a3b8;">{date_range}</td>
            <td style="text-align:center;font-weight:bold;">{all_cnt}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{all_wins}</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{all_losses}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{all_wr:.1f}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{all_loss_r:.1f}%</td>
            <td style="text-align:center;font-weight:bold;color:{all_stat_col};">${all_pnl:+.2f}</td>
            <td style="text-align:center;"><span style="color:{all_stat_col};font-weight:bold;">{all_stat_badge}</span></td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">{best_all_name}</td>
            <td style="text-align:center;"><button class="sort-btn" style="padding:3px 10px;font-size:11px;" onclick="selectWeeklyDetail('wk-card-{yr}-{wk}')">👁️ کالبدشکافی باکس‌ها</button></td>
        </tr>
        """)

        weekly_dropdown_options.append(f'<option value="wk-card-{yr}-{wk}">هفته {wk} ({date_range}) - سود سلاطین: ${k_pnl:+.2f}</option>')

        box_rows_html = []
        sorted_boxes_this_wk = sorted(w_data['boxes_all'].items(), key=lambda x: sum(calc_scaleout_pnl(r, FRICTION_04_PER_TRADE) for r in x[1]), reverse=True)
        for b_name, b_trades in sorted_boxes_this_wk:
            b_cnt = len(b_trades)
            b_wins = len([r for r in b_trades if int(r.get('HitTargetRatio', 0)) >= 1])
            b_sl = len([r for r in b_trades if int(r.get('HitTargetRatio', 0)) == 0])
            b_wr = (b_wins / b_cnt * 100) if b_cnt else 0
            b_loss_r = (b_sl / b_cnt * 100) if b_cnt else 0
            b_pnl = sum(calc_scaleout_pnl(r, FRICTION_04_PER_TRADE) for r in b_trades)
            b_col = "#00e676" if b_pnl >= 0 else "#ef4444"

            parts = b_name.rsplit(' [', 1)
            r_name = parts[0]
            tf_name = parts[1].rstrip(']') if len(parts) > 1 else 'M1'
            is_b_king = (r_name, tf_name) in king_keys
            b_crown = "👑 " if is_b_king else ""
            b_title_col = "#facc15" if is_b_king else "#e2e8f0"

            box_rows_html.append(f"""
            <tr style="border-bottom:1px solid #334155;">
                <td style="color:{b_title_col};font-weight:bold;">{b_crown}{b_name}</td>
                <td style="text-align:center;font-weight:bold;">{b_cnt}</td>
                <td style="text-align:center;color:#00e676;font-weight:bold;">{b_wins}</td>
                <td style="text-align:center;color:#ef4444;font-weight:bold;">{b_sl}</td>
                <td style="text-align:center;color:#00e676;font-weight:bold;">{b_wr:.1f}%</td>
                <td style="text-align:center;color:#ef4444;font-weight:bold;">{b_loss_r:.1f}%</td>
                <td style="text-align:center;color:{b_col};font-weight:bold;">${b_pnl:+.2f}</td>
            </tr>
            """)

        weekly_details_cards_html.append(f"""
        <div id="wk-card-{yr}-{wk}" class="week-detail-card" style="display:none;background:#1e293b;border:1px solid #38bdf8;border-radius:10px;padding:16px;margin-top:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #334155;padding-bottom:10px;margin-bottom:12px;flex-wrap:wrap;gap:10px;">
                <h4 style="margin:0;color:#38bdf8;font-size:16px;">🔍 کالبدشکافی کامل تمام باکس‌های هفته {wk} ({date_range})</h4>
                <div style="font-size:13px;color:#facc15;font-weight:bold;">سود دلاری سلاطین در این هفته: <span style="color:{k_stat_col};font-size:15px;">${k_pnl:+.2f}</span></div>
            </div>
            <div style="overflow-x:auto;">
                <table style="width:100%;font-size:13px;">
                    <thead>
                        <tr style="background:#0f172a;color:#94a3b8;">
                            <th>نام ساختار / باکس</th>
                            <th style="text-align:center;">تعداد معامله</th>
                            <th style="text-align:center;">برد (تاچ TP)</th>
                            <th style="text-align:center;">باخت (SL)</th>
                            <th style="text-align:center;">وین‌ریت %</th>
                            <th style="text-align:center;">درصد استاپ %</th>
                            <th style="text-align:center;">سود خالص دلاری ($)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(box_rows_html)}
                    </tbody>
                </table>
            </div>
        </div>
        """)

    # Multi-period consistency
    mp_res = calc_multi_period_consistency(closed, qualified_kings, base_yr, FRICTION_04_PER_TRADE)
    period_configs = mp_res['period_configs']
    mp_period_data = mp_res['mp_period_data']
    mp_intersection_list = mp_res['mp_intersection_list']
    inter_map = mp_res['inter_map']
    master_map = mp_res['master_map']

    # Chronological equity curve
    sorted_closed = sorted(closed, key=lambda x: x.get('ExitTime', x.get('EntryTime', '')))
    bal_initial = 100.0
    bal_k = bal_initial
    bal_a = bal_initial
    peak_k = bal_initial
    max_dd_k = 0.0
    peak_a = bal_initial
    max_dd_a = 0.0

    t_init = date_start_str if date_start_str and date_start_str != 'N/A' else '2025.01.01 00:00'
    pts_kings = [{'idx': 0, 't': t_init, 'b': round(bal_k, 2), 'p': 0.0, 'n': 'موجودی اولیه (Initial Balance)', 'peak': round(bal_k, 2), 'dd': 0.0, 'ddPct': 0.0}]
    pts_all = [{'idx': 0, 't': t_init, 'b': round(bal_a, 2), 'p': 0.0, 'n': 'موجودی اولیه (Initial Balance)', 'peak': round(bal_a, 2), 'dd': 0.0, 'ddPct': 0.0}]

    active_open_kings = []
    active_open_all = []
    for r in sorted_closed:
        pnl = calc_scaleout_pnl(r, FRICTION_04_PER_TRADE)
        et = r.get('EntryTime', '')
        xt = r.get('ExitTime', et)
        if not xt or xt <= et:
            xt = et + "z"
        role = r.get('Role', '')
        tf = r.get('Timeframe', '')
        b_name = f"{role} [{tf}]"

        # All
        bal_a += pnl
        if bal_a > peak_a: peak_a = bal_a
        dd_a = peak_a - bal_a
        if dd_a > max_dd_a: max_dd_a = dd_a
        ddPct_a = (dd_a / peak_a * 100.0) if peak_a > 0 else 0.0
        active_open_all = [x for x in active_open_all if x > et]
        active_open_all.append(xt)
        c_all = len(active_open_all)
        pts_all.append({'idx': len(pts_all), 't': et, 'b': round(bal_a, 2), 'p': round(pnl, 2), 'n': b_name, 'peak': round(peak_a, 2), 'dd': round(dd_a, 2), 'ddPct': round(ddPct_a, 1), 'concurrent': c_all})

        # Kings
        if (role, tf) in king_keys:
            bal_k += pnl
            if bal_k > peak_k: peak_k = bal_k
            dd_k = peak_k - bal_k
            if dd_k > max_dd_k: max_dd_k = dd_k
            ddPct_k = (dd_k / peak_k * 100.0) if peak_k > 0 else 0.0
            active_open_kings = [x for x in active_open_kings if x > et]
            active_open_kings.append(xt)
            c_k = len(active_open_kings)
            pts_kings.append({'idx': len(pts_kings), 't': et, 'b': round(bal_k, 2), 'p': round(pnl, 2), 'n': b_name, 'peak': round(peak_k, 2), 'dd': round(dd_k, 2), 'ddPct': round(ddPct_k, 1), 'concurrent': c_k})

    net_k = bal_k - bal_initial
    net_k_pct = (net_k / bal_initial * 100.0) if bal_initial > 0 else 0.0
    max_dd_k_pct = (max_dd_k / peak_k * 100.0) if peak_k > 0 else 0.0
    net_a = bal_a - bal_initial
    net_a_pct = (net_a / bal_initial * 100.0) if bal_initial > 0 else 0.0
    max_dd_a_pct = (max_dd_a / peak_a * 100.0) if peak_a > 0 else 0.0
    avg_trade_k = (net_k / tot_k_cnt) if tot_k_cnt > 0 else 0.0

    # Simulator Kings Data Preparation
    kings_sim_list = []
    for i, k in enumerate(qualified_kings, 1):
        sl_count = k['sl']
        sl_trades = [r for r in k['trades'] if int(r.get('HitTargetRatio', 0)) == 0]
        sl_dollar = round(sum(float(r.get('RiskPoints', 0.0)) * 0.04 + FRICTION_04_PER_TRADE for r in sl_trades), 2)
        kings_sim_list.append({
            'id': i,
            'role': k['role'],
            'tf': k['tf'],
            'kk': f"{k['role']}|{k['tf']}",
            'score': round(k['score'], 1),
            'cnt': k['cnt'],
            'net': round(k['net'], 2),
            'gross': round(k.get('gross', 0.0), 2),
            'fric': round(k.get('fric', 0.0), 2),
            'w1_p': round(k['w1_p'], 1),
            'w2_p': round(k.get('w2_p', 0.0), 1),
            'w3_p': round(k.get('w3_p', 0.0), 1),
            'w4_p': round(k.get('w4_p', 0.0), 1),
            'sl_cnt': sl_count,
            'sl_usd': sl_dollar,
            'sl_p': round(k['sl_p'], 1),
            'pf': round(k['pf'], 2) if k['pf'] < 900 else 999.0,
            'max_dd': round(k.get('max_dd', 0.0), 2),
            'ret_dd': round(k.get('ret_dd', 0.0), 1),
            'perf': 1 if k['is_perfect'] else 0,
            'run': 1 if k['is_runner'] else 0
        })

    sorted_by_sl_cnt = sorted(kings_sim_list, key=lambda x: (x['sl_cnt'], x['sl_usd']), reverse=True)
    sorted_by_sl_usd = sorted(kings_sim_list, key=lambda x: (x['sl_usd'], x['sl_cnt']), reverse=True)
    sorted_by_sl_pct = sorted([x for x in kings_sim_list if x['cnt'] >= 10], key=lambda x: (x['sl_p'], x['sl_cnt']), reverse=True)

    top3_sl_cnt_keys = [x['kk'] for x in sorted_by_sl_cnt[:3]]
    top3_sl_usd_keys = [x['kk'] for x in sorted_by_sl_usd[:3]]
    top5_sl_usd_keys = [x['kk'] for x in sorted_by_sl_usd[:5]]
    top3_sl_pct_keys = [x['kk'] for x in sorted_by_sl_pct[:3]]

    for k in kings_sim_list:
        k['is_top_sl_cnt'] = 1 if k['kk'] in top3_sl_cnt_keys else 0
        k['is_top_sl_usd'] = 1 if k['kk'] in top3_sl_usd_keys else 0
        k['is_top_sl_pct'] = 1 if k['kk'] in top3_sl_pct_keys else 0
        k['is_danger'] = 1 if (k['is_top_sl_cnt'] or k['is_top_sl_usd'] or k['sl_cnt'] >= 45 or k['sl_p'] >= 45.0) else 0

    # Chronological Trades for Simulator
    trades_chrono = sorted([r for r in closed if r.get('Timeframe') in ['M1','M5','M15']], key=lambda x: x.get('EntryTime', ''))
    trades_sim_list = []
    for idx, r in enumerate(trades_chrono, 1):
        tf = r.get('Timeframe', 'M1')
        role = r.get('Role', '')
        is_k = 1 if (role, tf) in king_keys else 0
        hr = int(r.get('HitTargetRatio', 0))
        pts = float(r.get('RiskPoints', 0.0))
        if hr == 0:
            pnl = -pts * 0.04 - FRICTION_04_PER_TRADE
        else:
            pnl = -FRICTION_04_PER_TRADE
            if hr >= 1: pnl += pts * 1.0 * 0.01
            if hr >= 2: pnl += pts * 2.0 * 0.01
            if hr >= 3: pnl += pts * 3.0 * 0.01
            if hr >= 4: pnl += pts * 4.0 * 0.01

        et = r.get('EntryTime', '')
        xt = r.get('ExitTime', et)
        h_val = int(et[11:13]) if len(et) >= 13 else 0
        trades_sim_list.append({
            'i': idx,
            't': et,
            'xt': xt,
            'h': h_val,
            'tf': tf,
            'r': role,
            'k': is_k,
            'kk': f"{role}|{tf}",
            'pts': round(pts, 1),
            'pot': round(pts * 0.04, 2),
            'hr': hr,
            'p': round(pnl, 2),
            'ex_p': round(float(r.get('ExitPrice', 0.0)), 5)
        })

    active_open_intervals = []
    concurrent_counts = []
    for t_item in trades_sim_list:
        if t_item['k'] == 1:
            en_str = t_item['t']
            ex_str = t_item['xt']
            if not ex_str or ex_str <= en_str:
                ex_str = en_str + "z"
            active_open_intervals = [x for x in active_open_intervals if x > en_str]
            active_open_intervals.append(ex_str)
            concurrent_counts.append(len(active_open_intervals))
    init_max_concurrent = max(concurrent_counts) if concurrent_counts else 0
    init_avg_concurrent = (sum(concurrent_counts) / len(concurrent_counts)) if concurrent_counts else 0.0

    # Optimize smart presets
    smart_presets_defs, smart_presets_json_data = optimize_smart_presets(trades_sim_list, kings_sim_list, len(closed))

    # Trades Journal JSON Data
    trades_sorted = sorted([r for r in closed if r.get('Timeframe') in ['M1','M5','M15']], key=lambda x: x.get('EntryTime', ''), reverse=True)
    trades_json_list = []
    for idx, r in enumerate(trades_sorted, 1):
        tf = r.get('Timeframe', 'M1')
        role = r.get('Role', '')
        is_k = 1 if (role, tf) in king_keys else 0
        hr = int(r.get('HitTargetRatio', 0))
        pts = float(r.get('RiskPoints', 0.0))
        if hr == 0:
            pnl = -pts * 0.04 - FRICTION_04_PER_TRADE
        else:
            pnl = -FRICTION_04_PER_TRADE
            if hr >= 1: pnl += pts * 1.0 * 0.01
            if hr >= 2: pnl += pts * 2.0 * 0.01
            if hr >= 3: pnl += pts * 3.0 * 0.01
            if hr >= 4: pnl += pts * 4.0 * 0.01

        wm = get_box_wait_time_minutes(r)
        trades_json_list.append({
            'id': idx,
            'box_t': r.get('BoxTimeStart', ''),
            'en_t': r.get('EntryTime', ''),
            'ex_t': r.get('ExitTime', ''),
            'wait_m': round(wm, 1) if wm is not None else 0.0,
            'wait_fmt': format_duration_persian(wm) if wm is not None else '-',
            'wait_short': format_duration_short(wm) if wm is not None else '-',
            'tf': tf,
            'role': role,
            'bname': r.get('BoxName', ''),
            'is_k': is_k,
            'dir': r.get('Direction', 'BUY'),
            'en_p': round(float(r.get('EntryPrice', 0.0)), 5),
            'ex_p': round(float(r.get('ExitPrice', 0.0)), 5),
            'sl': round(float(r.get('StopLoss', 0.0)), 5),
            'pts': round(pts, 1),
            'tp1': round(float(r.get('TP1', 0.0)), 5),
            'tp2': round(float(r.get('TP2', 0.0)), 5),
            'tp3': round(float(r.get('TP3', 0.0)), 5),
            'tp4': round(float(r.get('TP4', 0.0)), 5),
            't1': 1 if hr >= 1 else 0,
            't2': 1 if hr >= 2 else 0,
            't3': 1 if hr >= 3 else 0,
            't4': 1 if hr >= 4 else 0,
            'mfe_r': round(float(r.get('MFE_R', 0.0)), 2),
            'mae_r': round(float(r.get('MAE_R', 0.0)), 2),
            'hr': hr,
            'pnl': round(pnl, 2),
            'net': round(pnl, 2)
        })

    return {
        'symbol': symbol,
        'clean_symbol': clean_symbol,
        'csv_file': csv_file,
        'min_date': min_date,
        'max_date': max_date,
        'tfs_str': tfs_str,
        'date_start_str': date_start_str,
        'date_end_str': date_end_str,
        'bal_initial': bal_initial,
        'net_k': net_k,
        'net_k_pct': net_k_pct,
        'bal_k': bal_k,
        'peak_k': peak_k,
        'max_dd_k': max_dd_k,
        'max_dd_k_pct': max_dd_k_pct,
        's3_pf': s3_pf,
        's3_net': s3_net,
        'tot_k_cnt': tot_k_cnt,
        'total_setups': total_setups,
        'closed_count': len(closed),
        'pending': len(pending),
        'in_trade_count': len(in_trade),
        'sl_in_rej': sl_in_rej,
        'rej_accuracy': rej_accuracy,
        'ev_a': ev_a,
        'ev_b': ev_b,
        'w1_p': d_tot_kings['w1_p'],
        'kings_sim_list': kings_sim_list,
        'top3_sl_cnt_keys': top3_sl_cnt_keys,
        'top3_sl_usd_keys': top3_sl_usd_keys,
        'top5_sl_usd_keys': top5_sl_usd_keys,
        'top3_sl_pct_keys': top3_sl_pct_keys,
        'trades_sim_list': trades_sim_list,
        'smart_presets': smart_presets_json_data,
        'weekly_bar_data': weekly_bar_data,
        'trades_json_list': trades_json_list,
        'latency_all': symbol_latency_all,
        'latency_kings': symbol_latency_kings,
        'latency_tfs': symbol_latency_tfs,
        'mp_intersection_list': mp_intersection_list
    }
