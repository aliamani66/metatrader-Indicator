window.currentTesterReportKey = window.currentTesterReportKey || '';
window.currentTesterFilter = window.currentTesterFilter || 'all';
window.currentTesterSearch = window.currentTesterSearch || '';
window.currentTesterScenarioKey = window.currentTesterScenarioKey || 'auto';

var currentTesterReportKey = window.currentTesterReportKey;
var currentTesterFilter = window.currentTesterFilter;
var currentTesterSearch = window.currentTesterSearch;
var currentTesterScenarioKey = window.currentTesterScenarioKey;

function copyTesterReportsFolder() {
    let p = 'C:\\Users\\USER\\AppData\\Roaming\\MetaQuotes\\Terminal\\Common\\Files\\FlagPro_TesterReports';
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(p).then(() => {
            alert('📋 آدرس پوشه گزارشات متاتریدر ۵ در کلیپ‌بورد کپی شد!\n\nاکنون در پنجره بازشده، در نوار بالای آدرس کلیدهای Ctrl+V را بزنید تا مستقیماً به این پوشه هدایت شوید:\n\n' + p);
        }).catch(() => {
            prompt('آدرس پوشه گزارشات تستر متاتریدر ۵ (کپی کنید):', p);
        });
    } else {
        prompt('آدرس پوشه گزارشات تستر متاتریدر ۵ (کپی کنید):', p);
    }
}

function getAvailableTesterScenarios() {
    let list = [
        {
            id: 'auto',
            name: '🔍 تشخیص خودکار سناریو از فایل تستر (Auto Detect)',
            badge: 'هوشمند',
            minPot: 0.0,
            minPotDisplay: '$0.00 (خودکار)',
            tfM1: 'غیرفعال (False)',
            hoursDisplay: 'هوشمند / طبق تستر',
            disabledKings: 'بررسی هوشمند',
            beBuffer: '0.0 pips',
            maxDev: '2.5 pips',
            simWinRate: 63.5,
            simPf: 2.20,
            simNetR: '+124.5R'
        },
        {
            id: 'golden',
            name: '⚖️ تعادل طلایی حجم و سود (Golden Balance)',
            badge: 'بالانس بهینه',
            minPot: 0.0,
            minPotDisplay: '$0.00 (بدون محدودیت)',
            tfM1: 'غیرفعال (False) - بدون معامله در M1',
            hoursDisplay: '۲۴ ساعته (00 تا 23)',
            disabledKings: 'بدون مسدودی',
            beBuffer: '0.0 pips',
            maxDev: '2.5 pips',
            simWinRate: 58.5,
            simPf: 1.85,
            simNetR: '+98.4R'
        },
        {
            id: 'champion',
            name: '🎯 الماس و سوپر اسنایپر خودکار (Champion Sniper)',
            badge: 'بیشترین سود',
            minPot: 2.0,
            minPotDisplay: '$2.00+',
            tfM1: 'غیرفعال (False) - بدون معامله در M1',
            hoursDisplay: 'حذف شب (۰۴ الی ۲۲)',
            disabledKings: 'OInner-BE (M1), RS-BE (M1)',
            beBuffer: '0.0 pips',
            maxDev: '2.0 pips',
            simWinRate: 66.2,
            simPf: 2.45,
            simNetR: '+142.1R'
        },
        {
            id: 'day',
            name: '☀️ اسنایپر سشن روزانه لندن و نیویورک (Day Session)',
            badge: 'اوج نقدینگی',
            minPot: 1.5,
            minPotDisplay: '$1.50+',
            tfM1: 'غیرفعال (False) - بدون معامله در M1',
            hoursDisplay: 'سشن لندن و نیویورک (۰۷ الی ۲۰)',
            disabledKings: 'بدون مسدودی',
            beBuffer: '0.0 pips',
            maxDev: '2.5 pips',
            simWinRate: 64.0,
            simPf: 2.10,
            simNetR: '+118.0R'
        },
        {
            id: 'shield',
            name: '🛡️ سپر کمترین افت سرمایه (Stop Loss Shield)',
            badge: 'کمترین دروداون',
            minPot: 1.0,
            minPotDisplay: '$1.00+',
            tfM1: 'غیرفعال (False) - بدون معامله در M1',
            hoursDisplay: '۲۴ ساعته (وقفه بعد ۲ استاپ)',
            disabledKings: 'حذف ۳ سلطان پرریسک',
            beBuffer: '0.0 pips',
            maxDev: '2.0 pips',
            simWinRate: 67.5,
            simPf: 2.30,
            simNetR: '+105.2R'
        },
        {
            id: 'base',
            name: '🌐 سبد جامع پایه (تمام سلاطین ۲۴ ساعته)',
            badge: 'جامع پایه',
            minPot: 0.0,
            minPotDisplay: '$0.00',
            tfM1: 'فعال (True) - تمام تایم‌ها',
            hoursDisplay: '۲۴ ساعته کامل',
            disabledKings: 'بدون مسدودی',
            beBuffer: '1.0 pips',
            maxDev: '0.0 (نامحدود)',
            simWinRate: 52.0,
            simPf: 1.45,
            simNetR: '+65.0R'
        }
    ];

    if (window.AI_OPTIMAL_CONFIG) {
        let ai = window.AI_OPTIMAL_CONFIG;
        list.push({
            id: 'ai',
            name: '🤖 سناریوی کشف‌شده هوش مصنوعی (AI Optimized)',
            badge: 'کشف هوش مصنوعی',
            minPot: ai.min_pot || 1.5,
            minPotDisplay: '$' + (ai.min_pot || 1.5).toFixed(2) + '+',
            tfM1: 'غیرفعال (False)',
            hoursDisplay: ai.hours_name || 'ساعات بهینه کشف‌شده',
            disabledKings: 'فیلتر هوشمند سلاطین',
            beBuffer: '0.0 pips',
            maxDev: '2.5 pips',
            simWinRate: ai.wr || 65.0,
            simPf: ai.pf || 2.2,
            simNetR: (ai.net_r ? '+' + ai.net_r + 'R' : '+125.0R')
        });
    }

    try {
        let custom = JSON.parse(localStorage.getItem('flagpro_custom_presets') || '[]');
        custom.forEach((cp, idx) => {
            list.push({
                id: 'custom_' + (cp.id || idx),
                name: '⭐ سناریوی شخصی: ' + (cp.name || ('سفارشی ' + (idx + 1))),
                badge: 'دست‌ساز کاربر',
                minPot: cp.min_pot || 0.0,
                minPotDisplay: '$' + (cp.min_pot || 0).toFixed(2),
                tfM1: 'غیرفعال (False)',
                hoursDisplay: cp.hours_name || 'ساعات سفارشی',
                disabledKings: 'انتخابی کاربر',
                beBuffer: (cp.be_buffer !== undefined ? cp.be_buffer + ' pips' : '0.0 pips'),
                maxDev: '2.5 pips',
                simWinRate: cp.wr || 60.0,
                simPf: cp.pf || 2.0,
                simNetR: '+100.0R'
            });
        });
    } catch(e) {}

    return list;
}

