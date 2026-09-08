window.currentTesterReportKey = window.currentTesterReportKey || '';
window.currentTesterFilter = window.currentTesterFilter || 'all';
window.currentTesterSearch = window.currentTesterSearch || '';
window.currentTesterScenarioKey = window.currentTesterScenarioKey || 'equity_active';

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
    let sym = window.currentActiveSymbol || 'EURUSD';
    let cleanSym = sym.replace(/[^a-zA-Z0-9]/g, '');
    let sData = (window.ALL_SYMBOLS_DATA && (window.ALL_SYMBOLS_DATA[sym] || window.ALL_SYMBOLS_DATA[cleanSym] || window.ALL_SYMBOLS_DATA[window.currentActiveSymbol])) || {};
    let spList = sData.smart_presets || (typeof smartPresets !== 'undefined' ? smartPresets : []);
    let allKings = sData.kings_sim_list || [];
    if (!allKings.length && typeof kingsSimList !== 'undefined' && kingsSimList && kingsSimList.length) {
        allKings = kingsSimList;
    }
    if (!allKings.length && window.ALL_SYMBOLS_DATA) {
        for (let k in window.ALL_SYMBOLS_DATA) {
            if (window.ALL_SYMBOLS_DATA[k] && window.ALL_SYMBOLS_DATA[k].kings_sim_list && window.ALL_SYMBOLS_DATA[k].kings_sim_list.length) {
                allKings = window.ALL_SYMBOLS_DATA[k].kings_sim_list;
                break;
            }
        }
    }

    function formatHours(hArr, hName, hStr) {
        let boolArr = null;
        if (Array.isArray(hArr)) {
            if (hArr.length === 24 && typeof hArr[0] === 'boolean') {
                boolArr = hArr;
            } else {
                boolArr = new Array(24).fill(false);
                hArr.forEach(h => {
                    let n = parseInt(h);
                    if (!isNaN(n) && n >= 0 && n < 24) boolArr[n] = true;
                });
            }
        } else if (typeof hStr === 'string' && hStr.trim()) {
            boolArr = new Array(24).fill(false);
            hStr.split(/[,;\s]+/).forEach(h => {
                let n = parseInt(h);
                if (!isNaN(n) && n >= 0 && n < 24) boolArr[n] = true;
            });
        } else if (typeof hArr === 'string' && hArr.trim()) {
            boolArr = new Array(24).fill(false);
            hArr.split(/[,;\s]+/).forEach(h => {
                let n = parseInt(h);
                if (!isNaN(n) && n >= 0 && n < 24) boolArr[n] = true;
            });
        }

        if (!boolArr) {
            return hName || '۲۴ ساعته (بدون محدودیت)';
        }

        let trueCount = boolArr.filter(Boolean).length;
        if (trueCount === 24) return '۲۴ ساعته کامل (00 الی 23)';
        if (trueCount === 0) return 'هیچ ساعتی فعال نیست';

        let ranges = [];
        let cur = [];
        for (let i = 0; i < 24; i++) {
            if (boolArr[i]) {
                cur.push(i);
            } else if (cur.length) {
                let s = (cur[0] < 10 ? '0' + cur[0] : cur[0]) + ':00';
                let e = (cur[cur.length - 1] < 10 ? '0' + cur[cur.length - 1] : cur[cur.length - 1]) + ':00';
                ranges.push(s === e ? s : `${s} الی ${e}`);
                cur = [];
            }
        }
        if (cur.length) {
            let s = (cur[0] < 10 ? '0' + cur[0] : cur[0]) + ':00';
            let e = (cur[cur.length - 1] < 10 ? '0' + cur[cur.length - 1] : cur[cur.length - 1]) + ':00';
            ranges.push(s === e ? s : `${s} الی ${e}`);
        }

        let rangeStr = ranges.join(' و ');
        let prefix = (hName && !hName.includes('سفارشی') && !hName.includes('custom') && !hName.includes('۲۴')) ? (hName + ' - ') : '';
        return `${prefix}${rangeStr} (${trueCount} ساعت)`;
    }

    function formatDisabledKings(kList, cp) {
        if (cp && cp.disabled_kings_str && cp.disabled_kings_str.trim()) {
            return cp.disabled_kings_str.trim();
        }
        if (cp && Array.isArray(cp.disabled_kings) && cp.disabled_kings.length) {
            return cp.disabled_kings.map(k => (typeof k === 'string' ? k.replace(/\|(M\d+)/, ' [$1]') : '')).join(', ');
        }

        let activeList = kList || (cp && cp.kings);
        if (activeList && Array.isArray(activeList)) {
            if (allKings.length > 0) {
                let activeSet = new Set(activeList.map(k => (typeof k === 'string' ? k : (k.kk || ''))));
                let disabled = [];
                for (let k of allKings) {
                    let kk = typeof k === 'string' ? k : (k.kk || '');
                    if (kk && !activeSet.has(kk)) {
                        disabled.push(kk.replace(/\|(M\d+)/, ' [$1]'));
                    }
                }
                if (disabled.length > 0) {
                    return disabled.join(', ');
                } else {
                    return 'بدون مسدودی (تمام ' + allKings.length + ' سلطان فعال)';
                }
            } else {
                return 'فعال: ' + activeList.length + ' سلطان (' + activeList.map(k => (typeof k === 'string' ? k.replace(/\|(M\d+)/, ' [$1]') : '')).join(', ') + ')';
            }
        }

        return 'بدون مسدودی (تمام سلاطین فعال)';
    }

    function formatAllowedKings(activeList) {
        if (activeList && activeList.length > 0) {
            return activeList.map(k => (typeof k === 'string' ? k.replace(/\|(M\d+)/, ' [$1]') : '')).join(', ');
        }
        return 'تمام سلاطین مجاز';
    }

    let pChamp = spList.find(p => p.idx === 0 || (p.title && (p.title.includes('الماس') || p.title.includes('Champion'))));
    let pGolden = spList.find(p => p.idx === 1 || (p.title && (p.title.includes('طلا') || p.title.includes('Golden'))));
    let pDay = spList.find(p => p.idx === 2 || (p.title && (p.title.includes('روز') || p.title.includes('Day'))));
    let pShield = spList.find(p => p.idx === 3 || (p.title && (p.title.includes('سپر') || p.title.includes('Shield'))));
    let pBase = spList.find(p => p.idx === 4 || (p.title && (p.title.includes('پایه') || p.title.includes('جامع') || p.title.includes('Base'))));

    let curActivePreset = window.currentActivePreset;
    let curActiveTitle = window.currentActivePresetTitle || (curActivePreset ? (curActivePreset.title || curActivePreset.name) : 'تنظیمات جاری نمودار رشد');

    let isRawEquity = (window.currentActivePresetIdx === -1)
        || !window.currentActivePreset
        || (curActiveTitle && (curActiveTitle.includes('خام') || curActiveTitle.includes('کل معاملات') || curActiveTitle.includes('بدون فیلتر')))
        || (window.simState && window.simState.mode === 'all');

    let curHours = isRawEquity ? new Array(24).fill(true) : ((window.simState && window.simState.allowedHours) || (curActivePreset && curActivePreset.hours) || new Array(24).fill(true));
    let curKings = isRawEquity ? [] : ((window.simState && window.simState.enabledKings) ? Array.from(window.simState.enabledKings) : ((curActivePreset && curActivePreset.kings) ? curActivePreset.kings : []));
    let curMinPot = isRawEquity ? 0.0 : ((window.simState && window.simState.minProfit !== undefined) ? window.simState.minProfit : ((curActivePreset && curActivePreset.min_pot) ? curActivePreset.min_pot : 0.0));
    let curWr = (window.currentActiveSimStats && window.currentActiveSimStats.wr) ? window.currentActiveSimStats.wr : ((curActivePreset && curActivePreset.wr) ? curActivePreset.wr : 66.7);
    let curPf = (window.currentActiveSimStats && window.currentActiveSimStats.pf) ? window.currentActiveSimStats.pf : ((curActivePreset && curActivePreset.pf) ? curActivePreset.pf : 3.94);
    let curNet = (window.currentActiveSimStats && window.currentActiveSimStats.net !== undefined) ? ((window.currentActiveSimStats.net >= 0 ? '+$' : '-$') + Math.abs(window.currentActiveSimStats.net).toFixed(2)) : ((curActivePreset && curActivePreset.net) ? ((curActivePreset.net >= 0 ? '+$' : '-$') + Math.abs(curActivePreset.net).toFixed(2)) : '+180.9 pips');

    let curTfM1 = isRawEquity ? 'فعال (True) - شامل تمام معاملات M1' : ((curActivePreset && curActivePreset.tfM1 !== undefined) ? (curActivePreset.tfM1 ? 'فعال (True)' : 'غیرفعال (False)') : 'غیرفعال (False) - بدون معامله در M1');

    let list = [
        {
            id: 'equity_active',
            name: '📈 سناریوی انتخابی نمودار اکوئیتی (' + curActiveTitle + ')',
            title: curActiveTitle,
            rawTitle: curActiveTitle,
            badge: isRawEquity ? 'تست خام' : 'نمودار رشد',
            isRaw: isRawEquity,
            isBaseScenario: isRawEquity,
            minPot: isRawEquity ? 0.0 : curMinPot,
            minPotDisplay: isRawEquity ? '$0.00 (بدون فیلتر)' : ('$' + curMinPot.toFixed(2) + (curMinPot > 0 ? '+' : ' (بدون محدودیت)')),
            tfM1: curTfM1,
            hoursDisplay: isRawEquity ? '۲۴ ساعته کامل (00 الی 23)' : formatHours(curHours, (curActivePreset ? curActivePreset.hours_name : '')),
            hours: curHours,
            allowedKings: isRawEquity ? 'تمام معاملات چارت (خام بدون فیلتر)' : formatAllowedKings(curKings),
            disabledKings: isRawEquity ? 'بدون مسدودی (همه معاملات مجاز)' : formatDisabledKings(curKings, curActivePreset),
            kings: curKings,
            beBuffer: (curActivePreset && curActivePreset.be_buffer !== undefined) ? (curActivePreset.be_buffer + ' pips') : '0.0 pips',
            maxDev: (curActivePreset && curActivePreset.max_dev !== undefined) ? (curActivePreset.max_dev + ' pips') : '2.5 pips',
            enableHTFDominance: (window.simState && window.simState.enableHTFDominance) || false,
            maxConcurrentLimit: (window.simState && window.simState.maxConcurrentLimit) || 0,
            simWinRate: curWr,
            simPf: curPf,
            simNetR: curNet
        },
        {
            id: 'raw',
            name: '📊 نتیجه تست خام (کل معاملات چارت - بدون هیچ فیلتری)',
            title: 'نتیجه تست خام (کل معاملات چارت)',
            rawTitle: 'نتیجه تست خام (کل معاملات چارت)',
            badge: 'خام چارت',
            minPot: 0.0,
            minPotDisplay: '$0.00 (بدون فیلتر)',
            tfM1: 'فعال (True) - تمام تایم‌ها',
            hoursDisplay: '۲۴ ساعته کامل (00 الی 23)',
            hours: new Array(24).fill(true),
            allowedKings: 'تمام معاملات چارت (بدون فیلتر)',
            disabledKings: 'بدون مسدودی (تمام معاملات مجاز)',
            kings: [],
            beBuffer: '0.0 pips',
            maxDev: '0.0 (نامحدود)',
            isRaw: true,
            isBaseScenario: true,
            simWinRate: sData.raw_wr || 52.0,
            simPf: sData.raw_pf || 1.35,
            simNetR: sData.raw_net || '+45.0R'
        },
        {
            id: 'auto',
            name: '🔍 تشخیص خودکار سناریو از فایل تستر (Auto Detect)',
            badge: 'هوشمند',
            minPot: pChamp ? pChamp.min_pot : 0.0,
            minPotDisplay: pChamp ? ('$' + pChamp.min_pot.toFixed(2) + ' (خودکار)') : '$0.00 (خودکار)',
            tfM1: 'هوشمند (طبق تستر)',
            hoursDisplay: 'هوشمند / طبق تستر',
            allowedKings: 'بررسی هوشمند',
            disabledKings: 'بررسی هوشمند',
            beBuffer: '0.0 pips',
            maxDev: '2.5 pips',
            simWinRate: pChamp ? pChamp.wr : 63.5,
            simPf: pChamp ? pChamp.pf : 2.20,
            simNetR: pChamp ? ((pChamp.net >= 0 ? '+$' : '-$') + Math.abs(pChamp.net).toFixed(2)) : '+124.5R'
        },
        {
            id: 'golden',
            name: '⚖️ تعادل طلایی حجم و سود (Golden Balance)',
            badge: 'بالانس بهینه',
            minPot: pGolden ? pGolden.min_pot : 0.0,
            minPotDisplay: pGolden ? ('$' + pGolden.min_pot.toFixed(2) + '+') : '$0.00 (بدون محدودیت)',
            tfM1: 'غیرفعال (False) - بدون معامله در M1',
            hoursDisplay: pGolden ? formatHours(pGolden.hours, pGolden.hours_name) : '۲۴ ساعته (00 تا 23)',
            hours: (pGolden && pGolden.hours) ? pGolden.hours : new Array(24).fill(true),
            allowedKings: pGolden ? formatAllowedKings(pGolden.kings) : 'تمام سلاطین',
            disabledKings: pGolden ? formatDisabledKings(pGolden.kings) : 'بدون مسدودی',
            beBuffer: '0.0 pips',
            maxDev: '2.5 pips',
            simWinRate: pGolden ? pGolden.wr : 58.5,
            simPf: pGolden ? pGolden.pf : 1.85,
            simNetR: pGolden ? ((pGolden.net >= 0 ? '+$' : '-$') + Math.abs(pGolden.net).toFixed(2)) : '+98.4R'
        },
        {
            id: 'champion',
            name: '🎯 الماس و سوپر اسنایپر خودکار (Champion Sniper)',
            badge: 'بیشترین سود',
            minPot: pChamp ? pChamp.min_pot : 2.0,
            minPotDisplay: pChamp ? ('$' + pChamp.min_pot.toFixed(2) + '+') : '$2.00+',
            tfM1: 'غیرفعال (False) - بدون معامله در M1',
            hoursDisplay: pChamp ? formatHours(pChamp.hours, pChamp.hours_name) : 'حذف شب (۰۴ الی ۲۲)',
            hours: (pChamp && pChamp.hours) ? pChamp.hours : Array.from({length:24}, (_, i) => (i >= 4 && i < 22)),
            allowedKings: pChamp ? formatAllowedKings(pChamp.kings) : 'سلاطین منتخب',
            disabledKings: pChamp ? formatDisabledKings(pChamp.kings) : 'OInner-BE (M1), RS-BE (M1)',
            beBuffer: '0.0 pips',
            maxDev: '2.0 pips',
            simWinRate: pChamp ? pChamp.wr : 66.2,
            simPf: pChamp ? pChamp.pf : 2.45,
            simNetR: pChamp ? ((pChamp.net >= 0 ? '+$' : '-$') + Math.abs(pChamp.net).toFixed(2)) : '+142.1R'
        },
        {
            id: 'day',
            name: '☀️ اسنایپر سشن روزانه لندن و نیویورک (Day Session)',
            badge: 'اوج نقدینگی',
            minPot: pDay ? pDay.min_pot : 1.5,
            minPotDisplay: pDay ? ('$' + pDay.min_pot.toFixed(2) + '+') : '$1.50+',
            tfM1: 'غیرفعال (False) - بدون معامله در M1',
            hoursDisplay: pDay ? formatHours(pDay.hours, pDay.hours_name) : 'سشن لندن و نیویورک (۰۷ الی ۲۰)',
            hours: (pDay && pDay.hours) ? pDay.hours : Array.from({length:24}, (_, i) => (i >= 7 && i <= 20)),
            allowedKings: pDay ? formatAllowedKings(pDay.kings) : 'سلاطین منتخب',
            disabledKings: pDay ? formatDisabledKings(pDay.kings) : 'بدون مسدودی',
            beBuffer: '0.0 pips',
            maxDev: '2.5 pips',
            simWinRate: pDay ? pDay.wr : 64.0,
            simPf: pDay ? pDay.pf : 2.10,
            simNetR: pDay ? ((pDay.net >= 0 ? '+$' : '-$') + Math.abs(pDay.net).toFixed(2)) : '+118.0R'
        },
        {
            id: 'shield',
            name: '🛡️ سپر کمترین افت سرمایه (Stop Loss Shield)',
            badge: 'کمترین دروداون',
            minPot: pShield ? pShield.min_pot : 1.0,
            minPotDisplay: pShield ? ('$' + pShield.min_pot.toFixed(2) + '+') : '$1.00+',
            tfM1: 'غیرفعال (False) - بدون معامله در M1',
            hoursDisplay: pShield ? formatHours(pShield.hours, pShield.hours_name) : '۲۴ ساعته (وقفه بعد ۲ استاپ)',
            hours: (pShield && pShield.hours) ? pShield.hours : new Array(24).fill(true),
            allowedKings: pShield ? formatAllowedKings(pShield.kings) : 'سلاطین کم‌ریسک',
            disabledKings: pShield ? formatDisabledKings(pShield.kings) : 'حذف ۳ سلطان پرریسک',
            beBuffer: '0.0 pips',
            maxDev: '2.0 pips',
            simWinRate: pShield ? pShield.wr : 67.5,
            simPf: pShield ? pShield.pf : 2.30,
            simNetR: pShield ? ((pShield.net >= 0 ? '+$' : '-$') + Math.abs(pShield.net).toFixed(2)) : '+105.2R'
        },
        {
            id: 'base',
            name: '🌐 سبد جامع پایه (تمام سلاطین ۲۴ ساعته)',
            badge: 'جامع پایه',
            minPot: 0.0,
            minPotDisplay: '$0.00',
            tfM1: 'فعال (True) - تمام تایم‌ها',
            hoursDisplay: '۲۴ ساعته کامل',
            hours: new Array(24).fill(true),
            allowedKings: 'تمام سلاطین مجاز',
            disabledKings: 'بدون مسدودی',
            beBuffer: '1.0 pips',
            maxDev: '0.0 (نامحدود)',
            simWinRate: pBase ? pBase.wr : 52.0,
            simPf: pBase ? pBase.pf : 1.45,
            simNetR: pBase ? ((pBase.net >= 0 ? '+$' : '-$') + Math.abs(pBase.net).toFixed(2)) : '+65.0R'
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
            hours: ai.hours || null,
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
            let hDisp = formatHours(cp.hours, cp.hours_name, cp.hours_str);
            let dKings = formatDisabledKings(cp.kings, cp);
            let potVal = (cp.min_pot !== undefined && !isNaN(Number(cp.min_pot))) ? Number(cp.min_pot) : 0.0;
            
            // Build raw hours array for matching
            let hArr = null;
            if (Array.isArray(cp.hours) && cp.hours.length === 24 && typeof cp.hours[0] === 'boolean') {
                hArr = cp.hours;
            } else if (Array.isArray(cp.hours)) {
                hArr = new Array(24).fill(false);
                cp.hours.forEach(h => { let n = parseInt(h); if (!isNaN(n) && n >= 0 && n < 24) hArr[n] = true; });
            } else if (typeof cp.hours_str === 'string' && cp.hours_str.trim()) {
                hArr = new Array(24).fill(false);
                cp.hours_str.split(/[,;\s]+/).forEach(h => { let n = parseInt(h); if (!isNaN(n) && n >= 0 && n < 24) hArr[n] = true; });
            } else if (typeof cp.hours === 'string' && cp.hours.trim()) {
                hArr = new Array(24).fill(false);
                cp.hours.split(/[,;\s]+/).forEach(h => { let n = parseInt(h); if (!isNaN(n) && n >= 0 && n < 24) hArr[n] = true; });
            } else if (hDisp) {
                let rm = hDisp.match(/(\d{1,2}):?00?\s*(?:الی|-|تا)\s*(\d{1,2}):?00?/);
                if (rm) {
                    hArr = new Array(24).fill(false);
                    let s = parseInt(rm[1]), e = parseInt(rm[2]);
                    for (let i = s; i <= e; i++) hArr[i] = true;
                }
            }

            let rawTitle = cp.title || cp.name || ('سفارشی ' + (idx + 1));
            list.push({
                id: 'custom_' + (cp.id || idx),
                title: rawTitle,
                rawTitle: rawTitle,
                name: '⭐ سناریوی شخصی: ' + rawTitle,
                badge: 'دست‌ساز کاربر',
                minPot: potVal,
                minPotDisplay: '$' + potVal.toFixed(2),
                tfM1: 'غیرفعال (False) - بدون معامله در M1',
                hoursDisplay: hDisp,
                hours: hArr,
                hours_str: cp.hours_str || (hArr ? hArr.map((v, i) => v ? (i < 10 ? '0' + i : '' + i) : null).filter(Boolean).join(',') : ''),
                disabledKings: dKings,
                kings: cp.kings || [],
                beBuffer: (cp.be_buffer !== undefined ? cp.be_buffer + ' pips' : '0.0 pips'),
                maxDev: (cp.max_dev !== undefined ? cp.max_dev + ' pips' : '2.0 pips'),
                simWinRate: cp.wr || 65.0,
                simPf: cp.pf || 2.2,
                simNetR: (cp.net ? ((cp.net >= 0 ? '+$' : '-$') + Math.abs(cp.net).toFixed(2)) : '+100.0R')
            });
        });
    } catch(e) {}

    return list;
}

