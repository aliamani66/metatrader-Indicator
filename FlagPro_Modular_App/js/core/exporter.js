// ==============================================================================
// 🤖 FlagPro Strategy Dashboard - MT5 Strategy Tester (.ini) & EA (.set) Exporter
// ==============================================================================

var currentExportConfig = null;

function getExactBrokerSymbol(baseSym) {
    if (typeof tradesRaw !== 'undefined' && tradesRaw && tradesRaw.length > 0 && tradesRaw[0].Symbol) {
        return tradesRaw[0].Symbol;
    }
    if (typeof ALL_SYMBOLS_DATA !== 'undefined' && ALL_SYMBOLS_DATA && ALL_SYMBOLS_DATA[baseSym]) {
        let sData = ALL_SYMBOLS_DATA[baseSym];
        if (sData.tradesRaw && sData.tradesRaw.length > 0 && sData.tradesRaw[0].Symbol) {
            return sData.tradesRaw[0].Symbol;
        }
    }
    let sym = baseSym || (typeof currentActiveSymbol !== 'undefined' ? currentActiveSymbol : 'EURUSD');
    if (!sym.endsWith('!')) {
        sym = sym + '!';
    }
    return sym;
}

function buildCleanScenarioTitle(rawTitle, sym) {
    let cleanTitle = 'Custom';
    if (!rawTitle) return cleanTitle;
    if (rawTitle.indexOf('Conservative') >= 0 || rawTitle.indexOf('محافظه') >= 0) cleanTitle = 'Conservative';
    else if (rawTitle.indexOf('Aggressive') >= 0 || rawTitle.indexOf('تهاجمی') >= 0) cleanTitle = 'Aggressive';
    else if (rawTitle.indexOf('Golden') >= 0 || rawTitle.indexOf('طلا') >= 0 || rawTitle.indexOf('Balanced') >= 0 || rawTitle.indexOf('متعادل') >= 0) cleanTitle = 'GoldenBalance';
    else if (rawTitle.indexOf('Diamond') >= 0 || rawTitle.indexOf('الماس') >= 0 || rawTitle.indexOf('Champion') >= 0) cleanTitle = 'DiamondKings';
    else if (rawTitle.indexOf('MaxProfit') >= 0 || rawTitle.indexOf('حداکثر') >= 0 || rawTitle.indexOf('Runner') >= 0) cleanTitle = 'MaxProfit';
    else if (rawTitle.indexOf('London') >= 0 || rawTitle.indexOf('لندن') >= 0) cleanTitle = 'LondonNY';
    else if (rawTitle.indexOf('سپر') >= 0 || rawTitle.indexOf('Shield') >= 0 || rawTitle.indexOf('UltraLow') >= 0 || rawTitle.indexOf('افت') >= 0) cleanTitle = 'UltraLowDDShield';
    else if (rawTitle.indexOf('سبد') >= 0 || rawTitle.indexOf('جامع') >= 0 || rawTitle.indexOf('تمام') >= 0 || rawTitle.indexOf('پایه') >= 0) cleanTitle = 'AllKings24H';
    else if (rawTitle.indexOf('چیدمان') >= 0 || rawTitle.indexOf('فعال') >= 0) cleanTitle = 'ActiveSetup';
    else {
        let asciiOnly = rawTitle.replace(/[^a-zA-Z0-9]/g, '');
        if (asciiOnly.length >= 3 && asciiOnly.toUpperCase() !== (sym || '').toUpperCase()) cleanTitle = asciiOnly;
        else cleanTitle = 'CustomSetup';
    }
    return cleanTitle;
}

// --------------------------------------------------------------------------
// 📄 MT5 Strategy Tester (.ini) Filename & Content Generator
// --------------------------------------------------------------------------

function buildMT5IniFilename(cfg) {
    let rawSym = cfg.symbol || (typeof currentActiveSymbol !== 'undefined' ? currentActiveSymbol : 'EURUSD');
    let sym = rawSym.replace(/[^a-zA-Z0-9]/g, '');
    if (!sym) sym = 'EURUSD';

    let cleanTitle = buildCleanScenarioTitle(cfg.title, sym);
    let wrVal = parseFloat(String(cfg.wr).replace(/[^0-9.]/g, '')) || 0;
    let pfVal = parseFloat(String(cfg.pf).replace(/[^0-9.]/g, '')) || 0;
    let wrPart = 'WR' + Math.round(wrVal);
    let pfPart = 'PF' + pfVal.toFixed(1);

    return ['FlagPro_Tester', sym, cleanTitle, wrPart, pfPart].join('_') + '.ini';
}

