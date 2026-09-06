import math
from dashboard_builder.config import FRICTION_04_PER_TRADE
from dashboard_builder.filters import compute_latency_stats

def calc_scaleout_pnl(r, friction=FRICTION_04_PER_TRADE):
    pts = float(r.get('RiskPoints', 0.0))
    hr = int(r.get('HitTargetRatio', 0))
    if hr == 0: gross = - pts * 0.04
    elif hr == 1: gross = pts * 0.02
    elif hr in [2, 3]: gross = (pts * 0.02) + (pts * 2 * 0.01)
    else: gross = (pts * 0.02) + (pts * 2 * 0.01) + (pts * 4 * 0.01)
    return gross - friction

def calc_pattern_metrics(t_list, tf, role, friction_04_per_trade=FRICTION_04_PER_TRADE):
    cnt = len(t_list)
    w1 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 1])
    w2 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 2])
    w3 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 3])
    w4 = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) >= 4])
    sl = len([r for r in t_list if int(r.get('HitTargetRatio', 0)) == 0])

    w1_p = (w1 / cnt * 100) if cnt else 0.0
    w2_p = (w2 / cnt * 100) if cnt else 0.0
    w3_p = (w3 / cnt * 100) if cnt else 0.0
    w4_p = (w4 / cnt * 100) if cnt else 0.0
    sl_p = (sl / cnt * 100) if cnt else 0.0

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

    is_king_eligible = is_perfect or (cnt >= 4 and net > 5.0 and w1_p >= 50.0)

    return {
        'tf': tf, 'role': role, 'cnt': cnt,
        'w1': w1, 'w2': w2, 'w3': w3, 'w4': w4, 'sl': sl,
        'w1_p': w1_p, 'w2_p': w2_p, 'w3_p': w3_p, 'w4_p': w4_p, 'sl_p': sl_p,
        'score': final_score, 'is_perfect': is_perfect, 'is_runner': is_runner, 'is_proven': is_proven,
        'min_sl': min_sl, 'max_sl': max_sl, 'avg_sl': avg_sl,
        'gross': gross, 'fric': fric, 'net': net,
        'max_dd': max_dd, 'pf': pf, 'ret_dd': ret_dd,
        'trades': t_list,
        'is_king_eligible': is_king_eligible
    }

def calc_tf_metrics(t_list, friction_04_per_trade=FRICTION_04_PER_TRADE):
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
    lat = compute_latency_stats(t_list)
    return {
        'cnt': cnt,
        'w1_p': w1 / cnt * 100,
        'w2_p': w2 / cnt * 100,
        'w3_p': w3 / cnt * 100,
        'w4_p': w4 / cnt * 100,
        'sl_p': sl / cnt * 100,
        'gross': gross,
        'fric': fric,
        'net': net,
        'wait_avg_fmt': lat['avg_fmt'],
        'wait_min_fmt': lat['min_fmt'],
        'wait_max_fmt': lat['max_fmt'],
        'wait_med_fmt': lat['med_fmt'],
        'wait_p90_fmt': lat['p90_fmt'],
        'wait_avg_short': lat['avg_short'],
        'wait_med_short': lat['med_short'],
        'wait_range_fmt': f"{lat['min_short']} ~ {lat['max_short']}",
        'wait_stats': lat
    }

def calc_scaleout_comparison(kings_trades, friction_04_per_trade=FRICTION_04_PER_TRADE):
    tot_k_cnt = len(kings_trades)
    tot_k_fric = tot_k_cnt * friction_04_per_trade

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
            m2_gross += (pts * 1.0 * 0.01) - (pts * 1.0 * 0.03)
        elif hr == 2:
            m2_gross += (pts * 1.0 * 0.01) + (pts * 2.0 * 0.01)
        elif hr == 3:
            m2_gross += (pts * 1.0 * 0.01) + (pts * 2.0 * 0.01) + (pts * 3.0 * 0.01)
        elif hr >= 4:
            m2_gross += (pts * 1.0 * 0.01) + (pts * 2.0 * 0.01) + (pts * 3.0 * 0.01) + (pts * 4.0 * 0.01)
    m2_net = m2_gross - tot_k_fric
    be_diff = m1_net - m2_net

    return {
        's1_gross': s1_gross, 's1_net': s1_net, 's1_pf': s1_pf,
        's2_gross': s2_gross, 's2_net': s2_net, 's2_pf': s2_pf, 's2_diff_dollar': s2_diff_dollar, 's2_diff_pct': s2_diff_pct,
        's3_gross': s3_gross, 's3_net': s3_net, 's3_pf': s3_pf, 's3_diff_dollar': s3_diff_dollar, 's3_diff_pct': s3_diff_pct,
        'sl_direct': sl_direct, 'tp1_only': tp1_only, 'tp2_only': tp2_only, 'tp3_4': tp3_4,
        'sl_direct_pct': sl_direct_pct, 'tp1_only_pct': tp1_only_pct, 'tp2_only_pct': tp2_only_pct, 'tp3_4_pct': tp3_4_pct,
        'm1_gross': m1_gross, 'm1_net': m1_net,
        'm2_gross': m2_gross, 'm2_net': m2_net,
        'be_diff': be_diff
    }
