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
    
    let parseStr = function(raw) {
        if (!raw || typeof raw !== 'string') return null;
        let str = raw.trim().toLowerCase();
        // 1. 24 Hours / All hours check in any language
        if (str === 'all' || str.includes('24') || str.includes('۲۴') || str.includes('شبانه‌روز') || str.includes('تمام ساعات') || str.includes('تمام شبانه‌روز')) {
            let s = new Set();
            for (let i = 0; i < 24; i++) s.add(i);
            return s;
        }
        // 2. Hour range (e.g. 04 الی 22, 08-20, 07:00 to 20:00)
        let rm = str.match(/(\d{1,2}):?00?\s*(?:الی|-|to|تا)\s*(\d{1,2}):?00?/);
        if (rm) {
            let s = parseInt(rm[1]), e = parseInt(rm[2]);
            let res = new Set();
            if (s <= e) {
                for (let i = s; i <= e; i++) res.add(i);
            } else {
                for (let i = s; i < 24; i++) res.add(i);
                for (let i = 0; i <= e; i++) res.add(i);
            }
            return res;
        }
        // 3. Comma / space separated list of hour numbers
        let parts = str.split(/[,;\s]+/).map(x => parseInt(x)).filter(n => !isNaN(n) && n >= 0 && n < 24);
        if (parts.length > 0) {
            return new Set(parts);
        }
        return null;
    };

    let fromVal = parseStr(val);
    if (fromVal && fromVal.size > 0) return fromVal;

    let fromFb = parseStr(fallbackDisplay);
    if (fromFb && fromFb.size > 0) return fromFb;

    return set;
}

function checkIsRawOrBaseScenario(scenario, report) {
    if (!scenario) return false;
    if (scenario.isRaw === true || scenario.isBaseScenario === true) return true;
    if (scenario.id === 'base' || scenario.id === 'raw' || scenario.id === 'all') return true;
    let title = ((scenario.title || scenario.rawTitle || scenario.name || '')).toLowerCase();
    if (title.includes('خام') || title.includes('کل معاملات') || title.includes('بدون فیلتر')) return true;
    if (scenario.id === 'equity_active') {
        let activeTitle = (window.currentActivePresetTitle || '').toLowerCase();
        if (window.currentActivePresetIdx === -1 || !window.currentActivePreset || activeTitle.includes('خام') || activeTitle.includes('کل معاملات') || (window.simState && window.simState.mode === 'all')) {
            return true;
        }
    }
    if (scenario.id === 'auto') {
        let p = (report && report.parameters) || {};
        if (!p.InpScenarioName || p.InpScenarioName.toLowerCase() === 'default' || p.InpScenarioName.toLowerCase().includes('base') || p.InpEnableKingsM1 === true) {
            return true;
        }
    }
    return false;
}