function generateIniFileText(cfg) {
    let rawSym = cfg.symbol || (typeof currentActiveSymbol !== 'undefined' ? currentActiveSymbol : 'EURUSD');
    let sym = getExactBrokerSymbol(rawSym);

    let safeTitle = (cfg.title || 'Custom').replace(/[^a-zA-Z0-9_\s\-]/g, ' ').trim();
    if (!safeTitle) safeTitle = 'Custom Strategy';

    let minPotVal = parseFloat(cfg.min_pot || 0).toFixed(2);
    let hoursStr = cfg.hours_str || '';
    let consecTrigVal = parseInt(cfg.consec_trig || 0);
    let consecActVal = parseInt(cfg.consec_action || 1);
    let disabledStr = cfg.disabled_kings_str || '';

    let sData = (typeof ALL_SYMBOLS_DATA !== 'undefined' && ALL_SYMBOLS_DATA) ? (ALL_SYMBOLS_DATA[rawSym] || ALL_SYMBOLS_DATA[sym] || ALL_SYMBOLS_DATA[currentActiveSymbol]) : null;
    let fromDate = '';
    let toDate = '';
    if (sData && sData.min_date && sData.max_date) {
        fromDate = sData.min_date;
        toDate = sData.max_date;
    } else {
        let now = new Date();
        toDate = now.getFullYear() + '.' + String(now.getMonth() + 1).padStart(2, '0') + '.' + String(now.getDate()).padStart(2, '0');
        let tenDaysAgo = new Date(now.getTime() - 10 * 24 * 3600 * 1000);
        fromDate = tenDaysAgo.getFullYear() + '.' + String(tenDaysAgo.getMonth() + 1).padStart(2, '0') + '.' + String(tenDaysAgo.getDate()).padStart(2, '0');
    }

    let cleanTitle = buildCleanScenarioTitle(cfg.title, sym);
    let isBaseScenario = (cleanTitle === 'AllKings24H');
    let useTF7Val = (cfg.use_tf7 !== undefined) ? (cfg.use_tf7 ? 'true' : 'false') : (isBaseScenario ? 'true' : 'false');
    let enableKingsM1Val = (cfg.enable_kings_m1 !== undefined) ? (cfg.enable_kings_m1 ? 'true' : 'false') : useTF7Val;
    let beBufferVal = (cfg.be_buffer !== undefined) ? parseFloat(cfg.be_buffer).toFixed(1) : (isBaseScenario ? '1.0' : '0.0');
    let maxDevVal = (cfg.max_dev !== undefined) ? parseFloat(cfg.max_dev).toFixed(1) : ((cleanTitle.indexOf('Diamond') >= 0 || cleanTitle.indexOf('Shield') >= 0) ? '2.0' : '2.5');

    let fNight = (cfg.filterNightHours !== undefined) ? (cfg.filterNightHours ? 'true' : 'false') : ((typeof simState !== 'undefined' && simState.filterNightHours !== undefined) ? (simState.filterNightHours ? 'true' : 'false') : 'true');
    let fPreLon = (cfg.filterPreLondonHunt !== undefined) ? (cfg.filterPreLondonHunt ? 'true' : 'false') : ((typeof simState !== 'undefined' && simState.filterPreLondonHunt !== undefined) ? (simState.filterPreLondonHunt ? 'true' : 'false') : 'true');
    let fToxic = (cfg.filterToxicPatterns !== undefined) ? (cfg.filterToxicPatterns ? 'true' : 'false') : ((typeof simState !== 'undefined' && simState.filterToxicPatterns !== undefined) ? (simState.filterToxicPatterns ? 'true' : 'false') : 'true');
    let fSingleLS = (cfg.filterSingleLS !== undefined) ? (cfg.filterSingleLS ? 'true' : 'false') : ((typeof simState !== 'undefined' && simState.filterSingleLS !== undefined) ? (simState.filterSingleLS ? 'true' : 'false') : 'true');
    let fPureFlags = (cfg.filterPureFlags !== undefined) ? (cfg.filterPureFlags ? 'true' : 'false') : ((typeof simState !== 'undefined' && simState.filterPureFlags !== undefined) ? (simState.filterPureFlags ? 'true' : 'false') : 'true');
    let fLowReward = (cfg.filterLowRewardVsFriction !== undefined) ? (cfg.filterLowRewardVsFriction ? 'true' : 'false') : 'true';

    let lines = [
        ';MetaTrader 5 Strategy Tester Configuration (.ini)',
        ';Auto-generated by FlagPro Strategy Dashboard',
        ';Drag & drop this file onto MetaTrader 5 Strategy Tester window (Ctrl+R)',
        '[Tester]',
        'Expert=FlagPro_Trader.ex5',
        'Symbol=' + sym,
        'Period=M1',
        'Optimization=0',
        'Model=4',
        'FromDate=' + fromDate,
        'ToDate=' + toDate,
        'ForwardMode=0',
        'Deposit=10000',
        'Currency=USD',
        'ProfitInPips=0',
        'Leverage=100',
        'ExecutionMode=0',
        'OptimizationCriterion=0',
        'Visual=1',
        '[TesterInputs]',
        '; === 🎯 ۱. حجم معاملات، اجرای سفارشات و خروج ۴ مرحله‌ای ===',
        'InpOrderExecMode=0',
        'InpLimitExpirationBars=40',
        'InpEnableScaleOut=true',
        'InpLot_TP1=0.01',
        'InpLot_TP2=0.01',
        'InpLot_TP3=0.01',
        'InpLot_TP4=0.01',
        'InpMoveToBreakEven=true',
        'InpBEBufferPips=' + beBufferVal,
        'InpTrailToTP1=true',
        'InpTrailToTP2=true',
        '; === 👑 ۲. سلاطین طلایی، سناریوی داشبورد و ستاپ‌ها ===',
        'InpScenarioName=' + safeTitle,
        'InpOnlyTradeKings=true',
        'InpTradeOnlyGoldenKings=true',
        'InpAllowedKingsList=' + (cfg.allowed_kings_str || ''),
        'InpDisabledKingsList=' + disabledStr,
        'InpEnableKingsM15=true',
        'InpEnableKingsM5=true',
        'InpEnableKingsM1=' + enableKingsM1Val,
        'InpAllowOverlappingTrades=true',
        '; === ⚡ ۳. مدیریت ریسک، حد ضرر، لغزش و مجیک نامبر ===',
        'InpMagicNumber=777123',
        'InpSLOffsetPips=8.0',
        'InpMaxSLPips=0.0',
        'InpSlippagePoints=20',
        'InpMaxEntryDeviationPips=' + maxDevVal,
        'InpMaxOpenGroups=5',
        '; === ⏰ ۴. ساعات معاملاتی، کف سود و فیوز ایمنی ===',
        'InpAllowedTradingHours=' + hoursStr,
        'InpMinTradePotential=' + minPotVal,
        'InpConsecLossTrigger=' + consecTrigVal,
        'InpConsecLossAction=' + consecActVal,
        '; === 🛡️ ۵. فیلترهای هوشمند ضد استاپ و هزینه بروکر ===',
        'InpFilterNightHours=' + fNight,
        'InpFilterPreLondonHunt=' + fPreLon,
        'InpFilterToxicPatterns=' + fToxic,
        'InpFilterSingleLS=' + fSingleLS,
        'InpFilterPureFlags=' + fPureFlags,
        'InpFilterLowRewardVsFriction=' + fLowReward,
        'InpBrokerCommissionPerLot=6.0',
        'InpEstimatedSpreadPips=0.8',
        'InpMinNetProfitRatioTP1=1.0',
        '; === ⏱️ ۶. تایم‌فریم‌های فعال معامله و سرعت پردازش ===',
        'InpUseTF7=' + useTF7Val,
        'InpUseTF6=true',
        'InpUseTF5=true',
        'InpTradeMacroTFs=false',
        'InpLookbackBars=15000',
        'InpHistoryMode=1',
        'InpHistoryStartDate=2025.01.01 00:00:00',
        'InpHistoryDays=10',
        '; === 🎯 ۷. خطوط گرافیک و استخراج ===',
        'InpAutoDrawTrades=true',
        'InpUniqueTradeColors=true',
        'InpExportCSV=true'
    ];

    return lines.join(String.fromCharCode(13, 10));
}

