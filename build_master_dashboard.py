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
        print(f"❌ هیچ فایل CSV معتبری یافت نشد: {csv_file}")
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

    # Date range extraction
    dates = [r.get('BoxTimeStart') for r in rows if r.get('BoxTimeStart') and r.get('BoxTimeStart') != 'None']
    min_date = min(dates) if dates else 'نامشخص'
    max_date = max(dates) if dates else 'نامشخص'

    # Filter evaluation
    accepted_trades = []
    rejected_trades = []

    for r in closed:
        role = r.get('Role', '')
        entry_time = r.get('EntryTime', '')
        rejected = False

        if is_single_ls(role) or is_night_session(entry_time) or is_pre_london(entry_time) or            is_toxic_pattern(role) or is_pure_flag(role) or            is_low_reward_vs_friction(float(r.get('RiskPoints', 0.0))):
            rejected = True

        if rejected:
            rejected_trades.append(r)
        else:
            accepted_trades.append(r)

    # Basic win rates
    w1_cnt_b = len([r for r in closed if int(r.get('HitTargetRatio', 0)) >= 1])
    w2_cnt_b = len([r for r in closed if int(r.get('HitTargetRatio', 0)) >= 2])
    sl_cnt_b = len([r for r in closed if int(r.get('HitTargetRatio', 0)) == 0])
    w1_rate_b = w1_cnt_b / len(closed) * 100 if closed else 0
    w2_rate_b = w2_cnt_b / len(closed) * 100 if closed else 0
    sl_rate_b = sl_cnt_b / len(closed) * 100 if closed else 0
    ev_b = (w2_rate_b / 100.0 * 2.0) - (sl_rate_b / 100.0 * 1.0)

    w1_cnt_a = len([r for r in accepted_trades if int(r.get('HitTargetRatio', 0)) >= 1])
    w2_cnt_a = len([r for r in accepted_trades if int(r.get('HitTargetRatio', 0)) >= 2])
    sl_cnt_a = len([r for r in accepted_trades if int(r.get('HitTargetRatio', 0)) == 0])
    w1_rate_a = w1_cnt_a / len(accepted_trades) * 100 if accepted_trades else 0
    w2_rate_a = w2_cnt_a / len(accepted_trades) * 100 if accepted_trades else 0
    sl_rate_a = sl_cnt_a / len(accepted_trades) * 100 if accepted_trades else 0
    ev_a = (w2_rate_a / 100.0 * 2.0) - (sl_rate_a / 100.0 * 1.0)

    sl_in_rej = len([r for r in rejected_trades if int(r.get('HitTargetRatio', 0)) == 0])
    rej_accuracy = sl_in_rej / len(rejected_trades) * 100 if rejected_trades else 0

    # Kings 7 Dynamic Extraction
    kings_7_defs = [
        ('OInner-BE > RS-BU', '🥇', 'رتبه اول: تلاقی او‌اینر نزولی به آر‌اس صعودی'),
        ('OInner-BU > RS-BE', '🥈', 'رتبه دوم: تلاقی او‌اینر صعودی به آر‌اس نزولی'),
        ('RS-BU', '🥉', 'رتبه سوم: آر‌اس صعودی مستقیم'),
        ('OInner-BU > RS-BU', '#4', 'رتبه چهارم: تلاقی او‌اینر صعودی به آر‌اس صعودی'),
        ('OInner-BU', '#5', 'رتبه پنجم: او‌اینر صعودی کلاسیک'),
        ('OInner-BE', '#6', 'رتبه ششم: او‌اینر نزولی کلاسیک'),
        ('RS-BE', '#7', 'رتبه هفتم: آر‌اس نزولی مستقیم')
    ]

    kings_rows_html = []
    tot_kings_trades = 0
    tot_kings_gross = 0.0
    tot_kings_friction = 0.0
    tot_kings_net = 0.0

    friction_04_per_trade = 0.48

    for role_name, rank_icon, role_desc in kings_7_defs:
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

        tot_kings_trades += cnt
        w1 = len([r for r in kt if int(r.get('HitTargetRatio', 0)) >= 1])
        w2 = len([r for r in kt if int(r.get('HitTargetRatio', 0)) >= 2])
        sl = len([r for r in kt if int(r.get('HitTargetRatio', 0)) == 0])

        stops = [float(r.get('RiskPoints', 0.0)) / 10.0 for r in kt]
        min_sl = min(stops) if stops else 0.0
        max_sl = max(stops) if stops else 0.0
        avg_sl = sum(stops) / len(stops) if stops else 0.0

        # PnL with 0.04 Scale-Out (50% TP1, 25% TP2, 25% TP4)
        k_gross = 0.0
        for r in kt:
            pts = float(r.get('RiskPoints', 0.0))
            hr = int(r.get('HitTargetRatio', 0))
            if hr == 0:
                k_gross -= pts * 0.04
            elif hr == 1:
                k_gross += pts * 0.02
            elif hr in [2, 3]:
                k_gross += (pts * 0.02) + (pts * 2 * 0.01)
            elif hr >= 4:
                k_gross += (pts * 0.02) + (pts * 2 * 0.01) + (pts * 4 * 0.01)

        k_fric = cnt * friction_04_per_trade
        k_net = k_gross - k_fric
        tot_kings_gross += k_gross
        tot_kings_friction += k_fric
        tot_kings_net += k_net

        net_color = "#00e676" if k_net >= 0 else "#ef4444"

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
            <td style="text-align:center;color:{net_color};font-weight:bold;font-size:14px;">${k_net:+.2f} دلار</td>
        </tr>
        """)

    # 3-Way Scale-Out Comparison on Kings
    kings_all_trades = [r for r in closed if any(r.get('Role') == k[0] for k in kings_7_defs)]
    tot_k_cnt = len(kings_all_trades)

    # Strategy 1: Fixed TP 1:1
    s1_gross = 0.0
    s1_wins = 0.0
    s1_losses = 0.0
    for r in kings_all_trades:
        pts = float(r.get('RiskPoints', 0.0))
        hr = int(r.get('HitTargetRatio', 0))
        if hr >= 1:
            win = pts * 0.04
            s1_gross += win
            s1_wins += win
        else:
            loss = pts * 0.04
            s1_gross -= loss
            s1_losses += loss
    s1_fric = tot_k_cnt * friction_04_per_trade
    s1_net = s1_gross - s1_fric
    s1_pf = s1_wins / s1_losses if s1_losses > 0 else 0.0

    # Strategy 2: Fixed TP 1:2
    s2_gross = 0.0
    s2_wins = 0.0
    s2_losses = 0.0
    for r in kings_all_trades:
        pts = float(r.get('RiskPoints', 0.0))
        hr = int(r.get('HitTargetRatio', 0))
        if hr >= 2:
            win = pts * 2 * 0.04
            s2_gross += win
            s2_wins += win
        else:
            loss = pts * 0.04
            s2_gross -= loss
            s2_losses += loss
    s2_fric = tot_k_cnt * friction_04_per_trade
    s2_net = s2_gross - s2_fric
    s2_pf = s2_wins / s2_losses if s2_losses > 0 else 0.0

    # Strategy 3: Dynamic Multi-Stage Scale-Out (50% TP1 + BE, 25% TP2 + Lock, 25% TP4 Runner)
    s3_wins = 0.0
    s3_losses = 0.0
    for r in kings_all_trades:
        pts = float(r.get('RiskPoints', 0.0))
        hr = int(r.get('HitTargetRatio', 0))
        if hr == 0:
            loss = pts * 0.04
            s3_losses += loss
        elif hr == 1:
            win = pts * 0.02
            s3_wins += win
        elif hr in [2, 3]:
            win = (pts * 0.02) + (pts * 2 * 0.01)
            s3_wins += win
        elif hr >= 4:
            win = (pts * 0.02) + (pts * 2 * 0.01) + (pts * 4 * 0.01)
            s3_wins += win
    s3_pf = s3_wins / s3_losses if s3_losses > 0 else 0.0

    # Master Table: All Patterns Breakdown
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

    # Timeframes Breakdown
    tf_map = defaultdict(list)
    for r in closed:
        tf_map[r.get('Timeframe', 'Unknown')].append(r)

    tf_rows = []
    for tf_name in ['M1', 'M5', 'M15']:
        t_list = tf_map.get(tf_name, [])
        cnt = len(t_list)
        if cnt == 0: continue
        w1 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 1])
        w2 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 2])
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

        tf_rows.append(f"""
        <tr>
            <td style="color:#38bdf8;font-weight:bold;font-size:14px;">{tf_name}</td>
            <td style="text-align:center;font-weight:bold;">{cnt}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{w1/cnt*100:.1f}%</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{w2/cnt*100:.1f}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{sl/cnt*100:.1f}%</td>
            <td style="text-align:center;color:{col};font-weight:bold;font-size:14px;">${tf_net:+.2f} دلار</td>
        </tr>
        """)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>داشبورد جامع و هوشمند FlagPro - تحلیل کامل معاملات</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            background-color: #0b0f19;
            color: #f1f5f9;
            margin: 0;
            padding: 24px;
            direction: rtl;
        }}
        .container {{
            max-width: 1500px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 24px;
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
            gap: 16px;
            margin-bottom: 24px;
        }}
        .kpi-card {{
            background: #1e293b;
            border: 1px solid #334155;
            padding: 18px;
            border-radius: 10px;
            text-align: center;
        }}
        .kpi-title {{
            font-size: 13px;
            color: #94a3b8;
            margin-bottom: 8px;
        }}
        .kpi-value {{
            font-size: 26px;
            font-weight: bold;
            color: #f8fafc;
        }}
        .kpi-sub {{
            font-size: 11px;
            color: #64748b;
            margin-top: 4px;
        }}
        .section-box {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
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
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div>
                <h1>🎯 داشبورد جامع و هوشمند FlagPro - تحلیل کامل معاملات</h1>
                <p style="margin:6px 0 0 0;color:#94a3b8;font-size:13px;">
                    جفت‌ارز EURUSD | بازه تحت پوشش: <b>{min_date}</b> تا <b>{max_date}</b> | تایم‌های فعال: <b>M1, M5, M15</b>
                </p>
            </div>
            <div style="text-align:left;">
                <span style="background:#0f172a;border:1px solid #334155;padding:6px 14px;border-radius:8px;font-size:12px;color:#38bdf8;">
                    🔄 تاریخ بازتولید فایل: {now_str}
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
                <div class="kpi-title">🛡️ استاپ‌های فیلترشده</div>
                <div class="kpi-value" style="color:#f59e0b;">{sl_in_rej} 🎯</div>
                <div class="kpi-sub">دقت فیلتر در شناسایی باخت: {rej_accuracy:.1f}%</div>
            </div>
            <div class="kpi-card" style="border-top: 4px solid #10b981;">
                <div class="kpi-title">🚀 امید ریاضی پس از فیلتر</div>
                <div class="kpi-value" style="color:#10b981;">{ev_a:+.2f} R</div>
                <div class="kpi-sub">امید ریاضی قبل از فیلتر: {ev_b:+.2f} R</div>
            </div>
            <div class="kpi-card" style="border-top: 4px solid #eab308;">
                <div class="kpi-title">💵 سود خالص دلاری سلاطین (0.04)</div>
                <div class="kpi-value" style="color:#facc15;">${tot_kings_net:+.2f}</div>
                <div class="kpi-sub">از {tot_k_cnt} معامله سلاطین برتر</div>
            </div>
        </div>

        <!-- 👑 THE 7 GOLDEN KINGS TABLE -->
        <div class="section-box" style="border: 1px solid #eab308; background: #1a1608;">
            <div style="border-bottom: 1px solid #854d0e; padding-bottom: 14px; margin-bottom: 16px;">
                <h3 style="margin:0;color:#facc15;font-size:19px;">👑 سلاطین استراتژی (۷ ساختار برتر استخراج‌شده مستقیماً از فایل داده‌ها)</h3>
                <p style="margin:4px 0 0 0;color:#fef08a;font-size:12px;">کالبدشکافی کامل و ۱۰۰٪ پویا از رفتار ۷ ساختار برتر در این بازه با حجم 0.04 لات:</p>
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

        <!-- 💎 SPECIAL SECTION: REALISTIC SCALE-OUT COMPARISON -->
        <div class="section-box" style="border: 2px solid #38bdf8; background: #082136;">
            <div style="border-bottom: 1px solid #0284c7; padding-bottom: 14px; margin-bottom: 16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <h3 style="margin:0;color:#38bdf8;font-size:20px;">💎 مقایسه سیستم خروج پلکانی با خروج‌های ساده (حجم 0.04 لات)</h3>
                        <p style="margin:6px 0 0 0;color:#bae6fd;font-size:13px;">تحلیل عملکرد {tot_k_cnt} معامله سلاطین در ۳ روش مختلف خروج از بازار:</p>
                    </div>
                    <div style="background:#0c4a6e;border:1px solid #0284c7;padding:8px 14px;border-radius:8px;font-size:12px;color:#7dd3fc;text-align:right;">
                        <div>💵 ارزش هر پیپ: <b>$0.40 دلار</b></div>
                        <div>🧾 اصطکاک پرداخت‌شده بروکر (کمیسیون+اسپرد): <b>${tot_k_cnt * 0.48:.2f} دلار</b></div>
                    </div>
                </div>
            </div>

            <!-- Steps Breakdown Grid -->
            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:14px;margin-bottom:18px;">
                <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                    <div style="color:#facc15;font-weight:bold;font-size:14px;">🎯 پله اول (TP 1:1) - خروج ۰.۰۲ لات (۵۰٪)</div>
                    <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">ذخیره ۵۰٪ سود معامله + <b>انتقال فوری استاپ لاس به نقطه ورود (Break-Even)</b></div>
                    <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">🛡️ نتیجه: پوشش کامل اصطکاک و صفر شدن ریسک معامله!</div>
                </div>
                <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                    <div style="color:#facc15;font-weight:bold;font-size:14px;">🎯 پله دوم (TP 1:2) - خروج ۰.۰۱ لات (۲۵٪)</div>
                    <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">نقد کردن ۲۵٪ دیگر از حجم با سود ۲ برابری + <b>قفل سود در سطح TP1</b></div>
                    <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">📈 نتیجه: تثبیت سود عالی و محافظت در برابر برگشت قیمت</div>
                </div>
                <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                    <div style="color:#facc15;font-weight:bold;font-size:14px;">🚀 پله سوم (TP 1:4) - خروج ۰.۰۱ لات (۲۵٪ رانر)</div>
                    <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">نگهداری ۲۵٪ باقیمانده بدون هیچ ریسکی برای امواج بزرگ روندی</div>
                    <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">👑 نتیجه: دوشیدن حداکثر روند در رالی‌های انفجاری</div>
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
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="color:#94a3b8;font-weight:bold;">۱. خروج ساده تک‌تارگت در TP 1:1 (بستن ۱۰۰٪ حجم در 1:1)</td>
                            <td style="text-align:center;color:#38bdf8;">${s1_gross:+.2f}</td>
                            <td style="text-align:center;color:#f87171;">${s1_fric:.2f}</td>
                            <td style="text-align:center;color:{'#00e676' if s1_net >= 0 else '#ef4444'};font-weight:bold;">${s1_net:+.2f} دلار</td>
                            <td style="text-align:center;color:#facc15;font-weight:bold;">{s1_pf:.2f}</td>
                        </tr>
                        <tr>
                            <td style="color:#94a3b8;font-weight:bold;">۲. خروج ساده تک‌تارگت در TP 1:2 (بستن ۱۰۰٪ حجم در 1:2)</td>
                            <td style="text-align:center;color:#38bdf8;">${s2_gross:+.2f}</td>
                            <td style="text-align:center;color:#f87171;">${s2_fric:.2f}</td>
                            <td style="text-align:center;color:{'#00e676' if s2_net >= 0 else '#ef4444'};font-weight:bold;">${s2_net:+.2f} دلار</td>
                            <td style="text-align:center;color:#facc15;font-weight:bold;">{s2_pf:.2f}</td>
                        </tr>
                        <tr style="background:#0c4a6e;border-top:2px solid #38bdf8;">
                            <td style="color:#facc15;font-weight:bold;font-size:14px;">۳. خروج پلکانی تطبیقی هوشمند (Scale-Out + BE + Runner)</td>
                            <td style="text-align:center;color:#38bdf8;font-weight:bold;">${tot_kings_gross:+.2f}</td>
                            <td style="text-align:center;color:#f87171;font-weight:bold;">${tot_kings_friction:.2f}</td>
                            <td style="text-align:center;color:{'#00e676' if tot_kings_net >= 0 else '#ef4444'};font-weight:bold;font-size:16px;">${tot_kings_net:+.2f} دلار نقد! 🚀</td>
                            <td style="text-align:center;color:#34d399;font-weight:bold;font-size:15px;">{s3_pf:.2f}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 📊 TIMEFRAME BREAKDOWN -->
        <div class="section-box">
            <h3 style="margin:0 0 16px 0;color:#38bdf8;font-size:18px;">📊 عملکرد به تفکیک تایم‌فریم (M1, M5, M15)</h3>
            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr>
                            <th>تایم‌فریم</th>
                            <th style="text-align:center;">تعداد معامله</th>
                            <th style="text-align:center;">وین‌ریت ۱:۱</th>
                            <th style="text-align:center;">وین‌ریت ۱:۲</th>
                            <th style="text-align:center;">نرخ باخت (SL)</th>
                            <th style="text-align:center;">💵 سود خالص دلاری (0.04)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(tf_rows)}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 📑 ALL PATTERNS MASTER TABLE -->
        <div class="section-box">
            <h3 style="margin:0 0 16px 0;color:#38bdf8;font-size:18px;">📑 جدول تفصیلی عملکرد تمام الگوهای شناسایی‌شده در دیتابیس</h3>
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
</body>
</html>
"""

    for out_path in OUT_PATHS:
        try:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ فایل داشبورد با موفقیت ایجاد گردید: {out_path}")
        except Exception as e:
            print(f"❌ خطا در ایجاد {out_path}: {e}")

if __name__ == '__main__':
    build_dashboard()
