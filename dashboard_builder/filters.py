from datetime import datetime

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

def get_box_wait_time_minutes(r):
    bts = r.get('BoxTimeStart', '')
    et = r.get('EntryTime', '')
    if not bts or not et or bts == 'None' or et == 'None':
        return None
    try:
        t_start = datetime.strptime(bts[:16], '%Y.%m.%d %H:%M')
        t_entry = datetime.strptime(et[:16], '%Y.%m.%d %H:%M')
        diff_sec = (t_entry - t_start).total_seconds()
        if diff_sec >= 0:
            return diff_sec / 60.0
    except:
        pass
    return None

def format_duration_short(minutes):
    if minutes is None or minutes <= 0:
        return "0m"
    if minutes < 60:
        return f"{minutes:.0f}m"
    elif minutes < 1440:
        hours = minutes / 60.0
        return f"{hours:.1f}h"
    else:
        days = minutes / 1440.0
        return f"{days:.1f}d"

def format_duration_persian(minutes):
    if minutes is None or minutes <= 0:
        return "۰ دقیقه"
    if minutes < 60:
        return f"{minutes:.0f} دقیقه"
    elif minutes < 1440:
        hours = minutes / 60.0
        return f"{hours:.1f} ساعت ({minutes:.0f} دقیقه)"
    else:
        days = minutes / 1440.0
        hours = (minutes % 1440) / 60.0
        return f"{days:.1f} روز ({hours:.0f} ساعت)"

def compute_latency_stats(t_list):
    delays = []
    for r in t_list:
        wm = get_box_wait_time_minutes(r)
        if wm is not None:
            delays.append(wm)
    if not delays:
        return {
            'cnt': 0, 'min': 0.0, 'max': 0.0, 'avg': 0.0, 'med': 0.0, 'p90': 0.0,
            'avg_fmt': '-', 'min_fmt': '-', 'max_fmt': '-', 'med_fmt': '-', 'p90_fmt': '-',
            'avg_short': '-', 'min_short': '-', 'max_short': '-', 'med_short': '-', 'p90_short': '-'
        }
    delays.sort()
    n = len(delays)
    d_min = delays[0]
    d_max = delays[-1]
    d_avg = sum(delays) / n
    d_med = delays[n // 2]
    d_p90 = delays[int(n * 0.90)]
    return {
        'cnt': n,
        'min': d_min,
        'max': d_max,
        'avg': d_avg,
        'med': d_med,
        'p90': d_p90,
        'avg_fmt': format_duration_persian(d_avg),
        'min_fmt': format_duration_persian(d_min),
        'max_fmt': format_duration_persian(d_max),
        'med_fmt': format_duration_persian(d_med),
        'p90_fmt': format_duration_persian(d_p90),
        'avg_short': format_duration_short(d_avg),
        'min_short': format_duration_short(d_min),
        'max_short': format_duration_short(d_max),
        'med_short': format_duration_short(d_med),
        'p90_short': format_duration_short(d_p90),
    }

def evaluate_trade_filters(closed_trades):
    accepted_trades = []
    rejected_trades = []

    f1_rej, f1_sl = 0, 0
    f2_rej, f2_sl = 0, 0
    f3_rej, f3_sl = 0, 0
    f4_rej, f4_sl = 0, 0
    f5_rej, f5_sl = 0, 0
    f7_rej, f7_sl = 0, 0

    for r in closed_trades:
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

    w1_cnt_b = len([r for r in closed_trades if int(r.get('HitTargetRatio', 0)) >= 1])
    w2_cnt_b = len([r for r in closed_trades if int(r.get('HitTargetRatio', 0)) >= 2])
    sl_cnt_b = len([r for r in closed_trades if int(r.get('HitTargetRatio', 0)) == 0])
    w1_rate_b = w1_cnt_b / len(closed_trades) * 100 if closed_trades else 0
    w2_rate_b = w2_cnt_b / len(closed_trades) * 100 if closed_trades else 0
    sl_rate_b = sl_cnt_b / len(closed_trades) * 100 if closed_trades else 0
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

    return {
        'accepted_trades': accepted_trades,
        'rejected_trades': rejected_trades,
        'f1_rej': f1_rej, 'f1_sl': f1_sl,
        'f2_rej': f2_rej, 'f2_sl': f2_sl,
        'f3_rej': f3_rej, 'f3_sl': f3_sl,
        'f4_rej': f4_rej, 'f4_sl': f4_sl,
        'f5_rej': f5_rej, 'f5_sl': f5_sl,
        'f7_rej': f7_rej, 'f7_sl': f7_sl,
        'w1_cnt_b': w1_cnt_b, 'w2_cnt_b': w2_cnt_b, 'sl_cnt_b': sl_cnt_b,
        'w1_rate_b': w1_rate_b, 'w2_rate_b': w2_rate_b, 'sl_rate_b': sl_rate_b, 'ev_b': ev_b,
        'w1_cnt_a': w1_cnt_a, 'w2_cnt_a': w2_cnt_a, 'sl_cnt_a': sl_cnt_a,
        'w1_rate_a': w1_rate_a, 'w2_rate_a': w2_rate_a, 'sl_rate_a': sl_rate_a, 'ev_a': ev_a,
        'sl_in_rej': sl_in_rej,
        'rej_accuracy': rej_accuracy
    }