// --------------------------------------------------------------------------
// 📄 MT5 EA Settings (.set) Filename & Content Generator
// --------------------------------------------------------------------------

function buildMT5SetFilename(cfg) {
    let rawSym = cfg.symbol || (typeof currentActiveSymbol !== 'undefined' ? currentActiveSymbol : 'EURUSD');
    let sym = rawSym.replace(/[^a-zA-Z0-9]/g, '');
    if (!sym) sym = 'EURUSD';

    let cleanTitle = buildCleanScenarioTitle(cfg.title, sym);
    let wrVal = parseFloat(String(cfg.wr).replace(/[^0-9.]/g, '')) || 0;
    let pfVal = parseFloat(String(cfg.pf).replace(/[^0-9.]/g, '')) || 0;
    let wrPart = 'WR' + Math.round(wrVal);
    let pfPart = 'PF' + pfVal.toFixed(1);

    let now = new Date();
    let y = now.getFullYear();
    let m = String(now.getMonth() + 1).padStart(2, '0');
    let d = String(now.getDate()).padStart(2, '0');
    let hh = String(now.getHours()).padStart(2, '0');
    let mm = String(now.getMinutes()).padStart(2, '0');
    let dtPart = y + '-' + m + '-' + d + '_' + hh + '-' + mm;

    return ['FlagPro', sym, cleanTitle, wrPart, pfPart, dtPart].join('_') + '.set';
}

