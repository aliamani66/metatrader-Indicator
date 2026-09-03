import os
import sys
import csv
from collections import defaultdict
from datetime import datetime

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

    # 7 Golden Kings
    kings_7_defs = [
        ('OInner-BE > RS-BU', '🥇', 'رتبه ۱'),
        ('OInner-BU > RS-BE', '🥈', 'رتبه ۲'),
        ('RS-BU', '🥉', 'رتبه ۳'),
        ('OInner-BU > RS-BU', '#4', 'رتبه ۴'),
        ('OInner-BU', '#5', 'رتبه ۵'),
        ('OInner-BE', '#6', 'رتبه ۶'),
        ('RS-BE', '#7', 'رتبه ۷')
    ]

    kings_trades = [r for r in closed if any(r.get('Role') == k[0] for k in kings_7_defs)]
    tot_k_cnt = len(kings_trades)
    friction_04_per_trade = 0.48
    tot_k_fric = tot_k_cnt * friction_04_per_trade

    kings_rows_html = []
    for role_name, rank_icon, rank_label in kings_7_defs:
        kt = [r for r in closed if r.get('Role') == role_name]
        cnt = len(kt)
        if cnt == 0:
            kings_rows_html.append(f"""
            <tr>
                <td style="text-align:center;font-size:16px;">{rank_icon}</td>
                <td style="color:#facc15;font-weight:bold;">{role_name}</td>
                <td style="text-align:center;color:#64748b;">۰</td>
                <td style="text-align:center;color:#64748b;">-</td>
                <td style="text-align:center;color:#64748b;">-</td>
                <td style="text-align:center;color:#64748b;">-</td>
                <td style="text-align:center;color:#64748b;">-</td>
                <td style="text-align:center;color:#64748b;">-</td>
                <td style="text-align:center;color:#64748b;">-</td>
                <td style="text-align:center;color:#64748b;">$0.00</td>
            </tr>
            """)
            continue

        w1 = len([r for r in kt if int(r.get('HitTargetRatio', 0)) >= 1])
        w2 = len([r for r in kt if int(r.get('HitTargetRatio', 0)) >= 2])
        sl = len([r for r in kt if int(r.get('HitTargetRatio', 0)) == 0])

        stops = [float(r.get('RiskPoints', 0.0)) / 10.0 for r in kt]
        min_sl = min(stops) if stops else 0.0
        max_sl = max(stops) if stops else 0.0
        avg_sl = sum(stops) / len(stops) if stops else 0.0

        k_gross = 0.0
        for r in kt:
            pts = float(r.get('RiskPoints', 0.0))
            hr = int(r.get('HitTargetRatio', 0))
            if hr == 0: k_gross -= pts * 0.04
            elif hr == 1: k_gross += pts * 0.02
            elif hr in [2, 3]: k_gross += (pts * 0.02) + (pts * 2 * 0.01)
            elif hr >= 4: k_gross += (pts * 0.02) + (pts * 2 * 0.01) + (pts * 4 * 0.01)

        k_fric = cnt * friction_04_per_trade
        k_net = k_gross - k_fric
        net_col = "#00e676" if k_net >= 0 else "#ef4444"

        kings_rows_html.append(f"""
        <tr>
            <td style="text-align:center;font-size:16px;">{rank_icon}</td>
            <td style="color:#facc15;font-weight:bold;font-size:14px;">{role_name}</td>
            <td style="text-align:center;font-weight:bold;">{cnt}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{w1/cnt*100:.1f}%</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{w2/cnt*100:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">{sl/cnt*100:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">{min_sl:.1f} پیپ <span style="font-size:11px;color:#bae6fd;">(${min_sl*0.40:.2f})</span></td>
            <td style="text-align:center;color:#f87171;font-weight:bold;">{max_sl:.1f} پیپ <span style="font-size:11px;color:#fca5a5;">(${max_sl*0.40:.2f})</span></td>
            <td style="text-align:center;color:#facc15;">{avg_sl:.1f} پیپ <span style="font-size:11px;color:#fef08a;">(${avg_sl*0.40:.2f})</span></td>
            <td style="text-align:center;color:{net_col};font-weight:bold;font-size:14px;">${k_net:+.2f} دلار</td>
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

    # Strategy 3: Multi-Stage Scale-Out (50% TP1 + BE, 25% TP2 + Lock, 25% TP4 Runner)
    s3_gross, s3_w, s3_l = 0.0, 0.0, 0.0
    for r in kings_trades:
        pts = float(r.get('RiskPoints', 0.0))
        hr = int(r.get('HitTargetRatio', 0))
        if hr == 0: loss = pts * 0.04; s3_gross -= loss; s3_l += loss
        elif hr == 1: win = pts * 0.02; s3_gross += win; s3_w += win
        elif hr in [2, 3]: win = (pts * 0.02) + (pts * 2 * 0.01); s3_gross += win; s3_w += win
        elif hr >= 4: win = (pts * 0.02) + (pts * 2 * 0.01) + (pts * 4 * 0.01); s3_gross += win; s3_w += win
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
        if hr == 0: m2_gross -= pts * 0.04
        elif hr == 1: m2_gross += (pts * 0.02) - (pts * 0.02)
        elif hr in [2, 3]: m2_gross += (pts * 0.02) + (pts * 2 * 0.01)
        elif hr >= 4: m2_gross += (pts * 0.02) + (pts * 2 * 0.01) + (pts * 4 * 0.01)
    m2_net = m2_gross - tot_k_fric
    be_diff = m1_net - m2_net

    # Timeframe Summary (M1, M5, M15)
    tf_map = defaultdict(list)
    for r in closed:
        tf_map[r.get('Timeframe', 'Unknown')].append(r)

    tf_summary_rows = []
    for tf_name in ['M1', 'M5', 'M15']:
        t_list = tf_map.get(tf_name, [])
        cnt = len(t_list)
        if cnt == 0: continue
        w1 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 1])
        w2 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 2])
        w3 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 3])
        w4 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 4])
        sl = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) == 0])

        tf_gross = 0.0
        for r in t_list:
            pts = float(r.get('RiskPoints', 0.0))
            hr = int(r.get('HitTargetRatio', 0))
            if hr == 0: tf_gross -= pts * 0.04
            elif hr == 1: tf_gross += pts * 0.02
            elif hr in [2, 3]: tf_gross += (pts * 0.02) + (pts * 2 * 0.01)
            elif hr >= 4: tf_gross += (pts * 0.02) + (pts * 2 * 0.01) + (pts * 4 * 0.01)
        tf_net = tf_gross - (cnt * friction_04_per_trade)
        col = "#00e676" if tf_net >= 0 else "#ef4444"

        tf_summary_rows.append(f"""
        <tr>
            <td style="color:#38bdf8;font-weight:bold;font-size:14px;">{tf_name}</td>
            <td style="text-align:center;font-weight:bold;">{cnt} معامله</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{w1/cnt*100:.1f}%</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{w2/cnt*100:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;">{w3/cnt*100:.1f}%</td>
            <td style="text-align:center;color:#c084fc;">{w4/cnt*100:.1f}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{sl/cnt*100:.1f}%</td>
            <td style="text-align:center;color:{col};font-weight:bold;font-size:15px;">${tf_net:+.2f} دلار</td>
        </tr>
        """)

    # Interactive Timeframe-Role Table
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
        ev_item = (w2_p / 100.0 * 2.0) - (sl_p / 100.0 * 1.0)
        computed_tf_roles.append({
            'tf': tf, 'role': role, 'cnt': cnt,
            'w1_p': w1_p, 'w2_p': w2_p, 'w3_p': w3_p, 'w4_p': w4_p, 'sl_p': sl_p,
            'ev_item': ev_item
        })

    # Sort by EV descending by default, breaking ties with trade count
    computed_tf_roles.sort(key=lambda x: (x['ev_item'], x['cnt']), reverse=True)

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
        ev_item = item['ev_item']
        ev_col = "#00e676" if ev_item >= 0.2 else ("#38bdf8" if ev_item >= 0 else "#ef4444")

        tf_role_rows.append(f"""
        <tr class="tf-row" data-tf="{tf}" data-role="{role}" data-cnt="{cnt}" data-w1="{w1_p:.2f}" data-w2="{w2_p:.2f}" data-w3="{w3_p:.2f}" data-w4="{w4_p:.2f}" data-sl="{sl_p:.2f}" data-ev="{ev_item:.3f}">
            <td style="color:#38bdf8;font-weight:bold;">{tf}</td>
            <td style="color:#facc15;font-weight:bold;">{role}</td>
            <td style="text-align:center;font-weight:bold;">{cnt}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{w1_p:.1f}%</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{w2_p:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;">{w3_p:.1f}%</td>
            <td style="text-align:center;color:#c084fc;">{w4_p:.1f}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{sl_p:.1f}%</td>
            <td style="text-align:center;color:{ev_col};font-weight:bold;font-size:14px;">{ev_item:+.2f} R</td>
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
            <button class="tab-btn active" onclick="openTab(event, 'tab-kings')">👑 سلاطین ۷ گانه</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-scaleout')">💎 خروج پلکانی و بریک‌ایون (0.04)</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-timeframes')">📊 عملکرد تایم‌فریم‌ها (M1/M5/M15)</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-filters')">🛡️ فیلترهای ضد استاپ و مقایسه</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-financials')">💰 حسابداری دلاری 0.01 لات</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-all-patterns')">🏆 رتبه‌بندی تمام الگوها</button>
            <button class="tab-btn" onclick="openTab(event, 'tab-loss-intel')">🔍 هوش باخت‌ها و استاپ‌ها</button>
        </div>

        <!-- ==================== TAB 1: 👑 GOLDEN KINGS ==================== -->
        <div id="tab-kings" class="tab-content active">
            <div class="section-box" style="border: 1px solid #eab308; background: #1a1608;">
                <div style="border-bottom: 1px solid #854d0e; padding-bottom: 14px; margin-bottom: 16px;">
                    <h3 style="margin:0;color:#facc15;font-size:19px;">👑 سلاطین استراتژی (۷ ساختار برتر در شرایط واقعی لایو با تایید ساختاری کامل)</h3>
                    <p style="margin:4px 0 0 0;color:#fef08a;font-size:12px;">کالبدشکافی ۱۰۰٪ پویا از رفتار {tot_k_cnt} معامله واقعی سلاطین برتر با حجم 0.04 لات:</p>
                </div>

                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#261e07;">
                                <th style="text-align:center;">رتبه</th>
                                <th>نام ساختار / تلاقی گره‌ها</th>
                                <th style="text-align:center;">تعداد معامله</th>
                                <th style="text-align:center;">وین‌ریت ۱:۱</th>
                                <th style="text-align:center;">وین‌ریت ۱:۲</th>
                                <th style="text-align:center;">نرخ باخت (SL)</th>
                                <th style="text-align:center;color:#38bdf8;">🟢 حداقل استاپ</th>
                                <th style="text-align:center;color:#f87171;">🔴 حداکثر استاپ</th>
                                <th style="text-align:center;color:#facc15;">میانگین استاپ</th>
                                <th style="text-align:center;color:#00e676;">💵 سود خالص دلاری (۰.۰۴ لات)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(kings_rows_html)}
                        </tbody>
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
                            <p style="margin:6px 0 0 0;color:#bae6fd;font-size:13px;">کالبدشکافی رفتار {tot_k_cnt} معامله واقعی سلاطین ۷ گانه با تایید قطعی پولبک، پرتاب و حجم <b>0.04 لات</b>:</p>
                        </div>
                        <div style="background:#0c4a6e;border:1px solid #0284c7;padding:8px 14px;border-radius:8px;font-size:12px;color:#7dd3fc;text-align:right;">
                            <div>💵 ارزش هر پیپ: <b>$0.40 دلار</b></div>
                            <div>🧾 کل اصطکاک پرداخت‌شده (کمیسیون+اسپرد): <b>${tot_k_fric:.2f} دلار</b></div>
                        </div>
                    </div>
                </div>

                <!-- Steps Breakdown Grid -->
                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:14px;margin-bottom:18px;">
                    <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                        <div style="color:#facc15;font-weight:bold;font-size:14px;">🎯 پله اول (TP 1:1) - خروج ۰.۰۲ لات (۵۰٪)</div>
                        <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">ذخیره ۵۰٪ سود معامله + <b>انتقال فوری استاپ لاس به نقطه ورود (ریسک‌فری سریع)</b></div>
                        <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">🛡️ نتیجه: ریسک کل معامله صفر شد و کمیسیون پوشش یافت!</div>
                    </div>
                    <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                        <div style="color:#facc15;font-weight:bold;font-size:14px;">🎯 پله دوم (TP 1:2) - خروج ۰.۰۱ لات (۲۵٪)</div>
                        <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">نقد کردن ۲۵٪ دیگر از حجم با سود ۲ برابری + <b>قفل سود در سطح TP1</b></div>
                        <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">📈 نتیجه: تثبیت سود عالی بدون هیچ‌گونه استرس روانی</div>
                    </div>
                    <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                        <div style="color:#facc15;font-weight:bold;font-size:14px;">🚀 پله سوم (TP 1:4) - خروج ۰.۰۱ لات (۲۵٪ رانر)</div>
                        <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">نگهداری ۲۵٪ باقیمانده بدون ریسک برای دوشیدن امواج بزرگ روندی</div>
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
                                <td style="color:#00e676;font-weight:bold;font-size:14px;">👑 ۳. خروج پلکانی شکار امواج تا TP4 (۰.۰۲ در TP1 + ریسک‌فری | ۰.۰۱ در TP2 | ۰.۰۱ در TP4) 🚀</td>
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
                    <h3 style="margin:0;color:#38bdf8;font-size:19px;">📊 جدول عملکرد جامع به تفکیک تایم‌فریم‌ها (M1, M5, M15)</h3>
                    <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">کالبدشکافی عملکرد معاملاتی و سودآوری خالص در هر یک از تایم‌فریم‌های فعال بازار:</p>
                </div>

                <!-- Timeframe Summary Table -->
                <div style="overflow-x:auto;margin-bottom:20px;">
                    <table>
                        <thead>
                            <tr style="background:#0f172a;">
                                <th>تایم‌فریم</th>
                                <th style="text-align:center;">تعداد کل معامله</th>
                                <th style="text-align:center;">وین‌ریت TP 1:1</th>
                                <th style="text-align:center;">وین‌ریت TP 1:2</th>
                                <th style="text-align:center;">وین‌ریت TP 1:3</th>
                                <th style="text-align:center;">وین‌ریت TP 1:4</th>
                                <th style="text-align:center;">نرخ باخت (SL)</th>
                                <th style="text-align:center;">💵 سود خالص دلاری (0.04)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(tf_summary_rows)}
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

                <!-- Quick Combined Sorting Buttons -->
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:12px 0;background:#0f172a;padding:8px 12px;border-radius:8px;border:1px solid #334155;">
                    <span style="color:#94a3b8;font-size:12px;font-weight:bold;">🔀 دکمه‌های سورت هوشمند و ترکیبی:</span>
                    <button class="sort-btn active" id="btnSortEV" onclick="sortTableByAttr('tfTable', 'data-ev', true, true, this)">🚀 بیشترین امید ریاضی (EV)</button>
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
                                <th onclick="sortTableByAttr('tfTable', 'data-ev', true, true)" data-sort="data-ev" style="cursor:pointer;text-align:center;color:#38bdf8;background:#1e293b;" title="مرتب‌سازی شده بر اساس امید ریاضی">امید ریاضی (EV) <span class="sort-icon">▼</span></th>
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
    </div>

    <script>
        function openTab(evt, tabId) {{
            let contents = document.querySelectorAll('.tab-content');
            contents.forEach(c => c.classList.remove('active'));

            let btns = document.querySelectorAll('.tab-btn');
            btns.forEach(b => b.classList.remove('active'));

            document.getElementById(tabId).classList.add('active');
            evt.currentTarget.classList.add('active');
        }}

        let sortDirections = {{ 'data-ev': true }};

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
                    let evA = parseFloat(a.getAttribute('data-ev')) || 0.0;
                    let evB = parseFloat(b.getAttribute('data-ev')) || 0.0;
                    return evB - evA;
                }} else {{
                    let res = valA.localeCompare(valB);
                    if (res !== 0) return newDesc ? -res : res;
                    let evA = parseFloat(a.getAttribute('data-ev')) || 0.0;
                    let evB = parseFloat(b.getAttribute('data-ev')) || 0.0;
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