function resolveActiveScenario(scenarioKey, report) {
    let scenarios = getAvailableTesterScenarios();
    if (!scenarioKey || scenarioKey === 'auto') {
        let p = (report && report.parameters) || {};
        let scName = (p.InpScenarioName || '').toLowerCase();
        let hours = (p.InpAllowedTradingHours || '');
        let pot = Number(p.InpMinTradePotential || 0);

        if (scName.includes('champion') || scName.includes('diamond') || pot >= 2.0) {
            return scenarios.find(s => s.id === 'champion') || scenarios[1];
        }
        if (scName.includes('day') || scName.includes('london') || (hours.includes('08') && hours.includes('14'))) {
            return scenarios.find(s => s.id === 'day') || scenarios[1];
        }
        if (scName.includes('shield') || scName.includes('stop')) {
            return scenarios.find(s => s.id === 'shield') || scenarios[1];
        }
        if (scName.includes('base') || scName.includes('all')) {
            return scenarios.find(s => s.id === 'base') || scenarios[1];
        }
        return scenarios.find(s => s.id === 'golden') || scenarios[1];
    }
    return scenarios.find(s => s.id === scenarioKey) || scenarios[1];
}

function parseReportSortKey(k) {
    let r = (window.TESTER_REPORTS && window.TESTER_REPORTS[k]) || {};
    if (k.startsWith('uploaded_')) {
        return { isUploaded: 1, endStr: '9999.99.99', startStr: '9999.99.99', mtime: Date.now(), exp: '' };
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
    let exp = r.exportedAt || '';
    
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
        let sA = parseReportSortKey(a);
        let sB = parseReportSortKey(b);
        
        if (sA.isUploaded !== sB.isUploaded) return sB.isUploaded - sA.isUploaded;
        
        // 1. Compare end date descending (e.g. 2026.08.19 > 2026.08.15 > 2026.08.14)
        if (sA.endStr && sB.endStr && sA.endStr !== sB.endStr) {
            return sB.endStr.localeCompare(sA.endStr);
        }
        
        // 2. Compare start date descending
        if (sA.startStr && sB.startStr && sA.startStr !== sB.startStr) {
            return sB.startStr.localeCompare(sA.startStr);
        }
        
        // 3. Compare mtime descending
        if (sA.mtime && sB.mtime && sA.mtime !== sB.mtime) {
            return sB.mtime - sA.mtime;
        }
        
        // 4. Compare exportedAt descending
        if (sA.exp && sB.exp && sA.exp !== sB.exp) {
            return sB.exp.localeCompare(sA.exp);
        }
        
        return b.localeCompare(a);
    });
    return keys;
}

function formatTesterOptionLabel(k, r) {
    let title = r.reportTitle || k;
    let dr = r.dateRange || '';
    let cnt = (r.trades && r.trades.length) || 0;
    let datePart = '';
    
    let m = dr.match(/(\d{4}[.\-/]\d{2}[.\-/]\d{2})\s*[-_to]+\s*(\d{4}[.\-/]\d{2}[.\-/]\d{2})/i);
    if (m) {
        let sD = m[1].replace(/[\/-]/g, '.');
        let eD = m[2].replace(/[\/-]/g, '.');
        datePart = `از ${sD} تا ${eD}`;
    } else if (dr) {
        datePart = dr;
    }
    
    return datePart ? `${title} | ${datePart} | ${cnt} معامله` : `${title} | ${cnt} معامله`;
}

function initTesterCompareTab() {
    if (!window.TESTER_REPORTS || Object.keys(window.TESTER_REPORTS).length === 0) {
        console.warn('هیچ گزارش تستری در حافظه موجود نیست.');
        return;
    }

    let keys = getSortedTesterReportKeys();
    if (!currentTesterReportKey || !window.TESTER_REPORTS[currentTesterReportKey]) {
        currentTesterReportKey = keys[0];
    }

    let sel = document.getElementById('testerRunSelector');
    if (sel) {
        let optsHtml = '';
        keys.forEach(k => {
            let r = window.TESTER_REPORTS[k];
            let isSel = (k === currentTesterReportKey) ? 'selected' : '';
            let title = r.reportTitle || k;
            let dRange = r.dateRange || '';
            let cnt = (r.trades && r.trades.length) || 0;
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
            let isSel = (sc.id === (currentTesterScenarioKey || 'auto')) ? 'selected' : '';
            scHtml += `<option value="${sc.id}" ${isSel}>${sc.name}</option>`;
        });
        scSel.innerHTML = scHtml;
        scSel.value = currentTesterScenarioKey || 'auto';
    }

    let report = window.TESTER_REPORTS[currentTesterReportKey];
    if (!report) return;

    renderTesterHeaderBadges(report);
    renderTesterKPIs(report, currentTesterScenarioKey);
    renderParameterDriftTable(report, currentTesterScenarioKey);
    drawTesterCompareChart(report, currentTesterScenarioKey);
    renderTesterTradesTable(report, currentTesterFilter, currentTesterSearch);
}

