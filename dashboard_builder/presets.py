import os
from datetime import datetime, timedelta
from dashboard_builder.config import REPO_ROOT

def _make_preset_fdesc(p_opt):
    pot_v = p_opt.get('pot', 0.0)
    h_lbl = p_opt.get('h_label', '')
    return f"{h_lbl} | کف: ${pot_v:.1f}" if pot_v > 0 else h_lbl

def optimize_smart_presets(trades_sim_list, kings_sim_list, closed_count):
    total_kings_trades = len([t for t in trades_sim_list if t.get('k') == 1])
    min_15pct_trades = max(15, int(total_kings_trades * 0.15))
    min_35pct_trades = max(25, int(total_kings_trades * 0.35))

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

    hours_map = {
        'all': ('۲۴ ساعته', set(range(24)), [True]*24),
        'no_night': ('حذف شب (۰۴ تا ۲۲)', set(range(4, 22)), [False if h in [22,23,0,1,2,3] else True for h in range(24)]),
        'lon_ny': ('سشن روز (۰۷ تا ۲۰)', set(range(7, 20)), [True if 7 <= h < 20 else False for h in range(24)]),
        'core_day': ('اوج سشن (۰۸ تا ۱۸)', set(range(8, 19)), [True if 8 <= h <= 18 else False for h in range(24)])
    }

    min_pot_candidates = [0.0, 1.0, 1.5, 2.0, 2.5, 3.0]
    circuit_breaker_candidates = [(0, 0, False, 'بدون وقفه'), (2, 1, False, '۲ استاپ -> رد معامله ۳')]

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
                    score = (pf ** 1.3) * (wr / 50.0) * max(0.5, avg) / max(12.0, max_dd) * 100
                    evaluated_combos.append({
                        'h_key': h_key, 'h_label': h_label, 'h_arr': h_arr,
                        'pot': pot, 'dropped_n': drop_n, 'kings': list(active_kings), 'kings_cnt': len(active_kings),
                        'trig': trig, 'sk': sk, 'day': day, 'cb_label': cb_label,
                        'total': total, 'wr': wr, 'pf': pf, 'net': net, 'avg': avg, 'max_dd': max_dd, 'score': score
                    })

    evaluated_combos.sort(key=lambda x: x['score'], reverse=True)

    if evaluated_combos:
        opt_p1 = evaluated_combos[0]
    else:
        opt_p1 = {
            'h_key': 'all', 'h_label': '۲۴ ساعته', 'h_arr': [True]*24,
            'pot': 0.0, 'dropped_n': 0, 'kings': list(all_dataset_kings_set), 'kings_cnt': len(all_dataset_kings_set),
            'trig': 0, 'sk': 0, 'day': False, 'cb_label': 'بدون وقفه',
            'total': closed_count, 'wr': 50.0, 'pf': 1.0, 'net': 0.0, 'avg': 0.0, 'max_dd': 0.0, 'score': 0.0
        }

    cands_p2 = [r for r in evaluated_combos if r['total'] >= min_35pct_trades and r['h_key'] in ['no_night', 'all']]
    opt_p2 = cands_p2[0] if cands_p2 else (evaluated_combos[1] if len(evaluated_combos) > 1 else opt_p1)

    cands_p3 = [r for r in evaluated_combos if r['h_key'] == 'lon_ny' and r['pot'] <= 2.0]
    opt_p3 = cands_p3[0] if cands_p3 else opt_p1

    cands_p4 = sorted([r for r in evaluated_combos if r['pf'] >= 2.5 and r['total'] >= min_15pct_trades and r['total'] != opt_p1['total']], key=lambda x: x['max_dd'])
    opt_p4 = cands_p4[0] if cands_p4 else opt_p1

    smart_presets_defs = [
        {
            'id': 'preset-champion',
            'idx': 0,
            'title': '🎯 اسنایپر هوشمند',
            'badge': f'🏆 منتخب (PF {opt_p1["pf"]:.2f})',
            'badge_bg': '#831843',
            'badge_col': '#fbcfe8',
            'strategy_desc': 'بالاترین پرافیت فاکتور و بیشترین بازدهی با کنترل دقیق ریسک',
            'filter_desc': _make_preset_fdesc(opt_p1),
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
            'title': '⚖️ تعادل طلایی',
            'badge': '⭐ سود متوازن',
            'badge_bg': '#854d0e',
            'badge_col': '#fef08a',
            'strategy_desc': 'بیشترین سود دلاری پایدار با حجم ترید بالا و پرافیت فاکتور مطلوب',
            'filter_desc': _make_preset_fdesc(opt_p2),
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
            'title': '☀️ سشن روزانه',
            'badge': '☀️ اوج بازار',
            'badge_bg': '#0c4a6e',
            'badge_col': '#7dd3fc',
            'strategy_desc': 'معاملات پرقدرت روز در ساعات اوج نقدینگی و کمترین اسپرد',
            'filter_desc': _make_preset_fdesc(opt_p3),
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
            'title': '🛡️ سپر حداقل افت',
            'badge': f'🛡️ حداقل افت (${opt_p4["max_dd"]:.0f})',
            'badge_bg': '#064e3b',
            'badge_col': '#34d399',
            'strategy_desc': 'محافظه‌کارانه‌ترین استراتژی با حذف گره‌های پرریسک و حفظ سرمایه',
            'filter_desc': _make_preset_fdesc(opt_p4),
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
            'title': '🌐 سبد پایه ۲۴ ساعته',
            'badge': '🌐 کل چارت',
            'badge_bg': '#1e293b',
            'badge_col': '#94a3b8',
            'strategy_desc': 'شبیه‌سازی کامل تمام سلاطین در ۲۴ ساعت بدون فیلتر',
            'filter_desc': '۲۴ ساعته کامل | بدون محدودیت کف',
            'min_pot': 0.0,
            'hours': [True]*24,
            'hours_name': 'all',
            'kings': list(all_dataset_kings_set),
            'consec_trig': 0,
            'consec_sk': 0,
            'consec_day': False,
            'is_featured': False
        }
    ]

    smart_presets_json_data = []
    for p in smart_presets_defs:
        k_set = set(p['kings'])
        h_arr = p['hours']
        min_p = p['min_pot']
        sub = []
        consec_loss = 0
        skips = 0
        for t in trades_sim_list:
            if t['k'] != 1: continue
            if t['kk'] not in k_set: continue
            h = t['h']
            if not (0 <= h < len(h_arr) and h_arr[h]): continue
            if t['pot'] < min_p: continue
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
            'net': round(nt, 2),
            'strategy_desc': p['strategy_desc'],
            'filter_desc': p['filter_desc'],
            'badge': p['badge'],
            'badge_bg': p['badge_bg'],
            'badge_col': p['badge_col'],
            'is_featured': p['is_featured']
        }
        smart_presets_json_data.append(p_data)

    return smart_presets_defs, smart_presets_json_data

