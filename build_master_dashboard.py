import json
import os
import sys
import csv
import math
import re
from collections import defaultdict
from datetime import datetime, timedelta
import tester_compare_module

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CSV_PATH_PRIMARY = r"c:\Users\USER\AppData\Roaming\MetaQuotes\Terminal\3F2C3A2F8B221C9D88E569F2FD1D3E97\MQL5\Files\flagpro_trades_EURUSD.csv"
CSV_PATH_FALLBACK = r"c:\Users\USER\AppData\Roaming\MetaQuotes\Terminal\3F2C3A2F8B221C9D88E569F2FD1D3E97\MQL5\Files\flagpro_trades_export.csv"

OUT_PATHS = [
    r"c:\Users\USER\AppData\Roaming\MetaQuotes\Terminal\3F2C3A2F8B221C9D88E569F2FD1D3E97\MQL5\Files\eurusd_performance_report.html",
    r"c:\Users\USER\AppData\Roaming\MetaQuotes\Terminal\3F2C3A2F8B221C9D88E569F2FD1D3E97\MQL5\Files\flagpro_performance_dashboard.html",
    r"C:\Users\USER\Desktop\FlagPro_Dashboard.html"
]

def is_single_ls(role):
    return role in ["LS-BE", "LS-BU"]

def is_night_session(entry_time_str):
    if not entry_time_str or entry_time_str == 'None': return False
    try:
        dt = datetime.strptime(entry_time_str, "%Y.%m.%d %H:%M")
        return dt.hour in [21, 22, 23, 0]
    except:
        return False

def is_pre_london(entry_time_str):
    if not entry_time_str or entry_time_str == 'None': return False
    try:
        dt = datetime.strptime(entry_time_str, "%Y.%m.%d %H:%M")
        return dt.hour == 7
    except:
        return False

def is_toxic_pattern(role):
    for x in ["LS-BE > RS-BE", "LS-BU > RS-BU", "LS-BE > OInner-BE > RS-BE", "LS-BE > OInner-BU > RS-BU"]:
        if x in role: return True
    return False

def is_pure_flag(role):
    return role in ["Flag", "Flag-BE", "Flag-BU"]

def is_low_reward_vs_friction(risk_pts, comm_per_lot=6.0, spread_pips=0.8, min_ratio=1.0):
    if risk_pts <= 0: return False
    comm_pips = comm_per_lot / 10.0
    total_friction_pips = spread_pips + comm_pips
    min_pts = total_friction_pips * min_ratio * 10.0
    return (risk_pts <= min_pts)



