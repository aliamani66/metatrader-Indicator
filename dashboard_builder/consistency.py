from collections import defaultdict
from datetime import datetime, timedelta
from dashboard_builder.config import FRICTION_04_PER_TRADE
from dashboard_builder.metrics import calc_scaleout_pnl

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

def calc_weekly_consistency(closed_trades, qualified_kings, friction_04_per_trade=FRICTION_04_PER_TRADE):
    weekly_data = defaultdict(lambda: {
        'trades_all': [],
        'trades_kings': [],
        'boxes_all': defaultdict(list),
        'boxes_kings': defaultdict(list)
    })
    box_weekly_history = defaultdict(lambda: defaultdict(list))
    king_keys = {(k['role'], k['tf']) for k in qualified_kings}

    for r in closed_trades:
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
            w_pnl = sum(calc_scaleout_pnl(r, friction_04_per_trade) for r in t_list)
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

    weekly_bar_data = []
    for yr, wk in sorted_wk_keys:
        w_data = weekly_data[(yr, wk)]
        t_kings = w_data['trades_kings']
        t_all = w_data['trades_all']

        k_cnt = len(t_kings)
        k_wins = len([r for r in t_kings if int(r.get('HitTargetRatio', 0)) >= 1])
        k_losses = len([r for r in t_kings if int(r.get('HitTargetRatio', 0)) == 0])
        k_wr = (k_wins / k_cnt * 100) if k_cnt else 0
        k_pnl = round(sum(calc_scaleout_pnl(r, friction_04_per_trade) for r in t_kings), 2)

        all_cnt = len(t_all)
        all_wins = len([r for r in t_all if int(r.get('HitTargetRatio', 0)) >= 1])
        all_losses = len([r for r in t_all if int(r.get('HitTargetRatio', 0)) == 0])
        all_wr = (all_wins / all_cnt * 100) if all_cnt else 0
        all_pnl = round(sum(calc_scaleout_pnl(r, friction_04_per_trade) for r in t_all), 2)

        try:
            first_date = datetime.strptime(f"{yr}-W{wk:02d}-1", "%Y-W%W-%w")
            last_date = first_date + timedelta(days=4)
            d_range = f"{first_date.strftime('%m.%d')} - {last_date.strftime('%m.%d')}"
        except:
            d_range = f"Wk {wk}"

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

    return {
        'weekly_data': weekly_data,
        'box_weekly_history': box_weekly_history,
        'sorted_wk_keys': sorted_wk_keys,
        'total_weeks': total_weeks,
        'consistency_list': consistency_list,
        'weekly_bar_data': weekly_bar_data,
        'top_consistent_box': consistency_list[0]['box'] if consistency_list else 'N/A'
    }

def calc_multi_period_consistency(closed_trades, qualified_kings, base_yr=2025, friction_04_per_trade=FRICTION_04_PER_TRADE):
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

    box_trades_map = defaultdict(list)
    king_keys = {(k['role'], k['tf']) for k in qualified_kings}

    for r in closed_trades:
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
                pnl = calc_scaleout_pnl(r, friction_04_per_trade)
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

    inter_map = {k['kk']: (idx, k) for idx, k in enumerate(mp_intersection_list, 1)}
    master_map = {f"{k['role']}|{k['tf']}": (idx, k) for idx, k in enumerate(qualified_kings, 1)}
    overlap_count = sum(1 for k in qualified_kings if f"{k['role']}|{k['tf']}" in inter_map)
    master_only_count = len(qualified_kings) - overlap_count
    overlap_ratio = (overlap_count / len(qualified_kings) * 100) if qualified_kings else 0

    return {
        'period_configs': period_configs,
        'mp_period_data': mp_period_data,
        'mp_intersection_list': mp_intersection_list,
        'inter_map': inter_map,
        'master_map': master_map,
        'overlap_count': overlap_count,
        'master_only_count': master_only_count,
        'overlap_ratio': overlap_ratio
    }
