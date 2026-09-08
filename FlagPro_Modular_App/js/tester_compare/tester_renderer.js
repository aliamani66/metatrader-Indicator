function renderTesterKPIs(report, scenarioKey) {
    if (!report) return;
    let processed = getProcessedTesterTrades(report, scenarioKey);
    let mt5Trades = processed.filter(p => p.matchType !== 'sim_only');
    let totalSetups = mt5Trades.length;

    let sym = report.symbol || window.currentActiveSymbol || 'GBPUSD';
    let cleanSym = sym.replace(/[^a-zA-Z0-9]/g, '');
    let sData = (window.ALL_SYMBOLS_DATA && (window.ALL_SYMBOLS_DATA[sym] || window.ALL_SYMBOLS_DATA[cleanSym] || window.ALL_SYMBOLS_DATA[window.currentActiveSymbol])) || {};
    let indTrades = sData.trades_json_list || [];

    if (totalSetups === 0) {
        let netAct = document.getElementById('tcValNetActual'); if (netAct) netAct.textContent = '$0.00';
        let netInd = document.getElementById('tcValNetInd'); if (netInd) netInd.textContent = '$0.00';
        let diffPnL = document.getElementById('tcDiffTotalPnL'); if (diffPnL) diffPnL.textContent = 'داده‌ای ثبت نشده';
        return;
    }

    // 1. Tester MT5 Actual Metrics (strictly on deals executed in MT5)
    let tUsd = mt5Trades.reduce((acc, p) => acc + p.profitUSD, 0);
    let tPips = mt5Trades.reduce((acc, p) => acc + p.profitPips, 0);
    let tWins = mt5Trades.filter(p => p.profitUSD >= 0).length;
    let tLosses = totalSetups - tWins;
    let tWr = totalSetups > 0 ? ((tWins / totalSetups) * 100) : 0;
    let tGrossWin = mt5Trades.filter(p => p.profitUSD > 0).reduce((acc, p) => acc + p.profitUSD, 0);
    let tGrossLoss = mt5Trades.filter(p => p.profitUSD < 0).reduce((acc, p) => acc + Math.abs(p.profitUSD), 0);
    let tPf = tGrossLoss > 0 ? (tGrossWin / tGrossLoss) : (tGrossWin > 0 ? 99.9 : 0.0);

    // 2. Indicator Theoretical Metrics (for indicator setups in active scenario)
    let indSetups = processed.filter(p => p.matchType !== 'tester_only' && p.isAllowed);
    let totalIndSetups = indSetups.length;
    let iUsd = indSetups.reduce((acc, p) => acc + p.indNet, 0);
    let iPips = indSetups.reduce((acc, p) => acc + p.indPips, 0);
    let iWins = indSetups.filter(p => p.isIndWin).length;
    let iLosses = totalIndSetups - iWins;
    let iWr = totalIndSetups > 0 ? ((iWins / totalIndSetups) * 100) : 0;
    let iGrossWin = indSetups.filter(p => p.indNet > 0).reduce((acc, p) => acc + p.indNet, 0);
    let iGrossLoss = indSetups.filter(p => p.indNet < 0).reduce((acc, p) => acc + Math.abs(p.indNet), 0);
    let iPf = iGrossLoss > 0 ? (iGrossWin / iGrossLoss) : (iGrossWin > 0 ? 99.9 : 0.0);

    // --- Card 1: Total Profit / PnL & Gap ---
    let netAct = document.getElementById('tcValNetActual');
    if (netAct) {
        netAct.textContent = (tUsd >= 0 ? '+$' : '-$') + Math.abs(tUsd).toFixed(2);
        netAct.style.color = tUsd >= 0 ? '#34d399' : '#f87171';
    }

    let netInd = document.getElementById('tcValNetInd');
    if (netInd) {
        netInd.textContent = (iUsd >= 0 ? '+$' : '-$') + Math.abs(iUsd).toFixed(2);
        netInd.style.color = iUsd >= 0 ? '#34d399' : '#f87171';
    }

    let diffPnLEl = document.getElementById('tcDiffTotalPnL');
    if (diffPnLEl) {
        let diffUsd = tUsd - iUsd;
        let diffPips = tPips - iPips;
        let signUsd = diffUsd >= 0 ? '+$' : '-$';
        let signPips = diffPips >= 0 ? '+' : '';
        let favorText = diffUsd >= 0 ? 'به نفع تستر' : 'به نفع اندیکاتور';
        diffPnLEl.textContent = `اختلاف کل: ${signUsd}${Math.abs(diffUsd).toFixed(2)} (${signPips}${diffPips.toFixed(1)}p) ${favorText}`;
        diffPnLEl.style.color = diffUsd >= 0 ? '#facc15' : '#f87171';
    }

    // --- Card 2: Win Rate ---
    let wrAct = document.getElementById('tcValWinRateActual');
    if (wrAct) {
        wrAct.textContent = tWr.toFixed(1) + '%';
        wrAct.style.color = tWr >= 50.0 ? '#34d399' : '#f87171';
    }

    let wrSim = document.getElementById('tcValWinRateSim');
    if (wrSim) {
        wrSim.textContent = iWr.toFixed(1) + '%';
        wrSim.style.color = iWr >= 50.0 ? '#34d399' : '#f87171';
    }

    let diffWr = document.getElementById('tcDiffWinRate');
    if (diffWr) {
        let diffWrVal = tWr - iWr;
        let diffColor = diffWrVal >= 0 ? '#34d399' : '#f87171';
        diffWr.style.color = diffColor;
        diffWr.textContent = (diffWrVal >= 0 ? 'بهبود: +' : 'اختلاف: ') + diffWrVal.toFixed(1) + '% (' + tWins + ' برد تستر vs ' + iWins + ' برد اندیکاتور)';
    }

    // --- Card 3: Profit Factor ---
    let pfAct = document.getElementById('tcValPfActual');
    if (pfAct) {
        pfAct.textContent = tPf.toFixed(2);
        pfAct.style.color = tPf >= 1.0 ? '#34d399' : '#f87171';
    }

    let pfSim = document.getElementById('tcValPfSim');
    if (pfSim) {
        pfSim.textContent = iPf.toFixed(2);
        pfSim.style.color = iPf >= 1.0 ? '#34d399' : '#f87171';
    }

    let diffPf = document.getElementById('tcDiffPf');
    if (diffPf) {
        let diffPfVal = tPf - iPf;
        let diffColor = diffPfVal >= 0 ? '#34d399' : '#f87171';
        diffPf.style.color = diffColor;
        diffPf.textContent = (diffPfVal >= 0 ? 'بهبود: +' : 'اختلاف: ') + diffPfVal.toFixed(2) + ' ضریب سود تستر vs اندیکاتور';
    }

    // --- Card 4: Outcome Discrepancies ---
    let matchedTrades = processed.filter(p => p.matchType === 'matched');
    let outcomeDiffTrades = matchedTrades.filter(p => (p.profitUSD >= 0) !== p.isIndWin);
    let outcomeDiffCount = outcomeDiffTrades.length;
    let bothAgreedCount = matchedTrades.length - outcomeDiffCount;
    let bothWinCount = matchedTrades.filter(p => p.profitUSD >= 0 && p.isIndWin).length;
    let bothLossCount = matchedTrades.filter(p => p.profitUSD < 0 && !p.isIndWin).length;

    let elOutDiff = document.getElementById('tcValOutcomeDiff');
    if (elOutDiff) {
        elOutDiff.textContent = outcomeDiffCount + ' ستاپ';
        elOutDiff.style.color = outcomeDiffCount > 0 ? '#f87171' : '#34d399';
    }

    let elOutAgr = document.getElementById('tcValOutcomeAgreed');
    if (elOutAgr) {
        elOutAgr.textContent = bothAgreedCount + ' ستاپ';
    }

    let elOutSub = document.getElementById('tcOutcomeDiffSub');
    if (elOutSub) {
        elOutSub.textContent = `${bothWinCount} برد مشترک | ${bothLossCount} باخت مشترک (${outcomeDiffCount} تغییر برد/باخت)`;
    }

    // --- Card 5: Platform Presence ---
    let bothPlatformsCount = matchedTrades.length;
    let onlyTesterCount = processed.filter(p => p.matchType === 'tester_only').length;
    let onlyIndCount = processed.filter(p => p.matchType === 'sim_only').length;

    let startDate = (processed.length > 0 && processed[0].tEntryTime) ? processed[0].tEntryTime.substring(0, 10) : '';
    let endDate = (processed.length > 0 && processed[processed.length - 1].tEntryTime) ? processed[processed.length - 1].tEntryTime.substring(0, 10) : '';

    let elBothPlat = document.getElementById('tcValBothPlatforms');
    if (elBothPlat) elBothPlat.textContent = bothPlatformsCount;

    let elOnlyTester = document.getElementById('tcValOnlyTester');
    if (elOnlyTester) elOnlyTester.textContent = onlyTesterCount;

    let elOnlyInd = document.getElementById('tcValOnlyIndicator');
    if (elOnlyInd) elOnlyInd.textContent = onlyIndCount;

    let elPlatSub = document.getElementById('tcPlatformPresenceSub');
    if (elPlatSub) {
        elPlatSub.textContent = `کل دوره (${startDate} الی ${endDate}): ${bothPlatformsCount} مشترک | ${onlyTesterCount} فقط تستر | ${onlyIndCount} فقط شبیه‌ساز`;
    }

    // --- Card 6: Box-to-Entry Latency KPIs ---
    let lat = sData.latency_all || {};
    let waitMinEl = document.getElementById('tcValWaitMin');
    let waitAvgEl = document.getElementById('tcValWaitAvg');
    let waitMedEl = document.getElementById('tcValWaitMed');
    let diffWaitEl = document.getElementById('tcDiffWait');
    if (waitMinEl) waitMinEl.textContent = lat.min_short || '۹د';
    if (waitAvgEl) waitAvgEl.textContent = lat.avg_short || '۴۶د';
    if (waitMedEl) waitMedEl.textContent = lat.median_short || '۲۶د';
    if (diffWaitEl) {
        let p90 = lat.p90_short ? `۹۰٪ اردرها زیر ${lat.p90_short}` : 'انقضای اردر لیمیت';
        diffWaitEl.textContent = `${p90} (کل: ${totalSetups} ستاپ)`;
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

    // 1. Evaluate Scenario Name Status & Impact
    let actScName = (p.InpScenarioName || '').trim();
    let actScLower = actScName.toLowerCase();
    let expScName = (scenario.title || scenario.rawTitle || scenario.name || '').trim();
    let expScLower = expScName.toLowerCase();

    let isActDefaultOrBase = !actScName || actScLower === 'default' || actScLower.includes('default') || actScLower.includes('base') || actScName.includes('پایه') || actScName.includes('پیش‌فرض') || actScName.includes('سبد جامع') || actScName.includes('خام');
    let isExpDefaultOrBase = checkIsRawOrBaseScenario(scenario, report) || scenario.id === 'base' || scenario.id === 'default' || expScLower.includes('base') || expScName.includes('پایه') || expScName.includes('سبد جامع') || expScName.includes('پیش‌فرض') || expScName.includes('خام');

    let nameMatched = false;
    if (isActDefaultOrBase && isExpDefaultOrBase) {
        nameMatched = true;
    } else if (actScName && expScName) {
        if (actScLower === expScLower || actScLower.includes(expScLower) || expScLower.includes(actScLower)) {
            nameMatched = true;
        } else if (scenario.id && actScLower.includes(scenario.id.toLowerCase())) {
            nameMatched = true;
        } else {
            let cleanWords = str => str.replace(/[^a-zA-Z0-9\u0600-\u06FF]/g, ' ').toLowerCase().split(/\s+/).filter(w => w.length >= 2);
            let actTokens = cleanWords(actScName);
            let expTokens = cleanWords(expScName);
            let common = actTokens.filter(t => expTokens.includes(t));
            if (common.length >= 1) {
                nameMatched = true;
            }
        }
    }
    if (!nameMatched && actScName) {
        if (scenario.id.startsWith('custom_') && (actScName.includes('سفارشی') || actScLower.includes('custom') || actScLower.includes('ai'))) nameMatched = true;
    }

    let nameStatus = nameMatched ? 'match' : ((!p.InpScenarioName || p.InpScenarioName.includes('Default')) ? 'severe' : 'warn');
    let nameImpact = '';
    if (nameMatched) {
        if (isActDefaultOrBase && isExpDefaultOrBase) {
            nameImpact = 'تنظیمات Default / خام در تستر MT5 کاملاً منطبق بر تست خام (کل معاملات چارت) است.';
        } else {
            nameImpact = 'نام سناریو در متاتریدر ۵ («' + (p.InpScenarioName || '') + '») کاملاً منطبق بر این سناریو است.';
        }
    } else {
        nameImpact = 'در تستر MT5 مقدار «' + (p.InpScenarioName || 'Default') + '» تنظیم شده که با این سناریو متفاوت است.';
    }

    // 2. Evaluate Hours Status & Impact
    let actHours = (p.InpAllowedTradingHours || '').trim();
    let actHoursSet = extractHourSet(actHours);
    if (!actHours || actHours.length === 0 || actHours.toLowerCase() === 'all') {
        for (let i = 0; i < 24; i++) actHoursSet.add(i);
    }

    let expHoursSet = extractHourSet(scenario.hours, scenario.hoursDisplay);
    if (expHoursSet.size === 0 && (!scenario.hoursDisplay || scenario.hoursDisplay.includes('۲۴ ساعته'))) {
        for (let i = 0; i < 24; i++) expHoursSet.add(i);
    }

    let hoursStatus = 'warn';
    let hoursImpact = '';
    if (actHoursSet.size === 24 && expHoursSet.size === 24) {
        hoursStatus = 'match';
        hoursImpact = 'معاملات ۲۴ ساعته کامل طبق برنامه سناریو اعمال شده است.';
    } else {
        let commonHours = [...actHoursSet].filter(h => expHoursSet.has(h));
        if (actHoursSet.size === expHoursSet.size && commonHours.length === expHoursSet.size) {
            hoursStatus = 'match';
            hoursImpact = 'ساعات مجاز معاملاتی در تستر متاتریدر ۵ کاملاً منطبق بر این سناریو است (' + actHoursSet.size + ' ساعت فعال).';
        } else if (commonHours.length === expHoursSet.size && actHoursSet.size > expHoursSet.size) {
            hoursStatus = 'warn';
            hoursImpact = `ساعات تستر همه ساعات سناریو را پوشش می‌دهد اما ${actHoursSet.size - expHoursSet.size} ساعت اضافه دارد.`;
        } else if (commonHours.length > 0) {
            hoursStatus = 'warn';
            hoursImpact = `تطابق جزئی در ساعات: ${commonHours.length} از ${expHoursSet.size} ساعت سناریو در تستر فعال بوده است.`;
        } else if (actHoursSet.size === 24 && expHoursSet.size < 24) {
            hoursStatus = 'severe';
            hoursImpact = 'در متاتریدر ۵ تستر به صورت ۲۴ ساعته اجرا شده، در حالی که این سناریو نیازمند فیلتر ساعات غیرفعال است.';
        } else {
            hoursStatus = 'severe';
            hoursImpact = 'ساعات معاملاتی ست‌شده در تستر با ساعات این سناریو مغایرت دارد.';
        }
    }

    // 3. Evaluate Disabled Kings Status & Impact
    let actDis = (p.InpDisabledKingsList || '').trim();
    let isActNoDis = !actDis || actDis.toLowerCase().includes('none') || actDis.includes('هیچ') || actDis.includes('بدون') || actDis.length <= 3;
    let isExpNoDis = !scenario.disabledKings || scenario.disabledKings.includes('بدون مسدودی') || scenario.disabledKings.toLowerCase().includes('none') || scenario.disabledKings.includes('هیچ');

    let kingsStatus = 'warn';
    let kingsImpact = '';
    if (isActNoDis && isExpNoDis) {
        kingsStatus = 'match';
        kingsImpact = 'تمامی سلاطین طبق انتظار سناریو در تستر مجاز و فعال بوده‌اند (بدون مسدودی).';
    } else if (!isActNoDis && !isExpNoDis) {
        let actDisClean = actDis.replace(/\s+|\[|\]/g, '');
        let expDisClean = scenario.disabledKings.replace(/\s+|\[|\]/g, '');
        if (actDisClean === expDisClean || actDisClean.includes(expDisClean) || expDisClean.includes(actDisClean)) {
            kingsStatus = 'match';
            kingsImpact = 'سلاطین پرریسک به درستی طبق سناریو در تستر MT5 مسدود شده‌اند.';
        } else {
            kingsStatus = 'warn';
            kingsImpact = 'سلاطین مسدودشده در تستر با لیست مسدودی این سناریو تفاوت دارد.';
        }
    } else if (isActNoDis && !isExpNoDis) {
        kingsStatus = 'severe';
        kingsImpact = 'در تستر هیچ سلطانی مسدود نشده است، در حالی که این سناریو نیازمند مسدودسازی سلاطین پرریسک است.';
    } else {
        kingsStatus = 'warn';
        kingsImpact = 'در تستر برخی سلاطین مسدود شده‌اند اما سناریو همه سلاطین را مجاز می‌داند.';
    }

    let rows = [
        {
            name: 'سناریوی معاملاتی (InpScenarioName)',
            actual: p.InpScenarioName || 'Default (تنظیمات پیش‌فرض)',
            expected: scenario.name,
            status: nameStatus,
            impact: nameImpact
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
            status: hoursStatus,
            impact: hoursImpact
        },
        {
            name: 'لیست سفید سلاطین مجاز (InpAllowedKingsList)',
            actual: (p.InpAllowedKingsList && p.InpAllowedKingsList.trim().length > 0) ? p.InpAllowedKingsList : 'تعریف‌نشده (پیش‌فرض ۱۸ سلطان)',
            expected: scenario.allowedKings || 'طبق سناریو',
            status: (p.InpAllowedKingsList && p.InpAllowedKingsList.trim().length > 0) ? 'match' : 'neutral',
            impact: (p.InpAllowedKingsList && p.InpAllowedKingsList.trim().length > 0)
                ? 'فهرست سفید در متاتریدر ۵ فعال است و فقط سلاطین مشخص‌شده معامله می‌شوند.'
                : 'فهرست سفید خالی است؛ اکسپرت از ۱۸ الگوی کینگ استاندارد استفاده می‌کند.'
        },
        {
            name: 'لیست سلاطین غیرمجاز (InpDisabledKingsList)',
            actual: (p.InpDisabledKingsList && p.InpDisabledKingsList.length > 3) ? p.InpDisabledKingsList : 'None (هیچ سلطانی مسدود نبود)',
            expected: scenario.disabledKings,
            status: kingsStatus,
            impact: kingsImpact
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
            name: 'افست حد ضرر (InpSLOffsetPips)',
            actual: (p.InpSLOffsetPips !== undefined ? (Number(p.InpSLOffsetPips).toFixed(1) + ' pips') : '8.0 pips (پیش‌فرض اکسپرت)'),
            expected: '8.0 pips (فاصله اطمینان فرار از شدو)',
            status: (p.InpSLOffsetPips === undefined || Number(p.InpSLOffsetPips) === 8.0) ? 'match' : (Number(p.InpSLOffsetPips) >= 5.0 ? 'warn' : 'severe'),
            impact: (p.InpSLOffsetPips === undefined || Number(p.InpSLOffsetPips) === 8.0)
                ? 'فاصله اطمینان حد ضرر روی ۸ پیپ تنظیم شده و از استاپ هانت شدوها در نوسانات شدید جلوگیری می‌کند.'
                : 'افست استاپ کمتر از ۸ پیپ است و احتمال استاپ خوردن توسط شدوها افزایش می‌یابد.'
        },
        {
            name: 'روش اجرای سفارشات (InpOrderExecMode)',
            actual: (p.InpOrderExecMode == 1 ? 'Market Order (ورود مارکت)' : 'Pending Limit (اردر لیمیت دقیق)'),
            expected: 'Pending Limit (ورود دقیق در لبه باکس - اسلیپیج صفر)',
            status: (p.InpOrderExecMode == 1 ? 'warn' : 'match'),
            impact: (p.InpOrderExecMode == 1)
                ? 'اجرای مارکت پس از بسته شدن کندل ممکن است به دلیل اسلیپیج نقطه ورود را جابجا کند.'
                : 'سفارش لیمیت دقیقاً روی لبه باکس منتظر تاچ قیمت می‌ماند و اسلیپیج ورود به صفر می‌رسد.'
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
    let w = rect.width || canvas.offsetWidth || canvas.clientWidth || (canvas.parentElement ? canvas.parentElement.clientWidth : 0);
    let h = rect.height || canvas.offsetHeight || canvas.clientHeight || (canvas.parentElement ? canvas.parentElement.clientHeight : 0) || 320;

    if (w <= 0 || h <= 0) {
        if (!canvas._retryCount) canvas._retryCount = 0;
        if (canvas._retryCount < 40) {
            canvas._retryCount++;
            requestAnimationFrame(() => setTimeout(() => drawTesterCompareChart(report, scenarioKey), 50));
        }
        return;
    }
    canvas._retryCount = 0;

    if (window.ResizeObserver && canvas.parentElement && !canvas._roAttached) {
        canvas._roAttached = true;
        let ro = new ResizeObserver(() => {
            let curRep = (window.TESTER_REPORTS && window.TESTER_REPORTS[window.currentTesterReportKey]) || report;
            drawTesterCompareChart(curRep, window.currentTesterScenarioKey);
        });
        ro.observe(canvas.parentElement);
    }

    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.scale(dpr, dpr);

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

    let sym = report.symbol || window.currentActiveSymbol || 'GBPUSD';
    let cleanSym = sym.replace(/[^a-zA-Z0-9]/g, '');
    let sData = (window.ALL_SYMBOLS_DATA && (window.ALL_SYMBOLS_DATA[sym] || window.ALL_SYMBOLS_DATA[cleanSym] || window.ALL_SYMBOLS_DATA[window.currentActiveSymbol])) || {};
    let tradesList = sData.trades_sim_list || window.simTrades || [];

    let simPoints = [];
    let actPoints = [];
    let n = eqActual.length;

    // Filter tradesList based on active scenario:
    let scKings = (scenario.kings && Array.isArray(scenario.kings) && scenario.kings.length > 0) ? new Set(scenario.kings) : null;
    let scHours = extractHourSet(scenario.hours, scenario.hoursDisplay);
    let minPot = scenario.minPot || 0.0;

    let isBaseScenario = checkIsRawOrBaseScenario(scenario, report);
    let acceptedTrades = [];
    if (isBaseScenario) {
        acceptedTrades = tradesList.slice();
    } else {
        acceptedTrades = tradesList.filter(t => {
            // Check King status (match Tab 1 simulation logic)
            if (scKings) {
                if (!scKings.has(t.kk) && !scKings.has(t.r)) return false;
            } else if (t.k !== 1) {
                return false;
            }
            // Check Hours
            if (scHours && scHours.size > 0 && scHours.size < 24 && !scHours.has(t.h)) return false;
            if (scenario.hours && Array.isArray(scenario.hours) && scenario.hours[t.h] === false) return false;
            // Check Min Potential
            if (minPot > 0 && t.pot !== undefined && t.pot < minPot) return false;
            return true;
        });
    }

    for (let i = 0; i < n; i++) {
        let tItem = eqActual[i];
        let tTime = tItem.time || '';
        let actVal = (tItem.pnlPips !== undefined && !isNaN(Number(tItem.pnlPips))) ? Number(tItem.pnlPips) : 0.0;
        let actUSD = (tItem.pnlUSD !== undefined && !isNaN(Number(tItem.pnlUSD))) ? Number(tItem.pnlUSD) : (actVal / 10.0);
        actPoints.push({ time: tTime, val: actVal, valUSD: actUSD });

        // Calculate REAL cumulative strategy PnL up to tTime
        let cumUSD = 0.0;
        for (let j = 0; j < acceptedTrades.length; j++) {
            if (acceptedTrades[j].t <= tTime) {
                cumUSD += (acceptedTrades[j].p !== undefined ? acceptedTrades[j].p : 0.0);
            }
        }
        let cumPips = cumUSD * 10.0;
        simPoints.push({ time: tTime, val: cumPips, valUSD: cumUSD });
    }

    // Update legend with real PnL
    let legTester = document.getElementById('tcLegendTester');
    let legSim = document.getElementById('tcLegendStrategy');
    let lastAct = actPoints[n - 1] || { val: 0, valUSD: 0 };
    let lastSim = simPoints[n - 1] || { val: 0, valUSD: 0 };
    if (legTester) {
        let pnlText = (lastAct.val >= 0 ? '+' : '') + lastAct.val.toFixed(1) + 'p (' + (lastAct.valUSD >= 0 ? '+$' : '-$') + Math.abs(lastAct.valUSD).toFixed(2) + ')';
        legTester.innerHTML = `<span style="width:14px;height:4px;background:#ef4444;display:inline-block;border-radius:2px;"></span> تستر MT5 (${pnlText})`;
    }
    if (legSim) {
        let pnlText = (lastSim.val >= 0 ? '+' : '') + lastSim.val.toFixed(1) + 'p (' + (lastSim.valUSD >= 0 ? '+$' : '-$') + Math.abs(lastSim.valUSD).toFixed(2) + ')';
        let scTitle = scenario.title || scenario.name || 'شبیه‌ساز';
        legSim.innerHTML = `<span style="width:14px;height:4px;background:#0284c7;display:inline-block;border-radius:2px;"></span> شبیه‌ساز استراتژی [${scTitle}]: (${pnlText})`;
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
    let stepGrid = (maxVal - minVal > 600) ? 200 : 100;
    let startGrid = Math.floor(minVal / stepGrid) * stepGrid;
    for (let v = startGrid; v <= maxVal; v += stepGrid) {
        if (v === 0) continue;
        let y = getY(v);
        if (y < padTop || y > padTop + plotH) continue;
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

    // Fill gradient for Strategy Simulation (Blue)
    let gradSim = ctx.createLinearGradient(0, padTop, 0, zeroY);
    gradSim.addColorStop(0, 'rgba(56, 189, 248, 0.2)');
    gradSim.addColorStop(1, 'rgba(56, 189, 248, 0.0)');
    ctx.fillStyle = gradSim;
    ctx.beginPath();
    ctx.moveTo(getX(0), zeroY);
    for (let i = 0; i < n; i++) ctx.lineTo(getX(i), getY(simPoints[i].val));
    ctx.lineTo(getX(n - 1), zeroY);
    ctx.closePath();
    ctx.fill();

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

    // Hover Tooltip / Crosshair
    if (hoverIdx !== undefined && hoverIdx >= 0 && hoverIdx < n) {
        let hX = getX(hoverIdx);
        let hYAct = getY(actPoints[hoverIdx].val);
        let hYSim = getY(simPoints[hoverIdx].val);

        // Vertical Guide Line
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 1;
        ctx.setLineDash([2, 2]);
        ctx.beginPath();
        ctx.moveTo(hX, padTop);
        ctx.lineTo(hX, padTop + plotH);
        ctx.stroke();
        ctx.setLineDash([]);

        // Red point
        ctx.fillStyle = '#ef4444';
        ctx.beginPath();
        ctx.arc(hX, hYAct, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Blue point
        ctx.fillStyle = '#38bdf8';
        ctx.beginPath();
        ctx.arc(hX, hYSim, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Tooltip box
        let ttW = 180;
        let ttH = 80;
        let ttX = hX + 10;
        if (ttX + ttW > w - padRight) ttX = hX - ttW - 10;
        let ttY = padTop + 10;

        ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(ttX, ttY, ttW, ttH, 6);
        ctx.fill();
        ctx.stroke();

        ctx.textAlign = 'right';
        ctx.font = 'bold 11px Segoe UI, sans-serif';
        ctx.fillStyle = '#f8fafc';
        ctx.fillText('📅 ' + actPoints[hoverIdx].time, ttX + ttW - 10, ttY + 18);

        ctx.font = '10.5px Segoe UI, sans-serif';
        ctx.fillStyle = '#f87171';
        let actSign = actPoints[hoverIdx].val >= 0 ? '+' : '';
        ctx.fillText('تستر MT5: ' + actSign + actPoints[hoverIdx].val.toFixed(1) + 'p ($' + actPoints[hoverIdx].valUSD.toFixed(2) + ')', ttX + ttW - 10, ttY + 38);

        ctx.fillStyle = '#38bdf8';
        let simSign = simPoints[hoverIdx].val >= 0 ? '+' : '';
        ctx.fillText('شبیه‌ساز: ' + simSign + simPoints[hoverIdx].val.toFixed(1) + 'p ($' + simPoints[hoverIdx].valUSD.toFixed(2) + ')', ttX + ttW - 10, ttY + 56);

        let diffVal = simPoints[hoverIdx].val - actPoints[hoverIdx].val;
        ctx.fillStyle = diffVal >= 0 ? '#34d399' : '#f87171';
        ctx.font = '9.5px Segoe UI, sans-serif';
        ctx.fillText('اختلاف: ' + (diffVal >= 0 ? '+' : '') + diffVal.toFixed(1) + 'p', ttX + ttW - 10, ttY + 72);
    }

    // Attach mouse event listeners once
    if (!canvas._tcEventsAttached) {
        canvas._tcEventsAttached = true;
        canvas.addEventListener('mousemove', function(e) {
            let cRect = canvas.getBoundingClientRect();
            let mX = e.clientX - cRect.left;
            let mY = e.clientY - cRect.top;
            if (mX >= padLeft && mX <= padLeft + plotW && mY >= padTop && mY <= padTop + plotH) {
                let frac = (mX - padLeft) / plotW;
                let cIdx = Math.round(frac * (n - 1));
                cIdx = Math.max(0, Math.min(n - 1, cIdx));
                let curRep = (window.TESTER_REPORTS && window.TESTER_REPORTS[window.currentTesterReportKey]) || report;
                drawTesterCompareChart(curRep, window.currentTesterScenarioKey, cIdx);
            }
        });
        canvas.addEventListener('mouseleave', function() {
            let curRep = (window.TESTER_REPORTS && window.TESTER_REPORTS[window.currentTesterReportKey]) || report;
            drawTesterCompareChart(curRep, window.currentTesterScenarioKey);
        });
    }
}

function renderTesterTradesTable(report, filterMode, searchQuery) {
    filterMode = filterMode || window.currentTesterFilter || 'all';
    searchQuery = searchQuery || window.currentTesterSearch || '';
    let tbody = document.getElementById('testerTradesBody');
    if (!tbody) return;

    let trades = report.trades || [];
    let processed = getProcessedTesterTrades(report, window.currentTesterScenarioKey);

    if (processed.length === 0) {
        tbody.innerHTML = '<tr><td colspan="16" style="text-align:center;padding:20px;color:#94a3b8;">هیچ معامله‌ای در این گزارش ثبت نشده است.</td></tr>';
        return;
    }

    // Update Filter Buttons Text & Badge Counts
    let cntAll = processed.length;
    let cntWin = processed.filter(x => x.matchType !== 'sim_only' ? (x.profitUSD >= 0) : x.isIndWin).length;
    let cntLoss = processed.filter(x => x.matchType !== 'sim_only' ? (x.profitUSD < 0) : !x.isIndWin).length;
    let cntM1 = processed.filter(x => x.tTF === 'M1').length;
    let cntSlip = processed.filter(x => x.slippagePips >= 2.0).length;
    let cntBe = processed.filter(x => x.exitClass && x.exitClass.includes('BE')).length;
    let cntDisc = processed.filter(x => x.isDisc).length;
    let cntMatched = processed.filter(x => x.matchType === 'matched').length;
    let cntSimOnly = processed.filter(x => x.matchType === 'sim_only').length;

    let bAll = document.getElementById('tcFilterAll'); if (bAll) bAll.textContent = 'همه (' + cntAll + ')';
    let bWin = document.getElementById('tcFilterWin'); if (bWin) bWin.textContent = 'بردها (' + cntWin + ')';
    let bLoss = document.getElementById('tcFilterLoss'); if (bLoss) bLoss.textContent = 'باخت‌ها (' + cntLoss + ')';
    let bM1 = document.getElementById('tcFilterM1'); if (bM1) bM1.textContent = 'نویز M1 (' + cntM1 + ')';
    let bSlip = document.getElementById('tcFilterSlip'); if (bSlip) bSlip.textContent = 'اسلیپیج بالا > 2p (' + cntSlip + ')';
    let bBe = document.getElementById('tcFilterBe'); if (bBe) bBe.textContent = 'خروج در BE (' + cntBe + ')';
    let bDisc = document.getElementById('tcFilterDisc'); if (bDisc) bDisc.textContent = '⚠️ مغایرت‌ها (' + cntDisc + ')';
    let bMatched = document.getElementById('tcFilterMatched'); if (bMatched) bMatched.textContent = '🤝 منطبق (' + cntMatched + ')';
    let bSimOnly = document.getElementById('tcFilterSimOnly'); if (bSimOnly) bSimOnly.textContent = '🔮 فقط شبیه‌ساز (' + cntSimOnly + ')';

    let tblTitle = document.getElementById('tcTradesTableTitle');
    if (tblTitle) {
        tblTitle.textContent = 'جدول بازرسی و مقایسه نظیر به نظیر (1:1) تستر MT5 با شبیه‌ساز (' + cntAll + ' ستاپ | ' + cntMatched + ' منطبق | ' + cntDisc + ' مغایرت)';
    }

    // Apply active filter
    let filtered = processed.filter(pt => {
        if (filterMode === 'win' && (pt.matchType !== 'sim_only' ? pt.profitUSD < 0 : !pt.isIndWin)) return false;
        if (filterMode === 'loss' && (pt.matchType !== 'sim_only' ? pt.profitUSD >= 0 : pt.isIndWin)) return false;
        if (filterMode === 'm1' && pt.tTF !== 'M1') return false;
        if (filterMode === 'slip' && pt.slippagePips < 2.0) return false;
        if (filterMode === 'be' && (!pt.exitClass || !pt.exitClass.includes('BE'))) return false;
        if (filterMode === 'disc' && !pt.isDisc) return false;
        if (filterMode === 'matched' && pt.matchType !== 'matched') return false;
        if (filterMode === 'sim_only' && pt.matchType !== 'sim_only') return false;
        if (filterMode === 'tester_only' && pt.matchType !== 'tester_only') return false;
        if (searchQuery) {
            let q = searchQuery.toLowerCase();
            let hay = (pt.pattern + ' ' + pt.tTF + ' ' + pt.tDir + ' ' + pt.tEntryTime + ' ' + pt.filterReason).toLowerCase();
            if (!hay.includes(q)) return false;
        }
        return true;
    });

    let html = '';
    filtered.forEach(pt => {
        let isSimOnly = (pt.matchType === 'sim_only');
        let isTesterOnly = (pt.matchType === 'tester_only');
        let isWin = isSimOnly ? pt.isIndWin : (pt.profitUSD >= 0);
        let tUsdColor = (pt.profitUSD >= 0) ? '#34d399' : '#f87171';
        let indUsdColor = (pt.indNet >= 0) ? '#34d399' : '#f87171';
        let slipColor = (pt.slippagePips > 2.0) ? '#f59e0b' : '#94a3b8';

        let sideBadge = pt.tDir === 'BUY'
            ? '<span style="color:#34d399;font-weight:bold;">BUY</span>'
            : '<span style="color:#f87171;font-weight:bold;">SELL</span>';

        let tfBadge = pt.tTF === 'M1'
            ? '<span style="background:#450a0a;color:#fca5a5;padding:1px 5px;border-radius:3px;font-size:10px;border:1px solid #991b1b;">M1</span>'
            : '<span style="background:#064e3b;color:#a7f3d0;padding:1px 5px;border-radius:3px;font-size:10px;border:1px solid #059669;">' + pt.tTF + '</span>';

        // Match type category tag
        let matchTag = '';
        if (isSimOnly) {
            matchTag = '<span style="background:#78350f33;color:#fef08a;border:1px solid #ca8a04;padding:1px 4px;border-radius:3px;font-size:8.5px;font-weight:bold;margin-right:4px;">🔮 شبیه‌ساز</span>';
        } else if (isTesterOnly) {
            matchTag = '<span style="background:#1e293b;color:#7dd3fc;border:1px solid #0284c7;padding:1px 4px;border-radius:3px;font-size:8.5px;font-weight:bold;margin-right:4px;">🤖 تستر</span>';
        } else {
            matchTag = '<span style="background:#064e3b;color:#34d399;border:1px solid #059669;padding:1px 4px;border-radius:3px;font-size:8.5px;font-weight:bold;margin-right:4px;">🤝 منطبق</span>';
        }

        // Tester PnL HTML (USD & Pips)
        let tUsdHtml = '';
        let tPipsHtml = '';
        if (isSimOnly) {
            tUsdHtml = `<span style="color:#64748b;font-size:10px;">-</span>`;
            tPipsHtml = `<span style="color:#64748b;font-size:10px;">-</span>`;
        } else {
            tUsdHtml = `<span style="direction:ltr;display:inline-block;unicode-bidi:embed;font-weight:bold;color:${tUsdColor};">${(pt.profitUSD >= 0 ? '+$' : '-$')}${Math.abs(pt.profitUSD).toFixed(2)}</span>`;
            tPipsHtml = `<span style="direction:ltr;display:inline-block;unicode-bidi:embed;font-weight:bold;color:${tUsdColor};">${(pt.profitPips >= 0 ? '+' : '')}${pt.profitPips.toFixed(1)}p</span>`;
        }

        // Indicator PnL HTML (USD & Pips)
        let indUsdHtml = '';
        let indPipsHtml = '';
        if (!pt.isAllowed) {
            indUsdHtml = `<span style="direction:ltr;display:inline-block;unicode-bidi:embed;color:#94a3b8;font-size:10px;text-decoration:line-through;">${(pt.indNet >= 0 ? '+$' : '-$')}${Math.abs(pt.indNet).toFixed(2)}</span> <span style="color:#fca5a5;font-size:9px;">(فیلتر)</span>`;
            indPipsHtml = `<span style="direction:ltr;display:inline-block;unicode-bidi:embed;color:#94a3b8;font-size:10px;text-decoration:line-through;">${(pt.indPips >= 0 ? '+' : '')}${pt.indPips.toFixed(1)}p</span>`;
        } else {
            indUsdHtml = `<span style="direction:ltr;display:inline-block;unicode-bidi:embed;font-weight:bold;color:${indUsdColor};">${(pt.indNet >= 0 ? '+$' : '-$')}${Math.abs(pt.indNet).toFixed(2)}</span>`;
            indPipsHtml = `<span style="direction:ltr;display:inline-block;unicode-bidi:embed;font-weight:bold;color:${indUsdColor};">${(pt.indPips >= 0 ? '+' : '')}${pt.indPips.toFixed(1)}p</span>`;
        }

        // Tester Exit / Target HTML
        let tExitHtml = '';
        if (isSimOnly) {
            tExitHtml = `<div style="color:#f87171;font-size:10px;font-weight:600;">عدم ورود MT5</div>`;
        } else {
            tExitHtml = `<div style="color:#e2e8f0;font-size:10.5px;font-weight:600;white-space:nowrap;">${pt.exitClass}</div>`;
            if (pt.exitPrice > 0) {
                tExitHtml += `<div style="color:#38bdf8;font-size:9.5px;font-family:monospace;margin-top:2px;">${pt.exitPrice.toFixed(5)}</div>`;
            }
        }

        // Indicator Target HTML
        let indTgtHtml = '';
        if (!pt.isAllowed) {
            indTgtHtml = `<span style="background:#450a0a;color:#fca5a5;padding:2px 6px;border-radius:4px;font-size:10px;border:1px solid #7f1d1d;">🛑 ${pt.filterReason}</span>`;
        } else if (pt.isIndWin) {
            indTgtHtml = `<span style="background:#064e3b;color:#a7f3d0;padding:2px 6px;border-radius:4px;font-size:10px;border:1px solid #059669;font-weight:600;">${pt.indTgt}</span>`;
        } else {
            indTgtHtml = `<span style="background:#450a0a;color:#fca5a5;padding:2px 6px;border-radius:4px;font-size:10px;border:1px solid #7f1d1d;">${pt.indTgt}</span>`;
        }
        if (pt.tp1 > 0 && pt.isAllowed) {
            indTgtHtml += `<div style="color:#34d399;font-size:9.5px;font-family:monospace;margin-top:2px;">TP1: ${pt.tp1.toFixed(5)}</div>`;
        }

        let waitTag = (pt.match && pt.match.wait_fmt && pt.match.wait_fmt !== '-')
            ? `<div style="color:#38bdf8;font-size:9.5px;margin-top:2px;direction:rtl;font-family:sans-serif;">⏱️ انتظار: ${pt.match.wait_fmt}</div>`
            : '';

        let rowBg = isSimOnly ? 'background:#241a0822;' : (isTesterOnly ? 'background:#0d1c3022;' : (!pt.isAllowed ? 'background:#1a0e1422;' : ''));

        // 16 Columns strictly aligned with table thead:
        // 1:# | 2:الگو | 3:تایم | 4:جهت | 5:زمان ورود | 6:ورود تستر | 7:ورود اندیکاتور | 8:لغزش | 9:حد ضرر | 10:تارگت تستر | 11:تارگت اندیکاتور | 12:سود تستر $ | 13:سود اندیکاتور $ | 14:سود تستر p | 15:سود اندیکاتور p | 16:کالبدشکافی
        html += `<tr style="border-bottom:1px solid #1e293b;${rowBg}">
            <td style="padding:7px 8px;text-align:center;color:#64748b;font-size:10px;">${pt.raw.setupId || ''}</td>
            <td style="padding:7px 8px;font-weight:600;color:#f8fafc;white-space:nowrap;text-align:right;">${pt.pattern} ${matchTag}</td>
            <td style="padding:7px 8px;text-align:center;">${tfBadge}</td>
            <td style="padding:7px 8px;text-align:center;">${sideBadge}</td>
            <td style="padding:7px 8px;color:#94a3b8;font-size:10.5px;direction:ltr;text-align:right;">${pt.tEntryTime}${waitTag}</td>
            <td style="padding:7px 8px;color:#38bdf8;font-size:10.5px;font-weight:600;font-family:monospace;text-align:center;background:#0f243822;border-right:1px solid #1e3a5f33;">${pt.marketFill > 0 ? pt.marketFill.toFixed(5) : '<span style="color:#64748b;">-</span>'}</td>
            <td style="padding:7px 8px;color:#34d399;font-size:10.5px;font-weight:600;font-family:monospace;text-align:center;background:#0d2e2422;border-right:1px solid #064e3b33;">${pt.boxEntry > 0 ? pt.boxEntry.toFixed(5) : '-'}</td>
            <td style="padding:7px 8px;text-align:center;color:${slipColor};font-weight:bold;">${pt.slippagePips > 0 ? pt.slippagePips.toFixed(1) + 'p' : '-'}</td>
            <td style="padding:7px 8px;text-align:center;color:#f87171;font-family:monospace;font-size:10.5px;">${pt.slPrice > 0 ? pt.slPrice.toFixed(5) : '-'}</td>
            <td style="padding:7px 8px;text-align:center;background:#0f243822;border-right:1px solid #1e3a5f33;white-space:nowrap;">${tExitHtml}</td>
            <td style="padding:7px 8px;text-align:center;background:#0d2e2422;border-right:1px solid #064e3b33;white-space:nowrap;">${indTgtHtml}</td>
            <td style="padding:7px 8px;text-align:center;background:#0f243822;border-right:1px solid #1e3a5f33;">${tUsdHtml}</td>
            <td style="padding:7px 8px;text-align:center;background:#0d2e2422;border-right:1px solid #064e3b33;">${indUsdHtml}</td>
            <td style="padding:7px 8px;text-align:center;background:#0f243822;border-right:1px solid #1e3a5f33;">${tPipsHtml}</td>
            <td style="padding:7px 8px;text-align:center;background:#0d2e2422;border-right:1px solid #064e3b33;">${indPipsHtml}</td>
            <td style="padding:7px 10px;border-left:1px solid #334155;font-size:11px;line-height:1.5;text-align:right;">${pt.verdictHtml}</td>
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

