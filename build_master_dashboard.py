import os
import sys
import csv
import math
import re
from collections import defaultdict
from datetime import datetime, timedelta

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

def build_dashboard(custom_csv=None):
    if custom_csv and os.path.exists(custom_csv):
        csv_file = custom_csv
    elif len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        csv_file = sys.argv[1]
    else:
        files_dir = os.path.dirname(CSV_PATH_PRIMARY)
        cands = [os.path.join(files_dir, f) for f in os.listdir(files_dir) 
                 if (f.startswith('flagpro_trades') or f.startswith('flag_trades')) and f.endswith('.csv')]
        if cands:
            cands.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            csv_file = cands[0]
        elif os.path.exists(CSV_PATH_PRIMARY):
            csv_file = CSV_PATH_PRIMARY
        elif os.path.exists(CSV_PATH_FALLBACK):
            csv_file = CSV_PATH_FALLBACK
        else:
            print(f"CSV not found in: {files_dir}")
            return

    print(f"📂 در حال پردازش فایل دیتا: {csv_file}")

    all_raw_rows = []
    with open(csv_file, mode='r', encoding='utf-8-sig', errors='ignore') as f:
        for r in csv.DictReader(f):
            all_raw_rows.append(r)

    # Dynamic Symbol Detection
    symbol = 'EURUSD'
    if all_raw_rows and all_raw_rows[0].get('Symbol'):
        symbol = all_raw_rows[0].get('Symbol').strip()
    else:
        m = re.search(r'flagpro_trades_([A-Za-z0-9_]+)\.csv', os.path.basename(csv_file))
        if m: symbol = m.group(1).upper()

    clean_symbol = re.sub(r'[^A-Za-z0-9]', '', symbol) or 'EURUSD'

    available_tfs = sorted(list(set(r.get('Timeframe') for r in all_raw_rows if r.get('Timeframe'))))
    if not available_tfs: available_tfs = ['M1', 'M5', 'M15']
    tfs_str = ', '.join(available_tfs)

    rows = [r for r in all_raw_rows if r.get('Timeframe') in available_tfs]
    total_setups = len(rows)
    entered = [r for r in rows if r.get('Outcome') != 'Pending']
    closed = [r for r in entered if r.get('IsClosed') == 'True']
    in_trade = [r for r in entered if r.get('IsClosed') != 'True']

    dates = [r.get('BoxTimeStart') for r in rows if r.get('BoxTimeStart') and r.get('BoxTimeStart') != 'None']
    min_date = min(dates) if dates else 'نامشخص'
    max_date = max(dates) if dates else 'نامشخص'
    entry_dates = [r.get('EntryTime', '') for r in closed if r.get('EntryTime')]
    date_start_str = min(entry_dates)[:10] if entry_dates else min_date
    date_end_str = max(entry_dates)[:10] if entry_dates else max_date

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
    # EQUITY & BALANCE CURVE ENGINE (منحنی رشد سرمایه و بالانس به سبک متاتریدر)
    # =========================================================================
    sorted_closed = sorted(closed, key=lambda x: x.get('ExitTime', x.get('EntryTime', '')))
    bal_initial = 10000.0
    bal_k = bal_initial
    bal_a = bal_initial

    pts_kings = [{'idx': 0, 't': '2026.03.09 00:00', 'b': round(bal_k, 2), 'p': 0.0, 'n': 'موجودی اولیه (Initial Balance)'}]
    pts_all = [{'idx': 0, 't': '2026.03.09 00:00', 'b': round(bal_a, 2), 'p': 0.0, 'n': 'موجودی اولیه (Initial Balance)'}]

    peak_k = bal_initial
    max_dd_k = 0.0
    peak_a = bal_initial
    max_dd_a = 0.0

    for r in sorted_closed:
        pnl = calc_scaleout_pnl(r)
        et = r.get('EntryTime', '')
        role = r.get('Role', '')
        tf = r.get('Timeframe', '')
        b_name = f"{role} [{tf}]"
        
        # All
        bal_a += pnl
        pts_all.append({'idx': len(pts_all), 't': et, 'b': round(bal_a, 2), 'p': round(pnl, 2), 'n': b_name})
        if bal_a > peak_a: peak_a = bal_a
        dd_a = peak_a - bal_a
        if dd_a > max_dd_a: max_dd_a = dd_a
        
        # Kings
        if (role, tf) in king_keys:
            bal_k += pnl
            pts_kings.append({'idx': len(pts_kings), 't': et, 'b': round(bal_k, 2), 'p': round(pnl, 2), 'n': b_name})
            if bal_k > peak_k: peak_k = bal_k
            dd_k = peak_k - bal_k
            if dd_k > max_dd_k: max_dd_k = dd_k

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
        h_val = int(et[11:13]) if len(et) >= 13 else 0
        trades_sim_list.append({
            'i': idx,
            't': et,
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

    # ==================== DYNAMIC AUTO-OPTIMIZER ENGINE ====================
    all_sim_k_keys = [k['kk'] for k in kings_sim_list]
    total_base_trades = len(trades_sim_list)
    min_15pct_trades = max(20, int(total_base_trades * 0.15))
    min_35pct_trades = max(35, int(total_base_trades * 0.35))

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
                    bal = 10000.0; peak = bal; max_dd = 0.0; wins = 0; total = 0; gp = 0.0; gl = 0.0
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
                    net = bal - 10000.0
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
    opt_p1 = evaluated_combos[0] if evaluated_combos else None

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
            'strategy_desc': f'معامله در ساعات پرقدرت روز با اسپرد پایین و تاییدیه مومنتوم - PF {opt_p3["pf"]:.2f} و افت ${opt_p3["max_dd"]:.2f}',
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
            'badge': f'🛡️ حداقل افت: ${opt_p4["max_dd"]:.2f}',
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
        
        bal = 10000.0
        peak = 10000.0
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
            <td style="text-align:center;padding:10px 8px;font-weight:bold;font-size:13px;color:#facc15;">#{p['idx']+1}</td>
            <td style="padding:10px 12px;">
                <div style="font-weight:bold;color:#f1f5f9;font-size:13px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                    <span>{p['title']}</span>
                    {featured_tag}
                </div>
                <div style="color:#94a3b8;font-size:11px;margin-top:3px;">{p['strategy_desc']}</div>
            </td>
            <td style="padding:10px 10px;font-size:11.5px;color:#cbd5e1;text-align:center;">
                <div>{p['filter_desc']}</div>
            </td>
            <td style="text-align:center;padding:10px 8px;font-size:12px;font-weight:bold;color:#38bdf8;">
                {len(p['kings'])} سلطان
            </td>
            <td style="text-align:center;padding:10px 8px;font-weight:bold;font-size:13px;color:#e2e8f0;">
                {c:,}
            </td>
            <td style="text-align:center;padding:10px 8px;font-weight:bold;color:#34d399;font-size:13px;">
                {wr:.1f}٪
            </td>
            <td style="text-align:center;padding:10px 8px;font-weight:bold;color:#38bdf8;font-size:13.5px;">
                {pf_display}
            </td>
            <td style="text-align:center;padding:10px 8px;font-weight:bold;color:#facc15;font-size:13.5px;">
                ${avg:+.2f}
            </td>
            <td style="text-align:center;padding:10px 8px;font-weight:bold;color:#fca5a5;font-size:12.5px;">
                ${max_dd:.2f}
            </td>
            <td style="text-align:center;padding:10px 10px;font-weight:bold;color:{net_col};font-size:15px;background:#064e3b22;">
                ${nt:+,.2f}
            </td>
            <td style="text-align:center;padding:10px 10px;">
                <button id="btnApplyPreset{p['idx']}" class="apply-preset-btn" onclick="applySmartPreset({p['idx']})" style="background:linear-gradient(135deg, #0284c7, #0369a1);border:1px solid #38bdf8;color:#fff;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;transition:all 0.2s;white-space:nowrap;box-shadow:0 2px 8px rgba(2,132,199,0.3);">
                    ⚡ اعمال روی نمودار
                </button>
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

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>داشبورد جامع و هوشمند FlagPro - ساختار تبولار (بدون اسکرول)</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            background-color: #070b14;
            color: #f1f5f9;
            margin: 0;
            padding: 0;
            line-height: 1.4;
            overflow: hidden;
            height: 100vh;
            direction: rtl;
        }}
        .app-layout {{
            display: flex;
            height: 100vh;
            width: 100vw;
            overflow: hidden;
            direction: rtl;
        }}

        /* 📌 SLEEK COMPACT SIDEBAR */
        .sidebar {{
            width: 215px;
            min-width: 215px;
            max-width: 215px;
            background: #090e1a;
            border-left: 1px solid #1e293b;
            display: flex;
            flex-direction: column;
            height: 100vh;
            z-index: 1000;
            box-shadow: -4px 0 20px rgba(0,0,0,0.5);
            user-select: none;
        }}
        .sidebar-brand {{
            padding: 14px 12px;
            border-bottom: 1px solid #1e293b;
            display: flex;
            align-items: center;
            gap: 10px;
            background: #060a12;
        }}
        .sidebar-brand-title {{
            font-size: 14.5px;
            font-weight: bold;
            color: #38bdf8;
            margin: 0;
            letter-spacing: -0.2px;
        }}
        .sidebar-brand-sub {{
            font-size: 10px;
            color: #64748b;
            margin: 2px 0 0 0;
        }}
        .sidebar-menu {{
            padding: 8px 6px;
            display: flex;
            flex-direction: column;
            gap: 3px;
            flex: 1;
            overflow-y: auto;
        }}
        .tab-btn {{
            background: transparent;
            border: 1px solid transparent;
            color: #94a3b8;
            padding: 8px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            width: 100%;
            text-align: right;
            box-sizing: border-box;
        }}
        .tab-btn:hover {{
            color: #f8fafc;
            background: #1e293b;
            border-color: #334155;
        }}
        .tab-btn.active {{
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            color: #ffffff;
            border-color: #38bdf8;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35);
        }}
        .tab-btn .tab-icon {{
            font-size: 14px;
            min-width: 18px;
            text-align: center;
        }}
        .tab-btn .tab-title {{
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .sidebar-footer {{
            padding: 10px 12px;
            border-top: 1px solid #1e293b;
            font-size: 10px;
            color: #64748b;
            background: #060a12;
            line-height: 1.4;
        }}

        /* 🖥️ MAIN WORKSPACE CONTENT */
        .main-workspace {{
            flex: 1;
            min-width: 0;
            height: 100vh;
            overflow-y: auto;
            padding: 12px 18px;
            box-sizing: border-box;
            background: #070b14;
        }}

        /* Compact Header */
        .workspace-header {{
            background: linear-gradient(135deg, #0f172a 0%, #090e1a 100%);
            border: 1px solid #1e293b;
            padding: 10px 16px;
            border-radius: 8px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .workspace-header h1 {{
            margin: 0;
            font-size: 16px;
            color: #38bdf8;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        /* Institutional Metric Cards */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 8px;
            margin-bottom: 10px;
        }}
        .kpi-card {{
            background: #0f172a;
            border: 1px solid #334155;
            padding: 7px 12px;
            border-radius: 8px;
            text-align: center;
        }}
        .kpi-title {{
            font-size: 10.5px;
            color: #94a3b8;
            margin-bottom: 3px;
        }}
        .kpi-value {{
            font-size: 18px;
            font-weight: bold;
            color: #f8fafc;
        }}
        .kpi-sub {{
            font-size: 9.5px;
            color: #64748b;
            margin-top: 2px;
        }}

        /* Subtabs in Equity Curve */
        .eq-subtab-btn {{
            background: #0f172a;
            border: 1px solid #334155;
            color: #94a3b8;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 11.5px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .eq-subtab-btn:hover {{
            color: #fff;
            border-color: #38bdf8;
            background: #1e293b;
        }}
                .consec-btn, .consec-btn-filter {{
            background: #0f172a;
            border: 1px solid #334155;
            color: #94a3b8;
            padding: 5px 11px;
            border-radius: 6px;
            font-size: 11.5px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .consec-btn:hover, .consec-btn-filter:hover {{
            color: #f8fafc;
            border-color: #38bdf8;
        }}
        .consec-btn.active, .consec-btn-filter.active {{
            background: #0c4a6e;
            border-color: #38bdf8;
            color: #38bdf8;
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.25);
        }}

                /* 🌟 TWO-COLUMN WORKSPACE LAYOUT */
        .equity-two-col-container {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
            gap: 12px;
            align-items: stretch;
            margin-bottom: 12px;
        }}
        .equity-two-col-container.single-col {{
            grid-template-columns: 1fr !important;
        }}
        .equity-col-chart, .equity-col-controls {{
            min-width: 0;
            display: flex;
            flex-direction: column;
        }}
        .eq-subpanels-wrapper {{
            flex: 1;
            overflow-y: auto;
            overflow-x: auto;
            max-height: 485px;
            padding-left: 2px;
        }}
        .eq-subpanels-wrapper::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        .eq-subpanels-wrapper::-webkit-scrollbar-track {{
            background: #060a12;
            border-radius: 4px;
        }}
        .eq-subpanels-wrapper::-webkit-scrollbar-thumb {{
            background: #1e3a5f;
            border-radius: 4px;
        }}
        .eq-subpanels-wrapper::-webkit-scrollbar-thumb:hover {{
            background: #38bdf8;
        }}
        @media (max-width: 1250px) {{
            .equity-two-col-container {{
                grid-template-columns: 1fr;
            }}
        }}

        .eq-subtab-btn.active {{
            background: #0284c7;
            color: #fff;
            border-color: #38bdf8;
            font-weight: bold;
            box-shadow: 0 2px 8px rgba(2, 132, 199, 0.4);
        }}

        /* Tab Content Panel */
        .tab-content {{
            display: none;
            animation: fadeIn 0.2s ease;
        }}
        .tab-content.active {{
            display: block;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(4px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .section-box {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 22px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 12px;
        }}
        th, td {{
            padding: 10px 12px;
            border-bottom: 1px solid #334155;
            text-align: right;
        }}
        th {{
            background: #0f172a;
            color: #94a3b8;
            font-weight: 600;
        }}
        tr:hover {{
            background: #1e293b80;
        }}
        .sort-btn {{
            background: #1e293b;
            border: 1px solid #334155;
            color: #94a3b8;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
            margin-left: 6px;
        }}
        .sort-btn.active, .sort-btn:hover {{
            background: #38bdf8;
            color: #0f172a;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="app-layout">
        <!-- 📌 COMPACT SIDEBAR NAVIGATION (RIGHT SIDE IN RTL) -->
        <aside class="sidebar">
            <div class="sidebar-brand">
                <div style="font-size:22px;">🎯</div>
                <div>
                    <div class="sidebar-brand-title">FlagPro Master</div>
                    <div class="sidebar-brand-sub">{symbol} | {tfs_str}</div>
                </div>
            </div>

            <div class="sidebar-menu">
                <button class="tab-btn active" onclick="openTab(event, 'tab-equity')">
                    <span class="tab-icon">📈</span>
                    <span class="tab-title">نمودار رشد و اکوئیتی</span>
                </button>
                <button class="tab-btn" onclick="openTab(event, 'tab-kings')">
                    <span class="tab-icon">👑</span>
                    <span class="tab-title">سلاطین برگزیده ({len(qualified_kings)})</span>
                </button>
                <button class="tab-btn" onclick="openTab(event, 'tab-trades')">
                    <span class="tab-icon">📑</span>
                    <span class="tab-title">ژورنال معاملات و خروج</span>
                </button>
                <button class="tab-btn" onclick="openTab(event, 'tab-scaleout')">
                    <span class="tab-icon">💎</span>
                    <span class="tab-title">خروج پلکانی (0.04)</span>
                </button>
                <button class="tab-btn" onclick="openTab(event, 'tab-timeframes')">
                    <span class="tab-icon">📊</span>
                    <span class="tab-title">عملکرد تایم‌فریم‌ها</span>
                </button>
                <button class="tab-btn" onclick="openTab(event, 'tab-weekly')">
                    <span class="tab-icon">📅</span>
                    <span class="tab-title">کارنامه هفته به هفته</span>
                </button>
                <button class="tab-btn" onclick="openTab(event, 'tab-filters')">
                    <span class="tab-icon">🛡️</span>
                    <span class="tab-title">فیلترهای ضد استاپ</span>
                </button>
                <button class="tab-btn" onclick="openTab(event, 'tab-loss-intel')">
                    <span class="tab-icon">🔍</span>
                    <span class="tab-title">هوش باخت‌ها و استاپ‌ها</span>
                </button>
            </div>

            <div class="sidebar-footer">
                <div>🔄 آخرین همگام‌سازی:</div>
                <div style="color:#38bdf8;font-weight:bold;margin-top:2px;">{now_str}</div>
            </div>
        </aside>

        <!-- 🖥️ MAIN WORKSPACE CONTENT -->
        <main class="main-workspace">
            <!-- Workspace Top Bar -->
            <div class="workspace-header">
                <div>
                    <h1>🎯 سیستم جامع معاملاتی FlagPro</h1>
                    <div style="margin-top:3px;color:#94a3b8;font-size:11.5px;">
                        بازه داده‌ها: <b>{min_date}</b> تا <b>{max_date}</b> | حجم: <b>0.04 لات پلکانی</b>
                    </div>
                </div>
                <div>
                    <span style="background:#081420;border:1px solid #1e3a5f;padding:4px 10px;border-radius:6px;font-size:11px;color:#38bdf8;">
                        {symbol} ({tfs_str})
                    </span>
                </div>
            </div>


        <!-- ==================== TAB: 📈 EQUITY & BALANCE CURVE ==================== -->
        <div id="tab-equity" class="tab-content active">
            <!-- Equity Metrics Banner (Dynamically updated by simulation) -->
            <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));gap:8px;margin-bottom:10px;">
                <div class="kpi-card" style="border-color:#38bdf8;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">💵 بالانس شروع حساب</div>
                    <div class="kpi-value" style="color:#f1f5f9;font-size:16px;">${bal_initial:,.2f}</div>
                    <div class="kpi-sub" style="font-size:9.5px;">شروع از {date_start_str}</div>
                </div>
                <div class="kpi-card" style="border-color:#00e676;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">📈 بالانس نهایی شبیه‌سازی</div>
                    <div class="kpi-value" id="eqKpiFinalBal" style="color:#00e676;font-size:16px;">${bal_k:,.2f}</div>
                    <div class="kpi-sub" id="eqKpiNetSub" style="font-size:9.5px;">سود خالص: ${net_k:+,.2f} ({net_k_pct:+.2f}٪)</div>
                </div>
                <div class="kpi-card" style="border-color:#facc15;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">🏔️ سقف سرمایه (Peak)</div>
                    <div class="kpi-value" id="eqKpiPeak" style="color:#facc15;font-size:16px;">${peak_k:,.2f}</div>
                    <div class="kpi-sub" id="eqKpiPeakSub" style="font-size:9.5px;">ثبت رکورد در پایان بازه</div>
                </div>
                <div class="kpi-card" style="border-color:#ef4444;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">🛡️ حداکثر افت (Max DD)</div>
                    <div class="kpi-value" id="eqKpiMaxDD" style="color:#fca5a5;font-size:16px;">${max_dd_k:.2f} ({max_dd_k_pct:.2f}٪)</div>
                    <div class="kpi-sub" id="eqKpiMaxDDSub" style="font-size:9.5px;">مدیریت ریسک بی‌نقص</div>
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
            </div>

                                    <!-- 🌟 2-COLUMN MAIN WORKSPACE GRID -->
            <div class="equity-two-col-container" id="eqTwoColContainer">

                <!-- 🔹 COLUMN 1: CHART SECTION (HALF-WIDTH) -->
                <div class="equity-col-chart" id="eqColChart">
                    <!-- 📈 INTERACTIVE EQUITY CANVAS GRAPH (AT THE VERY TOP) -->
            <!-- Interactive Canvas Graph Container -->
            <div class="section-box" style="border:1px solid #38bdf8;background:#0b0f19;padding:10px 14px;border-radius:8px;height:100%;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;margin-bottom:0;">
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e293b;padding-bottom:8px;margin-bottom:10px;flex-wrap:wrap;gap:12px;">
                    <div>
                        <h3 style="margin:0;color:#38bdf8;font-size:15px;display:flex;align-items:center;gap:6px;">
                            <span>📈 نمودار تعاملی رشد بالانس و اکوئیتی (MT5 Strategy Tester Graph)</span>
                        </h3>
                        <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">رسم دقیق منحنی رشد سرمایه معامله به معامله در طول زمان ۶ ماهه - موس را روی نمودار حرکت دهید تا جزئیات هر معامله را ببینید:</p>
                    </div>
                    <div style="display:flex;gap:8px;">
                        <button id="btnEqKings" class="sort-btn active" onclick="switchEquityMode('kings')">👑 منحنی سلاطین {len(qualified_kings)} گانه ({len(pts_kings)-1} معامله)</button>
                        <button onclick="toggleTwoColLayout()" id="btnToggleTwoCol" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:4px 8px;border-radius:5px;font-size:11px;cursor:pointer;" title="تغییر حالت به تمام‌صفحه یا دو ستونی">⛶</button>
                        <button id="btnEqAll" class="sort-btn" onclick="switchEquityMode('all')">🌐 منحنی کل ساختارهای چارت ({len(pts_all)-1} معامله)</button>
                    </div>
                </div>

                <!-- Canvas Box -->
                <div style="position:relative;width:100%;height:425px;background:#0f172a;border:1px solid #1e293b;border-radius:10px;overflow:hidden;">
                    <canvas id="equityCanvas" style="width:100%;height:100%;display:block;cursor:crosshair;"></canvas>
                    <div id="equityTooltip" style="display:none;position:absolute;pointer-events:none;background:rgba(15,23,42,0.95);border:1px solid #38bdf8;padding:10px 14px;border-radius:8px;font-size:12px;color:#f1f5f9;box-shadow:0 8px 24px rgba(0,0,0,0.7);z-index:20;direction:rtl;min-width:210px;"></div>
                </div>

                <!-- Graph Legend & Stats Bar -->
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:14px;font-size:12px;color:#94a3b8;flex-wrap:wrap;gap:10px;">
                    <div style="display:flex;align-items:center;gap:16px;">
                        <span style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:14px;height:4px;background:#38bdf8;border-radius:2px;"></span> خط رشد بالانس (Balance Curve)</span>
                        <span style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:14px;height:4px;background:#475569;border-radius:2px;"></span> خط تراز پایه ۱۰ هزار دلار</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:12px;">
                        <span>تعداد نقاط ثبت‌شده: <b id="lblEqPts" style="color:#facc15;">{len(pts_kings)-1}</b></span>
                        <span>|</span>
                        <span>بازه زمانی: <b style="color:#38bdf8;">{date_start_str} تا {date_end_str}</b></span>
                    </div>
                </div>
            </div>
                </div>

                <!-- 🔹 COLUMN 2: SUBTABS & CONTROLS (PRESETS / FILTERS / RISK) -->
                <div class="equity-col-controls" id="eqColControls">
                    <div style="background:#080d1a;border:1px solid #1e3a5f;border-radius:10px;padding:10px 12px;height:100%;box-sizing:border-box;display:flex;flex-direction:column;">
                        <!-- Subtabs Navigation Bar -->
                        <!-- 📑 SUB-NAVIGATION FOR CONTROLS & PRESETS -->
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:14px;margin-bottom:12px;border-bottom:2px solid #1e3a5f;padding-bottom:10px;flex-wrap:wrap;gap:8px;">
                <div style="display:flex;gap:6px;flex-wrap:wrap;">
                    <button class="eq-subtab-btn active" onclick="openEqSubtab(event, 'eq-sub-presets')">
                        ⚡ سناریوهای استراتژی (پیش‌فرض‌ها و ذخیره‌شده‌ها)
                    </button>
                    <button class="eq-subtab-btn" onclick="openEqSubtab(event, 'eq-sub-filters')">
                        🎛️ شبیه‌ساز فیلترها (اسلایدر، ساعات و سلاطین)
                    </button>
                    <button class="eq-subtab-btn" onclick="openEqSubtab(event, 'eq-sub-risk')">
                        🚨 کالبدشکافی استاپ‌ها و باخت‌ها
                    </button>
                    <button class="eq-subtab-btn" onclick="openEqSubtab(event, 'eq-sub-weekly')">
                        📊 کارنامه میله‌ای هفتگی
                    </button>
                    <button class="eq-subtab-btn" onclick="openEqSubtab(event, 'eq-sub-compare')">
                        ⚖️ مقایسه سلاطین با کل چارت
                    </button>
                </div>
                <div style="display:flex;gap:6px;">
                    <button onclick="runClientAutoOptimizer()" style="background:linear-gradient(135deg, #7c3aed, #a855f7);border:1px solid #c084fc;color:#fff;font-size:12px;padding:6px 14px;border-radius:6px;cursor:pointer;font-weight:bold;box-shadow:0 2px 10px rgba(168,85,247,0.4);display:flex;align-items:center;gap:6px;">
                            <span>🤖 کشف خودکار بهترین چیدمان این دیتا (AI Optimizer)</span>
                        </button>
                        <button onclick="openSavePresetModal()" style="background:#064e3b;border:1px solid #10b981;color:#6ee7b7;padding:5px 12px;border-radius:6px;font-size:11.5px;cursor:pointer;font-weight:bold;">💾 ذخیره چیدمان فعلی</button>
                    <button onclick="resetAllSimFilters()" style="background:#1e293b;border:1px solid #ef4444;color:#fca5a5;padding:5px 12px;border-radius:6px;font-size:11.5px;cursor:pointer;font-weight:bold;">🔄 بازنشانی (Reset)</button>
                </div>
            </div>

                        <!-- Subpanels Scrollable Wrapper -->
                        <div class="eq-subpanels-wrapper">
                            <!-- SUBPANEL 1: PRESETS -->
            <div id="eq-sub-presets" class="eq-subpanel active">
                <!-- ⚡ SMART PRESETS & CUSTOM STRATEGY PORTFOLIOS -->
            <div class="section-box" style="border: 2px solid #facc15; background: #0b1528; padding: 18px; margin-bottom: 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #1e3a5f; padding-bottom: 12px; margin-bottom: 14px; flex-wrap:wrap; gap:10px;">
                    <div>
                        <h3 style="margin:0;color:#facc15;font-size:18px;display:flex;align-items:center;gap:8px;">
                            <span>⚡ پیشنهادات استراتژیک سیستم و سناریوهای شخصی شما (Strategy Portfolios & Saved Presets)</span>
                        </h3>
                        <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">با کلیک روی دکمه «اعمال روی نمودار»، فیلترها بلافاصله تنظیم می‌شوند. همچنین با دکمه سبز می‌توانید چیدمان‌های دلخواه خود را برای همیشه در مرورگر ذخیره کنید:</p>
                    </div>
                    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                        <button onclick="openSavePresetModal()" style="background:linear-gradient(135deg, #059669, #10b981);border:1px solid #34d399;color:#fff;font-size:12px;padding:6px 14px;border-radius:6px;cursor:pointer;font-weight:bold;box-shadow:0 2px 8px rgba(16,185,129,0.3);display:flex;align-items:center;gap:6px;">
                            <span>💾 ذخیره چیدمان فعلی به عنوان سناریوی شخصی</span>
                        </button>
                        <button onclick="exportCustomPresets()" style="background:#1e293b;border:1px solid #38bdf8;color:#7dd3fc;font-size:11.5px;padding:6px 10px;border-radius:6px;cursor:pointer;" title="خروجی گرفتن از تمام سناریوهای شخصی شما در قالب فایل JSON">
                            📥 دانلود فایل پشتیبان (JSON)
                        </button>
                        <button onclick="document.getElementById('importPresetsInput').click()" style="background:#1e293b;border:1px solid #ca8a04;color:#fef08a;font-size:11.5px;padding:6px 10px;border-radius:6px;cursor:pointer;" title="وارد کردن سناریوها از فایل قبلی">
                            📤 بارگذاری از فایل
                        </button>
                        <input type="file" id="importPresetsInput" accept=".json" style="display:none;" onchange="importCustomPresets(event)" />
                    </div>
                </div>

                <div style="overflow-x:auto;">
                    <table style="width:100%;border-collapse:collapse;font-size:12px;text-align:right;">
                        <thead>
                            <tr style="background:#1e293b;color:#94a3b8;border-bottom:2px solid #334155;">
                                <th style="padding:10px 8px;text-align:center;">#</th>
                                <th style="padding:10px 12px;">سناریوی استراتژی و ویژگی‌ها</th>
                                <th style="padding:10px 10px;text-align:center;">تنظیمات فیلتر</th>
                                <th style="padding:10px 8px;text-align:center;">سلاطین</th>
                                <th style="padding:10px 8px;text-align:center;">تعداد ترید</th>
                                <th style="padding:10px 8px;text-align:center;">وین‌ریت</th>
                                <th style="padding:10px 8px;text-align:center;">پرافیت فاکتور</th>
                                <th style="padding:10px 8px;text-align:center;">میانگین هر سود</th>
                                <th style="padding:10px 8px;text-align:center;">حداکثر افت (DD)</th>
                                <th style="padding:10px 10px;text-align:center;">سود خالص نهایی</th>
                                <th style="padding:10px 10px;text-align:center;">اقدام سریع</th>
                            </tr>
                        </thead>
                        <!-- 1. SYSTEM BUILT-IN PRESETS -->
                        <tbody id="systemPresetsTbody">
                            {smart_presets_table_rows_str}
                        </tbody>
                        <!-- 2. USER SAVED CUSTOM PRESETS HEADER -->
                        <tbody id="customPresetsHeaderTbody">
                            <tr style="background:#131d2e;border-top:2px solid #38bdf8;border-bottom:1px solid #1e3a5f;">
                                <td colspan="11" style="padding:9px 14px;">
                                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                                        <div style="font-weight:bold;color:#38bdf8;font-size:13px;display:flex;align-items:center;gap:6px;">
                                            <span>⭐ سناریوهای شخصی ذخیره‌شده شما (Your Custom Saved Portfolios):</span>
                                            <span id="customPresetsCountBadge" style="background:#0c4a6e;color:#7dd3fc;font-size:10.5px;padding:2px 8px;border-radius:10px;">0 سناریو</span>
                                        </div>
                                        <div style="font-size:11px;color:#94a3b8;">
                                            این سناریوها در مرورگر شما ذخیره هستند و حتی با تغییر یا بروزرسانی دیتا، محاسبات آنها فوراً بروز می‌شود.
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
                                <td style="text-align:center;">${bal_initial:,.2f}</td>
                                <td style="text-align:center;font-weight:bold;color:#00e676;">${bal_k:,.2f}</td>
                                <td style="text-align:center;font-weight:bold;color:#00e676;">${net_k:+,.2f}</td>
                                <td style="text-align:center;font-weight:bold;color:#00e676;">{net_k_pct:+.2f}٪</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">${max_dd_k:.2f} ({max_dd_k_pct:.2f}٪)</td>
                                <td style="text-align:center;"><span style="background:#064e3b;color:#34d399;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">💎 رشد مستمر و اکوئیتی صعودی</span></td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#94a3b8;">🌐 کل ساختارهای خام چارت (بدون فیلتر)</td>
                                <td style="text-align:center;font-weight:bold;">{len(pts_all)-1}</td>
                                <td style="text-align:center;">${bal_initial:,.2f}</td>
                                <td style="text-align:center;font-weight:bold;color:{'#00e676' if net_a>=0 else '#ef4444'};">${bal_a:,.2f}</td>
                                <td style="text-align:center;font-weight:bold;color:{'#00e676' if net_a>=0 else '#ef4444'};">${net_a:+,.2f}</td>
                                <td style="text-align:center;font-weight:bold;color:{'#00e676' if net_a>=0 else '#ef4444'};">{net_a_pct:+.2f}٪</td>
                                <td style="text-align:center;color:#ef4444;font-weight:bold;">${max_dd_a:.2f} ({max_dd_a_pct:.2f}٪)</td>
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

        </div>

        <!-- ==================== TAB 1: 👑 GOLDEN KINGS ==================== -->
        <div id="tab-kings" class="tab-content">
            <!-- Global Performance KPI Cards (Placed inside Tab 1) -->
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
        
            </div>
        </div>

        <!-- ==================== TAB 1: 👑 GOLDEN KINGS ==================== -->
        <div id="tab-kings" class="tab-content">
            <!-- Global Performance KPI Cards (Placed inside Tab 1) -->
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
        </div>

        <!-- ==================== TAB: 📑 TRADES JOURNAL & EXIT POINTS ==================== -->
        <div id="tab-trades" class="tab-content">
            <div class="section-box" style="border: 1px solid #38bdf8; background: #081a2e;">
                <div style="border-bottom: 1px solid #0284c7; padding-bottom: 14px; margin-bottom: 16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                        <div>
                            <h3 style="margin:0;color:#38bdf8;font-size:20px;">📑 ژورنال جامع معاملات، استراتژی‌ها و نقاط خروج (Exit Targets)</h3>
                            <p style="margin:6px 0 0 0;color:#bae6fd;font-size:13px;">نمایش زنده تمامی معاملات، نقاط ورود، استاپ، تارگت‌های ۴ گانه TP1..TP4، وضعیت تاچ خروج‌ها و سود/زیان خالص بر مبنای خروج پلکانی 0.04 لات:</p>
                        </div>
                        <div style="display:flex;gap:8px;align-items:center;">
                            <span style="background:#0c4a6e;border:1px solid #0284c7;padding:6px 12px;border-radius:6px;font-size:12px;color:#7dd3fc;">حجم پایه: <b>0.04 لات</b></span>
                            <span style="background:#1e293b;border:1px solid #475569;padding:6px 12px;border-radius:6px;font-size:12px;color:#e2e8f0;">اسپرد+کمیسیون: <b>$0.48</b></span>
                        </div>
                    </div>
                </div>

                <!-- KPI Summary Cards for Filtered Trades -->
                <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));gap:8px;margin-bottom:10px;">
                    <div class="kpi-card" style="padding:10px 14px;border-color:#38bdf8;background:#0c2d48;">
                        <div class="kpi-title" style="font-size:11px;">تعداد کل معاملات فیلترشده</div>
                        <div class="kpi-value" id="trKpiCount" style="font-size:20px;color:#38bdf8;">-</div>
                        <div class="kpi-sub" id="trKpiCountSub">در این نمایش</div>
                    </div>
                    <div class="kpi-card" style="padding:10px 14px;border-color:#10b981;background:#063a2a;">
                        <div class="kpi-title" style="font-size:11px;">سود خالص نهایی (Net PnL)</div>
                        <div class="kpi-value" id="trKpiNet" style="font-size:20px;color:#34d399;">-</div>
                        <div class="kpi-sub" id="trKpiNetSub">پس از کسر اسپرد</div>
                    </div>
                    <div class="kpi-card" style="padding:10px 14px;border-color:#facc15;background:#2a2408;">
                        <div class="kpi-title" style="font-size:11px;">وین‌ریت حداقل TP1 (ریسک‌فری+)</div>
                        <div class="kpi-value" id="trKpiWin1" style="font-size:20px;color:#facc15;">-</div>
                        <div class="kpi-sub">تارگت اول و بدون ضرر</div>
                    </div>
                    <div class="kpi-card" style="padding:10px 14px;border-color:#a855f7;background:#24123a;">
                        <div class="kpi-title" style="font-size:11px;">معاملات فول تارگت (TP4)</div>
                        <div class="kpi-value" id="trKpiWin4" style="font-size:20px;color:#c084fc;">-</div>
                        <div class="kpi-sub">پرتاب کامل ۱ به ۴</div>
                    </div>
                    <div class="kpi-card" style="padding:10px 14px;border-color:#ef4444;background:#351015;">
                        <div class="kpi-title" style="font-size:11px;">معاملات استاپ خورده (SL)</div>
                        <div class="kpi-value" id="trKpiLoss" style="font-size:20px;color:#f87171;">-</div>
                        <div class="kpi-sub">حد زیان اولیه</div>
                    </div>
                </div>

                <!-- Filters & Controls Bar -->
                <div style="background:#0c253d;border:1px solid #1e4976;padding:12px 16px;border-radius:10px;margin-bottom:16px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;">
                    <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
                        <!-- Basket switch -->
                        <span style="color:#94a3b8;font-size:12px;font-weight:bold;">سبد:</span>
                        <div style="display:inline-flex;border-radius:6px;overflow:hidden;border:1px solid #0284c7;">
                            <button id="btnTrBasketKings" class="active" onclick="setTrFilter('basket', 'kings', this)" style="background:#0284c7;color:#fff;border:none;padding:5px 12px;font-size:11.5px;cursor:pointer;font-weight:bold;">👑 سلاطین برگزیده</button>
                            <button id="btnTrBasketAll" onclick="setTrFilter('basket', 'all', this)" style="background:#1e293b;color:#94a3b8;border:none;padding:5px 12px;font-size:11.5px;cursor:pointer;font-weight:bold;">🌐 تمامی معاملات</button>
                        </div>

                        <!-- Timeframe switch -->
                        <span style="color:#94a3b8;font-size:12px;font-weight:bold;margin-right:8px;">تایم‌فریم:</span>
                        <div style="display:inline-flex;border-radius:6px;overflow:hidden;border:1px solid #334155;">
                            <button class="active" onclick="setTrFilter('tf', 'ALL', this)" style="background:#0284c7;color:#fff;border:none;padding:5px 10px;font-size:11px;cursor:pointer;">همه</button>
                            <button onclick="setTrFilter('tf', 'M1', this)" style="background:#1e293b;color:#94a3b8;border:none;padding:5px 10px;font-size:11px;cursor:pointer;">M1</button>
                            <button onclick="setTrFilter('tf', 'M5', this)" style="background:#1e293b;color:#94a3b8;border:none;padding:5px 10px;font-size:11px;cursor:pointer;">M5</button>
                            <button onclick="setTrFilter('tf', 'M15', this)" style="background:#1e293b;color:#94a3b8;border:none;padding:5px 10px;font-size:11px;cursor:pointer;">M15</button>
                        </div>

                        <!-- Direction switch -->
                        <span style="color:#94a3b8;font-size:12px;font-weight:bold;margin-right:8px;">جهت:</span>
                        <div style="display:inline-flex;border-radius:6px;overflow:hidden;border:1px solid #334155;">
                            <button class="active" onclick="setTrFilter('dir', 'ALL', this)" style="background:#0284c7;color:#fff;border:none;padding:5px 10px;font-size:11px;cursor:pointer;">همه</button>
                            <button onclick="setTrFilter('dir', 'BUY', this)" style="background:#1e293b;color:#34d399;border:none;padding:5px 10px;font-size:11px;cursor:pointer;">🟢 خرید (BUY)</button>
                            <button onclick="setTrFilter('dir', 'SELL', this)" style="background:#1e293b;color:#f87171;border:none;padding:5px 10px;font-size:11px;cursor:pointer;">🔴 فروش (SELL)</button>
                        </div>

                        <!-- Outcome switch -->
                        <span style="color:#94a3b8;font-size:12px;font-weight:bold;margin-right:8px;">نتیجه:</span>
                        <div style="display:inline-flex;border-radius:6px;overflow:hidden;border:1px solid #334155;">
                            <button class="active" onclick="setTrFilter('outcome', 'ALL', this)" style="background:#0284c7;color:#fff;border:none;padding:5px 10px;font-size:11px;cursor:pointer;">همه</button>
                            <button onclick="setTrFilter('outcome', 'TP4', this)" style="background:#1e293b;color:#c084fc;border:none;padding:5px 10px;font-size:11px;cursor:pointer;">🎯 TP4</button>
                            <button onclick="setTrFilter('outcome', 'TP2_PLUS', this)" style="background:#1e293b;color:#60a5fa;border:none;padding:5px 10px;font-size:11px;cursor:pointer;">🎯 TP2+</button>
                            <button onclick="setTrFilter('outcome', 'TP1_PLUS', this)" style="background:#1e293b;color:#facc15;border:none;padding:5px 10px;font-size:11px;cursor:pointer;">🎯 TP1+</button>
                            <button onclick="setTrFilter('outcome', 'LOSS', this)" style="background:#1e293b;color:#f87171;border:none;padding:5px 10px;font-size:11px;cursor:pointer;">🛑 SL</button>
                        </div>
                    </div>

                    <!-- Search Input -->
                    <div style="position:relative;">
                        <input id="trSearchInput" type="text" placeholder="جستجو در استراتژی یا تاریخ..." oninput="onTrSearch(this.value)" style="background:#1e293b;border:1px solid #475569;border-radius:6px;color:#fff;padding:6px 12px;font-size:12px;width:210px;outline:none;" />
                    </div>
                </div>

                <!-- Trades Table -->
                <div style="overflow-x:auto;">
                    <table style="width:100%;border-collapse:collapse;font-size:12px;">
                        <thead>
                            <tr style="background:#0e3355;color:#93c5fd;border-bottom:2px solid #0284c7;">
                                <th style="text-align:center;padding:10px 6px;">#</th>
                                <th style="text-align:center;padding:10px 8px;">زمان ورود / خروج</th>
                                <th style="text-align:center;padding:10px 6px;">تایم</th>
                                <th style="text-align:right;padding:10px 10px;">استراتژی / نقش ساختار</th>
                                <th style="text-align:center;padding:10px 8px;">جهت</th>
                                <th style="text-align:center;padding:10px 8px;">قیمت ورود</th>
                                <th style="text-align:center;padding:10px 8px;color:#f87171;">حد ضرر (SL)</th>
                                <th style="text-align:center;padding:10px 8px;color:#fbbf24;">تارگت ۱ (TP 1:1)</th>
                                <th style="text-align:center;padding:10px 8px;color:#60a5fa;">تارگت ۲ (TP 1:2)</th>
                                <th style="text-align:center;padding:10px 8px;color:#38bdf8;">تارگت ۳ (TP 1:3)</th>
                                <th style="text-align:center;padding:10px 8px;color:#c084fc;">تارگت ۴ (TP 1:4)</th>
                                <th style="text-align:center;padding:10px 8px;">نقطه و نوع خروج</th>
                                <th style="text-align:center;padding:10px 10px;color:#34d399;">سود خالص دلاری</th>
                            </tr>
                        </thead>
                        <tbody id="tradesTableBody">
                            <!-- Populated dynamically via JS -->
                        </tbody>
                    </table>
                </div>

                <!-- Pagination Footer -->
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:16px;padding:10px 14px;background:#0c253d;border:1px solid #1e4976;border-radius:8px;flex-wrap:wrap;gap:10px;">
                    <div id="trPaginationInfo" style="color:#94a3b8;font-size:12px;">نمایش ۱ تا ۵۰ از - معامله</div>
                    <div style="display:flex;gap:6px;align-items:center;">
                        <button id="trBtnPrev" onclick="prevTrPage()" style="background:#1e293b;border:1px solid #475569;color:#e2e8f0;padding:5px 12px;border-radius:6px;cursor:pointer;font-size:12px;">◀ صفحه قبل</button>
                        <span id="trPageCurrent" style="color:#facc15;font-weight:bold;font-size:13px;padding:0 8px;">صفحه ۱ از ۱</span>
                        <button id="trBtnNext" onclick="nextTrPage()" style="background:#1e293b;border:1px solid #475569;color:#e2e8f0;padding:5px 12px;border-radius:6px;cursor:pointer;font-size:12px;">صفحه بعد ▶</button>
                    </div>
                    <div style="display:flex;align-items:center;gap:6px;">
                        <span style="color:#94a3b8;font-size:12px;">تعداد در صفحه:</span>
                        <select id="trPageSize" onchange="changeTrPageSize(this.value)" style="background:#1e293b;border:1px solid #475569;color:#fff;padding:4px 8px;border-radius:5px;font-size:12px;outline:none;">
                            <option value="25">۲۵</option>
                            <option value="50" selected>۵۰</option>
                            <option value="100">۱۰۰</option>
                            <option value="250">۲۵۰</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>

        <!-- ==================== TAB 2: 💎 SCALE-OUT & BREAK-EVEN ==================== -->
        <div id="tab-scaleout" class="tab-content">
            <div class="section-box" style="border: 2px solid #38bdf8; background: #082136;">
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
            </div>
        </div>

        <!-- ==================== TAB 3: 📊 TIMEFRAMES BREAKDOWN ==================== -->
        <div id="tab-timeframes" class="tab-content">
            <div class="section-box">
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
                <div id="rawTfTable" style="display:none;overflow-x:auto;margin-bottom:24px;border:1px dashed #475569;border-radius:8px;padding:10px;">
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
            </div>
        </div>

        <!-- ==================== TAB 4: 🛡️ ANTI-SL FILTERS ==================== -->
        <div id="tab-filters" class="tab-content">
            <div class="section-box" style="border: 1px solid #38bdf8; background: #0c1829;">
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
            </div>
        </div>

        <!-- ==================== TAB 7: 🔍 LOSS INTELLIGENCE ==================== -->
        <div id="tab-loss-intel" class="tab-content">
            <div class="section-box" style="border: 1px solid #ef4444; background: #18111c;">
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
            </div>
        </div>

        <!-- ==================== TAB 8: 📅 WEEKLY BREAKDOWN & CONSISTENCY ==================== -->
        <div id="tab-weekly" class="tab-content">
            <!-- Weekly KPI Banner -->
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
            </div>
        </div>

    </div>

    <script>


        let currentWeeklyBarMode = 'kings';
        let dataWeeklyBars = {json_weekly_bars};

        function switchWeeklyBarMode(mode) {{
            currentWeeklyBarMode = mode;
            let btnK = document.getElementById('btnWkKings');
            let btnA = document.getElementById('btnWkAll');
            if(mode === 'kings') {{
                if(btnK) btnK.classList.add('active');
                if(btnA) btnA.classList.remove('active');
            }} else {{
                if(btnK) btnK.classList.remove('active');
                if(btnA) btnA.classList.add('active');
            }}
            drawWeeklyBarChart(mode);
        }}

        function drawWeeklyBarChart(mode) {{
            let canvas = document.getElementById('weeklyBarCanvas');
            if (!canvas) return;
            let ctx = canvas.getContext('2d');
            if (!ctx) return;

            let dpr = window.devicePixelRatio || 1;
            let rect = canvas.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return;

            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            ctx.scale(dpr, dpr);

            let w = rect.width;
            let h = rect.height;
            let padLeft = 45;
            let padRight = 20;
            let padTop = 25;
            let padBottom = 35;
            let plotW = w - padLeft - padRight;
            let plotH = h - padTop - padBottom;

            let bars = dataWeeklyBars;
            if (!bars || bars.length === 0) return;

            let minVal = 0;
            let maxVal = 0;
            for (let i = 0; i < bars.length; i++) {{
                let val = (mode === 'kings') ? bars[i].k_pnl : bars[i].all_pnl;
                if (val < minVal) minVal = val;
                if (val > maxVal) maxVal = val;
            }}

            let absMax = Math.max(Math.abs(minVal), Math.abs(maxVal), 50);
            absMax = Math.ceil(absMax / 25) * 25;
            let valRange = absMax * 2;

            ctx.clearRect(0, 0, w, h);

            // Background
            ctx.fillStyle = '#0b0f19';
            ctx.fillRect(0, 0, w, h);

            // Plot area
            ctx.fillStyle = '#0f172a';
            ctx.fillRect(padLeft, padTop, plotW, plotH);

            // Zero line Y
            let zeroY = padTop + plotH * (absMax / valRange);

            // Grid lines
            let steps = 4;
            ctx.strokeStyle = '#1e293b';
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.font = '11px Segoe UI, Tahoma, sans-serif';
            ctx.textAlign = 'right';

            for (let s = -steps; s <= steps; s += 2) {{
                let val = (absMax / steps) * s;
                let y = zeroY - (val / valRange) * plotH;

                ctx.beginPath();
                ctx.moveTo(padLeft, y);
                ctx.lineTo(padLeft + plotW, y);
                ctx.stroke();

                ctx.fillStyle = '#64748b';
                let sign = val > 0 ? '+' : '';
                ctx.fillText(sign + '$' + val.toFixed(0), padLeft - 6, y + 4);
            }}

            ctx.setLineDash([]);

            // Solid Baseline at $0
            ctx.strokeStyle = '#64748b';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(padLeft, zeroY);
            ctx.lineTo(padLeft + plotW, zeroY);
            ctx.stroke();

            // Draw Bars
            let numBars = bars.length;
            let barSlot = plotW / numBars;
            let barW = Math.max(4, barSlot * 0.72);
            let barCoords = [];

            for (let i = 0; i < numBars; i++) {{
                let val = (mode === 'kings') ? bars[i].k_pnl : bars[i].all_pnl;
                let barH = (Math.abs(val) / valRange) * plotH;
                let x = padLeft + i * barSlot + (barSlot - barW) / 2;
                let y = (val >= 0) ? (zeroY - barH) : zeroY;

                let isGreen = val >= 0;
                let grad = ctx.createLinearGradient(0, y, 0, y + barH);
                if (isGreen) {{
                    grad.addColorStop(0, '#00e676');
                    grad.addColorStop(1, '#059669');
                }} else {{
                    grad.addColorStop(0, '#dc2626');
                    grad.addColorStop(1, '#ef4444');
                }}

                ctx.fillStyle = grad;
                ctx.fillRect(x, y, barW, barH);

                ctx.strokeStyle = isGreen ? '#34d399' : '#f87171';
                ctx.lineWidth = 1;
                ctx.strokeRect(x, y, barW, barH);

                // Week label on X-axis
                ctx.font = '10px Segoe UI, Tahoma, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillStyle = '#64748b';
                ctx.fillText('W' + bars[i].week, x + barW / 2, padTop + plotH + 18);

                barCoords.push({{
                    x: x,
                    y: y,
                    w: barW,
                    h: barH,
                    val: val,
                    item: bars[i]
                }});
            }}

            // Border
            ctx.strokeStyle = '#334155';
            ctx.lineWidth = 1;
            ctx.strokeRect(padLeft, padTop, plotW, plotH);

            canvas._barCoords = barCoords;
            canvas._padLeft = padLeft;
            canvas._padTop = padTop;
            canvas._plotW = plotW;
            canvas._plotH = plotH;
        }}

        let weeklyBarEventsInitialized = false;
        function initWeeklyBarCanvasEvents() {{
            let canvas = document.getElementById('weeklyBarCanvas');
            if (!canvas || weeklyBarEventsInitialized) return;
            weeklyBarEventsInitialized = true;

            canvas.addEventListener('mousemove', function(evt) {{
                if (!canvas._barCoords) return;
                let rect = canvas.getBoundingClientRect();
                let mouseX = evt.clientX - rect.left;
                let mouseY = evt.clientY - rect.top;

                let tt = document.getElementById('weeklyBarTooltip');
                let found = null;

                for (let i = 0; i < canvas._barCoords.length; i++) {{
                    let b = canvas._barCoords[i];
                    if (mouseX >= b.x - 2 && mouseX <= b.x + b.w + 2) {{
                        found = b;
                        break;
                    }}
                }}

                if (!found) {{
                    if (tt) tt.style.display = 'none';
                    drawWeeklyBarChart(currentWeeklyBarMode);
                    return;
                }}

                drawWeeklyBarChart(currentWeeklyBarMode);
                let ctx = canvas.getContext('2d');
                let dpr = window.devicePixelRatio || 1;
                ctx.save();
                ctx.scale(dpr, dpr);

                // Highlight hovered bar
                ctx.strokeStyle = '#facc15';
                ctx.lineWidth = 2.5;
                ctx.strokeRect(found.x - 1, found.y - 1, found.w + 2, found.h + 2);
                ctx.restore();

                if (tt) {{
                    tt.style.display = 'block';
                    let item = found.item;
                    let val = found.val;
                    let pnlCol = val >= 0 ? '#00e676' : '#ef4444';
                    let sign = val >= 0 ? '+' : '';
                    let trds = (currentWeeklyBarMode === 'kings') ? item.k_trades : item.all_trades;
                    let wins = (currentWeeklyBarMode === 'kings') ? item.k_wins : item.all_wins;
                    let losses = (currentWeeklyBarMode === 'kings') ? item.k_losses : item.all_losses;
                    let wr = (currentWeeklyBarMode === 'kings') ? item.k_wr : item.all_wr;

                    tt.innerHTML = `
                        <div style="font-weight:bold;color:#facc15;margin-bottom:4px;border-bottom:1px solid #334155;padding-bottom:2px;">هفته ${{item.week}} (${{item.dates}})</div>
                        <div>سود/زیان خالص این هفته: <b style="color:${{pnlCol}};font-size:13px;">${{sign}}$${{val.toFixed(2)}}</b></div>
                        <div style="color:#94a3b8;margin-top:4px;">تعداد کل معاملات: <b style="color:#f1f5f9;">${{trds}} معامله</b></div>
                        <div>بردها: <b style="color:#00e676;">${{wins}}</b> | باخت‌ها: <b style="color:#ef4444;">${{losses}}</b></div>
                        <div>وین‌ریت هفته: <b style="color:#38bdf8;">${{wr}}%</b></div>
                    `;

                    let ttX = found.x + 15;
                    let ttY = found.y - 50;
                    if (ttX + 230 > rect.width) ttX = found.x - 240;
                    if (ttY < 10) ttY = 10;
                    tt.style.left = ttX + 'px';
                    tt.style.top = ttY + 'px';
                }}
            }});

            canvas.addEventListener('mouseleave', function() {{
                let tt = document.getElementById('weeklyBarTooltip');
                if (tt) tt.style.display = 'none';
                drawWeeklyBarChart(currentWeeklyBarMode);
            }});

            window.addEventListener('resize', function() {{
                drawWeeklyBarChart(currentWeeklyBarMode);
            }});
        }}

        let kingsSimList = {json_kings_sim};
        let top3SLCntKeys = {json_top3_sl_cnt};
        let top3SLUsdKeys = {json_top3_sl_usd};
        let top5SLUsdKeys = {json_top5_sl_usd};
        let top3SLPctKeys = {json_top3_sl_pct};
        let simTrades = {json_trades_sim};
        let smartPresets = {json_smart_presets};
        let currentEquityMode = 'kings';
        let currentSimPts = [];
        let simState = {{
            mode: 'kings',
            enabledKings: new Set(kingsSimList.map(k => k.kk)),
            allowedHours: new Array(24).fill(true),
            minProfit: 0.0,
            consecLossTrigger: 0,
            consecLossSkipCount: 1,
            consecLossSkipDay: false
        }};

        let simCanvasEventsInitialized = false;

        function clearPresetActiveState() {{
            document.querySelectorAll('.preset-table-row').forEach(r => {{
                r.style.outline = 'none';
                r.style.boxShadow = 'none';
            }});
            document.querySelectorAll('.apply-preset-btn').forEach(b => {{
                b.innerHTML = '⚡ اعمال روی نمودار';
                b.style.background = 'linear-gradient(135deg, #0284c7, #0369a1)';
                b.style.borderColor = '#38bdf8';
            }});
        }}

        function applySmartPreset(idx) {{
            let p = smartPresets.find(x => x.idx === idx);
            if (!p) return;

            // 1. Set mode to kings
            simState.mode = 'kings';
            let btnK = document.getElementById('btnEqKings');
            let btnA = document.getElementById('btnEqAll');
            if (btnK) btnK.classList.add('active');
            if (btnA) btnA.classList.remove('active');

            // 2. Set min profit
            simState.minProfit = p.min_pot;
            let slider = document.getElementById('simProfitSlider');
            if (slider) slider.value = p.min_pot;
            let sliderVal = document.getElementById('simProfitSliderVal');
            if (sliderVal) sliderVal.textContent = '$' + p.min_pot.toFixed(2);
            let pBadge = document.getElementById('simProfitBadge');
            if (pBadge) {{
                pBadge.textContent = (p.min_pot === 0) ? 'بدون فیلتر ($0)' : 'حداقل $' + p.min_pot.toFixed(2);
                pBadge.style.background = (p.min_pot === 0) ? '#064e3b' : '#0369a1';
            }}
            document.querySelectorAll('.profit-preset-btn').forEach(b => {{
                b.classList.remove('active');
                if (parseFloat(b.dataset.val) === p.min_pot) b.classList.add('active');
            }});

            // 3. Set allowed hours
            simState.allowedHours = [...p.hours];
            document.querySelectorAll('.hour-preset-btn').forEach(b => b.classList.remove('active'));
            if (p.hours_name === 'all') {{
                let b = document.getElementById('btnHAll');
                if (b) b.classList.add('active');
            }} else if (p.hours_name === 'no_night') {{
                let b = document.getElementById('btnHNoNight');
                if (b) b.classList.add('active');
            }} else if (p.hours_name === 'lon_ny') {{
                let b = document.getElementById('btnHLonNy');
                if (b) b.classList.add('active');
            }}

            // 4. Set enabled kings
            simState.enabledKings = new Set(p.kings);

            // 4B. Consecutive Loss Circuit Breaker from Preset
            if (p.consec_trig !== undefined) {{
                simState.consecLossTrigger = p.consec_trig;
                simState.consecLossSkipCount = p.consec_sk || 1;
                simState.consecLossSkipDay = !!p.consec_day;
                syncConsecButtonsUI();
            }} else {{
                simState.consecLossTrigger = 0;
                simState.consecLossSkipCount = 1;
                simState.consecLossSkipDay = false;
                syncConsecButtonsUI();
            }}

            // 5. Update UI components
            renderSimKingsGrid();
            renderSimHoursBar();

            // 6. Highlight active preset row
            clearPresetActiveState();
            let activeRow = document.getElementById('presetRow' + idx);
            if (activeRow) {{
                activeRow.style.outline = '2px solid #38bdf8';
                activeRow.style.boxShadow = '0 0 16px rgba(56, 189, 248, 0.4)';
            }}
            let activeBtn = document.getElementById('btnApplyPreset' + idx);
            if (activeBtn) {{
                activeBtn.innerHTML = '✅ سناریوی فعال';
                activeBtn.style.background = 'linear-gradient(135deg, #059669, #10b981)';
                activeBtn.style.borderColor = '#34d399';
            }}

            // 7. Run equity simulation
            runEquitySimulation();
        }}


        // ==========================================
        // 💾 CUSTOM PRESETS MANAGEMENT SYSTEM (LOCALSTORAGE)
        // ==========================================
        let customPresetsList = [];

        function openSavePresetModal() {{
            let activeHoursCount = simState.allowedHours.filter(Boolean).length;
            let activeKingsCount = simState.enabledKings.size;

            let elCnt = document.getElementById('eqKpiCnt');
            let elWR = document.getElementById('eqKpiWR');
            let elPF = document.getElementById('eqKpiPF');
            let elAvg = document.getElementById('eqKpiAvgTrade');
            let elMaxDD = document.getElementById('eqKpiMaxDD');
            let elNet = document.getElementById('eqKpiNetSub');

            let tradesStr = elCnt ? elCnt.textContent : '0 معامله';
            let wrStr = elWR ? elWR.textContent : '0%';
            let pfStr = elPF ? elPF.textContent : '0.00';
            let avgStr = elAvg ? elAvg.textContent : '$0.00';
            let ddStr = elMaxDD ? elMaxDD.textContent : '$0.00';
            let netStr = elNet ? elNet.textContent.replace('سود خالص: ', '').replace('سود: ', '') : '$0.00';

            document.getElementById('modalPreviewMinProfit').textContent = '$' + simState.minProfit.toFixed(2);
            document.getElementById('modalPreviewHours').textContent = activeHoursCount + ' ساعت فعال';
            document.getElementById('modalPreviewKings').textContent = activeKingsCount + ' سلطان فعال';
            document.getElementById('modalPreviewTrades').textContent = tradesStr;
            document.getElementById('modalPreviewWR').textContent = wrStr;
            document.getElementById('modalPreviewPF').textContent = pfStr;
            document.getElementById('modalPreviewAvg').textContent = avgStr;
            document.getElementById('modalPreviewDD').textContent = ddStr;
            document.getElementById('modalPreviewNet').textContent = netStr;

            let titleInput = document.getElementById('modalPresetTitle');
            if (titleInput && !titleInput.value) {{
                titleInput.value = 'سناریوی من (' + tradesStr + ' - PF ' + pfStr + ')';
            }}

            let modal = document.getElementById('savePresetModal');
            if (modal) modal.style.display = 'flex';
        }}

        function closeSavePresetModal() {{
            let modal = document.getElementById('savePresetModal');
            if (modal) modal.style.display = 'none';
        }}

        function confirmSaveCurrentPreset() {{
            let title = document.getElementById('modalPresetTitle').value.trim();
            if (!title) {{
                alert('لطفاً یک نام برای این سناریو وارد کنید.');
                return;
            }}
            let desc = document.getElementById('modalPresetDesc').value.trim();
            if (!desc) {{
                desc = 'کف سود $' + simState.minProfit.toFixed(2) + '، ' + simState.allowedHours.filter(Boolean).length + ' ساعت فعال، ' + simState.enabledKings.size + ' سلطان';
            }}

            let newPreset = {{
                id: 'custom_' + Date.now(),
                title: title,
                desc: desc,
                min_pot: simState.minProfit,
                hours: [...simState.allowedHours],
                kings: Array.from(simState.enabledKings),
                consec_trig: simState.consecLossTrigger,
                consec_sk: simState.consecLossSkipCount,
                consec_day: simState.consecLossSkipDay,
                createdAt: new Date().toLocaleDateString('fa-IR')
            }};

            try {{
                let list = JSON.parse(localStorage.getItem('flagpro_custom_presets') || '[]');
                list.unshift(newPreset);
                localStorage.setItem('flagpro_custom_presets', JSON.stringify(list));
            }} catch(e) {{
                console.error('Failed to save preset to localStorage', e);
            }}

            closeSavePresetModal();
            loadCustomPresets();
            alert('✅ سناریوی «' + title + '» با موفقیت ذخیره شد و در لیست سناریوهای شخصی قرار گرفت.');
        }}

        function loadCustomPresets() {{
            let tbody = document.getElementById('customPresetsTbody');
            if (!tbody) return;

            let list = [];
            try {{
                list = JSON.parse(localStorage.getItem('flagpro_custom_presets') || '[]');
            }} catch(e) {{
                list = [];
            }}
            customPresetsList = list;

            let badge = document.getElementById('customPresetsCountBadge');
            if (badge) badge.textContent = list.length + ' سناریو';

            if (list.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:16px;color:#64748b;font-size:12px;background:#06101c;">' +
                    '💡 هنوز هیچ سناریوی شخصی ذخیره نکرده‌اید. هر زمان فیلترها، اسلایدر یا ساعات را طبق سلیقه خود تغییر دادید، دکمه «💾 ذخیره چیدمان فعلی» را بزنید تا برای همیشه در مرورگر شما ذخیره شود.' +
                    '</td></tr>';
                return;
            }}

            let html = '';
            for (let i = 0; i < list.length; i++) {{
                let p = list[i];
                let kSet = new Set(p.kings);
                let sub = simTrades.filter(t => t.k === 1 && kSet.has(t.kk) && t.pot >= p.min_pot && p.hours[t.h]);
                let c = sub.length;
                let nt = sub.reduce((acc, t) => acc + t.p, 0);
                let wins = sub.filter(t => t.p > 0).length;
                let wr = c > 0 ? (wins / c * 100) : 0;
                let avg = c > 0 ? (nt / c) : 0;
                let gp = sub.filter(t => t.p > 0).reduce((acc, t) => acc + t.p, 0);
                let gl = sub.filter(t => t.p <= 0).reduce((acc, t) => acc + Math.abs(t.p), 0);
                let pf = gl > 0 ? (gp / gl) : 999;

                let bal = 10000.0, peak = 10000.0, max_dd = 0.0;
                for (let j = 0; j < sub.length; j++) {{
                    bal += sub[j].p;
                    if (bal > peak) peak = bal;
                    let dd = peak - bal;
                    if (dd > max_dd) max_dd = dd;
                }}

                let netCol = nt >= 0 ? '#00e676' : '#ef4444';
                let pfStr = pf < 900 ? pf.toFixed(2) : '∞';
                let hoursCnt = p.hours.filter(Boolean).length;

                html += '<tr id="customRow_' + p.id + '" class="preset-table-row" style="border-bottom:1px solid #1e293b;background:#0c192c;transition:all 0.2s;">' +
                    '<td style="text-align:center;padding:10px 8px;font-weight:bold;color:#38bdf8;">⭐ ' + (i + 1) + '</td>' +
                    '<td style="padding:10px 12px;">' +
                        '<div style="font-weight:bold;color:#f1f5f9;font-size:13px;display:flex;align-items:center;gap:6px;">' +
                            '<span>' + p.title + '</span>' +
                            '<span style="background:#1e3a8a;color:#93c5fd;font-size:10px;padding:1px 6px;border-radius:4px;font-weight:bold;">سفارشی</span>' +
                        '</div>' +
                        '<div style="color:#94a3b8;font-size:11px;margin-top:3px;">' + p.desc + '</div>' +
                    '</td>' +
                    '<td style="padding:10px 10px;font-size:11.5px;color:#cbd5e1;text-align:center;">' +
                        '<div>کف سود: <b>$' + p.min_pot.toFixed(2) + '</b> | ساعات: <b>' + hoursCnt + ' ساعت</b></div>' +
                    '</td>' +
                    '<td style="text-align:center;padding:10px 8px;font-size:12px;font-weight:bold;color:#facc15;">' +
                        p.kings.length + ' سلطان' +
                    '</td>' +
                    '<td style="text-align:center;padding:10px 8px;font-weight:bold;font-size:13px;color:#e2e8f0;">' +
                        c.toLocaleString() +
                    '</td>' +
                    '<td style="text-align:center;padding:10px 8px;font-weight:bold;color:#34d399;font-size:13px;">' +
                        wr.toFixed(1) + '٪' +
                    '</td>' +
                    '<td style="text-align:center;padding:10px 8px;font-weight:bold;color:#38bdf8;font-size:13.5px;">' +
                        pfStr +
                    '</td>' +
                    '<td style="text-align:center;padding:10px 8px;font-weight:bold;color:#c084fc;font-size:13.5px;">' +
                        '$' + avg.toFixed(2) +
                    '</td>' +
                    '<td style="text-align:center;padding:10px 8px;font-weight:bold;color:#fca5a5;font-size:12.5px;">' +
                        '$' + max_dd.toFixed(2) +
                    '</td>' +
                    '<td style="text-align:center;padding:10px 10px;font-weight:bold;color:' + netCol + ';font-size:15px;background:#064e3b22;">' +
                        (nt >= 0 ? '+' : '') + '$' + nt.toFixed(2) +
                    '</td>' +
                    '<td style="text-align:center;padding:10px 10px;white-space:nowrap;">' +
                        '<div style="display:flex;gap:4px;justify-content:center;align-items:center;">' +
                            '<button data-id="' + p.id + '" onclick="applyCustomPreset(this.dataset.id)" style="background:linear-gradient(135deg, #0284c7, #0369a1);border:1px solid #38bdf8;color:#fff;padding:5px 10px;border-radius:5px;font-size:11.5px;cursor:pointer;font-weight:bold;">⚡ اعمال</button>' +
                            '<button data-id="' + p.id + '" onclick="updateCustomPresetWithCurrent(this.dataset.id)" style="background:#1e293b;border:1px solid #ca8a04;color:#fef08a;padding:5px 8px;border-radius:5px;font-size:11px;cursor:pointer;" title="به‌روزرسانی این سناریو با فیلترهای فعلی چارت">🔄 بروزرسانی</button>' +
                            '<button data-id="' + p.id + '" onclick="deleteCustomPreset(this.dataset.id)" style="background:#450a0a;border:1px solid #dc2626;color:#fca5a5;padding:5px 8px;border-radius:5px;font-size:11px;cursor:pointer;" title="حذف سناریو">🗑️</button>' +
                        '</div>' +
                    '</td>' +
                '</tr>';
            }}
            tbody.innerHTML = html;
        }}

        function applyCustomPreset(id) {{
            let p = customPresetsList.find(x => x.id === id);
            if (!p) return;

            simState.mode = 'kings';
            let btnK = document.getElementById('btnEqKings');
            let btnA = document.getElementById('btnEqAll');
            if (btnK) btnK.classList.add('active');
            if (btnA) btnA.classList.remove('active');

            // 1. Min profit
            simState.minProfit = p.min_pot;
            let slider = document.getElementById('simProfitSlider');
            if (slider) slider.value = p.min_pot;
            let sliderVal = document.getElementById('simProfitSliderVal');
            if (sliderVal) sliderVal.textContent = '$' + p.min_pot.toFixed(2);
            let pBadge = document.getElementById('simProfitBadge');
            if (pBadge) {{
                pBadge.textContent = (p.min_pot === 0) ? 'بدون فیلتر ($0)' : 'حداقل $' + p.min_pot.toFixed(2);
                pBadge.style.background = (p.min_pot === 0) ? '#064e3b' : '#0369a1';
            }}

            document.querySelectorAll('.profit-preset-btn').forEach(b => {{
                b.classList.remove('active');
                if (parseFloat(b.dataset.val) === p.min_pot) b.classList.add('active');
            }});

            // 2. Allowed Hours
            simState.allowedHours = [...p.hours];
            document.querySelectorAll('.hour-preset-btn').forEach(b => b.classList.remove('active'));

            // 3. Enabled Kings
            simState.enabledKings = new Set(p.kings);

            // 4. Update UI
            // 4. Consecutive Loss Filter
            if (p.consec_trig !== undefined) {{
                simState.consecLossTrigger = p.consec_trig;
                simState.consecLossSkipCount = p.consec_sk || 1;
                simState.consecLossSkipDay = !!p.consec_day;
                syncConsecButtonsUI();
            }}

            renderSimKingsGrid();
            renderSimHoursBar();

            // 5. Highlight active row
            clearPresetActiveState();
            let row = document.getElementById('customRow_' + p.id);
            if (row) {{
                row.style.outline = '2px solid #38bdf8';
                row.style.boxShadow = '0 0 16px rgba(56, 189, 248, 0.4)';
            }}

            runEquitySimulation();
        }}

        function updateCustomPresetWithCurrent(id) {{
            let p = customPresetsList.find(x => x.id === id);
            if (!p) return;
            if (!confirm('آیا مایلید سناریوی «' + p.title + '» با تنظیمات فعلی فیلترهای چارت بازنویسی و بروزرسانی شود؟')) return;

            p.min_pot = simState.minProfit;
            p.hours = [...simState.allowedHours];
            p.kings = Array.from(simState.enabledKings);
            p.consec_trig = simState.consecLossTrigger;
            p.consec_sk = simState.consecLossSkipCount;
            p.consec_day = simState.consecLossSkipDay;
            p.updatedAt = new Date().toLocaleDateString('fa-IR');

            try {{
                localStorage.setItem('flagpro_custom_presets', JSON.stringify(customPresetsList));
            }} catch(e) {{
                console.error(e);
            }}
            loadCustomPresets();
            alert('✅ سناریوی «' + p.title + '» با موفقیت با تنظیمات فعلی بروز شد.');
        }}

        function deleteCustomPreset(id) {{
            let p = customPresetsList.find(x => x.id === id);
            if (!p) return;
            if (!confirm('آیا از حذف سناریوی «' + p.title + '» اطمینان دارید؟')) return;

            customPresetsList = customPresetsList.filter(x => x.id !== id);
            try {{
                localStorage.setItem('flagpro_custom_presets', JSON.stringify(customPresetsList));
            }} catch(e) {{
                console.error(e);
            }}
            loadCustomPresets();
        }}

        function exportCustomPresets() {{
            let list = [];
            try {{
                list = JSON.parse(localStorage.getItem('flagpro_custom_presets') || '[]');
            }} catch(e) {{}}

            if (list.length === 0) {{
                alert('سناریوی ذخیره‌شده‌ای برای خروجی گرفتن وجود ندارد.');
                return;
            }}

            let dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(list, null, 2));
            let dlAnchor = document.createElement('a');
            dlAnchor.setAttribute('href', dataStr);
            dlAnchor.setAttribute('download', 'flagpro_custom_presets.json');
            document.body.appendChild(dlAnchor);
            dlAnchor.click();
            dlAnchor.remove();
        }}

        function importCustomPresets(event) {{
            let file = event.target.files[0];
            if (!file) return;

            let reader = new FileReader();
            reader.onload = function(e) {{
                try {{
                    let imported = JSON.parse(e.target.result);
                    if (!Array.isArray(imported)) throw new Error('فایل معتبر نیست.');

                    let current = JSON.parse(localStorage.getItem('flagpro_custom_presets') || '[]');
                    let merged = [...imported, ...current];
                    // unique by id
                    let map = new Map();
                    merged.forEach(item => map.set(item.id, item));
                    let finalList = Array.from(map.values());

                    localStorage.setItem('flagpro_custom_presets', JSON.stringify(finalList));
                    loadCustomPresets();
                    alert('✅ تعداد ' + imported.length + ' سناریو با موفقیت از فایل وارد شدند.');
                }} catch(err) {{
                    alert('خطا در بارگذاری فایل سناریوها: ' + err.message);
                }}
            }};
            reader.readAsText(file);
            event.target.value = '';
        }}

        function initSimUI() {{
            renderSimKingsGrid();
            renderSimHoursBar();
            loadCustomPresets();
            runEquitySimulation();
        }}

        function renderSimKingsGrid() {{
            let grid = document.getElementById('simKingsGrid');
            if (!grid) return;
            let html = '';
            for (let i = 0; i < kingsSimList.length; i++) {{
                let k = kingsSimList[i];
                let isEnabled = simState.enabledKings.has(k.kk);
                let isDanger = k.is_danger === 1;

                let bg = isEnabled ? (isDanger ? '#240a0a' : '#0c2742') : '#081420';
                let border = isEnabled 
                    ? (isDanger ? 'border:1px solid #ef4444;box-shadow:0 0 8px rgba(239,68,68,0.3);' 
                      : (k.perf ? 'border:1px solid #facc15;' : 'border:1px solid #0284c7;')) 
                    : 'border:1px solid #1e293b;opacity:0.38;';
                let checkIcon = isEnabled ? (isDanger ? '🛑' : '☑️') : '⬜';
                let medal = isDanger ? '⚠️' : (k.perf ? '💎' : (k.run ? '🚀' : '👑'));
                let netCol = k.net >= 0 ? '#34d399' : '#f87171';
                let netSign = k.net >= 0 ? '+' : '';

                let slBadge = isDanger 
                    ? '<span style="background:#7f1d1d;color:#fecaca;font-size:9.5px;padding:1px 5px;border-radius:3px;font-weight:bold;margin-left:4px;" title="تعداد استاپ: ' + k.sl_cnt + ' (' + k.sl_p + '٪) | زیان استاپ‌ها: -$' + k.sl_usd + '">🛑 ' + k.sl_cnt + ' باخت</span>' 
                    : '';

                let disabledText = !isEnabled ? '<span style="color:#64748b;font-size:10px;margin-right:4px;">(حذف شده)</span>' : '';

                html += '<div data-kk="' + k.kk + '" onclick="toggleSimKing(this.dataset.kk)" style="' + bg + ';' + border + 'padding:6px 10px;border-radius:6px;cursor:pointer;user-select:none;transition:all 0.15s;display:flex;justify-content:space-between;align-items:center;">' +
                    '<div style="display:flex;align-items:center;gap:5px;overflow:hidden;">' +
                        '<span style="font-size:13px;">' + checkIcon + '</span>' +
                        '<span style="font-size:11px;">' + medal + '</span>' +
                        '<span style="font-size:11.5px;color:#e2e8f0;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="' + k.role + ' [' + k.tf + ']">' + k.role + '</span>' +
                        '<span style="background:#1e293b;color:#93c5fd;font-size:9.5px;padding:1px 5px;border-radius:3px;font-weight:bold;">' + k.tf + '</span>' +
                        slBadge +
                    '</div>' +
                    '<div style="text-align:left;font-size:11px;font-family:monospace;white-space:nowrap;display:flex;align-items:center;">' +
                        disabledText +
                        '<span style="color:' + netCol + ';font-weight:bold;">$' + netSign + k.net.toFixed(0) + '</span>' +
                        '<span style="color:#64748b;font-size:9.5px;margin-right:4px;">(' + k.cnt + ')</span>' +
                    '</div>' +
                '</div>';
            }}
            grid.innerHTML = html;

            let lbl = document.getElementById('simKingsCountLabel');
            if (lbl) {{
                let activeCnt = simState.enabledKings.size;
                let totCnt = kingsSimList.length;
                lbl.textContent = activeCnt + ' از ' + totCnt + ' سلطان فعال';
                lbl.style.background = (activeCnt === totCnt) ? '#854d0e' : (activeCnt > 0 ? '#0284c7' : '#450a0a');
            }}
            renderSLRiskPanel();
        }}

        function renderSLRiskPanel() {{
            let container = document.getElementById('slTop3CardsContainer');
            if (!container) return;

            let featuredKeys = ['Flag-BE|M1', 'Flag-BU|M1', 'OInner-BU|M1', 'S-RS|M1'];
            let html = '';

            for (let i = 0; i < featuredKeys.length; i++) {{
                let kk = featuredKeys[i];
                let k = kingsSimList.find(x => x.kk === kk);
                if (!k) continue;

                let isEnabled = simState.enabledKings.has(k.kk);
                let cardBg = isEnabled ? 'rgba(239, 68, 68, 0.09)' : '#0f172a';
                let cardBorder = isEnabled ? '1px solid #ef4444' : '1px solid #334155';
                let statusBadge = isEnabled 
                    ? '<span style="background:#450a0a;color:#fca5a5;font-size:10px;padding:2px 6px;border-radius:4px;border:1px solid #7f1d1d;font-weight:bold;">🟢 فعال در سبد</span>'
                    : '<span style="background:#1e293b;color:#94a3b8;font-size:10px;padding:2px 6px;border-radius:4px;border:1px solid #334155;font-weight:bold;">🔴 حذف شده</span>';

                let btnHtml = isEnabled
                    ? '<button data-kk="' + k.kk + '" onclick="toggleSimKing(this.dataset.kk)" style="background:#dc2626;border:1px solid #ef4444;color:#fff;font-size:11px;padding:5px 12px;border-radius:5px;cursor:pointer;font-weight:bold;white-space:nowrap;box-shadow:0 2px 6px rgba(220,38,38,0.3);">❌ حذف این سلطان</button>'
                    : '<button data-kk="' + k.kk + '" onclick="toggleSimKing(this.dataset.kk)" style="background:#065f46;border:1px solid #10b981;color:#a7f3d0;font-size:11px;padding:5px 12px;border-radius:5px;cursor:pointer;font-weight:bold;white-space:nowrap;box-shadow:0 2px 6px rgba(16,185,129,0.3);">➕ بازگردانی به سبد</button>';

                let tagRank = (i === 3) ? '⚠️ بالاترین نرخ باخت (۴۹.۵٪)' : ('#' + (i + 1) + ' بیشترین استاپ چارت');
                let tagCol = (i === 3) ? '#c084fc' : '#f87171';

                html += '<div style="background:' + cardBg + ';border:' + cardBorder + ';border-radius:8px;padding:10px 12px;display:flex;justify-content:space-between;align-items:center;transition:all 0.2s;">' +
                    '<div>' +
                        '<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;flex-wrap:wrap;">' +
                            '<span style="background:#260d0d;color:' + tagCol + ';font-size:10px;font-weight:bold;padding:1px 6px;border-radius:4px;border:1px solid #450a0a;">' + tagRank + '</span>' +
                            '<span style="font-weight:bold;color:#f1f5f9;font-size:13px;">' + k.role + '</span>' +
                            '<span style="background:#1e293b;color:#93c5fd;font-size:9.5px;padding:1px 5px;border-radius:3px;font-weight:bold;">' + k.tf + '</span>' +
                            statusBadge +
                        '</div>' +
                        '<div style="font-size:11px;color:#fca5a5;margin-bottom:2px;">' +
                            '🛑 <b>' + k.sl_cnt + ' استاپ</b> (' + k.sl_p + '٪ باخت) | زیان استاپ‌ها: <b style="color:#ef4444;">-$' + k.sl_usd.toFixed(2) + '</b>' +
                        '</div>' +
                        '<div style="font-size:10.5px;color:#94a3b8;">' +
                            'کل معاملات: ' + k.cnt + ' | سود خالص کل: <span style="color:#34d399;font-weight:bold;">+$' + k.net.toFixed(2) + '</span>' +
                        '</div>' +
                    '</div>' +
                    '<div>' + btnHtml + '</div>' +
                '</div>';
            }}
            container.innerHTML = html;

            let btnCnt = document.getElementById('btnRemoveTop3Cnt');
            if (btnCnt) {{
                let top3Active = top3SLCntKeys.some(kk => simState.enabledKings.has(kk));
                btnCnt.innerHTML = top3Active ? '🚫 حذف ۳ سلطان با بیشترین استاپ (تعداد)' : '✅ ۳ سلطان حذف شدند (کلیک برای بازگردانی)';
                btnCnt.style.background = top3Active ? '#7f1d1d' : '#065f46';
                btnCnt.style.borderColor = top3Active ? '#ef4444' : '#10b981';
            }}

            let btnUsd = document.getElementById('btnRemoveTop3Usd');
            if (btnUsd) {{
                let top3Active = top3SLUsdKeys.some(kk => simState.enabledKings.has(kk));
                btnUsd.innerHTML = top3Active ? '💸 حذف ۳ سلطان با بیشترین زیان دلاری' : '✅ ۳ سلطان حذف شدند (کلیک برای بازگردانی)';
                btnUsd.style.background = top3Active ? '#450a0a' : '#065f46';
                btnUsd.style.borderColor = top3Active ? '#dc2626' : '#10b981';
            }}

            let btnRate = document.getElementById('btnRemoveWorstRate');
            if (btnRate) {{
                let worstActive = top3SLPctKeys.some(kk => simState.enabledKings.has(kk));
                btnRate.innerHTML = worstActive ? '🛡️ حذف سلاطین کم‌دقت (باخت > ۴۵٪)' : '✅ سلاطین کم‌دقت حذف شدند (بازگردانی)';
                btnRate.style.background = worstActive ? '#3b0764' : '#065f46';
                btnRate.style.borderColor = worstActive ? '#a855f7' : '#10b981';
            }}
        }}

        function toggleTop3SL(mode) {{
            clearPresetActiveState();
            let keys = (mode === 'usd') ? top3SLUsdKeys : top3SLCntKeys;
            let anyActive = keys.some(kk => simState.enabledKings.has(kk));
            if (anyActive) {{
                keys.forEach(kk => simState.enabledKings.delete(kk));
            }} else {{
                keys.forEach(kk => simState.enabledKings.add(kk));
            }}
            renderSimKingsGrid();
            runEquitySimulation();
        }}

        function toggleWorstRateKings() {{
            clearPresetActiveState();
            let keys = top3SLPctKeys;
            let anyActive = keys.some(kk => simState.enabledKings.has(kk));
            if (anyActive) {{
                keys.forEach(kk => simState.enabledKings.delete(kk));
            }} else {{
                keys.forEach(kk => simState.enabledKings.add(kk));
            }}
            renderSimKingsGrid();
            runEquitySimulation();
        }}

        function toggleSimKing(kk) {{
            clearPresetActiveState();
            if (simState.enabledKings.has(kk)) {{
                simState.enabledKings.delete(kk);
            }} else {{
                simState.enabledKings.add(kk);
            }}
            renderSimKingsGrid();
            runEquitySimulation();
        }}

        function selectAllKings(enableAll) {{
            clearPresetActiveState();
            if (enableAll) {{
                kingsSimList.forEach(k => simState.enabledKings.add(k.kk));
            }} else {{
                simState.enabledKings.clear();
            }}
            renderSimKingsGrid();
            runEquitySimulation();
        }}

        function selectOnlyPerfectKings() {{
            clearPresetActiveState();
            simState.enabledKings.clear();
            kingsSimList.forEach(k => {{
                if (k.perf === 1) simState.enabledKings.add(k.kk);
            }});
            renderSimKingsGrid();
            runEquitySimulation();
        }}

        function selectOnlyRunnerKings() {{
            clearPresetActiveState();
            simState.enabledKings.clear();
            kingsSimList.forEach(k => {{
                if (k.run === 1) simState.enabledKings.add(k.kk);
            }});
            renderSimKingsGrid();
            runEquitySimulation();
        }}

        function renderSimHoursBar() {{
            let bar = document.getElementById('simHoursBar');
            if (!bar) return;
            let html = '';
            let activeCount = 0;
            for (let h = 0; h < 24; h++) {{
                let on = simState.allowedHours[h];
                if (on) activeCount++;
                let bg = on ? '#0c4a6e' : '#111827';
                let border = on ? 'border:1px solid #0284c7;' : 'border:1px solid #1f2937;';
                let col = on ? '#7dd3fc' : '#475569';
                let decor = on ? '' : 'text-decoration:line-through;opacity:0.5;';
                let hStr = (h < 10 ? '0' : '') + h;

                html += '<button onclick="toggleHour(' + h + ')" style="' + bg + ';' + border + 'color:' + col + ';' + decor + 'font-family:monospace;font-size:10px;padding:5px 2px;border-radius:4px;cursor:pointer;font-weight:bold;" title="ساعت ' + hStr + ':00">' + hStr + '</button>';
            }}
            bar.innerHTML = html;

            let badge = document.getElementById('simHoursActiveBadge');
            if (badge) {{
                badge.textContent = activeCount + ' ساعت فعال (' + (24 - activeCount) + ' فیلتر)';
                badge.style.background = (activeCount === 24) ? '#0c4a6e' : (activeCount > 0 ? '#065f46' : '#450a0a');
            }}
        }}

        function toggleHour(h) {{
            clearPresetActiveState();
            simState.allowedHours[h] = !simState.allowedHours[h];
            renderSimHoursBar();
            document.querySelectorAll('.hour-preset-btn').forEach(b => b.classList.remove('active'));
            runEquitySimulation();
        }}

        function applyHourPreset(preset, btnElem) {{
            clearPresetActiveState();
            document.querySelectorAll('.hour-preset-btn').forEach(b => b.classList.remove('active'));
            if (btnElem) btnElem.classList.add('active');

            if (preset === 'all') {{
                simState.allowedHours.fill(true);
            }} else if (preset === 'no_night') {{
                simState.allowedHours.fill(true);
                let night = [22, 23, 0, 1, 2, 3];
                night.forEach(h => simState.allowedHours[h] = false);
            }} else if (preset === 'lon_ny') {{
                for (let h = 0; h < 24; h++) {{
                    simState.allowedHours[h] = (h >= 7 && h < 20);
                }}
            }} else if (preset === 'asia') {{
                for (let h = 0; h < 24; h++) {{
                    simState.allowedHours[h] = (h >= 0 && h < 8);
                }}
            }}
            renderSimHoursBar();
            runEquitySimulation();
        }}

        function applyProfitPreset(val, btnElem) {{
            clearPresetActiveState();
            simState.minProfit = val;
            let slider = document.getElementById('simProfitSlider');
            if (slider) slider.value = val;
            let sliderVal = document.getElementById('simProfitSliderVal');
            if (sliderVal) sliderVal.textContent = '$' + val.toFixed(2);
            let badge = document.getElementById('simProfitBadge');
            if (badge) {{
                badge.textContent = (val === 0) ? 'بدون فیلتر ($0)' : 'حداقل $' + val.toFixed(2);
                badge.style.background = (val === 0) ? '#064e3b' : '#0369a1';
            }}

            document.querySelectorAll('.profit-preset-btn').forEach(b => b.classList.remove('active'));
            if (btnElem) btnElem.classList.add('active');
            runEquitySimulation();
        }}

        function onProfitSliderInput(val) {{
            clearPresetActiveState();
            let num = parseFloat(val) || 0.0;
            simState.minProfit = num;
            let sliderVal = document.getElementById('simProfitSliderVal');
            if (sliderVal) sliderVal.textContent = '$' + num.toFixed(2);
            let badge = document.getElementById('simProfitBadge');
            if (badge) {{
                badge.textContent = (num === 0) ? 'بدون فیلتر ($0)' : 'حداقل $' + num.toFixed(2);
                badge.style.background = (num === 0) ? '#064e3b' : '#0369a1';
            }}
            document.querySelectorAll('.profit-preset-btn').forEach(b => b.classList.remove('active'));
            runEquitySimulation();
        }}

        function resetAllSimFilters() {{
            clearPresetActiveState();
            simState.mode = 'kings';
            kingsSimList.forEach(k => simState.enabledKings.add(k.kk));
            simState.allowedHours.fill(true);
            simState.minProfit = 0.0;

            let slider = document.getElementById('simProfitSlider');
            if (slider) slider.value = 0;
            let sliderVal = document.getElementById('simProfitSliderVal');
            if (sliderVal) sliderVal.textContent = '$0.00';
            let badge = document.getElementById('simProfitBadge');
            if (badge) {{
                badge.textContent = 'بدون فیلتر ($0)';
                badge.style.background = '#064e3b';
            }}

            document.querySelectorAll('.hour-preset-btn').forEach(b => b.classList.remove('active'));
            let btnHAll = document.getElementById('btnHAll');
            if (btnHAll) btnHAll.classList.add('active');

            document.querySelectorAll('.profit-preset-btn').forEach(b => b.classList.remove('active'));
            let firstProf = document.querySelector('.profit-preset-btn');
            if (firstProf) firstProf.classList.add('active');

            let btnK = document.getElementById('btnEqKings');
            let btnA = document.getElementById('btnEqAll');
            if (btnK) btnK.classList.add('active');
            if (btnA) btnA.classList.remove('active');

            simState.consecLossTrigger = 0;
            simState.consecLossSkipCount = 1;
            simState.consecLossSkipDay = false;
            let selTrig = document.getElementById('selConsecTrigger');
            if (selTrig) selTrig.value = 0;
            let selAct = document.getElementById('selConsecAction');
            if (selAct) selAct.value = 'skip_1';
            syncConsecButtonsUI();

            renderSimKingsGrid();
            renderSimHoursBar();
            runEquitySimulation();
        }}

        function switchEquityMode(mode) {{
            simState.mode = mode;
            let btnK = document.getElementById('btnEqKings');
            let btnA = document.getElementById('btnEqAll');
            if(mode === 'kings') {{
                if(btnK) btnK.classList.add('active');
                if(btnA) btnA.classList.remove('active');
            }} else {{
                if(btnK) btnK.classList.remove('active');
                if(btnA) btnA.classList.add('active');
            }}
            runEquitySimulation();
        }}

        function runEquitySimulation() {{
            let pts = [{{ idx: 0, t: '2026.03.09 00:00', b: 10000.0, p: 0.0, n: 'موجودی اولیه (Initial Balance)' }}];
            let bal = 10000.0;
            let peak = bal;
            let maxDD = 0.0;
            let winCnt = 0;
            let totalTrades = 0;
            let grossP = 0.0;
            let grossL = 0.0;
            let baseTotal = 0;

            let consecLoss = 0;
            let skipsLeft = 0;
            let lastSkipDay = '';
            let consecSkippedCount = 0;
            let consecSavedLosses = 0;
            let consecMissedWins = 0;

            let maxConsecLoss = 0;
            let maxConsecWin = 0;
            let curConsecWin = 0;
            let curLossStreak = 0;
            let lossStreaks = [];

            for (let i = 0; i < simTrades.length; i++) {{
                let t = simTrades[i];
                let isMatchBase = (simState.mode === 'kings') ? (t.k === 1) : true;
                if (!isMatchBase) continue;
                baseTotal++;

                // King filter
                if (simState.mode === 'kings' && !simState.enabledKings.has(t.kk)) continue;

                // Hour filter
                if (!simState.allowedHours[t.h]) continue;

                // Min profit filter
                if (t.pot < simState.minProfit) continue;

                // Consecutive loss circuit breaker filter
                let tradeDate = t.t ? t.t.substring(0, 10) : '';
                if (simState.consecLossTrigger > 0) {{
                    if (simState.consecLossSkipDay && lastSkipDay === tradeDate) {{
                        consecSkippedCount++;
                        if (t.p <= 0) consecSavedLosses++; else consecMissedWins++;
                        continue;
                    }}
                    if (skipsLeft > 0) {{
                        skipsLeft--;
                        consecSkippedCount++;
                        if (t.p <= 0) consecSavedLosses++; else consecMissedWins++;
                        continue;
                    }}
                }}

                // Trade accepted!
                totalTrades++;
                bal += t.p;
                pts.push({{ idx: totalTrades, t: t.t, b: Math.round(bal * 100) / 100, p: t.p, n: t.r + ' [' + t.tf + ']' }});
                if (bal > peak) peak = bal;
                let dd = peak - bal;
                if (dd > maxDD) maxDD = dd;
                if (t.p > 0) {{
                    winCnt++;
                    grossP += t.p;
                    curConsecWin++;
                    if (curConsecWin > maxConsecWin) maxConsecWin = curConsecWin;
                    if (curLossStreak > 0) {{
                        lossStreaks.push(curLossStreak);
                        curLossStreak = 0;
                    }}
                    consecLoss = 0;
                }} else {{
                    grossL += Math.abs(t.p);
                    curConsecWin = 0;
                    curLossStreak++;
                    if (curLossStreak > maxConsecLoss) maxConsecLoss = curLossStreak;
                    consecLoss++;
                    if (simState.consecLossTrigger > 0 && consecLoss >= simState.consecLossTrigger) {{
                        if (simState.consecLossSkipDay) {{
                            lastSkipDay = tradeDate;
                        }} else {{
                            skipsLeft = simState.consecLossSkipCount;
                        }}
                        consecLoss = 0;
                    }}
                }}
            }}

            if (curLossStreak > 0) {{
                lossStreaks.push(curLossStreak);
            }}

            let streakDist = {{}};
            for (let s of lossStreaks) {{
                streakDist[s] = (streakDist[s] || 0) + 1;
            }}
            let totalLossStreaks = lossStreaks.length;
            let avgLossStreak = totalLossStreaks > 0 ? (lossStreaks.reduce((a, b) => a + b, 0) / totalLossStreaks) : 0;

            let net = bal - 10000.0;
            let netPct = (net / 10000.0) * 100;
            let maxDDPct = peak > 0 ? ((maxDD / peak) * 100) : 0;
            let pf = grossL > 0 ? (grossP / grossL) : (grossP > 0 ? 999.0 : 1.0);
            let wr = totalTrades > 0 ? ((winCnt / totalTrades) * 100) : 0;
            let avgTrade = totalTrades > 0 ? (net / totalTrades) : 0;

            // Update KPI Banner
            let elBal = document.getElementById('eqKpiFinalBal');
            let elNetSub = document.getElementById('eqKpiNetSub');
            let elPeak = document.getElementById('eqKpiPeak');
            let elMaxDD = document.getElementById('eqKpiMaxDD');
            let elMaxDDSub = document.getElementById('eqKpiMaxDDSub');
            let elPF = document.getElementById('eqKpiPF');
            let elWR = document.getElementById('eqKpiWR');
            let elCnt = document.getElementById('eqKpiCnt');
            let elAvg = document.getElementById('eqKpiAvgTrade');

            if (elBal) {{
                let sign = bal >= 10000 ? '' : '-';
                elBal.textContent = '$' + bal.toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
                elBal.style.color = bal >= 10000 ? '#00e676' : '#ef4444';
            }}
            if (elNetSub) {{
                let sign = net >= 0 ? '+' : '';
                elNetSub.textContent = 'سود خالص: $' + sign + net.toFixed(2) + ' (' + sign + netPct.toFixed(2) + '٪)';
            }}
            if (elPeak) elPeak.textContent = '$' + peak.toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
            if (elMaxDD) elMaxDD.textContent = '$' + maxDD.toFixed(2) + ' (' + maxDDPct.toFixed(2) + '٪)';
            if (elMaxDDSub) elMaxDDSub.textContent = 'افت از سقف $' + peak.toFixed(0);
            if (elPF) elPF.textContent = pf >= 900 ? '∞ قطعی' : pf.toFixed(2);
            if (elWR) elWR.textContent = wr.toFixed(1) + '٪ (' + winCnt + ' برد)';
            if (elCnt) elCnt.textContent = totalTrades.toLocaleString() + ' معامله';
            if (elAvg) {{
                let aSign = avgTrade >= 0 ? '+' : '';
                elAvg.textContent = '$' + aSign + avgTrade.toFixed(2);
                elAvg.style.color = avgTrade >= 0 ? '#38bdf8' : '#f87171';
            }}

            // Update Simulator Footer Status
            let elAct = document.getElementById('simActiveTradesCount');
            let elBase = document.getElementById('simTotalBaseCount');
            let elFilt = document.getElementById('simFilteredOutCount');
            let elWrVal = document.getElementById('simWinRateVal');
            let elPfVal = document.getElementById('simPfVal');

            if (elAct) elAct.textContent = totalTrades.toLocaleString();
            if (elBase) elBase.textContent = baseTotal.toLocaleString();
            if (elFilt) {{
                let diff = baseTotal - totalTrades;
                elFilt.textContent = diff.toLocaleString() + ' معامله حذف شده';
            }}
            if (elWrVal) elWrVal.textContent = wr.toFixed(1) + '٪';
            if (elPfVal) elPfVal.textContent = pf >= 900 ? '∞ قطعی' : pf.toFixed(2);

            let lbl = document.getElementById('lblEqPts');
            if (lbl) lbl.textContent = Math.max(0, pts.length - 1);

            if (elMaxDDSub) elMaxDDSub.textContent = 'افت از سقف | سقف باخت: ' + maxConsecLoss + ' ترید';

            updateConsecutiveLossUI(maxConsecLoss, maxConsecWin, totalLossStreaks, avgLossStreak, streakDist, consecSkippedCount, consecSavedLosses, consecMissedWins, maxDD);

            currentSimPts = pts;
            drawEquityChart();
        }}

        function drawEquityChart() {{
            let canvas = document.getElementById('equityCanvas');
            if (!canvas) return;
            let ctx = canvas.getContext('2d');
            if (!ctx) return;

            let dpr = window.devicePixelRatio || 1;
            let rect = canvas.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return;

            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            ctx.scale(dpr, dpr);

            let w = rect.width;
            let h = rect.height;
            let padLeft = 30;
            let padRight = 75;
            let padTop = 25;
            let padBottom = 35;
            let plotW = w - padLeft - padRight;
            let plotH = h - padTop - padBottom;

            let pts = currentSimPts;
            if (!pts || pts.length <= 1) {{
                ctx.clearRect(0, 0, w, h);
                ctx.fillStyle = '#0b0f19';
                ctx.fillRect(0, 0, w, h);
                ctx.fillStyle = '#94a3b8';
                ctx.font = '13px Segoe UI, Tahoma, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('هیچ معامله‌ای با این ترکیب فیلترها وجود ندارد! لطفاً فیلترها را تسهیل کنید.', w / 2, h / 2);
                canvas._coords = [];
                return;
            }}

            let minBal = Infinity;
            let maxBal = -Infinity;
            for (let i = 0; i < pts.length; i++) {{
                if (pts[i].b < minBal) minBal = pts[i].b;
                if (pts[i].b > maxBal) maxBal = pts[i].b;
            }}
            let balRange = maxBal - minBal;
            if (balRange < 50) balRange = 50;
            minBal = Math.floor((minBal - balRange * 0.05) / 50) * 50;
            maxBal = Math.ceil((maxBal + balRange * 0.05) / 50) * 50;
            balRange = maxBal - minBal;

            ctx.clearRect(0, 0, w, h);

            // Background
            ctx.fillStyle = '#0b0f19';
            ctx.fillRect(0, 0, w, h);

            // Plot area
            ctx.fillStyle = '#0f172a';
            ctx.fillRect(padLeft, padTop, plotW, plotH);

            // Horizontal Grid & Price Labels
            let gridSteps = 6;
            ctx.strokeStyle = '#1e293b';
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.font = '11px Segoe UI, Tahoma, sans-serif';
            ctx.textAlign = 'left';

            for (let s = 0; s <= gridSteps; s++) {{
                let val = minBal + (balRange / gridSteps) * s;
                let y = padTop + plotH - ((val - minBal) / balRange) * plotH;

                ctx.beginPath();
                ctx.moveTo(padLeft, y);
                ctx.lineTo(padLeft + plotW, y);
                ctx.stroke();

                ctx.fillStyle = '#94a3b8';
                ctx.fillText('$' + val.toFixed(0), padLeft + plotW + 10, y + 4);
            }}

            // Vertical Grid & Dates
            let totalPts = pts.length;
            let dateSteps = 6;
            ctx.textAlign = 'center';

            for (let s = 0; s <= dateSteps; s++) {{
                let idx = Math.min(Math.floor((totalPts - 1) * (s / dateSteps)), totalPts - 1);
                let x = padLeft + (idx / (totalPts - 1)) * plotW;

                ctx.beginPath();
                ctx.moveTo(x, padTop);
                ctx.lineTo(x, padTop + plotH);
                ctx.stroke();

                let dStr = pts[idx].t ? pts[idx].t.substring(5, 10) : '';
                ctx.fillStyle = '#64748b';
                ctx.fillText(dStr, x, padTop + plotH + 20);
            }}

            ctx.setLineDash([]);

            // Baseline ($10,000)
            let baseVal = 10000.0;
            if (baseVal >= minBal && baseVal <= maxBal) {{
                let baseY = padTop + plotH - ((baseVal - minBal) / balRange) * plotH;
                ctx.strokeStyle = '#475569';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(padLeft, baseY);
                ctx.lineTo(padLeft + plotW, baseY);
                ctx.stroke();
            }}

            // Curve points
            let coords = [];
            for (let i = 0; i < totalPts; i++) {{
                let x = padLeft + (i / (totalPts - 1)) * plotW;
                let y = padTop + plotH - ((pts[i].b - minBal) / balRange) * plotH;
                coords.push({{ x: x, y: y, pt: pts[i] }});
            }}

            // Gradient Fill
            let grad = ctx.createLinearGradient(0, padTop, 0, padTop + plotH);
            if (simState.mode === 'kings') {{
                grad.addColorStop(0, 'rgba(56, 189, 248, 0.30)');
                grad.addColorStop(1, 'rgba(56, 189, 248, 0.0)');
            }} else {{
                grad.addColorStop(0, 'rgba(168, 85, 247, 0.30)');
                grad.addColorStop(1, 'rgba(168, 85, 247, 0.0)');
            }}

            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.moveTo(coords[0].x, padTop + plotH);
            for (let i = 0; i < coords.length; i++) {{
                ctx.lineTo(coords[i].x, coords[i].y);
            }}
            ctx.lineTo(coords[coords.length - 1].x, padTop + plotH);
            ctx.closePath();
            ctx.fill();

            // Line
            ctx.strokeStyle = (simState.mode === 'kings') ? '#38bdf8' : '#a855f7';
            ctx.lineWidth = 2.2;
            ctx.beginPath();
            for (let i = 0; i < coords.length; i++) {{
                if (i === 0) ctx.moveTo(coords[i].x, coords[i].y);
                else ctx.lineTo(coords[i].x, coords[i].y);
            }}
            ctx.stroke();

            // Border
            ctx.strokeStyle = '#334155';
            ctx.lineWidth = 1;
            ctx.strokeRect(padLeft, padTop, plotW, plotH);

            canvas._coords = coords;
            canvas._padLeft = padLeft;
            canvas._padTop = padTop;
            canvas._plotW = plotW;
            canvas._plotH = plotH;
        }}

        function initEquityCanvasEvents() {{
            let canvas = document.getElementById('equityCanvas');
            if (!canvas || simCanvasEventsInitialized) return;
            simCanvasEventsInitialized = true;

            canvas.addEventListener('mousemove', function(evt) {{
                if (!canvas._coords || canvas._coords.length === 0) return;
                let rect = canvas.getBoundingClientRect();
                let mouseX = evt.clientX - rect.left;
                let mouseY = evt.clientY - rect.top;

                let tt = document.getElementById('equityTooltip');
                if (mouseX < canvas._padLeft || mouseX > canvas._padLeft + canvas._plotW ||
                    mouseY < canvas._padTop || mouseY > canvas._padTop + canvas._plotH) {{
                    if(tt) tt.style.display = 'none';
                    return;
                }}

                let coords = canvas._coords;
                let ratio = (mouseX - canvas._padLeft) / canvas._plotW;
                let idx = Math.round(ratio * (coords.length - 1));
                if (idx < 0) idx = 0;
                if (idx >= coords.length) idx = coords.length - 1;

                let target = coords[idx];
                let pt = target.pt;

                drawEquityChart();
                let ctx = canvas.getContext('2d');
                let dpr = window.devicePixelRatio || 1;
                ctx.save();
                ctx.scale(dpr, dpr);

                // Crosshair vertical
                ctx.strokeStyle = 'rgba(248, 250, 252, 0.4)';
                ctx.lineWidth = 1;
                ctx.setLineDash([2, 2]);
                ctx.beginPath();
                ctx.moveTo(target.x, canvas._padTop);
                ctx.lineTo(target.x, canvas._padTop + canvas._plotH);
                ctx.stroke();

                // Target Circle
                ctx.setLineDash([]);
                ctx.fillStyle = '#facc15';
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(target.x, target.y, 5, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();
                ctx.restore();

                if (tt) {{
                    tt.style.display = 'block';
                    let pnlCol = pt.p >= 0 ? '#00e676' : '#ef4444';
                    let pnlSign = pt.p >= 0 ? '+' : '';
                    let totProfit = pt.b - 10000.0;
                    let totCol = totProfit >= 0 ? '#00e676' : '#ef4444';
                    let totSign = totProfit >= 0 ? '+' : '';

                    tt.innerHTML = `
                        <div style="font-weight:bold;color:#facc15;margin-bottom:4px;border-bottom:1px solid #334155;padding-bottom:2px;">معامله #${{pt.idx}} - ${{pt.n}}</div>
                        <div style="color:#94a3b8;font-size:11px;">🕒 زمان: <span style="direction:ltr;display:inline-block;font-family:monospace;color:#f1f5f9;">${{pt.t}}</span></div>
                        <div style="margin-top:4px;">سود این معامله: <b style="color:${{pnlCol}};">${{pnlSign}}$${{pt.p.toFixed(2)}}</b></div>
                        <div>بالانس حساب: <b style="color:#38bdf8;">$${{pt.b.toFixed(2)}}</b></div>
                        <div>رشد کل: <b style="color:${{totCol}};">${{totSign}}$${{totProfit.toFixed(2)}} (${{(totProfit/100).toFixed(2)}}%)</b></div>
                    `;

                    let ttX = target.x + 15;
                    let ttY = target.y - 40;
                    if (ttX + 220 > rect.width) ttX = target.x - 230;
                    if (ttY < 10) ttY = 10;
                    tt.style.left = ttX + 'px';
                    tt.style.top = ttY + 'px';
                }}
            }});

            canvas.addEventListener('mouseleave', function() {{
                let tt = document.getElementById('equityTooltip');
                if (tt) tt.style.display = 'none';
                drawEquityChart();
            }});

            window.addEventListener('resize', function() {{
                drawEquityChart();
            }});
        }}


        function selectWeeklyDetail(cardId) {{
            if(!cardId) return;
            document.querySelectorAll('.week-detail-card').forEach(c => c.style.display = 'none');
            let el = document.getElementById(cardId);
            if(el) {{
                el.style.display = 'block';
                el.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
            }}
        }}

        function filterWeeklyMode(mode) {{
            let kingsRows = document.querySelectorAll('.wk-row-kings');
            let allRows = document.querySelectorAll('.wk-row-all');
            let btnKings = document.getElementById('btnWkTableKings');
            let btnAll = document.getElementById('btnWkTableAll');
            if(mode === 'kings') {{
                kingsRows.forEach(r => r.style.display = '');
                allRows.forEach(r => r.style.display = 'none');
                if(btnKings) btnKings.classList.add('active');
                if(btnAll) btnAll.classList.remove('active');
            }} else {{
                kingsRows.forEach(r => r.style.display = 'none');
                allRows.forEach(r => r.style.display = '');
                if(btnKings) btnKings.classList.remove('active');
                if(btnAll) btnAll.classList.add('active');
            }}
        }}

        
        function openEqSubtab(evt, subtabId) {{
            document.querySelectorAll('.eq-subpanel').forEach(p => p.style.display = 'none');
            document.querySelectorAll('.eq-subtab-btn').forEach(b => b.classList.remove('active'));

            let target = document.getElementById(subtabId);
            if (target) target.style.display = 'block';
            if (evt && evt.currentTarget) evt.currentTarget.classList.add('active');

            if (subtabId === 'eq-sub-weekly') {{
                setTimeout(() => {{
                    drawWeeklyBarChart(currentWeeklyBarMode);
                }}, 40);
            }}
        }}

        
        // ====================================================
        // 🛡️ CONSECUTIVE LOSS FILTER CONTROLLER & UI SYNC
        // ====================================================
        function applyConsecFromFilterTab(trigger, skipCount, skipDay, btnEl) {{
            setConsecLossFilter(trigger, skipCount, skipDay, btnEl);
        }}

        function setConsecLossFilter(trigger, skipCount, skipDay, btnEl) {{
            simState.consecLossTrigger = trigger;
            simState.consecLossSkipCount = skipCount;
            simState.consecLossSkipDay = skipDay;

            let selTrig = document.getElementById('selConsecTrigger');
            let selAct = document.getElementById('selConsecAction');
            if (selTrig) selTrig.value = trigger;
            if (selAct) {{
                if (skipDay) selAct.value = 'skip_day';
                else selAct.value = 'skip_' + (skipCount || 1);
            }}

            syncConsecButtonsUI();
            runEquitySimulation();
        }}

        function onCustomConsecChange() {{
            let selTrig = document.getElementById('selConsecTrigger');
            let selAct = document.getElementById('selConsecAction');
            let trigger = parseInt(selTrig ? selTrig.value : 0, 10);
            let act = selAct ? selAct.value : 'skip_1';

            let skipDay = (act === 'skip_day');
            let skipCount = 1;
            if (act === 'skip_2') skipCount = 2;
            if (act === 'skip_3') skipCount = 3;

            simState.consecLossTrigger = trigger;
            simState.consecLossSkipCount = skipCount;
            simState.consecLossSkipDay = skipDay;

            syncConsecButtonsUI();
            runEquitySimulation();
        }}

        function syncConsecButtonsUI() {{
            let t = simState.consecLossTrigger;
            let sk = simState.consecLossSkipCount;
            let day = simState.consecLossSkipDay;

            document.querySelectorAll('.consec-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.consec-btn-filter').forEach(b => b.classList.remove('active'));

            let badge1 = document.getElementById('consecLossSummaryBadge');
            let badge2 = document.getElementById('simConsecBadge2');

            if (t === 0) {{
                let b0 = document.getElementById('btnConsecNone');
                if (b0) b0.classList.add('active');
                let f0 = document.querySelector('.consec-btn-filter[data-trig="0"]');
                if (f0) f0.classList.add('active');
                if (badge1) {{ badge1.textContent = 'وضعیت: فیلتر خاموش (ترید عادی)'; badge1.style.color = '#7dd3fc'; badge1.style.borderColor = '#0284c7'; }}
                if (badge2) {{ badge2.textContent = 'بدون وقفه (خاموش)'; badge2.style.color = '#cbd5e1'; badge2.style.background = '#1e293b'; }}
            }} else {{
                let text = '';
                if (day) {{
                    text = 'توقف بعد از ' + t + ' باخت تا فردا';
                    let bd = document.getElementById('btnConsec2Daily');
                    if (bd && t === 2) bd.classList.add('active');
                    let fd = document.querySelector('.consec-btn-filter[data-day="1"]');
                    if (fd && t === 2) fd.classList.add('active');
                }} else {{
                    text = 'بعد از ' + t + ' باخت 👈 رد ' + sk + ' ترید';
                    if (t === 2 && sk === 1) {{
                        let b = document.getElementById('btnConsec2Skip1');
                        if (b) b.classList.add('active');
                        let fb = document.querySelector('.consec-btn-filter[data-trig="2"][data-sk="1"]');
                        if (fb) fb.classList.add('active');
                    }} else if (t === 2 && sk === 2) {{
                        let b = document.getElementById('btnConsec2Skip2');
                        if (b) b.classList.add('active');
                        let fb = document.querySelector('.consec-btn-filter[data-trig="2"][data-sk="2"]');
                        if (fb) fb.classList.add('active');
                    }} else if (t === 3 && sk === 1) {{
                        let b = document.getElementById('btnConsec3Skip1');
                        if (b) b.classList.add('active');
                        let fb = document.querySelector('.consec-btn-filter[data-trig="3"][data-sk="1"]');
                        if (fb) fb.classList.add('active');
                    }}
                }}
                if (badge1) {{ badge1.textContent = '⚡ فعال: ' + text; badge1.style.color = '#34d399'; badge1.style.borderColor = '#10b981'; }}
                if (badge2) {{ badge2.textContent = '⚡ فعال: ' + text; badge2.style.color = '#34d399'; badge2.style.background = '#064e3b'; }}
            }}
        }}

        function updateConsecutiveLossUI(maxLoss, maxWin, totalLossStreaks, avgLoss, streakDist, skippedCnt, savedLosses, missedWins, maxDD) {{
            let elMaxLoss = document.getElementById('kpiMaxConsecLoss');
            let elMaxWin = document.getElementById('kpiMaxConsecWin');
            let elTotalStreaks = document.getElementById('kpiTotalLossStreaks');
            let elAvgLoss = document.getElementById('kpiAvgLossStreak');

            if (elMaxLoss) elMaxLoss.textContent = maxLoss + ' معامله';
            if (elMaxWin) elMaxWin.textContent = maxWin + ' معامله';
            if (elTotalStreaks) elTotalStreaks.textContent = totalLossStreaks.toLocaleString() + ' رگه';
            if (elAvgLoss) elAvgLoss.textContent = avgLoss.toFixed(1) + ' معامله';

            // Render distribution cards
            let grid = document.getElementById('consecLossBarsGrid');
            if (grid) {{
                let html = '';
                let streakKeys = [1, 2, 3, 4, 5, 6];
                for (let k of streakKeys) {{
                    let count = streakDist[k] || 0;
                    let pct = totalLossStreaks > 0 ? ((count / totalLossStreaks) * 100) : 0;
                    let color = k === 1 ? '#38bdf8' : (k === 2 ? '#facc15' : (k === 3 ? '#fb923c' : '#ef4444'));
                    let bg = k === 1 ? 'rgba(56, 189, 248, 0.1)' : (k === 2 ? 'rgba(250, 204, 21, 0.1)' : 'rgba(239, 68, 68, 0.15)');
                    let title = (k === 6) ? '۶+ باخت متوالی' : (k + ' باخت متوالی');
                    html += `
                        <div style="background:${{bg}};border:1px solid ${{color}};padding:6px 8px;border-radius:6px;text-align:center;">
                            <div style="font-size:10px;color:#94a3b8;margin-bottom:2px;">${{title}}</div>
                            <div style="font-size:14px;font-weight:bold;color:${{color}};">${{count}} بار</div>
                            <div style="font-size:9.5px;color:#cbd5e1;margin-top:2px;">${{pct.toFixed(1)}}٪</div>
                            <div style="width:100%;height:3px;background:#1e293b;border-radius:2px;margin-top:4px;overflow:hidden;">
                                <div style="width:${{Math.min(100, pct)}}%;height:100%;background:${{color}};"></div>
                            </div>
                        </div>
                    `;
                }}
                grid.innerHTML = html;
            }}

            // Impact box
            let elSkipped = document.getElementById('consecSkippedTradesVal');
            let elSaved = document.getElementById('consecSavedLossesVal');
            let elMissed = document.getElementById('consecMissedWinsVal');
            let elDD = document.getElementById('consecDDImpactVal');

            if (elSkipped) elSkipped.textContent = skippedCnt.toLocaleString();
            if (elSaved) elSaved.textContent = savedLosses.toLocaleString() + ' استاپ نجات یافت';
            if (elMissed) elMissed.textContent = missedWins.toLocaleString() + ' برد رد شد';
            if (elDD) elDD.textContent = 'افت سرمایه فعلی: $' + maxDD.toFixed(2);
        }}

        
        
        // ====================================================
        // 🤖 CLIENT-SIDE AI AUTO-OPTIMIZER ENGINE
        // ====================================================
        function runClientAutoOptimizer() {{
            let kingTrades = simTrades.filter(t => t.k === 1);
            let totalBase = kingTrades.length;
            if (totalBase === 0) {{
                alert('هیچ معامله‌ای برای بهینه‌سازی یافت نشد.');
                return;
            }}

            let min15 = Math.max(20, Math.floor(totalBase * 0.15));

            // Calculate king PF stats
            let kStats = {{}};
            for (let t of kingTrades) {{
                if (!kStats[t.kk]) kStats[t.kk] = {{ gp: 0, gl: 0, p: 0, wins: 0, cnt: 0 }};
                kStats[t.kk].cnt++;
                kStats[t.kk].p += t.p;
                if (t.p > 0) {{ kStats[t.kk].wins++; kStats[t.kk].gp += t.p; }}
                else {{ kStats[t.kk].gl += Math.abs(t.p); }}
            }}
            for (let kk in kStats) {{
                kStats[kk].pf = kStats[kk].gl > 0 ? (kStats[kk].gp / kStats[kk].gl) : 999;
            }}
            let sortedKings = Object.keys(kStats).sort((a, b) => kStats[a].pf - kStats[b].pf);
            let allKingsSet = new Set(Object.keys(kStats));

            let hoursMap = {{
                'all': new Array(24).fill(true),
                'no_night': Array.from({{length: 24}}, (_, h) => !(h >= 22 || h <= 3)),
                'lon_ny': Array.from({{length: 24}}, (_, h) => (h >= 7 && h < 20)),
                'core_day': Array.from({{length: 24}}, (_, h) => (h >= 8 && h <= 18))
            }};

            let pots = [0.0, 1.0, 1.5, 2.0, 2.5, 3.0];
            let cbs = [{{trig: 0, sk: 0}}, {{trig: 2, sk: 1}}];

            let best = null;
            let bestScore = -999999;

            for (let hKey in hoursMap) {{
                let hArr = hoursMap[hKey];
                for (let pot of pots) {{
                    for (let dropN = 0; dropN <= Math.min(7, sortedKings.length - 5); dropN++) {{
                        let activeKings = new Set(allKingsSet);
                        for (let d = 0; d < dropN; d++) activeKings.delete(sortedKings[d]);

                        for (let cb of cbs) {{
                            let bal = 10000.0, peak = bal, maxDD = 0.0, wins = 0, total = 0, gp = 0.0, gl = 0.0;
                            let consecLoss = 0, skips = 0;

                            for (let t of kingTrades) {{
                                if (!activeKings.has(t.kk)) continue;
                                if (!hArr[t.h]) continue;
                                if (t.pot < pot) continue;
                                if (skips > 0) {{ skips--; continue; }}

                                total++;
                                bal += t.p;
                                if (bal > peak) peak = bal;
                                let dd = peak - bal;
                                if (dd > maxDD) maxDD = dd;
                                if (t.p > 0) {{
                                    wins++; gp += t.p; consecLoss = 0;
                                }} else {{
                                    gl += Math.abs(t.p); consecLoss++;
                                    if (cb.trig > 0 && consecLoss >= cb.trig) {{
                                        skips = cb.sk; consecLoss = 0;
                                    }}
                                }}
                            }}

                            if (total < min15) continue;
                            let wr = (wins / total) * 100;
                            let pf = gl > 0 ? (gp / gl) : 999;
                            let net = bal - 10000.0;
                            let avg = net / total;
                            let score = Math.pow(pf, 1.3) * (wr / 50.0) * Math.max(0.5, avg) / Math.max(12.0, maxDD) * 100;

                            if (score > bestScore) {{
                                bestScore = score;
                                best = {{
                                    hKey: hKey, hArr: hArr, pot: pot, kings: Array.from(activeKings),
                                    cb: cb, total: total, wr: wr, pf: pf, avg: avg, maxDD: maxDD, net: net
                                }};
                            }}
                        }}
                    }}
                }}
            }}

            if (!best) {{
                alert('هیچ ترکیب متناسبی با شرط حداقل ۱۵٪ معاملات یافت نشد.');
                return;
            }}

            let msg = [
                '🏆 بهترین ترکیب کشف‌شده توسط هوش مصنوعی (شرط حداقل ۱۵٪ = ' + min15 + ' معامله):',
                '',
                '🔹 تعداد معامله: ' + best.total + ' (' + ((best.total/totalBase)*100).toFixed(1) + '٪ کل چارت)',
                '🔹 وین‌ریت: ' + best.wr.toFixed(1) + '٪',
                '🔹 پرافیت فاکتور: ' + (best.pf < 900 ? best.pf.toFixed(2) : 'MAX'),
                '🔹 میانگین سود هر ترید: $' + best.avg.toFixed(2),
                '🔹 حداکثر افت سرمایه (DD): $' + best.maxDD.toFixed(2),
                '🔹 سود خالص: $' + best.net.toFixed(2),
                '🔹 تنظیمات: کف سود $' + best.pot.toFixed(2) + ' | ' + best.kings.length + ' سلطان فعال' + (best.cb.trig > 0 ? ' | وقفه بعد از ۲ استاپ' : ''),
                '',
                'آیا مایلید این چیدمان بلافاصله روی نمودار و فیلترها اعمال شود؟'
            ].join('\\n');

            if (confirm(msg)) {{
                simState.mode = 'kings';
                simState.minProfit = best.pot;
                simState.allowedHours = [...best.hArr];
                simState.enabledKings = new Set(best.kings);
                simState.consecLossTrigger = best.cb.trig;
                simState.consecLossSkipCount = best.cb.sk;
                simState.consecLossSkipDay = false;

                // Sync UI elements
                let slider = document.getElementById('simProfitSlider');
                if (slider) slider.value = best.pot;
                let sliderVal = document.getElementById('simProfitSliderVal');
                if (sliderVal) sliderVal.textContent = '$' + best.pot.toFixed(2);

                renderSimKingsGrid();
                renderSimHoursBar();
                syncConsecButtonsUI();
                runEquitySimulation();
                alert('✅ چیدمان قهرمان هوش مصنوعی با موفقیت اعمال شد!');
            }}
        }}

        function toggleTwoColLayout() {{
            let container = document.getElementById('eqTwoColContainer');
            let btn = document.getElementById('btnToggleTwoCol');
            if (!container) return;
            if (container.classList.contains('single-col')) {{
                container.classList.remove('single-col');
                if (btn) {{ btn.textContent = '⛶'; btn.title = 'حالت تمام‌صفحه'; }}
            }} else {{
                container.classList.add('single-col');
                if (btn) {{ btn.textContent = '🗗'; btn.title = 'حالت دو ستونی'; }}
            }}
            setTimeout(() => {{
                drawEquityChart();
            }}, 50);
        }}

        function openTab(evt, tabId) {{
            let contents = document.querySelectorAll('.tab-content');
            contents.forEach(c => c.classList.remove('active'));

            let btns = document.querySelectorAll('.tab-btn');
            btns.forEach(b => b.classList.remove('active'));

            document.getElementById(tabId).classList.add('active');
            evt.currentTarget.classList.add('active');

            if (tabId === 'tab-equity') {{
                setTimeout(() => {{
                    initEquityCanvasEvents();
                    initSimUI();
                    initWeeklyBarCanvasEvents();
                    drawWeeklyBarChart(currentWeeklyBarMode);
                }}, 50);
            }}

            if (tabId === 'tab-trades') {{
                setTimeout(() => {{
                    renderTrades();
                }}, 30);
            }}
        }}

        let sortDirections = {{ 'data-score': true }};

        function sortTableByAttr(tableId, attrName, isNumeric, defaultDesc, btnElem) {{
            let table = document.getElementById(tableId);
            if (!table) return;
            let tbody = table.querySelector('tbody');
            if (!tbody) return;
            let rows = Array.from(tbody.querySelectorAll('tr.tf-row'));

            let isCurrentDesc = sortDirections[attrName];
            let newDesc = (isCurrentDesc === undefined) ? defaultDesc : !isCurrentDesc;
            sortDirections[attrName] = newDesc;

            let headers = table.querySelectorAll('th');
            headers.forEach(h => {{
                let icon = h.querySelector('.sort-icon');
                if (icon) icon.textContent = ' ⬍';
                h.style.background = '';
            }});

            let activeTh = table.querySelector(`th[data-sort="${{attrName}}"]`);
            if (activeTh) {{
                let icon = activeTh.querySelector('.sort-icon');
                if (icon) icon.textContent = newDesc ? ' ▼' : ' ▲';
                activeTh.style.background = '#1e293b';
            }}

            if (btnElem) {{
                let p = btnElem.parentElement;
                if (p) {{
                    p.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                    btnElem.classList.add('active');
                }}
            }}

            rows.sort((a, b) => {{
                let valA = a.getAttribute(attrName) || '';
                let valB = b.getAttribute(attrName) || '';

                if (isNumeric) {{
                    let numA = parseFloat(valA) || 0.0;
                    let numB = parseFloat(valB) || 0.0;
                    if (numA !== numB) {{
                        return newDesc ? (numB - numA) : (numA - numB);
                    }}
                    let evA = parseFloat(a.getAttribute('data-score')) || 0.0;
                    let evB = parseFloat(b.getAttribute('data-score')) || 0.0;
                    return evB - evA;
                }} else {{
                    let res = valA.localeCompare(valB);
                    if (res !== 0) return newDesc ? -res : res;
                    let evA = parseFloat(a.getAttribute('data-score')) || 0.0;
                    let evB = parseFloat(b.getAttribute('data-score')) || 0.0;
                    return evB - evA;
                }}
            }});

            rows.forEach(r => tbody.appendChild(r));
        }}

        function filterTF(tf) {{
            let btns = document.querySelectorAll('.tf-btn');
            btns.forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');

            let rows = document.querySelectorAll('.tf-row');
            rows.forEach(r => {{
                if(tf === 'ALL' || r.getAttribute('data-tf') === tf) {{
                    r.style.display = '';
                }} else {{
                    r.style.display = 'none';
                }}
            }});
        }}

        // ================= TRADES JOURNAL SCRIPT =================
        let allTrades = {json_trades};
        let trFilters = {{
            basket: 'kings',
            tf: 'ALL',
            dir: 'ALL',
            outcome: 'ALL',
            search: '',
            page: 1,
            pageSize: 50
        }};

        function setTrFilter(key, val, btnElem) {{
            trFilters[key] = val;
            trFilters.page = 1;
            if (btnElem && btnElem.parentElement) {{
                btnElem.parentElement.querySelectorAll('button').forEach(b => {{
                    b.classList.remove('active');
                    b.style.background = '#1e293b';
                    b.style.color = '#94a3b8';
                }});
                btnElem.classList.add('active');
                btnElem.style.background = '#0284c7';
                btnElem.style.color = '#ffffff';
            }}
            renderTrades();
        }}

        function onTrSearch(val) {{
            trFilters.search = val.trim().toLowerCase();
            trFilters.page = 1;
            renderTrades();
        }}

        function changeTrPageSize(sz) {{
            trFilters.pageSize = parseInt(sz) || 50;
            trFilters.page = 1;
            renderTrades();
        }}

        function prevTrPage() {{
            if (trFilters.page > 1) {{
                trFilters.page--;
                renderTrades();
            }}
        }}

        function nextTrPage() {{
            let list = getFilteredTrades();
            let maxPage = Math.ceil(list.length / trFilters.pageSize) || 1;
            if (trFilters.page < maxPage) {{
                trFilters.page++;
                renderTrades();
            }}
        }}

        function getFilteredTrades() {{
            return allTrades.filter(t => {{
                if (trFilters.basket === 'kings' && !t.is_k) return false;
                if (trFilters.tf !== 'ALL' && t.tf !== trFilters.tf) return false;
                if (trFilters.dir !== 'ALL' && t.dir !== trFilters.dir) return false;
                if (trFilters.outcome === 'TP4' && t.t4 !== 1) return false;
                if (trFilters.outcome === 'TP2_PLUS' && t.t2 !== 1) return false;
                if (trFilters.outcome === 'TP1_PLUS' && t.t1 !== 1) return false;
                if (trFilters.outcome === 'LOSS' && t.t1 === 1) return false;
                if (trFilters.search) {{
                    let s = trFilters.search;
                    let hay = (t.role + ' ' + t.bname + ' ' + t.en_t + ' ' + t.ex_t).toLowerCase();
                    if (!hay.includes(s)) return false;
                }}
                return true;
            }});
        }}

        function renderTrades() {{
            let list = getFilteredTrades();
            let total = list.length;
            let pageSize = trFilters.pageSize;
            let totalPages = Math.ceil(total / pageSize) || 1;
            if (trFilters.page > totalPages) trFilters.page = totalPages;
            let curPage = trFilters.page;

            let startIdx = (curPage - 1) * pageSize;
            let endIdx = Math.min(startIdx + pageSize, total);
            let pageTrades = list.slice(startIdx, endIdx);

            let sumNet = 0;
            let cntWin1 = 0;
            let cntWin4 = 0;
            let cntLoss = 0;
            for (let i = 0; i < total; i++) {{
                let tr = list[i];
                sumNet += tr.net;
                if (tr.t1 === 1) cntWin1++;
                else cntLoss++;
                if (tr.t4 === 1) cntWin4++;
            }}

            let kpiCount = document.getElementById('trKpiCount');
            let kpiNet = document.getElementById('trKpiNet');
            let kpiWin1 = document.getElementById('trKpiWin1');
            let kpiWin4 = document.getElementById('trKpiWin4');
            let kpiLoss = document.getElementById('trKpiLoss');

            if (kpiCount) kpiCount.textContent = total.toLocaleString() + ' معامله';
            if (kpiNet) {{
                let sign = sumNet >= 0 ? '+' : '';
                kpiNet.textContent = '$' + sign + sumNet.toFixed(2);
                kpiNet.style.color = sumNet >= 0 ? '#34d399' : '#f87171';
            }}
            if (kpiWin1) {{
                let p1 = total > 0 ? ((cntWin1 / total) * 100).toFixed(1) : '0.0';
                kpiWin1.textContent = p1 + '٪ (' + cntWin1 + ')';
            }}
            if (kpiWin4) {{
                let p4 = total > 0 ? ((cntWin4 / total) * 100).toFixed(1) : '0.0';
                kpiWin4.textContent = p4 + '٪ (' + cntWin4 + ')';
            }}
            if (kpiLoss) {{
                let pL = total > 0 ? ((cntLoss / total) * 100).toFixed(1) : '0.0';
                kpiLoss.textContent = pL + '٪ (' + cntLoss + ')';
            }}

            let tbody = document.getElementById('tradesTableBody');
            if (!tbody) return;

            let rowsHtml = '';
            for (let i = 0; i < pageTrades.length; i++) {{
                let t = pageTrades[i];
                let rowNum = startIdx + i + 1;
                let dirBadge = t.dir === 'BUY' 
                    ? '<span style="background:#064e3b;color:#34d399;padding:2px 8px;border-radius:4px;font-weight:bold;">BUY 🟢</span>' 
                    : '<span style="background:#450a0a;color:#f87171;padding:2px 8px;border-radius:4px;font-weight:bold;">SELL 🔴</span>';
                
                let kingBadge = t.is_k 
                    ? '<span style="background:#854d0e;color:#fef08a;font-size:10px;padding:1px 6px;border-radius:4px;margin-right:4px;">👑 سلطان</span>' 
                    : '';

                let tfBadge = '<span style="background:#1e293b;color:#93c5fd;font-weight:bold;padding:2px 6px;border-radius:4px;">' + t.tf + '</span>';

                function tpPill(val, hit, label, col) {{
                    let border = hit ? 'border:1px solid ' + col + ';' : 'opacity:0.35;';
                    let check = hit ? ' <b style="color:' + col + ';">✓</b>' : '';
                    let bg = hit ? 'background:#0f172a;' : 'background:transparent;';
                    return '<div style="' + bg + 'padding:2px 6px;border-radius:4px;font-family:monospace;font-size:11px;' + border + '">' +
                           '<span style="color:' + col + ';font-size:9.5px;display:block;">' + label + '</span>' +
                           val.toFixed(5) + check + '</div>';
                }}

                let tp1Html = tpPill(t.tp1, t.t1 === 1, 'TP1 (1:1)', '#fbbf24');
                let tp2Html = tpPill(t.tp2, t.t2 === 1, 'TP2 (1:2)', '#60a5fa');
                let tp3Html = tpPill(t.tp3, t.t3 === 1, 'TP3 (1:3)', '#38bdf8');
                let tp4Html = tpPill(t.tp4, t.t4 === 1, 'TP4 (1:4)', '#c084fc');

                let exitDesc = '';
                if (t.t4 === 1) {{
                    exitDesc = '<span style="background:#3b0764;color:#e9d5ff;padding:3px 8px;border-radius:4px;border:1px solid #a855f7;font-weight:bold;">💎 تارگت ۴ (فول تارگت)</span>';
                }} else if (t.t3 === 1) {{
                    exitDesc = '<span style="background:#075985;color:#bae6fd;padding:3px 8px;border-radius:4px;border:1px solid #0284c7;">🎯 خروج تا پله ۳ (SL+2)</span>';
                }} else if (t.t2 === 1) {{
                    exitDesc = '<span style="background:#1e3a8a;color:#bfdbfe;padding:3px 8px;border-radius:4px;border:1px solid #3b82f6;">🎯 خروج تا پله ۲ (SL+1)</span>';
                }} else if (t.t1 === 1) {{
                    exitDesc = '<span style="background:#854d0e;color:#fef08a;padding:3px 8px;border-radius:4px;border:1px solid #eab308;">🛡️ خروج پله ۱ + BE</span>';
                }} else {{
                    exitDesc = '<span style="background:#450a0a;color:#fca5a5;padding:3px 8px;border-radius:4px;border:1px solid #dc2626;">🛑 حد زیان اولیه (SL)</span>';
                }}

                let netColor = t.net >= 0 ? '#34d399' : '#f87171';
                let netBg = t.net >= 0 ? '#064e3b33' : '#450a0a33';
                let netSign = t.net >= 0 ? '+' : '';
                let netHtml = '<span style="background:' + netBg + ';color:' + netColor + ';padding:3px 10px;border-radius:4px;font-weight:bold;font-family:monospace;font-size:12.5px;">$' + netSign + t.net.toFixed(2) + '</span>';

                let rowBg = i % 2 === 0 ? 'background:#081c30;' : 'background:#0a233c;';

                rowsHtml += '<tr style="' + rowBg + 'border-bottom:1px solid #133352;text-align:center;">' +
                    '<td style="padding:8px 6px;color:#64748b;font-size:11px;">' + rowNum + '</td>' +
                    '<td style="padding:8px 6px;font-size:11px;direction:ltr;font-family:monospace;color:#94a3b8;">' +
                        '<div>🟢 ' + t.en_t + '</div>' +
                        '<div style="color:#64748b;font-size:10px;">🔴 ' + t.ex_t + '</div>' +
                    '</td>' +
                    '<td style="padding:8px 6px;">' + tfBadge + '</td>' +
                    '<td style="padding:8px 10px;text-align:right;">' +
                        '<div>' + kingBadge + '<b style="color:#e2e8f0;font-size:12.5px;">' + t.role + '</b></div>' +
                        '<div style="color:#94a3b8;font-size:10.5px;margin-top:2px;">' + t.bname + '</div>' +
                    '</td>' +
                    '<td style="padding:8px 6px;">' + dirBadge + '</td>' +
                    '<td style="padding:8px 6px;font-family:monospace;color:#e2e8f0;">' + t.en_p.toFixed(5) + '</td>' +
                    '<td style="padding:8px 6px;font-family:monospace;color:#fca5a5;background:#2d121733;">' + t.sl.toFixed(5) + '</td>' +
                    '<td style="padding:8px 6px;">' + tp1Html + '</td>' +
                    '<td style="padding:8px 6px;">' + tp2Html + '</td>' +
                    '<td style="padding:8px 6px;">' + tp3Html + '</td>' +
                    '<td style="padding:8px 6px;">' + tp4Html + '</td>' +
                    '<td style="padding:8px 8px;">' + exitDesc + '</td>' +
                    '<td style="padding:8px 10px;">' + netHtml + '</td>' +
                '</tr>';
            }}

            tbody.innerHTML = rowsHtml;

            let pInfo = document.getElementById('trPaginationInfo');
            let pCur = document.getElementById('trPageCurrent');
            let btnP = document.getElementById('trBtnPrev');
            let btnN = document.getElementById('trBtnNext');

            if (pInfo) {{
                if (total === 0) {{
                    pInfo.textContent = 'هیچ معامله‌ای با این فیلترها یافت نشد.';
                }} else {{
                    pInfo.textContent = 'نمایش ' + (startIdx + 1) + ' تا ' + endIdx + ' از مجموع ' + total.toLocaleString() + ' معامله';
                }}
            }}
            if (pCur) pCur.textContent = 'صفحه ' + curPage + ' از ' + totalPages;
            if (btnP) btnP.disabled = (curPage <= 1);
            if (btnN) btnN.disabled = (curPage >= totalPages);
        }}

        // Initial render of trades journal and simulator
        setTimeout(() => {{
            initEquityCanvasEvents();
            initSimUI();
            renderTrades();
        }}, 60);
    </script>
        </main>
    </div>

    <!-- 💾 SAVE PRESET MODAL DIALOG -->
    <div id="savePresetModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:999999;align-items:center;justify-content:center;backdrop-filter:blur(5px);direction:rtl;">
        <div style="background:#0f172a;border:2px solid #38bdf8;border-radius:14px;padding:22px;width:90%;max-width:540px;box-shadow:0 15px 35px rgba(0,0,0,0.9);color:#f1f5f9;">
            <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #334155;padding-bottom:12px;margin-bottom:16px;">
                <h3 style="margin:0;color:#38bdf8;font-size:18px;display:flex;align-items:center;gap:8px;">
                    <span>💾 ذخیره ترکیب فعلی فیلترها به عنوان سناریو</span>
                </h3>
                <button onclick="closeSavePresetModal()" style="background:none;border:none;color:#94a3b8;font-size:20px;cursor:pointer;">✖</button>
            </div>
            
            <div style="background:#081420;border:1px solid #1e3a5f;border-radius:8px;padding:12px;margin-bottom:16px;font-size:12px;">
                <div style="font-weight:bold;color:#facc15;margin-bottom:8px;">📊 پیش‌نمایش عملکرد فیلترهای فعلی شما:</div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;color:#cbd5e1;">
                    <div>💰 کف سود: <b id="modalPreviewMinProfit" style="color:#34d399;">-</b></div>
                    <div>⏰ ساعات معاملاتی: <b id="modalPreviewHours" style="color:#38bdf8;">-</b></div>
                    <div>👑 سلاطین فعال: <b id="modalPreviewKings" style="color:#facc15;">-</b></div>
                    <div>📊 تعداد معامله: <b id="modalPreviewTrades" style="color:#f1f5f9;">-</b></div>
                    <div>🎯 وین‌ریت: <b id="modalPreviewWR" style="color:#34d399;">-</b></div>
                    <div>⚖️ پرافیت فاکتور: <b id="modalPreviewPF" style="color:#38bdf8;">-</b></div>
                    <div>⚡ میانگین سود هر ترید: <b id="modalPreviewAvg" style="color:#c084fc;">-</b></div>
                    <div>🛡️ حداکثر افت سرمایه: <b id="modalPreviewDD" style="color:#fca5a5;">-</b></div>
                    <div style="grid-column:span 2;background:#064e3b22;padding:6px 10px;border-radius:6px;border:1px solid #065f46;">
                        💵 سود خالص کل: <b id="modalPreviewNet" style="color:#00e676;font-size:14px;">-</b>
                    </div>
                </div>
            </div>

            <div style="margin-bottom:14px;">
                <label style="display:block;font-size:12px;color:#94a3b8;margin-bottom:6px;">نام سناریو (الزامی):</label>
                <input id="modalPresetTitle" type="text" placeholder="مثال: استراتژی الماس من (PF 4.04 & WR 78%)" style="width:100%;box-sizing:border-box;background:#1e293b;border:1px solid #334155;color:#fff;padding:9px 12px;border-radius:6px;font-size:13px;font-family:inherit;" />
            </div>

            <div style="margin-bottom:20px;">
                <label style="display:block;font-size:12px;color:#94a3b8;margin-bottom:6px;">توضیحات و خلاصه استراتژی:</label>
                <input id="modalPresetDesc" type="text" placeholder="مثال: تارگت سود بالای ۳ دلار، بدون سلاطین پر استاپ، سشن نیویورک" style="width:100%;box-sizing:border-box;background:#1e293b;border:1px solid #334155;color:#fff;padding:9px 12px;border-radius:6px;font-size:12.5px;font-family:inherit;" />
            </div>

            <div style="display:flex;justify-content:flex-end;gap:10px;">
                <button onclick="closeSavePresetModal()" style="background:#1e293b;border:1px solid #475569;color:#cbd5e1;padding:8px 16px;border-radius:6px;font-size:12px;cursor:pointer;">انصراف</button>
                <button onclick="confirmSaveCurrentPreset()" style="background:linear-gradient(135deg, #0284c7, #0369a1);border:1px solid #38bdf8;color:#fff;padding:8px 20px;border-radius:6px;font-size:13px;font-weight:bold;cursor:pointer;box-shadow:0 2px 8px rgba(2,132,199,0.4);">✅ ذخیره سناریو</button>
            </div>
        </div>
    </div>
</body>
</html>
"""

    dyn_out_paths = [
        os.path.join(os.path.dirname(csv_file), f"{clean_symbol.lower()}_performance_report.html"),
        os.path.join(os.path.dirname(csv_file), "flagpro_performance_dashboard.html"),
        r"C:\Users\USER\Desktop\FlagPro_Dashboard.html"
    ]
    for out_path in dyn_out_paths:
        try:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, mode='w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ فایل با موفقیت نوشته شد: {out_path}")
        except Exception as e:
            print(f"❌ خطا در نوشتن {out_path}: {e}")

if __name__ == "__main__":
    build_dashboard()
