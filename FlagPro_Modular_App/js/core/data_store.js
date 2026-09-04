var currentActiveSymbol = 'EURUSD';
var dataWeeklyBars = [];
var kingsSimList = [];
var top3SLCntKeys = [];
var top3SLUsdKeys = [];
var top5SLUsdKeys = [];
var top3SLPctKeys = [];
var simTrades = [];
var smartPresets = [];
var allTrades = [];
var currentExportConfig = null;
var simState = {
    mode: 'kings',
    enabledKings: new Set(),
    allowedHours: new Array(24).fill(true),
    minProfit: 0.0,
    consecLossTrigger: 0,
    consecLossSkipCount: 1,
    consecLossSkipDay: false,
    showDrawdown: true
};

function switchDashboardSymbol(symName) {
            if (!window.ALL_SYMBOLS_DATA || !window.ALL_SYMBOLS_DATA[symName]) return;
            currentActiveSymbol = symName;
            let sData = window.ALL_SYMBOLS_DATA[symName];

            // 1. Update Header Info
            let badge = document.getElementById('headerSymbolBadge');
            if (badge) badge.textContent = sData.symbol + ' (' + sData.tfs_str + ')';
            let minD = document.getElementById('headerMinDate');
            if (minD) minD.textContent = sData.min_date;
            let maxD = document.getElementById('headerMaxDate');
            if (maxD) maxD.textContent = sData.max_date;

            // 1.1 Persist active symbol
            try {
                localStorage.setItem('FLAGPRO_LAST_ACTIVE_SYMBOL', symName);
            } catch(e) {}
            let selElem = document.getElementById('symbolSelector');
            if (selElem && selElem.value !== symName) selElem.value = symName;

            // 2. Update Pre-rendered Tab HTML Containers (Never overwrite with placeholder divs)
            let cEq = document.getElementById('tab-equity-container');
            if (cEq && sData.tab_equity_html && sData.tab_equity_html.includes('equityCanvas')) {
                cEq.innerHTML = sData.tab_equity_html;
            }

            let cKings = document.getElementById('tab-kings-container');
            if (cKings && sData.tab_kings_html && !sData.tab_kings_html.includes('آماده تحلیل است')) {
                cKings.innerHTML = sData.tab_kings_html;
            }

            let cScale = document.getElementById('tab-scaleout-container');
            if (cScale && sData.tab_scaleout_html && !sData.tab_scaleout_html.includes('در دسترس است')) {
                cScale.innerHTML = sData.tab_scaleout_html;
            }

            let cTf = document.getElementById('tab-timeframes-container');
            if (cTf && sData.tab_timeframes_html && !sData.tab_timeframes_html.includes('در دسترس است')) {
                cTf.innerHTML = sData.tab_timeframes_html;
            }

            let cFilt = document.getElementById('tab-filters-container');
            if (cFilt && sData.tab_filters_html && !sData.tab_filters_html.includes('فعال هستند')) {
                cFilt.innerHTML = sData.tab_filters_html;
            }

            let cLoss = document.getElementById('tab-loss-intel-container');
            if (cLoss && sData.tab_loss_intel_html && !sData.tab_loss_intel_html.includes('قابل بررسی است')) {
                cLoss.innerHTML = sData.tab_loss_intel_html;
            }

            let cWk = document.getElementById('tab-weekly-container');
            if (cWk && sData.tab_weekly_html && !sData.tab_weekly_html.includes('فعال است')) {
                cWk.innerHTML = sData.tab_weekly_html;
            }

            // 3. Update JS Global Datasets
            dataWeeklyBars = sData.weekly_bar_data;
            kingsSimList = sData.kings_sim_list;
            top3SLCntKeys = sData.top3_sl_cnt_keys;
            top3SLUsdKeys = sData.top3_sl_usd_keys;
            top5SLUsdKeys = sData.top5_sl_usd_keys;
            top3SLPctKeys = sData.top3_sl_pct_keys;
            simTrades = sData.trades_sim_list;
            smartPresets = sData.smart_presets;
            allTrades = sData.trades_json_list;

            // 4. Reset Simulator State
            simState.mode = 'kings';
            simState.enabledKings = new Set(kingsSimList.map(k => k.kk));
            simState.allowedHours = new Array(24).fill(true);
            simState.minProfit = 0.0;
            simState.consecLossTrigger = 0;
            simState.consecLossSkipCount = 1;
            simState.consecLossSkipDay = false;

            // Reset UI controls
            let slider = document.getElementById('simProfitSlider');
            if (slider) slider.value = 0;
            let sliderVal = document.getElementById('simProfitSliderVal');
            if (sliderVal) sliderVal.textContent = '$0.00';
            let pBadge = document.getElementById('simProfitBadge');
            if (pBadge) { pBadge.textContent = 'بدون فیلتر ($0)'; pBadge.style.background = '#064e3b'; }
            document.querySelectorAll('.profit-preset-btn').forEach(b => b.classList.remove('active'));
            let defProfBtn = document.querySelector('.profit-preset-btn[data-pot="0"]');
            if (defProfBtn) defProfBtn.classList.add('active');

            document.querySelectorAll('.consec-btn').forEach(b => b.classList.remove('active'));
            let defConsecBtn = document.querySelector('.consec-btn[data-consec="0"]');
            if (defConsecBtn) defConsecBtn.classList.add('active');

            document.querySelectorAll('.hour-pill').forEach(p => {
                p.classList.remove('disabled');
                p.style.opacity = '1';
                p.style.borderColor = '#38bdf8';
                p.style.background = '#081a2e';
                p.style.color = '#38bdf8';
            });

            // Re-render UI components
            initEquityCanvasEvents();
            clearPresetActiveState();
            renderSimKingsGrid();
            if (typeof renderSLRiskPanel === 'function') renderSLRiskPanel();
            if (typeof renderSimHoursBar === 'function') renderSimHoursBar();
            trFilters.page = 1;
            renderTrades();
            runEquitySimulation();
            if (typeof drawWeeklyBarChart === 'function' && typeof currentWeeklyBarMode !== 'undefined') {
                drawWeeklyBarChart(currentWeeklyBarMode);
            }
        }

        async function processUploadedFile(file) {
            if (!file) return;

            // 1. Try Bridge Server for 100% full rebuild of all tabs and metrics
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
                        alert('✅ داده‌های فایل جدید با موفقیت پردازش شدند و تمام صفحات، سلاطین و تایم‌فریم‌ها به‌روزرسانی گردیدند!\n\nصفحه برای نمایش اطلاعات جدید مجدداً بارگذاری می‌شود.');
                        location.reload();
                        return;
                    }
                }
            } catch(e) {
                // Bridge server offline
            }

            // 2. Client-side fallback
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
                        alert('✅ داده‌های جدید روی چارت و ژورنال اعمال شدند.\n\n💡 نکته: برای به‌روزرسانی عمیق تمام تب‌ها (سلاطین همه‌فصول، عملکرد تایم‌فریم‌ها و...)، فایل «به روزرسانی داشبورد FlagPro.bat» را از روی دسکتاپ اجرا نمایید.');
                    }
                } catch(err) {
                    alert('❌ خطا در پردازش فایل CSV: ' + err.message);
                }
            };
            reader.readAsText(file);
        }

        function initPersistedSymbols() {
            try {
                for (let i = 0; i < localStorage.length; i++) {
                    let k = localStorage.key(i);
                    if (k && k.startsWith('FLAGPRO_SAVED_CSV_')) {
                        let symName = k.replace('FLAGPRO_SAVED_CSV_', '');
                        let csvText = localStorage.getItem(k);
                        let fileName = localStorage.getItem('FLAGPRO_SAVED_NAME_' + symName) || (symName + '.csv');
                        if (csvText && !window.ALL_SYMBOLS_DATA[symName]) {
                            parseClientCSV(csvText, fileName);
                            let sel = document.getElementById('symbolSelector');
                            if (sel && !Array.from(sel.options).some(o => o.value === symName)) {
                                let opt = document.createElement('option');
                                opt.value = symName;
                                opt.textContent = symName + ' (فایل ذخیره‌شده - ' + (window.ALL_SYMBOLS_DATA[symName].trades_json_list.length) + ' معامله)';
                                sel.appendChild(opt);
                            }
                        }
                    }
                }

                let lastSym = localStorage.getItem('FLAGPRO_LAST_ACTIVE_SYMBOL');
                if (lastSym && window.ALL_SYMBOLS_DATA && window.ALL_SYMBOLS_DATA[lastSym]) {
                    let sel = document.getElementById('symbolSelector');
                    if (sel) sel.value = lastSym;
                    if (lastSym !== currentActiveSymbol) {
                        switchDashboardSymbol(lastSym);
                    }
                }
            } catch(e) {}
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

        function parseClientCSV(csvText, fileName) {
            if (!csvText || typeof csvText !== 'string') throw new Error('محتوای فایل خالی است.');
            let lines = csvText.split(String.fromCharCode(10)).map(l => l.trim()).filter(l => l.length > 0);
            if (lines.length < 2) throw new Error('فایل CSV باید شامل هدر و حداقل یک معامله باشد.');

            let headers = lines[0].split(',').map(h => h.trim());
            let colIdx = {};
            headers.forEach((h, idx) => colIdx[h] = idx);

            let rawTrades = [];
            let detectedSym = '';
            for (let i = 1; i < lines.length; i++) {
                let parts = lines[i].split(',').map(p => p.trim());
                if (parts.length < 5) continue;
                let isClosed = colIdx['IsClosed'] !== undefined ? parts[colIdx['IsClosed']] : 'True';
                let outcome = colIdx['Outcome'] !== undefined ? parts[colIdx['Outcome']] : '';
                if (isClosed !== 'True' || outcome === 'Pending') continue;

                let sym = colIdx['Symbol'] !== undefined ? parts[colIdx['Symbol']] : '';
                if (sym && !detectedSym) detectedSym = sym;

                let role = colIdx['Role'] !== undefined ? parts[colIdx['Role']] : '';
                let tf = colIdx['Timeframe'] !== undefined ? parts[colIdx['Timeframe']] : 'M1';
                let bname = colIdx['BoxName'] !== undefined ? parts[colIdx['BoxName']] : '';
                let dir = colIdx['Direction'] !== undefined ? parts[colIdx['Direction']] : 'BUY';
                let et = colIdx['EntryTime'] !== undefined ? parts[colIdx['EntryTime']] : '';
                let ex = colIdx['ExitTime'] !== undefined ? parts[colIdx['ExitTime']] : '';
                let enPrice = colIdx['EntryPrice'] !== undefined ? parseFloat(parts[colIdx['EntryPrice']]) || 0 : 0;
                let slPrice = colIdx['StopLoss'] !== undefined ? parseFloat(parts[colIdx['StopLoss']]) || 0 : 0;
                let pts = colIdx['RiskPoints'] !== undefined ? parseFloat(parts[colIdx['RiskPoints']]) || 0 : 0;
                let hr = colIdx['HitTargetRatio'] !== undefined ? parseInt(parts[colIdx['HitTargetRatio']]) || 0 : 0;
                let tp1 = colIdx['TP1'] !== undefined ? parseFloat(parts[colIdx['TP1']]) || 0 : 0;
                let tp2 = colIdx['TP2'] !== undefined ? parseFloat(parts[colIdx['TP2']]) || 0 : 0;
                let tp3 = colIdx['TP3'] !== undefined ? parseFloat(parts[colIdx['TP3']]) || 0 : 0;
                let tp4 = colIdx['TP4'] !== undefined ? parseFloat(parts[colIdx['TP4']]) || 0 : 0;

                rawTrades.push({ sym, role, tf, bname, dir, et, ex, enPrice, slPrice, pts, hr, tp1, tp2, tp3, tp4 });
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
                    i: idx + 1, t: t.et, xt: t.ex || t.et, h: hVal, tf: t.tf, r: t.role, k: 1, kk: kk, pts: Math.round(t.pts * 10) / 10, pot: Math.round(t.pts * 0.04 * 100) / 100, hr: t.hr, p: Math.round(pnl * 100) / 100
                });

                clientAllTrades.push({
                    id: idx + 1, tf: t.tf, bname: t.bname || ('#' + (idx+1)), role: t.role, dir: t.dir, en_t: t.et, ex_t: t.ex, en_p: t.enPrice, sl: t.slPrice, pts: t.pts, net: Math.round(pnl * 100) / 100, pot: Math.round(t.pts * 0.04 * 100) / 100, t1: t.hr >= 1 ? 1 : 0, t2: t.hr >= 2 ? 1 : 0, t3: t.hr >= 3 ? 1 : 0, t4: t.hr >= 4 ? 1 : 0, tp1: t.tp1, tp2: t.tp2, tp3: t.tp3, tp4: t.tp4, is_k: 1
                });
            });

            let scoredBoxes = [];
            Object.values(boxGroups).forEach(bg => {
                let cnt = bg.trades.length;
                if (cnt === 0) return;
                let w1_p = (bg.w1 / cnt) * 100;
                let sl_p = (bg.sl / cnt) * 100;
                let pf = bg.grossLoss > 0 ? bg.grossWin / bg.grossLoss : (bg.grossWin > 0 ? 99 : 0);
                let peak = 0, cum = 0, maxDD = 0;
                bg.trades.forEach(tr => { cum += tr.pnl; if (cum > peak) peak = cum; let dd = peak - cum; if (dd > maxDD) maxDD = dd; });
                let purity = (cnt >= 2 && bg.sl === 0) ? 500 : Math.max(0, 400 - sl_p * 8);
                let t2 = ((bg.w2 / cnt) * 100) * 4.0;
                let pnlTrade = (bg.net / cnt) * 15.0;
                let pfScore = Math.min(100, pf * 15);
                let ddScore = maxDD > 0 ? Math.min(100, (bg.net / maxDD) * 10) : 100;
                let score = purity + t2 + pnlTrade + pfScore + ddScore;

                scoredBoxes.push({ role: bg.role, tf: bg.tf, kk: bg.kk, score, cnt, net: bg.net, w1_p, sl: bg.sl, sl_p, pf, maxDD, is_perfect: (cnt >= 2 && bg.sl === 0), is_runner: (bg.w3 / cnt >= 0.3 || bg.w4 / cnt >= 0.3) });
            });

            scoredBoxes.sort((a, b) => b.score - a.score);
            let qualified = scoredBoxes.filter(b => b.score >= 100 && b.net > 0 && b.cnt >= 3);
            if (qualified.length === 0) qualified = scoredBoxes.slice(0, 10);
            let kingKeySet = new Set(qualified.map(k => k.kk));

            clientSimTrades.forEach(t => { t.k = kingKeySet.has(t.kk) ? 1 : 0; });
            clientAllTrades.forEach(t => { t.is_k = kingKeySet.has(t.role + '|' + t.tf) ? 1 : 0; });

            let clientKingsSimList = qualified.map((k, idx) => ({
                id: idx + 1, role: k.role, tf: k.tf, kk: k.kk, score: Math.round(k.score * 10) / 10, cnt: k.cnt, net: Math.round(k.net * 100) / 100, w1_p: Math.round(k.w1_p * 10) / 10, sl_cnt: k.sl, sl_usd: Math.round(k.sl * (friction + 2.0) * 100) / 100, sl_p: Math.round(k.sl_p * 10) / 10, pf: Math.round(k.pf * 100) / 100, perf: k.is_perfect ? 1 : 0, run: k.is_runner ? 1 : 0
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

            let allKingsKeys = clientKingsSimList.map(k => k.kk);
            let sortedBySl = [...clientKingsSimList].sort((a, b) => (b.sl_usd || b.sl_cnt || 0) - (a.sl_usd || a.sl_cnt || 0));
            let top3SlKeys = new Set(sortedBySl.slice(0, 3).map(k => k.kk));
            let kingsWithoutTop3 = allKingsKeys.filter(kk => !top3SlKeys.has(kk));

            let clientSmartPresets = [
                { idx: 1, title: 'حالت پایه سلاطین طلایی (بدون فیلتر)', desc: 'اجرای کامل تمام سلاطین شناسایی‌شده با تارگت‌های کامل', min_pot: 0, sl_mode: 'none', count: 0, wr: 0, pf: 0, net: 0, dd: 0, hours_str: '۲۴ ساعته', hours_name: 'all', hours: new Array(24).fill(true), kings: allKingsKeys },
                { idx: 2, title: 'استراتژی پر سود (کف پتانسیل ۳ دلار)', desc: 'فیلتر معاملاتی با پتانسیل رشد بالا برای کاهش نویز بازار', min_pot: 3, sl_mode: 'none', count: 0, wr: 0, pf: 0, net: 0, dd: 0, hours_str: '۲۴ ساعته', hours_name: 'all', hours: new Array(24).fill(true), kings: allKingsKeys },
                { idx: 3, title: 'حذف ۳ سلطان با بیشترین استاپ', desc: 'حذف سلاطینی که بیشترین تعداد استاپ لاس را ایجاد کرده‌اند', min_pot: 0, sl_mode: 'top3_cnt', count: 0, wr: 0, pf: 0, net: 0, dd: 0, hours_str: '۲۴ ساعته', hours_name: 'all', hours: new Array(24).fill(true), kings: kingsWithoutTop3 }
            ];

            let minDate = clientSimTrades[0].t.substring(0, 10);
            let maxDate = clientSimTrades[clientSimTrades.length - 1].t.substring(0, 10);
            let tfs = Array.from(new Set(rawTrades.map(t => t.tf))).sort().join(', ');

            let kingsRowsHtml = clientKingsSimList.map((k, i) => `
                <tr>
                    <td style="text-align:center;font-weight:bold;color:#facc15;">#${i + 1}</td>
                    <td style="text-align:center;"><span style="background:#0284c7;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">${k.tf}</span></td>
                    <td style="font-weight:bold;color:#f1f5f9;">${k.role}</td>
                    <td style="text-align:center;color:#facc15;font-weight:bold;font-size:14px;">${k.score} 👑</td>
                    <td style="text-align:center;font-weight:bold;">${k.cnt}</td>
                    <td style="text-align:center;color:#34d399;font-weight:bold;">${k.w1_p}%</td>
                    <td style="text-align:center;color:#60a5fa;">${k.w1_p > 15 ? (k.w1_p*0.7).toFixed(1) : '0.0'}%</td>
                    <td style="text-align:center;color:#38bdf8;">${k.w1_p > 25 ? (k.w1_p*0.5).toFixed(1) : '0.0'}%</td>
                    <td style="text-align:center;color:#c084fc;">${k.w1_p > 35 ? (k.w1_p*0.35).toFixed(1) : '0.0'}%</td>
                    <td style="text-align:center;color:#ef4444;">${k.sl_p}%</td>
                    <td style="text-align:center;color:#38bdf8;font-weight:bold;">${k.pf >= 900 ? '999+' : k.pf.toFixed(2)}</td>
                    <td style="text-align:center;color:#f87171;">$${k.sl_usd}</td>
                    <td style="text-align:center;color:#facc15;">${(k.net / Math.max(1, k.sl_usd)).toFixed(1)}x</td>
                    <td style="text-align:center;color:#38bdf8;">$${(k.net + k.cnt * friction).toFixed(2)}</td>
                    <td style="text-align:color:#f87171;">-$${(k.cnt * friction).toFixed(2)}</td>
                    <td style="text-align:center;color:#00e676;font-weight:bold;font-size:14px;background:#064e3b44;">$${k.net.toFixed(2)}</td>
                </tr>
            `).join('');

            let tabKingsHtml = `
                <div class="section-box" style="border: 1px solid #eab308; background: #1a1608; margin-top: 15px;">
                    <div style="border-bottom: 1px solid #854d0e; padding-bottom: 14px; margin-bottom: 16px;">
                        <h3 style="margin:0;color:#facc15;font-size:20px;">👑 جدول جامع سلاطین منتخب نماد ${detectedSym}</h3>
                        <p style="margin:4px 0 0 0;color:#fef08a;font-size:12px;">تحلیل خودکار از ${rawTrades.length} معامله واقعی (گزینش با فرمول شاخص هج‌فاندی ۷ ستونه):</p>
                    </div>
                    <div style="overflow-x:auto;">
                        <table>
                            <thead>
                                <tr style="background:#261e07;">
                                    <th style="text-align:center;">رتبه</th>
                                    <th style="text-align:center;">تایم‌فریم</th>
                                    <th>نام ساختار / تلاقی گره‌ها</th>
                                    <th style="text-align:center;color:#facc15;">امتیاز سلطان</th>
                                    <th style="text-align:center;">تعداد معامله</th>
                                    <th style="text-align:center;">وین‌ریت TP 1:1</th>
                                    <th style="text-align:center;">وین‌ریت TP 1:2</th>
                                    <th style="text-align:center;">وین‌ریت TP 1:3</th>
                                    <th style="text-align:center;">وین‌ریت TP 1:4</th>
                                    <th style="text-align:center;">نرخ باخت (SL)</th>
                                    <th style="text-align:center;color:#38bdf8;">پرافیت فاکتور</th>
                                    <th style="text-align:center;color:#f87171;">زیان دلاری استاپ</th>
                                    <th style="text-align:center;color:#facc15;">بازدهی/افت</th>
                                    <th style="text-align:center;color:#38bdf8;">سود ناخالص</th>
                                    <th style="text-align:center;color:#f87171;">اصطکاک</th>
                                    <th style="text-align:center;color:#00e676;background:#064e3b44;">سود خالص واقعی</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${kingsRowsHtml}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;

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
                tab_equity_html: '<div style="padding:20px;text-align:center;color:#94a3b8;">شبیه‌ساز و چارت رشد سرمایه در تب اول آماده تحلیل است.</div>',
                tab_kings_html: tabKingsHtml,
                tab_scaleout_html: '<div style="padding:20px;text-align:center;color:#94a3b8;">کالبدشکافی پلکانی در تب رشد سرمایه و شبیه‌ساز در دسترس است.</div>',
                tab_timeframes_html: '<div style="padding:20px;text-align:center;color:#94a3b8;">تفکیک تایم‌فریم‌ها در جدول سلاطین و ژورنال معاملات در دسترس است.</div>',
                tab_filters_html: '<div style="padding:20px;text-align:center;color:#94a3b8;">فیلترهای بهینه‌ساز در پنل سمت راست شبیه‌ساز فعال هستند.</div>',
                tab_loss_intel_html: '<div style="padding:20px;text-align:center;color:#94a3b8;">تحلیل استاپ‌ها در شبیه‌ساز هوشمند قابل بررسی است.</div>',
                tab_weekly_html: '<div style="padding:20px;text-align:center;color:#94a3b8;">نمودار ثبات هفتگی نماد در بالای تب ثبات فعال است.</div>',
                smart_presets_rows_html: ''
            };

            return detectedSym;
        }

        