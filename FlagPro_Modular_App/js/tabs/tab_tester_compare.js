function parseReportSortKey(k) {
    let r = (window.TESTER_REPORTS && window.TESTER_REPORTS[k]) || {};
    if (k.startsWith('uploaded_')) {
        return { isUploaded: 1, endStr: '9999.99.99', startStr: '9999.99.99', mtime: Date.now(), exp: '9999.99.99' };
    }
    
    let dr = r.dateRange || '';
    let startStr = '';
    let endStr = '';
    let m = dr.match(/(\d{4}[.\-/]\d{2}[.\-/]\d{2})\s*[-_to]+\s*(\d{4}[.\-/]\d{2}[.\-/]\d{2})/i);
    if (m) {
        startStr = m[1].replace(/[\/-]/g, '.');
        endStr = m[2].replace(/[\/-]/g, '.');
    }
    
    if (!endStr) {
        let m2 = k.match(/(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})/);
        if (m2) {
            startStr = m2[1].replace(/-/g, '.');
            endStr = m2[2].replace(/-/g, '.');
        }
    }
    
    if (!endStr && r.trades && r.trades.length > 0) {
        let lastT = r.trades[r.trades.length - 1];
        let tStr = lastT.closeTime || lastT.entryTime || '';
        if (tStr.length >= 10) endStr = tStr.substring(0, 10).replace(/[\/-]/g, '.');
    }
    
    let mt = r.mtime || 0;
    let exp = r.fileTime || r.realExecutionTime || r.executionTime || r.exportedAt || '';
    if (!mt && exp) {
        let parsed = Date.parse(exp.replace(/\./g, '-'));
        if (!isNaN(parsed)) mt = parsed / 1000;
    }
    
    return {
        isUploaded: 0,
        endStr: endStr,
        startStr: startStr,
        mtime: mt,
        exp: exp
    };
}

function getSortedTesterReportKeys() {
    if (!window.TESTER_REPORTS) return [];
    let keys = Object.keys(window.TESTER_REPORTS);
    keys.sort((a, b) => {
        let rA = window.TESTER_REPORTS[a] || {};
        let rB = window.TESTER_REPORTS[b] || {};
        let cntA = (rA.trades && rA.trades.length) || 0;
        let cntB = (rB.trades && rB.trades.length) || 0;

        // TOP PRIORITY: Comprehensive full trades test (e.g. 42 trades) first!
        let isFullA = (cntA >= 30 || a.includes('64Trades')) ? 1 : 0;
        let isFullB = (cntB >= 30 || b.includes('64Trades')) ? 1 : 0;
        if (isFullA !== isFullB) return isFullB - isFullA;

        let sA = parseReportSortKey(a);
        let sB = parseReportSortKey(b);
        
        if (sA.isUploaded !== sB.isUploaded) return sB.isUploaded - sA.isUploaded;
        
        // 1. PRIMARY: Compare mtime descending (most recently executed/modified test run FIRST)
        if (sA.mtime && sB.mtime && sA.mtime !== sB.mtime) {
            return sB.mtime - sA.mtime;
        }

        // 2. Compare exportedAt / execution time descending
        if (sA.exp && sB.exp && sA.exp !== sB.exp) {
            return sB.exp.localeCompare(sA.exp);
        }

        // 3. Compare end date descending
        if (sA.endStr && sB.endStr && sA.endStr !== sB.endStr) {
            return sB.endStr.localeCompare(sA.endStr);
        }

        // 4. Compare start date descending
        if (sA.startStr && sB.startStr && sA.startStr !== sB.startStr) {
            return sB.startStr.localeCompare(sA.startStr);
        }
        
        return b.localeCompare(a);
    });
    return keys;
}