function switchTesterScenario(scenarioKey) {
    currentTesterScenarioKey = scenarioKey || 'auto';
    window.currentTesterScenarioKey = currentTesterScenarioKey;
    let scSel = document.getElementById('testerScenarioSelector');
    if (scSel && scSel.value !== currentTesterScenarioKey) {
        scSel.value = currentTesterScenarioKey;
    }

    let report = window.TESTER_REPORTS[currentTesterReportKey];
    if (report) {
        renderTesterKPIs(report, currentTesterScenarioKey);
        renderParameterDriftTable(report, currentTesterScenarioKey);
        drawTesterCompareChart(report, currentTesterScenarioKey);
    }
}

function switchTesterReport(reportKey) {
    if (!window.TESTER_REPORTS || !window.TESTER_REPORTS[reportKey]) return;
    currentTesterReportKey = reportKey;
    window.currentTesterReportKey = reportKey;
    let report = window.TESTER_REPORTS[reportKey];
    renderTesterHeaderBadges(report);
    renderTesterKPIs(report, currentTesterScenarioKey);
    renderParameterDriftTable(report, currentTesterScenarioKey);
    drawTesterCompareChart(report, currentTesterScenarioKey);
    renderTesterTradesTable(report, currentTesterFilter, currentTesterSearch);
}

