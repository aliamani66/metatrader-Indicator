import os
import sys
import csv
import math
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

def build_dashboard():
    csv_file = CSV_PATH_PRIMARY if os.path.exists(CSV_PATH_PRIMARY) else CSV_PATH_FALLBACK
    if not os.path.exists(csv_file):
        print(f"CSV not found: {csv_file}")
        return

    all_raw_rows = []
    with open(csv_file, mode='r', encoding='utf-8-sig', errors='ignore') as f:
        for r in csv.DictReader(f):
            all_raw_rows.append(r)

    rows = [r for r in all_raw_rows if r.get('Timeframe') in ['M1', 'M5', 'M15']]
    total_setups = len(rows)
    entered = [r for r in rows if r.get('Outcome') != 'Pending']
    closed = [r for r in entered if r.get('IsClosed') == 'True']
    in_trade = [r for r in entered if r.get('IsClosed') != 'True']

    dates = [r.get('BoxTimeStart') for r in rows if r.get('BoxTimeStart') and r.get('BoxTimeStart') != 'None']
    min_date = min(dates) if dates else 'نامشخص'
    max_date = max(dates) if dates else 'نامشخص'

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
    for tf_name in ['M1', 'M5', 'M15']:
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

    d_tot_kings = calc_tf_metrics(kings_trades)
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
    for tf_name in ['M1', 'M5', 'M15']:
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

    d_tot_raw = calc_tf_metrics(closed)
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
            background-color: #0b0f19;
            color: #f1f5f9;
            margin: 0;
            padding: 20px;
            direction: rtl;
        }}
        .container {{
            max-width: 1550px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            padding: 20px 24px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            color: #38bdf8;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 14px;
            margin-bottom: 20px;
        }}
        .kpi-card {{
            background: #1e293b;
            border: 1px solid #334155;
            padding: 14px 18px;
            border-radius: 10px;
            text-align: center;
        }}
        .kpi-title {{
            font-size: 12px;
            color: #94a3b8;
            margin-bottom: 6px;
        }}
        .kpi-value {{
            font-size: 24px;
            font-weight: bold;
            color: #f8fafc;
        }}
        .kpi-sub {{
            font-size: 11px;
            color: #64748b;
            margin-top: 4px;
        }}

        /* Modern Tabs Navigation */
        .tabs-nav {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            background: #1e293b;
            padding: 10px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid #334155;
        }}
        .tab-btn {{
            background: #0f172a;
            border: 1px solid #334155;
            color: #94a3b8;
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 13.5px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.25s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .tab-btn:hover {{
            color: #f8fafc;
            border-color: #38bdf8;
            background: #1e293b;
        }}
        .tab-btn.active {{
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            color: #ffffff;
            border-color: #38bdf8;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
        }}

        /* Tab Content Panel */
        .tab-content {{
            display: none;
            animation: fadeIn 0.25s ease;
        }}
        .tab-content.active {{
            display: block;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(6px); }}
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
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div>
                <h1>🎯 داشبورد جامع FlagPro - معماری تبولار (دسترسی بدون اسکرول)</h1>
                <p style="margin:6px 0 0 0;color:#94a3b8;font-size:13px;">
                    جفت‌ارز EURUSD | بازه داده‌ها: <b>{min_date}</b> تا <b>{max_date}</b> | تایم‌های فعال: <b>M1, M5, M15</b>
                </p>
            </div>
            <div style="text-align:left;">
                <span style="background:#0f172a;border:1px solid #334155;padding:6px 14px;border-radius:8px;font-size:12px;color:#38bdf8;">
                    🔄 همگام‌سازی زنده: {now_str}
                </span>
            </div>
        </div>

        <!-- KPI Cards Grid -->
        <div class="kpi-grid">
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

        <!-- 📑 TABS NAVIGATION BAR -->
        <div class="tabs-nav">
            <button class="tab-btn active" onclick="openTab(event, 'tab-kings')">👑 سلاطین ۱۸ گانه</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-equity')">📈 نمودار رشد و اکوئیتی</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-scaleout')">💎 خروج پلکانی و بریک‌ایون (0.04)</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-timeframes')">📊 عملکرد تایم‌فریم‌ها (M1/M5/M15)</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-weekly')">📅 کالبدشکافی هفته به هفته</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-filters')">🛡️ فیلترهای ضد استاپ و مقایسه</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-financials')">💰 حسابداری دلاری 0.01 لات</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-all-patterns')">🏆 رتبه‌بندی تمام الگوها</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-loss-intel')">🔍 هوش باخت‌ها و استاپ‌ها</button>
        </div>


        <!-- ==================== TAB: 📈 EQUITY & BALANCE CURVE ==================== -->
        <div id="tab-equity" class="tab-content">
            <!-- Equity Metrics Banner -->
            <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));margin-bottom:20px;">
                <div class="kpi-card" style="border-color:#38bdf8;">
                    <div class="kpi-title">💵 بالانس شروع حساب</div>
                    <div class="kpi-value" style="color:#f1f5f9;">${bal_initial:,.2f}</div>
                    <div class="kpi-sub">شروع از ۹ مارس ۲۰۲۶</div>
                </div>
                <div class="kpi-card" style="border-color:#00e676;">
                    <div class="kpi-title">📈 بالانس نهایی سلاطین</div>
                    <div class="kpi-value" style="color:#00e676;">${bal_k:,.2f}</div>
                    <div class="kpi-sub">سود خالص: ${net_k:+,.2f} ({net_k_pct:+.2f}٪)</div>
                </div>
                <div class="kpi-card" style="border-color:#facc15;">
                    <div class="kpi-title">🏔️ بالاترین سقف سرمایه (Peak)</div>
                    <div class="kpi-value" style="color:#facc15;">${peak_k:,.2f}</div>
                    <div class="kpi-sub">ثبت رکورد در پایان بازه ۶ ماهه</div>
                </div>
                <div class="kpi-card" style="border-color:#ef4444;">
                    <div class="kpi-title">🛡️ حداکثر افت حساب (Max Drawdown)</div>
                    <div class="kpi-value" style="color:#fca5a5;">${max_dd_k:.2f} ({max_dd_k_pct:.2f}٪)</div>
                    <div class="kpi-sub">مدیریت ریسک بی‌نقص در ۶ ماه!</div>
                </div>
            </div>

            <!-- Interactive Canvas Graph Container -->
            <div class="section-box" style="border:1px solid #38bdf8;background:#0b0f19;padding:20px;margin-bottom:24px;">
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e293b;padding-bottom:14px;margin-bottom:16px;flex-wrap:wrap;gap:12px;">
                    <div>
                        <h3 style="margin:0;color:#38bdf8;font-size:20px;display:flex;align-items:center;gap:8px;">
                            <span>📈 نمودار تعاملی رشد بالانس و اکوئیتی (MT5 Strategy Tester Graph)</span>
                        </h3>
                        <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">رسم دقیق منحنی رشد سرمایه معامله به معامله در طول زمان ۶ ماهه - موس را روی نمودار حرکت دهید تا جزئیات هر معامله را ببینید:</p>
                    </div>
                    <div style="display:flex;gap:8px;">
                        <button id="btnEqKings" class="sort-btn active" onclick="switchEquityMode('kings')">👑 منحنی سلاطین ۱۸ گانه ({len(pts_kings)-1} معامله)</button>
                        <button id="btnEqAll" class="sort-btn" onclick="switchEquityMode('all')">🌐 منحنی کل ساختارهای چارت ({len(pts_all)-1} معامله)</button>
                    </div>
                </div>

                <!-- Canvas Box -->
                <div style="position:relative;width:100%;height:480px;background:#0f172a;border:1px solid #1e293b;border-radius:10px;overflow:hidden;">
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
                        <span>بازه زمانی: <b style="color:#38bdf8;">۹ مارس ۲۰۲۶ تا ۳ سپتامبر ۲۰۲۶</b></span>
                    </div>
                </div>
            </div>

            <!-- Interactive Weekly P&L Bar Chart Container -->
            <div class="section-box" style="border:1px solid #10b981;background:#0b0f19;padding:20px;margin-bottom:24px;">
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e293b;padding-bottom:14px;margin-bottom:16px;flex-wrap:wrap;gap:12px;">
                    <div>
                        <h3 style="margin:0;color:#10b981;font-size:20px;display:flex;align-items:center;gap:8px;">
                            <span>📊 نمودار میله‌ای سود و زیان هفته به هفته (Weekly Net Profit & Loss)</span>
                        </h3>
                        <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">توزیع عملکرد دلاری ۲۶ هفته متوالی - میله‌های سبز نشان‌دهنده سوددهی هفتگی و میله‌های قرمز نشان‌دهنده هفته‌های اصلاحی هستند:</p>
                    </div>
                    <div style="display:flex;gap:8px;">
                        <button id="btnWkKings" class="sort-btn active" onclick="switchWeeklyBarMode('kings')">👑 سلاطین ۱۸ گانه</button>
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
                        <span>تعداد کل هفته‌ها: <b style="color:#f1f5f9;">۲۶ هفته</b></span>
                        <span>|</span>
                        <span>هفته‌های سودده: <b style="color:#00e676;">{tot_kings_green_wks} هفته ({tot_kings_green_wks/26.0*100:.1f}٪)</b></span>
                        <span>|</span>
                        <span>هفته‌های زیان‌ده: <b style="color:#ef4444;">{tot_kings_red_wks} هفته ({tot_kings_red_wks/26.0*100:.1f}٪)</b></span>
                    </div>
                </div>
            </div>

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
                                <td style="font-weight:bold;color:#facc15;">👑 سبد سلاطین ۱۸ گانه (گزینش هوشمند)</td>
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

        <!-- ==================== TAB 1: 👑 GOLDEN KINGS ==================== -->
        <div id="tab-kings" class="tab-content active">
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

        <!-- ==================== TAB 2: 💎 SCALE-OUT & BREAK-EVEN ==================== -->
        <div id="tab-scaleout" class="tab-content">
            <div class="section-box" style="border: 2px solid #38bdf8; background: #082136;">
                <div style="border-bottom: 1px solid #0284c7; padding-bottom: 14px; margin-bottom: 16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                        <div>
                            <h3 style="margin:0;color:#38bdf8;font-size:20px;">💎 سیستم خروج پلکانی با حجم عملیاتی 0.04 لات (با اعمال ۳ شرط لایو بازار)</h3>
                            <p style="margin:6px 0 0 0;color:#bae6fd;font-size:13px;">کالبدشکافی رفتار {tot_k_cnt} معامله واقعی سلاطین ۱۸ گانه با تایید قطعی پولبک، پرتاب و حجم <b>0.04 لات</b>:</p>
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
                <div style="border-bottom:1px solid #334155;padding-bottom:14px;margin-bottom:16px;">
                    <h3 style="margin:0;color:#38bdf8;font-size:19px;">📊 تفکیک عملکرد تایم‌فریم‌ها در استراتژی سلاطین ۱۸ گانه FlagPro</h3>
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
                        <div style="color:#cbd5e1;font-size:11px;margin-top:2px;">اگر کل ۲۰۸۴ باکس و نویز چارت بدون فیلتر معامله می‌شد، ۵۵۲- دلار زیان تولید می‌شد؛ اما سلاطین ۱۸ گانه با فیلتر هوشمند آن را به ۱۸۴+ دلار سود خالص رسانده‌اند!</div>
                    </div>
                    <button class="sort-btn" style="border-color:#a5b4fc;color:#a5b4fc;" onclick="let el = document.getElementById('rawTfTable'); el.style.display = el.style.display==='none'?'':'none';">👁️ مشاهده جدول کل دیتای خام چارت</button>
                </div>

                <!-- Hidden Comparative Raw Table -->
                <div id="rawTfTable" style="display:none;overflow-x:auto;margin-bottom:24px;border:1px dashed #475569;border-radius:8px;padding:10px;">
                    <div style="color:#94a3b8;font-size:12px;margin-bottom:6px;font-weight:bold;">⚠️ عملکرد کل ۲۰۸۴ معامله خام چارت بدون گزینش سلاطین (Raw Market Noise):</div>
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

        <!-- ==================== TAB 5: 💰 FINANCIAL ACCOUNTING (0.01 LOT) ==================== -->
        <div id="tab-financials" class="tab-content">
            <div class="section-box" style="border: 1px solid #10b981; background: #061e14;">
                <div style="border-bottom: 1px solid #065f46; padding-bottom: 14px; margin-bottom: 16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <h3 style="margin:0;color:#34d399;font-size:19px;">💰 صورت سود و زیان دلاری بر مبنای حجم ثابت 0.01 لات (حساب میکرو / استاندارد)</h3>
                        <p style="margin:4px 0 0 0;color:#a7f3d0;font-size:12px;">محاسبه اصطکاک معاملاتی: کمیسیون بروکر ($0.06) + اسپرد میانگین ($0.06) | کل هزینه هر ترید: <b>$0.12</b></p>
                    </div>
                    <div style="background:#022c22;border:1px solid #059669;padding:6px 14px;border-radius:8px;font-size:12px;color:#6ee7b7;">
                        💵 ارزش هر پیپ در 0.01 لات = $0.10 دلار
                    </div>
                </div>

                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#064e3b;">
                                <th>سناریوی معاملاتی با حجم 0.01 لات</th>
                                <th style="text-align:center;">سود ناخالص</th>
                                <th style="text-align:center;">کل کمیسیون بروکر</th>
                                <th style="text-align:center;">کل هزینه اسپرد</th>
                                <th style="text-align:center;">💵 سود خالص دلاری نهایی</th>
                                <th style="text-align:center;">ضریب سود (PF)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="font-weight:bold;color:#facc15;">تارگت اول: ریسک به ریوارد ۱:۱ (TP 1:1)</td>
                                <td style="text-align:center;color:#38bdf8;">${f01_gross_tp1:+.2f}</td>
                                <td style="text-align:center;color:#f87171;">${f01_comm:.2f}</td>
                                <td style="text-align:center;color:#f87171;">${f01_spread:.2f}</td>
                                <td style="text-align:center;color:{'#00e676' if f01_net_tp1 >= 0 else '#ef4444'};font-weight:bold;font-size:15px;">${f01_net_tp1:+.2f} دلار</td>
                                <td style="text-align:center;color:#cbd5e1;font-weight:bold;">{f01_pf_tp1:.2f}</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#facc15;">تارگت دوم: ریسک به ریوارد ۱:۲ (TP 1:2)</td>
                                <td style="text-align:center;color:#38bdf8;">${f01_gross_tp2:+.2f}</td>
                                <td style="text-align:center;color:#f87171;">${f01_comm:.2f}</td>
                                <td style="text-align:center;color:#f87171;">${f01_spread:.2f}</td>
                                <td style="text-align:center;color:{'#00e676' if f01_net_tp2 >= 0 else '#ef4444'};font-weight:bold;font-size:15px;">${f01_net_tp2:+.2f} دلار</td>
                                <td style="text-align:center;color:#cbd5e1;font-weight:bold;">{f01_pf_tp2:.2f}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ==================== TAB 6: 🏆 ALL PATTERNS MASTER TABLE ==================== -->
        <div id="tab-all-patterns" class="tab-content">
            <div class="section-box">
                <h3 style="margin:0 0 16px 0;color:#38bdf8;font-size:18px;">🏆 جدول رتبه‌بندی جامع استراتژی‌ها و باکس‌ها (مرتب‌شده بر اساس تعداد معامله)</h3>
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>الگو / ساختار</th>
                                <th style="text-align:center;">تعداد</th>
                                <th style="text-align:center;">TP1 (1:1)</th>
                                <th style="text-align:center;">TP2 (1:2)</th>
                                <th style="text-align:center;">TP3 (1:3)</th>
                                <th style="text-align:center;">TP4 (1:4)</th>
                                <th style="text-align:center;">استاپ (SL)</th>
                                <th style="text-align:center;">سود خالص دلاری (0.04)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(all_patterns_rows)}
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
                        <h3 style="margin:0;color:#34d399;font-size:19px;">📅 کارنامه کامل هفته به هفته (Master 26-Week Timeline)</h3>
                        <p style="margin:4px 0 0 0;color:#a7f3d0;font-size:12px;">کالبدشکافی پیوسته تمام ۲۶ هفته از آغاز مارس تا کنون با تفکیک برد، استاپ و برترین سلطان هفته:</p>
                    </div>
                    <div style="display:flex;gap:8px;">
                        <button id="btnWkKings" class="sort-btn active" onclick="filterWeeklyMode('kings')">👑 فقط سلاطین ۱۸ گانه</button>
                        <button id="btnWkAll" class="sort-btn" onclick="filterWeeklyMode('all')">🌐 کل ساختارهای چارت</button>
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

        function initWeeklyBarCanvasEvents() {{
            let canvas = document.getElementById('weeklyBarCanvas');
            if (!canvas) return;

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

        let currentEquityMode = 'kings';
        let dataKings = {json_pts_kings};
        let dataAll = {json_pts_all};

        function switchEquityMode(mode) {{
            currentEquityMode = mode;
            let btnK = document.getElementById('btnEqKings');
            let btnA = document.getElementById('btnEqAll');
            let lbl = document.getElementById('lblEqPts');
            if(mode === 'kings') {{
                if(btnK) btnK.classList.add('active');
                if(btnA) btnA.classList.remove('active');
                if(lbl) lbl.textContent = dataKings.length - 1;
            }} else {{
                if(btnK) btnK.classList.remove('active');
                if(btnA) btnA.classList.add('active');
                if(lbl) lbl.textContent = dataAll.length - 1;
            }}
            drawEquityChart(mode);
        }}

        function drawEquityChart(mode) {{
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

            let pts = (mode === 'kings') ? dataKings : dataAll;
            if (!pts || pts.length === 0) return;

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
            if (mode === 'kings') {{
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
            ctx.strokeStyle = (mode === 'kings') ? '#38bdf8' : '#a855f7';
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
            if (!canvas) return;

            canvas.addEventListener('mousemove', function(evt) {{
                if (!canvas._coords) return;
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

                drawEquityChart(currentEquityMode);
                    initWeeklyBarCanvasEvents();
                    drawWeeklyBarChart(currentWeeklyBarMode);
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
                drawEquityChart(currentEquityMode);
                    initWeeklyBarCanvasEvents();
                    drawWeeklyBarChart(currentWeeklyBarMode);
            }});

            window.addEventListener('resize', function() {{
                drawEquityChart(currentEquityMode);
                    initWeeklyBarCanvasEvents();
                    drawWeeklyBarChart(currentWeeklyBarMode);
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
            let btnKings = document.getElementById('btnWkKings');
            let btnAll = document.getElementById('btnWkAll');
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
                    drawEquityChart(currentEquityMode);
                    initWeeklyBarCanvasEvents();
                    drawWeeklyBarChart(currentWeeklyBarMode);
                }}, 50);
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
    </script>
</body>
</html>
"""

    for out_path in OUT_PATHS:
        try:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, mode='w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ فایل با موفقیت نوشته شد: {out_path}")
        except Exception as e:
            print(f"❌ خطا در نوشتن {out_path}: {e}")

if __name__ == "__main__":
    build_dashboard()