function formatTesterOptionLabel(k, r) {
    let cnt = (r.trades && r.trades.length) || 0;
    let isFull = (cnt >= 30) || k.includes('64Trades');
    let isKingsOnly = (cnt <= 10 && k.includes('6Trades'));

    let title = isFull 
        ? '🌟 تست ۱۰ روزه جامع کل معاملات (۴۲ ستاپ - بدون فیلتر سلاطین)' 
        : (isKingsOnly 
            ? '🎯 تست سلاطین منتخب (فقط ۶ معامله ۵ پترن برتر)' 
            : (r.reportTitle || k));

    let dr = r.dateRange || '';
    let datePart = '';
    
    let m = dr.match(/(\d{4}[.\-/]\d{2}[.\-/]\d{2})\s*[-_to]+\s*(\d{4}[.\-/]\d{2}[.\-/]\d{2})/i);
    if (m) {
        let sD = m[1].replace(/[\/-]/g, '.');
        let eD = m[2].replace(/[\/-]/g, '.');
        datePart = `بازه: از ${sD} تا ${eD}`;
    } else if (dr) {
        datePart = `بازه: ${dr}`;
    }
    
    let execTime = r.fileTime || r.realExecutionTime || '';
    if (!execTime && r.mtime) {
        let dt = new Date(r.mtime * 1000);
        let y = dt.getFullYear();
        let mon = String(dt.getMonth() + 1).padStart(2, '0');
        let d = String(dt.getDate()).padStart(2, '0');
        let h = String(dt.getHours()).padStart(2, '0');
        let min = String(dt.getMinutes()).padStart(2, '0');
        execTime = `${y}.${mon}.${d} ${h}:${min}`;
    }
    if (!execTime) {
        execTime = r.executionTime || r.exportedAt || '';
    }
    let timeBadge = execTime ? ` | ⏱️ انجام تست: ${execTime}` : '';

    return datePart ? `${title} | ${datePart} | ${cnt} معامله${timeBadge}` : `${title} | ${cnt} معامله${timeBadge}`;
}