function generateSetFileText(cfg) {
    let rawSym = cfg.symbol || (typeof currentActiveSymbol !== 'undefined' ? currentActiveSymbol : 'EURUSD');
    let sym = rawSym.replace(/[^a-zA-Z0-9]/g, '') || 'EURUSD';
    let filename = buildMT5SetFilename(cfg);
    let now = new Date();
    let nowStr = now.getFullYear() + '.' + String(now.getMonth() + 1).padStart(2, '0') + '.' + String(now.getDate()).padStart(2, '0') + ' ' + String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0') + ':' + String(now.getSeconds()).padStart(2, '0');

    let safeTitle = (cfg.title || 'Custom').replace(/[^a-zA-Z0-9_\s\-]/g, ' ').trim();
    if (!safeTitle) safeTitle = 'Custom Strategy';

    let cleanTitle = buildCleanScenarioTitle(cfg.title, sym);
    let isBaseScenario = (cleanTitle === 'AllKings24H');
    let useTF7Val = (cfg.use_tf7 !== undefined) ? (cfg.use_tf7 ? 'true' : 'false') : (isBaseScenario ? 'true' : 'false');
    let enableKingsM1Val = (cfg.enable_kings_m1 !== undefined) ? (cfg.enable_kings_m1 ? 'true' : 'false') : useTF7Val;
    let beBufferVal = (cfg.be_buffer !== undefined) ? parseFloat(cfg.be_buffer).toFixed(1) : (isBaseScenario ? '1.0' : '0.0');
    let maxDevVal = (cfg.max_dev !== undefined) ? parseFloat(cfg.max_dev).toFixed(1) : ((cleanTitle.indexOf('Diamond') >= 0 || cleanTitle.indexOf('Shield') >= 0) ? '2.0' : '2.5');

    let fNight = (cfg.filterNightHours !== undefined) ? (cfg.filterNightHours ? 'true' : 'false') : ((typeof simState !== 'undefined' && simState.filterNightHours !== undefined) ? (simState.filterNightHours ? 'true' : 'false') : 'true');
    let fPreLon = (cfg.filterPreLondonHunt !== undefined) ? (cfg.filterPreLondonHunt ? 'true' : 'false') : ((typeof simState !== 'undefined' && simState.filterPreLondonHunt !== undefined) ? (simState.filterPreLondonHunt ? 'true' : 'false') : 'true');
    let fToxic = (cfg.filterToxicPatterns !== undefined) ? (cfg.filterToxicPatterns ? 'true' : 'false') : ((typeof simState !== 'undefined' && simState.filterToxicPatterns !== undefined) ? (simState.filterToxicPatterns ? 'true' : 'false') : 'true');
    let fSingleLS = (cfg.filterSingleLS !== undefined) ? (cfg.filterSingleLS ? 'true' : 'false') : ((typeof simState !== 'undefined' && simState.filterSingleLS !== undefined) ? (simState.filterSingleLS ? 'true' : 'false') : 'true');
    let fPureFlags = (cfg.filterPureFlags !== undefined) ? (cfg.filterPureFlags ? 'true' : 'false') : ((typeof simState !== 'undefined' && simState.filterPureFlags !== undefined) ? (simState.filterPureFlags ? 'true' : 'false') : 'true');
    let fLowReward = (cfg.filterLowRewardVsFriction !== undefined) ? (cfg.filterLowRewardVsFriction ? 'true' : 'false') : 'true';

    let lines = [
        ';+------------------------------------------------------------------+',
        ';| FlagPro_Trader EA - Expert Advisor Settings (.set)               |',
        ';| File: ' + filename,
        ';| Auto-generated from FlagPro Strategy Dashboard                   |',
        ';| Date: ' + nowStr,
        ';| Target Folder: MQL5/Experts/Settings/ (or تنظیمات/)              |',
        ';| Symbol: ' + sym + ' | Scenario: ' + safeTitle,
        ';| Win Rate: ' + cfg.wr + ' | Profit Factor: ' + cfg.pf,
        ';| Avg Profit: $' + cfg.avg + ' | Active Kings: ' + cfg.kings_count,
        ';+------------------------------------------------------------------+',
        '',
        ';=== ۱. حجم معاملات، اجرای سفارشات و خروج ۴ مرحله‌ای ===',
        'InpOrderExecMode=0',
        'InpLimitExpirationBars=40',
        'InpEnableScaleOut=true',
        'InpLot_TP1=0.01',
        'InpLot_TP2=0.01',
        'InpLot_TP3=0.01',
        'InpLot_TP4=0.01',
        'InpMoveToBreakEven=true',
        'InpBEBufferPips=' + beBufferVal,
        'InpTrailToTP1=true',
        'InpTrailToTP2=true',
        '',
        ';=== ۲. سلاطین طلایی، سناریوی داشبورد و ستاپ‌ها ===',
        'InpScenarioName=' + safeTitle,
        'InpOnlyTradeKings=true',
        'InpTradeOnlyGoldenKings=true',
        'InpAllowedKingsList=' + (cfg.allowed_kings_str || ''),
        'InpDisabledKingsList=' + (cfg.disabled_kings_str || ''),
        'InpEnableKingsM15=true',
        'InpEnableKingsM5=true',
        'InpEnableKingsM1=' + enableKingsM1Val,
        'InpAllowOverlappingTrades=true',
        '',
        ';=== ۳. مدیریت ریسک، حد ضرر، لغزش و مجیک نامبر ===',
        'InpMagicNumber=777123',
        'InpSLOffsetPips=8.0',
        'InpMaxSLPips=0.0',
        'InpSlippagePoints=20',
        'InpMaxEntryDeviationPips=' + maxDevVal,
        'InpMaxOpenGroups=5',
        '',
        ';=== ۴. ساعات معاملاتی، کف سود و فیوز ایمنی ===',
        'InpAllowedTradingHours=' + (cfg.hours_str || ''),
        'InpMinTradePotential=' + parseFloat(cfg.min_pot || 0).toFixed(2),
        'InpConsecLossTrigger=' + parseInt(cfg.consec_trig || 0),
        'InpConsecLossAction=' + parseInt(cfg.consec_action || 1),
        '',
        ';=== ۵. فیلترهای هوشمند ضد استاپ و هزینه کمیسیون ===',
        'InpFilterNightHours=' + fNight,
        'InpFilterPreLondonHunt=' + fPreLon,
        'InpFilterToxicPatterns=' + fToxic,
        'InpFilterSingleLS=' + fSingleLS,
        'InpFilterPureFlags=' + fPureFlags,
        'InpFilterLowRewardVsFriction=' + fLowReward,
        'InpBrokerCommissionPerLot=6.0',
        'InpEstimatedSpreadPips=0.8',
        'InpMinNetProfitRatioTP1=1.0',
        '',
        ';=== ۶. تایم‌فریم‌های فعال معامله و سرعت پردازش ===',
        'InpUseTF7=' + useTF7Val,
        'InpUseTF6=true',
        'InpUseTF5=true',
        'InpTradeMacroTFs=false',
        'InpLookbackBars=15000',
        'InpHistoryMode=1',
        'InpHistoryStartDate=2025.01.01 00:00:00',
        'InpHistoryDays=10',
        '',
        ';=== ۷. گرافیک و رسم روی چارت ===',
        'InpAutoDrawTrades=true',
        'InpUniqueTradeColors=true',
        'InpExportCSV=true'
    ];
    return lines.join(String.fromCharCode(13, 10));
}

// --------------------------------------------------------------------------
// 💾 Binary / UTF-16 LE Encoding and File Download
// --------------------------------------------------------------------------

function createUTF16LEBlob(text) {
    let buffer = new ArrayBuffer(2 + text.length * 2);
    let view = new DataView(buffer);
    view.setUint16(0, 0xFEFF, true);
    for (let i = 0; i < text.length; i++) {
        view.setUint16(2 + i * 2, text.charCodeAt(i), true);
    }
    return new Blob([buffer], { type: 'application/octet-stream' });
}

function downloadCurrentMT5IniFile() {
    if (!currentExportConfig) return;
    let filename = buildMT5IniFilename(currentExportConfig);
    let text = generateIniFileText(currentExportConfig);
    let blob = createUTF16LEBlob(text);
    let url = URL.createObjectURL(blob);
    let a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    if (typeof showSaveNotification === 'function') {
        showSaveNotification('📥 فایل استراتژی تستر «' + filename + '» با فرمت (.ini) دانلود شد. می‌توانید آن را مستقیماً داخل پنجره Strategy Tester متاتریدر Drag & Drop کنید.');
    }
}

function downloadCurrentMT5SetFile() {
    if (!currentExportConfig) return;
    let filename = buildMT5SetFilename(currentExportConfig);
    let text = generateSetFileText(currentExportConfig);
    let blob = createUTF16LEBlob(text);
    let url = URL.createObjectURL(blob);
    let a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    if (typeof showSaveNotification === 'function') {
        showSaveNotification('📥 فایل تنظیمات اکسپرت «' + filename + '» با فرمت (.set) دانلود شد.');
    }
}

// --------------------------------------------------------------------------
// 🚀 Preset / Setup Exporters to MT5
// --------------------------------------------------------------------------