def export_preset_set_files(symbols_data, repo_root=None):
    if repo_root is None:
        repo_root = REPO_ROOT

    dirs = [
        os.path.join(repo_root, "Experts", "تنظیمات"),
        os.path.join(repo_root, "Experts", "Settings")
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    today_date = datetime.now().strftime("%Y.%m.%d %H:%M:%S")

    saved_count = 0
    for sym, sym_info in symbols_data.items():
        presets = sym_info.get('smart_presets', [])
        all_kings_set = set(k['kk'] for k in sym_info.get('kings_sim_list', []))

        title_map = {
            0: "DiamondKings",
            1: "GoldenBalance",
            2: "LondonNY",
            3: "UltraLowDDShield",
            4: "AllKings24H"
        }

        for p in presets:
            raw_title = p.get('title', 'Preset')
            idx = p.get('idx', 0)
            clean_title = title_map.get(idx, f"Preset_{idx+1}")
            wr = p.get('wr', 0.0)
            pf = p.get('pf', 0.0)
            hours = p.get('hours', [])
            hours_str = ""
            if hours and sum(1 for h in hours if h) < 24:
                hours_str = ",".join(f"{h:02d}" for h in range(24) if hours[h])

            p_kings = set(p.get('kings', []))
            allowed_str = ", ".join(sorted(p_kings))
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
                "InpOrderExecMode=0",
                "InpLimitExpirationBars=40",
                f"InpScenarioName={raw_title}",
                f"InpMinTradePotential={float(p.get('min_pot', 0.0)):.2f}",
                f"InpAllowedTradingHours={hours_str}",
                f"InpConsecLossTrigger={trig_int}",
                f"InpConsecLossAction={action_int}",
                f"InpAllowedKingsList={allowed_str}",
                f"InpDisabledKingsList={disabled_str}",
                "InpOnlyTradeKings=true",
                "InpTradeOnlyGoldenKings=true",
                "InpEnableKingsM15=true",
                "InpEnableKingsM5=true",
                f"InpEnableKingsM1={use_m1}",
                "InpAllowOverlappingTrades=true",
                "InpSlippagePoints=20",
                f"InpMaxEntryDeviationPips={max_dev}",
                "InpSLOffsetPips=8.0",
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
                "InpHistoryDays=10",
                "InpShowBoxes=false",
                "InpAutoDrawTrades=true",
                "InpUniqueTradeColors=true",
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
                "InpOrderExecMode=0",
                "InpLimitExpirationBars=40",
                f"InpScenarioName={raw_title}",
                "InpOnlyTradeKings=true",
                f"InpAllowedKingsList={allowed_str}",
                f"InpDisabledKingsList={disabled_str}",
                "InpEnableKingsM15=true",
                "InpEnableKingsM5=true",
                f"InpEnableKingsM1={use_m1}",
                "InpTradeOnlyGoldenKings=true",
                "InpAllowOverlappingTrades=true",
                "InpSlippagePoints=20",
                f"InpMaxEntryDeviationPips={max_dev}",
                "InpSLOffsetPips=8.0",
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
                "InpHistoryDays=10",
                "InpAutoDrawTrades=true",
                "InpUniqueTradeColors=true",
                "InpExportCSV=true"
            ]
            ini_content = "\r\n".join(ini_lines)
            try:
                ini_fp = os.path.join(tester_dir, ini_filename)
                with open(ini_fp, 'w', encoding='utf-16') as f:
                    f.write(ini_content + "\r\n")
            except Exception as e:
                pass

    print(f"📁 ذخیره خودکار {saved_count} فایل تنظیمات (.set) در Experts/تنظیمات و فایل‌های (.ini) در Profiles/Tester انجام شد.")