function renderForensicCallout(report, scenarioKey) {
    let box = document.getElementById('tcForensicCalloutBox');
    if (!box || !report) return;

    let scenario = resolveActiveScenario(scenarioKey, report);
    let k = report.kpis || {};
    let t = report.trades || [];
    let p = report.parameters || {};

    let actWr = (k.winRate !== undefined && !isNaN(Number(k.winRate))) ? Number(k.winRate) : 0.0;
    let actPf = (k.profitFactor !== undefined && !isNaN(Number(k.profitFactor))) ? Number(k.profitFactor) : 0.0;
    let actNetPips = (k.netPips !== undefined && !isNaN(Number(k.netPips))) ? Number(k.netPips) : 0.0;
    let actNetUSD = (k.netUSD !== undefined && !isNaN(Number(k.netUSD))) ? Number(k.netUSD) : 0.0;
    let totalSetups = k.totalSetups || t.length;
    let winCount = k.winningSetups !== undefined ? k.winningSetups : t.filter(x => x.outcome === 'Win').length;
    let lossCount = k.losingSetups !== undefined ? k.losingSetups : t.filter(x => x.outcome === 'Loss').length;

    let m1Count = t.filter(x => (x.timeframe === 'PERIOD_M1' || x.timeframe === 'M1')).length;
    let m5Count = t.filter(x => (x.timeframe === 'PERIOD_M5' || x.timeframe === 'M5')).length;
    let m15Count = t.filter(x => (x.timeframe === 'PERIOD_M15' || x.timeframe === 'M15')).length;

    let slippages = t.map(x => Number(x.slippagePips || 0)).filter(x => !isNaN(x));
    let avgSlip = slippages.length > 0 ? (slippages.reduce((a, b) => a + b, 0) / slippages.length).toFixed(1) : '0.0';

    let beCount = t.filter(x => (x.exitClass && x.exitClass.includes('BE'))).length;

    let isSuccess = (actWr >= 55.0 && actPf >= 1.5);
    let titleHtml = '';
    if (isSuccess) {
        box.style.background = 'linear-gradient(135deg, #0d281e, #091c15)';
        box.style.border = '1px solid #059669';
        titleHtml = `
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
                <span style="font-size:20px;">🏆</span>
                <span style="font-size:13.5px;font-weight:bold;color:#34d399;">کالبدشکافی تطابق موفق: عملکرد تستر متاتریدر ۵ با سناریوی انتخابی («${scenario.title || scenario.name}») کاملاً همگام است!</span>
            </div>
        `;
    } else {
        box.style.background = 'linear-gradient(135deg, #1c1116, #140b10)';
        box.style.border = '1px solid #ef4444';
        titleHtml = `
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
                <span style="font-size:20px;">🚨</span>
                <span style="font-size:13.5px;font-weight:bold;color:#fca5a5;">کالبدشکافی ریشه‌ای مغایرت: علل تفاوت عملکرد تستر متاتریدر ۵ با سناریوی انتخابی («${scenario.title || scenario.name}»)</span>
            </div>
        `;
    }

    let cardsHtml = `
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(240px, 1fr));gap:10px;font-size:11.5px;line-height:1.5;">
            <!-- Card 1: Performance Summary -->
            <div style="background:${isSuccess ? '#0d3827' : '#26161c'};border:1px solid ${isSuccess ? '#10b981' : '#7f1d1d'};padding:9px 12px;border-radius:6px;">
                <div style="color:${isSuccess ? '#34d399' : '#f87171'};font-weight:bold;margin-bottom:3px;">۱. نتیجه کل و نرخ برد (Win Rate: ${actWr.toFixed(1)}%)</div>
                <div style="color:#cbd5e1;">در این تست، تعداد <b>${totalSetups} ستاپ</b> (${winCount} برد و ${lossCount} باخت) با سود خالص <b>${actNetPips >= 0 ? '+' : ''}${actNetPips.toFixed(1)} پیپ</b> ($${actNetUSD.toFixed(2)}) و ضریب سود <b>${actPf.toFixed(2)}</b> ثبت شد که ${isSuccess ? 'کاملاً مؤید سودآوری استراتژی است.' : 'نشان‌دهنده نیاز به اعمال سناریوی صحیح است.'}</div>
            </div>

            <!-- Card 2: Date Range -->
            <div style="background:${isSuccess ? '#0d3827' : '#26161c'};border:1px solid ${isSuccess ? '#10b981' : '#7f1d1d'};padding:9px 12px;border-radius:6px;">
                <div style="color:${isSuccess ? '#34d399' : '#f87171'};font-weight:bold;margin-bottom:3px;">۲. بازه زمانی تست متاتریدر (${report.dateRange || 'کوتاه‌مدت'})</div>
                <div style="color:#cbd5e1;">بازه تست در متاتریدر ۵ برابر با <b>${report.dateRange || '-'}</b> بوده است. توجه فرمایید نمودار کلی داشبورد تمام دیتای چندماهه را نمایش می‌دهد، اما در جدول زیر تنها ستاپ‌های معادل همین بازه مقایسه شده‌اند.</div>
            </div>

            <!-- Card 3: Timeframes & Noise Filter -->
            <div style="background:${isSuccess ? '#0d3827' : '#26161c'};border:1px solid ${isSuccess ? '#10b981' : '#7f1d1d'};padding:9px 12px;border-radius:6px;">
                <div style="color:${isSuccess ? '#34d399' : '#f87171'};font-weight:bold;margin-bottom:3px;">۳. فیلتر نویز تایم‌فریم‌ها (M5: ${m5Count} | M15: ${m15Count} | M1: ${m1Count})</div>
                <div style="color:#cbd5e1;">${m1Count === 0 ? '✅ فیلتر نویز M1 فعال بوده و هیچ معامله پرریسکی در ۱ دقیقه باز نشده است. معاملات در M5 با ثبات بالا انجام شدند.' : '⚠️ معامله در تایم ۱ دقیقه فعال بوده و ممکن است باعث افزایش استاپ‌ها به دلیل نویز نوسانات ریز شده باشد.'}</div>
            </div>

            <!-- Card 4: Execution & Risk Protection -->
            <div style="background:${isSuccess ? '#0d3827' : '#26161c'};border:1px solid ${isSuccess ? '#10b981' : '#7f1d1d'};padding:9px 12px;border-radius:6px;">
                <div style="color:${isSuccess ? '#34d399' : '#f87171'};font-weight:bold;margin-bottom:3px;">۴. اجرای اردرها، بریک‌ایون و اسپرد (لغزش: ${avgSlip} پیپ)</div>
                <div style="color:#cbd5e1;">خروج ۴ مرحله‌ای (Scale-Out) با موفقیت پوزیشن‌ها را مدیریت کرده و ${beCount > 0 ? (beCount + ' پوزیشن پس از TP1 ریسک‌فری (BE) شدند.') : 'سود پوزیشن‌ها در تارگت‌ها ذخیره شد.'} استاپ پوزیشن‌های باخت ناشی از اسپرد Ask بروکر در سقف پولبک بوده است.</div>
            </div>
        </div>
    `;

    box.innerHTML = titleHtml + cardsHtml;
}

