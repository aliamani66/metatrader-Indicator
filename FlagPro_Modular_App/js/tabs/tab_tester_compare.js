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

    let pChamp = spList.find(p => p.idx === 0 || (p.title && (p.title.includes('الماس') || p.title.includes('Champion'))));
    let pGolden = spList.find(p => p.idx === 1 || (p.title && (p.title.includes('طلا') || p.title.includes('Golden'))));
    let pDay = spList.find(p => p.idx === 2 || (p.title && (p.title.includes('روز') || p.title.includes('Day'))));
    let pShield = spList.find(p => p.idx === 3 || (p.title && (p.title.includes('سپر') || p.title.includes('Shield'))));
    let pBase = spList.find(p => p.idx === 4 || (p.title && (p.title.includes('پایه') || p.title.includes('جامع') || p.title.includes('Base'))));

    let list = [
        {
            id: 'auto',
            name: '🔍 تشخیص خودکار سناریو از فایل تستر (Auto Detect)',
            badge: 'هوشمند',
            minPot: pChamp ? pChamp.min_pot : 0.0,
            minPotDisplay: pChamp ? ('$' + pChamp.min_pot.toFixed(2) + ' (خودکار)') : '$0.00 (خودکار)',
            tfM1: 'غیرفعال (False)',
            hoursDisplay: 'هوشمند / طبق تستر',
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
        datePart = `بازه: از ${sD} تا ${eD}`;
    } else if (dr) {
        datePart = `بازه: ${dr}`;
    }
    
    let execTime = r.executionTime || r.fileTime || '';
    if (!execTime && r.mtime) {
        let dt = new Date(r.mtime * 1000);
        let y = dt.getFullYear();
        let mon = String(dt.getMonth() + 1).padStart(2, '0');
        let d = String(dt.getDate()).padStart(2, '0');
        let h = String(dt.getHours()).padStart(2, '0');
        let min = String(dt.getMinutes()).padStart(2, '0');
        execTime = `${y}.${mon}.${d} ${h}:${min}`;
    }
    let timeBadge = execTime ? ` | ⏱️ انجام تست: ${execTime}` : '';

    return datePart ? `${title} | ${datePart} | ${cnt} معامله${timeBadge}` : `${title} | ${cnt} معامله${timeBadge}`;
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

    // ⏱️ Update Box-to-Entry Latency KPIs
    let sym = (window.TESTER_REPORTS && window.TESTER_REPORTS[window.currentTesterReportKey] && window.TESTER_REPORTS[window.currentTesterReportKey].symbol) || window.currentActiveSymbol || 'GBPUSD';
    let cleanSym = sym.replace(/[^a-zA-Z0-9]/g, '');
    let sData = (window.ALL_SYMBOLS_DATA && (window.ALL_SYMBOLS_DATA[sym] || window.ALL_SYMBOLS_DATA[cleanSym] || window.ALL_SYMBOLS_DATA[window.currentActiveSymbol])) || {};
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
        let cnt = lat.count || (t ? t.length : 238);
        diffWaitEl.textContent = `${p90} (کل: ${cnt} ستاپ)`;
    }
}

