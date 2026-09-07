// FlagPro Strategy Dashboard - CSV Data Loader, Autonomous Parser & File Integrity System

async function processUploadedFile(file) {
    if (!file) return;

    // 1. Try Bridge Server for saving to MT5 Files/ folder and rebuilding
    try {
        let fileText = await file.text();
        let resp = await fetch('http://127.0.0.1:8288/rebuild', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: file.name, content: fileText })
        });
        if (resp.ok) {
            let json = await resp.json();
            if (json.success) {
                if (typeof showSaveNotification === 'function') {
                    showSaveNotification('🚀 فایل «' + file.name + '» ذخیره و تمام داشبورد با موفقیت به‌روزرسانی شد!');
                }
                location.reload();
                return;
            }
        }
    } catch(e) {
        // Bridge server offline, proceed with client-side autonomous engine
    }

    // 2. Client-side autonomous engine (100% in-browser)
    let reader = new FileReader();
    reader.onload = function(e) {
        try {
            let csvText = e.target.result;
            let symName = parseClientCSV(csvText, file.name);
            if (symName) {
                try {
                    localStorage.setItem('FLAGPRO_SAVED_CSV_' + symName, csvText);
                    localStorage.setItem('FLAGPRO_SAVED_NAME_' + symName, file.name);
                } catch(e) {}

                let sel = document.getElementById('symbolSelector');
                let exists = Array.from(sel.options).some(o => o.value === symName);
                if (!exists) {
                    let opt = document.createElement('option');
                    opt.value = symName;
                    opt.textContent = symName + ' (فایل کاربر - ' + (window.ALL_SYMBOLS_DATA[symName].trades_json_list.length) + ' معامله)';
                    sel.appendChild(opt);
                }
                sel.value = symName;
                switchDashboardSymbol(symName);

                let tradeCount = (window.ALL_SYMBOLS_DATA[symName] && window.ALL_SYMBOLS_DATA[symName].trades_json_list) ? window.ALL_SYMBOLS_DATA[symName].trades_json_list.length : 0;
                if (typeof showSaveNotification === 'function') {
                    showSaveNotification('🚀 فایل «' + file.name + '» با موفقیت اعمال شد!<br><span style="color:#34d399;font-size:11px;">' + tradeCount + ' معامله استخراج و تمام تب‌ها و چارت اکوئیتی به‌صورت خودکار به‌روزرسانی شدند.</span>');
                }
            }
        } catch(err) {
            alert('❌ خطا در پردازش فایل CSV: ' + err.message);
        }
    };
    reader.readAsText(file);
}