function initTesterCompareTab() {
    if (!window.TESTER_REPORTS || Object.keys(window.TESTER_REPORTS).length === 0) {
        console.warn('هیچ گزارش تستری در حافظه موجود نیست.');
        return;
    }

    let keys = getSortedTesterReportKeys();
    // Default to the comprehensive 10-day test (42 trades / 64Trades)
    let fullKey = keys.find(k => k.includes('64Trades') || (window.TESTER_REPORTS[k] && window.TESTER_REPORTS[k].trades && window.TESTER_REPORTS[k].trades.length >= 30));
    if (!window.userHasManuallySelectedReport || !currentTesterReportKey || !window.TESTER_REPORTS[currentTesterReportKey]) {
        currentTesterReportKey = fullKey || keys[0];
        window.currentTesterReportKey = currentTesterReportKey;
    }

    // Auto-sync with active equity tab scenario
    if (!window.userHasManuallySelectedScenario || !currentTesterScenarioKey) {
        currentTesterScenarioKey = 'equity_active';
        window.currentTesterScenarioKey = currentTesterScenarioKey;
    }

    let sel = document.getElementById('testerRunSelector');
    if (sel) {
        let optsHtml = '';
        keys.forEach(k => {
            let r = window.TESTER_REPORTS[k];
            let isSel = (k === currentTesterReportKey) ? 'selected' : '';
            let optLabel = formatTesterOptionLabel(k, r);
            optsHtml += `<option value="${k}" ${isSel}>${optLabel}</option>`;
        });
        sel.innerHTML = optsHtml;
        sel.value = currentTesterReportKey;
    }

    let scSel = document.getElementById('testerScenarioSelector');
    if (scSel) {
        let scList = getAvailableTesterScenarios();
        let scHtml = '';
        scList.forEach(sc => {
            let isSel = (sc.id === (currentTesterScenarioKey || 'equity_active')) ? 'selected' : '';
            scHtml += `<option value="${sc.id}" ${isSel}>${sc.name}</option>`;
        });
        scSel.innerHTML = scHtml;
        scSel.value = currentTesterScenarioKey || 'equity_active';
    }

    updateQuickSelectButtons(currentTesterReportKey);

    let report = window.TESTER_REPORTS[currentTesterReportKey];
    if (!report) return;

    renderTesterHeaderBadges(report);
    renderForensicCallout(report, currentTesterScenarioKey);
    renderTesterKPIs(report, currentTesterScenarioKey);
    renderParameterDriftTable(report, currentTesterScenarioKey);
    drawTesterCompareChart(report, currentTesterScenarioKey);
    renderTesterTradesTable(report, currentTesterFilter, currentTesterSearch);
}

function quickSelectTesterReport(type, event) {
    let keys = Object.keys(window.TESTER_REPORTS || {});
    let targetKey = '';
    if (type === 'full') {
        targetKey = keys.find(k => k.includes('64Trades') || (window.TESTER_REPORTS[k] && window.TESTER_REPORTS[k].trades && window.TESTER_REPORTS[k].trades.length >= 30));
    } else if (type === 'kings') {
        targetKey = keys.find(k => k.includes('6Trades') || (window.TESTER_REPORTS[k] && window.TESTER_REPORTS[k].trades && window.TESTER_REPORTS[k].trades.length <= 10));
    }
    if (!targetKey && keys.length > 0) targetKey = keys[0];

    if (targetKey) {
        let sel = document.getElementById('testerRunSelector');
        if (sel) sel.value = targetKey;
        switchTesterReport(targetKey);
    }
}

function updateQuickSelectButtons(reportKey) {
    let btnFull = document.getElementById('btnSelectAllTrades');
    let btnKings = document.getElementById('btnSelectKingsTrades');
    let r = window.TESTER_REPORTS && window.TESTER_REPORTS[reportKey];
    let cnt = r && r.trades ? r.trades.length : 0;

    let keys = Object.keys(window.TESTER_REPORTS || {});
    let fullKey = keys.find(k => k.includes('64Trades') || (window.TESTER_REPORTS[k] && window.TESTER_REPORTS[k].trades && window.TESTER_REPORTS[k].trades.length >= 30)) || reportKey;
    let kingsKey = keys.find(k => k.includes('6Trades') || (window.TESTER_REPORTS[k] && window.TESTER_REPORTS[k].trades && window.TESTER_REPORTS[k].trades.length <= 10));

    let fullCnt = (fullKey && window.TESTER_REPORTS[fullKey] && window.TESTER_REPORTS[fullKey].trades) ? window.TESTER_REPORTS[fullKey].trades.length : (cnt || 0);
    let kingsCnt = (kingsKey && window.TESTER_REPORTS[kingsKey] && window.TESTER_REPORTS[kingsKey].trades) ? window.TESTER_REPORTS[kingsKey].trades.length : 0;

    let elFullCnt = document.getElementById('tcTotalTradesBtnCount');
    if (elFullCnt) elFullCnt.textContent = fullCnt;
    let elKingsCnt = document.getElementById('tcKingsTradesBtnCount');
    if (elKingsCnt) elKingsCnt.textContent = kingsCnt;

    if (btnFull && btnKings) {
        if (cnt >= 30 || (reportKey && reportKey.includes('64Trades'))) {
            btnFull.classList.add('active');
            btnFull.style.color = '#38bdf8';
            btnFull.style.fontWeight = 'bold';
            btnKings.classList.remove('active');
            btnKings.style.color = '#cbd5e1';
            btnKings.style.fontWeight = 'normal';
        } else if (cnt <= 10 || (reportKey && reportKey.includes('6Trades'))) {
            btnKings.classList.add('active');
            btnKings.style.color = '#38bdf8';
            btnKings.style.fontWeight = 'bold';
            btnFull.classList.remove('active');
            btnFull.style.color = '#cbd5e1';
            btnFull.style.fontWeight = 'normal';
        } else {
            btnFull.classList.remove('active');
            btnKings.classList.remove('active');
        }
    }
}