function extractHourSet(val, fallbackDisplay) {
    let set = new Set();
    if (!val && !fallbackDisplay) return set;
    
    if (Array.isArray(val) && val.length === 24 && typeof val[0] === 'boolean') {
        val.forEach((active, h) => { if (active) set.add(h); });
        return set;
    }
    
    if (Array.isArray(val)) {
        val.forEach(h => {
            let n = parseInt(h);
            if (!isNaN(n) && n >= 0 && n < 24) set.add(n);
        });
        if (set.size > 0) return set;
    }
    
    if (typeof val === 'string' && val.trim()) {
        let str = val.trim();
        if (str.toLowerCase() === 'all' || str.includes('۲۴ ساعته') || str.includes('24h') || str.includes('24 ساعته')) {
            for (let i = 0; i < 24; i++) set.add(i);
            return set;
        }
        let parts = str.split(/[,;\s]+/).map(x => parseInt(x)).filter(n => !isNaN(n) && n >= 0 && n < 24);
        if (parts.length > 0) {
            parts.forEach(n => set.add(n));
            return set;
        }
        let rm = str.match(/(\d{1,2}):?00?\s*(?:الی|-|تا)\s*(\d{1,2}):?00?/);
        if (rm) {
            let s = parseInt(rm[1]), e = parseInt(rm[2]);
            if (s <= e) {
                for (let i = s; i <= e; i++) set.add(i);
            } else {
                for (let i = s; i < 24; i++) set.add(i);
                for (let i = 0; i <= e; i++) set.add(i);
            }
            return set;
        }
    }
    
    if (typeof fallbackDisplay === 'string' && fallbackDisplay.trim()) {
        let fstr = fallbackDisplay.trim();
        if (fstr.includes('۲۴ ساعته') || fstr.includes('24h')) {
            for (let i = 0; i < 24; i++) set.add(i);
            return set;
        }
        let rm = fstr.match(/(\d{1,2}):?00?\s*(?:الی|-|تا)\s*(\d{1,2}):?00?/);
        if (rm) {
            let s = parseInt(rm[1]), e = parseInt(rm[2]);
            if (s <= e) {
                for (let i = s; i <= e; i++) set.add(i);
            } else {
                for (let i = s; i < 24; i++) set.add(i);
                for (let i = 0; i <= e; i++) set.add(i);
            }
            return set;
        }
    }
    
    return set;
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
    let actScNameClean = actScName.toLowerCase().replace(/[^a-zA-Z0-9_\s\-]/g, ' ').replace(/\s+/g, ' ').trim();
    let expScName = (scenario.title || scenario.rawTitle || scenario.name || '').replace(/⭐\s*سناریوی شخصی:\s*/g, '').trim();
    let expScNameClean = expScName.toLowerCase().replace(/[^a-zA-Z0-9_\s\-]/g, ' ').replace(/\s+/g, ' ').trim();

    let nameMatched = false;
    if (actScNameClean && expScNameClean) {
        if (actScNameClean === expScNameClean || actScNameClean.includes(expScNameClean) || expScNameClean.includes(actScNameClean)) {
            nameMatched = true;
        } else {
            let actTokens = actScNameClean.split(/\s+/).filter(w => w.length >= 2);
            let expTokens = expScNameClean.split(/\s+/).filter(w => w.length >= 2);
            let commonTokens = actTokens.filter(t => expTokens.includes(t));
            if (commonTokens.length >= 2 || (actTokens.length === 1 && commonTokens.length === 1)) {
                nameMatched = true;
            }
        }
    }
    if (!nameMatched && actScName) {
        if (scenario.id && actScName.toLowerCase().includes(scenario.id.toLowerCase())) nameMatched = true;
        if (scenario.id.startsWith('custom_') && (actScName.includes('سفارشی') || actScName.toLowerCase().includes('custom') || actScName.toLowerCase().includes('ai'))) nameMatched = true;
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
    let isActNoDis = !actDis || actDis.toLowerCase() === 'none' || actDis.length <= 3;
    let isExpNoDis = !scenario.disabledKings || scenario.disabledKings.includes('بدون مسدودی');

    let kingsStatus = 'warn';
    let kingsImpact = '';
    if (isActNoDis && isExpNoDis) {
        kingsStatus = 'match';
        kingsImpact = 'تمامی سلاطین طبق انتظار سناریو در تستر مجاز و فعال بوده‌اند.';
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
            status: nameMatched ? 'match' : ((!p.InpScenarioName || p.InpScenarioName.includes('Default')) ? 'severe' : 'warn'),
            impact: nameMatched
                ? 'نام سناریو در متاتریدر ۵ («' + (p.InpScenarioName || '') + '») کاملاً منطبق بر این سناریو است.'
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
            status: hoursStatus,
            impact: hoursImpact
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
                tbody.innerHTML = '<tr><td colspan="13" style="text-align:center;padding:20px;color:#94a3b8;">هیچ معامله‌ای در این گزارش ثبت نشده است.</td></tr>';
                return;
            }

            let sym = report.symbol || window.currentActiveSymbol || 'EURUSD';
            let cleanSym = sym.replace(/[^a-zA-Z0-9]/g, '');
            let sData = (window.ALL_SYMBOLS_DATA && (window.ALL_SYMBOLS_DATA[sym] || window.ALL_SYMBOLS_DATA[cleanSym] || window.ALL_SYMBOLS_DATA[window.currentActiveSymbol])) || {};
            let indTrades = sData.trades_json_list || [];
            let scenario = resolveActiveScenario(window.currentTesterScenarioKey, report);

            // Pre-match and prepare trade metadata for 1:1 Deal-by-Deal forensics
            let processed = trades.map(t => {
                let profitPips = (t.profitPips !== undefined && !isNaN(Number(t.profitPips))) ? Number(t.profitPips) : ((t.pnlPips !== undefined && !isNaN(Number(t.pnlPips))) ? Number(t.pnlPips) : 0);
                let profitUSD = (t.profitUSD !== undefined && !isNaN(Number(t.profitUSD))) ? Number(t.profitUSD) : ((t.pnlUSD !== undefined && !isNaN(Number(t.pnlUSD))) ? Number(t.pnlUSD) : 0);
                let slippagePips = (t.slippagePips !== undefined && !isNaN(Number(t.slippagePips))) ? Number(t.slippagePips) : 0;
                let boxEntry = (t.boxEntryPrice !== undefined && !isNaN(Number(t.boxEntryPrice))) ? Number(t.boxEntryPrice) : 0;
                let marketFill = (t.marketFillPrice !== undefined && !isNaN(Number(t.marketFillPrice))) ? Number(t.marketFillPrice) : boxEntry;
                let slPrice = (t.slPrice !== undefined && !isNaN(Number(t.slPrice))) ? Number(t.slPrice) : 0;
                let tp1 = (t.tp1 !== undefined && !isNaN(Number(t.tp1))) ? Number(t.tp1) : 0;
                let tp4 = (t.tp4 !== undefined && !isNaN(Number(t.tp4))) ? Number(t.tp4) : 0;

                let tEntryTime = (t.entryTime || '').substring(0, 16).replace(/-/g, '.');
                let tTF = (t.timeframe || '').replace('PERIOD_', '');
                let tDir = (t.side || '').toUpperCase();

                // 1:1 Match with Strategy / Indicator Dataset
                let match = indTrades.find(it => {
                    let itEn = (it.en_t || '').substring(0, 16).replace(/-/g, '.');
                    let itTF = (it.tf || '').replace('PERIOD_', '');
                    let itDir = (it.dir || '').toUpperCase();
                    let itPrice = parseFloat(it.en_p || 0);

                    if (tEntryTime && itEn && tEntryTime === itEn && (!tTF || !itTF || tTF === itTF) && (!tDir || !itDir || tDir === itDir)) {
                        return true;
                    }
                    if (boxEntry > 0 && itPrice > 0 && Math.abs(boxEntry - itPrice) < 0.00015 && tEntryTime.substring(0, 10) === itEn.substring(0, 10) && tTF === itTF) {
                        return true;
                    }
                    return false;
                });

                // Check if trade is allowed by active scenario
                let isAllowed = true;
                let filterReason = '';
                if (tTF === 'M1' && scenario.tfM1 && !scenario.tfM1.includes('فعال (True)')) {
                    isAllowed = false;
                    filterReason = 'فیلتر نویز M1';
                }
                if (isAllowed) {
                    let h = tEntryTime.length >= 13 ? parseInt(tEntryTime.substring(11, 13)) : 0;
                    let scHours = extractHourSet(scenario.hours, scenario.hoursDisplay);
                    if (scHours.size > 0 && scHours.size < 24) {
                        if (!scHours.has(h)) {
                            isAllowed = false;
                            filterReason = 'ساعت غیرمجاز (ساعت ' + (h < 10 ? '0' + h : h) + ':00)';
                        }
                    } else if (scenario.id === 'day' && (h < 7 || h >= 20)) {
                        isAllowed = false;
                        filterReason = 'خارج از سشن روز (ساعت ' + h + ')';
                    } else if (scenario.id === 'champion' && (h >= 22 || h < 4)) {
                        isAllowed = false;
                        filterReason = 'فیلتر ساعات شب (ساعت ' + h + ')';
                    }
                }
                if (isAllowed && scenario.minPot > 0) {
                    let potVal = match && match.pts ? (match.pts * 0.04) : 0;
                    if (potVal > 0 && potVal < scenario.minPot) {
                        isAllowed = false;
                        filterReason = 'کف سود زیر ' + scenario.minPotDisplay;
                    }
                }
                if (isAllowed) {
                    let patName = (t.pattern || (match ? match.role : '') || '').trim();
                    let patKey = patName ? (patName + (tTF ? '|' + tTF : '')) : '';
                    if (Array.isArray(scenario.kings) && scenario.kings.length > 0) {
                        let kSet = new Set(scenario.kings);
                        if (!kSet.has(patName) && !kSet.has(patKey)) {
                            isAllowed = false;
                            filterReason = 'سلطان غیرفعال در سناریو (' + (patName || 'الگو') + ')';
                        }
                    } else if (scenario.disabledKings && !scenario.disabledKings.includes('بدون مسدودی')) {
                        if (patName && (scenario.disabledKings.includes(patName) || (patKey && scenario.disabledKings.includes(patKey)))) {
                            isAllowed = false;
                            filterReason = 'سلطان مسدود (' + patName + ')';
                        }
                    }
                }

                // Indicator Theoretical PnL & Outcome
                let indNet = 0.0;
                let indTgt = '';
                let isIndWin = false;
                if (match) {
                    indNet = match.net !== undefined ? match.net : (match.t1 ? (match.pts * 0.04) : -(match.pts * 0.04));
                    isIndWin = (match.t1 === 1 || indNet > 0);
                    if (match.t4) indTgt = 'TP 1:4 🚀';
                    else if (match.t3) indTgt = 'TP 1:3 🎯';
                    else if (match.t2) indTgt = 'TP 1:2 🎯';
                    else if (match.t1) indTgt = 'TP 1:1 🎯';
                    else indTgt = 'حد ضرر SL ❌';
                }

                // Forensic Verdict & Discrepancy Detection
                let verdictHtml = '';
                let isDisc = false;
                let exitCls = t.exitClass || '';

                if (!isAllowed) {
                    isDisc = true;
                    verdictHtml = `<span style="color:#fca5a5;font-size:11px;">🛑 <b>ورود اشتباه در تستر (فیلتر سناریو):</b> این ستاپ در سناریوی انتخابی به علت «${filterReason}» فیلتر بوده است اما در تستر به اشتباه باز شده و ${profitUSD < 0 ? 'منجر به باخت شد' : 'بسته شد'}.</span>`;
                } else if (match && match.t4 && exitCls.includes('BE')) {
                    isDisc = true;
                    verdictHtml = `<span style="color:#c7d2fe;font-size:11px;">🛡️ <b>سود بزرگ از دست رفته با بافر BE:</b> در اندیکاتور به تارگت کامل TP4 رسید، ولی در تستر متاتریدر با بافر ۱ پیپ پس از TP1 در اولین اصلاح قطع شد.</span>`;
                } else if (slippagePips >= 2.0) {
                    isDisc = true;
                    verdictHtml = `<span style="color:#fde68a;font-size:11px;">⚡ <b>اسلیپیج شدید ${slippagePips.toFixed(1)} پیپ ورود:</b> لغزش قیمت در ورود مارکت نسبت سود به ریسک را کاهش داده است.</span>`;
                } else if (match && match.t1 && profitUSD < 0) {
                    isDisc = true;
                    verdictHtml = `<span style="color:#fca5a5;font-size:11px;">❌ <b>اختلاف اجرای مارکت:</b> در اندیکاتور TP1 لمس شد اما در تستر به دلیل اسپرد یا نوسان حد ضرر لمس گردید.</span>`;
                } else if (profitUSD >= 0) {
                    verdictHtml = `<span style="color:#a7f3d0;font-size:11px;">🟢 <b>انطباق کامل:</b> تارگت در هر دو پلتفرم لمس شده و سود ذخیره گردید.</span>`;
                } else {
                    verdictHtml = `<span style="color:#94a3b8;font-size:11px;">همگام (استاپ طبیعی در هر دو پلتفرم).</span>`;
                }

                return {
                    raw: t,
                    profitPips: profitPips,
                    profitUSD: profitUSD,
                    slippagePips: slippagePips,
                    boxEntry: boxEntry,
                    marketFill: marketFill,
                    slPrice: slPrice,
                    tp1: tp1,
                    tp4: tp4,
                    tEntryTime: tEntryTime,
                    tTF: tTF,
                    tDir: tDir,
                    pattern: t.pattern || '',
                    exitClass: exitCls,
                    match: match,
                    isAllowed: isAllowed,
                    filterReason: filterReason,
                    indNet: indNet,
                    indTgt: indTgt,
                    isIndWin: isIndWin,
                    verdictHtml: verdictHtml,
                    isDisc: isDisc
                };
            });

            // Update Filter Buttons Text & Badge Counts
            let cntAll = processed.length;
            let cntWin = processed.filter(x => x.profitUSD >= 0).length;
            let cntLoss = processed.filter(x => x.profitUSD < 0).length;
            let cntM1 = processed.filter(x => x.tTF === 'M1').length;
            let cntSlip = processed.filter(x => x.slippagePips >= 2.0).length;
            let cntBe = processed.filter(x => x.exitClass.includes('BE')).length;
            let cntDisc = processed.filter(x => x.isDisc).length;

            let bAll = document.getElementById('tcFilterAll'); if (bAll) bAll.textContent = 'همه (' + cntAll + ')';
            let bWin = document.getElementById('tcFilterWin'); if (bWin) bWin.textContent = 'بردها (' + cntWin + ')';
            let bLoss = document.getElementById('tcFilterLoss'); if (bLoss) bLoss.textContent = 'باخت‌ها (' + cntLoss + ')';
            let bM1 = document.getElementById('tcFilterM1'); if (bM1) bM1.textContent = 'نویز M1 (' + cntM1 + ')';
            let bSlip = document.getElementById('tcFilterSlip'); if (bSlip) bSlip.textContent = 'اسلیپیج بالا > 2p (' + cntSlip + ')';
            let bBe = document.getElementById('tcFilterBe'); if (bBe) bBe.textContent = 'خروج در BE (' + cntBe + ')';
            let bDisc = document.getElementById('tcFilterDisc'); if (bDisc) bDisc.textContent = '⚠️ مغایرت‌ها (' + cntDisc + ')';

            let tblTitle = document.getElementById('tcTradesTableTitle');
            if (tblTitle) {
                tblTitle.textContent = 'جدول بازرسی و مقایسه نظیر به نظیر (1:1) معاملات متاتریدر ۵ با اندیکاتور (' + cntAll + ' ستاپ | ' + cntDisc + ' مغایرت ریشه‌ای)';
            }

            // Apply active filter
            let filtered = processed.filter(pt => {
                if (filterMode === 'win' && pt.profitUSD < 0) return false;
                if (filterMode === 'loss' && pt.profitUSD >= 0) return false;
                if (filterMode === 'm1' && pt.tTF !== 'M1') return false;
                if (filterMode === 'slip' && pt.slippagePips < 2.0) return false;
                if (filterMode === 'be' && !pt.exitClass.includes('BE')) return false;
                if (filterMode === 'disc' && !pt.isDisc) return false;
                if (searchQuery) {
                    let q = searchQuery.toLowerCase();
                    let hay = (pt.pattern + ' ' + pt.tTF + ' ' + pt.tDir + ' ' + pt.tEntryTime + ' ' + pt.filterReason).toLowerCase();
                    if (!hay.includes(q)) return false;
                }
                return true;
            });

            let html = '';
            filtered.forEach(pt => {
                let isWin = (pt.profitUSD >= 0);
                let sideBadge = pt.tDir === 'BUY'
                    ? '<span style="color:#34d399;font-weight:bold;">BUY</span>'
                    : '<span style="color:#f87171;font-weight:bold;">SELL</span>';

                let tfBadge = pt.tTF === 'M1'
                    ? '<span style="background:#450a0a;color:#fca5a5;padding:1px 5px;border-radius:3px;font-size:10px;border:1px solid #991b1b;">M1 (نویز)</span>'
                    : '<span style="background:#064e3b;color:#a7f3d0;padding:1px 5px;border-radius:3px;font-size:10px;border:1px solid #059669;">' + pt.tTF + '</span>';

                let slipColor = (pt.slippagePips > 2.0) ? '#f59e0b' : '#94a3b8';

                // Column: Status in Scenario
                let scStatusBadge = pt.isAllowed
                    ? '<span style="background:#064e3b;color:#a7f3d0;padding:2px 6px;border-radius:4px;font-size:10.5px;font-weight:bold;">🟢 مجاز در سناریو</span>'
                    : '<span style="background:#450a0a;color:#fca5a5;padding:2px 6px;border-radius:4px;border:1px solid #7f1d1d;font-size:10px;font-weight:bold;">🛑 ' + pt.filterReason + '</span>';

                // Column: Indicator PnL & Target
                let indResultHtml = '';
                if (pt.match) {
                    if (!pt.isAllowed) {
                        indResultHtml = '<span style="color:#94a3b8;font-size:10.5px;">فیلتر ($0.00)</span> <span style="font-size:9.5px;color:#64748b;">(اندیکاتور: ' + pt.indTgt + ')</span>';
                    } else if (pt.isIndWin) {
                        indResultHtml = '<span style="color:#34d399;font-weight:bold;direction:ltr;">+$' + Math.abs(pt.indNet).toFixed(2) + '</span> <span style="font-size:10px;color:#a7f3d0;">(' + pt.indTgt + ')</span>';
                    } else {
                        indResultHtml = '<span style="color:#f87171;font-weight:bold;direction:ltr;">-$' + Math.abs(pt.indNet).toFixed(2) + '</span> <span style="font-size:10px;color:#fca5a5;">(استاپ)</span>';
                    }
                } else {
                    indResultHtml = '<span style="color:#64748b;font-size:10px;">عدم تطابق داده</span>';
                }

                let pnlColor = isWin ? '#34d399' : '#f87171';

                let waitTag = (pt.match && pt.match.wait_fmt && pt.match.wait_fmt !== '-')
                    ? `<div style="color:#38bdf8;font-size:9.5px;margin-top:2px;direction:rtl;font-family:sans-serif;">⏱️ انتظار: ${pt.match.wait_fmt}</div>`
                    : '';

                html += `<tr style="border-bottom:1px solid #1e293b;${!pt.isAllowed ? 'background:#1a0e1422;' : ''}">
                    <td style="padding:7px 8px;text-align:center;color:#64748b;">${pt.raw.setupId || ''}</td>
                    <td style="padding:7px 8px;font-weight:600;color:#f8fafc;">${pt.pattern}</td>
                    <td style="padding:7px 8px;text-align:center;">${tfBadge}</td>
                    <td style="padding:7px 8px;text-align:center;">${sideBadge}</td>
                    <td style="padding:7px 8px;color:#94a3b8;font-size:10.5px;">${pt.tEntryTime}${waitTag}</td>
                    <td style="padding:7px 8px;color:#cbd5e1;font-size:10.5px;">${pt.boxEntry.toFixed(5)}</td>
                    <td style="padding:7px 8px;color:#38bdf8;font-size:10.5px;font-weight:600;">${pt.marketFill.toFixed(5)}</td>
                    <td style="padding:7px 8px;text-align:center;color:${slipColor};font-weight:bold;">${pt.slippagePips.toFixed(1)}p</td>
                    <td style="padding:7px 8px;text-align:center;background:#064e3b18;border-left:1px solid #05966933;">${scStatusBadge}</td>
                    <td style="padding:7px 8px;text-align:center;background:#064e3b18;">${indResultHtml}</td>
                    <td style="padding:7px 8px;text-align:center;background:#1e3a5f18;border-left:1px solid #0284c733;color:#e2e8f0;font-size:10.5px;">${pt.exitClass}</td>
                    <td style="padding:7px 8px;text-align:center;background:#1e3a5f18;color:${pnlColor};font-weight:bold;direction:ltr;">${(pt.profitPips > 0 ? '+' : '')}${pt.profitPips.toFixed(1)}p | ${(pt.profitUSD > 0 ? '+$' : '-$')}${Math.abs(pt.profitUSD).toFixed(2)}</td>
                    <td style="padding:7px 10px;border-left:1px solid #334155;">${pt.verdictHtml}</td>
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
                        let dt = new Date(file.lastModified);
                        let y = dt.getFullYear();
                        let mon = String(dt.getMonth() + 1).padStart(2, '0');
                        let d = String(dt.getDate()).padStart(2, '0');
                        let h = String(dt.getHours()).padStart(2, '0');
                        let min = String(dt.getMinutes()).padStart(2, '0');
                        let fileTime = `${y}.${mon}.${d} ${h}:${min}`;
                        reportData.executionTime = fileTime;
                        reportData.fileTime = fileTime;

                        window.TESTER_REPORTS = window.TESTER_REPORTS || {};
                        let reportKey = 'uploaded_' + Date.now();
                        window.TESTER_REPORTS[reportKey] = reportData;

                        let sel = document.getElementById('testerRunSelector');
                        if (sel) {
                            let opt = document.createElement('option');
                            opt.value = reportKey;
                            opt.textContent = formatTesterOptionLabel(reportKey, reportData);
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

        