function exportPresetToMT5(idx) {
    try {
        let p = (smartPresets || []).find(x => x.idx == idx);
        if (!p && smartPresets && smartPresets.length > 0) {
            p = smartPresets[0];
        }
        if (!p) {
            if (typeof alert === 'function') alert('سناریو برای خروجی متاتریدر یافت نشد!');
            return;
        }

        let allowedHours = [];
        if (p.hours) {
            for (let h = 0; h < 24; h++) {
                if (p.hours[h]) allowedHours.push(h < 10 ? '0' + h : '' + h);
            }
        }
        let hoursStr = allowedHours.length === 24 ? '' : allowedHours.join(',');

        let disabledKings = [];
        let enabledSet = new Set(p.kings || []);
        for (let k of (kingsSimList || [])) {
            if (k && k.kk && !enabledSet.has(k.kk)) {
                let kClean = k.kk.replace(/\|(M\d+)/, ' [$1]');
                disabledKings.push(kClean);
            }
        }
        let disabledStr = disabledKings.join(', ');

        let actionInt = p.consec_day ? 3 : (p.consec_sk === 2 ? 2 : 1);
        if (!p.consec_trig || p.consec_trig <= 0) actionInt = 0;

        let sym = (typeof currentActiveSymbol !== 'undefined' && currentActiveSymbol) ? currentActiveSymbol : 'EURUSD';
        let isBase = (p.idx === 4 || (p.title && (p.title.includes('پایه') || p.title.includes('جامع') || p.title.includes('AllKings'))));
        let useTF7 = isBase ? true : false;
        let beBuffer = isBase ? 1.0 : 0.0;
        let maxDev = (p.title && (p.title.includes('الماس') || p.title.includes('سپر'))) ? 2.0 : 2.5;

        let fNightPreset = isBase ? false : (p.hours_name === 'lon_ny' || p.hours_name === 'no_night');
        let fPreLonPreset = isBase ? false : true;
        let fToxicPreset = isBase ? false : true;
        let fSingleLSPreset = isBase ? false : true;
        let fPureFlagsPreset = isBase ? false : true;

        let allowedKings = (p.kings && Array.isArray(p.kings)) ? p.kings.join(', ') : '';

        let config = {
            title: (p.title || 'Custom').replace(/[^a-zA-Z0-9_\s\-\u0600-\u06FF]/gi, '').trim(),
            min_pot: (p.min_pot !== undefined && !isNaN(Number(p.min_pot))) ? Number(p.min_pot) : 0,
            hours_str: hoursStr,
            consec_trig: p.consec_trig || 0,
            consec_action: actionInt,
            allowed_kings_str: allowedKings,
            disabled_kings_str: disabledStr,
            use_tf7: useTF7,
            enable_kings_m1: useTF7,
            be_buffer: beBuffer,
            max_dev: maxDev,
            filterNightHours: fNightPreset,
            filterPreLondonHunt: fPreLonPreset,
            filterToxicPatterns: fToxicPreset,
            filterSingleLS: fSingleLSPreset,
            filterPureFlags: fPureFlagsPreset,
            cnt: p.cnt || p.count || '-',
            wr: p.wr || 0,
            pf: p.pf || 0,
            avg: p.avg || 0,
            net: p.net || 0,
            kings_count: (p.kings ? p.kings.length : (kingsSimList ? kingsSimList.length : 0)),
            symbol: sym
        };

        openMT5ExportModal(config);
    } catch(err) {
        console.error('Error in exportPresetToMT5:', err);
        if (typeof alert === 'function') alert('خطا در خروجی متاتریدر: ' + err.message);
    }
}

function exportPresetSetFile(idx) {
    try {
        let p = (smartPresets || []).find(x => x.idx == idx);
        if (!p && smartPresets && smartPresets.length > 0) {
            p = smartPresets[0];
        }
        if (!p) {
            if (typeof alert === 'function') alert('سناریو برای خروجی تنظیمات اندیکاتور یافت نشد!');
            return;
        }

        let allowedHours = [];
        if (p.hours) {
            for (let h = 0; h < 24; h++) {
                if (p.hours[h]) allowedHours.push(h < 10 ? '0' + h : '' + h);
            }
        }
        let hoursStr = allowedHours.length === 24 ? '' : allowedHours.join(',');

        let disabledKings = [];
        let enabledSet = new Set(p.kings || []);
        for (let k of (kingsSimList || [])) {
            if (k && k.kk && !enabledSet.has(k.kk)) {
                let kClean = k.kk.replace(/\|(M\d+)/, ' [$1]');
                disabledKings.push(kClean);
            }
        }
        let disabledStr = disabledKings.join(', ');

        let sym = (typeof currentActiveSymbol !== 'undefined' && currentActiveSymbol) ? currentActiveSymbol : 'EURUSD';
        let isBase = (p.idx === 4 || (p.title && (p.title.includes('پایه') || p.title.includes('جامع') || p.title.includes('AllKings'))));
        let useTF7 = isBase ? true : false;
        let beBuffer = isBase ? 1.0 : 0.0;
        let maxDev = (p.title && (p.title.includes('الماس') || p.title.includes('سپر'))) ? 2.0 : 2.5;

        let fNightPreset = isBase ? false : (p.hours_name === 'lon_ny' || p.hours_name === 'no_night');
        let fPreLonPreset = isBase ? false : true;
        let fToxicPreset = isBase ? false : true;
        let fSingleLSPreset = isBase ? false : true;
        let fPureFlagsPreset = isBase ? false : true;

        let allowedKings = (p.kings && Array.isArray(p.kings)) ? p.kings.join(', ') : '';

        let config = {
            title: (p.title || 'Custom').replace(/[^a-zA-Z0-9_\s\-\u0600-\u06FF]/gi, '').trim(),
            min_pot: (p.min_pot !== undefined && !isNaN(Number(p.min_pot))) ? Number(p.min_pot) : 0,
            hours_str: hoursStr,
            consec_trig: p.consec_trig || 0,
            consec_action: p.consec_day ? 3 : (p.consec_sk === 2 ? 2 : 1),
            allowed_kings_str: allowedKings,
            disabled_kings_str: disabledStr,
            use_tf7: useTF7,
            enable_kings_m1: useTF7,
            be_buffer: beBuffer,
            max_dev: maxDev,
            filterNightHours: fNightPreset,
            filterPreLondonHunt: fPreLonPreset,
            filterToxicPatterns: fToxicPreset,
            filterSingleLS: fSingleLSPreset,
            filterPureFlags: fPureFlagsPreset,
            cnt: p.cnt || p.count || '-',
            wr: p.wr || 0,
            pf: p.pf || 0,
            avg: p.avg || 0,
            net: p.net || 0,
            kings_count: (p.kings ? p.kings.length : (kingsSimList ? kingsSimList.length : 0)),
            symbol: sym
        };

        let filename = buildMT5SetFilename(config);
        let text = generateSetFileText(config);
        let blob = createUTF16LEBlob(text);
        let url = URL.createObjectURL(blob);
        let a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        if (typeof showSaveNotification === 'function') {
            showSaveNotification('📥 فایل تنظیمات اندیکاتور (.set) «' + filename + '» دانلود شد.');
        }
    } catch(err) {
        console.error('Error in exportPresetSetFile:', err);
        if (typeof alert === 'function') alert('خطا در دانلود تنظیمات اندیکاتور: ' + err.message);
    }
}

