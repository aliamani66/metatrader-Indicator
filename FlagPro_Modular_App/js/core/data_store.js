var currentActiveSymbol = 'GBPUSD';
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
    mode: 'all', // Default: Raw Test (All Trades)
    enabledKings: new Set(),
    allowedHours: new Array(24).fill(true),
    minProfit: 0.0,
    consecLossTrigger: 0,
    consecLossSkipCount: 1,
    consecLossSkipDay: false,
    showDrawdown: true
};

function switchDashboardSymbol(symName) {
    if (!window.ALL_SYMBOLS_DATA) return;
    if (!window.ALL_SYMBOLS_DATA[symName]) {
        let clean = symName.replace(/[!#]/g, '').trim();
        if (window.ALL_SYMBOLS_DATA[clean]) {
            symName = clean;
        } else if (window.ALL_SYMBOLS_DATA[symName + '!']) {
            symName = symName + '!';
        } else {
            return;
        }
    }
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

            // 1.2 Update Sidebar King & Timeframe dynamic badges
            let kCount = (sData.kings_sim_list ? sData.kings_sim_list.length : 0);
            let kTradeCount = (sData.tot_k_cnt !== undefined ? sData.tot_k_cnt : ((sData.trades_json_list || []).filter(t => t.is_k === 1 || t.k === 1).length));
            let sidebarKings = document.getElementById('sidebarKingsTitle');
            if (sidebarKings) {
                sidebarKings.textContent = 'سلاطین برگزیده (' + kCount + ' الگو | ' + kTradeCount + ' ترید)';
            }
            let sidebarTf = document.getElementById('sidebarTimeframesTitle');
            if (sidebarTf) {
                sidebarTf.textContent = 'تایم‌فریم‌ها و تحلیل (' + (sData.tfs_str || 'M1') + ')';
            }

            // 2. Update JS Global Datasets
            dataWeeklyBars = sData.weekly_bar_data || [];
            kingsSimList = sData.kings_sim_list || [];
            top3SLCntKeys = sData.top3_sl_cnt_keys || [];
            top3SLUsdKeys = sData.top3_sl_usd_keys || [];
            top5SLUsdKeys = sData.top5_sl_usd_keys || [];
            top3SLPctKeys = sData.top3_sl_pct_keys || [];
            simTrades = sData.trades_sim_list || [];
            smartPresets = sData.smart_presets || [];
            allTrades = sData.trades_json_list || [];

            let friction = 0.48;
            let rawTrades = allTrades;
            let totBoxes = sData.total_setups || sData.closed_count || rawTrades.length;
            let pendBoxes = sData.pending || 0;
            let openCnt = sData.in_trade_count || 0;

            // 3. Dynamically Render Tab HTML Containers from Data (Single Source of Truth)
            let cKings = document.getElementById('tab-kings-container');
            if (cKings && typeof generateClientKingsHTML === 'function') {
                cKings.innerHTML = generateClientKingsHTML(symName, rawTrades, kingsSimList, friction, totBoxes, pendBoxes, openCnt);
            }

            let cScale = document.getElementById('tab-scaleout-container');
            if (cScale && typeof generateClientScaleoutHTML === 'function') {
                cScale.innerHTML = generateClientScaleoutHTML(symName, rawTrades, kingsSimList, friction);
            }

            let cTf = document.getElementById('tab-timeframes-container');
            if (cTf && typeof generateClientTimeframesHTML === 'function') {
                cTf.innerHTML = generateClientTimeframesHTML(symName, rawTrades, kingsSimList, friction);
            }

            let cFilt = document.getElementById('tab-filters-container');
            if (cFilt && typeof generateClientFiltersHTML === 'function') {
                cFilt.innerHTML = generateClientFiltersHTML(symName, rawTrades, friction);
            }

            let cLoss = document.getElementById('tab-loss-intel-container');
            if (cLoss && typeof generateClientLossIntelHTML === 'function') {
                cLoss.innerHTML = generateClientLossIntelHTML(symName, rawTrades, kingsSimList, friction);
            }

            let cWk = document.getElementById('tab-weekly-container');
            if (cWk && typeof generateClientWeeklyHTML === 'function') {
                cWk.innerHTML = generateClientWeeklyHTML(symName, rawTrades, kingsSimList, dataWeeklyBars, friction);
            }

            // 3.1 Update Strategic Presets Table Rows
            let tbodyPresets = document.getElementById('systemPresetsTbody');
            if (tbodyPresets && typeof generateClientSmartPresetsRowsHTML === 'function') {
                tbodyPresets.innerHTML = generateClientSmartPresetsRowsHTML(symName, smartPresets);
            }
            if (typeof loadCustomPresets === 'function') {
                try { loadCustomPresets(); } catch(e) {}
            }

            // 3.2 Update Validation Status Badge
            if (typeof updateValidationStatus === 'function') {
                updateValidationStatus();
            }

            // 4. Reset Simulator State to Raw Test (All Trades)
            simState.mode = 'all';
            simState.enabledKings = new Set(kingsSimList.map(k => k.kk));
            simState.allowedHours = new Array(24).fill(true);
            simState.minProfit = 0.0;
            simState.consecLossTrigger = 0;
            simState.consecLossSkipCount = 1;
            simState.consecLossSkipDay = false;
            window.currentActivePreset = null;
            window.currentActivePresetIdx = -1;
            window.currentActivePresetTitle = '📊 نتیجه تست خام (کل معاملات چارت)';
            window.currentActiveSimSettings = JSON.parse(JSON.stringify(simState));

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

            let btnK = document.getElementById('btnEqKings');
            let btnA = document.getElementById('btnEqAll');
            if (btnK) {
                btnK.style.background = 'transparent';
                btnK.style.color = '#94a3b8';
                btnK.classList.remove('active');
            }
            if (btnA) {
                btnA.style.background = '#0284c7';
                btnA.style.color = '#fff';
                btnA.classList.add('active');
            }
            let lbl = document.getElementById('lblActiveEquityScenario');
            if (lbl) {
                lbl.textContent = '📊 نتیجه تست خام (کل معاملات چارت)';
                lbl.style.borderColor = '#0284c7';
                lbl.style.color = '#38bdf8';
                lbl.style.background = '#0f2942';
            }

            // Re-render UI components safely
            try { if (typeof initEquityCanvasEvents === 'function') initEquityCanvasEvents(); } catch(e) { console.error('initEquityCanvasEvents error:', e); }
            try { if (typeof clearPresetActiveState === 'function') clearPresetActiveState(); } catch(e) { console.error('clearPresetActiveState error:', e); }
            try { if (typeof renderSimKingsGrid === 'function') renderSimKingsGrid(); } catch(e) { console.error('renderSimKingsGrid error:', e); }
            try { if (typeof renderSLRiskPanel === 'function') renderSLRiskPanel(); } catch(e) { console.error('renderSLRiskPanel error:', e); }
            try { if (typeof renderSimHoursBar === 'function') renderSimHoursBar(); } catch(e) { console.error('renderSimHoursBar error:', e); }
            try { if (typeof trFilters !== 'undefined') trFilters.page = 1; } catch(e) {}
            try { if (typeof renderTrades === 'function') renderTrades(); } catch(e) {}
            try { if (typeof runEquitySimulation === 'function') runEquitySimulation(); } catch(e) { console.error('runEquitySimulation error:', e); }
            requestAnimationFrame(() => {
                try { if (typeof drawEquityChart === 'function') drawEquityChart(); } catch(e) {}
                setTimeout(() => {
                    try { if (typeof drawEquityChart === 'function') drawEquityChart(); } catch(e) {}
                }, 80);
            });
            try {
                if (typeof drawWeeklyBarChart === 'function' && typeof currentWeeklyBarMode !== 'undefined') {
                    drawWeeklyBarChart(currentWeeklyBarMode);
                }
            } catch(e) { console.error('drawWeeklyBarChart error:', e); }
            try {
                if (typeof initTesterCompareTab === 'function') {
                    initTesterCompareTab();
                }
            } catch(e) { console.error('initTesterCompareTab error:', e); }
        }
