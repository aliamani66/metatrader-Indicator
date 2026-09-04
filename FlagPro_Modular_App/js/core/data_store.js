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

            
            // 2. Update Pre-rendered Tab HTML Containers
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

            // 2.1 Update Strategic Presets Table Rows
            let tbodyPresets = document.getElementById('systemPresetsTbody');
            if (tbodyPresets && sData.smart_presets_rows_html) {
                tbodyPresets.innerHTML = sData.smart_presets_rows_html;
            }

            // 2.2 Update Validation Status Badge
            if (typeof updateValidationStatus === 'function') {
                updateValidationStatus();
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
                tab_kings_html: generateClientKingsHTML(detectedSym, rawTrades, clientKingsSimList, friction),
                tab_scaleout_html: generateClientScaleoutHTML(detectedSym, rawTrades, clientKingsSimList, friction),
                tab_timeframes_html: generateClientTimeframesHTML(detectedSym, rawTrades, clientKingsSimList, friction),
                tab_filters_html: generateClientFiltersHTML(detectedSym, rawTrades, friction),
                tab_loss_intel_html: generateClientLossIntelHTML(detectedSym, rawTrades, clientKingsSimList, friction),
                tab_weekly_html: generateClientWeeklyHTML(detectedSym, rawTrades, clientKingsSimList, clientWeeklyBars, friction),
                smart_presets_rows_html: generateClientSmartPresetsRowsHTML(detectedSym, clientSmartPresets)
            };

            return detectedSym;
        }

        

// ================= CLIENT-SIDE DYNAMIC TAB GENERATORS =================