function exportCurrentStateToMT5() {
    try {
        let allowedHours = [];
        for (let h = 0; h < 24; h++) {
            if (simState.allowedHours && simState.allowedHours[h]) allowedHours.push(h < 10 ? '0' + h : '' + h);
        }
        let hoursStr = allowedHours.length === 24 ? '' : allowedHours.join(',');

        let allowedKings = [];
        if (simState.enabledKings) {
            for (let kk of simState.enabledKings) {
                allowedKings.push(kk);
            }
        }
        let allowedStr = allowedKings.join(', ');

        let disabledKings = [];
        for (let k of (kingsSimList || [])) {
            if (k && k.kk && simState.enabledKings && !simState.enabledKings.has(k.kk)) {
                let kClean = k.kk.replace(/\|(M\d+)/, ' [$1]');
                disabledKings.push(kClean);
            }
        }
        let disabledStr = disabledKings.join(', ');

        let actionInt = simState.consecLossSkipDay ? 3 : (simState.consecLossSkipCount === 2 ? 2 : 1);
        if (!simState.consecLossTrigger || simState.consecLossTrigger <= 0) actionInt = 0;

        let elNet = document.getElementById('eqKpiNetVal');
        let elWr = document.getElementById('eqKpiWR');
        let elPf = document.getElementById('eqKpiPF');
        let elCnt = document.getElementById('eqKpiCnt');
        let elAvg = document.getElementById('eqKpiAvgTrade');

        let wrVal = elWr ? parseFloat(elWr.textContent.replace(/[^0-9.]/g, '')) || 0 : 0;
        let pfVal = elPf ? parseFloat(elPf.textContent.replace(/[^0-9.]/g, '')) || 0 : 0;
        let avgVal = elAvg ? parseFloat(elAvg.textContent.replace(/[^0-9.-]/g, '')) || 0 : 0;
        let kingsCount = simState.enabledKings ? simState.enabledKings.size : (kingsSimList ? kingsSimList.length : 0);
        let sym = (typeof currentActiveSymbol !== 'undefined' && currentActiveSymbol) ? currentActiveSymbol : 'EURUSD';

        let hasM1Kings = false;
        if (simState.enabledKings) {
            for (let kk of simState.enabledKings) {
                if (kk.includes('|M1') || kk.includes('[M1]')) {
                    hasM1Kings = true;
                    break;
                }
            }
        }

        let config = {
            title: 'چیدمان فعال (' + sym + ')',
            min_pot: simState.minProfit || 0,
            hours_str: hoursStr,
            consec_trig: simState.consecLossTrigger || 0,
            consec_action: actionInt,
            allowed_kings_str: allowedStr,
            disabled_kings_str: disabledStr,
            use_tf7: hasM1Kings,
            enable_kings_m1: hasM1Kings,
            be_buffer: 0.0,
            max_dev: 2.5,
            filterNightHours: (simState.filterNightHours !== undefined) ? simState.filterNightHours : false,
            filterPreLondonHunt: (simState.filterPreLondonHunt !== undefined) ? simState.filterPreLondonHunt : false,
            filterToxicPatterns: (simState.filterToxicPatterns !== undefined) ? simState.filterToxicPatterns : false,
            filterSingleLS: (simState.filterSingleLS !== undefined) ? simState.filterSingleLS : false,
            filterPureFlags: (simState.filterPureFlags !== undefined) ? simState.filterPureFlags : false,
            cnt: elCnt ? elCnt.textContent : '-',
            wr: wrVal,
            pf: pfVal,
            avg: avgVal,
            net: elNet ? elNet.textContent : '-',
            kings_count: kingsCount,
            symbol: sym
        };

        openMT5ExportModal(config);
    } catch(err) {
        console.error('Error in exportCurrentStateToMT5:', err);
        if (typeof alert === 'function') alert('خطا در خروجی تنظیمات فعال: ' + err.message);
    }
}