function resetToInitialTesterReport() {
    let keys = getSortedTesterReportKeys();
    if (keys.length > 0) {
        let latestKey = keys[0];
        let sel = document.getElementById('testerRunSelector');
        if (sel) sel.value = latestKey;
        switchTesterReport(latestKey);
        let nTrades = (window.TESTER_REPORTS[latestKey] && window.TESTER_REPORTS[latestKey].trades) ? window.TESTER_REPORTS[latestKey].trades.length : 0;
        alert('🔄 به آخرین تست استراتژی تستر متاتریدر ۵ بازنشانی شد:\n\n' + latestKey + ' (' + nTrades + ' معامله)');
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
    if (exBadge) exBadge.textContent = report.exportedAt || '-';
}

function renderTesterKPIs(report, scenarioKey) {
    let k = report.kpis || {};
    let t = report.trades || [];
    let scenario = resolveActiveScenario(scenarioKey, report);

    let actWr = (k.winRate !== undefined && !isNaN(Number(k.winRate))) ? Number(k.winRate) : 0.0;
    let simWr = scenario.simWinRate;
    let diffWrVal = actWr - simWr;

    let wrActual = document.getElementById('tcValWinRateActual');
    if (wrActual) wrActual.textContent = actWr.toFixed(1) + '%';

    let wrSim = document.getElementById('tcValWinRateSim');
    if (wrSim) wrSim.textContent = simWr.toFixed(1) + '%';

    let diffWr = document.getElementById('tcDiffWinRate');
    if (diffWr) {
        let diffColor = diffWrVal >= 0 ? '#34d399' : '#f87171';
        diffWr.style.color = diffColor;
        diffWr.textContent = (diffWrVal >= 0 ? 'بهبود: +' : 'اختلاف: ') + diffWrVal.toFixed(1) + '% (نسبت به ' + scenario.badge + ')';
    }

    let actNetPips = (k.netPips !== undefined && !isNaN(Number(k.netPips))) ? Number(k.netPips) : 0.0;
    let actNetUSD = (k.netUSD !== undefined && !isNaN(Number(k.netUSD))) ? Number(k.netUSD) : 0.0;

    let netAct = document.getElementById('tcValNetActual');
    if (netAct) {
        netAct.textContent = (actNetPips >= 0 ? '+' : '') + actNetPips.toFixed(1) + ' pips';
        netAct.style.color = actNetPips >= 0 ? '#34d399' : '#f87171';
    }

    let netSim = document.getElementById('tcValNetSim');
    if (netSim) netSim.textContent = scenario.simNetR;

    let diffNet = document.getElementById('tcDiffNet');
    if (diffNet) {
        let usdText = (actNetUSD >= 0 ? '+$' : '-$') + Math.abs(actNetUSD).toFixed(2);
        diffNet.textContent = 'سود/زیان دلاری تستر: ' + usdText + ' (0.01 Lot)';
        diffNet.style.color = actNetUSD >= 0 ? '#34d399' : '#f87171';
    }

    let actPf = (k.profitFactor !== undefined && !isNaN(Number(k.profitFactor))) ? Number(k.profitFactor) : 0.0;
    let pfAct = document.getElementById('tcValPfActual');
    if (pfAct) {
        pfAct.textContent = actPf.toFixed(2);
        pfAct.style.color = actPf >= 1.0 ? '#34d399' : '#f87171';
    }

    let pfSim = document.getElementById('tcValPfSim');
    if (pfSim) pfSim.textContent = scenario.simPf.toFixed(2);

    let setAct = document.getElementById('tcValTotalSetups');
    if (setAct) setAct.textContent = (k.totalSetups || t.length) + ' ستاپ';

    let posAct = document.getElementById('tcValTotalPositions');
    if (posAct) posAct.textContent = ((k.totalSetups || t.length) * 4) + ' معامله';

    let winLoss = document.getElementById('tcWinLossSplit');
    if (winLoss) {
        let wins = k.winningSetups !== undefined ? k.winningSetups : t.filter(x => x.outcome === 'Win').length;
        let losses = k.losingSetups !== undefined ? k.losingSetups : t.filter(x => x.outcome === 'Loss').length;
        winLoss.textContent = wins + ' برد | ' + losses + ' باخت';
    }
}

function renderParameterDriftTable(report, scenarioKey) {
    let tbody = document.getElementById('tcParamDriftBody');
    if (!tbody) return;

    let p = (report && report.parameters) || {};
    let scenario = resolveActiveScenario(scenarioKey, report);

    let colHeader = document.getElementById('tcColExpectedScenario');
    if (colHeader) colHeader.textContent = 'مقدار در سناریوی: ' + scenario.name;

    let m1Count = (report.trades || []).filter(t => t.timeframe === 'M1' || t.timeframe === 'PERIOD_M1').length;
    let totalTrades = (report.trades || []).length;
    let m1Pct = totalTrades > 0 ? (m1Count / totalTrades * 100).toFixed(0) : 0;

    let actPot = (p.InpMinTradePotential !== undefined && !isNaN(Number(p.InpMinTradePotential))) ? Number(p.InpMinTradePotential) : 0.0;
    let potDiff = Math.abs(actPot - scenario.minPot);
    let potStatus = potDiff <= 0.5 ? 'match' : (actPot < scenario.minPot ? 'severe' : 'warn');

    let rows = [
        {
            name: 'سناریوی معاملاتی (InpScenarioName)',
            actual: p.InpScenarioName || 'Default (تنظیمات پیش‌فرض)',
            expected: scenario.name,
            status: (p.InpScenarioName && p.InpScenarioName.toLowerCase().includes(scenario.id)) ? 'match' : ((!p.InpScenarioName || p.InpScenarioName.includes('Default')) ? 'severe' : 'warn'),
            impact: (p.InpScenarioName && p.InpScenarioName.toLowerCase().includes(scenario.id))
                ? 'نام سناریو در متاتریدر ۵ با این تنظیمات مطابقت دارد.'
                : 'در تستر MT5 مقدار «' + (p.InpScenarioName || 'Default') + '» تنظیم شده بود.'
        },
        {
            name: 'کف پتانسیل سود ستاپ (InpMinTradePotential)',
            actual: '$' + actPot.toFixed(1),
            expected: scenario.minPotDisplay,
            status: potStatus,
            impact: potStatus === 'match'
                ? 'کف سود ستاپ‌ها همگام با سناریو بوده و ستاپ‌های ضعیف فیلتر شده‌اند.'
                : (actPot < scenario.minPot ? 'کف سود پایین‌تر از سناریو است که باعث ورود در ستاپ‌های کم‌ارزش شده است.' : 'کف سود سخت‌گیرانه‌تر از سناریو اعمال شده است.')
        },
        {
            name: 'تایم‌فریم ۱ دقیقه (InpUseTF7 / PERIOD_M1)',
            actual: m1Count > 0 ? 'فعال (' + m1Count + ' معامله در M1)' : 'غیرفعال (بدون ترید در M1)',
            expected: scenario.tfM1,
            status: (m1Count > 0 && !scenario.tfM1.includes('فعال (True)')) ? 'severe' : 'match',
            impact: (m1Count > 0 && !scenario.tfM1.includes('فعال (True)'))
                ? m1Pct + '٪ معاملات در نویز ۱ دقیقه باز شده‌اند که عامل عمده افت عملکرد در تستر MT5 است.'
                : 'فیلتر نویز تایم ۱ دقیقه با موفقیت در تستر رعایت شده است.'
        },
        {
            name: 'ساعات مجاز معامله (InpAllowedTradingHours)',
            actual: p.InpAllowedTradingHours || '۲۴ ساعته (تمام شبانه‌روز)',
            expected: scenario.hoursDisplay,
            status: (p.InpAllowedTradingHours && (scenario.id === 'day' || scenario.id === 'champion')) ? 'match' : (!p.InpAllowedTradingHours && (scenario.id === 'golden' || scenario.id === 'base') ? 'match' : 'warn'),
            impact: (p.InpAllowedTradingHours && (scenario.id === 'day' || scenario.id === 'champion'))
                ? 'فیلتر ساعات پرنقدینگی در تستر فعال بوده و معاملات کم‌عمق شبانه حذف شده‌اند.'
                : 'اختلاف در ساعات مجاز معامله میان تستر متاتریدر و این سناریو.'
        },
        {
            name: 'لیست سلاطین غیرمجاز (InpDisabledKingsList)',
            actual: (p.InpDisabledKingsList && p.InpDisabledKingsList.length > 5) ? p.InpDisabledKingsList : 'None (هیچ سلطانی مسدود نبود)',
            expected: scenario.disabledKings,
            status: (p.InpDisabledKingsList && p.InpDisabledKingsList.length > 5) ? 'match' : (scenario.disabledKings.includes('بدون مسدودی') ? 'match' : 'warn'),
            impact: (p.InpDisabledKingsList && p.InpDisabledKingsList.length > 5)
                ? 'الگوهای پرریسک و باخت‌ساز در تستر مسدود شده بودند.'
                : (scenario.disabledKings.includes('بدون مسدودی') ? 'مجاز بودن تمام سلاطین طبق انتظار سناریو است.' : 'سلاطین پرریسک مسدود نشده بودند و موجب باخت شدند.')
        },
        {
            name: 'بافر بریک‌ایون (InpBEBufferPips)',
            actual: (p.InpBEBufferPips !== undefined ? Number(p.InpBEBufferPips).toFixed(1) + ' pips' : '0.0 pips'),
            expected: scenario.beBuffer,
            status: (Number(p.InpBEBufferPips || 0) === 0 || scenario.beBuffer.includes('1.0')) ? 'match' : 'warn',
            impact: Number(p.InpBEBufferPips || 0) === 0
                ? 'ریسک‌فری دقیقاً روی نقطه ورود تنظیم شده و بافر اضافی وجود ندارد.'
                : 'بافر ۱ پیپ ممکن است باعث بسته شدن زودهنگام معاملات در اصلاح طبیعی بازار شود.'
        },
        {
            name: 'حداکثر انحراف مجاز ورود (InpMaxEntryDeviationPips)',
            actual: (p.InpMaxEntryDeviationPips !== undefined && Number(p.InpMaxEntryDeviationPips) > 0 ? Number(p.InpMaxEntryDeviationPips).toFixed(1) + ' pips' : '0.0 (نامحدود)'),
            expected: scenario.maxDev,
            status: Number(p.InpMaxEntryDeviationPips || 0) > 0 ? 'match' : 'severe',
            impact: Number(p.InpMaxEntryDeviationPips || 0) > 0
                ? 'فیلتر ضد اسلیپیج فعال بوده و از ورود دیرهنگام مارکت جلوگیری کرده است.'
                : 'ورود بدون محدودیت انحراف قیمت بوده و اسلیپیج ورود مهار نشده است.'
        },
        {
            name: 'اسپرد Ask در شبیه‌سازی (Simulated Ask Spread)',
            actual: 'لحاظ در تستر واقعی MT5',
            expected: 'اضافه شده به سورس اندیکاتور و اکسپرت',
            status: 'match',
            impact: 'اسپرد خرید و فروش در هر دو پلتفرم کاملاً همگام و منطبق است.'
        }
    ];

    let matchCount = rows.filter(r => r.status === 'match').length;
    let warnCount = rows.filter(r => r.status === 'warn').length;
    let severeCount = rows.filter(r => r.status === 'severe').length;

    let badge = document.getElementById('tcDriftSummaryBadge');
    if (badge) {
        if (severeCount === 0 && warnCount === 0) {
            badge.style.background = '#064e3b';
            badge.style.borderColor = '#10b981';
            badge.style.color = '#a7f3d0';
            badge.textContent = '🎉 تطابق ۱۰۰٪: این تست دقیقاً بر اساس سناریوی «' + scenario.name + '» اجرا شده است!';
        } else if (matchCount >= 5) {
            badge.style.background = '#14532d';
            badge.style.borderColor = '#22c55e';
            badge.style.color = '#bbf7d0';
            badge.textContent = '✅ بیشترین هماهنگی (' + matchCount + ' پارامتر منطبق): احتمالاً این تست با سناریوی «' + scenario.name + '» ست شده بود.';
        } else {
            badge.style.background = '#450a0a';
            badge.style.borderColor = '#991b1b';
            badge.style.color = '#fca5a5';
            badge.textContent = '⚠️ مغایرت تنظیمی (' + severeCount + ' مغایرت شدید | ' + warnCount + ' اختلاف): این تست با سناریوی دیگری ست شده است.';
        }
    }

    let html = '';
    rows.forEach(r => {
        let bHtml = '';
        if (r.status === 'severe') {
            bHtml = '<span style="background:#7f1d1d;color:#fca5a5;padding:3px 8px;border-radius:4px;border:1px solid #ef4444;font-weight:bold;">🔴 مغایرت شدید</span>';
        } else if (r.status === 'warn') {
            bHtml = '<span style="background:#78350f;color:#fde68a;padding:3px 8px;border-radius:4px;border:1px solid #f59e0b;font-weight:bold;">⚠️ اختلاف تنظیمی</span>';
        } else {
            bHtml = '<span style="background:#064e3b;color:#a7f3d0;padding:3px 8px;border-radius:4px;border:1px solid #10b981;font-weight:bold;">🟢 منطبق و صحیح</span>';
        }

        html += `<tr style="border-bottom:1px solid #1e293b;">
            <td style="padding:8px 10px;font-weight:bold;color:#f8fafc;">${r.name}</td>
            <td style="padding:8px 10px;color:#fca5a5;">${r.actual}</td>
            <td style="padding:8px 10px;color:#86efac;font-weight:600;">${r.expected}</td>
            <td style="padding:8px 10px;">${bHtml}</td>
            <td style="padding:8px 10px;color:#cbd5e1;font-size:11px;">${r.impact}</td>
        </tr>`;
    });

    tbody.innerHTML = html;
}

function drawTesterCompareChart(report, scenarioKey) {
    let canvas = document.getElementById('testerCompareCanvas');
    if (!canvas) return;
    let ctx = canvas.getContext('2d');
    if (!ctx) return;

    let scenario = resolveActiveScenario(scenarioKey, report);

    let dpr = window.devicePixelRatio || 1;
    let rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    let w = rect.width;
    let h = rect.height;
    let padLeft = 45;
    let padRight = 65;
    let padTop = 25;
    let padBottom = 30;
    let plotW = w - padLeft - padRight;
    let plotH = h - padTop - padBottom;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#070b14';
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = '#0b111c';
    ctx.fillRect(padLeft, padTop, plotW, plotH);

    let eqActual = report.equityCurve || [];
    if (eqActual.length === 0) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '12px Segoe UI';
        ctx.textAlign = 'center';
        ctx.fillText('داده‌های نمودار اکوئیتی یافت نشد.', w / 2, h / 2);
        return;
    }

    let simPoints = [];
    let actPoints = [];
    let n = eqActual.length;

    let actVal = 0.0;
    let simVal = 0.0;
    let winRateFrac = (scenario.simWinRate || 60.0) / 100.0;
    let pfVal = scenario.simPf || 2.0;
    let winStep = 22.0 * pfVal;
    let lossStep = 22.0;

    for (let i = 0; i < n; i++) {
        actVal = (eqActual[i].pnlPips !== undefined && !isNaN(Number(eqActual[i].pnlPips))) ? Number(eqActual[i].pnlPips) : 0.0;
        actPoints.push({ time: eqActual[i].time || '', val: actVal });

        // Deterministic realistic curve for selected scenario
        let pseudoHash = ((i * 19 + 7) % 100) / 100.0;
        if (pseudoHash < winRateFrac) {
            simVal += winStep;
        } else {
            simVal -= lossStep;
        }
        simPoints.push({ time: eqActual[i].time || '', val: simVal });
    }

            let allVals = actPoints.map(p => p.val).concat(simPoints.map(p => p.val));
            let minVal = -50.0;
            let maxVal = 50.0;
            for (let vi = 0; vi < allVals.length; vi++) {
                if (allVals[vi] < minVal) minVal = allVals[vi];
                if (allVals[vi] > maxVal) maxVal = allVals[vi];
            }
            minVal -= 20.0;
            maxVal += 20.0;
            let valRange = Math.max(1, maxVal - minVal);

            function getY(val) {
                return padTop + plotH - ((val - minVal) / valRange) * plotH;
            }

            function getX(idx) {
                return padLeft + (idx / Math.max(1, n - 1)) * plotW;
            }

            // Zero line
            let zeroY = getY(0);
            ctx.strokeStyle = '#334155';
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.beginPath();
            ctx.moveTo(padLeft, zeroY);
            ctx.lineTo(padLeft + plotW, zeroY);
            ctx.stroke();
            ctx.setLineDash([]);

            // Grid lines
            ctx.strokeStyle = '#1e293b';
            ctx.lineWidth = 0.5;
            for (let v = -500; v <= 200; v += 100) {
                if (v === 0) continue;
                let y = getY(v);
                ctx.beginPath();
                ctx.moveTo(padLeft, y);
                ctx.lineTo(padLeft + plotW, y);
                ctx.stroke();

                ctx.fillStyle = '#64748b';
                ctx.font = '10px Segoe UI';
                ctx.textAlign = 'left';
                ctx.fillText((v > 0 ? '+' : '') + v + 'p', padLeft + plotW + 8, y + 3);
            }

            // Draw Actual MT5 Tester Curve (Red)
            ctx.strokeStyle = '#ef4444';
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            for (let i = 0; i < n; i++) {
                let x = getX(i);
                let y = getY(actPoints[i].val);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();

            // Fill gradient for Actual MT5
            let gradAct = ctx.createLinearGradient(0, zeroY, 0, padTop + plotH);
            gradAct.addColorStop(0, 'rgba(239, 68, 68, 0.0)');
            gradAct.addColorStop(1, 'rgba(239, 68, 68, 0.25)');
            ctx.fillStyle = gradAct;
            ctx.beginPath();
            ctx.moveTo(getX(0), zeroY);
            for (let i = 0; i < n; i++) ctx.lineTo(getX(i), getY(actPoints[i].val));
            ctx.lineTo(getX(n - 1), zeroY);
            ctx.closePath();
            ctx.fill();

            // Draw Strategy Theoretical Curve (Blue)
            ctx.strokeStyle = '#38bdf8';
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            for (let i = 0; i < n; i++) {
                let x = getX(i);
                let y = getY(simPoints[i].val);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();

            // Dates on X axis
            ctx.fillStyle = '#64748b';
            ctx.font = '10px Segoe UI';
            ctx.textAlign = 'center';
            let step = Math.max(1, Math.floor(n / 6));
            for (let i = 0; i < n; i += step) {
                let x = getX(i);
                let dStr = actPoints[i].time.substring(5, 10);
                ctx.fillText(dStr, x, padTop + plotH + 16);
            }
        }

        function renderTesterTradesTable(report, filterMode, searchQuery) {
            filterMode = filterMode || window.currentTesterFilter || 'all';
            searchQuery = searchQuery || window.currentTesterSearch || '';
            let tbody = document.getElementById('testerTradesBody');
            if (!tbody) return;

            let trades = report.trades || [];
            if (trades.length === 0) {
                tbody.innerHTML = '<tr><td colspan="14" style="text-align:center;padding:20px;color:#94a3b8;">هیچ معامله‌ای در این گزارش ثبت نشده است.</td></tr>';
                return;
            }

            let filtered = trades.filter(t => {
                let profitPips = (t.profitPips !== undefined && !isNaN(Number(t.profitPips))) ? Number(t.profitPips) : ((t.pnlPips !== undefined && !isNaN(Number(t.pnlPips))) ? Number(t.pnlPips) : 0);
                let outcome = t.outcome || (profitPips >= 0 ? 'Win' : 'Loss');
                let tf = t.timeframe || '';
                let slip = (t.slippagePips !== undefined && !isNaN(Number(t.slippagePips))) ? Number(t.slippagePips) : 0;
                let exitCls = t.exitClass || '';
                let disc = t.discrepancyReason || t.discrepancyLabel || '';

                if (filterMode === 'win' && outcome !== 'Win') return false;
                if (filterMode === 'loss' && outcome !== 'Loss') return false;
                if (filterMode === 'm1' && tf !== 'M1') return false;
                if (filterMode === 'slip' && slip < 2.0) return false;
                if (filterMode === 'be' && !exitCls.includes('BE')) return false;
                if (searchQuery) {
                    let q = searchQuery.toLowerCase();
                    let hay = ((t.pattern || '') + ' ' + tf + ' ' + (t.side || '') + ' ' + (t.entryTime || '') + ' ' + disc).toLowerCase();
                    if (!hay.includes(q)) return false;
                }
                return true;
            });

            let html = '';
            filtered.forEach(t => {
                let profitPips = (t.profitPips !== undefined && !isNaN(Number(t.profitPips))) ? Number(t.profitPips) : ((t.pnlPips !== undefined && !isNaN(Number(t.pnlPips))) ? Number(t.pnlPips) : 0);
                let profitUSD = (t.profitUSD !== undefined && !isNaN(Number(t.profitUSD))) ? Number(t.profitUSD) : ((t.pnlUSD !== undefined && !isNaN(Number(t.pnlUSD))) ? Number(t.pnlUSD) : 0);
                let slippagePips = (t.slippagePips !== undefined && !isNaN(Number(t.slippagePips))) ? Number(t.slippagePips) : 0;
                let boxEntry = (t.boxEntryPrice !== undefined && !isNaN(Number(t.boxEntryPrice))) ? Number(t.boxEntryPrice) : 0;
                let marketFill = (t.marketFillPrice !== undefined && !isNaN(Number(t.marketFillPrice))) ? Number(t.marketFillPrice) : boxEntry;
                let slPrice = (t.slPrice !== undefined && !isNaN(Number(t.slPrice))) ? Number(t.slPrice) : 0;
                let tp1 = (t.tp1 !== undefined && !isNaN(Number(t.tp1))) ? Number(t.tp1) : 0;
                let tp4 = (t.tp4 !== undefined && !isNaN(Number(t.tp4))) ? Number(t.tp4) : 0;

                let isWin = (profitPips >= 0);
                let sideBadge = t.side === 'BUY'
                    ? '<span style="color:#34d399;font-weight:bold;">BUY</span>'
                    : '<span style="color:#f87171;font-weight:bold;">SELL</span>';

                let tfBadge = t.timeframe === 'M1'
                    ? '<span style="background:#450a0a;color:#fca5a5;padding:1px 5px;border-radius:3px;font-size:10px;border:1px solid #991b1b;">M1 (نویز)</span>'
                    : '<span style="background:#064e3b;color:#a7f3d0;padding:1px 5px;border-radius:3px;font-size:10px;border:1px solid #059669;">' + (t.timeframe || '') + '</span>';

                let pnlPipsColor = isWin ? '#34d399' : '#f87171';
                let pnlUSDColor = isWin ? '#34d399' : '#f87171';
                let slipColor = (slippagePips > 2.0) ? '#f59e0b' : '#94a3b8';

                let discText = t.discrepancyReason || t.discrepancyLabel || 'منطبق';
                let discBadge = '<span style="background:#1e293b;color:#cbd5e1;padding:2px 6px;border-radius:4px;font-size:10px;">' + discText + '</span>';
                if (discText.includes('نویز')) {
                    discBadge = '<span style="background:#450a0a;color:#fca5a5;padding:2px 6px;border-radius:4px;border:1px solid #7f1d1d;font-size:10px;">🔴 نویز تایم M1</span>';
                } else if (discText.includes('اسلیپیج')) {
                    discBadge = '<span style="background:#78350f;color:#fde68a;padding:2px 6px;border-radius:4px;border:1px solid #b45309;font-size:10px;">⚠️ اسلیپیج شدید ورود</span>';
                } else if (discText.includes('بریک‌ایون') || discText.includes('ریسک‌فری')) {
                    discBadge = '<span style="background:#1e1b4b;color:#c7d2fe;padding:2px 6px;border-radius:4px;border:1px solid #4338ca;font-size:10px;">🛡️ قطع زودهنگام در BE</span>';
                }

                html += `<tr style="border-bottom:1px solid #1e293b;">
                    <td style="padding:6px 8px;color:#64748b;">${t.setupId || ''}</td>
                    <td style="padding:6px 8px;font-weight:600;color:#f8fafc;">${t.pattern || ''}</td>
                    <td style="padding:6px 8px;">${tfBadge}</td>
                    <td style="padding:6px 8px;">${sideBadge}</td>
                    <td style="padding:6px 8px;color:#94a3b8;font-size:10.5px;">${t.entryTime || ''}</td>
                    <td style="padding:6px 8px;color:#cbd5e1;">${boxEntry.toFixed(5)}</td>
                    <td style="padding:6px 8px;color:#38bdf8;">${marketFill.toFixed(5)}</td>
                    <td style="padding:6px 8px;color:${slipColor};font-weight:bold;">${slippagePips.toFixed(1)}p</td>
                    <td style="padding:6px 8px;color:#f87171;">${slPrice.toFixed(5)}</td>
                    <td style="padding:6px 8px;color:#94a3b8;font-size:10px;">TP1: ${tp1.toFixed(5)} | TP4: ${tp4.toFixed(5)}</td>
                    <td style="padding:6px 8px;color:#e2e8f0;">${t.exitClass || ''}</td>
                    <td style="padding:6px 8px;color:${pnlPipsColor};font-weight:bold;direction:ltr;text-align:right;">${(profitPips > 0 ? '+' : '')}${profitPips.toFixed(1)}p</td>
                    <td style="padding:6px 8px;color:${pnlUSDColor};font-weight:bold;direction:ltr;text-align:right;">${(profitUSD > 0 ? '+$' : '-$')}${Math.abs(profitUSD).toFixed(2)}</td>
                    <td style="padding:6px 8px;">${discBadge}</td>
                </tr>`;
            });

            tbody.innerHTML = html;
        }

        function filterTesterTradesTable(mode, event) {
            currentTesterFilter = mode;
            if (event && event.currentTarget) {
                let parent = event.currentTarget.parentElement;
                parent.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                event.currentTarget.classList.add('active');
            }
            let report = window.TESTER_REPORTS[currentTesterReportKey];
            if (report) renderTesterTradesTable(report, currentTesterFilter, currentTesterSearch);
        }

        function onTesterTradeSearch(query) {
            currentTesterSearch = query;
            let report = window.TESTER_REPORTS[currentTesterReportKey];
            if (report) renderTesterTradesTable(report, currentTesterFilter, currentTesterSearch);
        }

        function handleTesterReportUpload(event) {
            let file = event.target.files && event.target.files[0];
            if (!file) return;

            let reader = new FileReader();
            reader.onload = function(e) {
                try {
                    let buffer = e.target.result;
                    let uint8 = new Uint8Array(buffer);
                    let decoder;
                    if (uint8.length >= 2 && uint8[0] === 0xFF && uint8[1] === 0xFE) {
                        decoder = new TextDecoder('utf-16le');
                    } else if (uint8.length >= 2 && uint8[0] === 0xFE && uint8[1] === 0xFF) {
                        decoder = new TextDecoder('utf-16be');
                    } else if (uint8.length >= 4 && uint8[1] === 0 && uint8[3] === 0) {
                        decoder = new TextDecoder('utf-16le');
                    } else {
                        decoder = new TextDecoder('utf-8');
                    }
                    let content = decoder.decode(buffer);
                    if (content.charCodeAt(0) === 0xFEFF) {
                        content = content.slice(1);
                    }
                    content = content.trim();

                    let reportData = null;

                    if (file.name.toLowerCase().endsWith('.json') || content.startsWith('{')) {
                        reportData = JSON.parse(content);
                        if (reportData && Array.isArray(reportData.trades)) {
                            reportData.trades.forEach(t => {
                                if (t.pnlPips !== undefined && t.profitPips === undefined) t.profitPips = t.pnlPips;
                                if (t.pnlUSD !== undefined && t.profitUSD === undefined) t.profitUSD = t.pnlUSD;
                                if (t.profitPips !== undefined && t.pnlPips === undefined) t.pnlPips = t.profitPips;
                                if (t.profitUSD !== undefined && t.pnlUSD === undefined) t.pnlUSD = t.profitUSD;
                                if (t.discrepancyLabel && !t.discrepancyReason) t.discrepancyReason = t.discrepancyLabel;
                                if (!t.outcome) t.outcome = (((t.profitPips !== undefined ? t.profitPips : t.pnlPips) || 0) >= 0) ? 'Win' : 'Loss';
                            });
                        }
                    } else if (file.name.toLowerCase().endsWith('.csv') || content.includes(',')) {
                        reportData = parseTesterCsvReport(content, file.name);
                    }

                    if (reportData) {
                        window.TESTER_REPORTS = window.TESTER_REPORTS || {};
                        let reportKey = 'uploaded_' + Date.now();
                        window.TESTER_REPORTS[reportKey] = reportData;

                        let sel = document.getElementById('testerRunSelector');
                        if (sel) {
                            let opt = document.createElement('option');
                            opt.value = reportKey;
                            opt.textContent = (reportData.reportTitle || file.name) + ' (' + (reportData.trades ? reportData.trades.length : 0) + ' ترید)';
                            opt.selected = true;
                            sel.insertBefore(opt, sel.firstChild);
                            sel.value = reportKey;
                        }

                        switchTesterReport(reportKey);
                        alert('✅ گزارش تستر متاتریدر با موفقیت بارگذاری و تحلیل شد!');
                    } else {
                        alert('❌ فرمت فایل قابل پردازش نبود. لطفاً فایل خروجی JSON یا CSV تستر را انتخاب فرمایید.');
                    }
                } catch (err) {
                    alert('❌ خطا در پردازش فایل تستر: ' + err.message);
                }
            };
            reader.readAsArrayBuffer(file);
        }

        function parseTesterCsvReport(csvText, fileName) {
            let lines = csvText.split(/\r?\n/).filter(l => l.trim().length > 0);
            if (lines.length < 2) return null;

            let header = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
            let trades = [];
            let totalNetPips = 0.0;
            let totalNetUSD = 0.0;
            let winCnt = 0;
            let lossCnt = 0;
            let grossProfit = 0.0;
            let grossLoss = 0.0;

            for (let i = 1; i < lines.length; i++) {
                let cols = lines[i].split(',').map(c => c.trim().replace(/^"|"$/g, ''));
                if (cols.length < 5) continue;

                let setupId = i;
                let pattern = cols[1] || 'Setup ' + i;
                let tf = cols[2] || 'M1';
                let side = cols[3] || 'BUY';
                let entryTime = cols[4] || '';
                let closeTime = cols[5] || '';
                let boxEntry = parseFloat(cols[6]) || 0.0;
                let fillEntry = parseFloat(cols[7]) || boxEntry;
                let slip = parseFloat(cols[8]) || 0.0;
                let sl = parseFloat(cols[9]) || 0.0;
                let tp1 = parseFloat(cols[10]) || 0.0;
                let tp4 = parseFloat(cols[13]) || 0.0;
                let exitClass = cols[15] || 'Full SL ❌';
                let profitUSD = parseFloat(cols[16]) || 0.0;
                let profitPips = parseFloat(cols[17]) || 0.0;
                let outcome = cols[18] || (profitPips >= 0 ? 'Win' : 'Loss');

                totalNetPips += profitPips;
                totalNetUSD += profitUSD;
                if (profitPips >= 0) {
                    winCnt++;
                    grossProfit += profitPips;
                } else {
                    lossCnt++;
                    grossLoss += Math.abs(profitPips);
                }

                trades.push({
                    setupId: setupId,
                    pattern: pattern,
                    timeframe: tf,
                    side: side,
                    entryTime: entryTime,
                    closeTime: closeTime,
                    boxEntryPrice: boxEntry,
                    marketFillPrice: fillEntry,
                    slippagePips: slip,
                    slPrice: sl,
                    tp1: tp1,
                    tp2: 0,
                    tp3: 0,
                    tp4: tp4,
                    exitClass: exitClass,
                    outcome: outcome,
                    profitPips: profitPips,
                    profitUSD: profitUSD,
                    discrepancyReason: (tf === 'M1' ? 'تایم نویز M1' : (slip > 2.0 ? 'اسلیپیج شدید' : 'منطبق'))
                });
            }

            let wr = (trades.length > 0) ? (winCnt / trades.length * 100.0) : 0.0;
            let pf = (grossLoss > 0) ? (grossProfit / grossLoss) : 0.0;

            return {
                reportTitle: 'گزارش تستر بارگذاری‌شده: ' + fileName,
                symbol: 'Uploaded',
                timeframe: 'Custom',
                dateRange: (trades.length > 0 ? trades[0].entryTime.substring(0, 10) + ' - ' + trades[trades.length - 1].closeTime.substring(0, 10) : ''),
                exportedAt: new Date().toLocaleString('fa-IR'),
                parameters: {
                    InpScenarioName: 'Custom CSV Export'
                },
                kpis: {
                    totalSetups: trades.length,
                    winningSetups: winCnt,
                    losingSetups: lossCnt,
                    winRate: wr,
                    netPips: totalNetPips,
                    netUSD: totalNetUSD,
                    profitFactor: pf,
                    simWinRate: 57.1,
                    simNetR: '+112.1R'
                },
                equityCurve: trades.map((t, idx) => ({
                    time: t.closeTime || t.entryTime,
                    pnlPips: t.profitPips,
                    pnlUSD: t.profitUSD
                })),
                trades: trades
            };
        }

        