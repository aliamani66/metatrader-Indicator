// Global Simulation State
var simState = (typeof simState !== 'undefined') ? simState : {
    mode: 'kings',
    enabledKings: new Set(),
    allowedHours: new Array(24).fill(true),
    minProfit: 0.0,
    consecLossTrigger: 0,
    consecLossSkipCount: 1,
    consecLossSkipDay: false,
    showDrawdown: true
};
var kingsSimList = (typeof kingsSimList !== 'undefined') ? kingsSimList : [];
var top3SLCntKeys = (typeof top3SLCntKeys !== 'undefined') ? top3SLCntKeys : [];
var top3SLUsdKeys = (typeof top3SLUsdKeys !== 'undefined') ? top3SLUsdKeys : [];
var top5SLUsdKeys = (typeof top5SLUsdKeys !== 'undefined') ? top5SLUsdKeys : [];
var top3SLPctKeys = (typeof top3SLPctKeys !== 'undefined') ? top3SLPctKeys : [];
var simTrades = (typeof simTrades !== 'undefined') ? simTrades : [];
var smartPresets = (typeof smartPresets !== 'undefined') ? smartPresets : [];
var allTrades = (typeof allTrades !== 'undefined') ? allTrades : [];
var currentExportConfig = (typeof currentExportConfig !== 'undefined') ? currentExportConfig : null;
var simCanvasEventsInitialized = (typeof simCanvasEventsInitialized !== 'undefined') ? simCanvasEventsInitialized : false;
var currentSimPts = (typeof currentSimPts !== 'undefined') ? currentSimPts : [];


function clearPresetActiveState() {
            document.querySelectorAll('.preset-table-row').forEach(r => {
                r.style.outline = 'none';
                r.style.boxShadow = 'none';
            });
            document.querySelectorAll('.apply-preset-btn').forEach(b => {
                b.innerHTML = '⚡ اعمال روی نمودار';
                b.style.background = 'linear-gradient(135deg, #0284c7, #0369a1)';
                b.style.borderColor = '#38bdf8';
            });
        }

        function applySmartPreset(idx) {
            try {
                let p = (smartPresets || []).find(x => x.idx == idx);
                if (!p && smartPresets && smartPresets.length > 0) {
                    p = smartPresets[0];
                }
                if (!p) {
                    alert('سناریوی انتخابی یافت نشد!');
                    return;
                }

                // 1. Set mode to kings
                simState.mode = 'kings';
                let btnK = document.getElementById('btnEqKings');
                let btnA = document.getElementById('btnEqAll');
                if (btnK) btnK.classList.add('active');
                if (btnA) btnA.classList.remove('active');

                // 2. Set min profit
                simState.minProfit = (p.min_pot !== undefined && !isNaN(Number(p.min_pot))) ? Number(p.min_pot) : 0.0;
                let slider = document.getElementById('simProfitSlider');
                if (slider) slider.value = simState.minProfit;
                let sliderVal = document.getElementById('simProfitSliderVal');
                if (sliderVal) sliderVal.textContent = '$' + simState.minProfit.toFixed(2);
                let pBadge = document.getElementById('simProfitBadge');
                if (pBadge) {
                    pBadge.textContent = (simState.minProfit === 0) ? 'بدون فیلتر ($0)' : 'حداقل $' + simState.minProfit.toFixed(2);
                    pBadge.style.background = (simState.minProfit === 0) ? '#064e3b' : '#0369a1';
                }
                document.querySelectorAll('.profit-preset-btn').forEach(b => {
                    b.classList.remove('active');
                    if (parseFloat(b.dataset.val) === simState.minProfit) b.classList.add('active');
                });

                // 3. Set allowed hours
                if (Array.isArray(p.hours) && p.hours.length === 24) {
                    simState.allowedHours = [...p.hours];
                } else {
                    simState.allowedHours = new Array(24).fill(true);
                }
                document.querySelectorAll('.hour-preset-btn').forEach(b => b.classList.remove('active'));
                let hName = p.hours_name || 'all';
                if (hName === 'all') {
                    let b = document.getElementById('btnHAll');
                    if (b) b.classList.add('active');
                } else if (hName === 'no_night') {
                    let b = document.getElementById('btnHNoNight');
                    if (b) b.classList.add('active');
                } else if (hName === 'lon_ny') {
                    let b = document.getElementById('btnHLonNy');
                    if (b) b.classList.add('active');
                }

                // 4. Set enabled kings
                if (Array.isArray(p.kings) && p.kings.length > 0) {
                    simState.enabledKings = new Set(p.kings);
                } else if (p.sl_mode === 'top3_cnt') {
                    let sortedBySl = [...(kingsSimList || [])].sort((a, b) => (b.sl_usd || b.sl_cnt || 0) - (a.sl_usd || a.sl_cnt || 0));
                    let bad = new Set(sortedBySl.slice(0, 3).map(k => k.kk));
                    simState.enabledKings = new Set((kingsSimList || []).filter(k => !bad.has(k.kk)).map(k => k.kk));
                } else {
                    simState.enabledKings = new Set((kingsSimList || []).map(k => k.kk));
                }

                // 4B. Consecutive Loss Circuit Breaker from Preset
                if (p.consec_trig !== undefined) {
                    simState.consecLossTrigger = p.consec_trig;
                    simState.consecLossSkipCount = p.consec_sk || 1;
                    simState.consecLossSkipDay = !!p.consec_day;
                    if (typeof syncConsecButtonsUI === 'function') syncConsecButtonsUI();
                } else {
                    simState.consecLossTrigger = 0;
                    simState.consecLossSkipCount = 1;
                    simState.consecLossSkipDay = false;
                    if (typeof syncConsecButtonsUI === 'function') syncConsecButtonsUI();
                }

                // 5. Update UI components
                if (typeof renderSimKingsGrid === 'function') renderSimKingsGrid();
                if (typeof renderSimHoursBar === 'function') renderSimHoursBar();

                // 6. Highlight active preset row
                clearPresetActiveState();
                let activeRow = document.getElementById('presetRow' + idx);
                if (activeRow) {
                    activeRow.style.outline = '2px solid #38bdf8';
                    activeRow.style.boxShadow = '0 0 16px rgba(56, 189, 248, 0.4)';
                }
                let activeBtn = document.getElementById('btnApplyPreset' + idx);
                if (activeBtn) {
                    activeBtn.innerHTML = '✅ سناریوی فعال';
                    activeBtn.style.background = 'linear-gradient(135deg, #059669, #10b981)';
                    activeBtn.style.borderColor = '#34d399';
                }

                // 7. Run equity simulation
                if (typeof runEquitySimulation === 'function') runEquitySimulation();

                // 8. Smoothly scroll up to the equity chart
                let eqCanvas = document.getElementById('equityCanvas') || document.getElementById('equityChartSection');
                if (eqCanvas && typeof eqCanvas.scrollIntoView === 'function') {
                    eqCanvas.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }

                // 9. Display prominent toast notification
                if (typeof showSaveNotification === 'function') {
                    showSaveNotification('⚡ سناریوی «' + (p.title || '') + '» با موفقیت روی نمودار اعمال و شبیه‌سازی شد!');
                }
            } catch(err) {
                console.error('Error in applySmartPreset:', err);
                if (typeof alert === 'function') alert('خطا در اعمال سناریو: ' + err.message);
            }
        }


        // ==========================================
        // 💾 CUSTOM PRESETS MANAGEMENT SYSTEM (LOCALSTORAGE)
        // ==========================================
        let customPresetsList = [];

        