function getProcessedTesterTrades(report, scenarioKey) {
    if (!report) return [];
    let trades = report.trades || [];
    if (trades.length === 0) return [];

    let sym = report.symbol || window.currentActiveSymbol || 'GBPUSD';
    let cleanSym = sym.replace(/[^a-zA-Z0-9]/g, '');
    let sData = (window.ALL_SYMBOLS_DATA && (window.ALL_SYMBOLS_DATA[sym] || window.ALL_SYMBOLS_DATA[cleanSym] || window.ALL_SYMBOLS_DATA[window.currentActiveSymbol])) || {};
    let indTrades = sData.trades_json_list || [];
    let scenario = resolveActiveScenario(scenarioKey || window.currentTesterScenarioKey, report);
    let isBaseScenario = checkIsRawOrBaseScenario(scenario, report);

    // Pre-match and prepare trade metadata for 1:1 Deal-by-Deal forensics
    return trades.map(t => {
        let profitPips = (t.profitPips !== undefined && !isNaN(Number(t.profitPips))) ? Number(t.profitPips) : ((t.pnlPips !== undefined && !isNaN(Number(t.pnlPips))) ? Number(t.pnlPips) : 0);
        let profitUSD = (t.profitUSD !== undefined && !isNaN(Number(t.profitUSD))) ? Number(t.profitUSD) : ((t.pnlUSD !== undefined && !isNaN(Number(t.pnlUSD))) ? Number(t.pnlUSD) : 0);
        let slippagePips = (t.slippagePips !== undefined && !isNaN(Number(t.slippagePips))) ? Number(t.slippagePips) : 0;
        let boxEntry = (t.boxEntryPrice !== undefined && !isNaN(Number(t.boxEntryPrice))) ? Number(t.boxEntryPrice) : 0;
        let marketFill = (t.marketFillPrice !== undefined && !isNaN(Number(t.marketFillPrice))) ? Number(t.marketFillPrice) : boxEntry;
        let slPrice = (t.slPrice !== undefined && !isNaN(Number(t.slPrice))) ? Number(t.slPrice) : 0;
        let tp1 = (t.tp1 !== undefined && !isNaN(Number(t.tp1))) ? Number(t.tp1) : 0;
        let tp4 = (t.tp4 !== undefined && !isNaN(Number(t.tp4))) ? Number(t.tp4) : 0;

        let tEntryTime = (t.entryTime || '').substring(0, 16).replace(/-/g, '.');
        let tTF = (t.timeframe || '').replace('PERIOD_', '').trim();
        let tDir = (t.side || '').toUpperCase().trim();

        // 1:1 Match with Strategy / Indicator Dataset
        let match = null;
        let patClean = (t.pattern || '').trim();
        for (let it of indTrades) {
            let itEn = (it.en_t || '').substring(0, 16).replace(/-/g, '.');
            let itBoxT = (it.box_t || '').substring(0, 16).replace(/-/g, '.');
            let itTF = (it.tf || '').replace('PERIOD_', '').trim();
            let itDir = (it.dir || '').toUpperCase().trim();
            let itRole = (it.role || '').trim();

            if (tTF !== itTF || tDir !== itDir) continue;

            let isPatMatch = (patClean === itRole || patClean.replace(/\s*>\s*/g, '>') === itRole.replace(/\s*>\s*/g, '>') || patClean.includes(itRole) || itRole.includes(patClean));
            if (!isPatMatch) continue;

            if (tEntryTime && (tEntryTime === itEn || tEntryTime === itBoxT)) {
                match = it;
                break;
            }
            if (tEntryTime && itEn && tEntryTime.substring(0, 10) === itEn.substring(0, 10)) {
                let tM = parseInt(tEntryTime.substring(11, 13)) * 60 + parseInt(tEntryTime.substring(14, 16));
                let iM = parseInt(itEn.substring(11, 13)) * 60 + parseInt(itEn.substring(14, 16));
                if (Math.abs(tM - iM) <= 45) {
                    match = it;
                    break;
                }
            }
        }

        // Check if trade is allowed by active scenario
        let isAllowed = true;
        let filterReason = '';

        if (!isBaseScenario) {
            let patName = (t.pattern || (match ? match.role : '') || '').trim();
            let patKey = patName ? (patName + (tTF ? '|' + tTF : '')) : '';
            let isScenarioKing = false;
            if (Array.isArray(scenario.kings) && scenario.kings.length > 0) {
                let cleanP = patName.replace(/\s+/g, '').toLowerCase();
                let cleanPK = patKey.replace(/\s+/g, '').toLowerCase();
                isScenarioKing = scenario.kings.some(k => {
                    let kClean = (typeof k === 'string' ? k : (k.kk || k.role || '')).replace(/\s+/g, '').toLowerCase();
                    return kClean === cleanP || kClean === cleanPK || kClean.includes(cleanP) || cleanP.includes(kClean);
                });
            }

            if (tTF === 'M1' && !isScenarioKing) {
                let allowsM1 = scenario.tfM1 && (scenario.tfM1.includes('فعال (True)') || scenario.tfM1.includes('هوشمند'));
                if (!allowsM1) {
                    isAllowed = false;
                    filterReason = 'فیلتر نویز M1';
                }
            }
            if (isAllowed) {
                let h = tEntryTime.length >= 13 ? parseInt(tEntryTime.substring(11, 13)) : 0;
                let scHours = extractHourSet(scenario.hours, scenario.hoursDisplay);
                if (scHours.size > 0 && scHours.size < 24) {
                    if (!scHours.has(h)) {
                        isAllowed = false;
                        filterReason = 'ساعت غیرمجاز (' + (h < 10 ? '0' + h : h) + ':00)';
                    }
                } else if (scenario.id === 'day' && (h < 7 || h >= 20)) {
                    isAllowed = false;
                    filterReason = 'خارج از سشن روز (' + h + ':00)';
                } else if (scenario.id === 'champion' && (h >= 22 || h < 4)) {
                    isAllowed = false;
                    filterReason = 'فیلتر ساعات شب (' + h + ':00)';
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
                if (Array.isArray(scenario.kings) && scenario.kings.length > 0) {
                    if (!isScenarioKing) {
                        isAllowed = false;
                        filterReason = 'سلطان غیرمنتخب در سناریو (' + (patName || 'الگو') + ')';
                    }
                } else if (scenario.disabledKings && !scenario.disabledKings.includes('بدون مسدودی')) {
                    if (patName && (scenario.disabledKings.includes(patName) || (patKey && scenario.disabledKings.includes(patKey)))) {
                        isAllowed = false;
                        filterReason = 'سلطان مسدود (' + patName + ')';
                    }
                }
            }
        }

        // Indicator Theoretical PnL & Outcome
        let isJpy = sym.includes('JPY');
        let pipMult = isJpy ? 100 : 10000;
        let riskPips = (boxEntry > 0 && slPrice > 0) ? (Math.round(Math.abs(boxEntry - slPrice) * pipMult * 10) / 10) : 10.0;
        let riskPts = riskPips * 10;

        let exitPrice = 0.0;
        if (t.closePrice !== undefined && !isNaN(Number(t.closePrice))) {
            exitPrice = Number(t.closePrice);
        } else if (marketFill > 0 && profitPips !== 0) {
            exitPrice = (tDir === 'BUY') ? (marketFill + (profitPips / pipMult)) : (marketFill - (profitPips / pipMult));
        }

        let indNet = 0.0;
        let indPips = 0.0;
        let indTgt = '';
        let isIndWin = false;

        if (match) {
            indNet = match.net !== undefined ? Number(match.net) : (match.t1 ? (match.pts * 0.04) : -(match.pts * 0.04));
            isIndWin = (match.t1 === 1 || indNet > 0);
            indPips = match.pts ? (Math.round((match.pts / 10.0) * 10) / 10) : riskPips;
            if (!isIndWin && indPips > 0) indPips = -indPips;
            if (match.t4) indTgt = 'TP 1:4 🚀';
            else if (match.t3) indTgt = 'TP 1:3 🎯';
            else if (match.t2) indTgt = 'TP 1:2 🎯';
            else if (match.t1) indTgt = 'TP 1:1 🎯';
            else indTgt = 'Full SL ❌';
        } else {
            let tpsHit = (t.tpsHit !== undefined) ? parseInt(t.tpsHit) : ((t.outcome === 'Win' || profitUSD > 0) ? 1 : 0);
            if (tpsHit === 0) {
                indNet = -Math.round(riskPts * 0.04 * 100) / 100;
                indPips = -riskPips;
                indTgt = 'Full SL ❌';
                isIndWin = false;
            } else if (tpsHit === 1) {
                indNet = Math.round(riskPts * 0.04 * 0.5 * 100) / 100;
                indPips = riskPips;
                indTgt = 'TP 1:1 🎯';
                isIndWin = true;
            } else if (tpsHit === 2) {
                indNet = Math.round(riskPts * 0.04 * 1.5 * 100) / 100;
                indPips = Math.round(riskPips * 2.0 * 10) / 10;
                indTgt = 'TP 1:2 🎯';
                isIndWin = true;
            } else if (tpsHit === 3) {
                indNet = Math.round(riskPts * 0.04 * 2.5 * 100) / 100;
                indPips = Math.round(riskPips * 3.0 * 10) / 10;
                indTgt = 'TP 1:3 🎯';
                isIndWin = true;
            } else {
                indNet = Math.round(riskPts * 0.04 * 4.0 * 100) / 100;
                indPips = Math.round(riskPips * 4.0 * 10) / 10;
                indTgt = 'TP 1:4 🚀';
                isIndWin = true;
            }
        }

        // Forensic Verdict & Discrepancy Detection
        let verdictHtml = '';
        let isDisc = false;
        let exitCls = t.exitClass || '';
        let discMsg = t.discrepancyReason || t.discrepancyLabel || '';

        if (discMsg && discMsg.includes('اسپرد')) {
            isDisc = true;
            verdictHtml = `<span style="color:#fca5a5;">❌ <b>اسپرد Ask روی استاپ:</b> در پوزیشن فروش، حد ضرر با قیمت Ask معامله‌گر لمس شد.</span>`;
        } else if (!isAllowed) {
            isDisc = true;
            verdictHtml = `<span style="color:#fca5a5;">🛑 <b>فیلتر در سناریو:</b> علت: «${filterReason}» (${profitUSD < 0 ? 'جلوی این باخت در سناریو گرفته شد' : 'در سناریو رد شد'}).</span>`;
        } else if (isIndWin && profitUSD < 0) {
            isDisc = true;
            verdictHtml = `<span style="color:#fca5a5;">❌ <b>اختلاف اجرای مارکت:</b> در اندیکاتور تارگت زده شد اما در تستر به دلیل نوسان یا اسپرد استاپ خورد.</span>`;
        } else if (!isIndWin && profitUSD >= 0) {
            isDisc = true;
            verdictHtml = `<span style="color:#a7f3d0;">🟢 <b>سودآوری مازاد تستر:</b> خروج تستر با تریل یا نوسان سودآورتر از حد ضرر اندیکاتور بود.</span>`;
        } else if (isIndWin && profitUSD >= 0) {
            if (exitCls.includes('BE') || exitCls.includes('پولبک')) {
                verdictHtml = `<span style="color:#38bdf8;">🛡️ <b>سیو سود روی پولبک:</b> سود اولیه در هر دو ذخیره شد؛ در تستر پوزیشن باقیمانده روی BE خارج شد.</span>`;
            } else {
                verdictHtml = `<span style="color:#a7f3d0;">🟢 <b>انطباق کامل:</b> تارگت ستاپ در تستر و اندیکاتور با موفقیت لمس شد و سود ثبت گردید.</span>`;
            }
        } else if (slippagePips >= 2.0) {
            isDisc = true;
            verdictHtml = `<span style="color:#fde68a;">⚡ <b>اسلیپیج شدید ${slippagePips.toFixed(1)} پیپ:</b> لغزش قیمت در لحظه اجرای مارکت نسبت به قیمت لیمیت.</span>`;
        } else {
            verdictHtml = `<span style="color:#94a3b8;">همگام (استاپ طبیعی در تستر و اندیکاتور).</span>`;
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
            exitPrice: exitPrice,
            tEntryTime: tEntryTime,
            tTF: tTF,
            tDir: tDir,
            pattern: t.pattern || '',
            exitClass: exitCls,
            match: match,
            isAllowed: isAllowed,
            filterReason: filterReason,
            indNet: indNet,
            indPips: indPips,
            indTgt: indTgt,
            isIndWin: isIndWin,
            verdictHtml: verdictHtml,
            isDisc: isDisc
        };
    });
}