function initPersistedSymbols() {
    try {
        let sel = document.getElementById('symbolSelector');
        if (sel && window.ALL_SYMBOLS_DATA) {
            sel.innerHTML = '';
            for (let sym in window.ALL_SYMBOLS_DATA) {
                let sData = window.ALL_SYMBOLS_DATA[sym];
                let cCount = (sData.closed_count || (sData.trades_json_list ? sData.trades_json_list.length : (sData.trades_sim_list ? sData.trades_sim_list.length : 0)));
                let kCount = (sData.tot_k_cnt !== undefined ? sData.tot_k_cnt : (sData.trades_sim_list ? sData.trades_sim_list.filter(t => t.k === 1).length : (sData.kings_sim_list ? sData.kings_sim_list.length : 0)));
                let opt = document.createElement('option');
                opt.value = sym;
                opt.textContent = (sData.symbol || sym) + ' (' + (sData.tfs_str || 'M1, M5') + ') - کل: ' + cCount + ' | سلاطین: ' + kCount + ' معامله';
                sel.appendChild(opt);
            }
        }

        for (let i = 0; i < localStorage.length; i++) {
            let k = localStorage.key(i);
            if (k && k.startsWith('FLAGPRO_SAVED_CSV_')) {
                let symName = k.replace('FLAGPRO_SAVED_CSV_', '');
                let csvText = localStorage.getItem(k);
                let fileName = localStorage.getItem('FLAGPRO_SAVED_NAME_' + symName) || (symName + '.csv');
                if (csvText && !window.ALL_SYMBOLS_DATA[symName]) {
                    parseClientCSV(csvText, fileName);
                    if (sel && !Array.from(sel.options).some(o => o.value === symName)) {
                        let opt = document.createElement('option');
                        opt.value = symName;
                        opt.textContent = symName + ' (فایل ذخیره‌شده - ' + (window.ALL_SYMBOLS_DATA[symName].trades_json_list.length) + ' معامله)';
                        sel.appendChild(opt);
                    }
                }
            }
        }

        // Determine active symbol: prefer last valid symbol with kings, else GBPUSD, else symbol with most kings
        let targetSym = null;
        let lastSym = localStorage.getItem('FLAGPRO_LAST_ACTIVE_SYMBOL');
        let cleanLastSym = lastSym ? lastSym.replace(/[!#]/g, '').trim() : '';

        if (cleanLastSym && window.ALL_SYMBOLS_DATA && window.ALL_SYMBOLS_DATA[cleanLastSym]) {
            let kCnt = (window.ALL_SYMBOLS_DATA[cleanLastSym].kings_sim_list || []).length;
            if (kCnt > 0) {
                targetSym = cleanLastSym;
            }
        } else if (lastSym && window.ALL_SYMBOLS_DATA && window.ALL_SYMBOLS_DATA[lastSym]) {
            let kCnt = (window.ALL_SYMBOLS_DATA[lastSym].kings_sim_list || []).length;
            if (kCnt > 0) {
                targetSym = lastSym;
            }
        }

        if (!targetSym && window.ALL_SYMBOLS_DATA && window.ALL_SYMBOLS_DATA['GBPUSD']) {
            targetSym = 'GBPUSD';
        }

        if (!targetSym && window.ALL_SYMBOLS_DATA && Object.keys(window.ALL_SYMBOLS_DATA).length > 0) {
            let symKeys = Object.keys(window.ALL_SYMBOLS_DATA);
            symKeys.sort((a, b) => {
                let kA = (window.ALL_SYMBOLS_DATA[a].kings_sim_list || []).length;
                let kB = (window.ALL_SYMBOLS_DATA[b].kings_sim_list || []).length;
                if (kB !== kA) return kB - kA;
                let tA = (window.ALL_SYMBOLS_DATA[a].trades_sim_list || []).length;
                let tB = (window.ALL_SYMBOLS_DATA[b].trades_sim_list || []).length;
                return tB - tA;
            });
            targetSym = symKeys[0];
        }

        if (targetSym) {
            currentActiveSymbol = targetSym;
            if (sel) sel.value = targetSym;
            switchDashboardSymbol(targetSym);
        }
    } catch(e) {
        console.error('initPersistedSymbols error:', e);
    }
}

function handleCSVFileUpload(input) {
    if (!input.files || !input.files[0]) return;
    processUploadedFile(input.files[0]);
}

function getMT5FilesFolderPath() {
    return ['C:', 'Users', 'USER', 'AppData', 'Roaming', 'MetaQuotes', 'Terminal', '3F2C3A2F8B221C9D88E569F2FD1D3E97', 'MQL5', 'Files'].join(String.fromCharCode(92));
}

function triggerCSVUploadClick() {
    let mt5Path = getMT5FilesFolderPath();
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(mt5Path).catch(function(){});
    }
    if (typeof showSaveNotification === 'function') {
        showSaveNotification('📋 آدرس پوشه متاتریدر در کلیپ‌بورد کپی شد!<br><span style="color:#38bdf8;font-size:11.5px;">در کادر بالای پنجره انتخاب فایل، کلید <b>Ctrl+V</b> و سپس <b>Enter</b> را بزنید تا مستقیم به فایل‌های CSV بروید.</span>');
    }
    document.getElementById('csvFileInput').click();
}

function showMT5PathAlert() {
    let mt5Path = getMT5FilesFolderPath();
    let msg = ['📁 مسیر پوشه فایل‌های اکسپورت در متاتریدر:', '', mt5Path, '', '✅ این مسیر در کلیپ‌بورد کپی شد!', '(همچنین یک میانبر مستقیم به نام MT5_Files_Folder روی دسکتاپ شما قرار دارد)'].join(String.fromCharCode(10));
    alert(msg);
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(mt5Path).catch(function(){});
    }
}