function exportCustomPresetToMT5(id) {
    try {
        let list = [];
        try {
            list = JSON.parse(localStorage.getItem('flagpro_custom_presets') || '[]');
        } catch(e) {
            list = [];
        }
        let p = list.find(x => String(x.id) === String(id));
        if (!p && typeof customPresetsList !== 'undefined' && customPresetsList) {
            p = customPresetsList.find(x => String(x.id) === String(id));
        }
        if (!p) {
            if (typeof alert === 'function') alert('سناریوی شخصی یافت نشد!');
            return;
        }

        let allowedHours = [];
        if (p.hours) {
            for (let h = 0; h < 24; h++) {
                if (p.hours[h]) allowedHours.push(h < 10 ? '0' + h : '' + h);
            }
        }
        let hoursStr = allowedHours.length === 24 ? '' : allowedHours.join(',');

        let disabledKings = [];
        let enabledSet = new Set(p.kings || []);
        for (let k of (kingsSimList || [])) {
            if (k && k.kk && !enabledSet.has(k.kk)) {
                let kClean = k.kk.replace(/\|(M\d+)/, ' [$1]');
                disabledKings.push(kClean);
            }
        }
        let disabledStr = disabledKings.join(', ');

        let actionInt = p.consec_day ? 3 : (p.consec_sk === 2 ? 2 : 1);
        if (!p.consec_trig || p.consec_trig <= 0) actionInt = 0;

        let sym = (typeof currentActiveSymbol !== 'undefined' && currentActiveSymbol) ? currentActiveSymbol : 'EURUSD';

        // Recalculate metrics on current simTrades if available
        let kSet = new Set(p.kings || []);
        let sub = (typeof simTrades !== 'undefined' && simTrades) ? simTrades.filter(t => t.k === 1 && kSet.has(t.kk) && (t.pot === undefined || t.pot >= p.min_pot) && p.hours && p.hours[t.h]) : [];
        let c = sub.length;
        let nt = sub.reduce((acc, t) => acc + t.p, 0);
        let wins = sub.filter(t => t.p > 0).length;
        let wr = c > 0 ? (wins / c * 100) : (p.wr || 0);
        let avg = c > 0 ? (nt / c) : (p.avg || 0);
        let gp = sub.filter(t => t.p > 0).reduce((acc, t) => acc + t.p, 0);
        let gl = sub.filter(t => t.p <= 0).reduce((acc, t) => acc + Math.abs(t.p), 0);
        let pf = gl > 0 ? (gp / gl) : (p.pf || 999);

        let allowedKings = (p.kings && Array.isArray(p.kings)) ? p.kings.join(', ') : '';

        let config = {
            title: (p.title || 'Custom').replace(/[^a-zA-Z0-9_\s\-\u0600-\u06FF]/gi, '').trim(),
            min_pot: (p.min_pot !== undefined && !isNaN(Number(p.min_pot))) ? Number(p.min_pot) : 0,
            hours_str: hoursStr,
            consec_trig: p.consec_trig || 0,
            consec_action: actionInt,
            allowed_kings_str: allowedKings,
            disabled_kings_str: disabledStr,
            cnt: c || p.cnt || '-',
            wr: wr,
            pf: pf,
            avg: avg,
            net: nt || p.net || '-',
            kings_count: (p.kings ? p.kings.length : (kingsSimList ? kingsSimList.length : 0)),
            symbol: sym
        };

        openMT5ExportModal(config);
    } catch(err) {
        console.error('Error in exportCustomPresetToMT5:', err);
        if (typeof alert === 'function') alert('خطا در خروجی متاتریدر سناریوی شخصی: ' + err.message);
    }
}

// Export functions to global scope
if (typeof window !== 'undefined') {
    window.exportPresetToMT5 = exportPresetToMT5;
    window.exportPresetSetFile = exportPresetSetFile;
    window.exportCustomPresetToMT5 = exportCustomPresetToMT5;
    window.exportCurrentStateToMT5 = exportCurrentStateToMT5;
}

// --------------------------------------------------------------------------
// 🖥️ Modal UI Controller
// --------------------------------------------------------------------------

function openMT5ExportModal(cfg) {
    try {
        currentExportConfig = cfg;
        let modal = document.getElementById('mt5ExportModal');
        if (!modal) {
            console.error('mt5ExportModal not found!');
            if (typeof alert === 'function') alert('خطا: پنجره خروجی متاتریدر در صفحه پیدا نشد.');
            return;
        }

        modal.style.display = 'flex';
        modal.style.zIndex = '99999999';

        let filenameIni = buildMT5IniFilename(cfg);
        let elTitle = document.getElementById('mt5ModalTitle');
        if (elTitle) elTitle.textContent = cfg.title;
        let fileBadge = document.getElementById('mt5ModalFilename');
        if (fileBadge) fileBadge.textContent = filenameIni;

        let elMinPot = document.getElementById('mt5ParamMinPot');
        if (elMinPot) elMinPot.textContent = '$' + Number(cfg.min_pot || 0).toFixed(2);
        
        let elHours = document.getElementById('mt5ParamHours');
        if (elHours) elHours.textContent = cfg.hours_str ? cfg.hours_str : '۲۴ ساعته (بدون محدودیت)';

        let elConsec = document.getElementById('mt5ParamConsec');
        if (elConsec) elConsec.textContent = cfg.consec_trig > 0 ? (cfg.consec_trig + ' استاپ متوالی') : 'خاموش';
        
        let actName = 'بدون اقدام';
        if (cfg.consec_action === 1) actName = 'رد کردن ۱ معامله بعدی';
        else if (cfg.consec_action === 2) actName = 'رد کردن ۲ معامله بعدی';
        else if (cfg.consec_action === 3) actName = 'توقف تا پایان روز جاری';
        let elConsecAct = document.getElementById('mt5ParamConsecAct');
        if (elConsecAct) elConsecAct.textContent = actName;

        let elAllowed = document.getElementById('mt5ParamAllowed');
        if (elAllowed) elAllowed.textContent = cfg.allowed_kings_str ? cfg.allowed_kings_str : 'تمام سلاطین پیش‌فرض';

        let elDisabled = document.getElementById('mt5ParamDisabled');
        if (elDisabled) elDisabled.textContent = cfg.disabled_kings_str ? cfg.disabled_kings_str : 'هیچ‌کدام (تمام سلاطین فعال)';

        let fullIniText = generateIniFileText(cfg);
        let codeBox = document.getElementById('mt5ConfigCodeBox');
        if (codeBox) codeBox.textContent = fullIniText;

        if (typeof showSaveNotification === 'function') {
            showSaveNotification('🤖 پنجره کانفیگ استراتژی تستر متاتریدر ۵ (.ini) برای «' + (cfg.title || 'سناریو') + '» باز شد.');
        }
    } catch(err) {
        console.error('Error in openMT5ExportModal:', err);
        if (typeof alert === 'function') alert('خطا در باز کردن پنجره متاتریدر: ' + err.message);
    }
}

function closeMT5ExportModal() {
    let modal = document.getElementById('mt5ExportModal');
    if (modal) modal.style.display = 'none';
}