function openSavePresetModal() {
            let activeHoursCount = simState.allowedHours.filter(Boolean).length;
            let activeKingsCount = simState.enabledKings.size;

            let elCnt = document.getElementById('eqKpiCnt');
            let elWR = document.getElementById('eqKpiWR');
            let elPF = document.getElementById('eqKpiPF');
            let elAvg = document.getElementById('eqKpiAvgTrade');
            let elMaxDD = document.getElementById('eqKpiMaxDD');
            let elNet = document.getElementById('eqKpiNetVal') || document.getElementById('eqKpiNetSub');

            let tradesStr = elCnt ? elCnt.textContent : '0 معامله';
            let wrStr = elWR ? elWR.textContent : '0%';
            let pfStr = elPF ? elPF.textContent : '0.00';
            let avgStr = elAvg ? elAvg.textContent : '$0.00';
            let ddStr = elMaxDD ? elMaxDD.textContent : '$0.00';
            let netStr = elNet ? elNet.textContent.replace('سود خالص: ', '').replace('سود: ', '') : '$0';

            document.getElementById('modalPreviewMinProfit').textContent = '$' + simState.minProfit.toFixed(2);
            document.getElementById('modalPreviewHours').textContent = activeHoursCount + ' ساعت فعال';
            document.getElementById('modalPreviewKings').textContent = activeKingsCount + ' سلطان فعال';
            document.getElementById('modalPreviewTrades').textContent = tradesStr;
            document.getElementById('modalPreviewWR').textContent = wrStr;
            document.getElementById('modalPreviewPF').textContent = pfStr;
            document.getElementById('modalPreviewAvg').textContent = avgStr;
            document.getElementById('modalPreviewDD').textContent = ddStr;
            document.getElementById('modalPreviewNet').textContent = netStr;

            let titleInput = document.getElementById('modalPresetTitle');
            if (titleInput && !titleInput.value) {
                titleInput.value = 'سناریوی من (' + tradesStr + ' - PF ' + pfStr + ')';
            }

            let modal = document.getElementById('savePresetModal');
            if (modal) modal.style.display = 'flex';
        }

        function closeSavePresetModal() {
            let modal = document.getElementById('savePresetModal');
            if (modal) modal.style.display = 'none';
        }

        function confirmSaveCurrentPreset() {
            let title = document.getElementById('modalPresetTitle').value.trim();
            if (!title) {
                alert('لطفاً یک نام برای این سناریو وارد کنید.');
                return;
            }
            let desc = document.getElementById('modalPresetDesc').value.trim();
            if (!desc) {
                desc = 'کف سود $' + simState.minProfit.toFixed(2) + '، ' + simState.allowedHours.filter(Boolean).length + ' ساعت فعال، ' + simState.enabledKings.size + ' سلطان';
            }

            let newPreset = {
                id: 'custom_' + Date.now(),
                title: title,
                desc: desc,
                min_pot: simState.minProfit,
                hours: [...simState.allowedHours],
                kings: Array.from(simState.enabledKings),
                consec_trig: simState.consecLossTrigger,
                consec_sk: simState.consecLossSkipCount,
                consec_day: simState.consecLossSkipDay,
                createdAt: new Date().toLocaleDateString('fa-IR')
            };

            try {
                let list = JSON.parse(localStorage.getItem('flagpro_custom_presets') || '[]');
                list.unshift(newPreset);
                localStorage.setItem('flagpro_custom_presets', JSON.stringify(list));
            } catch(e) {
                console.error('Failed to save preset to localStorage', e);
            }

            closeSavePresetModal();
            loadCustomPresets();
            alert('✅ سناریوی «' + title + '» با موفقیت ذخیره شد و در لیست سناریوهای شخصی قرار گرفت.');
        }

        function loadCustomPresets() {
            let tbody = document.getElementById('customPresetsTbody');
            if (!tbody) return;

            let list = [];
            try {
                list = JSON.parse(localStorage.getItem('flagpro_custom_presets') || '[]');
            } catch(e) {
                list = [];
            }
            customPresetsList = list;

            let badge = document.getElementById('customPresetsCountBadge');
            if (badge) badge.textContent = list.length + ' سناریو';

            if (list.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:14px;color:#64748b;font-size:11.5px;background:#06101c;">' +
                    '💡 هنوز هیچ سناریوی شخصی ذخیره نکرده‌اید. با زدن دکمه «💾 ذخیره چیدمان»، تنظیمات فعلی ذخیره خواهد شد.' +
                    '</td></tr>';
                return;
            }

            let html = '';
            for (let i = 0; i < list.length; i++) {
                let p = list[i];
                if (!p) continue;
                let pHours = (Array.isArray(p.hours) && p.hours.length === 24) ? p.hours : new Array(24).fill(true);
                let pKings = Array.isArray(p.kings) ? p.kings : [];
                let pMinPot = typeof p.min_pot === 'number' ? p.min_pot : 0;
                let kSet = new Set(pKings);
                let sub = (Array.isArray(simTrades) ? simTrades : []).filter(t => t.k === 1 && kSet.has(t.kk) && t.pot >= pMinPot && pHours[t.h]);
                let c = sub.length;
                let nt = sub.reduce((acc, t) => acc + t.p, 0);
                let wins = sub.filter(t => t.p > 0).length;
                let wr = c > 0 ? (wins / c * 100) : 0;
                let avg = c > 0 ? (nt / c) : 0;
                let gp = sub.filter(t => t.p > 0).reduce((acc, t) => acc + t.p, 0);
                let gl = sub.filter(t => t.p <= 0).reduce((acc, t) => acc + Math.abs(t.p), 0);
                let pf = gl > 0 ? (gp / gl) : 999;

                let bal = 100.0, peak = 100.0, max_dd = 0.0;
                for (let j = 0; j < sub.length; j++) {
                    bal += sub[j].p;
                    if (bal > peak) peak = bal;
                    let dd = peak - bal;
                    if (dd > max_dd) max_dd = dd;
                }

                let netCol = nt >= 0 ? '#00e676' : '#ef4444';
                let pfStr = pf < 900 ? pf.toFixed(2) : '∞';
                let hoursCnt = pHours.filter(Boolean).length;

                html += '<tr id="customRow_' + p.id + '" class="preset-table-row" style="border-bottom:1px solid #1e293b;background:#0c192c;transition:all 0.2s;">' +
                    '<td style="text-align:center;padding:7px 4px;font-weight:bold;color:#38bdf8;font-size:12px;">⭐ ' + (i + 1) + '</td>' +
                    '<td style="padding:7px 8px;">' +
                        '<div style="font-weight:bold;color:#f1f5f9;font-size:12px;display:flex;align-items:center;gap:4px;">' +
                            '<span>' + p.title + '</span>' +
                            '<span style="background:#1e3a8a;color:#93c5fd;font-size:9.5px;padding:1px 5px;border-radius:4px;font-weight:bold;">سفارشی</span>' +
                        '</div>' +
                        '<div style="color:#94a3b8;font-size:10.5px;margin-top:2px;">' + p.desc + '</div>' +
                    '</td>' +
                    '<td style="padding:7px 6px;font-size:11px;color:#cbd5e1;text-align:center;white-space:nowrap;">' +
                        '<div>کف سود: <b>$' + p.min_pot.toFixed(2) + '</b> | ' + hoursCnt + ' ساعت</div>' +
                        '<div style="font-weight:bold;color:#facc15;font-size:10.5px;margin-top:2px;">👑 ' + p.kings.length + ' سلطان فعال</div>' +
                    '</td>' +
                    '<td style="text-align:center;padding:7px 4px;font-weight:bold;font-size:12px;color:#e2e8f0;">' +
                        c.toLocaleString() +
                    '</td>' +
                    '<td style="text-align:center;padding:7px 4px;font-weight:bold;color:#34d399;font-size:12px;">' +
                        wr.toFixed(1) + '٪' +
                    '</td>' +
                    '<td style="text-align:center;padding:7px 4px;font-weight:bold;color:#38bdf8;font-size:12.5px;">' +
                        pfStr +
                    '</td>' +
                    '<td style="text-align:center;padding:7px 4px;font-weight:bold;color:#facc15;font-size:12.5px;">' +
                        '$' + avg.toFixed(2) +
                    '</td>' +
                    '<td style="text-align:center;padding:7px 4px;font-weight:bold;color:#fca5a5;font-size:11.5px;">' +
                        '$' + Math.round(max_dd).toLocaleString() +
                    '</td>' +
                    '<td style="text-align:center;padding:7px 6px;font-weight:bold;color:' + netCol + ';font-size:13.5px;background:#064e3b22;white-space:nowrap;">' +
                        (nt >= 0 ? '+' : '') + '$' + Math.round(nt).toLocaleString() +
                    '</td>' +
                    '<td style="text-align:center;padding:7px 6px;white-space:nowrap;">' +
                        '<div style="display:flex;gap:3px;justify-content:center;align-items:center;flex-wrap:nowrap;">' +
                            '<button data-id="' + p.id + '" onclick="applyCustomPreset(this.dataset.id)" style="background:linear-gradient(135deg, #0284c7, #0369a1);border:1px solid #38bdf8;color:#fff;padding:4px 7px;border-radius:4px;font-size:11px;cursor:pointer;font-weight:bold;" title="اعمال روی چارت">⚡ اعمال</button>' +
                            '<button data-id="' + p.id + '" onclick="exportCustomPresetToMT5(this.dataset.id)" style="background:linear-gradient(135deg, #065f46, #047857);border:1px solid #34d399;color:#ecfdf5;padding:4px 7px;border-radius:4px;font-size:11px;cursor:pointer;font-weight:bold;display:inline-flex;align-items:center;gap:3px;" title="دریافت فایل استراتژی تستر متاتریدر ۵ (.ini) جهت Drag & Drop">' +
                                '<span>🤖 تنظیمات تستر (.ini)</span>' +
                            '</button>' +
                            '<button data-id="' + p.id + '" onclick="updateCustomPresetWithCurrent(this.dataset.id)" style="background:#1e293b;border:1px solid #ca8a04;color:#fef08a;padding:4px 5px;border-radius:4px;font-size:10.5px;cursor:pointer;" title="به‌روزرسانی این سناریو با فیلترهای فعلی">🔄</button>' +
                            '<button data-id="' + p.id + '" onclick="deleteCustomPreset(this.dataset.id)" style="background:#450a0a;border:1px solid #dc2626;color:#fca5a5;padding:4px 5px;border-radius:4px;font-size:10.5px;cursor:pointer;" title="حذف سناریو">🗑️</button>' +
                        '</div>' +
                    '</td>' +
                '</tr>';
            }
            tbody.innerHTML = html;
        }

        function applyCustomPreset(id) {
            let p = customPresetsList.find(x => x.id === id);
            if (!p) return;

            simState.mode = 'kings';
            let btnK = document.getElementById('btnEqKings');
            let btnA = document.getElementById('btnEqAll');
            if (btnK) btnK.classList.add('active');
            if (btnA) btnA.classList.remove('active');

            // 1. Min profit
            simState.minProfit = p.min_pot;
            let slider = document.getElementById('simProfitSlider');
            if (slider) slider.value = p.min_pot;
            let sliderVal = document.getElementById('simProfitSliderVal');
            if (sliderVal) sliderVal.textContent = '$' + p.min_pot.toFixed(2);
            let pBadge = document.getElementById('simProfitBadge');
            if (pBadge) {
                pBadge.textContent = (p.min_pot === 0) ? 'بدون فیلتر ($0)' : 'حداقل $' + p.min_pot.toFixed(2);
                pBadge.style.background = (p.min_pot === 0) ? '#064e3b' : '#0369a1';
            }

            document.querySelectorAll('.profit-preset-btn').forEach(b => {
                b.classList.remove('active');
                if (parseFloat(b.dataset.val) === p.min_pot) b.classList.add('active');
            });

            // 2. Allowed Hours
            simState.allowedHours = [...p.hours];
            document.querySelectorAll('.hour-preset-btn').forEach(b => b.classList.remove('active'));

            // 3. Enabled Kings
            simState.enabledKings = new Set(p.kings);

            // 4. Update UI
            // 4. Consecutive Loss Filter
            if (p.consec_trig !== undefined) {
                simState.consecLossTrigger = p.consec_trig;
                simState.consecLossSkipCount = p.consec_sk || 1;
                simState.consecLossSkipDay = !!p.consec_day;
                syncConsecButtonsUI();
            }

            renderSimKingsGrid();
            renderSimHoursBar();

            // 5. Highlight active row
            clearPresetActiveState();
            let row = document.getElementById('customRow_' + p.id);
            if (row) {
                row.style.outline = '2px solid #38bdf8';
                row.style.boxShadow = '0 0 16px rgba(56, 189, 248, 0.4)';
            }

            // 6. Run equity simulation
            runEquitySimulation();

            // 7. Auto-scroll up to equity chart
            let eqCanvas = document.getElementById('equityCanvas') || document.getElementById('equityChartSection');
            if (eqCanvas) {
                eqCanvas.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }

            // 8. Toast notification
            if (typeof showSaveNotification === 'function') {
                showSaveNotification('⚡ سناریوی شخصی «' + (p.title || '') + '» روی چارت اکوئیتی اعمال شد!');
            }
        }

        function updateCustomPresetWithCurrent(id) {
            let p = customPresetsList.find(x => x.id === id);
            if (!p) return;
            if (!confirm('آیا مایلید سناریوی «' + p.title + '» با تنظیمات فعلی فیلترهای چارت بازنویسی و بروزرسانی شود؟')) return;

            p.min_pot = simState.minProfit;
            p.hours = [...simState.allowedHours];
            p.kings = Array.from(simState.enabledKings);
            p.consec_trig = simState.consecLossTrigger;
            p.consec_sk = simState.consecLossSkipCount;
            p.consec_day = simState.consecLossSkipDay;
            p.updatedAt = new Date().toLocaleDateString('fa-IR');

            try {
                localStorage.setItem('flagpro_custom_presets', JSON.stringify(customPresetsList));
            } catch(e) {
                console.error(e);
            }
            loadCustomPresets();
            alert('✅ سناریوی «' + p.title + '» با موفقیت با تنظیمات فعلی بروز شد.');
        }

        function deleteCustomPreset(id) {
            let p = customPresetsList.find(x => x.id === id);
            if (!p) return;
            if (!confirm('آیا از حذف سناریوی «' + p.title + '» اطمینان دارید؟')) return;

            customPresetsList = customPresetsList.filter(x => x.id !== id);
            try {
                localStorage.setItem('flagpro_custom_presets', JSON.stringify(customPresetsList));
            } catch(e) {
                console.error(e);
            }
            loadCustomPresets();
        }

        function exportCustomPresets() {
            let list = [];
            try {
                list = JSON.parse(localStorage.getItem('flagpro_custom_presets') || '[]');
            } catch(e) {}

            if (list.length === 0) {
                alert('سناریوی ذخیره‌شده‌ای برای خروجی گرفتن وجود ندارد.');
                return;
            }

            let dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(list, null, 2));
            let dlAnchor = document.createElement('a');
            dlAnchor.setAttribute('href', dataStr);
            dlAnchor.setAttribute('download', 'flagpro_custom_presets.json');
            document.body.appendChild(dlAnchor);
            dlAnchor.click();
            dlAnchor.remove();
        }

        function importCustomPresets(event) {
            let file = event.target.files[0];
            if (!file) return;

            let reader = new FileReader();
            reader.onload = function(e) {
                try {
                    let imported = JSON.parse(e.target.result);
                    if (!Array.isArray(imported)) throw new Error('فایل معتبر نیست.');

                    let current = JSON.parse(localStorage.getItem('flagpro_custom_presets') || '[]');
                    let merged = [...imported, ...current];
                    // unique by id
                    let map = new Map();
                    merged.forEach(item => map.set(item.id, item));
                    let finalList = Array.from(map.values());

                    localStorage.setItem('flagpro_custom_presets', JSON.stringify(finalList));
                    loadCustomPresets();
                    alert('✅ تعداد ' + imported.length + ' سناریو با موفقیت از فایل وارد شدند.');
                } catch(err) {
                    alert('خطا در بارگذاری فایل سناریوها: ' + err.message);
                }
            };
            reader.readAsText(file);
            event.target.value = '';
        }

        function initSimUI() {
            renderSimKingsGrid();
            renderSimHoursBar();
            loadCustomPresets();
            runEquitySimulation();
        }

        function renderSimKingsGrid() {
            let grid = document.getElementById('simKingsGrid');
            if (!grid) return;
            let html = '';
            for (let i = 0; i < kingsSimList.length; i++) {
                let k = kingsSimList[i];
                let isEnabled = simState.enabledKings.has(k.kk);
                let isDanger = k.is_danger === 1;

                let bg = isEnabled ? (isDanger ? '#240a0a' : '#0c2742') : '#081420';
                let border = isEnabled 
                    ? (isDanger ? 'border:1px solid #ef4444;box-shadow:0 0 8px rgba(239,68,68,0.3);' 
                      : (k.perf ? 'border:1px solid #facc15;' : 'border:1px solid #0284c7;')) 
                    : 'border:1px solid #1e293b;opacity:0.38;';
                let checkIcon = isEnabled ? (isDanger ? '🛑' : '☑️') : '⬜';
                let medal = isDanger ? '⚠️' : (k.perf ? '💎' : (k.run ? '🚀' : '👑'));
                let netCol = k.net >= 0 ? '#34d399' : '#f87171';
                let netSign = k.net >= 0 ? '+' : '';

                let slBadge = isDanger 
                    ? '<span style="background:#7f1d1d;color:#fecaca;font-size:9.5px;padding:1px 5px;border-radius:3px;font-weight:bold;margin-left:4px;" title="تعداد استاپ: ' + k.sl_cnt + ' (' + k.sl_p + '٪) | زیان استاپ‌ها: -$' + k.sl_usd + '">🛑 ' + k.sl_cnt + ' باخت</span>' 
                    : '';

                let disabledText = !isEnabled ? '<span style="color:#64748b;font-size:10px;margin-right:4px;">(حذف شده)</span>' : '';

                html += '<div data-kk="' + k.kk + '" onclick="toggleSimKing(this.dataset.kk)" style="' + bg + ';' + border + 'padding:6px 10px;border-radius:6px;cursor:pointer;user-select:none;transition:all 0.15s;display:flex;justify-content:space-between;align-items:center;">' +
                    '<div style="display:flex;align-items:center;gap:5px;overflow:hidden;">' +
                        '<span style="font-size:13px;">' + checkIcon + '</span>' +
                        '<span style="font-size:11px;">' + medal + '</span>' +
                        '<span style="font-size:11.5px;color:#e2e8f0;font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="' + k.role + ' [' + k.tf + ']">' + k.role + '</span>' +
                        '<span style="background:#1e293b;color:#93c5fd;font-size:9.5px;padding:1px 5px;border-radius:3px;font-weight:bold;">' + k.tf + '</span>' +
                        slBadge +
                    '</div>' +
                    '<div style="text-align:left;font-size:11px;font-family:monospace;white-space:nowrap;display:flex;align-items:center;">' +
                        disabledText +
                        '<span style="color:' + netCol + ';font-weight:bold;">$' + netSign + k.net.toFixed(0) + '</span>' +
                        '<span style="color:#64748b;font-size:9.5px;margin-right:4px;">(' + k.cnt + ')</span>' +
                    '</div>' +
                '</div>';
            }
            grid.innerHTML = html;

            let lbl = document.getElementById('simKingsCountLabel');
            if (lbl) {
                let activeCnt = simState.enabledKings.size;
                let totCnt = kingsSimList.length;
                lbl.textContent = activeCnt + ' از ' + totCnt + ' سلطان فعال';
                lbl.style.background = (activeCnt === totCnt) ? '#854d0e' : (activeCnt > 0 ? '#0284c7' : '#450a0a');
            }
            renderSLRiskPanel();
        }

        function renderSLRiskPanel() {
            let container = document.getElementById('slTop3CardsContainer');
            if (!container) return;

            let featuredKeys = ['Flag-BE|M1', 'Flag-BU|M1', 'OInner-BU|M1', 'S-RS|M1'];
            let html = '';

            for (let i = 0; i < featuredKeys.length; i++) {
                let kk = featuredKeys[i];
                let k = kingsSimList.find(x => x.kk === kk);
                if (!k) continue;

                let isEnabled = simState.enabledKings.has(k.kk);
                let cardBg = isEnabled ? 'rgba(239, 68, 68, 0.09)' : '#0f172a';
                let cardBorder = isEnabled ? '1px solid #ef4444' : '1px solid #334155';
                let statusBadge = isEnabled 
                    ? '<span style="background:#450a0a;color:#fca5a5;font-size:10px;padding:2px 6px;border-radius:4px;border:1px solid #7f1d1d;font-weight:bold;">🟢 فعال در سبد</span>'
                    : '<span style="background:#1e293b;color:#94a3b8;font-size:10px;padding:2px 6px;border-radius:4px;border:1px solid #334155;font-weight:bold;">🔴 حذف شده</span>';

                let btnHtml = isEnabled
                    ? '<button data-kk="' + k.kk + '" onclick="toggleSimKing(this.dataset.kk)" style="background:#dc2626;border:1px solid #ef4444;color:#fff;font-size:11px;padding:5px 12px;border-radius:5px;cursor:pointer;font-weight:bold;white-space:nowrap;box-shadow:0 2px 6px rgba(220,38,38,0.3);">❌ حذف این سلطان</button>'
                    : '<button data-kk="' + k.kk + '" onclick="toggleSimKing(this.dataset.kk)" style="background:#065f46;border:1px solid #10b981;color:#a7f3d0;font-size:11px;padding:5px 12px;border-radius:5px;cursor:pointer;font-weight:bold;white-space:nowrap;box-shadow:0 2px 6px rgba(16,185,129,0.3);">➕ بازگردانی به سبد</button>';

                let tagRank = (i === 3) ? '⚠️ بالاترین نرخ باخت (۴۹.۵٪)' : ('#' + (i + 1) + ' بیشترین استاپ چارت');
                let tagCol = (i === 3) ? '#c084fc' : '#f87171';

                html += '<div style="background:' + cardBg + ';border:' + cardBorder + ';border-radius:8px;padding:10px 12px;display:flex;justify-content:space-between;align-items:center;transition:all 0.2s;">' +
                    '<div>' +
                        '<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;flex-wrap:wrap;">' +
                            '<span style="background:#260d0d;color:' + tagCol + ';font-size:10px;font-weight:bold;padding:1px 6px;border-radius:4px;border:1px solid #450a0a;">' + tagRank + '</span>' +
                            '<span style="font-weight:bold;color:#f1f5f9;font-size:13px;">' + k.role + '</span>' +
                            '<span style="background:#1e293b;color:#93c5fd;font-size:9.5px;padding:1px 5px;border-radius:3px;font-weight:bold;">' + k.tf + '</span>' +
                            statusBadge +
                        '</div>' +
                        '<div style="font-size:11px;color:#fca5a5;margin-bottom:2px;">' +
                            '🛑 <b>' + k.sl_cnt + ' استاپ</b> (' + k.sl_p + '٪ باخت) | زیان استاپ‌ها: <b style="color:#ef4444;">-$' + k.sl_usd.toFixed(2) + '</b>' +
                        '</div>' +
                        '<div style="font-size:10.5px;color:#94a3b8;">' +
                            'کل معاملات: ' + k.cnt + ' | سود خالص کل: <span style="color:#34d399;font-weight:bold;">+$' + k.net.toFixed(2) + '</span>' +
                        '</div>' +
                    '</div>' +
                    '<div>' + btnHtml + '</div>' +
                '</div>';
            }
            container.innerHTML = html;

            let btnCnt = document.getElementById('btnRemoveTop3Cnt');
            if (btnCnt) {
                let top3Active = top3SLCntKeys.some(kk => simState.enabledKings.has(kk));
                btnCnt.innerHTML = top3Active ? '🚫 حذف ۳ سلطان با بیشترین استاپ (تعداد)' : '✅ ۳ سلطان حذف شدند (کلیک برای بازگردانی)';
                btnCnt.style.background = top3Active ? '#7f1d1d' : '#065f46';
                btnCnt.style.borderColor = top3Active ? '#ef4444' : '#10b981';
            }

            let btnUsd = document.getElementById('btnRemoveTop3Usd');
            if (btnUsd) {
                let top3Active = top3SLUsdKeys.some(kk => simState.enabledKings.has(kk));
                btnUsd.innerHTML = top3Active ? '💸 حذف ۳ سلطان با بیشترین زیان دلاری' : '✅ ۳ سلطان حذف شدند (کلیک برای بازگردانی)';
                btnUsd.style.background = top3Active ? '#450a0a' : '#065f46';
                btnUsd.style.borderColor = top3Active ? '#dc2626' : '#10b981';
            }

            let btnRate = document.getElementById('btnRemoveWorstRate');
            if (btnRate) {
                let worstActive = top3SLPctKeys.some(kk => simState.enabledKings.has(kk));
                btnRate.innerHTML = worstActive ? '🛡️ حذف سلاطین کم‌دقت (باخت > ۴۵٪)' : '✅ سلاطین کم‌دقت حذف شدند (بازگردانی)';
                btnRate.style.background = worstActive ? '#3b0764' : '#065f46';
                btnRate.style.borderColor = worstActive ? '#a855f7' : '#10b981';
            }
        }

        function toggleTop3SL(mode) {
            clearPresetActiveState();
            let keys = (mode === 'usd') ? top3SLUsdKeys : top3SLCntKeys;
            let anyActive = keys.some(kk => simState.enabledKings.has(kk));
            if (anyActive) {
                keys.forEach(kk => simState.enabledKings.delete(kk));
            } else {
                keys.forEach(kk => simState.enabledKings.add(kk));
            }
            renderSimKingsGrid();
            runEquitySimulation();
        }

        function toggleWorstRateKings() {
            clearPresetActiveState();
            let keys = top3SLPctKeys;
            let anyActive = keys.some(kk => simState.enabledKings.has(kk));
            if (anyActive) {
                keys.forEach(kk => simState.enabledKings.delete(kk));
            } else {
                keys.forEach(kk => simState.enabledKings.add(kk));
            }
            renderSimKingsGrid();
            runEquitySimulation();
        }

        function toggleSimKing(kk) {
            clearPresetActiveState();
            if (simState.enabledKings.has(kk)) {
                simState.enabledKings.delete(kk);
            } else {
                simState.enabledKings.add(kk);
            }
            renderSimKingsGrid();
            runEquitySimulation();
        }

        function selectAllKings(enableAll) {
            clearPresetActiveState();
            if (enableAll) {
                kingsSimList.forEach(k => simState.enabledKings.add(k.kk));
            } else {
                simState.enabledKings.clear();
            }
            renderSimKingsGrid();
            runEquitySimulation();
        }

        function selectOnlyPerfectKings() {
            clearPresetActiveState();
            simState.enabledKings.clear();
            kingsSimList.forEach(k => {
                if (k.perf === 1) simState.enabledKings.add(k.kk);
            });
            renderSimKingsGrid();
            runEquitySimulation();
        }

        function selectOnlyRunnerKings() {
            clearPresetActiveState();
            simState.enabledKings.clear();
            kingsSimList.forEach(k => {
                if (k.run === 1) simState.enabledKings.add(k.kk);
            });
            renderSimKingsGrid();
            runEquitySimulation();
        }

        function renderSimHoursBar() {
            let bar = document.getElementById('simHoursBar');
            if (!bar) return;
            let html = '';
            let activeCount = 0;
            for (let h = 0; h < 24; h++) {
                let on = simState.allowedHours[h];
                if (on) activeCount++;
                let bg = on ? '#0c4a6e' : '#111827';
                let border = on ? 'border:1px solid #0284c7;' : 'border:1px solid #1f2937;';
                let col = on ? '#7dd3fc' : '#475569';
                let decor = on ? '' : 'text-decoration:line-through;opacity:0.5;';
                let hStr = (h < 10 ? '0' : '') + h;

                html += '<button onclick="toggleHour(' + h + ')" style="' + bg + ';' + border + 'color:' + col + ';' + decor + 'font-family:monospace;font-size:10px;padding:5px 2px;border-radius:4px;cursor:pointer;font-weight:bold;" title="ساعت ' + hStr + ':00">' + hStr + '</button>';
            }
            bar.innerHTML = html;

            let badge = document.getElementById('simHoursActiveBadge');
            if (badge) {
                badge.textContent = activeCount + ' ساعت فعال (' + (24 - activeCount) + ' فیلتر)';
                badge.style.background = (activeCount === 24) ? '#0c4a6e' : (activeCount > 0 ? '#065f46' : '#450a0a');
            }
        }

        function toggleHour(h) {
            clearPresetActiveState();
            simState.allowedHours[h] = !simState.allowedHours[h];
            renderSimHoursBar();
            document.querySelectorAll('.hour-preset-btn').forEach(b => b.classList.remove('active'));
            runEquitySimulation();
        }

        function applyHourPreset(preset, btnElem) {
            clearPresetActiveState();
            document.querySelectorAll('.hour-preset-btn').forEach(b => b.classList.remove('active'));
            if (btnElem) btnElem.classList.add('active');

            if (preset === 'all') {
                simState.allowedHours.fill(true);
            } else if (preset === 'no_night') {
                simState.allowedHours.fill(true);
                let night = [22, 23, 0, 1, 2, 3];
                night.forEach(h => simState.allowedHours[h] = false);
            } else if (preset === 'lon_ny') {
                for (let h = 0; h < 24; h++) {
                    simState.allowedHours[h] = (h >= 7 && h < 20);
                }
            } else if (preset === 'asia') {
                for (let h = 0; h < 24; h++) {
                    simState.allowedHours[h] = (h >= 0 && h < 8);
                }
            }
            renderSimHoursBar();
            runEquitySimulation();
        }

        function applyProfitPreset(val, btnElem) {
            clearPresetActiveState();
            simState.minProfit = val;
            let slider = document.getElementById('simProfitSlider');
            if (slider) slider.value = val;
            let sliderVal = document.getElementById('simProfitSliderVal');
            if (sliderVal) sliderVal.textContent = '$' + val.toFixed(2);
            let badge = document.getElementById('simProfitBadge');
            if (badge) {
                badge.textContent = (val === 0) ? 'بدون فیلتر ($0)' : 'حداقل $' + val.toFixed(2);
                badge.style.background = (val === 0) ? '#064e3b' : '#0369a1';
            }

            document.querySelectorAll('.profit-preset-btn').forEach(b => b.classList.remove('active'));
            if (btnElem) btnElem.classList.add('active');
            runEquitySimulation();
        }

        function onProfitSliderInput(val) {
            clearPresetActiveState();
            let num = parseFloat(val) || 0.0;
            simState.minProfit = num;
            let sliderVal = document.getElementById('simProfitSliderVal');
            if (sliderVal) sliderVal.textContent = '$' + num.toFixed(2);
            let badge = document.getElementById('simProfitBadge');
            if (badge) {
                badge.textContent = (num === 0) ? 'بدون فیلتر ($0)' : 'حداقل $' + num.toFixed(2);
                badge.style.background = (num === 0) ? '#064e3b' : '#0369a1';
            }
            document.querySelectorAll('.profit-preset-btn').forEach(b => b.classList.remove('active'));
            runEquitySimulation();
        }

        function resetAllSimFilters() {
            clearPresetActiveState();
            simState.mode = 'kings';
            kingsSimList.forEach(k => simState.enabledKings.add(k.kk));
            simState.allowedHours.fill(true);
            simState.minProfit = 0.0;

            let slider = document.getElementById('simProfitSlider');
            if (slider) slider.value = 0;
            let sliderVal = document.getElementById('simProfitSliderVal');
            if (sliderVal) sliderVal.textContent = '$0.00';
            let badge = document.getElementById('simProfitBadge');
            if (badge) {
                badge.textContent = 'بدون فیلتر ($0)';
                badge.style.background = '#064e3b';
            }

            document.querySelectorAll('.hour-preset-btn').forEach(b => b.classList.remove('active'));
            let btnHAll = document.getElementById('btnHAll');
            if (btnHAll) btnHAll.classList.add('active');

            document.querySelectorAll('.profit-preset-btn').forEach(b => b.classList.remove('active'));
            let firstProf = document.querySelector('.profit-preset-btn');
            if (firstProf) firstProf.classList.add('active');

            let btnK = document.getElementById('btnEqKings');
            let btnA = document.getElementById('btnEqAll');
            if (btnK) btnK.classList.add('active');
            if (btnA) btnA.classList.remove('active');

            simState.consecLossTrigger = 0;
            simState.consecLossSkipCount = 1;
            simState.consecLossSkipDay = false;
            let selTrig = document.getElementById('selConsecTrigger');
            if (selTrig) selTrig.value = 0;
            let selAct = document.getElementById('selConsecAction');
            if (selAct) selAct.value = 'skip_1';
            syncConsecButtonsUI();

            renderSimKingsGrid();
            renderSimHoursBar();
            runEquitySimulation();
        }

        function switchEquityMode(mode) {
            simState.mode = mode;
            let btnK = document.getElementById('btnEqKings');
            let btnA = document.getElementById('btnEqAll');
            if(mode === 'kings') {
                if(btnK) btnK.classList.add('active');
                if(btnA) btnA.classList.remove('active');
            } else {
                if(btnK) btnK.classList.remove('active');
                if(btnA) btnA.classList.add('active');
            }
            runEquitySimulation();
        }

        function runEquitySimulation() {
            let t_init = (simTrades.length > 0 && simTrades[0].t) ? simTrades[0].t : '2025.01.01 00:00';
            let pts = [{ idx: 0, t: t_init, b: 100.0, p: 0.0, n: 'موجودی اولیه (Initial Balance)', peak: 100.0, dd: 0.0, ddPct: 0.0 }];
            let bal = 100.0;
            let peak = bal;
            let maxDD = 0.0;
            let winCnt = 0;
            let totalTrades = 0;
            let grossP = 0.0;
            let grossL = 0.0;
            let baseTotal = 0;

            let consecLoss = 0;
            let skipsLeft = 0;
            let lastSkipDay = '';
            let consecSkippedCount = 0;
            let consecSavedLosses = 0;
            let consecMissedWins = 0;

            let maxConsecLoss = 0;
            let maxConsecWin = 0;
            let curConsecWin = 0;
            let curLossStreak = 0;
            let lossStreaks = [];

            let maxConcurrent = 0;
            let sumConcurrent = 0;
            let activeOpenExits = [];

            for (let i = 0; i < simTrades.length; i++) {
                let t = simTrades[i];
                let isMatchBase = (simState.mode === 'kings') ? (t.k === 1) : true;
                if (!isMatchBase) continue;
                baseTotal++;

                // King filter
                if (simState.mode === 'kings' && !simState.enabledKings.has(t.kk)) continue;

                // Hour filter
                if (!simState.allowedHours[t.h]) continue;

                // Min profit filter
                if (t.pot < simState.minProfit) continue;

                // Consecutive loss circuit breaker filter
                let tradeDate = t.t ? t.t.substring(0, 10) : '';
                if (simState.consecLossTrigger > 0) {
                    if (simState.consecLossSkipDay && lastSkipDay === tradeDate) {
                        consecSkippedCount++;
                        if (t.p <= 0) consecSavedLosses++; else consecMissedWins++;
                        continue;
                    }
                    if (skipsLeft > 0) {
                        skipsLeft--;
                        consecSkippedCount++;
                        if (t.p <= 0) consecSavedLosses++; else consecMissedWins++;
                        continue;
                    }
                }

                // Trade accepted!
                let enTime = t.t || '';
                let exTime = t.xt || t.t || '';
                if (!exTime || exTime <= enTime) {
                    exTime = enTime + "z";
                }
                activeOpenExits = activeOpenExits.filter(ex => ex > enTime);
                activeOpenExits.push(exTime);
                let curConcurrent = activeOpenExits.length;
                if (curConcurrent > maxConcurrent) maxConcurrent = curConcurrent;
                sumConcurrent += curConcurrent;

                totalTrades++;
                bal += t.p;
                if (bal > peak) peak = bal;
                let dd = peak - bal;
                if (dd > maxDD) maxDD = dd;
                let ddPct = peak > 0 ? (dd / peak * 100) : 0;
                pts.push({ idx: totalTrades, t: t.t, b: Math.round(bal * 100) / 100, p: t.p, n: t.r + ' [' + t.tf + ']', peak: Math.round(peak * 100) / 100, dd: Math.round(dd * 100) / 100, ddPct: Math.round(ddPct * 10) / 10, concurrent: curConcurrent });
                if (t.p > 0) {
                    winCnt++;
                    grossP += t.p;
                    curConsecWin++;
                    if (curConsecWin > maxConsecWin) maxConsecWin = curConsecWin;
                    if (curLossStreak > 0) {
                        lossStreaks.push(curLossStreak);
                        curLossStreak = 0;
                    }
                    consecLoss = 0;
                } else {
                    grossL += Math.abs(t.p);
                    curConsecWin = 0;
                    curLossStreak++;
                    if (curLossStreak > maxConsecLoss) maxConsecLoss = curLossStreak;
                    consecLoss++;
                    if (simState.consecLossTrigger > 0 && consecLoss >= simState.consecLossTrigger) {
                        if (simState.consecLossSkipDay) {
                            lastSkipDay = tradeDate;
                        } else {
                            skipsLeft = simState.consecLossSkipCount;
                        }
                        consecLoss = 0;
                    }
                }
            }

            if (curLossStreak > 0) {
                lossStreaks.push(curLossStreak);
            }

            let streakDist = {};
            for (let s of lossStreaks) {
                streakDist[s] = (streakDist[s] || 0) + 1;
            }
            let totalLossStreaks = lossStreaks.length;
            let avgLossStreak = totalLossStreaks > 0 ? (lossStreaks.reduce((a, b) => a + b, 0) / totalLossStreaks) : 0;

            let net = bal - 100.0;
            let netPct = (net / 100.0) * 100;
            let maxDDPct = peak > 0 ? ((maxDD / peak) * 100) : 0;
            let pf = grossL > 0 ? (grossP / grossL) : (grossP > 0 ? 999.0 : 1.0);
            let wr = totalTrades > 0 ? ((winCnt / totalTrades) * 100) : 0;
            let avgTrade = totalTrades > 0 ? (net / totalTrades) : 0;

            // Update KPI Banner
            let elNetVal = document.getElementById('eqKpiNetVal');
            let elNetSub = document.getElementById('eqKpiNetSub');
            let elBal = document.getElementById('eqKpiFinalBal');
            let elPeak = document.getElementById('eqKpiPeak');
            let elPeakSub = document.getElementById('eqKpiPeakSub');
            let elMaxDD = document.getElementById('eqKpiMaxDD');
            let elMaxDDSub = document.getElementById('eqKpiMaxDDSub');
            let elPF = document.getElementById('eqKpiPF');
            let elWR = document.getElementById('eqKpiWR');
            let elCnt = document.getElementById('eqKpiCnt');
            let elAvg = document.getElementById('eqKpiAvgTrade');

            if (elNetVal) {
                let sign = net >= 0 ? '+' : '-';
                elNetVal.textContent = sign + '$' + Math.abs(Math.round(net)).toLocaleString('en-US');
                elNetVal.style.color = net >= 0 ? '#00e676' : '#ef4444';
            }
            if (elNetSub) {
                let sign = netPct >= 0 ? '+' : '';
                elNetSub.textContent = 'نرخ رشد حساب: ' + sign + netPct.toFixed(1) + '٪';
            }
            if (elBal) {
                elBal.textContent = '$' + Math.round(bal).toLocaleString('en-US');
                elBal.style.color = bal >= 100 ? '#facc15' : '#ef4444';
            }
            if (elPeakSub) {
                elPeakSub.textContent = 'سقف سرمایه: $' + Math.round(peak).toLocaleString('en-US');
            }
            if (elPeak) elPeak.textContent = '$' + Math.round(peak).toLocaleString('en-US');
            if (elMaxDD) elMaxDD.textContent = '$' + Math.round(maxDD).toLocaleString('en-US') + ' (' + maxDDPct.toFixed(1) + '٪)';
            if (elMaxDDSub) elMaxDDSub.textContent = 'افت از سقف $' + Math.round(peak).toLocaleString('en-US');
            if (elPF) elPF.textContent = pf >= 900 ? '∞ قطعی' : pf.toFixed(2);
            if (elWR) elWR.textContent = wr.toFixed(1) + '٪ (' + winCnt + ' برد)';
            if (elCnt) elCnt.textContent = totalTrades.toLocaleString() + ' معامله';
            if (elAvg) {
                let aSign = avgTrade >= 0 ? '+' : '';
                elAvg.textContent = '$' + aSign + avgTrade.toFixed(2);
                elAvg.style.color = avgTrade >= 0 ? '#38bdf8' : '#f87171';
            }

            let avgConcurrent = totalTrades > 0 ? (sumConcurrent / totalTrades) : 0;
            let elMaxConc = document.getElementById('lblMaxConcurrentTrades');
            let elAvgConc = document.getElementById('lblAvgConcurrentTrades');
            let elKpiConcVal = document.getElementById('eqKpiConcVal');
            let elKpiConcSub = document.getElementById('eqKpiConcSub');
            if (elMaxConc) elMaxConc.textContent = maxConcurrent;
            if (elAvgConc) elAvgConc.textContent = avgConcurrent.toFixed(1);
            if (elKpiConcVal) elKpiConcVal.textContent = maxConcurrent + ' معامله';
            if (elKpiConcSub) elKpiConcSub.textContent = 'میانگین: ' + avgConcurrent.toFixed(1) + ' همزمان';

            // Update Simulator Footer Status
            let elAct = document.getElementById('simActiveTradesCount');
            let elBase = document.getElementById('simTotalBaseCount');
            let elFilt = document.getElementById('simFilteredOutCount');
            let elWrVal = document.getElementById('simWinRateVal');
            let elPfVal = document.getElementById('simPfVal');

            if (elAct) elAct.textContent = totalTrades.toLocaleString();
            if (elBase) elBase.textContent = baseTotal.toLocaleString();
            if (elFilt) {
                let diff = baseTotal - totalTrades;
                elFilt.textContent = diff.toLocaleString() + ' معامله حذف شده';
            }
            if (elWrVal) elWrVal.textContent = wr.toFixed(1) + '٪';
            if (elPfVal) elPfVal.textContent = pf >= 900 ? '∞ قطعی' : pf.toFixed(2);

            let lbl = document.getElementById('lblEqPts');
            if (lbl) lbl.textContent = Math.max(0, pts.length - 1);

            let elStartSub = document.getElementById('eqKpiStartSub');
            let elDateRange = document.getElementById('lblEqDateRange');
            let startDate = (simTrades && simTrades.length > 0 && simTrades[0].t) ? simTrades[0].t.substring(0, 10) : '2025.01.02';
            let endDate = (simTrades && simTrades.length > 0 && simTrades[simTrades.length - 1].t) ? simTrades[simTrades.length - 1].t.substring(0, 10) : '2026.09.04';
            if (elStartSub) elStartSub.textContent = 'شروع از ' + startDate;
            if (elDateRange) elDateRange.textContent = startDate + ' تا ' + endDate;

            if (elMaxDDSub) elMaxDDSub.textContent = 'افت از سقف | سقف باخت: ' + maxConsecLoss + ' ترید';

            updateConsecutiveLossUI(maxConsecLoss, maxConsecWin, totalLossStreaks, avgLossStreak, streakDist, consecSkippedCount, consecSavedLosses, consecMissedWins, maxDD);

            currentSimPts = pts;
            drawEquityChart();
            requestAnimationFrame(() => { drawEquityChart(); });
        }

        function drawEquityChart() {
            let canvas = document.getElementById('equityCanvas');
            if (!canvas) return;
            let ctx = canvas.getContext('2d');
            if (!ctx) return;

            let dpr = window.devicePixelRatio || 1;
            let rect = canvas.getBoundingClientRect();
            let w = rect.width || canvas.offsetWidth || canvas.clientWidth || (canvas.parentElement ? canvas.parentElement.clientWidth : 0);
            let h = rect.height || canvas.offsetHeight || canvas.clientHeight || (canvas.parentElement ? canvas.parentElement.clientHeight : 0) || 450;

            if (w <= 0 || h <= 0) {
                if (!canvas._retryCount) canvas._retryCount = 0;
                if (canvas._retryCount < 40) {
                    canvas._retryCount++;
                    requestAnimationFrame(() => setTimeout(drawEquityChart, 50));
                }
                return;
            }
            canvas._retryCount = 0;

            if (window.ResizeObserver && canvas.parentElement && !canvas._roAttached) {
                canvas._roAttached = true;
                const ro = new ResizeObserver(() => {
                    requestAnimationFrame(() => drawEquityChart());
                });
                ro.observe(canvas.parentElement);
            }

            canvas.width = Math.round(w * dpr);
            canvas.height = Math.round(h * dpr);
            ctx.scale(dpr, dpr);

            let padLeft = 30;
            let padRight = 75;
            let padTop = 20;
            let padBottom = 28;
            let plotW = w - padLeft - padRight;
            let totalAvailableH = h - padTop - padBottom;

            let pts = currentSimPts;
            if (!pts || pts.length <= 1) {
                if (typeof runEquitySimulation === 'function' && typeof simTrades !== 'undefined' && simTrades.length > 0 && !canvas._simRanOnce) {
                    canvas._simRanOnce = true;
                    runEquitySimulation();
                    return;
                }
                ctx.clearRect(0, 0, w, h);
                ctx.fillStyle = '#0b0f19';
                ctx.fillRect(0, 0, w, h);
                ctx.fillStyle = '#94a3b8';
                ctx.font = '13px Segoe UI, Tahoma, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('هیچ معامله‌ای با این ترکیب فیلترها وجود ندارد! لطفاً فیلترها را تسهیل کنید.', w / 2, h / 2);
                canvas._coords = [];
                return;
            }
            canvas._simRanOnce = false;

            let minBal = Infinity;
            let maxBal = -Infinity;
            let totalPts = pts.length;

            for (let i = 0; i < totalPts; i++) {
                if (pts[i].b < minBal) minBal = pts[i].b;
                if (pts[i].b > maxBal) maxBal = pts[i].b;
                if (pts[i].peak !== undefined && pts[i].peak > maxBal) maxBal = pts[i].peak;
            }
            let balRange = maxBal - minBal;
            if (balRange < 50) balRange = 50;
            minBal = Math.floor((minBal - balRange * 0.05) / 50) * 50;
            maxBal = Math.ceil((maxBal + balRange * 0.05) / 50) * 50;
            balRange = maxBal - minBal;

            ctx.clearRect(0, 0, w, h);

            // Background
            ctx.fillStyle = '#0b0f19';
            ctx.fillRect(0, 0, w, h);

            // Determine Pane Dimensions
            let showDD = simState.showDrawdown;
            let curveH = showDD ? Math.floor(totalAvailableH * 0.68) : totalAvailableH;
            let ddTop = showDD ? (padTop + curveH + 24) : 0;
            let ddH = showDD ? (padTop + totalAvailableH - ddTop) : 0;

            // Plot area background for Curve
            ctx.fillStyle = '#0f172a';
            ctx.fillRect(padLeft, padTop, plotW, curveH);

            // Horizontal Grid & Price Labels for Curve
            let gridSteps = 5;
            ctx.strokeStyle = '#1e293b';
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.font = '11px Segoe UI, Tahoma, sans-serif';
            ctx.textAlign = 'left';

            for (let s = 0; s <= gridSteps; s++) {
                let val = minBal + (balRange / gridSteps) * s;
                let y = padTop + curveH - ((val - minBal) / balRange) * curveH;

                ctx.beginPath();
                ctx.moveTo(padLeft, y);
                ctx.lineTo(padLeft + plotW, y);
                ctx.stroke();

                ctx.fillStyle = '#94a3b8';
                ctx.fillText('$' + val.toFixed(0), padLeft + plotW + 10, y + 4);
            }

            // Vertical Grid & Dates spanning available height
            let dateSteps = 6;
            ctx.textAlign = 'center';

            for (let s = 0; s <= dateSteps; s++) {
                let idx = Math.min(Math.floor((totalPts - 1) * (s / dateSteps)), totalPts - 1);
                let x = padLeft + (idx / (totalPts - 1)) * plotW;

                ctx.beginPath();
                ctx.moveTo(x, padTop);
                ctx.lineTo(x, padTop + totalAvailableH);
                ctx.stroke();

                let dStr = pts[idx].t ? pts[idx].t.substring(5, 10) : '';
                ctx.fillStyle = '#64748b';
                ctx.fillText(dStr, x, padTop + totalAvailableH + 18);
            }

            ctx.setLineDash([]);

            // Baseline ($100) on Curve
            let baseVal = 100.0;
            if (baseVal >= minBal && baseVal <= maxBal) {
                let baseY = padTop + curveH - ((baseVal - minBal) / balRange) * curveH;
                ctx.strokeStyle = '#475569';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(padLeft, baseY);
                ctx.lineTo(padLeft + plotW, baseY);
                ctx.stroke();
            }

            // Build Coordinates & Track Drawdowns
            let coords = [];
            let maxDDPt = null;
            let maxDDVal = 0;

            for (let i = 0; i < totalPts; i++) {
                let pt = pts[i];
                let x = padLeft + (i / (totalPts - 1)) * plotW;
                let y = padTop + curveH - ((pt.b - minBal) / balRange) * curveH;
                let pVal = (pt.peak !== undefined) ? pt.peak : pt.b;
                let peakY = padTop + curveH - ((pVal - minBal) / balRange) * curveH;
                let ddVal = (pt.dd !== undefined) ? pt.dd : Math.max(0, pVal - pt.b);
                let ddPctVal = (pt.ddPct !== undefined) ? pt.ddPct : (pVal > 0 ? (ddVal / pVal * 100) : 0);

                let cObj = {
                    idx: i,
                    x: x,
                    y: y,
                    peakY: peakY,
                    peakVal: pVal,
                    ddVal: ddVal,
                    ddPctVal: ddPctVal,
                    pt: pt
                };
                coords.push(cObj);

                if (ddVal > maxDDVal) {
                    maxDDVal = ddVal;
                    maxDDPt = cObj;
                }
            }

            // 🛡️ Drawdown Shaded Valleys on Upper Curve
            if (showDD && coords.length > 1) {
                ctx.save();
                ctx.beginPath();
                ctx.moveTo(coords[0].x, coords[0].y);
                for (let i = 0; i < coords.length; i++) {
                    ctx.lineTo(coords[i].x, coords[i].y);
                }
                for (let i = coords.length - 1; i >= 0; i--) {
                    ctx.lineTo(coords[i].x, coords[i].peakY);
                }
                ctx.closePath();

                let ddGrad = ctx.createLinearGradient(0, padTop, 0, padTop + curveH);
                ddGrad.addColorStop(0, 'rgba(239, 68, 68, 0.25)');
                ddGrad.addColorStop(1, 'rgba(239, 68, 68, 0.08)');
                ctx.fillStyle = ddGrad;
                ctx.fill();

                // 🏆 High-Water Mark (Cumulative Peak) Dashed Line
                ctx.strokeStyle = '#facc15';
                ctx.lineWidth = 1.6;
                ctx.setLineDash([5, 4]);
                ctx.beginPath();
                for (let i = 0; i < coords.length; i++) {
                    if (i === 0) ctx.moveTo(coords[i].x, coords[i].peakY);
                    else ctx.lineTo(coords[i].x, coords[i].peakY);
                }
                ctx.stroke();
                ctx.restore();
            }

            // Gradient Fill below Equity Curve
            let grad = ctx.createLinearGradient(0, padTop, 0, padTop + curveH);
            if (simState.mode === 'kings') {
                grad.addColorStop(0, 'rgba(56, 189, 248, 0.30)');
                grad.addColorStop(1, 'rgba(56, 189, 248, 0.0)');
            } else {
                grad.addColorStop(0, 'rgba(168, 85, 247, 0.30)');
                grad.addColorStop(1, 'rgba(168, 85, 247, 0.0)');
            }

            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.moveTo(coords[0].x, padTop + curveH);
            for (let i = 0; i < coords.length; i++) {
                ctx.lineTo(coords[i].x, coords[i].y);
            }
            ctx.lineTo(coords[coords.length - 1].x, padTop + curveH);
            ctx.closePath();
            ctx.fill();

            // Equity Line
            ctx.strokeStyle = (simState.mode === 'kings') ? '#38bdf8' : '#a855f7';
            ctx.lineWidth = 2.2;
            ctx.beginPath();
            for (let i = 0; i < coords.length; i++) {
                if (i === 0) ctx.moveTo(coords[i].x, coords[i].y);
                else ctx.lineTo(coords[i].x, coords[i].y);
            }
            ctx.stroke();

            // 🚨 Highlight Maximum Drawdown on Curve
            if (showDD && maxDDPt && maxDDVal > 0) {
                ctx.save();
                ctx.strokeStyle = 'rgba(239, 68, 68, 0.75)';
                ctx.lineWidth = 1.4;
                ctx.setLineDash([2, 2]);
                ctx.beginPath();
                ctx.moveTo(maxDDPt.x, maxDDPt.peakY);
                ctx.lineTo(maxDDPt.x, maxDDPt.y);
                ctx.stroke();

                ctx.fillStyle = '#facc15';
                ctx.beginPath();
                ctx.arc(maxDDPt.x, maxDDPt.peakY, 3, 0, Math.PI * 2);
                ctx.fill();

                ctx.setLineDash([]);
                ctx.fillStyle = '#ef4444';
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 1.8;
                ctx.beginPath();
                ctx.arc(maxDDPt.x, maxDDPt.y, 5, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();

                let badgeTxt = '🚨 Max DD: -$' + Math.round(maxDDVal).toLocaleString('en-US') + ' (' + maxDDPt.ddPctVal.toFixed(1) + '%)';
                ctx.font = 'bold 10px Segoe UI, Tahoma, sans-serif';
                let txtW = ctx.measureText(badgeTxt).width;
                let bW = txtW + 14;
                let bH = 20;
                let bX = maxDDPt.x - bW / 2;
                let bY = maxDDPt.y + 10;

                if (bX < padLeft + 4) bX = padLeft + 4;
                if (bX + bW > padLeft + plotW - 4) bX = padLeft + plotW - bW - 4;
                if (bY + bH > padTop + curveH - 4) bY = maxDDPt.y - bH - 10;

                ctx.fillStyle = 'rgba(15, 23, 42, 0.94)';
                ctx.strokeStyle = '#ef4444';
                ctx.lineWidth = 1;
                ctx.beginPath();
                if (typeof ctx.roundRect === 'function') {
                    ctx.roundRect(bX, bY, bW, bH, 4);
                } else {
                    ctx.rect(bX, bY, bW, bH);
                }
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = '#fca5a5';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(badgeTxt, bX + bW / 2, bY + bH / 2);
                ctx.restore();
            }

            // Border for Curve
            ctx.strokeStyle = '#334155';
            ctx.lineWidth = 1;
            ctx.strokeRect(padLeft, padTop, plotW, curveH);

            // =================================================================
            // 📊 LOWER PANE: UNDERWATER DRAWDOWN BARS (میله‌های افت سرمایه)
            // =================================================================
            if (showDD && ddH > 25) {
                ctx.save();

                // Separator Line & Label
                let sepY = ddTop - 10;
                ctx.strokeStyle = '#1e293b';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(padLeft, sepY);
                ctx.lineTo(padLeft + plotW, sepY);
                ctx.stroke();

                ctx.font = 'bold 10px Segoe UI, Tahoma, sans-serif';
                ctx.fillStyle = '#fca5a5';
                ctx.textAlign = 'left';
                ctx.fillText('📊 عمق تمام افت‌های سرمایه (Underwater Drawdown Bars)', padLeft + 6, sepY - 2);

                // Lower Pane Background
                ctx.fillStyle = 'rgba(15, 23, 42, 0.65)';
                ctx.fillRect(padLeft, ddTop, plotW, ddH);

                // Y-Axis Scale for Drawdown Pane
                let ddScale = Math.max(10, Math.ceil(maxDDVal / 10) * 10);

                // Drawdown Grid Lines & Axis Labels
                ctx.font = '10px Segoe UI, Tahoma, sans-serif';
                ctx.textAlign = 'left';

                // $0 baseline at ddTop
                ctx.strokeStyle = '#334155';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(padLeft, ddTop);
                ctx.lineTo(padLeft + plotW, ddTop);
                ctx.stroke();
                ctx.fillStyle = '#34d399';
                ctx.fillText('$0', padLeft + plotW + 10, ddTop + 3);

                // Mid DD grid line
                let midY = ddTop + ddH * 0.5;
                ctx.strokeStyle = '#1e293b';
                ctx.setLineDash([3, 3]);
                ctx.beginPath();
                ctx.moveTo(padLeft, midY);
                ctx.lineTo(padLeft + plotW, midY);
                ctx.stroke();
                ctx.fillStyle = '#94a3b8';
                ctx.fillText('-$' + (ddScale / 2).toFixed(0), padLeft + plotW + 10, midY + 3);

                // Max DD grid line
                let bottomY = ddTop + ddH;
                ctx.strokeStyle = 'rgba(239, 68, 68, 0.4)';
                ctx.beginPath();
                ctx.moveTo(padLeft, bottomY);
                ctx.lineTo(padLeft + plotW, bottomY);
                ctx.stroke();
                ctx.fillStyle = '#f87171';
                ctx.fillText('-$' + ddScale.toFixed(0), padLeft + plotW + 10, bottomY + 3);
                ctx.setLineDash([]);

                // Draw Bars for EVERY point with drawdown
                let barW = Math.max(1.5, (plotW / totalPts) * 0.95);

                for (let i = 0; i < totalPts; i++) {
                    let c = coords[i];
                    if (c.ddVal > 0) {
                        let bH = (c.ddVal / ddScale) * ddH;
                        let bX = c.x - barW / 2;
                        let intensity = Math.min(1.0, c.ddVal / (maxDDVal || 1));
                        let alpha = 0.45 + intensity * 0.45;
                        ctx.fillStyle = 'rgba(239, 68, 68, ' + alpha.toFixed(2) + ')';
                        ctx.fillRect(bX, ddTop, barW, bH);
                    }
                }

                // Find and Label Top Prominent Local Drawdown Troughs
                let candidatePeaks = [];
                for (let i = 1; i < totalPts - 1; i++) {
                    let dd = coords[i].ddVal;
                    if (dd >= 5.0 && dd >= coords[i - 1].ddVal && dd >= coords[i + 1].ddVal) {
                        candidatePeaks.push(coords[i]);
                    }
                }
                candidatePeaks.sort((a, b) => b.ddVal - a.ddVal);

                let labeledPeaks = [];
                for (let cp of candidatePeaks) {
                    let tooClose = false;
                    for (let lp of labeledPeaks) {
                        if (Math.abs(cp.x - lp.x) < 38) {
                            tooClose = true;
                            break;
                        }
                    }
                    if (!tooClose) {
                        labeledPeaks.push(cp);
                        if (labeledPeaks.length >= 7) break;
                    }
                }

                // Draw numeric tags at the tip of each prominent drawdown bar
                for (let lp of labeledPeaks) {
                    let bH = (lp.ddVal / ddScale) * ddH;
                    let isMax = (lp === maxDDPt);
                    let tagY = ddTop + bH + 11;
                    if (tagY > ddTop + ddH + 2) tagY = ddTop + bH - 6;

                    ctx.font = isMax ? 'bold 10px Segoe UI, Tahoma, sans-serif' : 'bold 9px Segoe UI, Tahoma, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.fillStyle = isMax ? '#ef4444' : '#fca5a5';
                    ctx.fillText('-$' + Math.round(lp.ddVal), lp.x, tagY);

                    // Small circle at tip
                    ctx.fillStyle = isMax ? '#ef4444' : '#f87171';
                    ctx.beginPath();
                    ctx.arc(lp.x, ddTop + bH, isMax ? 3 : 2, 0, Math.PI * 2);
                    ctx.fill();
                }

                // Border for Drawdown Pane
                ctx.strokeStyle = '#334155';
                ctx.lineWidth = 1;
                ctx.strokeRect(padLeft, ddTop, plotW, ddH);

                ctx.restore();
            }

            canvas._coords = coords;
            canvas._padLeft = padLeft;
            canvas._padTop = padTop;
            canvas._plotW = plotW;
            canvas._plotH = totalAvailableH;
            canvas._curveH = curveH;
            canvas._ddTop = ddTop;
            canvas._ddH = ddH;
            canvas._showDD = showDD;
            canvas._maxDDVal = maxDDVal;
        }

        function initEquityCanvasEvents() {
            let canvas = document.getElementById('equityCanvas');
            if (!canvas || canvas._eventsBound) return;
            canvas._eventsBound = true;
            simCanvasEventsInitialized = true;

            canvas.addEventListener('mousemove', function(evt) {
                if (!canvas._coords || canvas._coords.length === 0) return;
                let rect = canvas.getBoundingClientRect();
                let mouseX = evt.clientX - rect.left;
                let mouseY = evt.clientY - rect.top;

                let tt = document.getElementById('equityTooltip');
                if (mouseX < canvas._padLeft || mouseX > canvas._padLeft + canvas._plotW ||
                    mouseY < canvas._padTop || mouseY > canvas._padTop + canvas._plotH) {
                    if(tt) tt.style.display = 'none';
                    let liveTag = document.getElementById('lblLiveConcurrentTag');
                    if (liveTag) liveTag.style.display = 'none';
                    return;
                }

                let coords = canvas._coords;
                let ratio = (mouseX - canvas._padLeft) / canvas._plotW;
                let idx = Math.round(ratio * (coords.length - 1));
                if (idx < 0) idx = 0;
                if (idx >= coords.length) idx = coords.length - 1;

                let target = coords[idx];
                let pt = target.pt;

                let liveTag = document.getElementById('lblLiveConcurrentTag');
                if (liveTag) {
                    if (pt && pt.concurrent !== undefined && pt.concurrent > 0) {
                        liveTag.textContent = pt.concurrent + ' همزمان در این نقطه';
                        liveTag.style.display = 'inline-block';
                    } else {
                        liveTag.style.display = 'none';
                    }
                }

                drawEquityChart();
                let ctx = canvas.getContext('2d');
                let dpr = window.devicePixelRatio || 1;
                ctx.save();
                ctx.scale(dpr, dpr);

                // Crosshair vertical
                ctx.strokeStyle = 'rgba(248, 250, 252, 0.4)';
                ctx.lineWidth = 1;
                ctx.setLineDash([2, 2]);
                ctx.beginPath();
                ctx.moveTo(target.x, canvas._padTop);
                ctx.lineTo(target.x, canvas._padTop + canvas._plotH);
                ctx.stroke();

                // Target Circle on Curve
                ctx.setLineDash([]);
                ctx.fillStyle = '#facc15';
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(target.x, target.y, 5, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();

                // If drawdown overlay is active, show vertical drop to Peak on curve
                if (simState.showDrawdown && target.peakY !== undefined && target.ddVal > 0) {
                    ctx.strokeStyle = 'rgba(239, 68, 68, 0.8)';
                    ctx.lineWidth = 1;
                    ctx.setLineDash([2, 2]);
                    ctx.beginPath();
                    ctx.moveTo(target.x, target.peakY);
                    ctx.lineTo(target.x, target.y);
                    ctx.stroke();

                    ctx.fillStyle = '#facc15';
                    ctx.beginPath();
                    ctx.arc(target.x, target.peakY, 3, 0, Math.PI * 2);
                    ctx.fill();
                }

                // Highlight active bar in the Lower Drawdown Pane
                if (canvas._showDD && canvas._ddH > 25) {
                    let ddScale = Math.max(10, Math.ceil(canvas._maxDDVal / 10) * 10);
                    let barH = (target.ddVal / ddScale) * canvas._ddH;
                    let barW = Math.max(3, (canvas._plotW / canvas._coords.length) * 1.8);

                    // Glowing bar highlight
                    ctx.fillStyle = '#facc15';
                    ctx.fillRect(target.x - barW / 2, canvas._ddTop, barW, barH);

                    // Pin dot at bottom of bar
                    if (target.ddVal > 0) {
                        ctx.fillStyle = '#ffffff';
                        ctx.beginPath();
                        ctx.arc(target.x, canvas._ddTop + barH, 3, 0, Math.PI * 2);
                        ctx.fill();

                        // Floating tooltip near bar
                        ctx.font = 'bold 10px Segoe UI, Tahoma, sans-serif';
                        ctx.fillStyle = '#facc15';
                        ctx.textAlign = 'center';
                        let tagY = canvas._ddTop + barH + 12;
                        if (tagY > canvas._ddTop + canvas._ddH + 4) tagY = canvas._ddTop + barH - 6;
                        ctx.fillText('-$' + Math.round(target.ddVal) + ' (' + target.ddPctVal.toFixed(1) + '%)', target.x, tagY);
                    }
                }
                ctx.restore();

                if (tt) {
                    tt.style.display = 'block';
                    let pnlCol = pt.p >= 0 ? '#00e676' : '#ef4444';
                    let pnlSign = pt.p >= 0 ? '+' : '';
                    let totProfit = pt.b - 100.0;
                    let totCol = totProfit >= 0 ? '#00e676' : '#ef4444';
                    let totSign = totProfit >= 0 ? '+' : '';

                    let ddVal = (target.ddVal !== undefined) ? target.ddVal : ((pt.dd !== undefined) ? pt.dd : Math.max(0, (pt.peak || pt.b) - pt.b));
                    let ddPct = (target.ddPctVal !== undefined) ? target.ddPctVal : ((pt.ddPct !== undefined) ? pt.ddPct : 0);
                    let peakVal = (target.peakVal !== undefined) ? target.peakVal : ((pt.peak !== undefined) ? pt.peak : pt.b);

                    let ddHtml = ddVal > 0 
                        ? '<b style="color:#f87171;">-$' + Math.round(ddVal).toLocaleString('en-US') + ' (' + ddPct.toFixed(1) + '٪)</b>'
                        : '<b style="color:#34d399;">$0 (سقف جدید ✨)</b>';

                    let concHtml = (pt && pt.concurrent !== undefined && pt.concurrent > 0)
                        ? `<div style="color:#e2e8f0;font-size:11.5px;margin-top:2px;">⚡ پوزیشن‌های همزمان باز: <b style="color:#38bdf8;">${pt.concurrent} معامله</b></div>`
                        : '';

                    tt.innerHTML = `
                        <div style="font-weight:bold;color:#facc15;margin-bottom:4px;border-bottom:1px solid #334155;padding-bottom:2px;">معامله #${pt.idx} - ${pt.n}</div>
                        <div style="color:#94a3b8;font-size:11px;">🕒 زمان: <span style="direction:ltr;display:inline-block;font-family:monospace;color:#f1f5f9;">${pt.t}</span></div>
                        <div style="margin-top:4px;">سود این معامله: <b style="color:${pnlCol};">${pnlSign}$${pt.p.toFixed(2)}</b></div>
                        <div>بالانس حساب: <b style="color:#38bdf8;">$${Math.round(pt.b).toLocaleString()}</b></div>
                        ${concHtml}
                        <div>سود خالص کل: <b style="color:${totCol};">${totSign}$${Math.round(totProfit).toLocaleString()} (${(totProfit).toFixed(1)}٪)</b></div>
                        <div style="margin-top:4px;border-top:1px solid #1e293b;padding-top:4px;">
                            <div>🏆 سقف تا این لحظه: <b style="color:#facc15;">$${Math.round(peakVal).toLocaleString()}</b></div>
                            <div>🛡️ افت از سقف (DD): ${ddHtml}</div>
                        </div>
                    `;

                    let ttX = target.x + 15;
                    let ttY = target.y - 40;
                    if (ttX + 220 > rect.width) ttX = target.x - 230;
                    if (ttY < 10) ttY = 10;
                    tt.style.left = ttX + 'px';
                    tt.style.top = ttY + 'px';
                }
            });

            canvas.addEventListener('mouseleave', function() {
                let tt = document.getElementById('equityTooltip');
                if (tt) tt.style.display = 'none';
                let liveTag = document.getElementById('lblLiveConcurrentTag');
                if (liveTag) liveTag.style.display = 'none';
                drawEquityChart();
            });

            window.addEventListener('resize', function() {
                drawEquityChart();
            });
        }


        function selectWeeklyDetail(cardId) {
            if(!cardId) return;
            document.querySelectorAll('.week-detail-card').forEach(c => c.style.display = 'none');
            let el = document.getElementById(cardId);
            if(el) {
                el.style.display = 'block';
                el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }

        function filterWeeklyMode(mode) {
            let kingsRows = document.querySelectorAll('.wk-row-kings');
            let allRows = document.querySelectorAll('.wk-row-all');
            let btnKings = document.getElementById('btnWkTableKings');
            let btnAll = document.getElementById('btnWkTableAll');
            if(mode === 'kings') {
                kingsRows.forEach(r => r.style.display = '');
                allRows.forEach(r => r.style.display = 'none');
                if(btnKings) btnKings.classList.add('active');
                if(btnAll) btnAll.classList.remove('active');
            } else {
                kingsRows.forEach(r => r.style.display = 'none');
                allRows.forEach(r => r.style.display = '');
                if(btnKings) btnKings.classList.remove('active');
                if(btnAll) btnAll.classList.add('active');
            }
        }

        
        function openEqSubtab(evt, subtabId) {
            document.querySelectorAll('.eq-subpanel').forEach(p => p.style.display = 'none');
            document.querySelectorAll('.eq-subtab-btn').forEach(b => b.classList.remove('active'));

            let target = document.getElementById(subtabId);
            if (target) target.style.display = 'block';
            if (evt && evt.currentTarget) evt.currentTarget.classList.add('active');

            if (subtabId === 'eq-sub-weekly') {
                setTimeout(() => {
                    drawWeeklyBarChart(currentWeeklyBarMode);
                }, 40);
            }
        }

        
        // ====================================================
        // 🛡️ CONSECUTIVE LOSS FILTER CONTROLLER & UI SYNC
        // ====================================================
        function applyConsecFromFilterTab(trigger, skipCount, skipDay, btnEl) {
            setConsecLossFilter(trigger, skipCount, skipDay, btnEl);
        }

        function setConsecLossFilter(trigger, skipCount, skipDay, btnEl) {
            simState.consecLossTrigger = trigger;
            simState.consecLossSkipCount = skipCount;
            simState.consecLossSkipDay = skipDay;

            let selTrig = document.getElementById('selConsecTrigger');
            let selAct = document.getElementById('selConsecAction');
            if (selTrig) selTrig.value = trigger;
            if (selAct) {
                if (skipDay) selAct.value = 'skip_day';
                else selAct.value = 'skip_' + (skipCount || 1);
            }

            syncConsecButtonsUI();
            runEquitySimulation();
        }

        function onCustomConsecChange() {
            let selTrig = document.getElementById('selConsecTrigger');
            let selAct = document.getElementById('selConsecAction');
            let trigger = parseInt(selTrig ? selTrig.value : 0, 10);
            let act = selAct ? selAct.value : 'skip_1';

            let skipDay = (act === 'skip_day');
            let skipCount = 1;
            if (act === 'skip_2') skipCount = 2;
            if (act === 'skip_3') skipCount = 3;

            simState.consecLossTrigger = trigger;
            simState.consecLossSkipCount = skipCount;
            simState.consecLossSkipDay = skipDay;

            syncConsecButtonsUI();
            runEquitySimulation();
        }

        function syncConsecButtonsUI() {
            let t = simState.consecLossTrigger;
            let sk = simState.consecLossSkipCount;
            let day = simState.consecLossSkipDay;

            document.querySelectorAll('.consec-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.consec-btn-filter').forEach(b => b.classList.remove('active'));

            let badge1 = document.getElementById('consecLossSummaryBadge');
            let badge2 = document.getElementById('simConsecBadge2');

            if (t === 0) {
                let b0 = document.getElementById('btnConsecNone');
                if (b0) b0.classList.add('active');
                let f0 = document.querySelector('.consec-btn-filter[data-trig="0"]');
                if (f0) f0.classList.add('active');
                if (badge1) { badge1.textContent = 'وضعیت: فیلتر خاموش (ترید عادی)'; badge1.style.color = '#7dd3fc'; badge1.style.borderColor = '#0284c7'; }
                if (badge2) { badge2.textContent = 'بدون وقفه (خاموش)'; badge2.style.color = '#cbd5e1'; badge2.style.background = '#1e293b'; }
            } else {
                let text = '';
                if (day) {
                    text = 'توقف بعد از ' + t + ' باخت تا فردا';
                    let bd = document.getElementById('btnConsec2Daily');
                    if (bd && t === 2) bd.classList.add('active');
                    let fd = document.querySelector('.consec-btn-filter[data-day="1"]');
                    if (fd && t === 2) fd.classList.add('active');
                } else {
                    text = 'بعد از ' + t + ' باخت 👈 رد ' + sk + ' ترید';
                    if (t === 2 && sk === 1) {
                        let b = document.getElementById('btnConsec2Skip1');
                        if (b) b.classList.add('active');
                        let fb = document.querySelector('.consec-btn-filter[data-trig="2"][data-sk="1"]');
                        if (fb) fb.classList.add('active');
                    } else if (t === 2 && sk === 2) {
                        let b = document.getElementById('btnConsec2Skip2');
                        if (b) b.classList.add('active');
                        let fb = document.querySelector('.consec-btn-filter[data-trig="2"][data-sk="2"]');
                        if (fb) fb.classList.add('active');
                    } else if (t === 3 && sk === 1) {
                        let b = document.getElementById('btnConsec3Skip1');
                        if (b) b.classList.add('active');
                        let fb = document.querySelector('.consec-btn-filter[data-trig="3"][data-sk="1"]');
                        if (fb) fb.classList.add('active');
                    }
                }
                if (badge1) { badge1.textContent = '⚡ فعال: ' + text; badge1.style.color = '#34d399'; badge1.style.borderColor = '#10b981'; }
                if (badge2) { badge2.textContent = '⚡ فعال: ' + text; badge2.style.color = '#34d399'; badge2.style.background = '#064e3b'; }
            }
        }

        function updateConsecutiveLossUI(maxLoss, maxWin, totalLossStreaks, avgLoss, streakDist, skippedCnt, savedLosses, missedWins, maxDD) {
            let elMaxLoss = document.getElementById('kpiMaxConsecLoss');
            let elMaxWin = document.getElementById('kpiMaxConsecWin');
            let elTotalStreaks = document.getElementById('kpiTotalLossStreaks');
            let elAvgLoss = document.getElementById('kpiAvgLossStreak');

            if (elMaxLoss) elMaxLoss.textContent = maxLoss + ' معامله';
            if (elMaxWin) elMaxWin.textContent = maxWin + ' معامله';
            if (elTotalStreaks) elTotalStreaks.textContent = totalLossStreaks.toLocaleString() + ' رگه';
            if (elAvgLoss) elAvgLoss.textContent = avgLoss.toFixed(1) + ' معامله';

            // Render distribution cards
            let grid = document.getElementById('consecLossBarsGrid');
            if (grid) {
                let html = '';
                let streakKeys = [1, 2, 3, 4, 5, 6];
                for (let k of streakKeys) {
                    let count = streakDist[k] || 0;
                    let pct = totalLossStreaks > 0 ? ((count / totalLossStreaks) * 100) : 0;
                    let color = k === 1 ? '#38bdf8' : (k === 2 ? '#facc15' : (k === 3 ? '#fb923c' : '#ef4444'));
                    let bg = k === 1 ? 'rgba(56, 189, 248, 0.1)' : (k === 2 ? 'rgba(250, 204, 21, 0.1)' : 'rgba(239, 68, 68, 0.15)');
                    let title = (k === 6) ? '۶+ باخت متوالی' : (k + ' باخت متوالی');
                    html += `
                        <div style="background:${bg};border:1px solid ${color};padding:6px 8px;border-radius:6px;text-align:center;">
                            <div style="font-size:10px;color:#94a3b8;margin-bottom:2px;">${title}</div>
                            <div style="font-size:14px;font-weight:bold;color:${color};">${count} بار</div>
                            <div style="font-size:9.5px;color:#cbd5e1;margin-top:2px;">${pct.toFixed(1)}٪</div>
                            <div style="width:100%;height:3px;background:#1e293b;border-radius:2px;margin-top:4px;overflow:hidden;">
                                <div style="width:${Math.min(100, pct)}%;height:100%;background:${color};"></div>
                            </div>
                        </div>
                    `;
                }
                grid.innerHTML = html;
            }

            // Impact box
            let elSkipped = document.getElementById('consecSkippedTradesVal');
            let elSaved = document.getElementById('consecSavedLossesVal');
            let elMissed = document.getElementById('consecMissedWinsVal');
            let elDD = document.getElementById('consecDDImpactVal');

            if (elSkipped) elSkipped.textContent = skippedCnt.toLocaleString();
            if (elSaved) elSaved.textContent = savedLosses.toLocaleString() + ' استاپ نجات یافت';
            if (elMissed) elMissed.textContent = missedWins.toLocaleString() + ' برد رد شد';
            if (elDD) elDD.textContent = 'افت سرمایه فعلی: $' + maxDD.toFixed(2);
        }

        
        
        // ====================================================
        // 🤖 CLIENT-SIDE AI AUTO-OPTIMIZER ENGINE
        // ====================================================
        function runClientAutoOptimizer() {
            let kingTrades = simTrades.filter(t => t.k === 1);
            let totalBase = kingTrades.length;
            if (totalBase === 0) {
                alert('هیچ معامله‌ای برای بهینه‌سازی یافت نشد.');
                return;
            }

            let min15 = Math.max(20, Math.floor(totalBase * 0.15));

            // Calculate king PF stats
            let kStats = {};
            for (let t of kingTrades) {
                if (!kStats[t.kk]) kStats[t.kk] = { gp: 0, gl: 0, p: 0, wins: 0, cnt: 0 };
                kStats[t.kk].cnt++;
                kStats[t.kk].p += t.p;
                if (t.p > 0) { kStats[t.kk].wins++; kStats[t.kk].gp += t.p; }
                else { kStats[t.kk].gl += Math.abs(t.p); }
            }
            for (let kk in kStats) {
                kStats[kk].pf = kStats[kk].gl > 0 ? (kStats[kk].gp / kStats[kk].gl) : 999;
            }
            let sortedKings = Object.keys(kStats).sort((a, b) => kStats[a].pf - kStats[b].pf);
            let allKingsSet = new Set(Object.keys(kStats));

            let hoursMap = {
                'all': new Array(24).fill(true),
                'no_night': Array.from({length: 24}, (_, h) => !(h >= 22 || h <= 3)),
                'lon_ny': Array.from({length: 24}, (_, h) => (h >= 7 && h < 20)),
                'core_day': Array.from({length: 24}, (_, h) => (h >= 8 && h <= 18))
            };

            let pots = [0.0, 1.0, 1.5, 2.0, 2.5, 3.0];
            let cbs = [{trig: 0, sk: 0}, {trig: 2, sk: 1}];

            let best = null;
            let bestScore = -999999;

            for (let hKey in hoursMap) {
                let hArr = hoursMap[hKey];
                for (let pot of pots) {
                    for (let dropN = 0; dropN <= Math.min(7, sortedKings.length - 5); dropN++) {
                        let activeKings = new Set(allKingsSet);
                        for (let d = 0; d < dropN; d++) activeKings.delete(sortedKings[d]);

                        for (let cb of cbs) {
                            let bal = 100.0, peak = bal, maxDD = 0.0, wins = 0, total = 0, gp = 0.0, gl = 0.0;
                            let consecLoss = 0, skips = 0;

                            for (let t of kingTrades) {
                                if (!activeKings.has(t.kk)) continue;
                                if (!hArr[t.h]) continue;
                                if (t.pot < pot) continue;
                                if (skips > 0) { skips--; continue; }

                                total++;
                                bal += t.p;
                                if (bal > peak) peak = bal;
                                let dd = peak - bal;
                                if (dd > maxDD) maxDD = dd;
                                if (t.p > 0) {
                                    wins++; gp += t.p; consecLoss = 0;
                                } else {
                                    gl += Math.abs(t.p); consecLoss++;
                                    if (cb.trig > 0 && consecLoss >= cb.trig) {
                                        skips = cb.sk; consecLoss = 0;
                                    }
                                }
                            }

                            if (total < min15) continue;
                            let wr = (wins / total) * 100;
                            let pf = gl > 0 ? (gp / gl) : 999;
                            let net = bal - 100.0;
                            let avg = net / total;
                            let score = Math.pow(pf, 1.3) * (wr / 50.0) * Math.max(0.5, avg) / Math.max(12.0, maxDD) * 100;

                            if (score > bestScore) {
                                bestScore = score;
                                best = {
                                    hKey: hKey, hArr: hArr, pot: pot, kings: Array.from(activeKings),
                                    cb: cb, total: total, wr: wr, pf: pf, avg: avg, maxDD: maxDD, net: net
                                };
                            }
                        }
                    }
                }
            }

            if (!best) {
                alert('هیچ ترکیب متناسبی با شرط حداقل ۱۵٪ معاملات یافت نشد.');
                return;
            }

            let msg = [
                '🏆 بهترین ترکیب کشف‌شده توسط هوش مصنوعی (شرط حداقل ۱۵٪ = ' + min15 + ' معامله):',
                '',
                '🔹 تعداد معامله: ' + best.total + ' (' + ((best.total/totalBase)*100).toFixed(1) + '٪ کل چارت)',
                '🔹 وین‌ریت: ' + best.wr.toFixed(1) + '٪',
                '🔹 پرافیت فاکتور: ' + (best.pf < 900 ? best.pf.toFixed(2) : 'MAX'),
                '🔹 میانگین سود هر ترید: $' + best.avg.toFixed(2),
                '🔹 حداکثر افت سرمایه (DD): $' + Math.round(best.maxDD).toLocaleString(),
                '🔹 سود خالص: $' + Math.round(best.net).toLocaleString(),
                '🔹 تنظیمات: کف سود $' + best.pot.toFixed(2) + ' | ' + best.kings.length + ' سلطان فعال' + (best.cb.trig > 0 ? ' | وقفه بعد از ۲ استاپ' : ''),
                '',
                'آیا مایلید این چیدمان بلافاصله روی نمودار و فیلترها اعمال شود؟'
            ].join('\n');

            if (confirm(msg)) {
                let aiIdx = (typeof smartPresets !== 'undefined' && smartPresets) ? smartPresets.length : 0;
                let activeSym = typeof currentActiveSymbol !== 'undefined' ? currentActiveSymbol : 'EURUSD';
                let hoursActiveCount = best.hArr.filter(Boolean).length;
                let hoursStrLabel = hoursActiveCount === 24 ? '۲۴ ساعته' : (hoursActiveCount + ' ساعت فعال');
                let consecLabel = best.cb.trig > 0 ? (' | وقفه بعد از ' + best.cb.trig + ' استاپ') : '';
                let filterDesc = 'کف سود: <b>$' + best.pot.toFixed(2) + '+</b> | ساعات: <b>' + hoursStrLabel + '</b>' + consecLabel;
                let kingsDesc = '👑 ' + best.kings.length + ' سلطان منتخب هوش مصنوعی';

                let allowedHoursArr = [];
                for (let h = 0; h < 24; h++) {
                    if (best.hArr[h]) allowedHoursArr.push(h < 10 ? '0' + h : '' + h);
                }
                let allowedHoursStr = allowedHoursArr.length === 24 ? '' : allowedHoursArr.join(',');

                let disabledKingsArr = [];
                let activeKingsSet = new Set(best.kings);
                for (let k of (kingsSimList || [])) {
                    if (k && k.kk && !activeKingsSet.has(k.kk)) {
                        disabledKingsArr.push(k.kk.replace(/\|(M\d+)/, ' [$1]'));
                    }
                }
                let disabledKingsStr = disabledKingsArr.join(', ');

                let aiPreset = {
                    id: 'ai_opt_' + Date.now(),
                    idx: aiIdx,
                    is_ai: true,
                    title: '🤖 سناریوی کشف خودکار هوش مصنوعی (' + activeSym + ' AI Champion 🎯)',
                    badge: '🤖 کشف اختصاصی هوش مصنوعی',
                    badge_bg: '#6b21a8',
                    badge_col: '#f3e8ff',
                    desc: 'بهترین ترکیب ریاضی خودکار کشف‌شده با پرافیت فاکتور ' + (best.pf < 900 ? best.pf.toFixed(2) : 'MAX') + '، وین‌ریت ' + best.wr.toFixed(1) + '٪ و سود خالص $' + Math.round(best.net).toLocaleString(),
                    filterText: filterDesc,
                    kingsText: kingsDesc,
                    min_pot: best.pot,
                    hours: [...best.hArr],
                    hours_str: allowedHoursStr,
                    kings: Array.from(best.kings),
                    disabled_kings_str: disabledKingsStr,
                    consec_trig: best.cb.trig,
                    consec_action: best.cb.sk,
                    consec_sk: best.cb.sk,
                    consec_day: false,
                    cnt: best.total,
                    wr: best.wr,
                    pf: best.pf,
                    avg: best.avg,
                    max_dd: best.maxDD,
                    net: best.net,
                    symbol: activeSym
                };

                // Add to smartPresets array
                if (typeof smartPresets !== 'undefined' && smartPresets) {
                    smartPresets.push(aiPreset);
                }

                // Insert into the Strategic Presets Table
                let tbodyPresets = document.getElementById('systemPresetsTbody');
                if (tbodyPresets) {
                    let existingAiRow = document.getElementById('presetRow_AI');
                    if (existingAiRow) existingAiRow.remove();

                    let aiRowHtml = `
                        <tr id="presetRow_AI" style="border: 2px solid #a855f7; background: #1e1035; box-shadow: 0 0 16px rgba(168,85,247,0.35); transition:all 0.2s;" class="preset-table-row featured-preset">
                            <td style="text-align:center;padding:7px 4px;font-weight:bold;font-size:12px;color:#c084fc;">⭐ AI</td>
                            <td style="padding:7px 8px;">
                                <div style="font-weight:bold;color:#f1f5f9;font-size:12px;display:flex;align-items:center;gap:4px;flex-wrap:wrap;">
                                    <span>${aiPreset.title}</span>
                                    <span style='background:#6b21a8;color:#f3e8ff;font-size:10px;padding:2px 6px;border-radius:4px;font-weight:bold;'>🤖 کشف خودکار هوش مصنوعی</span>
                                </div>
                                <div style="color:#d8b4fe;font-size:10.5px;margin-top:2px;">${aiPreset.desc}</div>
                            </td>
                            <td style="padding:7px 6px;font-size:11px;color:#cbd5e1;text-align:center;white-space:nowrap;">
                                <div>${aiPreset.filterText}</div>
                                <div style="font-weight:bold;color:#facc15;font-size:10.5px;margin-top:2px;">${aiPreset.kingsText}</div>
                            </td>
                            <td style="text-align:center;padding:7px 4px;font-weight:bold;font-size:12px;color:#e2e8f0;">${aiPreset.cnt.toLocaleString()}</td>
                            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#34d399;font-size:12px;">${aiPreset.wr.toFixed(1)}٪</td>
                            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#38bdf8;font-size:12.5px;">${aiPreset.pf < 900 ? aiPreset.pf.toFixed(2) : 'MAX'}</td>
                            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#facc15;font-size:12.5px;">+$${aiPreset.avg.toFixed(2)}</td>
                            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#fca5a5;font-size:11.5px;">$${Math.round(aiPreset.max_dd).toLocaleString()}</td>
                            <td style="text-align:center;padding:7px 6px;font-weight:bold;color:#00e676;font-size:13.5px;background:#064e3b44;white-space:nowrap;">+$${Math.round(aiPreset.net).toLocaleString()}</td>
                            <td style="text-align:center;padding:7px 6px;white-space:nowrap;">
                                <div style="display:inline-flex;gap:4px;align-items:center;justify-content:center;">
                                    <button id="btnApplyPresetAI" class="apply-preset-btn" onclick="applySmartPreset(${aiIdx})" style="background:linear-gradient(135deg, #7c3aed, #9333ea);border:1px solid #c084fc;color:#fff;padding:5px 8px;border-radius:5px;font-size:11px;cursor:pointer;font-weight:bold;box-shadow:0 2px 8px rgba(124,58,237,0.4);" title="اعمال این سناریو روی نمودار اکوئیتی داشبورد">
                                        ⚡ اعمال
                                    </button>
                                    <button onclick="exportPresetToMT5(${aiIdx})" style="background:linear-gradient(135deg, #065f46, #047857);border:1px solid #34d399;color:#ecfdf5;padding:5px 7px;border-radius:5px;font-size:11px;cursor:pointer;font-weight:bold;display:inline-flex;align-items:center;gap:3px;" title="دریافت فایل استراتژی تستر متاتریدر ۵ (.ini) جهت Drag & Drop به تستر">
                                        <span>🤖 تنظیمات تستر (.ini)</span>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                    tbodyPresets.insertAdjacentHTML('afterbegin', aiRowHtml);
                }

                // Save to custom presets in localStorage as well
                try {
                    let customList = JSON.parse(localStorage.getItem('flagpro_custom_presets') || '[]');
                    customList.unshift({
                        id: aiPreset.id,
                        title: aiPreset.title,
                        desc: aiPreset.desc,
                        min_pot: aiPreset.min_pot,
                        hours: [...aiPreset.hours],
                        kings: [...aiPreset.kings],
                        consec_trig: aiPreset.consec_trig,
                        consec_sk: aiPreset.consec_sk,
                        consec_day: false,
                        createdAt: new Date().toLocaleDateString('fa-IR')
                    });
                    localStorage.setItem('flagpro_custom_presets', JSON.stringify(customList));
                    if (typeof loadCustomPresets === 'function') loadCustomPresets();
                } catch(e) {}

                // Apply immediately to chart & filters
                simState.mode = 'kings';
                simState.minProfit = best.pot;
                simState.allowedHours = [...best.hArr];
                simState.enabledKings = new Set(best.kings);
                simState.consecLossTrigger = best.cb.trig;
                simState.consecLossSkipCount = best.cb.sk;
                simState.consecLossSkipDay = false;

                let slider = document.getElementById('simProfitSlider');
                if (slider) slider.value = best.pot;
                let sliderVal = document.getElementById('simProfitSliderVal');
                if (sliderVal) sliderVal.textContent = '$' + best.pot.toFixed(2);

                renderSimKingsGrid();
                renderSimHoursBar();
                syncConsecButtonsUI();
                runEquitySimulation();

                if (typeof showSaveNotification === 'function') {
                    showSaveNotification('🤖 سناریوی بهینه‌شده هوش مصنوعی به ردیف اول جدول اضافه شد و پنجره خروجی (.ini) باز شد!');
                }

                // Open MT5 Export modal immediately for the AI preset
                if (typeof openMT5ExportModal === 'function') {
                    openMT5ExportModal({
                        title: aiPreset.title,
                        min_pot: aiPreset.min_pot,
                        hours_str: aiPreset.hours_str,
                        consec_trig: aiPreset.consec_trig,
                        consec_action: aiPreset.consec_action,
                        disabled_kings_str: aiPreset.disabled_kings_str,
                        cnt: aiPreset.cnt,
                        wr: aiPreset.wr,
                        pf: aiPreset.pf,
                        avg: aiPreset.avg,
                        net: aiPreset.net,
                        kings_count: aiPreset.kings.length,
                        symbol: activeSym
                    });
                }
            }
        }

        function toggleSidebar() {
            let sb = document.getElementById('mainSidebar');
            let icon = document.getElementById('btnToggleSidebarIcon');
            let txt = document.getElementById('btnToggleSidebarText');
            if (!sb) return;
            sb.classList.toggle('collapsed');
            let isCollapsed = sb.classList.contains('collapsed');
            try {
                localStorage.setItem('flagpro_sidebar_collapsed', isCollapsed ? 'true' : 'false');
            } catch(e) {}
            if (icon) icon.textContent = isCollapsed ? '📑' : '☰';
            if (txt) txt.textContent = isCollapsed ? 'نمایش منو' : 'منو';

            // Re-render charts on resize
            setTimeout(() => {
                if (typeof drawEquityChart === 'function') drawEquityChart();
                if (typeof drawWeeklyBarChart === 'function' && typeof currentWeeklyBarMode !== 'undefined') drawWeeklyBarChart(currentWeeklyBarMode);
            }, 260);
        }

        function toggleDrawdownOverlay() {
            simState.showDrawdown = !simState.showDrawdown;
            let btn = document.getElementById('btnToggleDrawdown');
            let lbl = document.getElementById('lblToggleDrawdownState');
            if (btn && lbl) {
                if (simState.showDrawdown) {
                    lbl.textContent = 'روشن';
                    lbl.style.color = '#4ade80';
                    btn.style.background = '#1e1b4b';
                    btn.style.borderColor = '#6366f1';
                    btn.style.color = '#c7d2fe';
                } else {
                    lbl.textContent = 'خاموش';
                    lbl.style.color = '#94a3b8';
                    btn.style.background = '#0f172a';
                    btn.style.borderColor = '#334155';
                    btn.style.color = '#94a3b8';
                }
            }
            drawEquityChart();
        }

        function toggleTwoColLayout() {
            let container = document.getElementById('eqTwoColContainer');
            let btn = document.getElementById('btnToggleTwoCol');
            if (!container) return;
            if (container.classList.contains('single-col')) {
                container.classList.remove('single-col');
                if (btn) { btn.textContent = '⛶'; btn.title = 'حالت تمام‌صفحه'; }
            } else {
                container.classList.add('single-col');
                if (btn) { btn.textContent = '🗗'; btn.title = 'حالت دو ستونی'; }
            }
            setTimeout(() => {
                drawEquityChart();
            }, 50);
        }

        
        