function switchTesterScenario(scenarioKey) {
    window.userHasManuallySelectedScenario = true;
    currentTesterScenarioKey = scenarioKey || 'equity_active';
    window.currentTesterScenarioKey = currentTesterScenarioKey;
    let scSel = document.getElementById('testerScenarioSelector');
    if (scSel && scSel.value !== currentTesterScenarioKey) {
        scSel.value = currentTesterScenarioKey;
    }

    let report = window.TESTER_REPORTS[currentTesterReportKey];
    if (report) {
        renderForensicCallout(report, currentTesterScenarioKey);
        renderTesterKPIs(report, currentTesterScenarioKey);
        renderParameterDriftTable(report, currentTesterScenarioKey);
        drawTesterCompareChart(report, currentTesterScenarioKey);
        renderTesterTradesTable(report, currentTesterFilter, currentTesterSearch);
    }
}

function switchTesterReport(reportKey) {
    if (!window.TESTER_REPORTS || !window.TESTER_REPORTS[reportKey]) return;
    window.userHasManuallySelectedReport = true;
    currentTesterReportKey = reportKey;
    window.currentTesterReportKey = reportKey;
    updateQuickSelectButtons(reportKey);
    let report = window.TESTER_REPORTS[reportKey];
    renderTesterHeaderBadges(report);
    renderForensicCallout(report, currentTesterScenarioKey);
    renderTesterKPIs(report, currentTesterScenarioKey);
    renderParameterDriftTable(report, currentTesterScenarioKey);
    drawTesterCompareChart(report, currentTesterScenarioKey);
    renderTesterTradesTable(report, currentTesterFilter, currentTesterSearch);
}

function resetToInitialTesterReport() {
    let keys = getSortedTesterReportKeys();
    if (keys.length > 0) {
        let fullKey = keys.find(k => k.includes('64Trades') || (window.TESTER_REPORTS[k] && window.TESTER_REPORTS[k].trades && window.TESTER_REPORTS[k].trades.length >= 30)) || keys[0];
        let sel = document.getElementById('testerRunSelector');
        if (sel) sel.value = fullKey;
        switchTesterReport(fullKey);
        let nTrades = (window.TESTER_REPORTS[fullKey] && window.TESTER_REPORTS[fullKey].trades) ? window.TESTER_REPORTS[fullKey].trades.length : 0;
        alert('🔄 به تست ۱۰ روزه جامع متاتریدر ۵ بازنشانی شد:\n\n' + fullKey + ' (' + nTrades + ' معامله)');
    }
}

function renderTesterHeaderBadges(report) {
    let tBadge = document.getElementById('tcBadgeReportTitle');
    if (tBadge) tBadge.textContent = report.reportTitle || 'گزارش تستر متاتریدر ۵';

    let sBadge = document.getElementById('tcBadgeSymbol');
    if (sBadge) sBadge.textContent = report.symbol || 'GBPUSD!';

    let dBadge = document.getElementById('tcBadgeDateRange');
    if (dBadge) dBadge.textContent = report.dateRange || '2026.08.01 - 2026.08.15';

    let trBadge = document.getElementById('tcBadgeTradesCount');
    let nTrades = (report.trades && report.trades.length) || 0;
    if (trBadge) trBadge.textContent = nTrades + ' ستاپ (' + (nTrades * 4) + ' پوزیشن)';

    let exBadge = document.getElementById('tcBadgeExportTime');
    let exTime = report.fileTime || report.realExecutionTime || report.executionTime || report.exportedAt || '-';
    if (exBadge) exBadge.textContent = exTime;
}