function getMT5TesterProfilesFolderPath() {
    return ['C:', 'Users', 'USER', 'AppData', 'Roaming', 'MetaQuotes', 'Terminal', '3F2C3A2F8B221C9D88E569F2FD1D3E97', 'MQL5', 'Profiles', 'Tester'].join(String.fromCharCode(92));
}

function getMT5ExpertsSettingsFolderPath() {
    return ['C:', 'Users', 'USER', 'AppData', 'Roaming', 'MetaQuotes', 'Terminal', '3F2C3A2F8B221C9D88E569F2FD1D3E97', 'MQL5', 'Experts', 'تنظیمات'].join(String.fromCharCode(92));
}

async function openTesterFolder() {
    try {
        let resp = await fetch('http://127.0.0.1:8288/open_tester_folder', { method: 'POST' });
        if (resp.ok) {
            let json = await resp.json();
            if (json.success) return;
        }
    } catch(e) {}
    
    let path = getMT5TesterProfilesFolderPath();
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(path).then(() => {
            alert('📋 مسیر پوشه پروفایل تستر متاتریدر در کلیپ‌بورد کپی شد:\n\n' + path + '\n\nمی‌توانید در نوار آدرس File Explorer ویندوز Paste کنید.');
        }).catch(() => {
            prompt('مسیر پوشه تستر (Ctrl+C برای کپی):', path);
        });
    } else {
        prompt('مسیر پوشه تستر (Ctrl+C برای کپی):', path);
    }
}

async function openSettingsFolder() {
    try {
        let resp = await fetch('http://127.0.0.1:8288/open_folder', { method: 'POST' });
        if (resp.ok) {
            let json = await resp.json();
            if (json.success) return;
        }
    } catch(e) {}
    
    let path = getMT5ExpertsSettingsFolderPath();
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(path).then(() => {
            alert('📋 مسیر پوشه تنظیمات اکسپرت در کلیپ‌بورد کپی شد:\n\n' + path + '\n\nمی‌توانید در نوار آدرس File Explorer ویندوز Paste کنید.');
        }).catch(() => {
            prompt('مسیر پوشه تنظیمات (Ctrl+C برای کپی):', path);
        });
    } else {
        prompt('مسیر پوشه تنظیمات (Ctrl+C برای کپی):', path);
    }
}

async function saveCurrentMT5IniFileToTesterFolder() {
    if (!currentExportConfig) return;
    let text = generateIniFileText(currentExportConfig);
    let filename = buildMT5IniFilename(currentExportConfig);
    let btn = document.getElementById('btnSaveToTesterFolder');
    let ind = document.getElementById('saveStatusIndicator');
    if (btn) btn.innerHTML = '<span>⏳ در حال ذخیره در تستر...</span>';
    if (ind) { ind.textContent = 'در حال ذخیره‌سازی در تستر...'; ind.style.color = '#facc15'; }

    // 1. Try local bridge server
    try {
        let resp = await fetch('http://127.0.0.1:8288/save_ini', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: filename, content: text })
        });
        if (resp.ok) {
            let json = await resp.json();
            if (json.success) {
                if (btn) btn.innerHTML = '<span>✅ در Profiles/Tester ذخیره شد!</span>';
                if (ind) { ind.textContent = '✅ فایل در Profiles/Tester ذخیره شد'; ind.style.color = '#4ade80'; }
                showSaveNotification('فایل تستر <b>' + filename + '</b> با موفقیت در پوشه <b>MQL5/Profiles/Tester</b> ذخیره شد.');
                setTimeout(() => {
                    if (btn) btn.innerHTML = '<span>💾 ذخیره تو Profiles/Tester (.ini)</span>';
                }, 3500);
                return;
            }
        }
    } catch(e) {
        // Bridge server is offline
    }

    // 2. Safe Fallback: Direct download in UTF-16 LE
    downloadCurrentMT5IniFile();
    if (btn) btn.innerHTML = '<span>📥 فایل تستر دانلود شد</span>';
    if (ind) { ind.textContent = 'فایل دانلود شد (فایل را به پنجره Strategy Tester بکشید)'; ind.style.color = '#38bdf8'; }
    showSaveNotification('فایل تستر <b>' + filename + '</b> با فرمت (.ini) دانلود شد. می‌توانید آن را مستقیماً داخل پنجره Strategy Tester متاتریدر Drag & Drop کنید.');
    setTimeout(() => {
        if (btn) btn.innerHTML = '<span>💾 ذخیره تو Profiles/Tester (.ini)</span>';
    }, 3500);
}

function showSaveNotification(msg) {
    let toast = document.getElementById('flagproGlobalToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'flagproGlobalToast';
        toast.style.cssText = 'position:fixed;bottom:24px;left:24px;z-index:9999999;background:rgba(15,23,42,0.95);border:1px solid #10b981;box-shadow:0 10px 25px rgba(0,0,0,0.8);border-radius:8px;padding:12px 18px;color:#f1f5f9;font-size:12.5px;display:flex;align-items:center;gap:10px;direction:rtl;max-width:420px;transition:all 0.3s ease;';
        document.body.appendChild(toast);
    }
    toast.innerHTML = '<span style="font-size:18px;">💾</span><div>' + msg + '</div>';
    toast.style.display = 'flex';
    toast.style.opacity = '1';
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => { toast.style.display = 'none'; }, 300);
    }, 5000);
}

function copyMT5ConfigText() {
    if (!currentExportConfig) return;
    let text = generateIniFileText(currentExportConfig);
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            alert('📋 تمام کانفیگ Strategy Tester (.ini) با موفقیت کپی شد!');
        }).catch(() => {
            fallbackCopy();
        });
    } else {
        fallbackCopy();
    }

    function fallbackCopy() {
        let box = document.getElementById('mt5ConfigCodeBox');
        if (box) {
            let range = document.createRange();
            range.selectNodeContents(box);
            let sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
            document.execCommand('copy');
            alert('📋 کانفیگ استراتژی تستر کپی شد!');
        }
    }
}