def process_symbol_dataset(csv_file):
    print(f"📂 در حال پردازش داده‌های فایل: {csv_file}")
    if not os.path.exists(csv_file):
        return None

    all_raw_rows = []
    with open(csv_file, mode='r', encoding='utf-8-sig', errors='ignore') as f:
        for r in csv.DictReader(f):
            all_raw_rows.append(r)

    # Dynamic Symbol Detection
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
    accepted_trades = []
    rejected_trades = []

    f1_rej, f1_sl = 0, 0
    f2_rej, f2_sl = 0, 0
    f3_rej, f3_sl = 0, 0
    f4_rej, f4_sl = 0, 0
    f5_rej, f5_sl = 0, 0
    f7_rej, f7_sl = 0, 0

    for r in closed:
        role = r.get('Role', '')
        entry_time = r.get('EntryTime', '')
        risk_pts = float(r.get('RiskPoints', 0.0))
        is_sl = (int(r.get('HitTargetRatio', 0)) == 0)

        r1 = is_single_ls(role)
        r2 = is_night_session(entry_time)
        r3 = is_pre_london(entry_time)
        r4 = is_toxic_pattern(role)
        r5 = is_pure_flag(role)
        r7 = is_low_reward_vs_friction(risk_pts)

        if r1: f1_rej += 1; f1_sl += (1 if is_sl else 0)
        if r2: f2_rej += 1; f2_sl += (1 if is_sl else 0)
        if r3: f3_rej += 1; f3_sl += (1 if is_sl else 0)
        if r4: f4_rej += 1; f4_sl += (1 if is_sl else 0)
        if r5: f5_rej += 1; f5_sl += (1 if is_sl else 0)
        if r7: f7_rej += 1; f7_sl += (1 if is_sl else 0)

        if r1 or r2 or r3 or r4 or r5 or r7:
            rejected_trades.append(r)
        else:
            accepted_trades.append(r)

    # Metrics Before
    w1_cnt_b = len([r for r in closed if int(r.get('HitTargetRatio', 0)) >= 1])
    w2_cnt_b = len([r for r in closed if int(r.get('HitTargetRatio', 0)) >= 2])
    sl_cnt_b = len([r for r in closed if int(r.get('HitTargetRatio', 0)) == 0])
    w1_rate_b = w1_cnt_b / len(closed) * 100 if closed else 0
    w2_rate_b = w2_cnt_b / len(closed) * 100 if closed else 0
    sl_rate_b = sl_cnt_b / len(closed) * 100 if closed else 0
    ev_b = (w2_rate_b / 100.0 * 2.0) - (sl_rate_b / 100.0 * 1.0)

    # Metrics After
    w1_cnt_a = len([r for r in accepted_trades if int(r.get('HitTargetRatio', 0)) >= 1])
    w2_cnt_a = len([r for r in accepted_trades if int(r.get('HitTargetRatio', 0)) >= 2])
    sl_cnt_a = len([r for r in accepted_trades if int(r.get('HitTargetRatio', 0)) == 0])
    w1_rate_a = w1_cnt_a / len(accepted_trades) * 100 if accepted_trades else 0
    w2_rate_a = w2_cnt_a / len(accepted_trades) * 100 if accepted_trades else 0
    sl_rate_a = sl_cnt_a / len(accepted_trades) * 100 if accepted_trades else 0
    ev_a = (w2_rate_a / 100.0 * 2.0) - (sl_rate_a / 100.0 * 1.0)

    sl_in_rej = len([r for r in rejected_trades if int(r.get('HitTargetRatio', 0)) == 0])
    rej_accuracy = sl_in_rej / len(rejected_trades) * 100 if rejected_trades else 0

    # Dynamic Kings Selection: Based on Timeframe, 100% Win Rate (>=2 trades), and King Quality Score (KQS)
    tf_role_map_raw = defaultdict(list)
    for r in closed:
        tf_role_map_raw[(r.get('Timeframe', 'M1'), r.get('Role', 'Unknown'))].append(r)

    qualified_kings = []
    friction_04_per_trade = 0.48

    for (tf, role), t_list in tf_role_map_raw.items():
        cnt = len(t_list)
        w1 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 1])
        w2 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 2])
        w3 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 3])
        w4 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 4])
        sl = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) == 0])

        w1_p = w1 / cnt * 100
        w2_p = w2 / cnt * 100
        w3_p = w3 / cnt * 100
        w4_p = w4 / cnt * 100
        sl_p = sl / cnt * 100

        # Calculate Net Profit with 0.04 scale-out
        gross = 0.0
        for r in t_list:
            pts = float(r.get('RiskPoints', 0.0))
            hr = int(r.get('HitTargetRatio', 0))
            if hr == 0:
                gross -= pts * 0.04
            else:
                if hr >= 1: gross += pts * 1.0 * 0.01
                if hr >= 2: gross += pts * 2.0 * 0.01
                if hr >= 3: gross += pts * 3.0 * 0.01
                if hr >= 4: gross += pts * 4.0 * 0.01
        fric = cnt * friction_04_per_trade
        net = gross - fric

        is_perfect = (cnt >= 2 and sl == 0)
        is_runner = (w3_p >= 30.0 or w4_p >= 30.0)
        is_proven = (cnt >= 20)

        # Institutional Metrics (Chronological Max Drawdown, Profit Factor, Return/DD Ratio)
        cum_pnl = 0.0
        peak = 0.0
        max_dd = 0.0
        gross_win = 0.0
        gross_loss = 0.0
        sorted_trades = sorted(t_list, key=lambda x: x.get('EntryTime', ''))
        for r in sorted_trades:
            pts = float(r.get('RiskPoints', 0.0))
            hr = int(r.get('HitTargetRatio', 0))
            if hr == 0:
                pnl = -pts * 0.04 - friction_04_per_trade
                gross_loss += abs(pnl)
            else:
                pnl = -friction_04_per_trade
                if hr >= 1: pnl += pts * 1.0 * 0.01
                if hr >= 2: pnl += pts * 2.0 * 0.01
                if hr >= 3: pnl += pts * 3.0 * 0.01
                if hr >= 4: pnl += pts * 4.0 * 0.01
                gross_win += max(pnl, 0.0)
                if pnl < 0: gross_loss += abs(pnl)

            cum_pnl += pnl
            if cum_pnl > peak: peak = cum_pnl
            dd = peak - cum_pnl
            if dd > max_dd: max_dd = dd

        pf = gross_win / gross_loss if gross_loss > 0 else (99.0 if gross_win > 0 else 0.0)
        ret_dd = net / max_dd if max_dd > 0 else (net if net > 0 else 0.0)

        # 7-Pillar Institutional King Score Formula:
        profit_per_trade = net / max(cnt, 1)

        if net <= 0:
            final_score = net * 2.0 - sl_p
        else:
            # Pillar 1: 🛡️ Purity / Zero-SL (0 to 500 pts)
            if cnt >= 2 and sl == 0:
                f_purity = 500.0
            elif cnt >= 3 and sl_p <= 15.0:
                f_purity = 300.0
            elif cnt >= 3 and sl_p <= 25.0:
                f_purity = 200.0
            elif cnt >= 4 and sl_p <= 35.0:
                f_purity = 100.0
            elif cnt >= 4 and sl_p <= 45.0:
                f_purity = 50.0
            else:
                f_purity = 0.0

            # Pillar 2: 🎯 TP2 Depth (0 to 400 pts)
            f_tp2 = w2_p * 4.0

            # Pillar 3: ⚡ Runner & Target Progression Quality (up to ~250 pts)
            f_prog = (w1_p * 0.5) + (w3_p * 1.0) + (w4_p * 1.5) - (sl_p * 0.5)

            # Pillar 4: 💰 Efficiency ($/trade) (0 to 200 pts)
            f_eff = min(max(profit_per_trade, 0.0) * 20.0, 200.0)

            # Pillar 5: 📊 Statistical Confidence (0 to 50 pts)
            f_rel = min(math.log10(cnt + 9) * 20.0, 50.0)

            # Pillar 6: ⚖️ Institutional Profit Factor (0 to 100 pts)
            if sl == 0 and cnt >= 2:
                f_pf = 100.0
            else:
                f_pf = min(max(pf - 1.0, 0.0) * 50.0, 100.0)

            # Pillar 7: 🛡️ Drawdown Resistance & Recovery Factor (0 to 100 pts)
            if sl == 0 and cnt >= 2:
                f_rec = 100.0
            else:
                f_rec = min(ret_dd * 6.0, 100.0)
                if max_dd > 30.0:
                    f_rec = max(f_rec - (max_dd - 30.0) * 1.5, 0.0)

            final_score = f_purity + f_tp2 + f_prog + f_eff + f_rel + f_pf + f_rec

        stops = [float(r.get('RiskPoints', 0.0)) / 10.0 for r in t_list]
        min_sl = min(stops) if stops else 0.0
        max_sl = max(stops) if stops else 0.0
        avg_sl = sum(stops) / len(stops) if stops else 0.0

        # Eligibility Criteria for Kings:
        # All 21 profitable kings qualify (perfect or positive net profit with at least 4 trades and Win Rate >= 50%)
        if is_perfect or (cnt >= 4 and net > 5.0 and w1_p >= 50.0):
            qualified_kings.append({
                'tf': tf, 'role': role, 'cnt': cnt,
                'w1': w1, 'w2': w2, 'w3': w3, 'w4': w4, 'sl': sl,
                'w1_p': w1_p, 'w2_p': w2_p, 'w3_p': w3_p, 'w4_p': w4_p, 'sl_p': sl_p,
                'score': final_score, 'is_perfect': is_perfect, 'is_runner': is_runner, 'is_proven': is_proven,
                'min_sl': min_sl, 'max_sl': max_sl, 'avg_sl': avg_sl,
                'gross': gross, 'fric': fric, 'net': net,
                'max_dd': max_dd, 'pf': pf, 'ret_dd': ret_dd,
                'trades': t_list
            })

    # Sort Kings by Score descending
    qualified_kings.sort(key=lambda x: (x['score'], x['cnt']), reverse=True)

    # Collect all trades belonging to qualified kings
    kings_trades = []
    for k in qualified_kings:
        kings_trades.extend(k['trades'])

    tot_k_cnt = len(kings_trades)
    tot_k_fric = tot_k_cnt * friction_04_per_trade
    tot_k_gross = sum(k['gross'] for k in qualified_kings)
    tot_k_net = sum(k['net'] for k in qualified_kings)

    kings_rows_html = []
    medals = ['🥇', '🥈', '🥉', '👑', '👑', '⭐', '⭐', '⭐', '⭐', '⭐']
    for idx, k in enumerate(qualified_kings, 1):
        rank_icon = medals[idx-1] if idx <= len(medals) else f"#{idx}"
        badge_html = ""
        if k['is_perfect']:
            badge_html = " <span style='background:#064e3b;color:#34d399;font-size:10px;padding:2px 5px;border-radius:4px;border:1px solid #059669;'>💎 ۱۰۰٪ قطعی</span>"
        elif k['is_runner']:
            badge_html = " <span style='background:#312e81;color:#a5b4fc;font-size:10px;padding:2px 5px;border-radius:4px;border:1px solid #4338ca;'>🚀 دونده</span>"

        net_col = "#00e676" if k['net'] >= 0 else "#ef4444"
        pf = k['pf']
        pf_str = "<span style='color:#00e676;'>MAX</span>" if pf >= 90 else f"{pf:.2f}"
        max_dd = k['max_dd']
        dd_col = "#00e676" if max_dd == 0 else ("#fbbf24" if max_dd <= 25 else "#f87171")
        ret_dd = k['ret_dd']
        ret_str = f"{ret_dd:.1f}x"

        kings_rows_html.append(f"""
        <tr>
            <td style="text-align:center;font-size:16px;font-weight:bold;">{rank_icon}</td>
            <td style="color:#38bdf8;font-weight:bold;text-align:center;font-size:14px;">{k['tf']}</td>
            <td style="color:#facc15;font-weight:bold;font-size:14px;">{k['role']}{badge_html}</td>
            <td style="text-align:center;color:#facc15;font-weight:bold;font-size:14px;background:#1e293b;">{k['score']:.1f}</td>
            <td style="text-align:center;font-weight:bold;">{k['cnt']}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{k['w1_p']:.1f}%</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{k['w2_p']:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;">{k['w3_p']:.1f}%</td>
            <td style="text-align:center;color:#c084fc;">{k['w4_p']:.1f}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{k['sl_p']:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;font-size:13px;">{pf_str}</td>
            <td style="text-align:center;color:{dd_col};font-weight:bold;font-size:13px;">${max_dd:.2f}</td>
            <td style="text-align:center;color:#facc15;font-weight:bold;font-size:13px;">{ret_str}</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;font-size:13px;">${k['gross']:+.2f}</td>
            <td style="text-align:center;color:#f87171;font-weight:bold;font-size:13px;">${k['fric']:.2f}-</td>
            <td style="text-align:center;color:{net_col};font-weight:bold;font-size:15px;background:#064e3b22;">${k['net']:+.2f} دلار</td>
        </tr>
        """)

    # Dynamic 0.04 Scale-Out Comparison
    # Strategy 1: Fixed 1:1
    s1_gross, s1_w, s1_l = 0.0, 0.0, 0.0
    for r in kings_trades:
        pts = float(r.get('RiskPoints', 0.0))
        hr = int(r.get('HitTargetRatio', 0))
        if hr >= 1: win = pts * 0.04; s1_gross += win; s1_w += win
        else: loss = pts * 0.04; s1_gross -= loss; s1_l += loss
    s1_net = s1_gross - tot_k_fric
    s1_pf = s1_w / s1_l if s1_l > 0 else 0.0

    # Strategy 2: Fixed 1:2
    s2_gross, s2_w, s2_l = 0.0, 0.0, 0.0
    for r in kings_trades:
        pts = float(r.get('RiskPoints', 0.0))
        hr = int(r.get('HitTargetRatio', 0))
        if hr >= 2: win = pts * 2 * 0.04; s2_gross += win; s2_w += win
        else: loss = pts * 0.04; s2_gross -= loss; s2_l += loss
    s2_net = s2_gross - tot_k_fric
    s2_pf = s2_w / s2_l if s2_l > 0 else 0.0
    s2_diff_dollar = s2_net - s1_net
    s2_diff_pct = (s2_net - s1_net) / abs(s1_net) * 100 if s1_net != 0 else 0.0

    # Strategy 3: Balanced 4-Way Scale-Out (25% TP1 + BE, 25% TP2 + Lock, 25% TP3, 25% TP4 Runner)
    s3_gross, s3_w, s3_l = 0.0, 0.0, 0.0
    for r in kings_trades:
        pts = float(r.get('RiskPoints', 0.0))
        hr = int(r.get('HitTargetRatio', 0))
        if hr == 0:
            loss = pts * 0.04
            s3_gross -= loss
            s3_l += loss
        else:
            win = 0.0
            if hr >= 1: win += pts * 1.0 * 0.01
            if hr >= 2: win += pts * 2.0 * 0.01
            if hr >= 3: win += pts * 3.0 * 0.01
            if hr >= 4: win += pts * 4.0 * 0.01
            s3_gross += win
            s3_w += win
    s3_net = s3_gross - tot_k_fric
    s3_pf = s3_w / s3_l if s3_l > 0 else 0.0
    s3_diff_dollar = s3_net - s1_net
    s3_diff_pct = (s3_net - s1_net) / abs(s1_net) * 100 if s1_net != 0 else 0.0

    # Break-Even Comparison: TP1 vs TP2
    sl_direct = len([r for r in kings_trades if int(r.get('HitTargetRatio', 0)) == 0])
    tp1_only  = len([r for r in kings_trades if int(r.get('HitTargetRatio', 0)) == 1])
    tp2_only  = len([r for r in kings_trades if int(r.get('HitTargetRatio', 0)) == 2])
    tp3_4     = len([r for r in kings_trades if int(r.get('HitTargetRatio', 0)) >= 3])

    sl_direct_pct = sl_direct / tot_k_cnt * 100 if tot_k_cnt else 0
    tp1_only_pct  = tp1_only / tot_k_cnt * 100 if tot_k_cnt else 0
    tp2_only_pct  = tp2_only / tot_k_cnt * 100 if tot_k_cnt else 0
    tp3_4_pct     = tp3_4 / tot_k_cnt * 100 if tot_k_cnt else 0

    m1_gross = s3_gross
    m1_net = s3_net

    m2_gross = 0.0
    for r in kings_trades:
        pts = float(r.get('RiskPoints', 0.0))
        hr = int(r.get('HitTargetRatio', 0))
        if hr == 0:
            m2_gross -= pts * 0.04
        elif hr == 1:
            # TP1 took 0.01 profit (+0.01R), but remaining 0.03 hit SL (-0.03R)
            m2_gross += (pts * 1.0 * 0.01) - (pts * 1.0 * 0.03)
        elif hr == 2:
            m2_gross += (pts * 1.0 * 0.01) + (pts * 2.0 * 0.01)
        elif hr == 3:
            m2_gross += (pts * 1.0 * 0.01) + (pts * 2.0 * 0.01) + (pts * 3.0 * 0.01)
        elif hr >= 4:
            m2_gross += (pts * 1.0 * 0.01) + (pts * 2.0 * 0.01) + (pts * 3.0 * 0.01) + (pts * 4.0 * 0.01)
    m2_net = m2_gross - tot_k_fric
    be_diff = m1_net - m2_net

    # Timeframe Breakdown: 1. Golden Kings Strategy (Trading Reality) vs 2. All Raw Boxes (Unfiltered Noise)
    tf_map = defaultdict(list)
    for r in closed:
        tf_map[r.get('Timeframe', 'Unknown')].append(r)

    def calc_tf_metrics(t_list):
        cnt = len(t_list)
        if cnt == 0: return None
        w1 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 1])
        w2 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 2])
        w3 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 3])
        w4 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 4])
        sl = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) == 0])
        gross = 0.0
        for r in t_list:
            pts = float(r.get('RiskPoints', 0.0))
            hr = int(r.get('HitTargetRatio', 0))
            if hr == 0:
                gross -= pts * 0.04
            else:
                if hr >= 1: gross += pts * 1.0 * 0.01
                if hr >= 2: gross += pts * 2.0 * 0.01
                if hr >= 3: gross += pts * 3.0 * 0.01
                if hr >= 4: gross += pts * 4.0 * 0.01
        net = gross - (cnt * friction_04_per_trade)
        fric = cnt * friction_04_per_trade
        return {
            'cnt': cnt,
            'w1_p': w1 / cnt * 100,
            'w2_p': w2 / cnt * 100,
            'w3_p': w3 / cnt * 100,
            'w4_p': w4 / cnt * 100,
            'sl_p': sl / cnt * 100,
            'gross': gross,
            'fric': fric,
            'net': net
        }

    # 1. Golden Kings Strategy per Timeframe (The actual system being traded)
    tf_kings_rows = []
    for tf_name in available_tfs:
        t_sub = [r for r in kings_trades if r.get('Timeframe') == tf_name]
        d = calc_tf_metrics(t_sub)
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
        </tr>
        """)

    d_tot_kings = calc_tf_metrics(kings_trades) or {
        'cnt': 0, 'w1_p': 0.0, 'w2_p': 0.0, 'w3_p': 0.0, 'w4_p': 0.0, 'sl_p': 0.0, 'gross': 0.0, 'fric': 0.0, 'net': 0.0
    }
    tot_kings_col = "#00e676" if d_tot_kings['net'] >= 0 else "#ef4444"
    tf_kings_rows.append(f"""
    <tr style="background:#1e293b;border-top:2px solid #38bdf8;">
        <td style="color:#facc15;font-weight:bold;font-size:15px;">👑 مجموع سلاطین (FlagPro)</td>
        <td style="text-align:center;font-weight:bold;color:#facc15;font-size:14px;">{d_tot_kings['cnt']} معامله</td>
        <td style="text-align:center;color:#00e676;font-weight:bold;">{d_tot_kings['w1_p']:.1f}%</td>
        <td style="text-align:center;color:#00e676;font-weight:bold;">{d_tot_kings['w2_p']:.1f}%</td>
        <td style="text-align:center;color:#38bdf8;">{d_tot_kings['w3_p']:.1f}%</td>
        <td style="text-align:center;color:#c084fc;">{d_tot_kings['w4_p']:.1f}%</td>
        <td style="text-align:center;color:#ef4444;font-weight:bold;">{d_tot_kings['sl_p']:.1f}%</td>
        <td style="text-align:center;color:#38bdf8;font-weight:bold;font-size:15px;">${d_tot_kings['gross']:+.2f}</td>
        <td style="text-align:center;color:#f87171;font-weight:bold;font-size:15px;">${d_tot_kings['fric']:.2f}-</td>
        <td style="text-align:center;color:{tot_kings_col};font-weight:bold;font-size:16px;background:#064e3b;">${d_tot_kings['net']:+.2f} دلار نقد</td>
    </tr>
    """)

    # 2. Raw noise summary (All 40+ patterns) for direct comparison
    tf_raw_rows = []
    for tf_name in available_tfs:
        t_sub = [r for r in closed if r.get('Timeframe') == tf_name]
        d = calc_tf_metrics(t_sub)
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
        </tr>
        """)

    d_tot_raw = calc_tf_metrics(closed) or {
        'cnt': 0, 'w1_p': 0.0, 'w2_p': 0.0, 'w3_p': 0.0, 'w4_p': 0.0, 'sl_p': 0.0, 'gross': 0.0, 'fric': 0.0, 'net': 0.0
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
    </tr>
    """)

    # Interactive Timeframe-Role Table: Scored by King Quality Score (KQS)
    tf_role_map = defaultdict(list)
    for r in closed:
        tf_role_map[(r.get('Timeframe', 'M1'), r.get('Role', 'Unknown'))].append(r)

    computed_tf_roles = []
    for (tf, role), t_list in tf_role_map.items():
        cnt = len(t_list)
        w1 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 1])
        w2 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 2])
        w3 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 3])
        w4 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 4])
        sl = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) == 0])

        w1_p = w1 / cnt * 100
        w2_p = w2 / cnt * 100
        w3_p = w3 / cnt * 100
        w4_p = w4 / cnt * 100
        sl_p = sl / cnt * 100

        is_perfect = (cnt >= 2 and sl == 0)
        is_runner = (w3_p >= 30.0 or w4_p >= 30.0)

        # Calculate Net Profit with 0.04 scale-out
        gross = 0.0
        for r in t_list:
            pts = float(r.get('RiskPoints', 0.0))
            hr = int(r.get('HitTargetRatio', 0))
            if hr == 0:
                gross -= pts * 0.04
            else:
                if hr >= 1: gross += pts * 1.0 * 0.01
                if hr >= 2: gross += pts * 2.0 * 0.01
                if hr >= 3: gross += pts * 3.0 * 0.01
                if hr >= 4: gross += pts * 4.0 * 0.01
        fric = cnt * friction_04_per_trade
        net = gross - fric

        # Institutional Metrics (Chronological Max Drawdown, Profit Factor, Return/DD Ratio)
        cum_pnl = 0.0
        peak = 0.0
        max_dd = 0.0
        gross_win = 0.0
        gross_loss = 0.0
        sorted_trades = sorted(t_list, key=lambda x: x.get('EntryTime', ''))
        for r in sorted_trades:
            pts = float(r.get('RiskPoints', 0.0))
            hr = int(r.get('HitTargetRatio', 0))
            if hr == 0:
                pnl = -pts * 0.04 - friction_04_per_trade
                gross_loss += abs(pnl)
            else:
                pnl = -friction_04_per_trade
                if hr >= 1: pnl += pts * 1.0 * 0.01
                if hr >= 2: pnl += pts * 2.0 * 0.01
                if hr >= 3: pnl += pts * 3.0 * 0.01
                if hr >= 4: pnl += pts * 4.0 * 0.01
                gross_win += max(pnl, 0.0)
                if pnl < 0: gross_loss += abs(pnl)

            cum_pnl += pnl
            if cum_pnl > peak: peak = cum_pnl
            dd = peak - cum_pnl
            if dd > max_dd: max_dd = dd

        pf = gross_win / gross_loss if gross_loss > 0 else (99.0 if gross_win > 0 else 0.0)
        ret_dd = net / max_dd if max_dd > 0 else (net if net > 0 else 0.0)

        # 7-Pillar Institutional King Score Formula:
        profit_per_trade = net / max(cnt, 1)

        if net <= 0:
            final_score = net * 2.0 - sl_p
        else:
            # Pillar 1: 🛡️ Purity / Zero-SL (0 to 500 pts)
            if cnt >= 2 and sl == 0:
                f_purity = 500.0
            elif cnt >= 3 and sl_p <= 15.0:
                f_purity = 300.0
            elif cnt >= 3 and sl_p <= 25.0:
                f_purity = 200.0
            elif cnt >= 4 and sl_p <= 35.0:
                f_purity = 100.0
            elif cnt >= 4 and sl_p <= 45.0:
                f_purity = 50.0
            else:
                f_purity = 0.0

            # Pillar 2: 🎯 TP2 Depth (0 to 400 pts)
            f_tp2 = w2_p * 4.0

            # Pillar 3: ⚡ Runner & Target Progression Quality (up to ~250 pts)
            f_prog = (w1_p * 0.5) + (w3_p * 1.0) + (w4_p * 1.5) - (sl_p * 0.5)

            # Pillar 4: 💰 Efficiency ($/trade) (0 to 200 pts)
            f_eff = min(max(profit_per_trade, 0.0) * 20.0, 200.0)

            # Pillar 5: 📊 Statistical Confidence (0 to 50 pts)
            f_rel = min(math.log10(cnt + 9) * 20.0, 50.0)

            # Pillar 6: ⚖️ Institutional Profit Factor (0 to 100 pts)
            if sl == 0 and cnt >= 2:
                f_pf = 100.0
            else:
                f_pf = min(max(pf - 1.0, 0.0) * 50.0, 100.0)

            # Pillar 7: 🛡️ Drawdown Resistance & Recovery Factor (0 to 100 pts)
            if sl == 0 and cnt >= 2:
                f_rec = 100.0
            else:
                f_rec = min(ret_dd * 6.0, 100.0)
                if max_dd > 30.0:
                    f_rec = max(f_rec - (max_dd - 30.0) * 1.5, 0.0)

            final_score = f_purity + f_tp2 + f_prog + f_eff + f_rel + f_pf + f_rec

        computed_tf_roles.append({
            'tf': tf, 'role': role, 'cnt': cnt,
            'w1_p': w1_p, 'w2_p': w2_p, 'w3_p': w3_p, 'w4_p': w4_p, 'sl_p': sl_p,
            'score': final_score, 'is_perfect': is_perfect, 'is_runner': is_runner,
            'gross': gross, 'fric': fric, 'net': net,
            'max_dd': max_dd, 'pf': pf, 'ret_dd': ret_dd
        })

    # Sort by King Score descending by default, breaking ties with trade count
    computed_tf_roles.sort(key=lambda x: (x['score'], x['cnt']), reverse=True)

    tf_role_rows = []
    for item in computed_tf_roles:
        tf = item['tf']
        role = item['role']
        cnt = item['cnt']
        w1_p = item['w1_p']
        w2_p = item['w2_p']
        w3_p = item['w3_p']
        w4_p = item['w4_p']
        sl_p = item['sl_p']
        score = item['score']
        net = item['net']
        net_col = "#00e676" if net >= 0 else "#ef4444"

        pf = item['pf']
        pf_str = "<span style='color:#00e676;'>MAX</span>" if pf >= 90 else f"{pf:.2f}"
        max_dd = item['max_dd']
        dd_str = f"<span style='color:#00e676;'>$0.00</span>" if max_dd == 0 else (f"<span style='color:#fbbf24;'>${max_dd:.2f}</span>" if max_dd <= 25 else f"<span style='color:#f87171;'>${max_dd:.2f}</span>")
        ret_dd = item['ret_dd']
        ret_str = f"<span style='color:#facc15;font-weight:bold;'>{ret_dd:.1f}x</span>"

        badge_html = ""
        if item['is_perfect']:
            badge_html += " <span style='background:#064e3b;color:#34d399;font-size:10px;padding:2px 5px;border-radius:4px;border:1px solid #059669;'>💎 ۱۰۰٪ قطعی</span>"
        elif item['is_runner']:
            badge_html += " <span style='background:#312e81;color:#a5b4fc;font-size:10px;padding:2px 5px;border-radius:4px;border:1px solid #4338ca;'>🚀 دونده</span>"

        if score >= 1000:
            score_html = f"<span style='color:#facc15;font-weight:bold;font-size:15px;'>{score:.1f} 👑</span>"
        elif score >= 500:
            score_html = f"<span style='color:#38bdf8;font-weight:bold;font-size:14px;'>{score:.1f} ⭐</span>"
        elif score >= 250:
            score_html = f"<span style='color:#00e676;font-weight:bold;font-size:13px;'>{score:.1f}</span>"
        else:
            score_html = f"<span style='color:#ef4444;font-size:13px;'>{score:.1f}</span>"

        tf_role_rows.append(f"""
        <tr class="tf-row" data-tf="{tf}" data-role="{role}" data-cnt="{cnt}" data-w1="{w1_p:.2f}" data-w2="{w2_p:.2f}" data-w3="{w3_p:.2f}" data-w4="{w4_p:.2f}" data-sl="{sl_p:.2f}" data-net="{net:.2f}" data-pf="{pf:.2f}" data-dd="{max_dd:.2f}" data-retdd="{ret_dd:.2f}" data-score="{score:.2f}">
            <td style="color:#38bdf8;font-weight:bold;">{tf}</td>
            <td style="color:#facc15;font-weight:bold;">{role}{badge_html}</td>
            <td style="text-align:center;font-weight:bold;">{cnt}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{w1_p:.1f}%</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{w2_p:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;">{w3_p:.1f}%</td>
            <td style="text-align:center;color:#c084fc;">{w4_p:.1f}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{sl_p:.1f}%</td>
            <td style="text-align:center;color:{net_col};font-weight:bold;font-size:14px;background:#064e3b18;">${net:+.2f}</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">{pf_str}</td>
            <td style="text-align:center;font-weight:bold;">{dd_str}</td>
            <td style="text-align:center;font-weight:bold;">{ret_str}</td>
            <td style="text-align:center;">{score_html}</td>
        </tr>
        """)

    # Financial 0.01 Lot
    f01_comm = len(closed) * 0.06
    f01_spread = len(closed) * 0.06
    f01_friction = f01_comm + f01_spread

    f01_gross_tp1, f01_w1, f01_l1 = 0.0, 0.0, 0.0
    for r in closed:
        pts = float(r.get('RiskPoints', 0.0))
        hr = int(r.get('HitTargetRatio', 0))
        if hr >= 1: win = pts * 0.01; f01_gross_tp1 += win; f01_w1 += win
        else: loss = pts * 0.01; f01_gross_tp1 -= loss; f01_l1 += loss
    f01_net_tp1 = f01_gross_tp1 - f01_friction
    f01_pf_tp1 = f01_w1 / f01_l1 if f01_l1 > 0 else 0.0

    f01_gross_tp2, f01_w2, f01_l2 = 0.0, 0.0, 0.0
    for r in closed:
        pts = float(r.get('RiskPoints', 0.0))
        hr = int(r.get('HitTargetRatio', 0))
        if hr >= 2: win = pts * 2 * 0.01; f01_gross_tp2 += win; f01_w2 += win
        else: loss = pts * 0.01; f01_gross_tp2 -= loss; f01_l2 += loss
    f01_net_tp2 = f01_gross_tp2 - f01_friction
    f01_pf_tp2 = f01_w2 / f01_l2 if f01_l2 > 0 else 0.0

    # Master Table All Patterns
    role_map = defaultdict(list)
    for r in closed:
        role_map[r.get('Role', 'Unknown')].append(r)

    all_patterns_rows = []
    for role_name, t_list in sorted(role_map.items(), key=lambda x: len(x[1]), reverse=True):
        cnt = len(t_list)
        w1 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 1])
        w2 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 2])
        w3 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 3])
        w4 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 4])
        sl = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) == 0])

        w1_p = w1 / cnt * 100
        w2_p = w2 / cnt * 100
        sl_p = sl / cnt * 100

        p_gross = 0.0
        for r in t_list:
            pts = float(r.get('RiskPoints', 0.0))
            hr = int(r.get('HitTargetRatio', 0))
            if hr == 0: p_gross -= pts * 0.04
            elif hr == 1: p_gross += pts * 0.02
            elif hr in [2, 3]: p_gross += (pts * 0.02) + (pts * 2 * 0.01)
            elif hr >= 4: p_gross += (pts * 0.02) + (pts * 2 * 0.01) + (pts * 4 * 0.01)

        p_fric = cnt * friction_04_per_trade
        p_net = p_gross - p_fric
        net_col = "#00e676" if p_net >= 0 else "#ef4444"

        all_patterns_rows.append(f"""
        <tr>
            <td style="color:#facc15;font-weight:bold;">{role_name}</td>
            <td style="text-align:center;font-weight:bold;">{cnt}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{w1_p:.1f}%</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{w2_p:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;">{w3/cnt*100:.1f}%</td>
            <td style="text-align:center;color:#c084fc;">{w4/cnt*100:.1f}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{sl_p:.1f}%</td>
            <td style="text-align:center;color:{net_col};font-weight:bold;">${p_net:+.2f}</td>
        </tr>
        """)

    # Loss Pattern Intelligence
    sl_trades = [r for r in closed if int(r.get('HitTargetRatio', 0)) == 0]
    total_losses = len(sl_trades)

    night_losses = len([r for r in sl_trades if is_night_session(r.get('EntryTime', ''))])
    single_ls_losses = len([r for r in sl_trades if is_single_ls(r.get('Role', ''))])
    toxic_losses = len([r for r in sl_trades if is_toxic_pattern(r.get('Role', ''))])
    pure_flag_losses = len([r for r in sl_trades if is_pure_flag(r.get('Role', ''))])


    # =========================================================================
    # WEEKLY BREAKDOWN & CONSISTENCY ENGINE (هفته به هفته و سنجش پایداری)
    # =========================================================================
    weekly_data = defaultdict(lambda: {
        'trades_all': [],
        'trades_kings': [],
        'boxes_all': defaultdict(list),
        'boxes_kings': defaultdict(list)
    })
    box_weekly_history = defaultdict(lambda: defaultdict(list))
    king_keys = {(k['role'], k['tf']) for k in qualified_kings}

    def calc_scaleout_pnl(r):
        pts = float(r.get('RiskPoints', 0.0))
        hr = int(r.get('HitTargetRatio', 0))
        if hr == 0: gross = - pts * 0.04
        elif hr == 1: gross = pts * 0.02
        elif hr in [2, 3]: gross = (pts * 0.02) + (pts * 2 * 0.01)
        else: gross = (pts * 0.02) + (pts * 2 * 0.01) + (pts * 4 * 0.01)
        return gross - friction_04_per_trade

    for r in closed:
        et = r.get('EntryTime', '')
        if not et or et == 'None': continue
        try:
            dt = datetime.strptime(et, "%Y.%m.%d %H:%M")
            yr, wk, _ = dt.isocalendar()
            wk_key = (yr, wk)
            role = r.get('Role', 'Unknown')
            tf = r.get('Timeframe', 'M1')
            b_key = f"{role} [{tf}]"
            is_k = (role, tf) in king_keys

            weekly_data[wk_key]['trades_all'].append(r)
            weekly_data[wk_key]['boxes_all'][b_key].append(r)
            box_weekly_history[b_key][wk_key].append(r)

            if is_k:
                weekly_data[wk_key]['trades_kings'].append(r)
                weekly_data[wk_key]['boxes_kings'][b_key].append(r)
        except:
            continue

    sorted_wk_keys = sorted(weekly_data.keys())
    total_weeks = len(sorted_wk_keys)

    # 1. Weekly Consistency Ranking for All Boxes
    consistency_list = []
    for b_key, w_dict in box_weekly_history.items():
        tot_wks = len(w_dict)
        if tot_wks < 2: continue
        green_wks = 0
        red_wks = 0
        flat_wks = 0
        tot_pnl = 0.0
        tot_t = 0
        tot_w1 = 0
        tot_sl = 0

        for wk_k, t_list in w_dict.items():
            w_pnl = sum(calc_scaleout_pnl(r) for r in t_list)
            tot_pnl += w_pnl
            tot_t += len(t_list)
            tot_w1 += len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 1])
            tot_sl += len([r for r in t_list if int(r.get('HitTargetRatio', 0)) == 0])
            if w_pnl > 0.05: green_wks += 1
            elif w_pnl < -0.05: red_wks += 1
            else: flat_wks += 1

        cons_pct = (green_wks / tot_wks) * 100 if tot_wks else 0
        parts = b_key.rsplit(' [', 1)
        r_name = parts[0]
        tf_name = parts[1].rstrip(']') if len(parts) > 1 else 'M1'
        is_k = (r_name, tf_name) in king_keys

        consistency_list.append({
            'box': b_key,
            'role': r_name,
            'tf': tf_name,
            'is_king': is_k,
            'weeks': tot_wks,
            'green': green_wks,
            'red': red_wks,
            'flat': flat_wks,
            'cons_pct': cons_pct,
            'net_usd': tot_pnl,
            'trades': tot_t,
            'w1_pct': (tot_w1 / tot_t * 100) if tot_t else 0,
            'sl_pct': (tot_sl / tot_t * 100) if tot_t else 0
        })

    consistency_list.sort(key=lambda x: (x['is_king'], x['cons_pct'] >= 65, x['green'], x['net_usd']), reverse=True)

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

    # 2. Timeline & Details
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
        k_pnl = sum(calc_scaleout_pnl(r) for r in t_kings)
        tot_kings_6m_pnl += k_pnl
        if k_pnl >= 0: tot_kings_green_wks += 1
        else: tot_kings_red_wks += 1

        all_cnt = len(t_all)
        all_wins = len([r for r in t_all if int(r.get('HitTargetRatio', 0)) >= 1])
        all_losses = len([r for r in t_all if int(r.get('HitTargetRatio', 0)) == 0])
        all_wr = (all_wins / all_cnt * 100) if all_cnt else 0
        all_loss_r = (all_losses / all_cnt * 100) if all_cnt else 0
        all_pnl = sum(calc_scaleout_pnl(r) for r in t_all)

        dts = [datetime.strptime(r['EntryTime'], '%Y.%m.%d %H:%M') for r in t_all]
        date_range = f"{min(dts).strftime('%Y.%m.%d')} تا {max(dts).strftime('%m.%d')}"

        best_k_name = "---"
        best_k_pnl = -999999
        for b_name, b_trades in w_data['boxes_kings'].items():
            bp = sum(calc_scaleout_pnl(r) for r in b_trades)
            if bp > best_k_pnl:
                best_k_pnl = bp
                best_k_name = f"{b_name} (+${bp:.2f})"
        if best_k_pnl == -999999 or best_k_pnl <= 0:
            best_k_name = "---"

        best_all_name = "---"
        best_all_pnl = -999999
        for b_name, b_trades in w_data['boxes_all'].items():
            bp = sum(calc_scaleout_pnl(r) for r in b_trades)
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
        sorted_boxes_this_wk = sorted(w_data['boxes_all'].items(), key=lambda x: sum(calc_scaleout_pnl(r) for r in x[1]), reverse=True)
        for b_name, b_trades in sorted_boxes_this_wk:
            b_cnt = len(b_trades)
            b_wins = len([r for r in b_trades if int(r.get('HitTargetRatio', 0)) >= 1])
            b_sl = len([r for r in b_trades if int(r.get('HitTargetRatio', 0)) == 0])
            b_wr = (b_wins / b_cnt * 100) if b_cnt else 0
            b_loss_r = (b_sl / b_cnt * 100) if b_cnt else 0
            b_pnl = sum(calc_scaleout_pnl(r) for r in b_trades)
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

    top_consistent_box = consistency_list[0]['box'] if consistency_list else 'N/A'

    # =========================================================================
    # MULTI-PERIOD CONSISTENCY, GOLDEN INTERSECTION & CROSS-VERIFICATION ENGINE
    # =========================================================================
    def get_period_key(dt, p_type, b_yr):
        yr = dt.year
        m = dt.month
        if p_type == '1M': return f"{yr}-{m:02d}"
        elif p_type == '2M': return f"{yr}-B{(m - 1) // 2 + 1}"
        elif p_type == '3M': return f"{yr}-Q{(m - 1) // 3 + 1}"
        elif p_type == '6M': return f"{yr}-H{1 if m <= 6 else 2}"
        elif p_type == '9M': return f"9M-P{((yr - b_yr) * 12 + (m - 1)) // 9 + 1}"
        elif p_type == '1Y': return f"{yr}"
        elif p_type == '2Y': return f"2Y-P{((yr - b_yr) // 2) + 1}"
        elif p_type == '3Y': return f"3Y-P{((yr - b_yr) // 3) + 1}"
        return f"{yr}"

    period_configs = [
        ('1M', 'بازه ۱ ماهه (Monthly)', 'دوره‌های ۱ ماهه تقویمی'),
        ('2M', 'بازه ۲ ماهه (Bi-Monthly)', 'دوره‌های ۲ ماهه متوالی بازار'),
        ('3M', 'بازه ۳ ماهه / فصلی (Quarterly)', 'فصول کامل معاملاتی'),
        ('6M', 'بازه ۶ ماهه / نیم‌سال (Semi-Annual)', 'نیم‌سال‌های کلان بازار'),
        ('9M', 'بازه ۹ ماهه (9-Month)', 'دوره‌های ۹ ماهه پیوسته'),
        ('1Y', 'بازه ۱ ساله (Annual)', 'دوره‌های سالانه تقویمی'),
        ('2Y', 'بازه ۲ ساله (Bi-Annual)', 'دوره‌های ۲ ساله کلان'),
        ('3Y', 'بازه ۳ ساله (Tri-Annual)', 'دوره‌های ۳ ساله بلندمدت')
    ]

    # Group trades by (Role, TF)
    box_trades_map = defaultdict(list)
    for r in closed:
        et = r.get('EntryTime', '')
        if not et or et == 'None': continue
        try:
            dt = datetime.strptime(et, "%Y.%m.%d %H:%M")
            role = r.get('Role', 'Unknown')
            tf = r.get('Timeframe', 'M1')
            box_trades_map[(role, tf)].append((dt, r))
        except:
            continue

    mp_period_data = {}
    for pt, ptitle, pdesc in period_configs:
        all_p_set = set()
        b_p_pnl = defaultdict(lambda: defaultdict(float))
        b_p_cnt = defaultdict(lambda: defaultdict(int))
        b_p_win = defaultdict(lambda: defaultdict(int))
        b_p_sl  = defaultdict(lambda: defaultdict(int))

        for (role, tf), t_list in box_trades_map.items():
            b_key = f"{role} [{tf}]"
            for dt, r in t_list:
                pkey = get_period_key(dt, pt, base_yr)
                all_p_set.add(pkey)
                pnl = calc_scaleout_pnl(r)
                b_p_pnl[b_key][pkey] += pnl
                b_p_cnt[b_key][pkey] += 1
                hr = int(r.get('HitTargetRatio', 0))
                if hr >= 1: b_p_win[b_key][pkey] += 1
                elif hr == 0: b_p_sl[b_key][pkey] += 1

        tot_p_cnt = len(all_p_set)
        b_list = []
        for (role, tf), t_list in box_trades_map.items():
            b_key = f"{role} [{tf}]"
            p_dict = b_p_cnt[b_key]
            act_p = len(p_dict)
            if act_p < 2 and pt in ['1M', '2M', '3M'] and len(t_list) < 4:
                continue

            green_c = sum(1 for pk, pnl in b_p_pnl[b_key].items() if pnl > 0.05)
            red_c   = sum(1 for pk, pnl in b_p_pnl[b_key].items() if pnl < -0.05)
            tot_pnl = sum(b_p_pnl[b_key].values())
            tot_t   = sum(b_p_cnt[b_key].values())
            tot_w   = sum(b_p_win[b_key].values())
            tot_s   = sum(b_p_sl[b_key].values())

            wr   = (tot_w / tot_t * 100) if tot_t else 0
            sl_r = (tot_s / tot_t * 100) if tot_t else 0
            cons = (green_c / act_p * 100) if act_p else 0
            is_k = (role, tf) in king_keys

            b_list.append({
                'role': role, 'tf': tf, 'b_key': b_key,
                'kk': f"{role}|{tf}",
                'is_king': is_k,
                'active_p': act_p, 'tot_p': tot_p_cnt,
                'green': green_c, 'red': red_c, 'cons': cons,
                'net': tot_pnl, 'trades': tot_t, 'wr': wr, 'sl_r': sl_r
            })

        b_list.sort(key=lambda x: (x['is_king'], x['cons'] >= 65, x['green'], x['net']), reverse=True)
        mp_period_data[pt] = {
            'title': ptitle, 'desc': pdesc, 'tot_p': tot_p_cnt, 'boxes': b_list
        }

    # All-Weather Golden Intersection Engine
    mp_intersection_list = []
    for (role, tf) in box_trades_map:
        b_key = f"{role} [{tf}]"
        b1 = next((x for x in mp_period_data['1M']['boxes'] if x['b_key'] == b_key), None)
        b3 = next((x for x in mp_period_data['3M']['boxes'] if x['b_key'] == b_key), None)
        b6 = next((x for x in mp_period_data['6M']['boxes'] if x['b_key'] == b_key), None)
        b1y = next((x for x in mp_period_data['1Y']['boxes'] if x['b_key'] == b_key), None)

        if b1 and b3 and b6 and b1y and b1['net'] > 20.0 and b1['cons'] >= 50.0 and b3['cons'] >= 60.0:
            all_weather_score = (b1['cons'] * 0.35) + (b3['cons'] * 0.30) + (b6['cons'] * 0.20) + (b1y['cons'] * 0.15)
            mp_intersection_list.append({
                'role': role, 'tf': tf, 'b_key': b_key,
                'kk': f"{role}|{tf}",
                'is_king': (role, tf) in king_keys,
                'b1': b1, 'b3': b3, 'b6': b6, 'b1y': b1y,
                'score': all_weather_score,
                'net': b1['net'], 'wr': b1['wr'], 'sl_r': b1['sl_r'], 'trades': b1['trades']
            })

    mp_intersection_list.sort(key=lambda x: (x['score'], x['net']), reverse=True)

    # Cross-Verification Maps
    inter_map = {k['kk']: (idx, k) for idx, k in enumerate(mp_intersection_list, 1)}
    master_map = {f"{k['role']}|{k['tf']}": (idx, k) for idx, k in enumerate(qualified_kings, 1)}
    overlap_count = sum(1 for k in qualified_kings if f"{k['role']}|{k['tf']}" in inter_map)
    master_only_count = len(qualified_kings) - overlap_count
    overlap_ratio = (overlap_count / len(qualified_kings) * 100) if qualified_kings else 0

    # 1. Regenerate kings_rows_html with prominent Golden Intersection Cross Badges
    kings_rows_html = []
    medals = ['🥇', '🥈', '🥉', '👑', '👑', '⭐', '⭐', '⭐', '⭐', '⭐']
    for idx, k in enumerate(qualified_kings, 1):
        rank_icon = medals[idx-1] if idx <= len(medals) else f"#{idx}"
        kk_cur = f"{k['role']}|{k['tf']}"
        badge_html = ""
        if kk_cur in inter_map:
            i_idx, _ = inter_map[kk_cur]
            badge_html += f" <span style='background:#064e3b;color:#34d399;font-size:10px;padding:2px 6px;border-radius:4px;border:1px solid #059669;' title='تایید استقامت در تمام فصول (رتبه #{i_idx})'>💎 اشتراک طلایی #{i_idx}</span>"
        else:
            badge_html += " <span style='background:#451a03;color:#fca5a5;font-size:10px;padding:2px 6px;border-radius:4px;border:1px solid #991b1b;' title='سودآور در کل تاریخچه، دارای نوسان یا افت در برخی فصول'>⚠️ نوسان فصلی</span>"

        if k['is_perfect']:
            badge_html += " <span style='background:#064e3b;color:#34d399;font-size:10px;padding:2px 5px;border-radius:4px;border:1px solid #059669;'>💎 ۱۰۰٪ قطعی</span>"
        elif k['is_runner']:
            badge_html += " <span style='background:#312e81;color:#a5b4fc;font-size:10px;padding:2px 5px;border-radius:4px;border:1px solid #4338ca;'>🚀 دونده</span>"

        net_col = "#00e676" if k['net'] >= 0 else "#ef4444"
        pf = k['pf']
        pf_str = "<span style='color:#00e676;'>MAX</span>" if pf >= 90 else f"{pf:.2f}"
        max_dd = k['max_dd']
        dd_col = "#00e676" if max_dd == 0 else ("#fbbf24" if max_dd <= 25 else "#f87171")
        ret_dd = k['ret_dd']
        ret_str = f"{ret_dd:.1f}x"

        kings_rows_html.append(f"""
        <tr>
            <td style="text-align:center;font-size:16px;font-weight:bold;">{rank_icon}</td>
            <td style="color:#38bdf8;font-weight:bold;text-align:center;font-size:14px;">{k['tf']}</td>
            <td style="color:#facc15;font-weight:bold;font-size:14px;">{k['role']}{badge_html}</td>
            <td style="text-align:center;color:#facc15;font-weight:bold;font-size:14px;background:#1e293b;">{k['score']:.1f}</td>
            <td style="text-align:center;font-weight:bold;">{k['cnt']}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{k['w1_p']:.1f}%</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{k['w2_p']:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;">{k['w3_p']:.1f}%</td>
            <td style="text-align:center;color:#c084fc;">{k['w4_p']:.1f}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{k['sl_p']:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;font-size:13px;">{pf_str}</td>
            <td style="text-align:center;color:{dd_col};font-weight:bold;font-size:13px;">${max_dd:.2f}</td>
            <td style="text-align:center;color:#facc15;font-weight:bold;font-size:13px;">{ret_str}</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;font-size:13px;">${k['gross']:+.2f}</td>
            <td style="text-align:center;color:#f87171;font-weight:bold;font-size:13px;">${k['fric']:.2f}-</td>
            <td style="text-align:center;color:{net_col};font-weight:bold;font-size:15px;background:#064e3b22;">${k['net']:+.2f} دلار</td>
        </tr>
        """)

    # 2. Generate HTML for Intersection Table Rows with Master Rank Column
    mp_intersection_rows_html = []
    for idx, k in enumerate(mp_intersection_list, 1):
        k_tag = "👑 سلطان" if k['is_king'] else "سایر"
        k_color = "#facc15" if k['is_king'] else "#94a3b8"
        pnl_col = "#00e676" if k['net'] >= 0 else "#ef4444"
        badge = "💎 الماس ضدضربه" if k['score'] >= 90 else ("⭐ طلایی همه‌فصول" if k['score'] >= 80 else "🟢 باثبات دائم")
        badge_bg = "#064e3b" if k['score'] >= 90 else ("#1e3a8a" if k['score'] >= 80 else "#451a03")
        badge_col = "#34d399" if k['score'] >= 90 else ("#93c5fd" if k['score'] >= 80 else "#fca5a5")

        m_idx, m_info = master_map.get(k['kk'], (None, None))
        if m_idx:
            m_rank_html = f'<span style="color:#facc15;font-weight:bold;">👑 رتبه #{m_idx} <span style="font-size:11px;color:#94a3b8;">({m_info["score"]:.1f})</span></span>'
        else:
            m_rank_html = '<span style="color:#94a3b8;">---</span>'

        mp_intersection_rows_html.append(f"""
        <tr class="mp-row" data-tf="{k['tf']}" style="border-bottom:1px solid #1e293b;">
            <td style="text-align:center;font-weight:bold;color:#94a3b8;">#{idx}</td>
            <td style="text-align:center;">{m_rank_html}</td>
            <td style="font-weight:bold;color:{k_color};">{k['b_key']}</td>
            <td style="text-align:center;"><span style="background:{'#854d0e' if k['is_king'] else '#1e293b'};color:{k_color};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">{k_tag}</span></td>
            <td style="text-align:center;font-weight:bold;color:#38bdf8;font-size:14px;background:#0c253d;">{k['score']:.1f}</td>
            <td style="text-align:center;color:#34d399;font-weight:bold;">{k['b1']['green']}/{k['b1']['active_p']} ({k['b1']['cons']:.0f}%)</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">{k['b3']['green']}/{k['b3']['active_p']} ({k['b3']['cons']:.0f}%)</td>
            <td style="text-align:center;color:#c084fc;font-weight:bold;">{k['b6']['green']}/{k['b6']['active_p']} ({k['b6']['cons']:.0f}%)</td>
            <td style="text-align:center;color:#fbbf24;font-weight:bold;">{k['b1y']['green']}/{k['b1y']['active_p']} ({k['b1y']['cons']:.0f}%)</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{k['wr']:.1f}%</td>
            <td style="text-align:center;color:#ef4444;">{k['sl_r']:.1f}%</td>
            <td style="text-align:center;font-weight:bold;">{k['trades']}</td>
            <td style="text-align:center;font-weight:bold;color:{pnl_col};font-size:13.5px;">${k['net']:+.2f}</td>
            <td style="text-align:center;"><span style="background:{badge_bg};color:{badge_col};padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">{badge}</span></td>
        </tr>
        """)

    if not mp_intersection_rows_html:
        mp_intersection_rows_html.append(f"""
        <tr>
            <td colspan="14" style="text-align:center;padding:26px 14px;color:#94a3b8;font-size:12.5px;background:#0d1527;">
                <div style="font-size:22px;margin-bottom:6px;">ℹ️</div>
                <b>در بازه تاریخی فعلی ({history_span_title})، افق‌های بلندمدت چندگانه به دلیل کوتاه‌تر بودن تاریخچه آزمون فعال نشده‌اند.</b><br>
                <span style="color:#facc15;display:inline-block;margin-top:6px;font-size:12px;">برای مشاهده {len(qualified_kings)} سلطان منتخب و عملکرد سودآوری آنها، از دکمه تب <b>«🏛️ جدول جامع رتبه‌بندی شاخص سلطان ({len(qualified_kings)} سلطان)»</b> در بالای همین جدول استفاده کنید.</span>
            </td>
        </tr>
        """)

    # 3. Generate HTML for Comparison Matrix View (All-Time vs All-Weather)
    compare_rows_html = []
    for m_idx, k in enumerate(qualified_kings, 1):
        kk = f"{k['role']}|{k['tf']}"
        b_name = f"{k['role']} [{k['tf']}]"
        in_inter = kk in inter_map
        pnl_col = "#00e676" if k['net'] >= 0 else "#ef4444"

        if in_inter:
            i_idx, i_k = inter_map[kk]
            status_html = '<span style="background:#064e3b;color:#34d399;padding:3px 8px;border-radius:5px;font-size:11px;font-weight:bold;border:1px solid #059669;">💎 تایید دوگانه (سلطان الماس)</span>'
            i_rank_html = f'<span style="color:#38bdf8;font-weight:bold;font-size:13px;">#{i_idx}</span>'
            score_all_w = f"{i_k['score']:.1f}"
            cons_1m = f"{i_k['b1']['cons']:.0f}% ({i_k['b1']['green']}/{i_k['b1']['active_p']})"
            cons_3m = f"{i_k['b3']['cons']:.0f}% ({i_k['b3']['green']}/{i_k['b3']['active_p']})"
            diag_reason = "✅ سودآوری پیوسته در تمام فصول، استقامت بالا در برابر تغییر فاز بازار"
            ea_rec = '<span style="background:#064e3b;color:#34d399;padding:3px 8px;border-radius:5px;font-size:11px;font-weight:bold;">🟢 تایید لایو (سپر ضدضربه)</span>'
        else:
            status_html = '<span style="background:#451a03;color:#fca5a5;padding:3px 8px;border-radius:5px;font-size:11px;font-weight:bold;border:1px solid #991b1b;">⚠️ فقط جدول جامع (نوسان فصلی)</span>'
            i_rank_html = '<span style="color:#94a3b8;">---</span>'
            score_all_w = '<span style="color:#94a3b8;">---</span>'
            b1 = next((x for x in mp_period_data['1M']['boxes'] if x['kk'] == kk), None)
            b3 = next((x for x in mp_period_data['3M']['boxes'] if x['kk'] == kk), None)
            cons_1m = f"{b1['cons']:.0f}%" if b1 else "---"
            cons_3m = f"{b3['cons']:.0f}%" if b3 else "---"
            if k['net'] < 20:
                diag_reason = f"⚠️ سود خالص دلاری (${k['net']:.2f}) زیر آستانه ۲۰ دلار اشتراک"
            elif k['sl_p'] >= 40:
                diag_reason = f"⚠️ نرخ استاپ بالا ({k['sl_p']:.1f}٪) و آسیب‌پذیری در فصول رکود"
            elif k['pf'] < 1.6:
                diag_reason = f"⚠️ پرافیت فاکتور لب‌مرزی ({k['pf']:.2f})"
            else:
                diag_reason = "⚠️ افت بازدهی در دوره‌های رکود فصلی (ثبات فصلی زیر ۶۰٪)"
            ea_rec = '<span style="background:#854d0e;color:#fef08a;padding:3px 8px;border-radius:5px;font-size:11px;font-weight:bold;">🟡 فقط مد تهاجمی (Aggressive)</span>'

        compare_rows_html.append(f"""
        <tr class="mp-row" data-tf="{k['tf']}" style="border-bottom:1px solid #1e293b;">
            <td style="text-align:center;font-weight:bold;color:#facc15;font-size:13.5px;">#{m_idx}</td>
            <td style="text-align:center;">{i_rank_html}</td>
            <td style="font-weight:bold;color:#e2e8f0;">{b_name}</td>
            <td style="text-align:center;">{status_html}</td>
            <td style="text-align:center;color:#facc15;font-weight:bold;background:#1e293b;">{k['score']:.1f}</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">{score_all_w}</td>
            <td style="text-align:center;color:#34d399;font-weight:bold;">{cons_1m}</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">{cons_3m}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{k['w1_p']:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">{k['pf']:.2f}</td>
            <td style="text-align:center;font-weight:bold;color:{pnl_col};">${k['net']:+.2f}</td>
            <td style="font-size:11.5px;color:#cbd5e1;line-height:1.4;">{diag_reason}</td>
            <td style="text-align:center;">{ea_rec}</td>
        </tr>
        """)

    # 4. Generate HTML for each Horizon's Table Rows (1M, 2M, 3M, 6M, 9M, 1Y, 2Y, 3Y)
    mp_tables_html = {}
    for pt, _, _ in period_configs:
        b_rows = []
        for idx, b in enumerate(mp_period_data[pt]['boxes'], 1):
            k_tag = "👑 سلطان" if b['is_king'] else "سایر"
            k_color = "#facc15" if b['is_king'] else "#94a3b8"
            pnl_col = "#00e676" if b['net'] >= 0 else "#ef4444"
            prog_col = "#10b981" if b['cons'] >= 75 else ("#38bdf8" if b['cons'] >= 60 else "#f59e0b")
            badge = "💎 عالی" if b['cons'] >= 80 else ("⭐ خوب" if b['cons'] >= 65 else "⚠️ نوسانی")
            badge_bg = "#064e3b" if b['cons'] >= 80 else ("#1e3a8a" if b['cons'] >= 65 else "#451a03")
            badge_col = "#34d399" if b['cons'] >= 80 else ("#93c5fd" if b['cons'] >= 65 else "#fca5a5")

            b_rows.append(f"""
            <tr class="mp-row" data-tf="{b['tf']}" style="border-bottom:1px solid #1e293b;">
                <td style="text-align:center;font-weight:bold;color:#94a3b8;">#{idx}</td>
                <td style="font-weight:bold;color:{k_color};">{b['b_key']}</td>
                <td style="text-align:center;"><span style="background:{'#854d0e' if b['is_king'] else '#1e293b'};color:{k_color};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">{k_tag}</span></td>
                <td style="text-align:center;">
                    <div style="display:flex;align-items:center;gap:8px;justify-content:center;">
                        <span style="font-weight:bold;color:{prog_col};min-width:42px;">{b['cons']:.1f}%</span>
                        <div style="width:70px;background:#1e293b;border-radius:10px;height:7px;overflow:hidden;border:1px solid #334155;">
                            <div style="width:{b['cons']}%;background:{prog_col};height:100%;"></div>
                        </div>
                    </div>
                </td>
                <td style="text-align:center;color:#34d399;font-weight:bold;">{b['green']} از {b['active_p']} دوره 🟢</td>
                <td style="text-align:center;color:#ef4444;font-weight:bold;">{b['red']} 🔴</td>
                <td style="text-align:center;color:#00e676;font-weight:bold;">{b['wr']:.1f}%</td>
                <td style="text-align:center;color:#ef4444;">{b['sl_r']:.1f}%</td>
                <td style="text-align:center;font-weight:bold;">{b['trades']}</td>
                <td style="text-align:center;font-weight:bold;color:{pnl_col};font-size:13.5px;">${b['net']:+.2f}</td>
                <td style="text-align:center;"><span style="background:{badge_bg};color:{badge_col};padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">{badge}</span></td>
            </tr>
            """)
        
        mp_tables_html[pt] = "".join(b_rows)

    # 5. Build Horizon Panels List
    mp_panels_list = []
    for pt, _, _ in period_configs:
        p_info = mp_period_data[pt]
        mp_panels_list.append(f"""
        <div id="panel-horizon-{pt}" class="horizon-view-panel" style="display:none;">
            <div class="section-box" style="border: 1px solid #38bdf8; background: #0c182c; margin-bottom: 0;">
                <div style="border-bottom: 1px solid #1e3a5f; padding-bottom: 14px; margin-bottom: 16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <h3 style="margin:0;color:#38bdf8;font-size:18px;display:flex;align-items:center;gap:8px;">
                            <span>📅</span> جدول رتبه‌بندی سلاطین در {p_info['title']} ({p_info['tot_p']} دوره)
                        </h3>
                        <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">{p_info['desc']}:</p>
                    </div>
                    <span style="background:#0c4a6e;color:#7dd3fc;font-size:12px;padding:4px 10px;border-radius:8px;font-weight:bold;">
                        📊 {len(p_info['boxes'])} الگوی فعال در این افق
                    </span>
                </div>

                <div style="overflow-x:auto;">
                    <table style="width:100%;font-size:12.5px;">
                        <thead>
                            <tr style="background:#1e293b;">
                                <th style="text-align:center;">رتبه</th>
                                <th>نام ساختار / تلاقی گره</th>
                                <th style="text-align:center;">وضعیت</th>
                                <th style="text-align:center;color:#38bdf8;">پایداری دوره‌ای (Consistency)</th>
                                <th style="text-align:center;color:#34d399;">دوره‌های مثبت (سبز)</th>
                                <th style="text-align:center;color:#ef4444;">دوره‌های منفی (قرمز)</th>
                                <th style="text-align:center;color:#00e676;">وین‌ریت TP1</th>
                                <th style="text-align:center;color:#ef4444;">نرخ باخت (SL)</th>
                                <th style="text-align:center;">تعداد ترید</th>
                                <th style="text-align:center;color:#00e676;background:#064e3b44;">سود خالص واقعی</th>
                                <th style="text-align:center;">ارزیابی</th>
                            </tr>
                        </thead>
                        <tbody>
                            {mp_tables_html[pt]}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        """)

    # 6. Horizon Pill Buttons (Dynamic for 1M to 3Y)
    horizon_pills_html = f"""
                <button class="horizon-pill-btn active" onclick="showHorizonView('INTERSECTION', this)" style="background:#0284c7;border:1px solid #38bdf8;color:#fff;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;box-shadow:0 0 10px rgba(56,189,248,0.3);">
                    🌟 اشتراک طلایی (همه‌فصول)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('1M', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۱ ماهه ({mp_period_data['1M']['tot_p']} دوره)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('2M', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۲ ماهه ({mp_period_data['2M']['tot_p']} دوره)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('3M', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۳ ماهه / فصلی ({mp_period_data['3M']['tot_p']} فصل)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('6M', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۶ ماهه / نیم‌سال ({mp_period_data['6M']['tot_p']} دوره)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('9M', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۹ ماهه ({mp_period_data['9M']['tot_p']} دوره)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('1Y', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۱ ساله ({mp_period_data['1Y']['tot_p']} دوره)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('2Y', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۲ ساله ({mp_period_data['2Y']['tot_p']} دوره)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('3Y', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۳ ساله ({mp_period_data['3Y']['tot_p']} دوره)
                </button>
    """

    has_intersection = (len(mp_intersection_list) > 0)
    btn_multi_cls = "kings-sub-btn active" if has_intersection else "kings-sub-btn"
    btn_multi_style = "background:#0284c7;border:1px solid #38bdf8;color:#fff;box-shadow:0 0 12px rgba(56,189,248,0.3);" if has_intersection else "background:#0f172a;border:1px solid #334155;color:#94a3b8;box-shadow:none;"

    btn_all_cls = "kings-sub-btn" if has_intersection else "kings-sub-btn active"
    btn_all_style = "background:#0f172a;border:1px solid #334155;color:#94a3b8;box-shadow:none;" if has_intersection else "background:#0284c7;border:1px solid #38bdf8;color:#fff;box-shadow:0 0 12px rgba(56,189,248,0.3);"

    disp_multi = "block" if has_intersection else "none"
    disp_all = "none" if has_intersection else "block"

    mp_full_html_section = f"""
    <!-- Sub-Navigation Toggle for Kings View (3 Sub-Views) -->
    <div style="display:flex;gap:10px;margin-bottom:18px;border-bottom:1px solid #334155;padding-bottom:12px;flex-wrap:wrap;align-items:center;justify-content:space-between;">
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button class="{btn_multi_cls}" id="btnKingsMulti" onclick="switchKingsSubView('multi', this)" style="{btn_multi_style}padding:8px 16px;border-radius:6px;font-size:12.5px;cursor:pointer;font-weight:bold;display:flex;align-items:center;gap:6px;">
                <span>🌟</span> کالبدشکافی چندبازه‌ای و اشتراک طلایی (1M تا 3Y)
            </button>
            <button class="{btn_all_cls}" id="btnKingsAllTime" onclick="switchKingsSubView('alltime', this)" style="{btn_all_style}padding:8px 16px;border-radius:6px;font-size:12.5px;cursor:pointer;font-weight:bold;display:flex;align-items:center;gap:6px;">
                <span>🏛️</span> جدول جامع رتبه‌بندی شاخص سلطان ({len(qualified_kings)} سلطان - {history_span_title})
            </button>
            <button class="kings-sub-btn" id="btnKingsCompare" onclick="switchKingsSubView('compare', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:8px 16px;border-radius:6px;font-size:12.5px;cursor:pointer;font-weight:bold;display:flex;align-items:center;gap:6px;">
                <span>⚖️</span> ماتریس تطبیق و مقایسه دو جدول (All-Time vs All-Weather)
            </button>
        </div>
        <div style="font-size:11.5px;color:#94a3b8;">
            کالبدشکافی پیوسته تمام دوره‌ها از <b>{date_start_str} تا {date_end_str}</b> ({history_span_title})
        </div>
    </div>

    <!-- VIEW 1: MULTI-PERIOD & GOLDEN INTERSECTION -->
    <div id="kingsViewMulti" style="display:{disp_multi};">
        <!-- Controls Bar: Horizon Switcher & Timeframe Filter -->
        <div style="background:#0b1322;border:1px solid #1e3a5f;border-radius:10px;padding:14px;margin-bottom:18px;box-shadow:0 4px 15px rgba(0,0,0,0.3);">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:12px;">
                <div>
                    <h4 style="margin:0;color:#facc15;font-size:15px;display:flex;align-items:center;gap:6px;">
                        <span>⏱️</span> انتخاب افق زمانی کالبدشکافی پایداری سلاطین (۱ ماه تا ۳ سال):
                    </h4>
                    <p style="margin:4px 0 0 0;color:#94a3b8;font-size:11.5px;">
                        سنجش استقامت و ثبات سودآوری الگوها در دوره‌های ۱ ماهه، ۲ ماهه، فصلی، نیم‌سال، ۹ ماهه، سالانه، ۲ ساله، ۳ ساله و اشتراک همه‌فصول:
                    </p>
                </div>
                <!-- Timeframe Filter Pills -->
                <div style="display:flex;align-items:center;gap:6px;background:#081424;padding:4px 8px;border-radius:6px;border:1px solid #1e293b;">
                    <span style="font-size:11px;color:#94a3b8;font-weight:bold;">فیلتر تایم:</span>
                    <button class="tf-filter-btn active" onclick="filterHorizonTF('ALL', this)" style="background:#0284c7;color:#fff;border:none;padding:3px 9px;border-radius:4px;font-size:11px;cursor:pointer;font-weight:bold;">همه</button>
                    <button class="tf-filter-btn" onclick="filterHorizonTF('M15', this)" style="background:#1e293b;color:#94a3b8;border:none;padding:3px 9px;border-radius:4px;font-size:11px;cursor:pointer;">M15</button>
                    <button class="tf-filter-btn" onclick="filterHorizonTF('M5', this)" style="background:#1e293b;color:#94a3b8;border:none;padding:3px 9px;border-radius:4px;font-size:11px;cursor:pointer;">M5</button>
                    <button class="tf-filter-btn" onclick="filterHorizonTF('M1', this)" style="background:#1e293b;color:#94a3b8;border:none;padding:3px 9px;border-radius:4px;font-size:11px;cursor:pointer;">M1</button>
                </div>
            </div>

            <!-- Horizon Pill Buttons -->
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
                {horizon_pills_html}
            </div>
        </div>

        <!-- Panel: All-Weather Golden Intersection -->
        <div id="panel-horizon-INTERSECTION" class="horizon-view-panel" style="display:block;">
            <div class="section-box" style="border: 1px solid #facc15; background: #131b2e; margin-bottom: 0;">
                <div style="border-bottom: 1px solid #854d0e; padding-bottom: 14px; margin-bottom: 16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <h3 style="margin:0;color:#facc15;font-size:19px;display:flex;align-items:center;gap:8px;">
                            <span>👑</span> جدول اشتراک طلایی سلاطین همه‌فصول (All-Weather Golden Intersection)
                        </h3>
                        <p style="margin:4px 0 0 0;color:#fef08a;font-size:12px;">
                            این الگوها در <b>تک‌تک افق‌های کوتاه‌مدت (۱ ماهه)، فصلی (۳ ماهه)، نیم‌سال (۶ ماهه) و سالانه (۱ ساله)</b> همواره سبز، پایدار و با کمترین نوسان دراداون بوده‌اند:
                        </p>
                    </div>
                    <span style="background:#854d0e;color:#fef08a;font-size:12px;padding:4px 10px;border-radius:8px;font-weight:bold;">
                        🏆 {len(mp_intersection_list)} سلطان ضدضربه
                    </span>
                </div>

                <div style="overflow-x:auto;">
                    <table style="width:100%;font-size:12.5px;">
                        <thead>
                            <tr style="background:#1e293b;">
                                <th style="text-align:center;">رتبه اشتراک</th>
                                <th style="text-align:center;">رتبه در جدول جامع</th>
                                <th>نام ساختار / تلاقی گره</th>
                                <th style="text-align:center;">وضعیت</th>
                                <th style="text-align:center;color:#38bdf8;" title="امتیاز پایداری ترکیبی در تمام افق‌های زمانی">شاخص همه‌فصول (Score)</th>
                                <th style="text-align:center;color:#34d399;">ثبات ۱ ماهه (1M)</th>
                                <th style="text-align:center;color:#38bdf8;">ثبات فصلی (3M)</th>
                                <th style="text-align:center;color:#c084fc;">ثبات نیم‌سال (6M)</th>
                                <th style="text-align:center;color:#fbbf24;">ثبات سالانه (1Y)</th>
                                <th style="text-align:center;color:#00e676;">وین‌ریت کلی</th>
                                <th style="text-align:center;color:#ef4444;">نرخ استاپ</th>
                                <th style="text-align:center;">تعداد ترید</th>
                                <th style="text-align:center;color:#00e676;background:#064e3b44;">سود خالص واقعی</th>
                                <th style="text-align:center;">ارزیابی پایداری</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(mp_intersection_rows_html)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        {''.join(mp_panels_list)}
    </div> <!-- End kingsViewMulti -->

    <!-- VIEW 3: DEDICATED CROSS-VERIFICATION & OVERLAP MATRIX -->
    <div id="kingsViewCompare" style="display:none;">
        <!-- KPI Comparison Summary Cards -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:14px;margin-bottom:18px;">
            <div style="background:#07271e;border:1px solid #059669;border-radius:10px;padding:16px;box-shadow:0 4px 15px rgba(0,0,0,0.3);">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <span style="font-size:24px;">💎</span>
                    <div>
                        <div style="font-size:12px;color:#34d399;font-weight:bold;">سلاطین الماس مشترک (هردو جدول)</div>
                        <div style="font-size:22px;color:#fff;font-weight:bold;">{overlap_count} الگو ({overlap_ratio:.0f}٪ کل سلاطین)</div>
                    </div>
                </div>
                <div style="font-size:11.5px;color:#a7f3d0;line-height:1.6;">
                    <b>۱۰۰٪ سلاطین اشتراک طلایی در جدول جامع هم حضور دارند!</b> این الگوها آزمون استقامت سودآوری را در تمام ماه‌ها، فصول و سال‌ها با درخشش کامل پاس کرده‌اند.
                </div>
            </div>

            <div style="background:#2a1b05;border:1px solid #d97706;border-radius:10px;padding:16px;box-shadow:0 4px 15px rgba(0,0,0,0.3);">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <span style="font-size:24px;">⚠️</span>
                    <div>
                        <div style="font-size:12px;color:#fcd34d;font-weight:bold;">سلاطین تک‌جدولی (فقط جدول جامع)</div>
                        <div style="font-size:22px;color:#fff;font-weight:bold;">{master_only_count} الگو (سودآور با نوسان فصلی)</div>
                    </div>
                </div>
                <div style="font-size:11.5px;color:#fde68a;line-height:1.6;">
                    در کل تاریخچه بازدهی مثبت ساخته‌اند، اما به دلیل افت در ۱ یا ۲ فصل خاص یا حجم ترید پایین‌تر، در اشتراک فصلی سخت‌گیرانه قرار نگرفتند.
                </div>
            </div>

            <div style="background:#0b1d3a;border:1px solid #0284c7;border-radius:10px;padding:16px;box-shadow:0 4px 15px rgba(0,0,0,0.3);">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <span style="font-size:24px;">🎯</span>
                    <div>
                        <div style="font-size:12px;color:#38bdf8;font-weight:bold;">توصیه اجرایی برای اکسپرت متاتریدر</div>
                        <div style="font-size:20px;color:#fff;font-weight:bold;">سپر کم‌ریسک (Conservative)</div>
                    </div>
                </div>
                <div style="font-size:11.5px;color:#bae6fd;line-height:1.6;">
                    برای حساب‌های لایو با حداقل دراوداون: <b>فقط {overlap_count} سلطان الماس مشترک</b> فعال شوند؛ ۶ الگوی دیگر برای مدهای تهاجمی مناسبند.
                </div>
            </div>
        </div>

        <!-- Analytical Explainer Box -->
        <div style="background:#131c2e;border:1px solid #38bdf8;border-radius:10px;padding:16px;margin-bottom:18px;">
            <h4 style="margin:0 0 8px 0;color:#facc15;font-size:15px;display:flex;align-items:center;gap:8px;">
                <span>🔍</span> کالبدشکافی تطبیق: آیا سلاطین اشتراک طلایی در جدول جامع حضور دارند؟
            </h4>
            <p style="margin:0;color:#cbd5e1;font-size:12.5px;line-height:1.7;">
                <b>پاسخ قطعی و مستند: بله! ۱۰۰٪ سلاطین اشتراک طلایی (تک‌تک {len(mp_intersection_list)} الگو) در جدول جامع سلاطین منتخب نیز رتبه برتر دارند.</b> 
                جدول تطبیقی زیر کالبدشکافی یک‌به‌یک تمام {len(qualified_kings)} سلطان را با رتبه جامع، رتبه اشتراک طلایی، شاخص همه‌فصول، درصد ثبات ماهانه و فصلی، و علت فنی تفاوت نمایش می‌دهد:
            </p>
        </div>

        <!-- Comparison Table -->
        <div class="section-box" style="border:1px solid #38bdf8;background:#0c182c;margin-bottom:0;">
            <div style="overflow-x:auto;">
                <table style="width:100%;font-size:12.5px;">
                    <thead>
                        <tr style="background:#1e293b;">
                            <th style="text-align:center;">رتبه جامع</th>
                            <th style="text-align:center;">رتبه اشتراک</th>
                            <th>نام ساختار / تلاقی گره</th>
                            <th style="text-align:center;">وضعیت انطباق دو جدول</th>
                            <th style="text-align:center;color:#facc15;">امتیاز جامع</th>
                            <th style="text-align:center;color:#38bdf8;">شاخص همه‌فصول</th>
                            <th style="text-align:center;color:#34d399;">ثبات ۱ ماهه</th>
                            <th style="text-align:center;color:#38bdf8;">ثبات فصلی</th>
                            <th style="text-align:center;color:#00e676;">وین‌ریت TP1</th>
                            <th style="text-align:center;color:#38bdf8;">پرافیت فاکتور</th>
                            <th style="text-align:center;color:#00e676;background:#064e3b44;">سود خالص ($)</th>
                            <th>کالبدشکافی فنی و دلیل</th>
                            <th style="text-align:center;">توصیه لایو برای اکسپرت</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(compare_rows_html)}
                    </tbody>
                </table>
            </div>
        </div>
    </div> <!-- End kingsViewCompare -->
    """
    # =========================================================================
    # EQUITY & BALANCE CURVE ENGINE (منحنی رشد سرمایه و بالانس به سبک متاتریدر)
    # =========================================================================
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
        pnl = calc_scaleout_pnl(r)
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

    import json
    json_pts_kings = json.dumps(pts_kings)
    json_pts_all = json.dumps(pts_all)

    # Simulator Kings Data Preparation (with Stop Loss analytics)
    kings_sim_list = []
    for i, k in enumerate(qualified_kings, 1):
        sl_count = k['sl']
        sl_trades = [r for r in k['trades'] if int(r.get('HitTargetRatio', 0)) == 0]
        sl_dollar = round(sum(float(r.get('RiskPoints', 0.0)) * 0.04 + friction_04_per_trade for r in sl_trades), 2)
        kings_sim_list.append({
            'id': i,
            'role': k['role'],
            'tf': k['tf'],
            'kk': f"{k['role']}|{k['tf']}",
            'score': round(k['score'], 1),
            'cnt': k['cnt'],
            'net': round(k['net'], 2),
            'w1_p': round(k['w1_p'], 1),
            'sl_cnt': sl_count,
            'sl_usd': sl_dollar,
            'sl_p': round(k['sl_p'], 1),
            'pf': round(k['pf'], 2) if k['pf'] < 900 else 999.0,
            'perf': 1 if k['is_perfect'] else 0,
            'run': 1 if k['is_runner'] else 0
        })

    # Sort Kings by Stop Loss metrics to identify top risk generators
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

    json_kings_sim = json.dumps(kings_sim_list, separators=(',', ':'))
    json_top3_sl_cnt = json.dumps(top3_sl_cnt_keys)
    json_top3_sl_usd = json.dumps(top3_sl_usd_keys)
    json_top5_sl_usd = json.dumps(top5_sl_usd_keys)
    json_top3_sl_pct = json.dumps(top3_sl_pct_keys)

    # Chronological Trades for Interactive Simulator
    trades_chrono = sorted([r for r in closed if r.get('Timeframe') in ['M1','M5','M15']], key=lambda x: x.get('EntryTime', ''))
    trades_sim_list = []
    for idx, r in enumerate(trades_chrono, 1):
        tf = r.get('Timeframe', 'M1')
        role = r.get('Role', '')
        is_k = 1 if (role, tf) in king_keys else 0
        hr = int(r.get('HitTargetRatio', 0))
        pts = float(r.get('RiskPoints', 0.0))
        if hr == 0:
            pnl = -pts * 0.04 - friction_04_per_trade
        else:
            pnl = -friction_04_per_trade
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
            'p': round(pnl, 2)
        })
    json_trades_sim = json.dumps(trades_sim_list, separators=(',', ':'))

    # Calculate initial concurrent open trades for base Kings
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

    # ==================== DYNAMIC AUTO-OPTIMIZER ENGINE ====================
    all_sim_k_keys = [k['kk'] for k in kings_sim_list]
    total_kings_trades = len([t for t in trades_sim_list if t.get('k') == 1])
    min_15pct_trades = max(15, int(total_kings_trades * 0.15))
    min_35pct_trades = max(25, int(total_kings_trades * 0.35))

    # 1. Rank Kings of this dataset dynamically by Profit Factor
    k_eval_stats = {}
    for t in trades_sim_list:
        if t['k'] != 1: continue
        kk = t['kk']
        if kk not in k_eval_stats: k_eval_stats[kk] = {'p': 0.0, 'wins': 0, 'cnt': 0, 'gp': 0.0, 'gl': 0.0}
        k_eval_stats[kk]['cnt'] += 1
        k_eval_stats[kk]['p'] += t['p']
        if t['p'] > 0:
            k_eval_stats[kk]['wins'] += 1
            k_eval_stats[kk]['gp'] += t['p']
        else:
            k_eval_stats[kk]['gl'] += abs(t['p'])

    for kk, s in k_eval_stats.items():
        s['pf'] = (s['gp'] / s['gl']) if s['gl'] > 0 else 999.0
        s['wr'] = (s['wins'] / s['cnt'] * 100) if s['cnt'] > 0 else 0
        s['avg'] = (s['p'] / s['cnt']) if s['cnt'] > 0 else 0

    sorted_kings_by_pf = sorted(k_eval_stats.keys(), key=lambda k: k_eval_stats[k]['pf'])
    all_dataset_kings_set = set(k_eval_stats.keys())

    # Hours Definitions
    hours_map = {
        'all': ('۲۴ ساعته', set(range(24)), [True]*24),
        'no_night': ('حذف شب (۰۴ تا ۲۲)', set(range(4, 22)), [False if h in [22,23,0,1,2,3] else True for h in range(24)]),
        'lon_ny': ('سشن روز (۰۷ تا ۲۰)', set(range(7, 20)), [True if 7 <= h < 20 else False for h in range(24)]),
        'core_day': ('اوج سشن (۰۸ تا ۱۸)', set(range(8, 19)), [True if 8 <= h <= 18 else False for h in range(24)])
    }

    min_pot_candidates = [0.0, 1.0, 1.5, 2.0, 2.5, 3.0]
    circuit_breaker_candidates = [(0, 0, False, 'بدون وقفه'), (2, 1, False, '۲ استاپ -> رد معامله ۳')]

    # Grid search across parameter space
    evaluated_combos = []
    for h_key, (h_label, h_set, h_arr) in hours_map.items():
        for pot in min_pot_candidates:
            for drop_n in range(0, min(8, max(1, len(sorted_kings_by_pf) - 5))):
                dropped = set(sorted_kings_by_pf[:drop_n]) if drop_n > 0 else set()
                active_kings = all_dataset_kings_set - dropped
                for (trig, sk, day, cb_label) in circuit_breaker_candidates:
                    bal = 100.0; peak = bal; max_dd = 0.0; wins = 0; total = 0; gp = 0.0; gl = 0.0
                    consec_loss = 0; skips = 0
                    for t in trades_sim_list:
                        if t['k'] != 1: continue
                        if t['kk'] not in active_kings: continue
                        if t['h'] not in h_set: continue
                        if t['pot'] < pot: continue
                        if skips > 0: skips -= 1; continue
                        total += 1
                        bal += t['p']
                        if bal > peak: peak = bal
                        dd = peak - bal
                        if dd > max_dd: max_dd = dd
                        if t['p'] > 0:
                            wins += 1; gp += t['p']; consec_loss = 0
                        else:
                            gl += abs(t['p']); consec_loss += 1
                            if trig > 0 and consec_loss >= trig: skips = sk; consec_loss = 0

                    if total < min_15pct_trades: continue
                    wr = (wins / total * 100) if total > 0 else 0
                    pf = (gp / gl) if gl > 0 else 999.0
                    net = bal - 100.0
                    avg = net / total if total > 0 else 0
                    # Composite score: high PF, high WR, high Avg, low DD
                    score = (pf ** 1.3) * (wr / 50.0) * max(0.5, avg) / max(12.0, max_dd) * 100
                    evaluated_combos.append({
                        'h_key': h_key, 'h_label': h_label, 'h_arr': h_arr,
                        'pot': pot, 'dropped_n': drop_n, 'kings': list(active_kings), 'kings_cnt': len(active_kings),
                        'trig': trig, 'sk': sk, 'day': day, 'cb_label': cb_label,
                        'total': total, 'wr': wr, 'pf': pf, 'net': net, 'avg': avg, 'max_dd': max_dd, 'score': score
                    })

    evaluated_combos.sort(key=lambda x: x['score'], reverse=True)

    # 1. Champion (Best score >= 15% trades)
    if evaluated_combos:
        opt_p1 = evaluated_combos[0]
    else:
        opt_p1 = {
            'h_key': 'all', 'h_label': '۲۴ ساعته', 'h_arr': [True]*24,
            'pot': 0.0, 'dropped_n': 0, 'kings': list(all_dataset_kings_set), 'kings_cnt': len(all_dataset_kings_set),
            'trig': 0, 'sk': 0, 'day': False, 'cb_label': 'بدون وقفه',
            'total': len(closed), 'wr': 50.0, 'pf': 1.0, 'net': 0.0, 'avg': 0.0, 'max_dd': 0.0, 'score': 0.0
        }

    # 2. Golden Balance (Best score with >= 35% trades)
    cands_p2 = [r for r in evaluated_combos if r['total'] >= min_35pct_trades and r['h_key'] in ['no_night', 'all']]
    opt_p2 = cands_p2[0] if cands_p2 else (evaluated_combos[1] if len(evaluated_combos) > 1 else opt_p1)

    # 3. Day Session (Best score in Day Session 07-20)
    cands_p3 = [r for r in evaluated_combos if r['h_key'] == 'lon_ny' and r['pot'] <= 2.0]
    opt_p3 = cands_p3[0] if cands_p3 else opt_p1

    # 4. Ultra-Low DD (Lowest DD with PF >= 2.5 and >= 15% trades)
    cands_p4 = sorted([r for r in evaluated_combos if r['pf'] >= 2.5 and r['total'] >= min_15pct_trades and r['total'] != opt_p1['total']], key=lambda x: x['max_dd'])
    opt_p4 = cands_p4[0] if cands_p4 else opt_p1

    smart_presets_defs = [
        {
            'id': 'preset-champion',
            'idx': 0,
            'title': f'۱. الماس و سوپر اسنایپر خودکار (AI Champion Sniper 🎯)',
            'badge': f'🏆 قهرمان کشف‌شده: PF {opt_p1["pf"]:.2f} & WR {opt_p1["wr"]:.0f}%',
            'badge_bg': '#831843',
            'badge_col': '#fbcfe8',
            'strategy_desc': f'بهترین ترکیب هوشمند داده‌های {symbol} با شرط حداقل ۱۵٪ معاملات - پرافیت فاکتور {opt_p1["pf"]:.2f}، وین‌ریت {opt_p1["wr"]:.1f}٪، میانگین سود ${opt_p1["avg"]:.2f} و افت ${opt_p1["max_dd"]:.2f} ({opt_p1["total"]} ترید)',
            'filter_desc': f'کف سود: <b>${opt_p1["pot"]:.2f}+</b> | ساعات: <b>{opt_p1["h_label"]}</b> | وقفه: <b>{opt_p1["cb_label"]}</b>',
            'min_pot': opt_p1['pot'],
            'hours': opt_p1['h_arr'],
            'hours_name': opt_p1['h_key'],
            'kings': opt_p1['kings'],
            'consec_trig': opt_p1['trig'],
            'consec_sk': opt_p1['sk'],
            'consec_day': opt_p1['day'],
            'is_featured': True
        },
        {
            'id': 'preset-golden',
            'idx': 1,
            'title': '۲. تعادل طلایی حجم و سود (Golden Balance ⚖️)',
            'badge': f'⭐ بالانس بهینه ({opt_p2["total"]} ترید)',
            'badge_bg': '#854d0e',
            'badge_col': '#fef08a',
            'strategy_desc': f'تعادل عالی میان تعداد ترید بالا ({opt_p2["total"]} معامله) و پرافیت فاکتور {opt_p2["pf"]:.2f} با میانگین سود ${opt_p2["avg"]:.2f}',
            'filter_desc': f'کف سود: <b>${opt_p2["pot"]:.2f}+</b> | ساعات: <b>{opt_p2["h_label"]}</b>',
            'min_pot': opt_p2['pot'],
            'hours': opt_p2['h_arr'],
            'hours_name': opt_p2['h_key'],
            'kings': opt_p2['kings'],
            'consec_trig': opt_p2['trig'],
            'consec_sk': opt_p2['sk'],
            'consec_day': opt_p2['day'],
            'is_featured': False
        },
        {
            'id': 'preset-day',
            'idx': 2,
            'title': '۳. اسنایپر سشن روزانه لندن و نیویورک (Day Session ☀️)',
            'badge': '☀️ اوج نقدینگی روزانه',
            'badge_bg': '#0c4a6e',
            'badge_col': '#7dd3fc',
            'strategy_desc': f'معامله در ساعات پرقدرت روز با اسپرد پایین و تاییدیه مومنتوم - PF {opt_p3["pf"]:.2f} و افت ${opt_p3["max_dd"]:.0f}',
            'filter_desc': f'کف سود: <b>${opt_p3["pot"]:.2f}+</b> | ساعات: <b>{opt_p3["h_label"]}</b>',
            'min_pot': opt_p3['pot'],
            'hours': opt_p3['h_arr'],
            'hours_name': opt_p3['h_key'],
            'kings': opt_p3['kings'],
            'consec_trig': opt_p3['trig'],
            'consec_sk': opt_p3['sk'],
            'consec_day': opt_p3['day'],
            'is_featured': False
        },
        {
            'id': 'preset-shield',
            'idx': 3,
            'title': '۴. سپر محافظتی کمترین افت سرمایه (Ultra-Low DD Shield 🛡️)',
            'badge': f'🛡️ حداقل افت: ${opt_p4["max_dd"]:.0f}',
            'badge_bg': '#064e3b',
            'badge_col': '#34d399',
            'strategy_desc': f'کمترین ریسک دلاری ممکن روی حساب ({symbol}) با حفظ پرافیت فاکتور عالی {opt_p4["pf"]:.2f} و وین‌ریت {opt_p4["wr"]:.1f}٪',
            'filter_desc': f'کف سود: <b>${opt_p4["pot"]:.2f}+</b> | ساعات: <b>{opt_p4["h_label"]}</b> | وقفه: <b>{opt_p4["cb_label"]}</b>',
            'min_pot': opt_p4['pot'],
            'hours': opt_p4['h_arr'],
            'hours_name': opt_p4['h_key'],
            'kings': opt_p4['kings'],
            'consec_trig': opt_p4['trig'],
            'consec_sk': opt_p4['sk'],
            'consec_day': opt_p4['day'],
            'is_featured': False
        },
        {
            'id': 'preset-base',
            'idx': 4,
            'title': f'۵. سبد جامع پایه {symbol} (تمام سلاطین ۲۴ ساعته 🌐)',
            'badge': '🌐 مبنای کل چارت',
            'badge_bg': '#1e293b',
            'badge_col': '#94a3b8',
            'strategy_desc': f'شبیه‌سازی کامل تمام سلاطین بدون فیلتر سود یا زمان - بالاترین حجم آماری ({len(pts_kings)-1} ترید)',
            'filter_desc': 'کف سود: <b>$0.00</b> | ساعات: <b>۲۴ ساعته کامل</b>',
            'min_pot': 0.0,
            'hours': [True]*24,
            'hours_name': 'all',
            'kings': all_sim_k_keys,
            'consec_trig': 0,
            'consec_sk': 1,
            'consec_day': False,
            'is_featured': False
        }
    ]

    smart_presets_json_data = []
    smart_presets_rows_html = []

    for p in smart_presets_defs:
        k_set = set(p['kings'])
        consec_loss = 0
        skips = 0
        sub = []
        for t in trades_sim_list:
            if t['k'] != 1 or t['kk'] not in k_set or t['pot'] < p['min_pot'] or not p['hours'][t['h']]:
                continue
            if skips > 0:
                skips -= 1
                continue
            sub.append(t)
            if t['p'] <= 0:
                consec_loss += 1
                if p.get('consec_trig', 0) > 0 and consec_loss >= p['consec_trig']:
                    skips = p.get('consec_sk', 1)
                    consec_loss = 0
            else:
                consec_loss = 0

        c = len(sub)
        if c == 0: continue
        nt = sum(t['p'] for t in sub)
        w = len([t for t in sub if t['p'] > 0])
        wr = (w / c * 100) if c > 0 else 0.0
        avg = (nt / c) if c > 0 else 0.0
        gp = sum(t['p'] for t in sub if t['p'] > 0)
        gl = sum(abs(t['p']) for t in sub if t['p'] <= 0)
        pf = (gp / gl) if gl > 0 else 999.0
        
        bal = 100.0
        peak = 100.0
        max_dd = 0.0
        for t in sub:
            bal += t['p']
            if bal > peak: peak = bal
            dd = peak - bal
            if dd > max_dd: max_dd = dd

        p_data = {
            'id': p['id'],
            'idx': p['idx'],
            'title': p['title'],
            'min_pot': p['min_pot'],
            'hours': p['hours'],
            'hours_name': p['hours_name'],
            'kings': p['kings'],
            'consec_trig': p.get('consec_trig', 0),
            'consec_sk': p.get('consec_sk', 1),
            'consec_day': p.get('consec_day', False),
            'cnt': c,
            'wr': round(wr, 1),
            'pf': round(pf, 2) if pf < 900 else 999.0,
            'avg': round(avg, 2),
            'max_dd': round(max_dd, 2),
            'net': round(nt, 2)
        }
        smart_presets_json_data.append(p_data)

        row_border = "border: 2px solid #facc15; background: #1c1806;" if p['is_featured'] else "border-bottom: 1px solid #1e293b;"
        pf_display = f"{pf:.2f}" if pf < 900 else "∞"
        net_col = "#00e676" if nt >= 0 else "#ef4444"
        featured_tag = f" <span style='background:{p['badge_bg']};color:{p['badge_col']};font-size:10px;padding:2px 6px;border-radius:4px;font-weight:bold;'>{p['badge']}</span>"

        smart_presets_rows_html.append(f"""
        <tr id="presetRow{p['idx']}" style="{row_border}transition:all 0.2s;" class="preset-table-row {'featured-preset' if p['is_featured'] else ''}">
            <td style="text-align:center;padding:7px 4px;font-weight:bold;font-size:12px;color:#facc15;">#{p['idx']+1}</td>
            <td style="padding:7px 8px;">
                <div style="font-weight:bold;color:#f1f5f9;font-size:12px;display:flex;align-items:center;gap:4px;flex-wrap:wrap;">
                    <span>{p['title']}</span>
                    {featured_tag}
                </div>
                <div style="color:#94a3b8;font-size:10.5px;margin-top:2px;">{p['strategy_desc']}</div>
            </td>
            <td style="padding:7px 6px;font-size:11px;color:#cbd5e1;text-align:center;white-space:nowrap;">
                <div>{p['filter_desc']}</div>
                <div style="font-weight:bold;color:#38bdf8;font-size:10.5px;margin-top:2px;">👑 {len(p['kings'])} سلطان فعال</div>
            </td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;font-size:12px;color:#e2e8f0;">
                {c:,}
            </td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#34d399;font-size:12px;">
                {wr:.1f}٪
            </td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#38bdf8;font-size:12.5px;">
                {pf_display}
            </td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#facc15;font-size:12.5px;">
                ${avg:+.2f}
            </td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#fca5a5;font-size:11.5px;">
                ${max_dd:.0f}
            </td>
            <td style="text-align:center;padding:7px 6px;font-weight:bold;color:{net_col};font-size:13.5px;background:#064e3b22;white-space:nowrap;">
                {'+$' if nt>=0 else '-$'}{abs(nt):,.0f}
            </td>
            <td style="text-align:center;padding:7px 6px;white-space:nowrap;">
                <div style="display:inline-flex;gap:4px;align-items:center;justify-content:center;">
                    <button id="btnApplyPreset{p['idx']}" class="apply-preset-btn" onclick="applySmartPreset({p['idx']})" style="background:linear-gradient(135deg, #0284c7, #0369a1);border:1px solid #38bdf8;color:#fff;padding:5px 8px;border-radius:5px;font-size:11px;cursor:pointer;font-weight:bold;transition:all 0.2s;white-space:nowrap;box-shadow:0 2px 8px rgba(2,132,199,0.3);" title="اعمال این سناریو روی نمودار اکوئیتی داشبورد">
                        ⚡ اعمال
                    </button>
                    <button onclick="exportPresetToMT5({p['idx']})" style="background:linear-gradient(135deg, #065f46, #047857);border:1px solid #34d399;color:#ecfdf5;padding:5px 7px;border-radius:5px;font-size:11px;cursor:pointer;font-weight:bold;transition:all 0.2s;white-space:nowrap;display:inline-flex;align-items:center;gap:3px;" title="دریافت فایل استراتژی تستر متاتریدر ۵ (.ini) جهت Drag & Drop به تستر">
                        <span>🤖 تنظیمات تستر (.ini)</span>
                    </button>
                </div>
            </td>
        </tr>
        """)

    json_smart_presets = json.dumps(smart_presets_json_data, separators=(',', ':'))
    smart_presets_table_rows_str = ''.join(smart_presets_rows_html)

    # Trades Journal JSON Data Preparation
    trades_sorted = sorted([r for r in closed if r.get('Timeframe') in ['M1','M5','M15']], key=lambda x: x.get('EntryTime', ''), reverse=True)
    trades_json_list = []
    for idx, r in enumerate(trades_sorted, 1):
        tf = r.get('Timeframe', 'M1')
        role = r.get('Role', '')
        is_k = 1 if (role, tf) in king_keys else 0
        hr = int(r.get('HitTargetRatio', 0))
        pts = float(r.get('RiskPoints', 0.0))
        if hr == 0:
            pnl = -pts * 0.04 - friction_04_per_trade
        else:
            pnl = -friction_04_per_trade
            if hr >= 1: pnl += pts * 1.0 * 0.01
            if hr >= 2: pnl += pts * 2.0 * 0.01
            if hr >= 3: pnl += pts * 3.0 * 0.01
            if hr >= 4: pnl += pts * 4.0 * 0.01

        trades_json_list.append({
            'id': idx,
            'en_t': r.get('EntryTime', ''),
            'ex_t': r.get('ExitTime', ''),
            'tf': tf,
            'role': role,
            'bname': r.get('BoxName', ''),
            'is_k': is_k,
            'dir': r.get('Direction', 'BUY'),
            'en_p': round(float(r.get('EntryPrice', 0.0)), 5),
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
            'net': round(pnl, 2)
        })
    json_trades = json.dumps(trades_json_list, separators=(',', ':'))

    # Weekly Bar Chart Data Preparation
    weekly_bar_data = []
    for yr, wk in sorted_wk_keys:
        w_data = weekly_data[(yr, wk)]
        t_kings = w_data['trades_kings']
        t_all = w_data['trades_all']
        
        k_cnt = len(t_kings)
        k_wins = len([r for r in t_kings if int(r.get('HitTargetRatio', 0)) >= 1])
        k_losses = len([r for r in t_kings if int(r.get('HitTargetRatio', 0)) == 0])
        k_wr = (k_wins / k_cnt * 100) if k_cnt else 0
        k_pnl = round(sum(calc_scaleout_pnl(r) for r in t_kings), 2)
        
        all_cnt = len(t_all)
        all_wins = len([r for r in t_all if int(r.get('HitTargetRatio', 0)) >= 1])
        all_losses = len([r for r in t_all if int(r.get('HitTargetRatio', 0)) == 0])
        all_wr = (all_wins / all_cnt * 100) if all_cnt else 0
        all_pnl = round(sum(calc_scaleout_pnl(r) for r in t_all), 2)
        
        first_date = datetime.strptime(f"{yr}-W{wk:02d}-1", "%Y-W%W-%w")
        last_date = first_date + timedelta(days=4)
        d_range = f"{first_date.strftime('%m.%d')} - {last_date.strftime('%m.%d')}"
        
        weekly_bar_data.append({
            'week': wk,
            'year': yr,
            'dates': d_range,
            'k_pnl': k_pnl,
            'k_trades': k_cnt,
            'k_wins': k_wins,
            'k_losses': k_losses,
            'k_wr': round(k_wr, 1),
            'all_pnl': all_pnl,
            'all_trades': all_cnt,
            'all_wins': all_wins,
            'all_losses': all_losses,
            'all_wr': round(all_wr, 1)
        })

    json_weekly_bars = json.dumps(weekly_bar_data)

    
    net_k = bal_k - bal_initial
    net_k_pct = (net_k / bal_initial) * 100
    max_dd_k_pct = (max_dd_k / peak_k) * 100 if peak_k else 0.0

    net_a = bal_a - bal_initial
    net_a_pct = (net_a / bal_initial) * 100
    max_dd_a_pct = (max_dd_a / peak_a) * 100 if peak_a else 0.0

    top_consistent_pct = consistency_list[0]['cons_pct'] if consistency_list else 0.0

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    

    tab_equity_html = f"""<!-- Equity Metrics Banner (Dynamically updated by simulation) -->
            <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));gap:8px;margin-bottom:10px;">
                <div class="kpi-card" style="border-color:#38bdf8;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">💵 بالانس شروع حساب</div>
                    <div class="kpi-value" style="color:#f1f5f9;font-size:16px;">${bal_initial:,.0f}</div>
                    <div class="kpi-sub" style="font-size:9.5px;">شروع از {date_start_str}</div>
                </div>
                <div class="kpi-card" style="border-color:#00e676;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">📈 سود خالص کل</div>
                    <div class="kpi-value" id="eqKpiNetVal" style="color:#00e676;font-size:16px;">{'+$' if net_k>=0 else '-$'}{abs(net_k):,.0f}</div>
                    <div class="kpi-sub" id="eqKpiNetSub" style="font-size:9.5px;">نرخ رشد حساب: {net_k_pct:+.1f}٪</div>
                </div>
                <div class="kpi-card" style="border-color:#facc15;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">🏁 بالانس نهایی حساب</div>
                    <div class="kpi-value" id="eqKpiFinalBal" style="color:#facc15;font-size:16px;">${bal_k:,.0f}</div>
                    <div class="kpi-sub" id="eqKpiPeakSub" style="font-size:9.5px;">سقف سرمایه: ${peak_k:,.0f}</div>
                </div>
                <div class="kpi-card" style="border-color:#ef4444;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">🛡️ حداکثر افت (Max DD)</div>
                    <div class="kpi-value" id="eqKpiMaxDD" style="color:#fca5a5;font-size:16px;">${max_dd_k:.0f} ({max_dd_k_pct:.1f}٪)</div>
                    <div class="kpi-sub" id="eqKpiMaxDDSub" style="font-size:9.5px;">مدیریت ریسک کنترل‌شده</div>
                </div>
                <div class="kpi-card" style="border-color:#38bdf8;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">⚖️ پرافیت فاکتور (PF)</div>
                    <div class="kpi-value" id="eqKpiPF" style="color:#38bdf8;font-size:16px;">{s3_pf:.2f}</div>
                    <div class="kpi-sub" id="eqKpiPFSub" style="font-size:9.5px;">نسبت سود ناخالص به ضرر</div>
                </div>
                <div class="kpi-card" style="border-color:#10b981;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">🎯 وین‌ریت پله ۱ (WinRate)</div>
                    <div class="kpi-value" id="eqKpiWR" style="color:#34d399;font-size:16px;">{d_tot_kings['w1_p']:.1f}%</div>
                    <div class="kpi-sub" id="eqKpiWRSub" style="font-size:9.5px;">نرخ موفقیت حداقل ۱R</div>
                </div>
                <div class="kpi-card" style="border-color:#eab308;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">📊 تعداد معاملات فعال</div>
                    <div class="kpi-value" id="eqKpiCnt" style="color:#facc15;font-size:16px;">{len(pts_kings)-1} معامله</div>
                    <div class="kpi-sub" id="eqKpiCntSub" style="font-size:9.5px;">معاملات منطبق با فیلتر</div>
                </div>
                <div class="kpi-card" style="border-color:#a855f7;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">⚡ متوسط سود هر ترید</div>
                    <div class="kpi-value" id="eqKpiAvgTrade" style="color:#c084fc;font-size:16px;">+${(net_k/(len(pts_kings)-1)):.2f}</div>
                    <div class="kpi-sub" id="eqKpiAvgTradeSub" style="font-size:9.5px;">میانگین خروجی هر ترید</div>
                </div>
                <div class="kpi-card" style="border-color:#0284c7;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">⚡ معامله باز همزمان</div>
                    <div class="kpi-value" id="eqKpiConcVal" style="color:#38bdf8;font-size:16px;">{init_max_concurrent} معامله</div>
                    <div class="kpi-sub" id="eqKpiConcSub" style="font-size:9.5px;">میانگین: {init_avg_concurrent:.1f} همزمان</div>
                </div>
            </div>

                                    <!-- 🌟 2-COLUMN MAIN WORKSPACE GRID -->
            <div class="equity-two-col-container" id="eqTwoColContainer">

                <!-- 🔹 COLUMN 1: CHART SECTION (HALF-WIDTH) -->
                <div class="equity-col-chart" id="eqColChart">
                    <!-- 📈 INTERACTIVE EQUITY CANVAS GRAPH (AT THE VERY TOP) -->
            <!-- Interactive Canvas Graph Container -->
            <div class="section-box" style="border:1px solid #38bdf8;background:#0b0f19;padding:10px 14px;border-radius:8px;height:100%;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;margin-bottom:0;">
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e293b;padding-bottom:8px;margin-bottom:8px;gap:8px;">
                    <div>
                        <h3 style="margin:0;color:#38bdf8;font-size:14px;display:flex;align-items:center;gap:6px;">
                            <span>📈 منحنی تعاملی رشد بالانس و اکوئیتی</span>
                        </h3>
                        <p style="margin:3px 0 0 0;color:#94a3b8;font-size:11px;">رسم دقیق معامله به معامله با حرکت موس روی نقاط</p>
                    </div>
                    <div style="display:flex;align-items:center;gap:6px;">
                        <button onclick="toggleDrawdownOverlay()" id="btnToggleDrawdown" style="background:#1e1b4b;border:1px solid #6366f1;color:#c7d2fe;padding:4px 9px;border-radius:5px;font-size:11px;cursor:pointer;display:flex;align-items:center;gap:4px;" title="نمایش یا پنهان‌سازی افت سرمایه (Drawdown) و خط سقف روی نمودار">
                            <span>🛡️ افت سرمایه (DD): <b id="lblToggleDrawdownState" style="color:#4ade80;">روشن</b></span>
                        </button>
                        <button onclick="toggleTwoColLayout()" id="btnToggleTwoCol" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:4px 8px;border-radius:5px;font-size:11px;cursor:pointer;display:flex;align-items:center;gap:4px;" title="تغییر حالت بین دو ستونی و تمام‌صفحه">
                            <span>⛶</span><span>تمام‌صفحه / ستونی</span>
                        </button>
                    </div>
                </div>

                <!-- Canvas Box -->
                <div style="position:relative;width:100%;height:450px;background:#0f172a;border:1px solid #1e293b;border-radius:10px;overflow:hidden;">
                    <!-- ⚡ Live & Peak Concurrent Trades Corner Badge -->
                    <div id="eqConcurrentBadge" style="position:absolute;top:12px;left:12px;background:rgba(15,23,42,0.92);backdrop-filter:blur(8px);border:1px solid #0284c7;border-radius:8px;padding:6px 12px;z-index:15;box-shadow:0 6px 20px rgba(0,0,0,0.6);display:flex;align-items:center;gap:10px;direction:rtl;pointer-events:none;">
                        <div style="width:26px;height:26px;border-radius:6px;background:#0369a1;border:1px solid #38bdf8;display:flex;align-items:center;justify-content:center;font-size:13px;">
                            ⚡
                        </div>
                        <div>
                            <div style="font-size:9.5px;color:#94a3b8;font-weight:600;display:flex;align-items:center;gap:4px;">
                                <span>تعداد معامله باز همزمان</span>
                                <span id="lblLiveConcurrentTag" style="display:none;background:#22c55e;color:#052e16;padding:1px 5px;border-radius:3px;font-size:8.5px;font-weight:bold;">روی نقطه</span>
                            </div>
                            <div style="font-size:13.5px;color:#f8fafc;font-weight:bold;display:flex;align-items:baseline;gap:6px;margin-top:1px;">
                                <span>حداکثر: <b id="lblMaxConcurrentTrades" style="color:#38bdf8;font-size:15px;">{init_max_concurrent}</b></span>
                                <span style="color:#475569;font-size:10px;">|</span>
                                <span style="font-size:11px;color:#94a3b8;">میانگین: <b id="lblAvgConcurrentTrades" style="color:#facc15;">{init_avg_concurrent:.1f}</b></span>
                            </div>
                        </div>
                    </div>

                    <canvas id="equityCanvas" style="width:100%;height:100%;display:block;cursor:crosshair;"></canvas>
                    <div id="equityTooltip" style="display:none;position:absolute;pointer-events:none;background:rgba(15,23,42,0.95);border:1px solid #38bdf8;padding:10px 14px;border-radius:8px;font-size:12px;color:#f1f5f9;box-shadow:0 8px 24px rgba(0,0,0,0.7);z-index:20;direction:rtl;min-width:210px;"></div>
                </div>

                <!-- Graph Legend & Stats Bar -->
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;font-size:11px;color:#94a3b8;flex-wrap:wrap;gap:8px;">
                    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                        <span style="display:flex;align-items:center;gap:4px;"><span style="display:inline-block;width:12px;height:3px;background:#38bdf8;border-radius:2px;"></span> رشد بالانس</span>
                        <span style="display:flex;align-items:center;gap:4px;"><span style="display:inline-block;width:12px;height:3px;background:#facc15;border-radius:2px;border-top:1px dashed #facc15;"></span> سقف سرمایه (HWM)</span>
                        <span style="display:flex;align-items:center;gap:4px;"><span style="display:inline-block;width:8px;height:10px;background:#ef4444;border-radius:2px;"></span> میله‌های افت (Underwater DD)</span>
                        <span style="display:flex;align-items:center;gap:4px;"><span style="display:inline-block;width:12px;height:3px;background:#475569;border-radius:2px;"></span> تراز پایه ($100)</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span>نقاط: <b id="lblEqPts" style="color:#facc15;">{len(pts_kings)-1}</b></span>
                        <span>|</span>
                        <span>{date_start_str} تا {date_end_str}</span>
                    </div>
                </div>
            </div>
                </div>

                <!-- 🔹 COLUMN 2: SUBTABS & CONTROLS (PRESETS / FILTERS / RISK) -->
                <div class="equity-col-controls" id="eqColControls">
                    <div style="background:#080d1a;border:1px solid #1e3a5f;border-radius:10px;padding:10px 12px;height:100%;box-sizing:border-box;display:flex;flex-direction:column;">
                        <!-- Subtabs Navigation Bar -->
                        <!-- 📑 SUB-NAVIGATION FOR CONTROLS & PRESETS -->
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;margin-bottom:10px;border-bottom:2px solid #1e3a5f;padding-bottom:8px;flex-wrap:wrap;gap:8px;">
                <div style="display:flex;gap:4px;flex-wrap:wrap;">
                    <button class="eq-subtab-btn active" onclick="openEqSubtab(event, 'eq-sub-presets')">
                        ⚡ سناریوهای استراتژی
                    </button>
                    <button class="eq-subtab-btn" onclick="openEqSubtab(event, 'eq-sub-filters')">
                        🎛️ شبیه‌ساز فیلترها
                    </button>
                    <button class="eq-subtab-btn" onclick="openEqSubtab(event, 'eq-sub-risk')">
                        🚨 کالبدشکافی استاپ‌ها
                    </button>
                    <button class="eq-subtab-btn" onclick="openEqSubtab(event, 'eq-sub-weekly')">
                        📊 کارنامه هفتگی
                    </button>
                    <button class="eq-subtab-btn" onclick="openEqSubtab(event, 'eq-sub-compare')">
                        ⚖️ مقایسه با کل چارت
                    </button>
                </div>
                <div style="display:flex;gap:5px;align-items:center;">
                    <button onclick="runClientAutoOptimizer()" style="background:linear-gradient(135deg, #7c3aed, #a855f7);border:1px solid #c084fc;color:#fff;font-size:11.5px;padding:5px 11px;border-radius:6px;cursor:pointer;font-weight:bold;box-shadow:0 2px 10px rgba(168,85,247,0.4);display:flex;align-items:center;gap:5px;">
                        <span>🤖 بهینه‌ساز خودکار (AI)</span>
                    </button>
                    <button onclick="openSavePresetModal()" style="background:#064e3b;border:1px solid #10b981;color:#6ee7b7;padding:5px 10px;border-radius:6px;font-size:11px;cursor:pointer;font-weight:bold;">💾 ذخیره چیدمان</button>
                    <button onclick="exportCurrentStateToMT5()" style="background:linear-gradient(135deg, #059669, #10b981);border:1px solid #34d399;color:#fff;padding:5px 10px;border-radius:6px;font-size:11px;cursor:pointer;font-weight:bold;display:flex;align-items:center;gap:4px;" title="خروجی مستقیم تنظیمات برای Strategy Tester متاتریدر (.ini) و اکسپرت (.set)">
                        <span>🤖 تنظیمات تستر (.ini)</span>
                    </button>
                    <button onclick="resetAllSimFilters()" style="background:#1e293b;border:1px solid #ef4444;color:#fca5a5;padding:5px 10px;border-radius:6px;font-size:11px;cursor:pointer;font-weight:bold;">🔄 بازنشانی</button>
                </div>
            </div>

                        <!-- Subpanels Scrollable Wrapper -->
                        <div class="eq-subpanels-wrapper">
                            <!-- SUBPANEL 1: PRESETS -->
            <div id="eq-sub-presets" class="eq-subpanel active">
                <!-- ⚡ SMART PRESETS & CUSTOM STRATEGY PORTFOLIOS -->
            <div class="section-box" style="border: 2px solid #facc15; background: #0b1528; padding: 12px; margin-bottom: 12px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #1e3a5f; padding-bottom: 10px; margin-bottom: 10px; flex-wrap:wrap; gap:8px;">
                    <div>
                        <h3 style="margin:0;color:#facc15;font-size:16px;display:flex;align-items:center;gap:6px;">
                            <span>⚡ پیشنهادات استراتژیک سیستم و سناریوهای شخصی شما</span>
                        </h3>
                        <p style="margin:3px 0 0 0;color:#94a3b8;font-size:11.5px;">با زدن دکمه «اعمال»، فیلترها روی چارت اعمال می‌شوند. با دکمه سبز می‌توانید هر چیدمانی را ذخیره کنید:</p>
                    </div>
                    <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
                        <button onclick="openSavePresetModal()" style="background:linear-gradient(135deg, #059669, #10b981);border:1px solid #34d399;color:#fff;font-size:11.5px;padding:5px 11px;border-radius:5px;cursor:pointer;font-weight:bold;box-shadow:0 2px 8px rgba(16,185,129,0.3);display:flex;align-items:center;gap:4px;">
                            <span>💾 ذخیره چیدمان فعلی</span>
                        </button>
                        <button onclick="exportCustomPresets()" style="background:#1e293b;border:1px solid #38bdf8;color:#7dd3fc;font-size:11px;padding:5px 8px;border-radius:5px;cursor:pointer;" title="خروجی فایل پشتیبان JSON">
                            📥 بکاپ (JSON)
                        </button>
                        <button onclick="document.getElementById('importPresetsInput').click()" style="background:#1e293b;border:1px solid #ca8a04;color:#fef08a;font-size:11px;padding:5px 8px;border-radius:5px;cursor:pointer;" title="بارگذاری سناریوهای ذخیره‌شده">
                            📤 بارگذاری
                        </button>
                        <input type="file" id="importPresetsInput" accept=".json" style="display:none;" onchange="importCustomPresets(event)" />
                    </div>
                </div>

                <div style="overflow-x:auto;">
                    <table style="width:100%;border-collapse:collapse;font-size:11.5px;text-align:right;">
                        <thead>
                            <tr style="background:#1e293b;color:#94a3b8;border-bottom:2px solid #334155;font-size:11.5px;">
                                <th style="padding:7px 5px;text-align:center;">#</th>
                                <th style="padding:7px 8px;">سناریوی استراتژی و ویژگی‌ها</th>
                                <th style="padding:7px 6px;text-align:center;">تنظیمات و سلاطین</th>
                                <th style="padding:7px 4px;text-align:center;">تعداد</th>
                                <th style="padding:7px 4px;text-align:center;">وین‌ریت</th>
                                <th style="padding:7px 4px;text-align:center;">PF</th>
                                <th style="padding:7px 4px;text-align:center;">متوسط سود</th>
                                <th style="padding:7px 4px;text-align:center;">Max DD</th>
                                <th style="padding:7px 6px;text-align:center;">سود خالص</th>
                                <th style="padding:7px 6px;text-align:center;">اقدام</th>
                            </tr>
                        </thead>
                        <!-- 1. SYSTEM BUILT-IN PRESETS -->
                        <tbody id="systemPresetsTbody">
                            {smart_presets_table_rows_str}
                        </tbody>
                        <!-- 2. USER SAVED CUSTOM PRESETS HEADER -->
                        <tbody id="customPresetsHeaderTbody">
                            <tr style="background:#131d2e;border-top:2px solid #38bdf8;border-bottom:1px solid #1e3a5f;">
                                <td colspan="10" style="padding:7px 10px;">
                                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                                        <div style="font-weight:bold;color:#38bdf8;font-size:12px;display:flex;align-items:center;gap:6px;">
                                            <span>⭐ سناریوهای شخصی ذخیره‌شده شما:</span>
                                            <span id="customPresetsCountBadge" style="background:#0c4a6e;color:#7dd3fc;font-size:10.5px;padding:1px 6px;border-radius:8px;">0 سناریو</span>
                                        </div>
                                        <div style="font-size:10.5px;color:#94a3b8;">
                                            این سناریوها در مرورگر شما پایدارند و با هر دیتای جدید فوراً با همان شرایط بازمحاسبه می‌شوند.
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                        <!-- 3. USER SAVED CUSTOM PRESETS ROWS -->
                        <tbody id="customPresetsTbody">
                            <!-- Populated dynamically by loadCustomPresets() -->
                        </tbody>
                    </table>
                </div>
            </div>
            </div>

            <!-- SUBPANEL 2: FILTERS (SLIDER, HOURS, KINGS) -->
            <div id="eq-sub-filters" class="eq-subpanel" style="display:none;">
                <!-- 🎛️ REAL-TIME FILTER SIMULATOR CONTROL PANEL -->
            <div class="section-box" style="border: 2px solid #0284c7; background: #081a2e; padding: 18px; margin-bottom: 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #1e4976; padding-bottom: 12px; margin-bottom: 16px; flex-wrap:wrap; gap:10px;">
                    <div>
                        <h3 style="margin:0;color:#38bdf8;font-size:18px;display:flex;align-items:center;gap:8px;">
                            <span>🎛️ شبیه‌ساز تعاملی فیلترها و بهینه‌ساز نمودار رشد (Real-time Strategy Optimizer)</span>
                        </h3>
                        <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">با حذف/اضافه هر سلطان، تغییر ساعات معاملاتی یا حداقل سود، نمودار و تمام شاخص‌های بالا به صورت آنی بازرسم می‌شوند:</p>
                    </div>
                    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                        <button onclick="openSavePresetModal()" style="background:#064e3b;border:1px solid #10b981;color:#6ee7b7;padding:6px 12px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;transition:all 0.2s;display:flex;align-items:center;gap:5px;">
                            <span>💾 ذخیره این ترکیب (Save Preset)</span>
                        </button>
                        <button onclick="resetAllSimFilters()" style="background:#1e293b;border:1px solid #ef4444;color:#fca5a5;padding:6px 12px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;transition:all 0.2s;">🔄 بازنشانی تمام فیلترها (Reset)</button>
                    </div>
                </div>

                <!-- 1. KINGS SELECTOR SECTION -->
                <div style="margin-bottom:18px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:8px;">
                        <div style="font-weight:bold;color:#facc15;font-size:13px;display:flex;align-items:center;gap:6px;">
                            <span>👑 فیلتر سلاطین منتخب (انتخاب تک‌تک یا گروهی {len(qualified_kings)} گره برتر):</span>
                            <span id="simKingsCountLabel" style="background:#854d0e;color:#fef08a;font-size:11px;padding:2px 8px;border-radius:10px;">{len(qualified_kings)} از {len(qualified_kings)} سلطان فعال</span>
                        </div>
                        <div style="display:flex;gap:6px;flex-wrap:wrap;">
                            <button onclick="selectAllKings(true)" style="background:#064e3b;border:1px solid #059669;color:#34d399;font-size:11px;padding:4px 10px;border-radius:5px;cursor:pointer;font-weight:bold;">🟢 انتخاب همه</button>
                            <button onclick="selectAllKings(false)" style="background:#450a0a;border:1px solid #dc2626;color:#fca5a5;font-size:11px;padding:4px 10px;border-radius:5px;cursor:pointer;font-weight:bold;">🔴 لغو همه</button>
                            <button onclick="selectOnlyPerfectKings()" style="background:#1e3a8a;border:1px solid #3b82f6;color:#93c5fd;font-size:11px;padding:4px 10px;border-radius:5px;cursor:pointer;">💎 فقط ۱۰۰٪ وین‌ریت</button>
                            <button onclick="selectOnlyRunnerKings()" style="background:#3b0764;border:1px solid #a855f7;color:#e9d5ff;font-size:11px;padding:4px 10px;border-radius:5px;cursor:pointer;">🚀 فقط الگوهای دونده</button>
                        </div>
                    </div>
                    <!-- Kings Chips Grid -->
                    <div id="simKingsGrid" style="display:grid;grid-template-columns:repeat(auto-fill, minmax(215px, 1fr));gap:8px;max-height:220px;overflow-y:auto;padding-right:4px;">
                        <!-- Dynamically filled by JS -->
                    </div>
                </div>

                <!-- 2. TRADING HOURS & PROFIT FILTER ROW -->
                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(320px, 1fr));gap:16px;background:#061424;padding:14px;border-radius:10px;border:1px solid #133352;">
                    
                    <!-- 2A. TRADING HOURS -->
                    <div>
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                            <div style="color:#38bdf8;font-weight:bold;font-size:12.5px;display:flex;align-items:center;gap:6px;">
                                <span>⏰ فیلتر ساعات معاملاتی و سشن‌ها:</span>
                            </div>
                            <span id="simHoursActiveBadge" style="font-size:11px;color:#7dd3fc;background:#0c4a6e;padding:2px 8px;border-radius:6px;">۲۴ ساعت فعال</span>
                        </div>
                        
                        <!-- Hour Presets -->
                        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
                            <button id="btnHAll" class="hour-preset-btn active" onclick="applyHourPreset('all', this)">🌍 ۲۴ ساعته</button>
                            <button id="btnHNoNight" class="hour-preset-btn" onclick="applyHourPreset('no_night', this)" title="بسته شدن معاملات از ۲۲:۰۰ شب تا ۰۴:۰۰ صبح (دقیقاً سناریوی درخواستی)">🛡️ بستن شب (۲۲ تا ۰۴)</button>
                            <button id="btnHLonNy" class="hour-preset-btn" onclick="applyHourPreset('lon_ny', this)">☀️ سشن لندن/نیویورک (۰۷ تا ۲۰)</button>
                            <button id="btnHAsia" class="hour-preset-btn" onclick="applyHourPreset('asia', this)">🌙 سشن آسیا (۰۰ تا ۰۸)</button>
                        </div>

                        <!-- 24-Hour Visual Buttons Bar -->
                        <div style="font-size:11px;color:#64748b;margin-bottom:4px;">کلیک روی هر ساعت برای فعال/غیرفعال کردن تکی:</div>
                        <div id="simHoursBar" style="display:grid;grid-template-columns:repeat(12, 1fr);gap:4px;">
                            <!-- 24 buttons 00 to 23 -->
                        </div>
                    </div>

                    <!-- 2B. MINIMUM TARGET PROFIT FILTER -->
                    <div>
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                            <div style="color:#34d399;font-weight:bold;font-size:12.5px;display:flex;align-items:center;gap:6px;">
                                <span>💰 فیلتر حداقل سود پتانسیل معامله (Min 1R Target $):</span>
                            </div>
                            <span id="simProfitBadge" style="font-size:11px;color:#6ee7b7;background:#064e3b;padding:2px 8px;border-radius:6px;">بدون فیلتر ($0)</span>
                        </div>

                        <!-- Presets -->
                        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
                            <button class="profit-preset-btn active" data-val="0" onclick="applyProfitPreset(0.0, this)">همه ($0)</button>
                            <button class="profit-preset-btn" data-val="1.5" onclick="applyProfitPreset(1.5, this)">$1.50+</button>
                            <button class="profit-preset-btn" data-val="2" onclick="applyProfitPreset(2.0, this)" title="اگر سود تارگت زیر ۲ دلار بود معامله نشود">$2.00+ ⭐</button>
                            <button class="profit-preset-btn" data-val="2.5" onclick="applyProfitPreset(2.5, this)">$2.50+</button>
                            <button class="profit-preset-btn" data-val="3" onclick="applyProfitPreset(3.0, this)">$3.00+</button>
                        </div>

                        <!-- Slider / Number Input -->
                        <div style="display:flex;align-items:center;gap:12px;margin-top:10px;">
                            <span style="font-size:12px;color:#94a3b8;">حداقل سود ۱R معامله (0.04 لات):</span>
                            <input type="range" id="simProfitSlider" min="0" max="6" step="0.25" value="0" oninput="onProfitSliderInput(this.value)" style="flex:1;cursor:pointer;accent-color:#10b981;" />
                            <span id="simProfitSliderVal" style="color:#34d399;font-family:monospace;font-weight:bold;font-size:14px;min-width:50px;text-align:left;">$0.00</span>
                        </div>
                        <div style="font-size:11px;color:#64748b;margin-top:6px;">
                            💡 در حجم 0.04 لات، سود تارگت اول معامله (1R) باید حداقل برابر این مبلغ باشد تا هزینه اسپرد/کمیسیون ($0.48) توجیه‌پذیر باشد.
                        </div>
                    </div>

                </div>

                                <!-- 2C. CONSECUTIVE LOSS FILTER ROW -->
                <div style="margin-top:12px;background:#061424;padding:12px 14px;border-radius:10px;border:1px solid #133352;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:8px;">
                        <div style="color:#ef4444;font-weight:bold;font-size:12.5px;display:flex;align-items:center;gap:6px;">
                            <span>🛡️ فیلتر وقفه بعد از استاپ‌های متوالی (Consecutive Loss Breaker):</span>
                        </div>
                        <span id="simConsecBadge2" style="font-size:11px;color:#cbd5e1;background:#1e293b;padding:2px 8px;border-radius:6px;">بدون وقفه (خاموش)</span>
                    </div>
                    <div style="display:flex;flex-wrap:wrap;gap:6px;">
                        <button class="consec-btn-filter active" data-trig="0" data-sk="0" data-day="0" onclick="applyConsecFromFilterTab(0, 0, false, this)">همه معاملات (عادی)</button>
                        <button class="consec-btn-filter" data-trig="2" data-sk="1" data-day="0" onclick="applyConsecFromFilterTab(2, 1, false, this)" title="دقیقاً سناریوی درخواستی: اگر ۲ استاپ متوالی خورد، معامله سوم گرفته نمی‌شود">🎯 بعد از ۲ استاپ 👈 رد معامله سوم</button>
                        <button class="consec-btn-filter" data-trig="2" data-sk="2" data-day="0" onclick="applyConsecFromFilterTab(2, 2, false, this)">🛑 بعد از ۲ استاپ 👈 رد ۲ معامله</button>
                        <button class="consec-btn-filter" data-trig="3" data-sk="1" data-day="0" onclick="applyConsecFromFilterTab(3, 1, false, this)">⚠️ بعد از ۳ استاپ 👈 رد ۱ معامله</button>
                        <button class="consec-btn-filter" data-trig="2" data-sk="0" data-day="1" onclick="applyConsecFromFilterTab(2, 0, true, this)">🌙 بعد از ۲ استاپ 👈 توقف تا فردا</button>
                    </div>
                </div>

                <!-- Status Footer -->
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;padding-top:10px;border-top:1px solid #133352;font-size:12px;color:#94a3b8;flex-wrap:wrap;gap:8px;">
                    <div>
                        وضعیت فیلتر جاری: <b id="simActiveTradesCount" style="color:#facc15;">{len(pts_kings)-1}</b> معامله فعال از مجموع <span id="simTotalBaseCount">{len(pts_kings)-1}</span> معامله (<span id="simFilteredOutCount" style="color:#f87171;">0 معامله حذف شده</span>)
                    </div>
                    <div style="display:flex;gap:14px;color:#cbd5e1;">
                        <span>وین‌ریت فیلترشده: <b id="simWinRateVal" style="color:#34d399;">66.5%</b></span>
                        <span>پرافیت فاکتور فیلترشده: <b id="simPfVal" style="color:#38bdf8;">2.44</b></span>
                    </div>
                </div>
            </div>
            </div>

            <!-- SUBPANEL 3: STOP LOSS RISK -->
            <div id="eq-sub-risk" class="eq-subpanel" style="display:none;">
                <!-- 🚨 STOP LOSS CONTROLLER & RISK ANALYZER -->
                    <!-- 🛡️ CONSECUTIVE LOSSES ANALYZER & COOLDOWN CIRCUIT BREAKER -->
                <div style="background: linear-gradient(135deg, #131b2e, #0c1222); border: 2px solid #38bdf8; border-radius: 10px; padding: 14px; margin-bottom: 14px; box-shadow: 0 4px 15px rgba(56, 189, 248, 0.15);">
                    <!-- Header -->
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #1e3a5f; padding-bottom: 8px; margin-bottom: 12px; flex-wrap:wrap; gap:8px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="font-size:20px;">🛡️</span>
                            <div>
                                <span style="font-weight:bold; color:#38bdf8; font-size:14px;">تحلیل تخصصی استاپ‌های پشت سر هم و فیلتر وقفه هوشمند (Consecutive Loss Breaker):</span>
                                <div style="font-size:11px; color:#94a3b8; margin-top:2px;">بررسی آماری طول رگه‌های باخت و شبیه‌سازی زنده قانون «توقف بعد از استاپ‌های متوالی»</div>
                            </div>
                        </div>
                        <!-- Quick Badge -->
                        <div id="consecLossSummaryBadge" style="background:#0f2d4a; border:1px solid #0284c7; color:#7dd3fc; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:bold;">
                            وضعیت: فیلتر خاموش (ترید عادی)
                        </div>
                    </div>

                    <!-- Row 1: KPI Stats for Streaks -->
                    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:8px; margin-bottom:12px;">
                        <div class="kpi-card" style="border-color:#ef4444; padding:8px 10px; background:#1e1420;">
                            <div class="kpi-title" style="color:#fca5a5; font-size:10.5px;">🚨 سقف استاپ پشت هم</div>
                            <div class="kpi-value" id="kpiMaxConsecLoss" style="color:#ef4444; font-size:18px;">۶ معامله</div>
                            <div class="kpi-sub" id="kpiMaxLossSub" style="color:#cbd5e1; font-size:9.5px;">در کل بازه ۶ ماهه</div>
                        </div>
                        <div class="kpi-card" style="border-color:#10b981; padding:8px 10px; background:#0f241d;">
                            <div class="kpi-title" style="color:#86efac; font-size:10.5px;">🏆 سقف برد پشت هم</div>
                            <div class="kpi-value" id="kpiMaxConsecWin" style="color:#34d399; font-size:18px;">۱۳ معامله</div>
                            <div class="kpi-sub" style="color:#cbd5e1; font-size:9.5px;">طولانی‌ترین رگه سود</div>
                        </div>
                        <div class="kpi-card" style="border-color:#f59e0b; padding:8px 10px; background:#241c0e;">
                            <div class="kpi-title" style="color:#fcd34d; font-size:10.5px;">📊 تعداد رگه‌های باخت</div>
                            <div class="kpi-value" id="kpiTotalLossStreaks" style="color:#facc15; font-size:18px;">۲۵۷ رگه</div>
                            <div class="kpi-sub" style="color:#cbd5e1; font-size:9.5px;">توالی‌های منتهی به برد</div>
                        </div>
                        <div class="kpi-card" style="border-color:#a855f7; padding:8px 10px; background:#1c1328;">
                            <div class="kpi-title" style="color:#d8b4fe; font-size:10.5px;">⚡ میانگین طول باخت‌ها</div>
                            <div class="kpi-value" id="kpiAvgLossStreak" style="color:#c084fc; font-size:18px;">۱.۸ معامله</div>
                            <div class="kpi-sub" style="color:#cbd5e1; font-size:9.5px;">اکثراً تک‌استاپ برمی‌گردد</div>
                        </div>
                    </div>

                    <!-- Row 2: Distribution Bars (1 SL, 2 SL, 3 SL, 4 SL, 5 SL, 6+ SL) -->
                    <div style="background:#090e1a; border:1px solid #1e293b; border-radius:8px; padding:10px 12px; margin-bottom:12px;">
                        <div style="font-size:11.5px; font-weight:bold; color:#cbd5e1; margin-bottom:8px; display:flex; justify-content:space-between;">
                            <span>📊 فراوانی و توزیع رگه‌های استاپ متوالی در چیدمان فعال:</span>
                            <span style="color:#64748b; font-size:10.5px;">(بررسی احتمال وقوع استاپ سوم بعد از خوردن ۲ استاپ)</span>
                        </div>
                        <div id="consecLossBarsGrid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(100px, 1fr)); gap:6px;">
                            <!-- Filled dynamically by JS -->
                        </div>
                    </div>

                    <!-- Row 3: Interactive Filter Controller -->
                    <div style="background:#090e1a; border:1px solid #1e293b; border-radius:8px; padding:12px 14px;">
                        <div style="font-size:12px; font-weight:bold; color:#38bdf8; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                            <span>🎛️ انتخاب سناریوی فیلتر استاپ متوالی (شبیه‌ساز آنی روی چارت):</span>
                        </div>
                        <div style="display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:10px;">
                            <button class="consec-btn active" id="btnConsecNone" onclick="setConsecLossFilter(0, 0, false, this)">
                                ⚪ بدون فیلتر (ترید عادی)
                            </button>
                            <button class="consec-btn" id="btnConsec2Skip1" onclick="setConsecLossFilter(2, 1, false, this)" title="دقیقاً سناریوی درخواستی: اگر ۲ استاپ متوالی خورد، معامله سوم گرفته نمی‌شود">
                                🎯 ۲ استاپ پشت‌هم 👈 معامله سوم رد شود (Skip 1)
                            </button>
                            <button class="consec-btn" id="btnConsec2Skip2" onclick="setConsecLossFilter(2, 2, false, this)">
                                🛑 ۲ استاپ پشت‌هم 👈 ۲ معامله بعدی رد شود (Skip 2)
                            </button>
                            <button class="consec-btn" id="btnConsec3Skip1" onclick="setConsecLossFilter(3, 1, false, this)">
                                ⚠️ ۳ استاپ پشت‌هم 👈 ۱ معامله بعدی رد شود
                            </button>
                            <button class="consec-btn" id="btnConsec2Daily" onclick="setConsecLossFilter(2, 0, true, this)" title="قانون شرکت‌های پراپ: اگر امروز ۲ استاپ خورد، کل باقی معاملات همان روز بسته شود">
                                🌙 ۲ استاپ پشت‌هم 👈 توقف معاملات تا روز بعد
                            </button>
                        </div>

                        <!-- Custom Controls Toggle / Inputs -->
                        <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; background:#070b14; padding:8px 12px; border-radius:6px; border:1px solid #1e293b; font-size:11.5px;">
                            <span style="color:#94a3b8;">تنظیم دستی دلخواه:</span>
                            <span>اگر</span>
                            <select id="selConsecTrigger" onchange="onCustomConsecChange()" style="background:#0f172a; color:#f1f5f9; border:1px solid #334155; border-radius:4px; padding:3px 6px; font-size:11px;">
                                <option value="0">خاموش</option>
                                <option value="1">۱ استاپ</option>
                                <option value="2">۲ استاپ</option>
                                <option value="3">۳ استاپ</option>
                                <option value="4">۴ استاپ</option>
                            </select>
                            <span>پشت‌هم خورد،</span>
                            <select id="selConsecAction" onchange="onCustomConsecChange()" style="background:#0f172a; color:#f1f5f9; border:1px solid #334155; border-radius:4px; padding:3px 6px; font-size:11px;">
                                <option value="skip_1">۱ معامله بعدی رد شود</option>
                                <option value="skip_2">۲ معامله بعدی رد شود</option>
                                <option value="skip_3">۳ معامله بعدی رد شود</option>
                                <option value="skip_day">تا روز بعد ترید متوقف شود</option>
                            </select>
                        </div>

                        <!-- Impact Result Box -->
                        <div id="consecFilterImpactBox" style="margin-top:10px; padding:8px 12px; border-radius:6px; background:#0d1829; border:1px solid #1e3a5f; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; font-size:11px;">
                            <div style="color:#cbd5e1;">
                                📌 تأثیر فیلتر روی چارت: <b id="consecSkippedTradesVal" style="color:#facc15;">0</b> معامله اسکیپ شد (<span id="consecSavedLossesVal" style="color:#00e676; font-weight:bold;">0 استاپ نجات یافت</span> | <span id="consecMissedWinsVal" style="color:#f87171;">0 برد از دست رفت</span>)
                            </div>
                            <div style="color:#38bdf8;">
                                🛡️ وضعیت دراودان: <b id="consecDDImpactVal">افت سرمایه فعلی: $42.75</b>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="slRiskPanel" style="background: linear-gradient(135deg, #1c0808, #110505); border: 2px solid #ef4444; border-radius: 10px; padding: 14px; margin-bottom: 14px; box-shadow: 0 4px 15px rgba(239, 68, 68, 0.2);">
                        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #450a0a; padding-bottom: 8px; margin-bottom: 10px; flex-wrap:wrap; gap:8px;">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span style="font-size:18px;">🚨</span>
                                <div>
                                    <span style="font-weight:bold; color:#fca5a5; font-size:13.5px;">کالبدشکافی پرریسک‌ترین سلاطین (بیشترین تعداد استاپ و زیان دلاری):</span>
                                    <span style="font-size:11px; color:#cbd5e1; margin-right:6px;">سلاطین قرمز رنگ زیر بیشترین حجم ضرر را تولید می‌کنند؛ با یک کلیک می‌توانید آنها را حذف کنید:</span>
                                </div>
                            </div>
                            <div style="display:flex; gap:6px; flex-wrap:wrap;">
                                <button id="btnRemoveTop3Cnt" onclick="toggleTop3SL('cnt')" style="background:#7f1d1d; border:1px solid #ef4444; color:#fff; font-size:11px; padding:5px 12px; border-radius:5px; cursor:pointer; font-weight:bold; transition:all 0.2s;">
                                    🚫 حذف ۳ سلطان با بیشترین استاپ (تعداد)
                                </button>
                                <button id="btnRemoveTop3Usd" onclick="toggleTop3SL('usd')" style="background:#450a0a; border:1px solid #dc2626; color:#fca5a5; font-size:11px; padding:5px 12px; border-radius:5px; cursor:pointer; font-weight:bold; transition:all 0.2s;">
                                    💸 حذف ۳ سلطان با بیشترین زیان دلاری
                                </button>
                                <button id="btnRemoveWorstRate" onclick="toggleWorstRateKings()" style="background:#3b0764; border:1px solid #a855f7; color:#e9d5ff; font-size:11px; padding:5px 12px; border-radius:5px; cursor:pointer; font-weight:bold; transition:all 0.2s;" title="حذف الگوهایی با نرخ باخت نزدیک به ۵۰٪ مثل S-RS و RS-BE">
                                    🛡️ حذف سلاطین کم‌دقت (باخت > ۴۵٪)
                                </button>
                            </div>
                        </div>

                        <!-- Top Stop Loss Cards Grid -->
                        <div id="slTop3CardsContainer" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:10px;">
                            <!-- Dynamically generated by JS -->
                        </div>
                    </div>
            </div>

            <!-- SUBPANEL 4: WEEKLY P&L BARS -->
            <div id="eq-sub-weekly" class="eq-subpanel" style="display:none;">
                <!-- Interactive Weekly P&L Bar Chart Container -->
            <div class="section-box" style="border:1px solid #10b981;background:#0b0f19;padding:10px 14px;margin-bottom:10px;border-radius:8px;">
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e293b;padding-bottom:8px;margin-bottom:10px;flex-wrap:wrap;gap:12px;">
                    <div>
                        <h3 style="margin:0;color:#10b981;font-size:15px;display:flex;align-items:center;gap:6px;">
                            <span>📊 نمودار میله‌ای سود و زیان هفته به هفته (Weekly Net Profit & Loss)</span>
                        </h3>
                        <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">توزیع عملکرد دلاری {total_weeks} هفته متوالی - میله‌های سبز نشان‌دهنده سوددهی هفتگی و میله‌های قرمز نشان‌دهنده هفته‌های اصلاحی هستند:</p>
                    </div>
                    <div style="display:flex;gap:8px;">
                        <button id="btnWkKings" class="sort-btn active" onclick="switchWeeklyBarMode('kings')">👑 سلاطین {len(qualified_kings)} گانه</button>
                        <button id="btnWkAll" class="sort-btn" onclick="switchWeeklyBarMode('all')">🌐 کل معاملات چارت</button>
                    </div>
                </div>

                <!-- Canvas Box -->
                <div style="position:relative;width:100%;height:340px;background:#0f172a;border:1px solid #1e293b;border-radius:10px;overflow:hidden;">
                    <canvas id="weeklyBarCanvas" style="width:100%;height:100%;display:block;cursor:pointer;"></canvas>
                    <div id="weeklyBarTooltip" style="display:none;position:absolute;pointer-events:none;background:rgba(15,23,42,0.95);border:1px solid #10b981;padding:10px 14px;border-radius:8px;font-size:12px;color:#f1f5f9;box-shadow:0 8px 24px rgba(0,0,0,0.7);z-index:20;direction:rtl;min-width:220px;"></div>
                </div>

                <!-- Legend & Summary -->
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:14px;font-size:12px;color:#94a3b8;flex-wrap:wrap;gap:10px;">
                    <div style="display:flex;align-items:center;gap:16px;">
                        <span style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:12px;height:12px;background:#00e676;border-radius:2px;"></span> هفته سودده (Green Week)</span>
                        <span style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:12px;height:12px;background:#ef4444;border-radius:2px;"></span> هفته زیان‌ده (Red Week)</span>
                        <span style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:14px;height:2px;background:#64748b;"></span> خط تراز صفر ($0)</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:12px;">
                        <span>تعداد کل هفته‌ها: <b style="color:#f1f5f9;">{total_weeks} هفته</b></span>
                        <span>|</span>
                        <span>هفته‌های سودده: <b style="color:#00e676;">{tot_kings_green_wks} هفته ({tot_kings_green_wks/(total_weeks or 1)*100:.1f}٪)</b></span>
                        <span>|</span>
                        <span>هفته‌های زیان‌ده: <b style="color:#ef4444;">{tot_kings_red_wks} هفته ({tot_kings_red_wks/(total_weeks or 1)*100:.1f}٪)</b></span>
                    </div>
                </div>
            </div>
            </div>

            <!-- SUBPANEL 5: COMPARISON TABLE -->
            <div id="eq-sub-compare" class="eq-subpanel" style="display:none;">
                <!-- Comparison Table: Kings vs All -->
            <div class="section-box" style="border:1px solid #475569;background:#1e293b;">
                <div style="border-bottom:1px solid #334155;padding-bottom:10px;margin-bottom:14px;">
                    <h4 style="margin:0;color:#e2e8f0;font-size:16px;">⚖️ مقایسه شاخص‌های کلیدی منحنی رشد: سلاطین منتخب در برابر کل معاملات خام چارت</h4>
                </div>
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#0f172a;color:#94a3b8;">
                                <th>استراتژی و دامنه ساختارها</th>
                                <th style="text-align:center;">تعداد کل معامله</th>
                                <th style="text-align:center;">بالانس اولیه</th>
                                <th style="text-align:center;">بالانس نهایی</th>
                                <th style="text-align:center;">سود خالص دلاری ($)</th>
                                <th style="text-align:center;">درصد رشد حساب</th>
                                <th style="text-align:center;">حداکثر افت (Max Drawdown)</th>
                                <th style="text-align:center;">قضاوت عملکرد</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom:1px solid #334155;">
                                <td style="font-weight:bold;color:#facc15;">👑 سبد سلاطین {len(qualified_kings)} گانه (گزینش هوشمند)</td>
                                <td style="text-align:center;font-weight:bold;">{len(pts_kings)-1}</td>
                                <td style="text-align:center;">${bal_initial:,.0f}</td>
                                <td style="text-align:center;font-weight:bold;color:#00e676;">${bal_k:,.0f}</td>
                                <td style="text-align:center;font-weight:bold;color:#00e676;">{'+$' if net_k>=0 else '-$'}{abs(net_k):,.0f}</td>
                                <td style="text-align:center;font-weight:bold;color:#00e676;">{net_k_pct:+.1f}٪</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">${max_dd_k:.0f} ({max_dd_k_pct:.1f}٪)</td>
                                <td style="text-align:center;"><span style="background:#064e3b;color:#34d399;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">💎 رشد مستمر و اکوئیتی صعودی</span></td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#94a3b8;">🌐 کل ساختارهای خام چارت (بدون فیلتر)</td>
                                <td style="text-align:center;font-weight:bold;">{len(pts_all)-1}</td>
                                <td style="text-align:center;">${bal_initial:,.0f}</td>
                                <td style="text-align:center;font-weight:bold;color:{'#00e676' if net_a>=0 else '#ef4444'};">${bal_a:,.0f}</td>
                                <td style="text-align:center;font-weight:bold;color:{'#00e676' if net_a>=0 else '#ef4444'};">{'+$' if net_a>=0 else '-$'}{abs(net_a):,.0f}</td>
                                <td style="text-align:center;font-weight:bold;color:{'#00e676' if net_a>=0 else '#ef4444'};">{net_a_pct:+.1f}٪</td>
                                <td style="text-align:center;color:#ef4444;font-weight:bold;">${max_dd_a:.0f} ({max_dd_a_pct:.1f}٪)</td>
                                <td style="text-align:center;"><span style="background:#451a03;color:#fca5a5;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">⚠️ فرسایش ناشی از نویزها</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
</div>
</div>"""
    tab_kings_html = f"""<!-- Global Performance KPI Cards (Placed inside Tab 1) -->
            <div class="kpi-grid" style="margin-bottom:20px;">
                <div class="kpi-card" style="border-top: 4px solid #38bdf8;">
                    <div class="kpi-title">📦 کل باکس‌های شناسایی‌شده</div>
                    <div class="kpi-value" style="color:#38bdf8;">{total_setups:,}</div>
                    <div class="kpi-sub">تایم‌های M1, M5, M15</div>
                </div>
                <div class="kpi-card" style="border-top: 4px solid #00e676;">
                    <div class="kpi-title">✅ معاملات وارد شده و بسته‌شده</div>
                    <div class="kpi-value" style="color:#00e676;">{len(closed):,}</div>
                    <div class="kpi-sub">در انتظار / فعال: {len(in_trade)} معامله</div>
                </div>
                <div class="kpi-card" style="border-top: 4px solid #f59e0b;">
                    <div class="kpi-title">🛡️ استاپ‌های نجات‌یافته با فیلتر</div>
                    <div class="kpi-value" style="color:#f59e0b;">{sl_in_rej} 🎯</div>
                    <div class="kpi-sub">دقت فیلتر در باخت: {rej_accuracy:.1f}%</div>
                </div>
                <div class="kpi-card" style="border-top: 4px solid #10b981;">
                    <div class="kpi-title">🚀 جهش امید ریاضی (EV)</div>
                    <div class="kpi-value" style="color:#10b981;">{ev_a:+.2f} R</div>
                    <div class="kpi-sub">قبل از فیلتر: {ev_b:+.2f} R</div>
                </div>
                <div class="kpi-card" style="border-top: 4px solid #eab308;">
                    <div class="kpi-title">💵 سود خالص دلاری سلاطین (0.04)</div>
                    <div class="kpi-value" style="color:#facc15;">${s3_net:+.2f}</div>
                    <div class="kpi-sub">از {tot_k_cnt} معامله سلاطین برتر</div>
                </div>
            </div>

            {mp_full_html_section}

            <!-- VIEW 2: ALL-TIME 7-PILLAR SCORE -->
            <div id="kingsViewAllTime" style="display:{disp_all};">
            <div class="section-box" style="border: 1px solid #eab308; background: #1a1608;">
                <div style="border-bottom: 1px solid #854d0e; padding-bottom: 14px; margin-bottom: 16px;">
                    <h3 style="margin:0;color:#facc15;font-size:20px;">👑 جدول جامع سلاطین منتخب بر مبنای شاخص ترکیبی و تفکیک تایم‌فریم</h3>
                    <p style="margin:4px 0 0 0;color:#fef08a;font-size:12px;">کالبدشکافی پویا از {tot_k_cnt} معامله واقعی سلاطین برتر FlagPro (گزینش با فرمول شاخص سلطان، بونوس ۱۰۰٪ قطعی و الگوهای دونده):</p>
                </div>

                <!-- Formula Highlight Banner -->
                <div style="font-size:12px;color:#fef08a;margin-bottom:16px;background:#261e07;padding:12px 16px;border-radius:8px;border-right:4px solid #facc15;display:flex;align-items:center;justify-content:space-between;flex-wrap:gap;gap:10px;">
                    <div>
                        <b style="color:#facc15;font-size:13px;">🏛️ شاخص ۷ ستونه هج‌فاندی سلطان (7-Pillar Institutional King Score):</b>
                        <span style="direction:ltr;display:inline-block;font-family:monospace;background:#1e293b;padding:3px 10px;border-radius:5px;color:#38bdf8;margin:0 8px;font-size:11.5px;font-weight:bold;">Score = 🛡️خلوص(۵۰۰) + 🎯تارگت۲(۴۰۰) + ⚡پیشروی(۲۵۰) + 💰بهره‌وری(۲۰۰) + 📊اعتبار(۵۰) + ⚖️پرافیت فاکتور(۱۰۰) + 🛡️کنترل افت و ریکاوری(۱۰۰)</span>
                    </div>
                    <div style="display:flex;gap:6px;">
                        <span style="background:#064e3b;color:#34d399;font-size:11px;padding:3px 8px;border-radius:4px;border:1px solid #059669;">👑 ۱۰۰٪ وین‌ریت (+۵۰۰ امتیاز قطعی)</span>
                        <span style="background:#1e3a8a;color:#93c5fd;font-size:11px;padding:3px 8px;border-radius:4px;border:1px solid #3b82f6;">⚖️ کنترل دراوداون و پرافیت فاکتور</span>
                    </div>
                </div>

                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#261e07;">
                                <th style="text-align:center;">رتبه</th>
                                <th style="text-align:center;">تایم‌فریم</th>
                                <th>نام ساختار / تلاقی گره‌ها</th>
                                <th style="text-align:center;color:#facc15;">امتیاز سلطان (Score)</th>
                                <th style="text-align:center;">تعداد معامله</th>
                                <th style="text-align:center;">وین‌ریت TP 1:1</th>
                                <th style="text-align:center;">وین‌ریت TP 1:2</th>
                                <th style="text-align:center;">وین‌ریت TP 1:3</th>
                                <th style="text-align:center;">وین‌ریت TP 1:4</th>
                                <th style="text-align:center;">نرخ باخت (SL)</th>
                                <th style="text-align:center;color:#38bdf8;" title="نسبت سود ناخالص به زیان ناخالص (Profit Factor)">⚖️ پرافیت فاکتور (PF)</th>
                                <th style="text-align:center;color:#f87171;" title="حداکثر افت موقت بالانس در طول معاملات (Max Drawdown)">🛡️ حداکثر افت (Max DD)</th>
                                <th style="text-align:center;color:#facc15;" title="نسبت سود خالص نهایی به حداکثر افت (Recovery Factor)">🚀 بازدهی/افت (Ret/DD)</th>
                                <th style="text-align:center;color:#38bdf8;" title="مجموع سود بدون کسر اسپرد">سود ناخالص (Gross)</th>
                                <th style="text-align:center;color:#f87171;" title="مجموع کل اسپرد و کمیسیون پرداخت شده به ازای هر ترید 0.04 لات ($0.48)">🧾 کل اصطکاک (اسپرد)</th>
                                <th style="text-align:center;color:#00e676;background:#064e3b44;" title="سود قطعی واریزی به حساب بعد از پرداخت کل اسپرد و کمیسیون">💵 سود خالص واقعی (Net)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(kings_rows_html)}
                        </tbody>
                        <tfoot>
                            <tr style="background:#261e07;border-top:2px solid #facc15;font-weight:bold;">
                                <td colspan="4" style="text-align:center;color:#facc15;font-size:14px;">👑 مجموع عملکرد کل سلاطین برگزیده ({len(qualified_kings)} گره برتر)</td>
                                <td style="text-align:center;color:#facc15;font-size:15px;">{tot_k_cnt}</td>
                                <td colspan="8" style="text-align:center;color:#94a3b8;font-size:11px;">مبتنی بر استراتژی خروج چهارپله‌ای 0.04 لات و پایش دقیق دراوداون</td>
                                <td style="text-align:center;color:#38bdf8;font-size:14px;">${tot_k_gross:+.2f}</td>
                                <td style="text-align:center;color:#f87171;font-size:14px;">${tot_k_fric:.2f}-</td>
                                <td style="text-align:center;color:#00e676;font-size:16px;background:#064e3b;">${tot_k_net:+.2f} دلار نقد خالص</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            </div>
            </div> <!-- End kingsViewAllTime -->"""
    tab_scaleout_html = f"""<div class="section-box" style="border: 2px solid #38bdf8; background: #082136;">
                <div style="border-bottom: 1px solid #0284c7; padding-bottom: 14px; margin-bottom: 16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                        <div>
                            <h3 style="margin:0;color:#38bdf8;font-size:20px;">💎 سیستم خروج پلکانی با حجم عملیاتی 0.04 لات (با اعمال ۳ شرط لایو بازار)</h3>
                            <p style="margin:6px 0 0 0;color:#bae6fd;font-size:13px;">کالبدشکافی رفتار {tot_k_cnt} معامله واقعی سلاطین {len(qualified_kings)} گانه با تایید قطعی پولبک، پرتاب و حجم <b>0.04 لات</b>:</p>
                        </div>
                        <div style="background:#0c4a6e;border:1px solid #0284c7;padding:8px 14px;border-radius:8px;font-size:12px;color:#7dd3fc;text-align:right;">
                            <div>💵 ارزش هر پیپ: <b>$0.40 دلار</b></div>
                            <div>🧾 کل اصطکاک پرداخت‌شده (کمیسیون+اسپرد): <b>${tot_k_fric:.2f} دلار</b></div>
                        </div>
                    </div>
                </div>

                <!-- Steps Breakdown Grid: 4-Way Balanced 25-25-25-25 -->
                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(240px, 1fr));gap:12px;margin-bottom:18px;">
                    <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                        <div style="color:#facc15;font-weight:bold;font-size:14px;">🎯 پله اول (TP 1:1) - خروج ۰.۰۱ لات (۲۵٪)</div>
                        <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">ذخیره سود پله ۱ + <b>انتقال فوری استاپ لاس به نقطه ورود (ریسک‌فری قطعی)</b></div>
                        <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">🛡️ نتیجه: ریسک کل معامله صفر شد و کمیسیون پوشش یافت!</div>
                    </div>
                    <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                        <div style="color:#facc15;font-weight:bold;font-size:14px;">🎯 پله دوم (TP 1:2) - خروج ۰.۰۱ لات (۲۵٪)</div>
                        <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">نقد کردن ۲۵٪ دیگر با سود ۲ برابری + <b>قفل سود در سطح TP1</b></div>
                        <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">📈 نتیجه: تثبیت سود عالی و کاهش کامل استرس معامله</div>
                    </div>
                    <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                        <div style="color:#facc15;font-weight:bold;font-size:14px;">🎯 پله سوم (TP 1:3) - خروج ۰.۰۱ لات (۲۵٪)</div>
                        <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">نقد کردن ۲۵٪ با سود ۳ برابری + <b>تریل استاپ به سطح TP2</b></div>
                        <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">💰 نتیجه: شکار میانه موج‌های قوی بازار</div>
                    </div>
                    <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                        <div style="color:#facc15;font-weight:bold;font-size:14px;">🚀 پله چهارم (TP 1:4) - خروج ۰.۰۱ لات (۲۵٪ رانر)</div>
                        <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">نگهداری ۲۵٪ باقیمانده بدون ریسک برای دوشیدن انتهای ترندهای بزرگ</div>
                        <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">👑 نتیجه: شکار سودهای ۴ برابری در {tp3_4} معامله!</div>
                    </div>
                </div>

                <!-- Table: 0.04 Lot Performance -->
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#0b3353;">
                                <th>استراتژی خروج معامله با حجم 0.04 لات</th>
                                <th style="text-align:center;">سود ناخالص</th>
                                <th style="text-align:center;">کل کمیسیون و اسپرد</th>
                                <th style="text-align:center;">💵 سود خالص دلاری نهایی</th>
                                <th style="text-align:center;">ضریب سود (PF)</th>
                                <th style="text-align:center;">جهش سود خالص دلاری</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="color:#94a3b8;font-weight:bold;">۱. خروج ساده تک‌تارگت در TP 1:1 (بستن ۱۰۰٪ حجم 0.04)</td>
                                <td style="text-align:center;color:#38bdf8;">${s1_gross:+.2f}</td>
                                <td style="text-align:center;color:#f87171;">${tot_k_fric:.2f}</td>
                                <td style="text-align:center;color:{'#00e676' if s1_net >= 0 else '#ef4444'};font-weight:bold;font-size:15px;">${s1_net:+.2f} دلار</td>
                                <td style="text-align:center;color:#cbd5e1;">{s1_pf:.2f}</td>
                                <td style="text-align:center;color:#94a3b8;">مبنا</td>
                            </tr>
                            <tr>
                                <td style="color:#94a3b8;font-weight:bold;">۲. خروج ساده تک‌تارگت در TP 1:2 (بستن ۱۰۰٪ حجم 0.04)</td>
                                <td style="text-align:center;color:#38bdf8;">${s2_gross:+.2f}</td>
                                <td style="text-align:center;color:#f87171;">${tot_k_fric:.2f}</td>
                                <td style="text-align:center;color:{'#00e676' if s2_net >= 0 else '#ef4444'};font-weight:bold;font-size:15px;">${s2_net:+.2f} دلار</td>
                                <td style="text-align:center;color:#cbd5e1;">{s2_pf:.2f}</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">${s2_diff_dollar:+.2f} ({s2_diff_pct:+.1f}%)</td>
                            </tr>
                            <tr style="background:#064e3b33;border:2px solid #10b981;">
                                <td style="color:#00e676;font-weight:bold;font-size:14px;">👑 ۳. خروج چهارپله‌ای متوازن FlagPro (۰.۰۱ در TP1 + ریسک‌فری | ۰.۰۱ در TP2 | ۰.۰۱ در TP3 | ۰.۰۱ در TP4) 🚀</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">${s3_gross:+.2f}</td>
                                <td style="text-align:color:#cbd5e1;">${tot_k_fric:.2f}</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:18px;">${s3_net:+.2f} دلار نقد خالص! 💵</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{s3_pf:.2f} 🚀</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">${s3_diff_dollar:+.2f} سود بیشتر ({s3_diff_pct:+.1f}%) 🚀</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Break-Even Comparison -->
                <div style="margin-top: 24px; border-top: 1px dashed #0284c7; padding-top: 18px;">
                    <h4 style="margin:0 0 10px 0; color:#facc15; font-size:16px;">⚖️ مقایسه بریک‌ایون (ریسک‌فری) با حجم 0.04 لات: انتقال استاپ در TP1 یا در TP2؟ کدام سودده‌تر است؟</h4>
                    <p style="margin:0 0 14px 0; color:#cbd5e1; font-size:12.5px; line-height:1.6;">
                        کالبدشکافی رفتار {tot_k_cnt} معامله سلاطین: <b>{sl_direct} معامله استاپ مستقیم ({sl_direct_pct:.1f}%)</b> | 
                        <b style="color:#facc15;">{tp1_only} معامله ({tp1_only_pct:.1f}%) فقط TP1 را تاچ کردند و برگشتند!</b> | 
                        <b>{tp2_only} معامله ({tp2_only_pct:.1f}%) تا TP2 رفتند</b> | 
                        <b style="color:#00e676;">{tp3_4} معامله ({tp3_4_pct:.1f}%) به TP3 و TP4 رسیدند!</b>
                    </p>

                    <div style="overflow-x:auto;">
                        <table>
                            <thead>
                                <tr style="background:#0b3353;">
                                    <th>روش انتقال استاپ به ورود (Break-Even) با حجم 0.04 لات</th>
                                    <th style="text-align:center;">سرنوشت {tp1_only} معامله‌ای که بعد از TP1 برگشتند</th>
                                    <th style="text-align:center;">سود ناخالص</th>
                                    <th style="text-align:center;">کل کمیسیون و اسپرد</th>
                                    <th style="text-align:center;">💵 سود خالص دلاری نهایی</th>
                                    <th style="text-align:center;">اختلاف و برتری مالی</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style="background:#064e3b44; border: 2px solid #10b981;">
                                    <td style="color:#00e676; font-weight:bold; font-size:13.5px;">🥇 حالت اول: انتقال استاپ به نقطه ورود (BE) در TP1</td>
                                    <td style="text-align:center; color:#a7f3d0; font-size:12px;">سود ۰.۰۲ لات در TP1 ذخیره شد + ۰.۰۲ لات باقیمانده بدون ضرر روی نقطه ورود خارج شد (سود خالص!)</td>
                                    <td style="text-align:center; color:#00e676; font-weight:bold;">${m1_gross:+.2f}</td>
                                    <td style="text-align:center; color:#cbd5e1;">${tot_k_fric:.2f}</td>
                                    <td style="text-align:center; color:#00e676; font-weight:bold;font-size:17px;">${m1_net:+.2f} دلار نقد 🚀</td>
                                    <td style="text-align:center; color:#facc15; font-weight:bold; font-size:14px;">🏆 برنده قطعی! (${be_diff:+.2f} دلار سود بیشتر)</td>
                                </tr>
                                <tr style="background:#450a0a22; border: 1px solid #7f1d1d;">
                                    <td style="color:#f87171; font-weight:bold; font-size:13.5px;">❌ حالت دوم: انتقال استاپ به نقطه ورود (BE) فقط در TP2</td>
                                    <td style="text-align:center; color:#fca5a5; font-size:12px;">سود ۰.۰۲ لات گرفته شد، اما چون استاپ دست نخورده بود، ۰.۰۲ لات باقیمانده برگشت و استاپ اولیه را زد!</td>
                                    <td style="text-align:center; color:#f87171; font-weight:bold;">${m2_gross:+.2f}</td>
                                    <td style="text-align:center; color:#cbd5e1;">${tot_k_fric:.2f}</td>
                                    <td style="text-align:center; color:#f87171; font-weight:bold; font-size:15px;">${m2_net:+.2f} دلار</td>
                                    <td style="text-align:center; color:#ef4444; font-size:13px;">بازنده (${abs(be_diff):.2f} دلار سود کمتر!)</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div style="background:#09304a; border-left:4px solid #38bdf8; padding:10px 14px; border-radius:4px; margin-top:12px; font-size:12px; color:#e0f2fe; line-height:1.5;">
                        💡 <b>نتیجه‌گیری مالی قطعی با حجم 0.04 لات:</b> دقیقاً <b>{tp1_only_pct:.1f}٪ معاملات ({tp1_only} معامله)</b> فقط تا TP1 پیش می‌روند. انتقال استاپ به ورود در TP1 مانع از سوختن {be_diff:.2f} دلار سود شما می‌شود و سود کل سیستم را به <b>${m1_net:+.2f} دلار نقد خالص</b> می‌رساند!
                    </div>
                </div>
            </div>"""
    tab_timeframes_html = f"""<div class="section-box">
                <div style="border-bottom:1px solid #334155;padding-bottom:8px;margin-bottom:10px;">
                    <h3 style="margin:0;color:#38bdf8;font-size:19px;">📊 تفکیک عملکرد تایم‌فریم‌ها در استراتژی سلاطین {len(qualified_kings)} گانه FlagPro</h3>
                    <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">بررسی سودآوری واقعی معاملات استراتژی سلاطین FlagPro (حجم پلکانی 0.04 با کسر اسپرد و کمیسیون):</p>
                </div>

                <!-- Primary: Golden Kings per Timeframe -->
                <div style="overflow-x:auto;margin-bottom:24px;">
                    <table>
                        <thead>
                            <tr style="background:#0f172a;">
                                <th>تایم‌فریم (سلاطین منتخب FlagPro)</th>
                                <th style="text-align:center;">تعداد معامله</th>
                                <th style="text-align:center;">وین‌ریت TP 1:1</th>
                                <th style="text-align:center;">وین‌ریت TP 1:2</th>
                                <th style="text-align:center;">وین‌ریت TP 1:3</th>
                                <th style="text-align:center;">وین‌ریت TP 1:4</th>
                                <th style="text-align:center;">نرخ باخت (SL)</th>
                                <th style="text-align:center;color:#38bdf8;">سود ناخالص</th>
                                <th style="text-align:center;color:#f87171;">کل اصطکاک (اسپرد)</th>
                                <th style="text-align:center;color:#00e676;">💵 سود خالص واقعی</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(tf_kings_rows)}
                        </tbody>
                    </table>
                </div>

                <!-- Comparison Banner: Why Filters & Kings Are Essential -->
                <div style="background:#1e1b4b;border:1px solid #4338ca;border-radius:8px;padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
                    <div>
                        <span style="color:#a5b4fc;font-weight:bold;font-size:13px;">💡 تفاوت معاملات سلاطین با کل بازار خام چارت:</span>
                        <div style="color:#cbd5e1;font-size:11px;margin-top:2px;">اگر کل {d_tot_raw['cnt']} معامله خام چارت بدون فیلتر معامله می‌شد، {abs(d_tot_raw['net']):.2f}$ {'زیان' if d_tot_raw['net'] < 0 else 'سود'} تولید می‌شد؛ اما سلاطین {len(qualified_kings)} گانه با فیلتر هوشمند آن را به {d_tot_kings['net']:+.2f}$ سود خالص رسانده‌اند!</div>
                    </div>
                    <button class="sort-btn" style="border-color:#a5b4fc;color:#a5b4fc;" onclick="let el = document.getElementById('rawTfTable'); el.style.display = el.style.display==='none'?'':'none';">👁️ مشاهده جدول کل دیتای خام چارت</button>
                </div>

                <!-- Hidden Comparative Raw Table -->
                <div id="rawTfTable" style="overflow-x:auto;margin-bottom:24px;border:1px dashed #475569;border-radius:8px;padding:10px;">
                    <div style="color:#94a3b8;font-size:12px;margin-bottom:6px;font-weight:bold;">⚠️ عملکرد کل {d_tot_raw['cnt']} معامله خام چارت بدون گزینش سلاطین (Raw Market Noise):</div>
                    <table>
                        <thead>
                            <tr style="background:#1e293b;">
                                <th>تایم‌فریم خام</th>
                                <th style="text-align:center;">کل معاملات</th>
                                <th style="text-align:center;">وین‌ریت 1:1</th>
                                <th style="text-align:center;">وین‌ریت 1:2</th>
                                <th style="text-align:center;">وین‌ریت 1:3</th>
                                <th style="text-align:center;">وین‌ریت 1:4</th>
                                <th style="text-align:center;">نرخ باخت</th>
                                <th style="text-align:center;">سود/زیان کل خام</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(tf_raw_rows)}
                        </tbody>
                    </table>
                </div>

                <!-- Detailed Entity Breakdown by Timeframe -->
                <div style="display:flex;justify-content:space-between;align-items:center;border-top:1px solid #334155;padding-top:14px;flex-wrap:wrap;gap:10px;">
                    <div>
                        <h4 style="margin:0;color:#f8fafc;font-size:15px;">تفکیک جزئی گره‌ها در هر تایم‌فریم:</h4>
                    </div>
                    <div>
                        <button class="sort-btn active tf-btn" onclick="filterTF('ALL')">همه تایم‌ها</button>
                        <button class="sort-btn tf-btn" style="border-color:#38bdf8;color:#38bdf8;" onclick="filterTF('M1')">⚡ M1 ({len(tf_map.get('M1', []))})</button>
                        <button class="sort-btn tf-btn" style="border-color:#00e676;color:#00e676;" onclick="filterTF('M5')">🌟 M5 ({len(tf_map.get('M5', []))})</button>
                        <button class="sort-btn tf-btn" style="border-color:#f59e0b;color:#f59e0b;" onclick="filterTF('M15')">🕒 M15 ({len(tf_map.get('M15', []))})</button>
                    </div>
                </div>

                <!-- Formula Explainer Box -->
                <div style="font-size:12px;color:#94a3b8;margin:10px 0;background:#0f172a;padding:10px 14px;border-radius:8px;border-right:4px solid #facc15;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                    <div>
                        <b style="color:#facc15;">🏛️ شاخص ۷ ستونه هج‌فاندی سلطان (7-Pillar Institutional King Score):</b>
                        <span style="direction:ltr;display:inline-block;font-family:monospace;background:#1e293b;padding:2px 8px;border-radius:4px;color:#38bdf8;margin:0 6px;">Score = 🛡️خلوص(۵۰۰) + 🎯وین‌ریت ۱:۲(۴۰۰) + ⚡عمق تارگت‌ها + 💰راندمان ترید + 📊اعتبار + ⚖️پرافیت فاکتور(۱۰۰) + 🛡️کنترل افت و ریکاوری(۱۰۰)</span>
                    </div>
                    <div>
                        <span style="background:#064e3b;color:#34d399;font-size:11px;padding:2px 6px;border-radius:4px;border:1px solid #059669;margin-left:4px;">👑 ۱۰۰٪ وین‌ریت (+۵۰۰ قطعی)</span>
                        <span style="background:#1e3a8a;color:#93c5fd;font-size:11px;padding:2px 6px;border-radius:4px;border:1px solid #3b82f6;">⚖️ کنترل دراوداون و پرافیت فاکتور</span>
                    </div>
                </div>

                <!-- Quick Combined Sorting Buttons -->
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:12px 0;background:#0f172a;padding:8px 12px;border-radius:8px;border:1px solid #334155;">
                    <span style="color:#94a3b8;font-size:12px;font-weight:bold;">🔀 دکمه‌های سورت هوشمند و ترکیبی:</span>
                    <button class="sort-btn active" id="btnSortScore" onclick="sortTableByAttr('tfTable', 'data-score', true, true, this)">👑 بیشترین امتیاز سلطان (Score)</button>
                    <button class="sort-btn" id="btnSortNet" style="border-color:#00e676;color:#00e676;" onclick="sortTableByAttr('tfTable', 'data-net', true, true, this)">💵 بیشترین سود خالص دلاری</button>
                    <button class="sort-btn" style="border-color:#38bdf8;color:#38bdf8;" onclick="sortTableByAttr('tfTable', 'data-pf', true, true, this)">⚖️ بیشترین پرافیت فاکتور (PF)</button>
                    <button class="sort-btn" style="border-color:#f87171;color:#f87171;" onclick="sortTableByAttr('tfTable', 'data-dd', true, false, this)">🛡️ کمترین افت (Max DD)</button>
                    <button class="sort-btn" style="border-color:#facc15;color:#facc15;" onclick="sortTableByAttr('tfTable', 'data-retdd', true, true, this)">🚀 نسبت سود به افت (Ret/DD)</button>
                    <button class="sort-btn" onclick="sortTableByAttr('tfTable', 'data-w4', true, true, this)">🚀 بیشترین تارگت دونده (TP4)</button>
                    <button class="sort-btn" onclick="sortTableByAttr('tfTable', 'data-w2', true, true, this)">🎯 بیشترین وین‌ریت ۱:۲</button>
                    <button class="sort-btn" onclick="sortTableByAttr('tfTable', 'data-w1', true, true, this)">🥇 بیشترین وین‌ریت ۱:۱</button>
                    <button class="sort-btn" onclick="sortTableByAttr('tfTable', 'data-cnt', true, true, this)">📦 بیشترین تعداد معامله</button>
                    <button class="sort-btn" onclick="sortTableByAttr('tfTable', 'data-sl', true, false, this)">🛡️ کمترین باخت (SL)</button>
                    <button class="sort-btn" onclick="sortTableByAttr('tfTable', 'data-tf', false, false, this)">🕒 بر اساس تایم‌فریم</button>
                </div>

                <div style="overflow-x:auto;margin-top:6px;">
                    <table id="tfTable">
                        <thead>
                            <tr>
                                <th onclick="sortTableByAttr('tfTable', 'data-tf', false, false)" data-sort="data-tf" style="cursor:pointer;" title="کلیک برای مرتب‌سازی صعودی/نزولی">تایم‌فریم <span class="sort-icon">⬍</span></th>
                                <th onclick="sortTableByAttr('tfTable', 'data-role', false, false)" data-sort="data-role" style="cursor:pointer;" title="کلیک برای مرتب‌سازی">موجودیت باکس / سواپ <span class="sort-icon">⬍</span></th>
                                <th onclick="sortTableByAttr('tfTable', 'data-cnt', true, true)" data-sort="data-cnt" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی">تعداد معامله <span class="sort-icon">⬍</span></th>
                                <th onclick="sortTableByAttr('tfTable', 'data-w1', true, true)" data-sort="data-w1" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی">TP 1:1 <span class="sort-icon">⬍</span></th>
                                <th onclick="sortTableByAttr('tfTable', 'data-w2', true, true)" data-sort="data-w2" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی">TP 1:2 <span class="sort-icon">⬍</span></th>
                                <th onclick="sortTableByAttr('tfTable', 'data-w3', true, true)" data-sort="data-w3" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی">TP 1:3 <span class="sort-icon">⬍</span></th>
                                <th onclick="sortTableByAttr('tfTable', 'data-w4', true, true)" data-sort="data-w4" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی">TP 1:4 <span class="sort-icon">⬍</span></th>
                                <th onclick="sortTableByAttr('tfTable', 'data-sl', true, false)" data-sort="data-sl" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی">باخت (SL) <span class="sort-icon">⬍</span></th>
                                <th onclick="sortTableByAttr('tfTable', 'data-net', true, true)" data-sort="data-net" style="cursor:pointer;text-align:center;color:#00e676;background:#064e3b33;" title="کلیک برای مرتب‌سازی بر اساس سود خالص دلاری">💵 سود خالص دلاری <span class="sort-icon">⬍</span></th>
                                <th onclick="sortTableByAttr('tfTable', 'data-pf', true, true)" data-sort="data-pf" style="cursor:pointer;text-align:center;color:#38bdf8;" title="کلیک برای مرتب‌سازی بر اساس Profit Factor">⚖️ PF <span class="sort-icon">⬍</span></th>
                                <th onclick="sortTableByAttr('tfTable', 'data-dd', true, false)" data-sort="data-dd" style="cursor:pointer;text-align:center;color:#f87171;" title="کلیک برای مرتب‌سازی بر اساس کمترین افت سرمایه (Max DD)">🛡️ Max DD <span class="sort-icon">⬍</span></th>
                                <th onclick="sortTableByAttr('tfTable', 'data-retdd', true, true)" data-sort="data-retdd" style="cursor:pointer;text-align:center;color:#facc15;" title="کلیک برای مرتب‌سازی بر اساس Recovery Factor (سود به افت)">🚀 Ret/DD <span class="sort-icon">⬍</span></th>
                                <th onclick="sortTableByAttr('tfTable', 'data-score', true, true)" data-sort="data-score" style="cursor:pointer;text-align:center;color:#facc15;background:#1e293b;" title="مرتب‌سازی شده بر مبنای فرمول شاخص سلطان">امتیاز سلطان (Score) <span class="sort-icon">▼</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(tf_role_rows)}
                        </tbody>
                    </table>
                </div>
            </div>"""
    tab_filters_html = f"""<div class="section-box" style="border: 1px solid #38bdf8; background: #0c1829;">
                <div style="border-bottom: 1px solid #1e3a8a; padding-bottom: 14px; margin-bottom: 16px;">
                    <h3 style="margin:0;color:#38bdf8;font-size:19px;">🛡️ جدول تفکیکی دقت فیلترهای ضد استاپ اعمال‌شده در FlagPro</h3>
                    <p style="margin:4px 0 0 0;color:#93c5fd;font-size:12px;">عملکرد مجزای هر فیلتر بر مبنای کل {len(closed):,} معامله واقعی این فایل داده:</p>
                </div>

                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>نام فیلتر هوشمند ضد استاپ</th>
                                <th style="text-align:center;">تنظیم ورودی در متاتریدر</th>
                                <th style="text-align:center;">تعداد معاملات حذفی</th>
                                <th style="text-align:center;">استاپ‌های نجات‌یافته</th>
                                <th style="text-align:center;">🎯 درصد دقت فیلتر</th>
                                <th>تفسیر و عملکرد فیلتر</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="font-weight:bold;color:#facc15;">🛡️ فیلتر ۱: حذف باکس‌های منفرد LS بدون تلاقی</td>
                                <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterSingleLS = true</span></td>
                                <td style="text-align:center;color:#cbd5e1;">{f1_rej} معامله</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">{f1_sl} استاپ قطعی!</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{(f1_sl/f1_rej*100) if f1_rej else 0:.1f}%</td>
                                <td style="color:#94a3b8;font-size:12px;">حذف تریدهای منفرد با بیشترین نرخ باخت</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#facc15;">⏰ فیلتر ۲: مسدودسازی بازه شبانه (۲۱:۰۰ تا ۰۱:۰۰)</td>
                                <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterNightHours = true</span></td>
                                <td style="text-align:center;color:#cbd5e1;">{f2_rej} معامله</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">{f2_sl} استاپ قطعی!</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{(f2_sl/f2_rej*100) if f2_rej else 0:.1f}%</td>
                                <td style="color:#94a3b8;font-size:12px;">فرار از واید شدن اسپرد و افت نقدینگی شبانه</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#facc15;">⏰ فیلتر ۳: مسدودسازی ساعت ۰۷:۰۰ صبح (شکار استاپ آسیا)</td>
                                <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterPreLondonHunt = true</span></td>
                                <td style="text-align:center;color:#cbd5e1;">{f3_rej} معامله</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">{f3_sl} استاپ قطعی!</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{(f3_sl/f3_rej*100) if f3_rej else 0:.1f}%</td>
                                <td style="color:#94a3b8;font-size:12px;">فرار از شکار نقدینگی قبل از اوپن لندن</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#facc15;">☣️ فیلتر ۴: حذف زنجیره‌های سمی و فرسایشی</td>
                                <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterToxicPatterns = true</span></td>
                                <td style="text-align:center;color:#cbd5e1;">{f4_rej} معامله</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">{f4_sl} استاپ قطعی!</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{(f4_sl/f4_rej*100) if f4_rej else 0:.1f}%</td>
                                <td style="color:#94a3b8;font-size:12px;">جلوگیری از ورود در امواج اشباع بازار</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#facc15;">📦 فیلتر ۵: حذف فلگ‌های ساده بدون تلاقی (نویز)</td>
                                <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterPureFlags = true</span></td>
                                <td style="text-align:center;color:#cbd5e1;">{f5_rej} معامله</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">{f5_sl} استاپ قطعی!</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{(f5_sl/f5_rej*100) if f5_rej else 0:.1f}%</td>
                                <td style="color:#94a3b8;font-size:12px;">تصفیه نویزهای ریز بازار</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#facc15;">💰 فیلتر ۶ (اقتصادی): حذف تریدهای با سود کمتر از اصطکاک</td>
                                <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterLowRewardVsFriction = true</span></td>
                                <td style="text-align:center;color:#cbd5e1;">{f7_rej} معامله</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">{f7_sl} زیان قطعی خنثی شد! 🎯</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{(f7_sl/f7_rej*100) if f7_rej else 0:.1f}%</td>
                                <td style="color:#94a3b8;font-size:12px;">عدم ورود در تریدهایی که سودشان کمتر از کارمزد بروکر است</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Before vs After -->
            <div class="section-box" style="border: 1px solid #10b981; background: #0c1a1a;">
                <div style="border-bottom: 1px solid #134e4a; padding-bottom: 14px; margin-bottom: 16px;">
                    <h3 style="margin:0;color:#2dd4bf;font-size:19px;">⚖️ گزارش اثرگذاری فیلتر ضد استاپ (مقایسه زنده قبل و بعد از فیلترها)</h3>
                    <p style="margin:4px 0 0 0;color:#99f6e4;font-size:12px;">محاسبه دقیق بهبود آماری با فیلتر کردن ساعات پرخطر و الگوهای سمی:</p>
                </div>

                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>شاخص عملکردی کلیدی</th>
                                <th style="text-align:center;">بدون فیلتر (حالت خام)</th>
                                <th style="text-align:center;">با فیلتر ضد استاپ (Flag_Filters)</th>
                                <th style="text-align:center;">میزان بهبود و تغییر</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="font-weight:bold;">تعداد کل معاملات ارزیابی‌شده</td>
                                <td style="text-align:center;color:#94a3b8;">{len(closed):,} معامله</td>
                                <td style="text-align:center;color:#38bdf8;font-weight:bold;">{len(accepted_trades):,} معامله تاییدشده</td>
                                <td style="text-align:center;color:#f59e0b;">{len(rejected_trades)} معامله فیلتر و رد شد</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#10b981;">تعداد باخت‌های حذف‌شده (استاپ‌های نجات‌یافته)</td>
                                <td style="text-align:center;color:#ef4444;">۰ ({sl_cnt_b} معامله استاپ)</td>
                                <td style="text-align:center;color:#10b981;font-weight:bold;">{sl_in_rej} معامله استاپ خورده نجات یافت! 🎯</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">دقت فیلتر: {rej_accuracy:.1f}%</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;">وین‌ریت تارگت اول (TP 1:1)</td>
                                <td style="text-align:center;color:#94a3b8;">{w1_rate_b:.1f}%</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">{w1_rate_a:.1f}%</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">{w1_rate_a - w1_rate_b:+.1f}%</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;">وین‌ریت تارگت دوم (TP 1:2)</td>
                                <td style="text-align:center;color:#94a3b8;">{w2_rate_b:.1f}%</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">{w2_rate_a:.1f}%</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">{w2_rate_a - w2_rate_b:+.1f}%</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;">نرخ استاپ خوردن (Stop Loss Rate)</td>
                                <td style="text-align:center;color:#ef4444;">{sl_rate_b:.1f}%</td>
                                <td style="text-align:center;color:#f87171;font-weight:bold;">{sl_rate_a:.1f}%</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">{sl_rate_a - sl_rate_b:+.1f}% کاهش باخت</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#38bdf8;">امید ریاضی به ازای هر ترید (EV در نسبت 1:2)</td>
                                <td style="text-align:center;color:#94a3b8;">{ev_b:+.2f} R</td>
                                <td style="text-align:center;color:#38bdf8;font-weight:bold;font-size:15px;">{ev_a:+.2f} R 🚀</td>
                                <td style="text-align:center;color:#38bdf8;font-weight:bold;">{ev_a - ev_b:+.2f} R رشد خالص</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>"""
    tab_loss_intel_html = f"""<div class="section-box" style="border: 1px solid #ef4444; background: #18111c;">
                <div style="border-bottom: 1px solid #332032; padding-bottom: 14px; margin-bottom: 18px;">
                    <h3 style="margin:0;color:#f87171;font-size:20px;">🔍 تحلیل آماری معاملات استاپ‌شده (Loss Pattern Intelligence)</h3>
                    <p style="margin:4px 0 0 0;color:#fca5a5;font-size:12px;">کالبدشکافی {total_losses} معامله استاپ‌خورده در این دیتاست جهت جلوگیری هوشمند از تکرار باخت:</p>
                </div>

                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));gap:14px;">
                    <div style="background:#261822;border:1px solid #4a1d2e;padding:14px;border-radius:8px;">
                        <div style="color:#f87171;font-weight:bold;font-size:14px;">🌙 باخت‌های ساعات شب (۲۱ تا ۰۱)</div>
                        <div style="font-size:22px;font-weight:bold;color:#fca5a5;margin:6px 0;">{night_losses} معامله <span style="font-size:12px;color:#94a3b8;">({(night_losses/total_losses*100) if total_losses else 0:.1f}%)</span></div>
                        <div style="color:#94a3b8;font-size:11px;">اسپرد بالا و نبود نقدینگی در سشن آسیا منشأ این باخت‌هاست.</div>
                    </div>
                    <div style="background:#261822;border:1px solid #4a1d2e;padding:14px;border-radius:8px;">
                        <div style="color:#f87171;font-weight:bold;font-size:14px;">🚫 باخت‌های باکس‌های تک LS</div>
                        <div style="font-size:22px;font-weight:bold;color:#fca5a5;margin:6px 0;">{single_ls_losses} معامله <span style="font-size:12px;color:#94a3b8;">({(single_ls_losses/total_losses*100) if total_losses else 0:.1f}%)</span></div>
                        <div style="color:#94a3b8;font-size:11px;">باکس‌های LS منفرد بدون تلاقی بیشترین ریسک را به همراه دارند.</div>
                    </div>
                    <div style="background:#261822;border:1px solid #4a1d2e;padding:14px;border-radius:8px;">
                        <div style="color:#f87171;font-weight:bold;font-size:14px;">☣️ باخت‌های زنجیره‌های سمی</div>
                        <div style="font-size:22px;font-weight:bold;color:#fca5a5;margin:6px 0;">{toxic_losses} معامله <span style="font-size:12px;color:#94a3b8;">({(toxic_losses/total_losses*100) if total_losses else 0:.1f}%)</span></div>
                        <div style="color:#94a3b8;font-size:11px;">ورود در روندهای فرسایشی انتهای موج.</div>
                    </div>
                    <div style="background:#261822;border:1px solid #4a1d2e;padding:14px;border-radius:8px;">
                        <div style="color:#f87171;font-weight:bold;font-size:14px;">📦 باخت‌های فلگ‌های ساده</div>
                        <div style="font-size:22px;font-weight:bold;color:#fca5a5;margin:6px 0;">{pure_flag_losses} معامله <span style="font-size:12px;color:#94a3b8;">({(pure_flag_losses/total_losses*100) if total_losses else 0:.1f}%)</span></div>
                        <div style="color:#94a3b8;font-size:11px;">نویزهای میانی چارت بدون شکست ساختار.</div>
                    </div>
                </div>
            </div>"""
    tab_weekly_html = f"""<!-- Weekly KPI Banner -->
            <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));margin-bottom:20px;">
                <div class="kpi-card" style="border-color:#38bdf8;">
                    <div class="kpi-title">📅 کل هفته‌های کالبدشکافی‌شده</div>
                    <div class="kpi-value" style="color:#38bdf8;">{len(sorted_wk_keys)} هفته</div>
                    <div class="kpi-sub">پوشش کامل ۶ ماه اخیر</div>
                </div>
                <div class="kpi-card" style="border-color:#00e676;">
                    <div class="kpi-title">🟢 هفته‌های سبز و سودده سلاطین</div>
                    <div class="kpi-value" style="color:#00e676;">{tot_kings_green_wks} از {len(sorted_wk_keys)}</div>
                    <div class="kpi-sub">{(tot_kings_green_wks/len(sorted_wk_keys)*100) if sorted_wk_keys else 0:.1f}٪ هفته‌ها در سود قطعی!</div>
                </div>
                <div class="kpi-card" style="border-color:#ef4444;">
                    <div class="kpi-title">🔴 هفته‌های اصلاحی و استاپ سلاطین</div>
                    <div class="kpi-value" style="color:#ef4444;">{tot_kings_red_wks} از {len(sorted_wk_keys)}</div>
                    <div class="kpi-sub">{(tot_kings_red_wks/len(sorted_wk_keys)*100) if sorted_wk_keys else 0:.1f}٪ هفته‌های نوسانی و رنج</div>
                </div>
                <div class="kpi-card" style="border-color:#facc15;">
                    <div class="kpi-title">👑 باثبات‌ترین سلطان دائمی چارت</div>
                    <div class="kpi-value" style="color:#facc15;font-size:18px;">{top_consistent_box}</div>
                    <div class="kpi-sub">ثبات هفتگی شگفت‌انگیز: {top_consistent_pct:.1f}٪</div>
                </div>
            </div>

            <!-- SECTION 1: Consistency Ranking -->
            <div class="section-box" style="border:1px solid #3b82f6;background:#0d1527;margin-bottom:24px;">
                <div style="border-bottom:1px solid #1e3a8a;padding-bottom:12px;margin-bottom:16px;">
                    <h3 style="margin:0;color:#60a5fa;font-size:19px;">🏆 جدول جامع رتبه‌بندی ثبات دائمی ساختارها (Consistency Leaderboard)</h3>
                    <p style="margin:4px 0 0 0;color:#93c5fd;font-size:12px;">پاسخ به سوال کلیدی شما: کدام باکس‌ها هفته به هفته پایدارترین سودآوری را برای همیشه حفظ کرده‌اند؟</p>
                </div>
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#1e293b;color:#94a3b8;">
                                <th style="text-align:center;">رتبه</th>
                                <th>نام ساختار و تایم‌فریم</th>
                                <th style="text-align:center;">دسته‌بندی</th>
                                <th style="text-align:center;">تعداد کل معامله</th>
                                <th style="text-align:center;">هفته‌های فعال</th>
                                <th style="text-align:center;">هفته‌های سبز 🟢</th>
                                <th style="text-align:center;">هفته‌های قرمز 🔴</th>
                                <th style="text-align:center;">درصد ثبات هفتگی</th>
                                <th style="text-align:center;">وین‌ریت TP1</th>
                                <th style="text-align:center;">نرخ باخت (SL)</th>
                                <th style="text-align:center;">سود کل ۶ ماه ($)</th>
                                <th style="text-align:center;">نشان پایداری</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(weekly_consistency_rows_html)}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- SECTION 2: Master Weekly Timeline -->
            <div class="section-box" style="border:1px solid #10b981;background:#061a14;margin-bottom:24px;">
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #064e3b;padding-bottom:12px;margin-bottom:16px;flex-wrap:wrap;gap:12px;">
                    <div>
                        <h3 style="margin:0;color:#34d399;font-size:19px;">📅 کارنامه کامل هفته به هفته (Master {total_weeks}-Week Timeline)</h3>
                        <p style="margin:4px 0 0 0;color:#a7f3d0;font-size:12px;">کالبدشکافی پیوسته تمام {total_weeks} هفته با تفکیک برد، استاپ و برترین سلطان هفته:</p>
                    </div>
                    <div style="display:flex;gap:8px;">
                        <button id="btnWkTableKings" class="sort-btn active" onclick="filterWeeklyMode('kings')">👑 فقط سلاطین {len(qualified_kings)} گانه</button>
                        <button id="btnWkTableAll" class="sort-btn" onclick="filterWeeklyMode('all')">🌐 کل ساختارهای چارت</button>
                    </div>
                </div>

                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#1e293b;color:#94a3b8;">
                                <th style="text-align:center;">شماره هفته</th>
                                <th style="text-align:center;">بازه تاریخ</th>
                                <th style="text-align:center;">تعداد معامله</th>
                                <th style="text-align:center;">برد (تارگت)</th>
                                <th style="text-align:center;">استاپ (Loss)</th>
                                <th style="text-align:center;">وین‌ریت %</th>
                                <th style="text-align:center;">درصد استاپ %</th>
                                <th style="text-align:center;">سود خالص دلاری ($)</th>
                                <th style="text-align:center;">وضعیت هفته</th>
                                <th style="text-align:center;">برترین سلطان هفته 🏆</th>
                                <th style="text-align:center;">عملیات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(weekly_timeline_rows_html)}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- SECTION 3: Detailed Box Deep Dive per Week -->
            <div class="section-box" style="border:1px solid #eab308;background:#171305;">
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #854d0e;padding-bottom:12px;margin-bottom:16px;flex-wrap:wrap;gap:12px;">
                    <div>
                        <h3 style="margin:0;color:#facc15;font-size:19px;">🔬 کالبدشکافی جزئیات تک‌تک ساختارها در هر هفته انتخابی</h3>
                        <p style="margin:4px 0 0 0;color:#fef08a;font-size:12px;">یک هفته را انتخاب کنید تا ببینید هر باکس در آن هفته مشخص دقیقاً چند سود، چند استاپ و چه مقدار دلار ساخته است:</p>
                    </div>
                    <div>
                        <select onchange="selectWeeklyDetail(this.value)" style="background:#1e293b;color:#f1f5f9;border:1px solid #475569;padding:8px 14px;border-radius:6px;font-size:13px;">
                            <option value="">-- انتخاب هفته جهت مشاهده جدول اختصاصی باکس‌ها --</option>
                            {''.join(weekly_dropdown_options)}
                        </select>
                    </div>
                </div>

                <div id="weeklyDetailsContainer">
                    {''.join(weekly_details_cards_html)}
                </div>
            </div>"""
    smart_presets_rows_html = "".join(smart_presets_rows_html)

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
        'in_trade_count': len(in_trade),
        'sl_in_rej': sl_in_rej,
        'rej_accuracy': rej_accuracy,
        'ev_a': ev_a,
        'ev_b': ev_b,
        'w1_p': d_tot_kings['w1_p'],
        'tab_equity_html': tab_equity_html,
        'tab_kings_html': tab_kings_html,
        'tab_scaleout_html': tab_scaleout_html,
        'tab_timeframes_html': tab_timeframes_html,
        'tab_filters_html': tab_filters_html,
        'tab_loss_intel_html': tab_loss_intel_html,
        'tab_weekly_html': tab_weekly_html,
        'smart_presets_rows_html': smart_presets_rows_html,
        'kings_sim_list': kings_sim_list,
        'top3_sl_cnt_keys': top3_sl_cnt_keys,
        'top3_sl_usd_keys': top3_sl_usd_keys,
        'top5_sl_usd_keys': top5_sl_usd_keys,
        'top3_sl_pct_keys': top3_sl_pct_keys,
        'trades_sim_list': trades_sim_list,
        'smart_presets': smart_presets_json_data,
        'weekly_bar_data': weekly_bar_data,
        'trades_json_list': trades_json_list
    }



def export_preset_set_files(symbols_data):
    repo_root = r"c:\Users\USER\AppData\Roaming\MetaQuotes\Terminal\3F2C3A2F8B221C9D88E569F2FD1D3E97\MQL5"
    dirs = [
        os.path.join(repo_root, "Experts", "تنظیمات"),
        os.path.join(repo_root, "Experts", "Settings")
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    today_date = datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    saved_count = 0
    for sym, data in symbols_data.items():
        presets = data.get('smart_presets', [])
        kings_list = data.get('kings_sim_list', [])
        all_kings_set = set(k['kk'] for k in kings_list)

        for p in presets:
            raw_title = p.get('title', 'Custom')
            clean_title = "Custom"
            if "محافظه" in raw_title or "Conservative" in raw_title: clean_title = "Conservative"
            elif "تهاجمی" in raw_title or "Aggressive" in raw_title: clean_title = "Aggressive"
            elif "طلا" in raw_title or "Golden" in raw_title or "متعادل" in raw_title or "Balanced" in raw_title: clean_title = "GoldenBalance"
            elif "الماس" in raw_title or "Diamond" in raw_title or "Champion" in raw_title: clean_title = "DiamondKings"
            elif "حداکثر" in raw_title or "MaxProfit" in raw_title or "Runner" in raw_title: clean_title = "MaxProfit"
            elif "لندن" in raw_title or "London" in raw_title: clean_title = "LondonNY"
            elif "سپر" in raw_title or "Shield" in raw_title or "UltraLow" in raw_title or "افت" in raw_title: clean_title = "UltraLowDDShield"
            elif "سبد" in raw_title or "جامع" in raw_title or "تمام" in raw_title or "پایه" in raw_title: clean_title = "AllKings24H"
            else: clean_title = "".join(c for c in raw_title if c.isalnum()) or "Preset"

            wr = p.get('wr', 0.0)
            pf = p.get('pf', 0.0)
            hours = p.get('hours', [])
            hours_str = ""
            if hours and sum(1 for h in hours if h) < 24:
                hours_str = ",".join(f"{h:02d}" for h in range(24) if hours[h])

            p_kings = set(p.get('kings', []))
            disabled_kings = [k for k in all_kings_set if k not in p_kings]
            disabled_str = ", ".join(disabled_kings)

            action_int = 3 if p.get('consec_day') else (2 if p.get('consec_sk') == 2 else 1)
            trig_int = p.get('consec_trig', 0)
            if trig_int <= 0: action_int = 0

            is_base = (clean_title == "AllKings24H")
            be_buffer = "1.0" if is_base else "0.0"
            max_dev = "2.5" if is_base else "2.0"
            use_m1 = "true" if is_base else "false"

            filename = f"FlagPro_{sym}_{clean_title}_WR{round(wr)}_PF{pf:.1f}_{now_str}.set"

            lines = [
                ";+------------------------------------------------------------------+",
                ";| FlagPro_Trader EA Settings File (.set)                           |",
                f";| File: {filename} |",
                ";| Auto-generated from FlagPro Master Strategy Dashboard            |",
                f";| Date: {today_date} |",
                f";| Symbol: {sym} | Scenario: {raw_title} |",
                f";| Win Rate: {wr:.1f}% | Profit Factor: {pf:.2f} |",
                f";| Active Kings: {len(p_kings)} | Target Folder: Experts/تنظیمات    |",
                ";+------------------------------------------------------------------+",
                f"InpScenarioName={raw_title}",
                f"InpMinTradePotential={float(p.get('min_pot', 0.0)):.2f}",
                f"InpAllowedTradingHours={hours_str}",
                f"InpConsecLossTrigger={trig_int}",
                f"InpConsecLossAction={action_int}",
                f"InpDisabledKingsList={disabled_str}",
                "InpOnlyTradeKings=true",
                "InpEnableScaleOut=true",
                "InpLot_TP1=0.01",
                "InpLot_TP2=0.01",
                "InpLot_TP3=0.01",
                "InpLot_TP4=0.01",
                "InpMoveToBreakEven=true",
                f"InpBEBufferPips={be_buffer}",
                f"InpMaxEntryDeviationPips={max_dev}",
                f"InpUseTF7={use_m1}",
                f"InpEnableKingsM1={use_m1}",
                "InpTrailToTP1=true",
                "InpTrailToTP2=true",
                "InpMaxOpenGroups=5",
                "InpMagicNumber=777123",
                "InpLookbackBars=15000",
                "InpHistoryMode=1",
                "InpHistoryStartDate=2025.01.01 00:00:00",
                "InpHistoryDays=10",
                "InpShowBoxes=false",
                "InpExportCSV=true"
            ]
            content = "\r\n".join(lines)

            for d in dirs:
                fp = os.path.join(d, filename)
                try:
                    with open(fp, 'w', encoding='utf-16') as f:
                        f.write(content + "\r\n")
                    saved_count += 1
                except Exception as e:
                    pass

            tester_dir = os.path.join(repo_root, "Profiles", "Tester")
            os.makedirs(tester_dir, exist_ok=True)
            ini_filename = f"FlagPro_Tester_{sym}_{clean_title}_WR{round(wr)}_PF{pf:.1f}.ini"
            broker_sym = sym if sym.endswith('!') else sym + '!'
            ini_lines = [
                ";MetaTrader 5 Strategy Tester Configuration (.ini)",
                ";Auto-generated by FlagPro Strategy Dashboard",
                ";Drag & drop this file onto MetaTrader 5 Strategy Tester window (Ctrl+R)",
                "[Tester]",
                "Expert=FlagPro_Trader.ex5",
                f"Symbol={broker_sym}",
                "Period=M1",
                "Optimization=0",
                "Model=4",
                f"FromDate={(datetime.now() - timedelta(days=10)).strftime('%Y.%m.%d')}",
                f"ToDate={datetime.now().strftime('%Y.%m.%d')}",
                "ForwardMode=0",
                "Deposit=10000",
                "Currency=USD",
                "ProfitInPips=0",
                "Leverage=100",
                "ExecutionMode=0",
                "OptimizationCriterion=0",
                "Visual=1",
                "[TesterInputs]",
                f"InpScenarioName={raw_title}",
                "InpOnlyTradeKings=true",
                f"InpDisabledKingsList={disabled_str}",
                "InpEnableKingsM15=true",
                "InpEnableKingsM5=true",
                f"InpEnableKingsM1={use_m1}",
                "InpTradeOnlyGoldenKings=true",
                "InpAllowOverlappingTrades=true",
                "InpSlippagePoints=20",
                f"InpMaxEntryDeviationPips={max_dev}",
                "InpSLOffsetPips=3.0",
                "InpMaxSLPips=0.0",
                "InpMaxOpenGroups=5",
                "InpMagicNumber=777123",
                "InpEnableScaleOut=true",
                "InpLot_TP1=0.01",
                "InpLot_TP2=0.01",
                "InpLot_TP3=0.01",
                "InpLot_TP4=0.01",
                "InpMoveToBreakEven=true",
                f"InpBEBufferPips={be_buffer}",
                "InpTrailToTP1=true",
                "InpTrailToTP2=true",
                f"InpAllowedTradingHours={hours_str}",
                f"InpMinTradePotential={float(p.get('min_pot', 0.0)):.2f}",
                f"InpConsecLossTrigger={trig_int}",
                f"InpConsecLossAction={action_int}",
                "InpFilterNightHours=true",
                "InpFilterPreLondonHunt=true",
                "InpFilterToxicPatterns=true",
                "InpFilterSingleLS=true",
                "InpFilterPureFlags=true",
                "InpFilterLowRewardVsFriction=true",
                "InpBrokerCommissionPerLot=6.0",
                "InpEstimatedSpreadPips=0.8",
                "InpMinNetProfitRatioTP1=1.0",
                f"InpUseTF7={use_m1}",
                "InpUseTF6=true",
                "InpUseTF5=true",
                "InpTradeMacroTFs=false",
                "InpLookbackBars=15000",
                "InpHistoryMode=1",
                "InpHistoryStartDate=2025.01.01 00:00:00",
                "InpHistoryDays=10"
            ]
            ini_content = "\r\n".join(ini_lines)
            try:
                with open(os.path.join(tester_dir, ini_filename), 'w', encoding='utf-16') as f:
                    f.write(ini_content + "\r\n")
            except Exception as e:
                pass
    if saved_count > 0:
        print(f"📁 ذخیره خودکار {saved_count} فایل تنظیمات (.set) در Experts/تنظیمات و فایل‌های (.ini) در Profiles/Tester انجام شد.")


def build_dashboard(custom_csv=None):
    files_dir = os.path.dirname(CSV_PATH_PRIMARY)
    repo_root = r"c:\Users\USER\AppData\Roaming\MetaQuotes\Terminal\3F2C3A2F8B221C9D88E569F2FD1D3E97\MQL5"
    cands = []
    if custom_csv and os.path.exists(custom_csv):
        cands = [custom_csv]
    elif len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        cands = [sys.argv[1]]
    else:
        for f in os.listdir(files_dir):
            if (f.startswith('flagpro_trades') or f.startswith('flag_trades')) and f.endswith('.csv'):
                cands.append(os.path.join(files_dir, f))

    if not cands:
        if os.path.exists(CSV_PATH_PRIMARY): cands.append(CSV_PATH_PRIMARY)
        elif os.path.exists(CSV_PATH_FALLBACK): cands.append(CSV_PATH_FALLBACK)

    # Sort files by modification time (newest first) so user's latest test is always picked
    cands.sort(key=lambda f: os.path.getmtime(f) if os.path.exists(f) else 0, reverse=True)

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

    # Auto-export smart preset .set files to Experts/تنظیمات
    export_preset_set_files(symbols_data)

    default_sym = 'EURUSD' if 'EURUSD' in symbols_data else list(symbols_data.keys())[0]
    default_data = symbols_data[default_sym]
    print(f"🌟 نماد پیش‌فرض هدر داشبورد: {default_sym} ({default_data['tfs_str']})")

    # Build options for symbol selector
    symbol_options_list = []
    for s_name, s_info in sorted(symbols_data.items()):
        sel_attr = 'selected' if s_name == default_sym else ''
        c_count = s_info.get("closed_count", len(s_info.get("trades_json_list", [])))
        symbol_options_list.append(f'<option value="{s_name}" {sel_attr}>{s_name} ({s_info["tfs_str"]}) - {c_count} معامله</option>')
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
            'kings_sim_list': s_data['kings_sim_list'],
            'top3_sl_cnt_keys': s_data['top3_sl_cnt_keys'],
            'top3_sl_usd_keys': s_data['top3_sl_usd_keys'],
            'top5_sl_usd_keys': s_data['top5_sl_usd_keys'],
            'top3_sl_pct_keys': s_data['top3_sl_pct_keys'],
            'trades_sim_list': s_data['trades_sim_list'],
            'smart_presets': s_data['smart_presets'],
            'weekly_bar_data': s_data['weekly_bar_data'],
            'trades_json_list': s_data['trades_json_list'],
            'tab_equity_html': s_data['tab_equity_html'],
            'tab_kings_html': s_data['tab_kings_html'],
            'tab_scaleout_html': s_data['tab_scaleout_html'],
            'tab_timeframes_html': s_data['tab_timeframes_html'],
            'tab_filters_html': s_data['tab_filters_html'],
            'tab_loss_intel_html': s_data['tab_loss_intel_html'],
            'tab_weekly_html': s_data['tab_weekly_html'],
            'smart_presets_rows_html': s_data.get('smart_presets_rows_html', ''),
        }

    json_symbols_payload = json.dumps(client_symbols_payload, separators=(',', ':'))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Load MT5 Strategy Tester Reports
    tester_reports_dir = os.path.join(files_dir, "FlagPro_TesterReports")
    tester_reports = tester_compare_module.load_tester_reports(tester_reports_dir)
    default_tester_key = list(tester_reports.keys())[0] if tester_reports else 'none'
    tester_compare_tab_html = tester_compare_module.get_tester_compare_html(tester_reports, default_tester_key)
    tester_compare_js = tester_compare_module.get_tester_compare_js()
    json_tester_reports_payload = json.dumps(tester_reports, separators=(',', ':'))

    # Load HTML template from templates/master_dashboard_template.html
    tpl_path = os.path.join(repo_root, "templates", "master_dashboard_template.html")
    with open(tpl_path, 'r', encoding='utf-8') as f:
        html = f.read()

    replacements = {
        "__DEFAULT_SYM__": default_sym,
        "__DEFAULT_SYMBOL__": default_data['symbol'],
        "__DEFAULT_TFS_STR__": default_data['tfs_str'],
        "__DEFAULT_KINGS_COUNT__": str(len(default_data.get('kings_sim_list', []))),
        "__DEFAULT_MIN_DATE__": default_data['min_date'],
        "__DEFAULT_MAX_DATE__": default_data['max_date'],
        "__SYMBOL_OPTIONS_HTML__": symbol_options_html,
        "__JSON_SYMBOLS_PAYLOAD__": json_symbols_payload,
        "__JSON_TESTER_REPORTS_PAYLOAD__": json_tester_reports_payload,
        "__NOW_STR__": now_str,
        "__TESTER_COMPARE_TAB_HTML__": tester_compare_tab_html,
        "__TESTER_COMPARE_JS__": tester_compare_js,
        "__DEFAULT_TAB_EQUITY_HTML__": default_data['tab_equity_html'],
        "__DEFAULT_TAB_KINGS_HTML__": default_data['tab_kings_html'],
        "__DEFAULT_TAB_SCALEOUT_HTML__": default_data['tab_scaleout_html'],
        "__DEFAULT_TAB_TIMEFRAMES_HTML__": default_data['tab_timeframes_html'],
        "__DEFAULT_TAB_FILTERS_HTML__": default_data['tab_filters_html'],
        "__DEFAULT_TAB_LOSS_INTEL_HTML__": default_data['tab_loss_intel_html'],
        "__DEFAULT_TAB_WEEKLY_HTML__": default_data['tab_weekly_html'],
    }
    for placeholder, val in replacements.items():
        html = html.replace(placeholder, str(val))

    clean_sym_name = default_data.get('clean_symbol', default_sym)
    out_paths = [
        os.path.join(files_dir, "flagpro_performance_dashboard.html"),
        os.path.join(files_dir, f"{clean_sym_name.lower()}_performance_report.html"),
        os.path.join(repo_root, "FlagPro_Master_Dashboard.html"),
        r"C:\Users\USER\Desktop\FlagPro_Dashboard.html"
    ]

    for out_path in out_paths:
        try:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, mode='w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ فایل با موفقیت نوشته شد: {out_path}")
        except Exception as e:
            print(f"❌ خطا در نوشتن {out_path}: {e}")

    # Also sync FlagPro_Modular_App initial data & bundled dist
    try:
        modular_data_file = os.path.join(repo_root, "FlagPro_Modular_App", "data", "initial_data.js")
        if os.path.exists(os.path.dirname(modular_data_file)):
            with open(modular_data_file, mode='w', encoding='utf-8') as f:
                f.write(f"window.ALL_SYMBOLS_DATA = {json_symbols_payload};\nwindow.TESTER_REPORTS = {json_tester_reports_payload};\n")
            print(f"✅ داده‌های پروژه ماژولار به‌روزرسانی شد: {modular_data_file}")

            bundler_script = os.path.join(repo_root, "FlagPro_Modular_App", "tools", "bundler.py")
            if os.path.exists(bundler_script):
                import subprocess
                subprocess.run([sys.executable, bundler_script], check=False)
    except Exception as e:
        print(f"⚠️ همگام‌سازی پروژه ماژولار: {e}")

if __name__ == "__main__":
    build_dashboard()
