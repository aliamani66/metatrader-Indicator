/**
 * FlagPro Dashboard - Tab 8: Strategic Smart Presets & MT5 EA Export
 */
const TabPresets = (function() {
    'use strict';

    let currentExportConfig = null;

    function init() {
        AppStateManager.subscribe('dataUpdate', () => {
            renderPresetsTable();
            loadCustomPresets();
        });
    }

    function renderPresetsTable() {
        const tbody = document.getElementById('systemPresetsTbody');
        const sData = AppStateManager.getSymbolData();
        if (!tbody || !sData || !sData.smart_presets) return;

        let html = '';
        sData.smart_presets.forEach(p => {
            const rowBorder = p.is_featured ? 'border: 2px solid #facc15; background: #1c1806;' : 'border-bottom: 1px solid #1e293b;';
            const pfDisplay = p.pf < 900 ? p.pf.toFixed(2) : '∞';
            const netCol = p.net >= 0 ? '#00e676' : '#ef4444';
            const badgeTag = `<span class="badge" style="background:${p.badge_bg};color:${p.badge_col};">${p.badge}</span>`;

            html += `
                <tr id="presetRow${p.idx}" style="${rowBorder}">
                    <td class="text-center" style="font-weight:bold;color:#facc15;">#${p.idx + 1}</td>
                    <td>
                        <div style="font-weight:bold;color:#f1f5f9;display:flex;align-items:center;gap:6px;">
                            <span>${p.title}</span>
                            ${badgeTag}
                        </div>
                        <div style="font-size:11px;color:#94a3b8;margin-top:2px;">${p.desc}</div>
                    </td>
                    <td class="text-center">
                        <div>کف سود: <b>$${(p.min_pot || 0).toFixed(2)}</b></div>
                        <div style="font-size:10.5px;color:#38bdf8;">👑 ${p.kings ? p.kings.length : 0} سلطان فعال</div>
                    </td>
                    <td class="text-center" style="font-weight:bold;">${p.cnt.toLocaleString()}</td>
                    <td class="text-center" style="font-weight:bold;color:#34d399;">${p.wr.toFixed(1)}٪</td>
                    <td class="text-center" style="font-weight:bold;color:#38bdf8;">${pfDisplay}</td>
                    <td class="text-center" style="font-weight:bold;color:#facc15;">$${p.avg.toFixed(2)}</td>
                    <td class="text-center" style="font-weight:bold;color:#fca5a5;">$${p.max_dd || 0}</td>
                    <td class="text-center" style="font-weight:bold;color:${netCol};background:rgba(6,78,59,0.2);">${p.net >= 0 ? '+' : ''}$${p.net.toLocaleString()}</td>
                    <td class="text-center">
                        <div style="display:inline-flex;gap:4px;">
                            <button id="btnApplyPreset${p.idx}" class="btn btn-primary" onclick="TabPresets.applyPreset(${p.idx})" style="padding:4px 8px;font-size:11px;">
                                ⚡ اعمال
                            </button>
                            <button class="btn btn-success" onclick="TabPresets.exportPreset(${p.idx})" style="padding:4px 8px;font-size:11px;">
                                🤖 خروجی EA
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
    }

    function applyPreset(idx) {
        try {
            const sData = AppStateManager.getSymbolData();
            if (!sData || !sData.smart_presets) return;

            let p = sData.smart_presets.find(x => x.idx == idx);
            if (!p && sData.smart_presets.length > 0) p = sData.smart_presets[0];
            if (!p) return;

            // Apply parameters to simulator
            const simState = AppStateManager.getSimState();
            simState.mode = 'kings';
            simState.minProfit = Number(p.min_pot || 0);

            if (Array.isArray(p.hours) && p.hours.length === 24) {
                simState.allowedHours = [...p.hours];
            } else {
                simState.allowedHours = new Array(24).fill(true);
            }

            if (Array.isArray(p.kings) && p.kings.length > 0) {
                simState.enabledKings = new Set(p.kings);
            } else {
                simState.enabledKings = new Set((sData.kings_sim_list || []).map(k => k.kk));
            }

            simState.consecLossTrigger = p.consec_trig || 0;
            simState.consecLossSkipCount = p.consec_sk || 1;
            simState.consecLossSkipDay = !!p.consec_day;

            // Sync controls
            const slider = document.getElementById('simProfitSlider');
            if (slider) slider.value = simState.minProfit;
            const sliderVal = document.getElementById('simProfitSliderVal');
            if (sliderVal) sliderVal.textContent = '$' + simState.minProfit.toFixed(2);

            TabEquity.simulateAndDraw();

            // Auto-scroll up to chart
            const eqCanvas = document.getElementById('equityCanvas');
            if (eqCanvas && typeof eqCanvas.scrollIntoView === 'function') {
                eqCanvas.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }

            showToast('⚡ سناریوی «' + (p.title || '') + '» روی چارت اعمال و شبیه‌سازی شد!');
        } catch(err) {
            console.error('Error applying preset:', err);
        }
    }

    function exportPreset(idx) {
        const sData = AppStateManager.getSymbolData();
        if (!sData || !sData.smart_presets) return;

        let p = sData.smart_presets.find(x => x.idx == idx) || sData.smart_presets[0];
        if (!p) return;

        const disabledKings = [];
        const enabledSet = new Set(p.kings || []);
        (sData.kings_sim_list || []).forEach(k => {
            if (!enabledSet.has(k.kk)) disabledKings.push(k.kk);
        });

        const allowedHours = [];
        if (p.hours) {
            for (let h = 0; h < 24; h++) {
                if (p.hours[h]) allowedHours.push(h < 10 ? '0' + h : '' + h);
            }
        }
        const hoursStr = allowedHours.length === 24 ? '' : allowedHours.join(',');

        const config = {
            title: p.title || 'Custom Preset',
            min_pot: Number(p.min_pot || 0),
            hours_str: hoursStr,
            consec_trig: p.consec_trig || 0,
            consec_action: p.consec_day ? 3 : (p.consec_sk === 2 ? 2 : 1),
            disabled_kings_str: disabledKings.join(', '),
            cnt: p.cnt || '-',
            wr: p.wr || 0,
            pf: p.pf || 0,
            avg: p.avg || 0,
            net: p.net || 0,
            kings_count: p.kings ? p.kings.length : 0,
            symbol: sData.symbol || 'EURUSD'
        };

        openExportModal(config);
    }

    function buildFilename(cfg) {
        const now = new Date();
        const dateStr = now.getFullYear() + '-' +
            String(now.getMonth() + 1).padStart(2, '0') + '-' +
            String(now.getDate()).padStart(2, '0') + '_' +
            String(now.getHours()).padStart(2, '0') + '-' +
            String(now.getMinutes()).padStart(2, '0');
        const cleanTitle = (cfg.title || 'Preset')
            .replace(/[^a-zA-Z0-9]/g, '_')
            .replace(/_+/g, '_')
            .replace(/^_|_$/g, '') || 'Preset';
        const wrStr = cfg.wr ? `_WR${Math.round(cfg.wr)}` : '';
        const pfStr = cfg.pf && cfg.pf < 900 ? `_PF${Number(cfg.pf).toFixed(1)}` : '';
        return `FlagPro_${cfg.symbol || 'EURUSD'}_${cleanTitle}${wrStr}${pfStr}_${dateStr}.set`;
    }

    function createUTF16LEBlob(text) {
        // MetaTrader 5 strictly requires UTF-16 LE with BOM (0xFF, 0xFE)
        const buffer = new ArrayBuffer(2 + text.length * 2);
        const view = new DataView(buffer);
        view.setUint16(0, 0xFEFF, true); // Little-Endian BOM (0xFF, 0xFE)
        for (let i = 0; i < text.length; i++) {
            view.setUint16(2 + i * 2, text.charCodeAt(i), true);
        }
        return new Blob([buffer], { type: 'application/octet-stream' });
    }

    function generateSetText(cfg) {
        const now = new Date();
        const nowStr = now.getFullYear() + '.' +
            String(now.getMonth() + 1).padStart(2, '0') + '.' +
            String(now.getDate()).padStart(2, '0') + ' ' +
            String(now.getHours()).padStart(2, '0') + ':' +
            String(now.getMinutes()).padStart(2, '0') + ':' +
            String(now.getSeconds()).padStart(2, '0');

        return [
            ';+------------------------------------------------------------------+',
            ';| FlagPro_Trader EA Settings File (.set)                           |',
            ';| File: ' + buildFilename(cfg) + ' |',
            ';| Auto-generated from FlagPro Strategy Dashboard                   |',
            ';| Date: ' + nowStr + ' |',
            ';| Target Folder: MQL5/Experts/تنظیمات/                             |',
            ';| Symbol: ' + (cfg.symbol || 'EURUSD') + ' | Scenario: ' + (cfg.title || 'Custom') + ' |',
            ';| Win Rate: ' + (cfg.wr || 0).toFixed(1) + '% | Profit Factor: ' + (cfg.pf || 0).toFixed(2) + ' |',
            ';| Avg Profit: $' + (cfg.avg || 0).toFixed(2) + ' | Active Kings: ' + (cfg.kings_count || 0) + ' |',
            ';+------------------------------------------------------------------+',
            'InpScenarioName=' + (cfg.title || 'Custom'),
            'InpMinTradePotential=' + parseFloat(cfg.min_pot || 0).toFixed(2),
            'InpAllowedTradingHours=' + (cfg.hours_str || ''),
            'InpConsecLossTrigger=' + parseInt(cfg.consec_trig || 0),
            'InpConsecLossAction=' + parseInt(cfg.consec_action || 0),
            'InpDisabledKingsList=' + (cfg.disabled_kings_str || ''),
            'InpOnlyTradeKings=true',
            'InpTradeOnlyGoldenKings=true',
            'InpEnableKingsM15=true',
            'InpEnableKingsM5=true',
            'InpEnableKingsM1=true',
            'InpAllowOverlappingTrades=true',
            'InpSlippagePoints=20',
            'InpMaxEntryDeviationPips=2.5',
            'InpSLOffsetPips=3.0',
            'InpMaxSLPips=0.0',
            'InpMaxOpenGroups=5',
            'InpMagicNumber=777123',
            'InpEnableScaleOut=true',
            'InpLot_TP1=0.01',
            'InpLot_TP2=0.01',
            'InpLot_TP3=0.01',
            'InpLot_TP4=0.01',
            'InpMoveToBreakEven=true',
            'InpBEBufferPips=1.0',
            'InpTrailToTP1=true',
            'InpTrailToTP2=true',
            'InpFilterSingleLS=true',
            'InpFilterNightHours=true',
            'InpFilterPreLondonHunt=true',
            'InpFilterToxicPatterns=true',
            'InpFilterPureFlags=true',
            'InpHideFilteredBoxes=true',
            'InpFilterLowRewardVsFriction=true',
            'InpBrokerCommissionPerLot=6.0',
            'InpEstimatedSpreadPips=0.8',
            'InpMinNetProfitRatioTP1=1.0',
            'InpUseTF7=true',
            'InpUseTF6=true',
            'InpUseTF5=true',
            'InpTradeMacroTFs=false',
            'InpLookbackBars=5000',
            'InpHistoryMode=0',
            'InpHistoryStartDate=1735689600',
            'InpHistoryDays=365',
            'InpShowBoxes=false',
            'InpAutoDrawTrades=true',
            'InpExportCSV=true'
        ].join('\r\n');
    }

    function openExportModal(cfg) {
        currentExportConfig = cfg;
        const modal = document.getElementById('mt5ExportModal');
        if (!modal) return;

        modal.style.display = 'flex';
        modal.style.zIndex = '99999999';

        const filename = buildFilename(cfg);
        const elTitle = document.getElementById('mt5ModalTitle');
        if (elTitle) elTitle.textContent = cfg.title;
        const elFile = document.getElementById('mt5ModalFilename');
        if (elFile) elFile.textContent = filename;

        const codeBox = document.getElementById('mt5ConfigCodeBox');
        if (codeBox) codeBox.textContent = generateSetText(cfg);

        const statusEl = document.getElementById('saveStatusIndicator');
        if (statusEl) {
            statusEl.textContent = 'آماده ذخیره‌سازی';
            statusEl.style.color = '#5eead4';
        }

        showToast('🤖 پنجره خروجی متاتریدر ۵ باز شد.');
    }

    function closeExportModal() {
        const modal = document.getElementById('mt5ExportModal');
        if (modal) modal.style.display = 'none';
    }

    function downloadSetFile() {
        if (!currentExportConfig) return;
        const text = generateSetText(currentExportConfig);
        const filename = buildFilename(currentExportConfig);
        const blob = createUTF16LEBlob(text);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('📥 فایل تنظیمات «' + filename + '» با فرمت UTF-16 LE متاتریدر ۵ دانلود شد.');
    }

    async function saveToSettingsFolder() {
        if (!currentExportConfig) return;
        const text = generateSetText(currentExportConfig);
        const filename = buildFilename(currentExportConfig);
        const btn = document.getElementById('btnSaveToSettingsFolder');
        const statusEl = document.getElementById('saveStatusIndicator');
        if (btn) btn.innerHTML = '<span>⏳ در حال ذخیره...</span>';
        if (statusEl) {
            statusEl.textContent = 'در حال ارتباط با سرور...';
            statusEl.style.color = '#facc15';
        }

        // 1. Try local bridge server
        try {
            const resp = await fetch('http://127.0.0.1:8288/save_set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: filename, content: text })
            });
            if (resp.ok) {
                const json = await resp.json();
                if (json.success) {
                    if (btn) btn.innerHTML = '<span>✅ در پوشه تنظیمات ذخیره شد!</span>';
                    if (statusEl) {
                        statusEl.textContent = '✅ فایل در Experts/تنظیمات ذخیره شد';
                        statusEl.style.color = '#4ade80';
                    }
                    showToast('✅ فایل تنظیمات <b>' + filename + '</b> مستقیماً در پوشه <b>Experts/تنظیمات</b> ذخیره شد.');
                    setTimeout(() => {
                        if (btn) btn.innerHTML = '<span>💾 ذخیره تو تنظیمات (.set)</span>';
                    }, 3500);
                    return;
                }
            }
        } catch (e) {
            // Bridge server offline
        }

        // 2. Safe Fallback: Direct download in UTF-16 LE (Bypassing Chromium system-files block)
        downloadSetFile();
        if (btn) btn.innerHTML = '<span>📥 فایل دانلود شد</span>';
        if (statusEl) {
            statusEl.textContent = 'فایل دانلود شد (سرور خودکار خاموش است)';
            statusEl.style.color = '#38bdf8';
        }
        showToast('📥 فایل با فرمت استاندارد متاتریدر دانلود شد. فایل <b>start_settings_bridge.bat</b> را اجرا کنید تا ذخیره مستقیم با یک کلیک فعال شود.');
        setTimeout(() => {
            if (btn) btn.innerHTML = '<span>💾 ذخیره تو تنظیمات (.set)</span>';
        }, 3500);
    }

    async function openSettingsFolder() {
        try {
            const resp = await fetch('http://127.0.0.1:8288/open_folder', { method: 'POST' });
            if (resp.ok) {
                const json = await resp.json();
                if (json.success) {
                    showToast('📂 پوشه تنظیمات در ویندوز باز شد.');
                    return;
                }
            }
        } catch (e) {}

        const path = ['C:', 'Users', 'USER', 'AppData', 'Roaming', 'MetaQuotes', 'Terminal', '3F2C3A2F8B221C9D88E569F2FD1D3E97', 'MQL5', 'Experts', 'تنظیمات'].join(String.fromCharCode(92));
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

    function copyConfigText() {
        if (!currentExportConfig) return;
        const text = generateSetText(currentExportConfig);
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('📋 متن تنظیمات در کلیپ‌بورد کپی شد.');
            });
        }
    }

    function loadCustomPresets() {
        // LocalStorage loading placeholder
    }

    function showToast(msg) {
        let toast = document.getElementById('flagproGlobalToast');
        if (!toast) return;
        toast.innerHTML = '<span>💾</span><div>' + msg + '</div>';
        toast.style.display = 'flex';
        toast.style.opacity = '1';
        clearTimeout(toast._timer);
        toast._timer = setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => { toast.style.display = 'none'; }, 300);
        }, 4000);
    }

    window.renderTab_presets = function(sData) {
        renderPresetsTable();
    };

    return {
        init: init,
        renderPresetsTable: renderPresetsTable,
        applyPreset: applyPreset,
        exportPreset: exportPreset,
        openExportModal: openExportModal,
        closeExportModal: closeExportModal,
        downloadSetFile: downloadSetFile,
        saveToSettingsFolder: saveToSettingsFolder,
        openSettingsFolder: openSettingsFolder,
        copyConfigText: copyConfigText
    };
})();