function resolveActiveScenario(scenarioKey, report) {
    let scenarios = getAvailableTesterScenarios();
    if (!scenarioKey || scenarioKey === 'auto') {
        let p = (report && report.parameters) || {};
        let scName = (p.InpScenarioName || '').trim().toLowerCase();
        let cleanScName = scName.replace(/[^a-zA-Z0-9_\s\-]/g, ' ').replace(/\s+/g, ' ').trim();
        
        // 1. Direct search against all available scenarios (standard + custom)
        if (cleanScName && cleanScName !== 'default') {
            for (let s of scenarios) {
                if (s.id === 'auto') continue;
                let sTitle = ((s.title || s.rawTitle || s.name || '')).replace(/⭐\s*سناریوی شخصی:\s*/g, '').toLowerCase();
                let cleanSTitle = sTitle.replace(/[^a-zA-Z0-9_\s\-]/g, ' ').replace(/\s+/g, ' ').trim();
                
                if (cleanSTitle && (cleanSTitle === cleanScName || cleanSTitle.includes(cleanScName) || cleanScName.includes(cleanSTitle))) {
                    return s;
                }
                if (s.id && cleanScName.includes(s.id.toLowerCase())) {
                    return s;
                }
            }

            // 2. Token overlap fallback
            let scTokens = cleanScName.split(/\s+/).filter(w => w.length >= 2);
            for (let s of scenarios) {
                if (s.id === 'auto') continue;
                let sTitle = ((s.title || s.rawTitle || s.name || '')).toLowerCase();
                let sTokens = sTitle.replace(/[^a-zA-Z0-9_\s\-]/g, ' ').split(/\s+/).filter(w => w.length >= 2);
                let matched = scTokens.filter(t => sTokens.includes(t));
                if (matched.length >= 2 || (scTokens.length === 1 && matched.length === 1)) {
                    return s;
                }
            }
        }

        let hours = (p.InpAllowedTradingHours || '');
        let pot = Number(p.InpMinTradePotential || 0);

        if (scName.includes('champion') || scName.includes('diamond') || pot >= 2.0) {
            let customChamp = scenarios.find(s => s.id.startsWith('custom_') && (s.name.toLowerCase().includes('champion') || (s.title && s.title.toLowerCase().includes('champion'))));
            if (customChamp) return customChamp;
            return scenarios.find(s => s.id === 'champion') || scenarios[1];
        }
        if (scName.includes('day') || scName.includes('london') || (hours.includes('08') && hours.includes('14'))) {
            return scenarios.find(s => s.id === 'day') || scenarios[1];
        }
        if (scName.includes('shield') || scName.includes('stop')) {
            return scenarios.find(s => s.id === 'shield') || scenarios[1];
        }
        if (scName.includes('base') || scName.includes('all') || scName.includes('default') || scName.includes('raw') || scName.includes('خام') || p.InpEnableKingsM1 === true) {
            return scenarios.find(s => s.id === 'raw') || scenarios.find(s => s.id === 'base') || scenarios[0];
        }
        return scenarios.find(s => s.id === 'golden') || scenarios[1];
    }
    return scenarios.find(s => s.id === scenarioKey) || scenarios[0];
}

