/**
 * FlagPro Dashboard - Core Data Processing Engine
 * Converts raw CSV data into comprehensive multi-dimensional datasets for all 11 tabs.
 */
const DataEngine = (function() {
    'use strict';

    function processCSVData(csvText, fileName) {
        // 1. Validate First
        const validation = DataValidator.validateCSV(csvText, fileName);
        if (!validation.isValid) {
            throw new Error(validation.issues.join('\n'));
        }

        const lines = csvText.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
        const headers = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, ''));
        const colIdx = {};
        headers.forEach((h, idx) => { colIdx[h] = idx; });

        let detectedSym = validation.detectedSymbol;
        if (!detectedSym) {
            const m = (fileName || '').match(/flagpro_trades_([A-Za-z0-9_]+)[.]csv/i);
            detectedSym = m ? m[1].toUpperCase() : 'CUSTOM';
        }

        const rawTrades = [];
        for (let i = 1; i < lines.length; i++) {
            const parts = lines[i].split(',').map(p => p.trim().replace(/^["']|["']$/g, ''));
            if (parts.length < 5) continue;

            const isClosed = colIdx['IsClosed'] !== undefined ? parts[colIdx['IsClosed']] : 'True';
            const outcome = colIdx['Outcome'] !== undefined ? parts[colIdx['Outcome']] : '';
            if (isClosed === 'False' || outcome.toLowerCase() === 'pending') continue;

            const role = parts[colIdx['Role']];
            const tf = parts[colIdx['Timeframe']] || 'M1';
            const bname = colIdx['BoxName'] !== undefined ? parts[colIdx['BoxName']] : '';
            const dir = colIdx['Direction'] !== undefined ? parts[colIdx['Direction']] : 'BUY';
            const et = parts[colIdx['EntryTime']];
            const ex = colIdx['ExitTime'] !== undefined ? parts[colIdx['ExitTime']] : et;
            const enPrice = colIdx['EntryPrice'] !== undefined ? parseFloat(parts[colIdx['EntryPrice']]) || 0 : 0;
            const slPrice = colIdx['StopLoss'] !== undefined ? parseFloat(parts[colIdx['StopLoss']]) || 0 : 0;
            const pts = colIdx['RiskPoints'] !== undefined ? parseFloat(parts[colIdx['RiskPoints']]) || 0 : 0;
            const hr = colIdx['HitTargetRatio'] !== undefined ? parseInt(parts[colIdx['HitTargetRatio']]) || 0 : 0;
            const tp1 = colIdx['TP1'] !== undefined ? parseFloat(parts[colIdx['TP1']]) || 0 : 0;
            const tp2 = colIdx['TP2'] !== undefined ? parseFloat(parts[colIdx['TP2']]) || 0 : 0;
            const tp3 = colIdx['TP3'] !== undefined ? parseFloat(parts[colIdx['TP3']]) || 0 : 0;
            const tp4 = colIdx['TP4'] !== undefined ? parseFloat(parts[colIdx['TP4']]) || 0 : 0;

            if (!role || isNaN(pts) || pts <= 0 || isNaN(hr) || !et) continue;

            rawTrades.push({ sym: detectedSym, role, tf, bname, dir, et, ex, enPrice, slPrice, pts, hr, tp1, tp2, tp3, tp4 });
        }

        // Sort chronologically
        rawTrades.sort((a, b) => (a.et > b.et ? 1 : -1));

        const friction = AppConfig.frictionPerTrade || 0.48;
        const simTrades = [];
        const allTrades = [];
        const boxGroups = {};

        // Scaleout trackers
        const scaleoutSummary = {
            total: rawTrades.length,
            slCount: 0,
            tp1Count: 0,
            tp2Count: 0,
            tp3Count: 0,
            tp4Count: 0,
            grossProfit: 0,
            grossLoss: 0,
            netUSD: 0
        };

        // Timeframe trackers
        const tfGroups = {};
        // Hourly & Day trackers
        const hourGroups = Array.from({ length: 24 }, (_, h) => ({ hour: h, count: 0, wins: 0, net: 0 }));
        const dayGroups = Array.from({ length: 7 }, (_, d) => ({ day: d, count: 0, wins: 0, net: 0 }));

        rawTrades.forEach((t, idx) => {
            let pnl = 0;
            if (t.hr === 0) {
                pnl = -t.pts * 0.04 - friction;
                scaleoutSummary.slCount++;
                scaleoutSummary.grossLoss += Math.abs(pnl);
            } else {
                pnl = -friction;
                scaleoutSummary.tp1Count++;
                if (t.hr >= 1) pnl += t.pts * 0.01 * 1.0;
                if (t.hr >= 2) { pnl += t.pts * 0.01 * 2.0; scaleoutSummary.tp2Count++; }
                if (t.hr >= 3) { pnl += t.pts * 0.01 * 3.0; scaleoutSummary.tp3Count++; }
                if (t.hr >= 4) { pnl += t.pts * 0.01 * 4.0; scaleoutSummary.tp4Count++; }
                scaleoutSummary.grossProfit += Math.max(0, pnl);
            }
            scaleoutSummary.netUSD += pnl;

            // Box grouping for Kings selection
            const kk = t.role + '|' + t.tf;
            if (!boxGroups[kk]) {
                boxGroups[kk] = { role: t.role, tf: t.tf, kk: kk, trades: [], wins: 0, losses: 0, sl: 0, grossWin: 0, grossLoss: 0, net: 0, w1: 0, w2: 0, w3: 0, w4: 0 };
            }
            const bg = boxGroups[kk];
            bg.trades.push({ pnl, hr: t.hr, pts: t.pts, et: t.et });
            if (t.hr === 0) {
                bg.sl++; bg.losses++; bg.grossLoss += Math.abs(pnl);
            } else {
                bg.wins++; bg.grossWin += Math.max(0, pnl);
                if (t.hr >= 1) bg.w1++;
                if (t.hr >= 2) bg.w2++;
                if (t.hr >= 3) bg.w3++;
                if (t.hr >= 4) bg.w4++;
            }
            bg.net += pnl;

            // Timeframe grouping
            if (!tfGroups[t.tf]) {
                tfGroups[t.tf] = { tf: t.tf, trades: 0, wins: 0, losses: 0, net: 0, grossWin: 0, grossLoss: 0, ptsSum: 0 };
            }
            const tfg = tfGroups[t.tf];
            tfg.trades++;
            tfg.ptsSum += t.pts;
            tfg.net += pnl;
            if (t.hr > 0) { tfg.wins++; tfg.grossWin += Math.max(0, pnl); }
            else { tfg.losses++; tfg.grossLoss += Math.abs(pnl); }

            // Hourly & Day grouping
            const hVal = t.et.length >= 13 ? parseInt(t.et.substring(11, 13)) : 0;
            if (hVal >= 0 && hVal < 24) {
                hourGroups[hVal].count++;
                hourGroups[hVal].net += pnl;
                if (t.hr > 0) hourGroups[hVal].wins++;
            }

            const dt = new Date(t.et.replace(/[.]/g, '-'));
            if (!isNaN(dt.getTime())) {
                const dayIdx = dt.getUTCDay();
                dayGroups[dayIdx].count++;
                dayGroups[dayIdx].net += pnl;
                if (t.hr > 0) dayGroups[dayIdx].wins++;
            }

            simTrades.push({
                i: idx + 1, t: t.et, xt: t.ex, h: hVal, tf: t.tf, r: t.role, k: 1, kk: kk, pts: Math.round(t.pts * 10) / 10, pot: Math.round(t.pts * 0.04 * 100) / 100, hr: t.hr, p: Math.round(pnl * 100) / 100
            });

            allTrades.push({
                id: idx + 1, tf: t.tf, bname: t.bname || ('#' + (idx+1)), role: t.role, dir: t.dir, en_t: t.et, ex_t: t.ex, en_p: t.enPrice, sl: t.slPrice, pts: t.pts, net: Math.round(pnl * 100) / 100, pot: Math.round(t.pts * 0.04 * 100) / 100, t1: t.hr >= 1 ? 1 : 0, t2: t.hr >= 2 ? 1 : 0, t3: t.hr >= 3 ? 1 : 0, t4: t.hr >= 4 ? 1 : 0, tp1: t.tp1, tp2: t.tp2, tp3: t.tp3, tp4: t.tp4, is_k: 1
            });
        });

        // Score Kings (Hedge-fund scoring formula)
        const scoredBoxes = [];
        Object.values(boxGroups).forEach(bg => {
            const cnt = bg.trades.length;
            if (cnt === 0) return;
            const w1_p = (bg.w1 / cnt) * 100;
            const sl_p = (bg.sl / cnt) * 100;
            const pf = bg.grossLoss > 0 ? bg.grossWin / bg.grossLoss : (bg.grossWin > 0 ? 99 : 0);
            let peak = 0, cum = 0, maxDD = 0;
            bg.trades.forEach(tr => { cum += tr.pnl; if (cum > peak) peak = cum; let dd = peak - cum; if (dd > maxDD) maxDD = dd; });
            const purity = (cnt >= 2 && bg.sl === 0) ? 500 : Math.max(0, 400 - sl_p * 8);
            const t2 = ((bg.w2 / cnt) * 100) * 4.0;
            const pnlTrade = (bg.net / cnt) * 15.0;
            const pfScore = Math.min(100, pf * 15);
            const ddScore = maxDD > 0 ? Math.min(100, (bg.net / maxDD) * 10) : 100;
            const score = purity + t2 + pnlTrade + pfScore + ddScore;

            scoredBoxes.push({
                role: bg.role, tf: bg.tf, kk: bg.kk, score, cnt, net: bg.net, w1_p, w2_p: (bg.w2 / cnt) * 100, w3_p: (bg.w3 / cnt) * 100, w4_p: (bg.w4 / cnt) * 100, sl: bg.sl, sl_p, pf, maxDD, is_perfect: (cnt >= 2 && bg.sl === 0), is_runner: (bg.w3 / cnt >= 0.3 || bg.w4 / cnt >= 0.3)
            });
        });

        scoredBoxes.sort((a, b) => b.score - a.score);
        let qualified = scoredBoxes.filter(b => b.score >= 100 && b.net > 0 && b.cnt >= 3);
        if (qualified.length === 0) qualified = scoredBoxes.slice(0, 10);
        const kingKeySet = new Set(qualified.map(k => k.kk));

        simTrades.forEach(t => { t.k = kingKeySet.has(t.kk) ? 1 : 0; });
        allTrades.forEach(t => { t.is_k = kingKeySet.has(t.role + '|' + t.tf) ? 1 : 0; });

        const kingsSimList = qualified.map((k, idx) => ({
            id: idx + 1, role: k.role, tf: k.tf, kk: k.kk, score: Math.round(k.score * 10) / 10, cnt: k.cnt, net: Math.round(k.net * 100) / 100, w1_p: Math.round(k.w1_p * 10) / 10, w2_p: Math.round(k.w2_p * 10) / 10, w3_p: Math.round(k.w3_p * 10) / 10, w4_p: Math.round(k.w4_p * 10) / 10, sl_cnt: k.sl, sl_usd: Math.round(k.sl * (friction + 2.0) * 100) / 100, sl_p: Math.round(k.sl_p * 10) / 10, pf: Math.round(k.pf * 100) / 100, perf: k.is_perfect ? 1 : 0, run: k.is_runner ? 1 : 0
        }));

        // Identify Top SL Sets
        const sortedSLCnt = [...kingsSimList].sort((a, b) => b.sl_cnt - a.sl_cnt);
        const sortedSLUsd = [...kingsSimList].sort((a, b) => b.sl_usd - a.sl_usd);
        const sortedSLPct = [...kingsSimList].filter(x => x.cnt >= 10).sort((a, b) => b.sl_p - a.sl_p);

        const top3SLCntKeys = sortedSLCnt.slice(0, 3).map(x => x.kk);
        const top3SLUsdKeys = sortedSLUsd.slice(0, 3).map(x => x.kk);
        const top5SLUsdKeys = sortedSLUsd.slice(0, 5).map(x => x.kk);
        const top3SLPctKeys = sortedSLPct.slice(0, 3).map(x => x.kk);

        // Weekly Bars Grouping
        const weeklyGroups = {};
        simTrades.forEach(t => {
            if (!t.t) return;
            const dt = new Date(t.t.substring(0, 10).replace(/[.]/g, '-'));
            if (isNaN(dt.getTime())) return;
            const day = dt.getUTCDay();
            const diff = dt.getUTCDate() - day + (day === 0 ? -6 : 1);
            const monday = new Date(dt.setDate(diff));
            const wkKey = monday.toISOString().substring(0, 10);
            if (!weeklyGroups[wkKey]) {
                weeklyGroups[wkKey] = { k_pnl: 0, k_trades: 0, k_wins: 0, k_losses: 0, all_pnl: 0, all_trades: 0, all_wins: 0, all_losses: 0 };
            }
            const wg = weeklyGroups[wkKey];
            wg.all_pnl += t.p; wg.all_trades++;
            if (t.p > 0) wg.all_wins++; else wg.all_losses++;
            if (t.k === 1) {
                wg.k_pnl += t.p; wg.k_trades++;
                if (t.p > 0) wg.k_wins++; else wg.k_losses++;
            }
        });

        const weeklyBarData = Object.keys(weeklyGroups).sort().map((wk, idx) => {
            const item = weeklyGroups[wk];
            return {
                week_idx: idx + 1, label: 'هفته ' + (idx + 1), date_range: wk, k_pnl: Math.round(item.k_pnl * 100) / 100, k_trades: item.k_trades, k_wins: item.k_wins, k_losses: item.k_losses, k_wr: item.k_trades > 0 ? Math.round(item.k_wins / item.k_trades * 1000) / 10 : 0, all_pnl: Math.round(item.all_pnl * 100) / 100, all_trades: item.all_trades, all_wins: item.all_wins, all_losses: item.all_losses, all_wr: item.all_trades > 0 ? Math.round(item.all_wins / item.all_trades * 1000) / 10 : 0
            };
        });

        // Dynamic Smart Presets Calculation
        const allKingsKeys = kingsSimList.map(k => k.kk);
        const kingsWithoutTop3 = allKingsKeys.filter(kk => !top3SLCntKeys.includes(kk));

        // Helper to simulate preset
        function calcPresetStats(kList, minPot, hoursArr, consecTrig, consecAction) {
            const kSet = new Set(kList);
            const sub = simTrades.filter(t => t.k === 1 && kSet.has(t.kk) && t.pot >= minPot && (hoursArr ? hoursArr[t.h] : true));
            const c = sub.length;
            const nt = sub.reduce((acc, t) => acc + t.p, 0);
            const wins = sub.filter(t => t.p > 0).length;
            const wr = c > 0 ? (wins / c * 100) : 0;
            const avg = c > 0 ? (nt / c) : 0;
            const gp = sub.filter(t => t.p > 0).reduce((acc, t) => acc + t.p, 0);
            const gl = sub.filter(t => t.p <= 0).reduce((acc, t) => acc + Math.abs(t.p), 0);
            const pf = gl > 0 ? (gp / gl) : 999;
            let peak = 100, bal = 100, maxDD = 0;
            sub.forEach(t => { bal += t.p; if (bal > peak) peak = bal; let dd = peak - bal; if (dd > maxDD) maxDD = dd; });
            return { c, wr: Math.round(wr * 10) / 10, pf: Math.round(pf * 100) / 100, avg: Math.round(avg * 100) / 100, maxDD: Math.round(maxDD), net: Math.round(nt) };
        }

        const londonNyHours = new Array(24).fill(false);
        for (let h = 8; h <= 20; h++) londonNyHours[h] = true;

        const p1 = calcPresetStats(allKingsKeys, 0, null, 0, 0);
        const p2 = calcPresetStats(allKingsKeys, 3.0, null, 0, 0);
        const p3 = calcPresetStats(kingsWithoutTop3, 0, null, 0, 0);
        const p4 = calcPresetStats(allKingsKeys, 0, londonNyHours, 0, 0);
        const p5 = calcPresetStats(kingsWithoutTop3, 1.5, londonNyHours, 2, 1);

        const smartPresets = [
            { idx: 0, title: 'حالت پایه سلاطین طلایی (بدون فیلتر)', desc: 'اجرای کامل تمام سلاطین شناسایی‌شده با تارگت‌های کامل', min_pot: 0, sl_mode: 'none', count: p1.c, cnt: p1.c, wr: p1.wr, pf: p1.pf, avg: p1.avg, max_dd: p1.maxDD, net: p1.net, hours_str: '۲۴ ساعته', hours_name: 'all', hours: new Array(24).fill(true), kings: allKingsKeys, badge: 'پایه', badge_bg: '#1e3a8a', badge_col: '#93c5fd' },
            { idx: 1, title: 'استراتژی پر سود (کف پتانسیل ۳ دلار)', desc: 'فیلتر معاملاتی با پتانسیل رشد بالا برای کاهش نویز بازار', min_pot: 3, sl_mode: 'none', count: p2.c, cnt: p2.c, wr: p2.wr, pf: p2.pf, avg: p2.avg, max_dd: p2.maxDD, net: p2.net, hours_str: '۲۴ ساعته', hours_name: 'all', hours: new Array(24).fill(true), kings: allKingsKeys, badge: 'پر سود', badge_bg: '#065f46', badge_col: '#6ee7b7' },
            { idx: 2, title: 'حذف ۳ سلطان با بیشترین استاپ (سپر ضد افت)', desc: 'حذف سلاطینی که بیشترین تعداد استاپ لاس را ایجاد کرده‌اند', min_pot: 0, sl_mode: 'top3_cnt', count: p3.c, cnt: p3.c, wr: p3.wr, pf: p3.pf, avg: p3.avg, max_dd: p3.maxDD, net: p3.net, hours_str: '۲۴ ساعته', hours_name: 'all', hours: new Array(24).fill(true), kings: kingsWithoutTop3, badge: 'سپر امنیتی', badge_bg: '#450a0a', badge_col: '#fca5a5' },
            { idx: 3, title: 'سشن‌های فعال لندن و نیویورک (۰۸ الی ۲۰)', desc: 'ترید انحصاری در ساعات با نقدینگی بالا و اسپرد پایین', min_pot: 0, sl_mode: 'none', count: p4.c, cnt: p4.c, wr: p4.wr, pf: p4.pf, avg: p4.avg, max_dd: p4.maxDD, net: p4.net, hours_str: '۰۸:۰۰ الی ۲۰:۰۰', hours_name: 'lon_ny', hours: londonNyHours, kings: allKingsKeys, badge: 'سشن لندن/نیویورک', badge_bg: '#312e81', badge_col: '#c7d2fe' },
            { idx: 4, title: 'سناریوی الماس متعادل (Balanced Golden)', desc: 'ترکیب کف سود ۱.۵ دلار، حذف استاپ‌های سنگین و فیوز ۲ استاپ', min_pot: 1.5, sl_mode: 'top3_cnt', count: p5.c, cnt: p5.c, wr: p5.wr, pf: p5.pf, avg: p5.avg, max_dd: p5.maxDD, net: p5.net, hours_str: '۰۸:۰۰ الی ۲۰:۰۰', hours_name: 'lon_ny', hours: londonNyHours, kings: kingsWithoutTop3, consec_trig: 2, consec_sk: 1, badge: 'الماس متعادل', badge_bg: '#713f12', badge_col: '#fde047', is_featured: true }
        ];

        // Format dates
        const minDate = validation.dateRange.start;
        const maxDate = validation.dateRange.end;
        const tfsStr = Array.from(validation.detectedTFs).sort().join(', ');

        const finalSymbolData = {
            symbol: detectedSym,
            min_date: minDate,
            max_date: maxDate,
            tfs_str: tfsStr,
            date_start_str: minDate,
            date_end_str: maxDate,
            bal_initial: AppConfig.defaultBalance || 10000,
            kings_sim_list: kingsSimList,
            top3_sl_cnt_keys: top3SLCntKeys,
            top3_sl_usd_keys: top3SLUsdKeys,
            top5_sl_usd_keys: top5SLUsdKeys,
            top3_sl_pct_keys: top3SLPctKeys,
            trades_sim_list: simTrades,
            trades_json_list: allTrades,
            weekly_bar_data: weeklyBarData,
            smart_presets: smartPresets,
            scaleout_summary: scaleoutSummary,
            timeframe_summary: Object.values(tfGroups),
            hourly_summary: hourGroups,
            daily_summary: dayGroups,
            validation_report: validation
        };

        return finalSymbolData;
    }

    return {
        processCSVData: processCSVData
    };
})();
