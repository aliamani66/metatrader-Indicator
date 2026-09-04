function buildMT5SetFilename(cfg) {
            let sym = (cfg.symbol || (typeof currentActiveSymbol !== 'undefined' ? currentActiveSymbol : 'EURUSD')).replace(/[^a-zA-Z0-9]/g, '');
            if (!sym) sym = 'EURUSD';

            // Clean scenario title to safe descriptive ASCII
            let rawTitle = cfg.title || 'Custom';
            let cleanTitle = 'Custom';
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
                if (asciiOnly.length >= 3 && asciiOnly.toUpperCase() !== sym.toUpperCase()) cleanTitle = asciiOnly;
                else cleanTitle = 'CustomSetup';
            }

            let wrVal = parseFloat(String(cfg.wr).replace(/[^0-9.]/g, '')) || 0;
            let pfVal = parseFloat(String(cfg.pf).replace(/[^0-9.]/g, '')) || 0;

            let wrPart = 'WR' + Math.round(wrVal);
            let pfPart = 'PF' + pfVal.toFixed(1);

            // 📅 Current Date & Time format: YYYY-MM-DD_HH-mm
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
            let sym = (cfg.symbol || (typeof currentActiveSymbol !== 'undefined' ? currentActiveSymbol : 'EURUSD'));
            let filename = buildMT5SetFilename(cfg);
            let now = new Date();
            let nowStr = now.getFullYear() + '.' + String(now.getMonth() + 1).padStart(2, '0') + '.' + String(now.getDate()).padStart(2, '0') + ' ' + String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0') + ':' + String(now.getSeconds()).padStart(2, '0');
            
            // Clean ASCII safe scenario title
            let safeTitle = (cfg.title || 'Custom').replace(/[^a-zA-Z0-9_\s\-]/g, ' ').trim();
            if (!safeTitle) safeTitle = 'Custom Strategy';

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
                ';=== ۱. سلاطین طلایی، سناریوی داشبورد و ستاپ‌ها ===',
                'InpScenarioName=' + safeTitle,
                'InpOnlyTradeKings=true',
                'InpDisabledKingsList=' + (cfg.disabled_kings_str || ''),
                'InpEnableKingsM15=true',
                'InpEnableKingsM5=true',
                'InpEnableKingsM1=true',
                'InpTradeOnlyGoldenKings=true',
                'InpAllowOverlappingTrades=true',
                '',
                ';=== ۲. اسلیپیج، انحراف مجاز ورود و مدیریت ریسک معامله ===',
                'InpSlippagePoints=20',
                'InpMaxEntryDeviationPips=2.5',
                'InpSLOffsetPips=3.0',
                'InpMaxSLPips=0.0',
                'InpMaxOpenGroups=5',
                'InpMagicNumber=777123',
                '',
                ';=== ۳. سیستم خروج ۴ مرحله‌ای (Scale-Out & Trailing) ===',
                'InpEnableScaleOut=true',
                'InpLot_TP1=0.01',
                'InpLot_TP2=0.01',
                'InpLot_TP3=0.01',
                'InpLot_TP4=0.01',
                'InpMoveToBreakEven=true',
                'InpBEBufferPips=1.0',
                'InpTrailToTP1=true',
                'InpTrailToTP2=true',
                '',
                ';=== ۴. ساعات معاملاتی، کف سود و فیوز ایمنی ===',
                'InpAllowedTradingHours=' + (cfg.hours_str || ''),
                'InpMinTradePotential=' + parseFloat(cfg.min_pot || 0).toFixed(2),
                'InpConsecLossTrigger=' + parseInt(cfg.consec_trig || 0),
                'InpConsecLossAction=' + parseInt(cfg.consec_action || 1),
                '',
                ';=== ۵. فیلترهای ضد استاپ و هزینه کمیسیون ===',
                'InpFilterNightHours=true',
                'InpFilterPreLondonHunt=true',
                'InpFilterToxicPatterns=true',
                'InpFilterSingleLS=true',
                'InpFilterPureFlags=true',
                'InpFilterLowRewardVsFriction=true',
                'InpBrokerCommissionPerLot=6.0',
                'InpEstimatedSpreadPips=0.8',
                'InpMinNetProfitRatioTP1=1.0',
                '',
                ';=== ۶. تایم‌فریم‌های فعال معامله ===',
                'InpUseTF7=true',
                'InpUseTF6=true',
                'InpUseTF5=true',
                'InpTradeMacroTFs=false',
                'InpLookbackBars=5000'
            ];
            return lines.join(String.fromCharCode(13, 10));
        }

        function createUTF16LEBlob(text) {
            let buffer = new ArrayBuffer(2 + text.length * 2);
            let view = new DataView(buffer);
            view.setUint16(0, 0xFEFF, true);
            for (let i = 0; i < text.length; i++) {
                view.setUint16(2 + i * 2, text.charCodeAt(i), true);
            }
            return new Blob([buffer], { type: 'application/octet-stream' });
        }

        function downloadSetFile(filename, text) {
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
                showSaveNotification('📥 فایل تنظیمات «' + filename + '» با فرمت متاتریدر ۵ (UTF-16 LE) دانلود شد.');
            }
        }

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
                let config = {
                    title: (p.title || 'Custom').replace(/[^a-zA-Z0-9_\s\-\u0600-\u06FF]/gi, '').trim(),
                    min_pot: (p.min_pot !== undefined && !isNaN(Number(p.min_pot))) ? Number(p.min_pot) : 0,
                    hours_str: hoursStr,
                    consec_trig: p.consec_trig || 0,
                    consec_action: actionInt,
                    disabled_kings_str: disabledStr,
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

        function exportCurrentStateToMT5() {
            try {
                let allowedHours = [];
                for (let h = 0; h < 24; h++) {
                    if (simState.allowedHours && simState.allowedHours[h]) allowedHours.push(h < 10 ? '0' + h : '' + h);
                }
                let hoursStr = allowedHours.length === 24 ? '' : allowedHours.join(',');

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

                let config = {
                    title: 'چیدمان فعال (' + sym + ')',
                    min_pot: simState.minProfit || 0,
                    hours_str: hoursStr,
                    consec_trig: simState.consecLossTrigger || 0,
                    consec_action: actionInt,
                    disabled_kings_str: disabledStr,
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

        function openMT5ExportModal(cfg) {
            try {
                currentExportConfig = cfg;
                let modal = document.getElementById('mt5ExportModal');
                if (!modal) {
                    console.error('mt5ExportModal not found!');
                    if (typeof alert === 'function') alert('خطا: پنجره خروجی متاتریدر در صفحه پیدا نشد.');
                    return;
                }

                // Display modal prominently
                modal.style.display = 'flex';
                modal.style.zIndex = '99999999';

                let filename = buildMT5SetFilename(cfg);
                let elTitle = document.getElementById('mt5ModalTitle');
                if (elTitle) elTitle.textContent = cfg.title;
                let fileBadge = document.getElementById('mt5ModalFilename');
                if (fileBadge) fileBadge.textContent = filename;

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

                let elDisabled = document.getElementById('mt5ParamDisabled');
                if (elDisabled) elDisabled.textContent = cfg.disabled_kings_str ? cfg.disabled_kings_str : 'هیچ‌کدام (تمام سلاطین فعال)';

                let fullText = generateSetFileText(cfg);
                let codeBox = document.getElementById('mt5ConfigCodeBox');
                if (codeBox) codeBox.textContent = fullText;

                if (typeof showSaveNotification === 'function') {
                    showSaveNotification('🤖 پنجره خروجی متاتریدر ۵ برای «' + (cfg.title || 'سناریو') + '» باز شد.');
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

        function getMT5ExpertsSettingsFolderPath() {
            return ['C:', 'Users', 'USER', 'AppData', 'Roaming', 'MetaQuotes', 'Terminal', '3F2C3A2F8B221C9D88E569F2FD1D3E97', 'MQL5', 'Experts', 'تنظیمات'].join(String.fromCharCode(92));
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
                    alert('📋 مسیر پوشه تنظیمات اکسپرت در کلیپ‌بورد کپی شد:\\n\\n' + path + '\\n\\nمی‌توانید در نوار آدرس File Explorer ویندوز Paste کنید.');
                }).catch(() => {
                    prompt('مسیر پوشه تنظیمات (Ctrl+C برای کپی):', path);
                });
            } else {
                prompt('مسیر پوشه تنظیمات (Ctrl+C برای کپی):', path);
            }
        }

        async function saveCurrentMT5SetFileToSettingsFolder() {
            if (!currentExportConfig) return;
            let text = generateSetFileText(currentExportConfig);
            let filename = buildMT5SetFilename(currentExportConfig);
            let btn = document.getElementById('btnSaveToSettingsFolder');
            let ind = document.getElementById('saveStatusIndicator');
            if (btn) btn.innerHTML = '<span>⏳ در حال ذخیره در پوشه...</span>';
            if (ind) { ind.textContent = 'در حال ذخیره‌سازی...'; ind.style.color = '#facc15'; }

            // 1. Try local bridge server first
            try {
                let resp = await fetch('http://127.0.0.1:8288/save_set', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: filename, content: text })
                });
                if (resp.ok) {
                    let json = await resp.json();
                    if (json.success) {
                        if (btn) btn.innerHTML = '<span>✅ در تنظیمات ذخیره شد!</span>';
                        if (ind) { ind.textContent = '✅ فایل در Experts/تنظیمات ذخیره شد'; ind.style.color = '#4ade80'; }
                        showSaveNotification('فایل تنظیمات <b>' + filename + '</b> با موفقیت در پوشه <b>MQL5/Experts/تنظیمات</b> ذخیره شد.');
                        setTimeout(() => {
                            if (btn) btn.innerHTML = '<span>💾 ذخیره تو تنظیمات (.set)</span>';
                        }, 3500);
                        return;
                    }
                }
            } catch(e) {
                // Bridge server is offline
            }

            // 2. Safe Fallback: Direct download in UTF-16 LE
            // Bypasses window.showSaveFilePicker to avoid Chromium system files sandbox error in AppData
            downloadSetFile(filename, text);
            if (btn) btn.innerHTML = '<span>📥 فایل دانلود شد</span>';
            if (ind) { ind.textContent = 'فایل دانلود شد (سرور خودکار خاموش است)'; ind.style.color = '#38bdf8'; }
            showSaveNotification('فایل <b>' + filename + '</b> با فرمت متاتریدر ۵ دانلود شد. فایل <b>start_settings_bridge.bat</b> را اجرا کنید تا ذخیره مستقیم فعال شود.');
            setTimeout(() => {
                if (btn) btn.innerHTML = '<span>💾 ذخیره تو تنظیمات (.set)</span>';
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

        function downloadCurrentMT5SetFile() {
            if (!currentExportConfig) return;
            let text = generateSetFileText(currentExportConfig);
            let filename = buildMT5SetFilename(currentExportConfig);
            downloadSetFile(filename, text);
        }

        function copyMT5ConfigText() {
            if (!currentExportConfig) return;
            let text = generateSetFileText(currentExportConfig);
            navigator.clipboard.writeText(text).then(() => {
                alert('📋 تمام پارامترهای اکسپرت با موفقیت کپی شد! می‌توانید در متاتریدر استفاده کنید.');
            }).catch(() => {
                let box = document.getElementById('mt5ConfigCodeBox');
                if (box) {
                    let range = document.createRange();
                    range.selectNodeContents(box);
                    let sel = window.getSelection();
                    sel.removeAllRanges();
                    sel.addRange(range);
                    document.execCommand('copy');
                    alert('📋 پارامترها کپی شد!');
                }
            });
        }

        