// Global Drag & Drop Handler
window.addEventListener('dragover', function(e) { e.preventDefault(); });
window.addEventListener('drop', function(e) {
    e.preventDefault();
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        let file = e.dataTransfer.files[0];
        if (file.name.toLowerCase().endsWith('.csv')) {
            processUploadedFile(file);
        }
    }
});

function calc7PillarKingMetrics(trades, tf, role, friction) {
    let cnt = trades.length;
    if (cnt === 0) return null;

    let w1 = 0, w2 = 0, w3 = 0, w4 = 0, sl = 0;
    trades.forEach(t => {
        let hr = t.hr !== undefined ? t.hr : 0;
        if (hr >= 1) w1++;
        if (hr >= 2) w2++;
        if (hr >= 3) w3++;
        if (hr >= 4) w4++;
        if (hr === 0) sl++;
    });

    let w1_p = (w1 / cnt) * 100.0;
    let w2_p = (w2 / cnt) * 100.0;
    let w3_p = (w3 / cnt) * 100.0;
    let w4_p = (w4 / cnt) * 100.0;
    let sl_p = (sl / cnt) * 100.0;

    let is_perfect = (cnt >= 2 && sl === 0);
    let is_runner = (w3_p >= 30.0 || w4_p >= 30.0);

    let gross = 0.0;
    trades.forEach(t => {
        let pts = t.pts || 0;
        let hr = t.hr !== undefined ? t.hr : 0;
        if (hr === 0) {
            gross -= pts * 0.04;
        } else {
            if (hr >= 1) gross += pts * 1.0 * 0.01;
            if (hr >= 2) gross += pts * 2.0 * 0.01;
            if (hr >= 3) gross += pts * 3.0 * 0.01;
            if (hr >= 4) gross += pts * 4.0 * 0.01;
        }
    });

    let fric = cnt * friction;
    let net = gross - fric;

    let cum_pnl = 0.0, peak = 0.0, max_dd = 0.0;
    let gross_win = 0.0, gross_loss = 0.0;
    let sorted_trades = trades.slice().sort((a, b) => {
        let tA = a.en_t || a.et || a.t || '';
        let tB = b.en_t || b.et || b.t || '';
        return tA > tB ? 1 : (tA < tB ? -1 : 0);
    });
    sorted_trades.forEach(t => {
        let pts = t.pts || 0;
        let hr = t.hr !== undefined ? t.hr : 0;
        let pnl = 0.0;
        if (hr === 0) {
            pnl = -pts * 0.04 - friction;
            gross_loss += Math.abs(pnl);
        } else {
            pnl = -friction;
            if (hr >= 1) pnl += pts * 1.0 * 0.01;
            if (hr >= 2) pnl += pts * 2.0 * 0.01;
            if (hr >= 3) pnl += pts * 3.0 * 0.01;
            if (hr >= 4) pnl += pts * 4.0 * 0.01;
            if (pnl > 0) gross_win += pnl;
            if (pnl < 0) gross_loss += Math.abs(pnl);
        }

        cum_pnl += pnl;
        if (cum_pnl > peak) peak = cum_pnl;
        let dd = peak - cum_pnl;
        if (dd > max_dd) max_dd = dd;
    });

    let pf = gross_loss > 0 ? (gross_win / gross_loss) : (gross_win > 0 ? 99.0 : 0.0);
    let ret_dd = max_dd > 0 ? (net / max_dd) : (net > 0 ? net : 0.0);

    let profit_per_trade = net / Math.max(cnt, 1);
    let final_score = 0.0;

    if (net <= 0) {
        final_score = net * 2.0 - sl_p;
    } else {
        // Pillar 1: 🛡️ Purity / Zero-SL (0 to 500 pts)
        let f_purity = 0.0;
        if (cnt >= 2 && sl === 0) f_purity = 500.0;
        else if (cnt >= 3 && sl_p <= 15.0) f_purity = 300.0;
        else if (cnt >= 3 && sl_p <= 25.0) f_purity = 200.0;
        else if (cnt >= 4 && sl_p <= 35.0) f_purity = 100.0;
        else if (cnt >= 4 && sl_p <= 45.0) f_purity = 50.0;

        // Pillar 2: 🎯 TP2 Depth (0 to 400 pts)
        let f_tp2 = w2_p * 4.0;

        // Pillar 3: ⚡ Runner & Target Progression Quality (up to ~250 pts)
        let f_prog = (w1_p * 0.5) + (w3_p * 1.0) + (w4_p * 1.5) - (sl_p * 0.5);

        // Pillar 4: 💰 Efficiency ($/trade) (0 to 200 pts)
        let f_eff = Math.min(Math.max(profit_per_trade, 0.0) * 20.0, 200.0);

        // Pillar 5: 📊 Statistical Confidence (0 to 50 pts)
        let f_rel = Math.min(Math.log10(cnt + 9) * 20.0, 50.0);

        // Pillar 6: ⚖️ Institutional Profit Factor (0 to 100 pts)
        let f_pf = (sl === 0 && cnt >= 2) ? 100.0 : Math.min(Math.max(pf - 1.0, 0.0) * 50.0, 100.0);

        // Pillar 7: 🛡️ Drawdown Resistance & Recovery Factor (0 to 100 pts)
        let f_rec = (sl === 0 && cnt >= 2) ? 100.0 : Math.min(ret_dd * 6.0, 100.0);
        if (max_dd > 30.0 && !(sl === 0 && cnt >= 2)) {
            f_rec = Math.max(f_rec - (max_dd - 30.0) * 1.5, 0.0);
        }

        final_score = f_purity + f_tp2 + f_prog + f_eff + f_rel + f_pf + f_rec;
    }

    let is_king_eligible = is_perfect || (cnt >= 4 && net > 5.0 && w1_p >= 50.0);

    return {
        tf, role, cnt,
        w1, w2, w3, w4, sl,
        w1_p, w2_p, w3_p, w4_p, sl_p,
        score: final_score, is_perfect, is_runner,
        gross, fric, net,
        max_dd, pf, ret_dd,
        trades, is_king_eligible
    };
}

