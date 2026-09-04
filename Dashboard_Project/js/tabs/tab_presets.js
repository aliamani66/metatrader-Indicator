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

    function openExportModal(cfg) {
        currentExportConfig = cfg;
        const modal = document.getElementById('mt5ExportModal');
        if (!modal) return;

        modal.style.display = 'flex';
        modal.style.zIndex = '99999999';

        const filename = `FlagPro_${cfg.symbol}_${cfg.title.replace(/[^a-zA-Z0-9]/g, '')}.set`;
        const elTitle = document.getElementById('mt5ModalTitle');
        if (elTitle) elTitle.textContent = cfg.title;
        const elFile = document.getElementById('mt5ModalFilename');
        if (elFile) elFile.textContent = filename;

        const codeBox = document.getElementById('mt5ConfigCodeBox');
        if (codeBox) codeBox.textContent = generateSetText(cfg);

        showToast('🤖 پنجره خروجی متاتریدر ۵ باز شد.');
    }

    function closeExportModal() {
        const modal = document.getElementById('mt5ExportModal');
        if (modal) modal.style.display = 'none';
    }

    function generateSetText(cfg) {
        return [
            ';+------------------------------------------------------------------+',
            ';| FlagPro_Trader EA Settings File (.set)                           |',
            ';| Symbol: ' + cfg.symbol + ' | Scenario: ' + cfg.title + ' |',
            ';+------------------------------------------------------------------+',
            'InpScenarioName=' + cfg.title,
            'InpMinTradePotential=' + (cfg.min_pot || 0).toFixed(2),
            'InpAllowedTradingHours=' + (cfg.hours_str || ''),
            'InpConsecLossTrigger=' + (cfg.consec_trig || 0),
            'InpConsecLossAction=' + (cfg.consec_action || 0),
            'InpDisabledKingsList=' + (cfg.disabled_kings_str || ''),
            'InpOnlyTradeKings=true',
            'InpEnableScaleOut=true',
            'InpLot_TP1=0.01',
            'InpLot_TP2=0.01',
            'InpLot_TP3=0.01',
            'InpLot_TP4=0.01',
            'InpMoveToBreakEven=true',
            'InpBEBufferPips=0.0'
        ].join('\r\n');
    }

    function downloadSetFile() {
        if (!currentExportConfig) return;
        const text = generateSetText(currentExportConfig);
        const filename = `FlagPro_${currentExportConfig.symbol}_Preset.set`;
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
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
        downloadSetFile: downloadSetFile
    };
})();