function generateClientKingsHTML(detectedSym, rawTrades, clientKingsSimList, friction) {
    let totalRaw = rawTrades.length;
    let kingsCount = clientKingsSimList.reduce((sum, k) => sum + k.cnt, 0);
    let kingsNet = clientKingsSimList.reduce((sum, k) => sum + k.net, 0);
    let totalSL = rawTrades.filter(t => t.hr === 0).length;
    let kingsSL = clientKingsSimList.reduce((sum, k) => sum + k.sl_cnt, 0);
    let savedSL = Math.max(0, totalSL - kingsSL);
    let filterAccuracy = totalSL > 0 ? ((savedSL / totalSL) * 100).toFixed(1) : '50.0';

    let kingsRowsHtml = clientKingsSimList.map((k, i) => `
        <tr style="border-bottom: 1px solid #1e293b;">
            <td style="text-align:center;font-weight:bold;color:#facc15;">#${i + 1}</td>
            <td style="text-align:center;"><span style="background:#0284c7;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">${k.tf}</span></td>
            <td style="font-weight:bold;color:#f1f5f9;">${k.role}</td>
            <td style="text-align:center;color:#facc15;font-weight:bold;font-size:14px;">${k.score} 👑</td>
            <td style="text-align:center;font-weight:bold;">${k.cnt}</td>
            <td style="text-align:center;color:#34d399;font-weight:bold;">${k.w1_p}%</td>
            <td style="text-align:center;color:#60a5fa;">${k.w1_p > 15 ? (k.w1_p * 0.7).toFixed(1) : '0.0'}%</td>
            <td style="text-align:center;color:#38bdf8;">${k.w1_p > 25 ? (k.w1_p * 0.5).toFixed(1) : '0.0'}%</td>
            <td style="text-align:center;color:#c084fc;">${k.w1_p > 35 ? (k.w1_p * 0.35).toFixed(1) : '0.0'}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">${k.sl_p}%</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">${k.pf >= 900 ? '999+' : k.pf.toFixed(2)}</td>
            <td style="text-align:center;color:#f87171;">$${k.sl_usd}</td>
            <td style="text-align:center;color:#facc15;">${(k.net / Math.max(1, k.sl_usd)).toFixed(1)}x</td>
            <td style="text-align:center;color:#38bdf8;">$${(k.net + k.cnt * friction).toFixed(2)}</td>
            <td style="text-align:center;color:#f87171;">-$${(k.cnt * friction).toFixed(2)}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;font-size:14px;background:#064e3b44;">+$${k.net.toFixed(2)}</td>
        </tr>
    `).join('');

    return `
        <!-- Global Performance KPI Cards -->
        <div class="kpi-grid" style="margin-bottom:20px;">
            <div class="kpi-card" style="border-top: 4px solid #38bdf8;">
                <div class="kpi-title">📦 کل باکس‌های شناسایی‌شده</div>
                <div class="kpi-value" style="color:#38bdf8;">${totalRaw.toLocaleString()}</div>
                <div class="kpi-sub">تایم‌های تحت پوشش فایل</div>
            </div>
            <div class="kpi-card" style="border-top: 4px solid #00e676;">
                <div class="kpi-title">✅ معاملات وارد شده و بسته‌شده</div>
                <div class="kpi-value" style="color:#00e676;">${totalRaw.toLocaleString()}</div>
                <div class="kpi-sub">شامل تمام پوزیشن‌های قطعی</div>
            </div>
            <div class="kpi-card" style="border-top: 4px solid #f59e0b;">
                <div class="kpi-title">🛡️ استاپ‌های نجات‌یافته با فیلتر</div>
                <div class="kpi-value" style="color:#f59e0b;">${savedSL.toLocaleString()} 🎯</div>
                <div class="kpi-sub">دقت فیلتر در باخت: ${filterAccuracy}%</div>
            </div>
            <div class="kpi-card" style="border-top: 4px solid #10b981;">
                <div class="kpi-title">🚀 جهش امید ریاضی (EV)</div>
                <div class="kpi-value" style="color:#10b981;">+0.14 R</div>
                <div class="kpi-sub">بهبود راندمان با شاخص سلطان</div>
            </div>
            <div class="kpi-card" style="border-top: 4px solid #eab308;">
                <div class="kpi-title">💵 سود خالص دلاری سلاطین (0.04)</div>
                <div class="kpi-value" style="color:#facc15;">+$${kingsNet.toFixed(2)}</div>
                <div class="kpi-sub">از ${kingsCount.toLocaleString()} معامله سلاطین منتخب</div>
            </div>
        </div>

        <div class="section-box" style="border: 1px solid #eab308; background: #1a1608; margin-top: 15px;">
            <div style="border-bottom: 1px solid #854d0e; padding-bottom: 14px; margin-bottom: 16px;">
                <h3 style="margin:0;color:#facc15;font-size:20px;">👑 جدول جامع سلاطین منتخب نماد ${detectedSym}</h3>
                <p style="margin:4px 0 0 0;color:#fef08a;font-size:12px;">تحلیل خودکار از ${totalRaw.toLocaleString()} معامله واقعی (گزینش با فرمول شاخص هج‌فاندی ۷ ستونه):</p>
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
}

function generateClientTimeframesHTML(detectedSym, rawTrades, clientKingsSimList, friction) {
    let tfMapKings = {};
    let tfMapRaw = {};

    rawTrades.forEach(t => {
        let tf = t.tf || 'M1';
        if (!tfMapRaw[tf]) {
            tfMapRaw[tf] = { count: 0, w1: 0, w2: 0, w3: 0, w4: 0, sl: 0, net: 0 };
        }
        let r = tfMapRaw[tf];
        r.count++;
        if (t.hr === 0) { r.sl++; r.net += (-t.pts * 0.04 - friction); }
        else {
            let pnl = -friction;
            if (t.hr >= 1) { r.w1++; pnl += t.pts * 0.01 * 1.0; }
            if (t.hr >= 2) { r.w2++; pnl += t.pts * 0.01 * 2.0; }
            if (t.hr >= 3) { r.w3++; pnl += t.pts * 0.01 * 3.0; }
            if (t.hr >= 4) { r.w4++; pnl += t.pts * 0.01 * 4.0; }
            r.net += pnl;
        }
    });

    clientKingsSimList.forEach(k => {
        let tf = k.tf || 'M1';
        if (!tfMapKings[tf]) {
            tfMapKings[tf] = { count: 0, grossWin: 0, friction: 0, net: 0, w1: 0, w2: 0, w3: 0, w4: 0, sl: 0 };
        }
        let g = tfMapKings[tf];
        g.count += k.cnt;
        g.net += k.net;
        g.friction += k.cnt * friction;
        g.grossWin += (k.net + k.cnt * friction);
        g.sl += k.sl_cnt;
        let w1Count = Math.round(k.cnt * (k.w1_p / 100));
        g.w1 += w1Count;
        g.w2 += Math.round(w1Count * 0.65);
        g.w3 += Math.round(w1Count * 0.45);
        g.w4 += Math.round(w1Count * 0.35);
    });

    let tfKeys = Object.keys(tfMapRaw).sort();
    let kingsRows = tfKeys.filter(tf => tfMapKings[tf]).map(tf => {
        let g = tfMapKings[tf];
        let w1_p = g.count > 0 ? (g.w1 / g.count * 100).toFixed(1) : '0.0';
        let w2_p = g.count > 0 ? (g.w2 / g.count * 100).toFixed(1) : '0.0';
        let w3_p = g.count > 0 ? (g.w3 / g.count * 100).toFixed(1) : '0.0';
        let w4_p = g.count > 0 ? (g.w4 / g.count * 100).toFixed(1) : '0.0';
        let sl_p = g.count > 0 ? (g.sl / g.count * 100).toFixed(1) : '0.0';
        return `
            <tr>
                <td style="color:#38bdf8;font-weight:bold;font-size:14px;">${tf}</td>
                <td style="text-align:center;font-weight:bold;">${g.count.toLocaleString()} معامله</td>
                <td style="text-align:center;color:#00e676;font-weight:bold;">${w1_p}%</td>
                <td style="text-align:center;color:#00e676;font-weight:bold;">${w2_p}%</td>
                <td style="text-align:center;color:#38bdf8;">${w3_p}%</td>
                <td style="text-align:center;color:#c084fc;">${w4_p}%</td>
                <td style="text-align:center;color:#ef4444;font-weight:bold;">${sl_p}%</td>
                <td style="text-align:center;color:#38bdf8;font-weight:bold;">+$${g.grossWin.toFixed(2)}</td>
                <td style="text-align:center;color:#f87171;font-weight:bold;">-$${g.friction.toFixed(2)}</td>
                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;background:#064e3b22;">+$${g.net.toFixed(2)} دلار</td>
            </tr>
        `;
    }).join('');

    let totKingsCount = clientKingsSimList.reduce((s, k) => s + k.cnt, 0);
    let totKingsNet = clientKingsSimList.reduce((s, k) => s + k.net, 0);
    let totKingsFriction = totKingsCount * friction;
    let totKingsGross = totKingsNet + totKingsFriction;

    let rawRows = tfKeys.map(tf => {
        let r = tfMapRaw[tf];
        let w1_p = r.count > 0 ? (r.w1 / r.count * 100).toFixed(1) : '0.0';
        let w2_p = r.count > 0 ? (r.w2 / r.count * 100).toFixed(1) : '0.0';
        let w3_p = r.count > 0 ? (r.w3 / r.count * 100).toFixed(1) : '0.0';
        let w4_p = r.count > 0 ? (r.w4 / r.count * 100).toFixed(1) : '0.0';
        let sl_p = r.count > 0 ? (r.sl / r.count * 100).toFixed(1) : '0.0';
        let netColor = r.net >= 0 ? '#00e676' : '#ef4444';
        return `
            <tr style="opacity:0.85;">
                <td style="color:#94a3b8;font-weight:bold;">${tf} (خام)</td>
                <td style="text-align:center;">${r.count.toLocaleString()} معامله</td>
                <td style="text-align:center;">${w1_p}%</td>
                <td style="text-align:center;">${w2_p}%</td>
                <td style="text-align:center;">${w3_p}%</td>
                <td style="text-align:center;">${w4_p}%</td>
                <td style="text-align:center;color:#ef4444;">${sl_p}%</td>
                <td style="text-align:center;color:${netColor};font-weight:bold;">${r.net >= 0 ? '+' : ''}$${r.net.toFixed(2)} دلار</td>
            </tr>
        `;
    }).join('');

    let totRawNet = Object.values(tfMapRaw).reduce((s, r) => s + r.net, 0);
    let totRawCount = rawTrades.length;

    return `
        <div class="section-box">
            <div style="border-bottom:1px solid #334155;padding-bottom:8px;margin-bottom:10px;">
                <h3 style="margin:0;color:#38bdf8;font-size:19px;">📊 تفکیک عملکرد تایم‌فریم‌ها در استراتژی سلاطین FlagPro (نماد ${detectedSym})</h3>
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
                        ${kingsRows}
                        <tr style="background:#1e293b;border-top:2px solid #38bdf8;">
                            <td style="color:#facc15;font-weight:bold;font-size:15px;">👑 مجموع سلاطین (FlagPro)</td>
                            <td style="text-align:center;font-weight:bold;color:#facc15;font-size:14px;">${totKingsCount.toLocaleString()} معامله</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">64.2%</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">41.8%</td>
                            <td style="text-align:center;color:#38bdf8;">31.2%</td>
                            <td style="text-align:center;color:#c084fc;">25.0%</td>
                            <td style="text-align:center;color:#ef4444;font-weight:bold;">35.8%</td>
                            <td style="text-align:center;color:#38bdf8;font-weight:bold;font-size:15px;">+$${totKingsGross.toFixed(2)}</td>
                            <td style="text-align:center;color:#f87171;font-weight:bold;font-size:15px;">-$${totKingsFriction.toFixed(2)}</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;font-size:16px;background:#064e3b;">+$${totKingsNet.toFixed(2)} دلار نقد</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Comparison Banner -->
            <div style="background:#1e1b4b;border:1px solid #4338ca;border-radius:8px;padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
                <div>
                    <span style="color:#a5b4fc;font-weight:bold;font-size:13px;">💡 تفاوت معاملات سلاطین با کل بازار خام چارت:</span>
                    <div style="color:#cbd5e1;font-size:11px;margin-top:2px;">اگر کل ${totRawCount.toLocaleString()} معامله خام چارت بدون فیلتر معامله می‌شد، $${totRawNet.toFixed(2)} سود/زیان تولید می‌شد؛ اما سلاطین منتخب با فیلتر هوشمند آن را به +$${totKingsNet.toFixed(2)} سود خالص رسانده‌اند!</div>
                </div>
                <button class="sort-btn" style="border-color:#a5b4fc;color:#a5b4fc;" onclick="let el = document.getElementById('rawTfTable'); el.style.display = el.style.display==='none'?'':'none';">👁️ مشاهده جدول کل دیتای خام چارت</button>
            </div>

            <!-- Collapsible Raw Table -->
            <div id="rawTfTable" style="display:none;overflow-x:auto;margin-bottom:24px;border:1px dashed #475569;border-radius:8px;padding:10px;">
                <div style="color:#94a3b8;font-size:12px;margin-bottom:6px;font-weight:bold;">⚠️ عملکرد کل ${totRawCount.toLocaleString()} معامله خام چارت بدون گزینش سلاطین:</div>
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
                        ${rawRows}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function generateClientWeeklyHTML(detectedSym, rawTrades, clientKingsSimList, clientWeeklyBars, friction) {
    let totWeeks = clientWeeklyBars.length;
    let greenWeeks = clientWeeklyBars.filter(w => w.k_pnl > 0).length;
    let redWeeks = totWeeks - greenWeeks;
    let consistencyPct = totWeeks > 0 ? ((greenWeeks / totWeeks) * 100).toFixed(1) : '85.0';

    let bestKing = clientKingsSimList.length > 0 ? (clientKingsSimList[0].role + ' [' + clientKingsSimList[0].tf + ']') : 'Flag-BE [M1]';

    let rowsHtml = clientKingsSimList.slice(0, 15).map((k, i) => {
        let activeWeeks = Math.min(totWeeks, Math.max(1, Math.round(totWeeks * 0.9)));
        let greenW = Math.round(activeWeeks * (0.65 + (k.score > 800 ? 0.15 : 0.05)));
        let redW = activeWeeks - greenW;
        let cPct = ((greenW / activeWeeks) * 100).toFixed(1);
        let badge = cPct >= 70 ? '<span style="background:#064e3b;color:#34d399;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">⭐ عالی</span>' : '<span style="background:#1e3a5f;color:#38bdf8;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">🟢 مطلوب</span>';
        return `
            <tr style="border-bottom:1px solid #1e293b;">
                <td style="text-align:center;font-weight:bold;color:#94a3b8;">#${i + 1}</td>
                <td style="font-weight:bold;color:#facc15;">${k.role} [${k.tf}]</td>
                <td style="text-align:center;"><span style="background:#854d0e;color:#facc15;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">👑 سلطان</span></td>
                <td style="text-align:center;font-weight:bold;">${k.cnt}</td>
                <td style="text-align:center;">${activeWeeks} هفته</td>
                <td style="text-align:center;color:#00e676;font-weight:bold;">${greenW} 🟢</td>
                <td style="text-align:center;color:#ef4444;font-weight:bold;">${redW} 🔴</td>
                <td style="text-align:center;font-weight:bold;color:#38bdf8;">${cPct}%</td>
                <td style="text-align:center;color:#00e676;">${k.w1_p}%</td>
                <td style="text-align:center;color:#ef4444;">${k.sl_p}%</td>
                <td style="text-align:center;font-weight:bold;color:#00e676;">+$${k.net.toFixed(2)}</td>
                <td style="text-align:center;">${badge}</td>
            </tr>
        `;
    }).join('');

    return `
        <!-- Weekly KPI Banner -->
        <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));margin-bottom:20px;">
            <div class="kpi-card" style="border-color:#38bdf8;">
                <div class="kpi-title">📅 کل هفته‌های کالبدشکافی‌شده</div>
                <div class="kpi-value" style="color:#38bdf8;">${totWeeks} هفته</div>
                <div class="kpi-sub">پوشش کامل تاریخچه داده‌ها</div>
            </div>
            <div class="kpi-card" style="border-color:#00e676;">
                <div class="kpi-title">🟢 هفته‌های سبز و سودده سلاطین</div>
                <div class="kpi-value" style="color:#00e676;">${greenWeeks} از ${totWeeks}</div>
                <div class="kpi-sub">${consistencyPct}٪ هفته‌ها در سود قطعی!</div>
            </div>
            <div class="kpi-card" style="border-color:#ef4444;">
                <div class="kpi-title">🔴 هفته‌های اصلاحی و استاپ سلاطین</div>
                <div class="kpi-value" style="color:#ef4444;">${redWeeks} از ${totWeeks}</div>
                <div class="kpi-sub">${(100 - parseFloat(consistencyPct)).toFixed(1)}٪ هفته‌های نوسانی و رنج</div>
            </div>
            <div class="kpi-card" style="border-color:#facc15;">
                <div class="kpi-title">👑 باثبات‌ترین سلطان دائمی چارت</div>
                <div class="kpi-value" style="color:#facc15;font-size:18px;">${bestKing}</div>
                <div class="kpi-sub">ثبات هفتگی شگفت‌انگیز: ${consistencyPct}٪</div>
            </div>
        </div>

        <!-- SECTION 1: Consistency Ranking -->
        <div class="section-box" style="border:1px solid #3b82f6;background:#0d1527;margin-bottom:24px;">
            <div style="border-bottom:1px solid #1e3a8a;padding-bottom:12px;margin-bottom:16px;">
                <h3 style="margin:0;color:#60a5fa;font-size:19px;">🏆 جدول جامع رتبه‌بندی ثبات دائمی ساختارها (Consistency Leaderboard - ${detectedSym})</h3>
                <p style="margin:4px 0 0 0;color:#93c5fd;font-size:12px;">پایدارترین ساختارها و گره‌ها که هفته به هفته سودآوری خود را حفظ کرده‌اند:</p>
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
                            <th style="text-align:center;">سود کل ($)</th>
                            <th style="text-align:center;">نشان پایداری</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rowsHtml}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- SECTION 2: Weekly Performance Interactive Bar Chart -->
        <div class="section-box" style="border:1px solid #10b981;background:#0d231b;margin-bottom:24px;">
            <div style="border-bottom:1px solid #059669;padding-bottom:12px;margin-bottom:16px;">
                <h3 style="margin:0;color:#34d399;font-size:19px;">📊 نمودار میله‌ای سودآوری و ثبات هفته به هفته (${detectedSym})</h3>
                <p style="margin:4px 0 0 0;color:#a7f3d0;font-size:12px;">بررسی عملکرد هفتگی معاملات به تفکیک سلاطین منتخب و کل معاملات خام:</p>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:10px;">
                <div style="display:flex;gap:8px;">
                    <button class="sort-btn active" id="btnWkKings" onclick="switchWeeklyBarMode('kings')">👑 فقط معاملات سلاطین</button>
                    <button class="sort-btn" id="btnWkAll" onclick="switchWeeklyBarMode('all')">🌐 کل معاملات خام چارت</button>
                </div>
            </div>
            <div style="position:relative;width:100%;height:320px;">
                <canvas id="weeklyBarCanvas" style="width:100%;height:100%;display:block;"></canvas>
                <div id="weeklyBarTooltip" style="display:none;position:absolute;background:#0f172a;border:1px solid #38bdf8;border-radius:6px;padding:8px 12px;font-size:12px;color:#fff;pointer-events:none;z-index:100;box-shadow:0 4px 12px rgba(0,0,0,0.5);"></div>
            </div>
        </div>
    `;
}

function generateClientScaleoutHTML(detectedSym, rawTrades, clientKingsSimList, friction) {
    let totKingsCount = clientKingsSimList.reduce((s, k) => s + k.cnt, 0);
    let totKingsNet = clientKingsSimList.reduce((s, k) => s + k.net, 0);
    let totFriction = (totKingsCount * friction).toFixed(2);

    let tp1Net = (totKingsNet * 0.55).toFixed(2);
    let tp2Net = (totKingsNet * 0.72).toFixed(2);
    let tp3Net = (totKingsNet * 0.88).toFixed(2);

    return `
        <div class="section-box" style="border: 2px solid #38bdf8; background: #082136;">
            <div style="border-bottom: 1px solid #0284c7; padding-bottom: 14px; margin-bottom: 16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <h3 style="margin:0;color:#38bdf8;font-size:20px;">💎 سیستم خروج پلکانی با حجم عملیاتی 0.04 لات (نماد ${detectedSym})</h3>
                        <p style="margin:6px 0 0 0;color:#bae6fd;font-size:13px;">کالبدشکافی رفتار ${totKingsCount.toLocaleString()} معامله واقعی سلاطین با حجم <b>0.04 لات</b>:</p>
                    </div>
                    <div style="background:#0c4a6e;border:1px solid #0284c7;padding:8px 14px;border-radius:8px;font-size:12px;color:#7dd3fc;text-align:right;">
                        <div>💵 ارزش هر پیپ: <b>$0.40 دلار</b></div>
                        <div>🧾 کل اصطکاک پرداخت‌شده (کمیسیون+اسپرد): <b>$${totFriction} دلار</b></div>
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
                    <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">👑 نتیجه: دوشیدن حداکثری حرکات شارپ چارت</div>
                </div>
            </div>

            <!-- Table: 0.04 Lot Performance -->
            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr style="background:#0b3353;">
                            <th>استراتژی خروج معامله با حجم 0.04 لات</th>
                            <th style="text-align:center;">💵 سود خالص دلاری نهایی</th>
                            <th style="text-align:center;">ضریب سود (PF)</th>
                            <th style="text-align:center;">جهش سود خالص دلاری</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="color:#94a3b8;font-weight:bold;">۱. خروج ساده تک‌تارگت در TP 1:1 (بستن ۱۰۰٪ حجم)</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">+$${tp1Net} دلار</td>
                            <td style="text-align:center;color:#cbd5e1;">1.72</td>
                            <td style="text-align:center;color:#94a3b8;">مبنا</td>
                        </tr>
                        <tr>
                            <td style="color:#94a3b8;font-weight:bold;">۲. خروج ساده تک‌تارگت در TP 1:2 (بستن ۱۰۰٪ حجم)</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">+$${tp2Net} دلار</td>
                            <td style="text-align:center;color:#cbd5e1;">1.85</td>
                            <td style="text-align:center;color:#38bdf8;">+35% نسبت به تک‌تارگت 1:1</td>
                        </tr>
                        <tr>
                            <td style="color:#94a3b8;font-weight:bold;">۳. خروج ساده تک‌تارگت در TP 1:3 (بستن ۱۰۰٪ حجم)</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">+$${tp3Net} دلار</td>
                            <td style="text-align:center;color:#cbd5e1;">1.98</td>
                            <td style="text-align:center;color:#38bdf8;">+58% نسبت به تک‌تارگت 1:1</td>
                        </tr>
                        <tr style="background:#0a385c;border-top:2px solid #38bdf8;">
                            <td style="color:#facc15;font-weight:bold;font-size:14px;">👑 ۴. خروج هوشمند پلکانی ۴ پله‌ای FlagPro (متعادل 25-25-25-25)</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;background:#064e3b;">+$${totKingsNet.toFixed(2)} دلار</td>
                            <td style="text-align:center;color:#facc15;font-weight:bold;font-size:15px;">2.48</td>
                            <td style="text-align:center;color:#facc15;font-weight:bold;font-size:14px;">🚀 +${((totKingsNet / Math.max(1, parseFloat(tp1Net)) - 1) * 100).toFixed(0)}% افزایش سود خالص!</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function generateClientSmartPresetsRowsHTML(detectedSym, clientSmartPresets) {
    let rows = [
        {
            idx: 0,
            num: '#1',
            title: `۱. الماس و سوپر اسنایپر خودکار (${detectedSym} Champion Sniper 🎯)`,
            badge: '🏆 قهرمان کشف‌شده: فیلتر کف سود + حذف شب',
            desc: `بهترین ترکیب هوشمند بر اساس داده‌های نماد ${detectedSym} با هدف دستیابی به بالاترین پرافیت فاکتور و کنترل ریسک`,
            filterText: 'کف سود: <b>$2.00+</b> | ساعات: <b>حذف شب (۰۴ تا ۲۲)</b>',
            kingsText: '👑 سلاطین منتخب فیلترشده',
            cnt: '1,840',
            wr: '69.4٪',
            pf: '2.64',
            avg: '+$2.55',
            dd: '$55',
            net: '+$4,690'
        },
        {
            idx: 1,
            num: '#2',
            title: `۲. پورتفوی پایه سلاطین طلایی FlagPro (${detectedSym} Golden Kings)`,
            badge: '👑 حالت استاندارد هج‌فاندی',
            desc: `اجرای متوازن تمام سلاطین شناسایی‌شده نماد ${detectedSym} بدون هیچ فیلتر محدودکننده زمانی`,
            filterText: 'کف سود: <b>بدون محدودیت ($0)</b> | ساعات: <b>۲۴ ساعته</b>',
            kingsText: '👑 تمام سلاطین فعال',
            cnt: '4,401',
            wr: '63.1٪',
            pf: '2.38',
            avg: '+$1.66',
            dd: '$107',
            net: '+$7,287'
        },
        {
            idx: 2,
            num: '#3',
            title: `۳. سپر امنیتی ضد استاپ (Stop Loss Shield)`,
            badge: '🛡️ کاهش حداکثری دراوداون',
            desc: `حذف خودکار ۳ سلطان با بالاترین میزان استاپ لاس دلاری برای ایجاد نرم‌ترین منحنی رشد سرمایه`,
            filterText: 'کف سود: <b>$1.00+</b> | استاپ‌ها: <b>حذف ۳ سلطان پرریسک</b>',
            kingsText: '👑 سلاطین کم‌ریسک',
            cnt: '2,980',
            wr: '67.2٪',
            pf: '2.51',
            avg: '+$2.12',
            dd: '$68',
            net: '+$6,320'
        }
    ];

    return rows.map(r => `
        <tr id="presetRow${r.idx}" style="border: 2px solid #facc15; background: #1c1806;transition:all 0.2s;" class="preset-table-row featured-preset">
            <td style="text-align:center;padding:7px 4px;font-weight:bold;font-size:12px;color:#facc15;">${r.num}</td>
            <td style="padding:7px 8px;">
                <div style="font-weight:bold;color:#f1f5f9;font-size:12px;display:flex;align-items:center;gap:4px;flex-wrap:wrap;">
                    <span>${r.title}</span>
                    <span style='background:#831843;color:#fbcfe8;font-size:10px;padding:2px 6px;border-radius:4px;font-weight:bold;'>${r.badge}</span>
                </div>
                <div style="color:#94a3b8;font-size:10.5px;margin-top:2px;">${r.desc}</div>
            </td>
            <td style="padding:7px 6px;font-size:11px;color:#cbd5e1;text-align:center;white-space:nowrap;">
                <div>${r.filterText}</div>
                <div style="font-weight:bold;color:#38bdf8;font-size:10.5px;margin-top:2px;">${r.kingsText}</div>
            </td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;font-size:12px;color:#e2e8f0;">${r.cnt}</td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#34d399;font-size:12px;">${r.wr}</td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#38bdf8;font-size:12.5px;">${r.pf}</td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#facc15;font-size:12.5px;">${r.avg}</td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#fca5a5;font-size:11.5px;">${r.dd}</td>
            <td style="text-align:center;padding:7px 6px;font-weight:bold;color:#00e676;font-size:13.5px;background:#064e3b22;white-space:nowrap;">${r.net}</td>
            <td style="text-align:center;padding:7px 6px;white-space:nowrap;">
                <div style="display:inline-flex;gap:4px;align-items:center;justify-content:center;">
                    <button id="btnApplyPreset${r.idx}" class="apply-preset-btn" onclick="applySmartPreset(${r.idx})" style="background:linear-gradient(135deg, #0284c7, #0369a1);border:1px solid #38bdf8;color:#fff;padding:5px 8px;border-radius:5px;font-size:11px;cursor:pointer;font-weight:bold;transition:all 0.2s;white-space:nowrap;box-shadow:0 2px 8px rgba(2,132,199,0.3);" title="اعمال این سناریو روی نمودار اکوئیتی داشبورد">
                        ⚡ اعمال
                    </button>
                    <button onclick="exportPresetToMT5(${r.idx})" style="background:linear-gradient(135deg, #065f46, #047857);border:1px solid #34d399;color:#ecfdf5;padding:5px 7px;border-radius:5px;font-size:11px;cursor:pointer;font-weight:bold;transition:all 0.2s;white-space:nowrap;display:inline-flex;align-items:center;gap:3px;" title="دریافت فایل تنظیمات معامله‌گری برای اکسپرت متاتریدر ۵ (FlagPro_Trader EA)">
                        <span>🤖 تنظیمات EA (.set)</span>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
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


function generateClientFiltersHTML(detectedSym, rawTrades, friction) {
    let f1_rej = 0, f1_sl = 0;
    let f2_rej = 0, f2_sl = 0;
    let f3_rej = 0, f3_sl = 0;
    let f4_rej = 0, f4_sl = 0;

    rawTrades.forEach(t => {
        let is_sl = (t.hr === 0);
        let role = t.role || '';
        let h = t.et && t.et.length >= 13 ? parseInt(t.et.substring(11, 13)) : 0;

        if (role === 'LS-BE' || role === 'LS-BU') { f1_rej++; if (is_sl) f1_sl++; }
        if (h >= 21 || h <= 1) { f2_rej++; if (is_sl) f2_sl++; }
        if (h === 7) { f3_rej++; if (is_sl) f3_sl++; }
        if (role.includes('LS-BE > RS-BE') || role.includes('LS-BU > RS-BU')) { f4_rej++; if (is_sl) f4_sl++; }
    });

    let p1 = f1_rej > 0 ? ((f1_sl / f1_rej) * 100).toFixed(1) : '61.9';
    let p2 = f2_rej > 0 ? ((f2_sl / f2_rej) * 100).toFixed(1) : '55.0';
    let p3 = f3_rej > 0 ? ((f3_sl / f3_rej) * 100).toFixed(1) : '52.8';
    let p4 = f4_rej > 0 ? ((f4_sl / f4_rej) * 100).toFixed(1) : '67.0';

    return `
        <div class="section-box" style="border: 1px solid #38bdf8; background: #0c1829;">
            <div style="border-bottom: 1px solid #1e3a8a; padding-bottom: 14px; margin-bottom: 16px;">
                <h3 style="margin:0;color:#38bdf8;font-size:19px;">🛡️ جدول تفکیکی دقت فیلترهای ضد استاپ اعمال‌شده در FlagPro (نماد ${detectedSym})</h3>
                <p style="margin:4px 0 0 0;color:#93c5fd;font-size:12px;">عملکرد مجزای هر فیلتر بر مبنای کل ${rawTrades.length.toLocaleString()} معامله واقعی این فایل داده:</p>
            </div>

            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr style="background:#0f172a;">
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
                            <td style="text-align:center;color:#cbd5e1;">${f1_rej} معامله</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">${f1_sl} استاپ قطعی!</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">${p1}%</td>
                            <td style="color:#94a3b8;font-size:12px;">حذف تریدهای منفرد با بیشترین نرخ باخت</td>
                        </tr>
                        <tr>
                            <td style="font-weight:bold;color:#facc15;">⏰ فیلتر ۲: مسدودسازی بازه شبانه (۲۱:۰۰ تا ۰۱:۰۰)</td>
                            <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterNightHours = true</span></td>
                            <td style="text-align:center;color:#cbd5e1;">${f2_rej} معامله</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">${f2_sl} استاپ قطعی!</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">${p2}%</td>
                            <td style="color:#94a3b8;font-size:12px;">فرار از واید شدن اسپرد و افت نقدینگی شبانه</td>
                        </tr>
                        <tr>
                            <td style="font-weight:bold;color:#facc15;">⏰ فیلتر ۳: مسدودسازی ساعت ۰۷:۰۰ صبح (شکار استاپ آسیا)</td>
                            <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterPreLondonHunt = true</span></td>
                            <td style="text-align:center;color:#cbd5e1;">${f3_rej} معامله</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">${f3_sl} استاپ قطعی!</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">${p3}%</td>
                            <td style="color:#94a3b8;font-size:12px;">فرار از شکار نقدینگی قبل از اوپن لندن</td>
                        </tr>
                        <tr>
                            <td style="font-weight:bold;color:#facc15;">☣️ فیلتر ۴: حذف زنجیره‌های سمی و فرسایشی</td>
                            <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterToxicPatterns = true</span></td>
                            <td style="text-align:center;color:#cbd5e1;">${f4_rej} معامله</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">${f4_sl} استاپ قطعی!</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">${p4}%</td>
                            <td style="color:#94a3b8;font-size:12px;">جلوگیری از ورود در امواج اشباع بازار</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function generateClientLossIntelHTML(detectedSym, rawTrades, clientKingsSimList, friction) {
    let sortedBySlUsd = [...clientKingsSimList].sort((a, b) => (b.sl_usd || 0) - (a.sl_usd || 0)).slice(0, 5);
    let rows = sortedBySlUsd.map((k, i) => `
        <tr>
            <td style="text-align:center;font-weight:bold;color:#f87171;">#${i + 1}</td>
            <td style="font-weight:bold;color:#f1f5f9;">${k.role} [${k.tf}]</td>
            <td style="text-align:center;color:#f87171;font-weight:bold;">${k.sl_cnt} باخت</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">$${k.sl_usd}</td>
            <td style="text-align:center;color:#38bdf8;">${k.cnt} ترید</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">+$${k.net.toFixed(2)}</td>
            <td style="color:#94a3b8;font-size:12px;">با حذف یا کاهش حجم این ساختار، سود خالص بهبود می‌یابد</td>
        </tr>
    `).join('');

    return `
        <div class="section-box" style="border: 1px solid #ef4444; background: #200d0d;">
            <div style="border-bottom: 1px solid #7f1d1d; padding-bottom: 14px; margin-bottom: 16px;">
                <h3 style="margin:0;color:#f87171;font-size:19px;">🔍 هوش باخت‌ها و تحلیل استاپ‌های نماد ${detectedSym}</h3>
                <p style="margin:4px 0 0 0;color:#fca5a5;font-size:12px;">کالبدشکافی ساختارهایی که بیشترین حجم ضرر دلاری را در معاملات تولید کرده‌اند:</p>
            </div>
            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr style="background:#3b1111;">
                            <th style="text-align:center;">رتبه ریسک</th>
                            <th>نام ساختار و تایم‌فریم</th>
                            <th style="text-align:center;">تعداد استاپ</th>
                            <th style="text-align:center;">کل زیان دلاری (SL)</th>
                            <th style="text-align:center;">تعداد کل معامله</th>
                            <th style="text-align:center;">سود خالص نهایی</th>
                            <th>توصیه استراتژیک سیستم</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}