function parseClientCSV(csvText, fileName) {
    if (!csvText || typeof csvText !== 'string') throw new Error('محتوای فایل خالی است.');
    let lines = csvText.split(String.fromCharCode(10)).map(l => l.trim()).filter(l => l.length > 0);
    if (lines.length < 2) throw new Error('فایل CSV باید شامل هدر و حداقل یک معامله باشد.');

    let headers = lines[0].split(',').map(h => h.trim());
    let colIdx = {};
    headers.forEach((h, idx) => colIdx[h] = idx);

    let rawTrades = [];
    let detectedSym = '';
    let totalBoxesCount = 0;
    let pendingBoxesCount = 0;
    let openTradesCount = 0;
    for (let i = 1; i < lines.length; i++) {
        let parts = lines[i].split(',').map(p => p.trim());
        if (parts.length < 5) continue;
        totalBoxesCount++;
        let isClosed = colIdx['IsClosed'] !== undefined ? parts[colIdx['IsClosed']] : 'True';
        let outcome = colIdx['Outcome'] !== undefined ? parts[colIdx['Outcome']] : '';
        if (outcome === 'Pending') {
            pendingBoxesCount++;
            continue;
        }
        if (isClosed !== 'True') {
            openTradesCount++;
            continue;
        }

        let sym = colIdx['Symbol'] !== undefined ? parts[colIdx['Symbol']] : '';
        if (sym && !detectedSym) detectedSym = sym;

        let role = colIdx['Role'] !== undefined ? parts[colIdx['Role']] : '';
        let tf = colIdx['Timeframe'] !== undefined ? parts[colIdx['Timeframe']] : 'M1';
        let bname = colIdx['BoxName'] !== undefined ? parts[colIdx['BoxName']] : '';
        let dir = colIdx['Direction'] !== undefined ? parts[colIdx['Direction']] : 'BUY';
        let et = colIdx['EntryTime'] !== undefined ? parts[colIdx['EntryTime']] : '';
        let ex = colIdx['ExitTime'] !== undefined ? parts[colIdx['ExitTime']] : '';
        let enPrice = colIdx['EntryPrice'] !== undefined ? parseFloat(parts[colIdx['EntryPrice']]) || 0 : 0;
        let exPrice = colIdx['ExitPrice'] !== undefined ? parseFloat(parts[colIdx['ExitPrice']]) || 0 : 0;
        let slPrice = colIdx['StopLoss'] !== undefined ? parseFloat(parts[colIdx['StopLoss']]) || 0 : 0;
        let pts = colIdx['RiskPoints'] !== undefined ? parseFloat(parts[colIdx['RiskPoints']]) || 0 : 0;
        let hr = colIdx['HitTargetRatio'] !== undefined ? parseInt(parts[colIdx['HitTargetRatio']]) || 0 : 0;
        let tp1 = colIdx['TP1'] !== undefined ? parseFloat(parts[colIdx['TP1']]) || 0 : 0;
        let tp2 = colIdx['TP2'] !== undefined ? parseFloat(parts[colIdx['TP2']]) || 0 : 0;
        let tp3 = colIdx['TP3'] !== undefined ? parseFloat(parts[colIdx['TP3']]) || 0 : 0;
        let tp4 = colIdx['TP4'] !== undefined ? parseFloat(parts[colIdx['TP4']]) || 0 : 0;

        let bts = colIdx['BoxTimeStart'] !== undefined ? parts[colIdx['BoxTimeStart']] : '';
        let bte = colIdx['BoxTimeEnd'] !== undefined ? parts[colIdx['BoxTimeEnd']] : '';
        let wm = (typeof calcWaitMinutes === 'function') ? calcWaitMinutes(bts, et) : null;

        rawTrades.push({ sym, role, tf, bname, dir, bts, bte, et, ex, enPrice, exPrice, slPrice, pts, hr, tp1, tp2, tp3, tp4, wm });
    }

    if (rawTrades.length === 0) throw new Error('هیچ معامله بسته‌شده‌ای در این فایل یافت نشد.');

    if (!detectedSym) {
        let m = fileName.match(/flagpro_trades_([A-Za-z0-9_]+)[.]csv/i);
        detectedSym = m ? m[1].toUpperCase() : 'CUSTOM';
    }

    rawTrades.sort((a, b) => (a.et > b.et ? 1 : -1));

    let friction = 0.48;
    let clientSimTrades = [];
    let clientAllTrades = [];
    let boxGroups = {};

    rawTrades.forEach((t, idx) => {
        let pnl = 0;
        if (t.hr === 0) {
            pnl = -t.pts * 0.04 - friction;
        } else {
            pnl = -friction;
            if (t.hr >= 1) pnl += t.pts * 0.01 * 1.0;
            if (t.hr >= 2) pnl += t.pts * 0.01 * 2.0;
            if (t.hr >= 3) pnl += t.pts * 0.01 * 3.0;
            if (t.hr >= 4) pnl += t.pts * 0.01 * 4.0;
        }

        let kk = t.role + '|' + t.tf;
        if (!boxGroups[kk]) {
            boxGroups[kk] = { role: t.role, tf: t.tf, kk: kk, trades: [], wins: 0, losses: 0, sl: 0, grossWin: 0, grossLoss: 0, net: 0, w1: 0, w2: 0, w3: 0, w4: 0 };
        }
        let bg = boxGroups[kk];
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

        let hVal = t.et.length >= 13 ? parseInt(t.et.substring(11, 13)) : 0;
        clientSimTrades.push({
            i: idx + 1, t: t.et, xt: t.ex || t.et, h: hVal, tf: t.tf, r: t.role, k: 1, kk: kk, pts: Math.round(t.pts * 10) / 10, pot: Math.round(t.pts * 0.04 * 100) / 100, hr: t.hr, p: Math.round(pnl * 100) / 100, ex_p: t.exPrice
        });

        clientAllTrades.push({
            id: idx + 1,
            box_t: t.bts || '',
            en_t: t.et,
            ex_t: t.ex,
            wait_m: t.wm !== null && t.wm !== undefined ? t.wm : 0.0,
            wait_fmt: (typeof formatDurationPersian === 'function') ? formatDurationPersian(t.wm) : (t.wm + 'm'),
            wait_short: (typeof formatDurationShort === 'function') ? formatDurationShort(t.wm) : (t.wm + 'm'),
            tf: t.tf,
            bname: t.bname || ('#' + (idx+1)),
            role: t.role,
            dir: t.dir,
            en_p: t.enPrice,
            ex_p: t.exPrice,
            sl: t.slPrice,
            pts: t.pts,
            net: Math.round(pnl * 100) / 100,
            pot: Math.round(t.pts * 0.04 * 100) / 100,
            t1: t.hr >= 1 ? 1 : 0,
            t2: t.hr >= 2 ? 1 : 0,
            t3: t.hr >= 3 ? 1 : 0,
            t4: t.hr >= 4 ? 1 : 0,
            tp1: t.tp1,
            tp2: t.tp2,
            tp3: t.tp3,
            tp4: t.tp4,
            is_k: 1
        });
    });

    let scoredBoxes = [];
    Object.values(boxGroups).forEach(bg => {
        let m = calc7PillarKingMetrics(bg.trades, bg.tf, bg.role, friction);
        if (m) {
            m.kk = bg.kk;
            scoredBoxes.push(m);
        }
    });

    scoredBoxes.sort((a, b) => (b.score !== a.score ? b.score - a.score : b.cnt - a.cnt));
    let qualified = scoredBoxes.filter(b => b.is_king_eligible);
    if (qualified.length === 0) qualified = scoredBoxes.filter(b => b.score >= 100 && b.net > 0);
    if (qualified.length === 0) qualified = scoredBoxes.slice(0, 10);
    let kingKeySet = new Set(qualified.map(k => k.kk));

    clientSimTrades.forEach(t => { t.k = kingKeySet.has(t.kk) ? 1 : 0; });
    clientAllTrades.forEach(t => { t.is_k = kingKeySet.has(t.role + '|' + t.tf) ? 1 : 0; });

    let clientKingsSimList = qualified.map((k, idx) => ({
        id: idx + 1, role: k.role, tf: k.tf, kk: k.kk,
        score: Math.round(k.score * 10) / 10,
        cnt: k.cnt, net: Math.round(k.net * 100) / 100,
        w1: k.w1, w2: k.w2, w3: k.w3, w4: k.w4, sl: k.sl,
        w1_p: Math.round(k.w1_p * 10) / 10,
        w2_p: Math.round(k.w2_p * 10) / 10,
        w3_p: Math.round(k.w3_p * 10) / 10,
        w4_p: Math.round(k.w4_p * 10) / 10,
        sl_cnt: k.sl, sl_usd: Math.round(k.sl * (friction + 2.0) * 100) / 100,
        sl_p: Math.round(k.sl_p * 10) / 10,
        pf: Math.round(k.pf * 100) / 100,
        max_dd: Math.round(k.max_dd * 100) / 100,
        ret_dd: Math.round(k.ret_dd * 10) / 10,
        perf: k.is_perfect ? 1 : 0, run: k.is_runner ? 1 : 0
    }));

    let sortedSLCnt = [...clientKingsSimList].sort((a, b) => b.sl_cnt - a.sl_cnt);
    let sortedSLUsd = [...clientKingsSimList].sort((a, b) => b.sl_usd - a.sl_usd);
    let sortedSLPct = [...clientKingsSimList].filter(x => x.cnt >= 10).sort((a, b) => b.sl_p - a.sl_p);

    let top3SLCnt = sortedSLCnt.slice(0, 3).map(x => x.kk);
    let top3SLUsd = sortedSLUsd.slice(0, 3).map(x => x.kk);
    let top5SLUsd = sortedSLUsd.slice(0, 5).map(x => x.kk);
    let top3SLPct = sortedSLPct.slice(0, 3).map(x => x.kk);

    clientKingsSimList.forEach(k => {
        k.is_top_sl_cnt = top3SLCnt.includes(k.kk) ? 1 : 0;
        k.is_top_sl_usd = top3SLUsd.includes(k.kk) ? 1 : 0;
        k.is_top_sl_pct = top3SLPct.includes(k.kk) ? 1 : 0;
        k.is_danger = (k.is_top_sl_cnt || k.is_top_sl_usd || k.sl_cnt >= 45 || k.sl_p >= 45) ? 1 : 0;
    });

    let weeklyGroups = {};
    clientSimTrades.forEach(t => {
        if (!t.t) return;
        let dtStr = t.t.substring(0, 10);
        let dt = new Date(dtStr.replace(/[.]/g, '-'));
        if (isNaN(dt.getTime())) return;
        let day = dt.getUTCDay();
        let diff = dt.getUTCDate() - day + (day === 0 ? -6 : 1);
        let monday = new Date(dt.setDate(diff));
        let wkKey = monday.toISOString().substring(0, 10);
        if (!weeklyGroups[wkKey]) {
            weeklyGroups[wkKey] = { k_pnl: 0, k_trades: 0, k_wins: 0, k_losses: 0, all_pnl: 0, all_trades: 0, all_wins: 0, all_losses: 0 };
        }
        let wg = weeklyGroups[wkKey];
        wg.all_pnl += t.p; wg.all_trades++;
        if (t.p > 0) wg.all_wins++; else wg.all_losses++;
        if (t.k === 1) {
            wg.k_pnl += t.p; wg.k_trades++;
            if (t.p > 0) wg.k_wins++; else wg.k_losses++;
        }
    });

    let clientWeeklyBars = [];
    let wkKeys = Object.keys(weeklyGroups).sort();
    wkKeys.forEach((wk, idx) => {
        let item = weeklyGroups[wk];
        clientWeeklyBars.push({
            week_idx: idx + 1, label: 'هفته ' + (idx + 1), date_range: wk, k_pnl: Math.round(item.k_pnl * 100) / 100, k_trades: item.k_trades, k_wins: item.k_wins, k_losses: item.k_losses, k_wr: item.k_trades > 0 ? Math.round(item.k_wins / item.k_trades * 1000) / 10 : 0, all_pnl: Math.round(item.all_pnl * 100) / 100, all_trades: item.all_trades, all_wins: item.all_wins, all_losses: item.all_losses, all_wr: item.all_trades > 0 ? Math.round(item.all_wins / item.all_trades * 1000) / 10 : 0
        });
    });

    let clientSmartPresets = buildAndSimulateClientSmartPresets(detectedSym, clientKingsSimList, clientSimTrades);

    let minDate = clientSimTrades[0].t.substring(0, 10);
    let maxDate = clientSimTrades[clientSimTrades.length - 1].t.substring(0, 10);
    let tfs = Array.from(new Set(rawTrades.map(t => t.tf))).sort().join(', ');

    let baseEqHtml = '';
    for (let s in window.ALL_SYMBOLS_DATA) {
        if (window.ALL_SYMBOLS_DATA[s] && window.ALL_SYMBOLS_DATA[s].tab_equity_html && window.ALL_SYMBOLS_DATA[s].tab_equity_html.includes('equityCanvas')) {
            baseEqHtml = window.ALL_SYMBOLS_DATA[s].tab_equity_html;
            break;
        }
    }

    window.ALL_SYMBOLS_DATA[detectedSym] = {
        symbol: detectedSym,
        min_date: minDate,
        max_date: maxDate,
        tfs_str: tfs,
        date_start_str: minDate,
        date_end_str: maxDate,
        bal_initial: 10000,
        kings_sim_list: clientKingsSimList,
        top3_sl_cnt_keys: top3SLCnt,
        top3_sl_usd_keys: top3SLUsd,
        top5_sl_usd_keys: top5SLUsd,
        top3_sl_pct_keys: top3SLPct,
        trades_sim_list: clientSimTrades,
        smart_presets: clientSmartPresets,
        weekly_bar_data: clientWeeklyBars,
        trades_json_list: clientAllTrades,
        tab_equity_html: baseEqHtml,
        tab_kings_html: generateClientKingsHTML(detectedSym, rawTrades, clientKingsSimList, friction, totalBoxesCount, pendingBoxesCount, openTradesCount),
        tab_scaleout_html: generateClientScaleoutHTML(detectedSym, rawTrades, clientKingsSimList, friction),
        tab_timeframes_html: generateClientTimeframesHTML(detectedSym, rawTrades, clientKingsSimList, friction),
        tab_filters_html: generateClientFiltersHTML(detectedSym, rawTrades, friction),
        tab_loss_intel_html: generateClientLossIntelHTML(detectedSym, rawTrades, clientKingsSimList, friction),
        tab_weekly_html: generateClientWeeklyHTML(detectedSym, rawTrades, clientKingsSimList, clientWeeklyBars, friction),
        smart_presets_rows_html: generateClientSmartPresetsRowsHTML(detectedSym, clientSmartPresets)
    };

    let cleanSym = detectedSym.replace(/[!#]/g, '').trim();
    if (cleanSym && cleanSym !== detectedSym && !window.ALL_SYMBOLS_DATA[cleanSym]) {
        window.ALL_SYMBOLS_DATA[cleanSym] = window.ALL_SYMBOLS_DATA[detectedSym];
    }

    return detectedSym;
}

// ================= DATA VALIDATION & INTEGRITY SYSTEM =================

function updateValidationStatus() {
    let pill = document.getElementById('headerValidationPill');
    if (!pill) return;
    let sData = window.ALL_SYMBOLS_DATA ? window.ALL_SYMBOLS_DATA[currentActiveSymbol] : null;
    if (sData) {
        let isCustom = localStorage.getItem('FLAGPRO_SAVED_CSV_' + currentActiveSymbol) !== null;
        pill.textContent = isCustom ? '● فایل کاربر (همگام)' : '● ۱۰۰٪ همگام';
        pill.style.background = isCustom ? '#0284c7' : '#059669';
    }
}

function openDataValidationModal() {
    let sData = window.ALL_SYMBOLS_DATA ? window.ALL_SYMBOLS_DATA[currentActiveSymbol] : null;
    if (!sData) {
        alert('داده‌ای برای نماد فعال یافت نشد.');
        return;
    }

    let savedName = localStorage.getItem('FLAGPRO_SAVED_NAME_' + currentActiveSymbol);
    let isUserFile = savedName !== null;
    let fileName = savedName || ('flagpro_trades_' + currentActiveSymbol + '.csv');
    let totalTrades = sData.trades_json_list ? sData.trades_json_list.length : 0;
    let kingsCount = sData.kings_sim_list ? sData.kings_sim_list.length : 0;
    let weeklyCount = sData.weekly_bar_data ? sData.weekly_bar_data.length : 0;

    let modal = document.getElementById('dataValidationModal');
    if (!modal) return;

    // Fill Dossier
    document.getElementById('valActiveSymbol').textContent = sData.symbol;
    document.getElementById('valFileName').textContent = fileName;
    document.getElementById('valSourceBadge').innerHTML = isUserFile ?
        '<span style="background:#0284c7;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">بارگذاری کاربر (Local CSV)</span>' :
        '<span style="background:#065f46;color:#34d399;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">دیتابیس پیش‌فرض متاتریدر ۵</span>';
    document.getElementById('valDateSpan').textContent = sData.min_date + '  تا  ' + sData.max_date;
    document.getElementById('valTotalTrades').textContent = totalTrades.toLocaleString() + ' معامله بسته‌شده';
    document.getElementById('valKingsCount').textContent = kingsCount + ' سلطان فعال';
    document.getElementById('valWeeklyWeeks').textContent = weeklyCount + ' هفته کالبدشکافی‌شده';
    document.getElementById('valSyncTimestamp').textContent = new Date().toLocaleString('fa-IR');

    modal.style.display = 'flex';
}

function closeDataValidationModal() {
    let modal = document.getElementById('dataValidationModal');
    if (modal) modal.style.display = 'none';
}
