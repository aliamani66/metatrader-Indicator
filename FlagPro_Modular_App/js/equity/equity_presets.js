// Global Simulation State
var simState = (typeof simState !== 'undefined') ? simState : {
    mode: 'all', // Default: Raw Test (All Trades)
    slMode: 0,   // 0: Fixed, 1: ATR Buffer, 2: Pure ATR, 3: Box Percent
    enabledKings: new Set(),
    allowedHours: new Array(24).fill(true),
    minProfit: 0.0,
    consecLossTrigger: 0,
    consecLossSkipCount: 1,
    consecLossSkipDay: false,
    showDrawdown: true,
    filterNightHours: false,
    filterPreLondonHunt: false,
    filterToxicPatterns: false,
    filterSingleLS: false,
    filterPureFlags: false,
    enableHTFDominance: false,
    maxConcurrentLimit: 0
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
                b.innerHTML = '⚡ اعمال';
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

                // Track active preset globally for synchronizing with Tester Compare tab
                window.currentActivePreset = p;
                window.currentActivePresetIdx = idx;
                window.currentActivePresetTitle = p.title || p.name || ('سناریوی ' + idx);
                window.currentActiveSimSettings = JSON.parse(JSON.stringify(simState));

                // 1. Set mode to kings
                simState.mode = 'kings';
                let btnK = document.getElementById('btnEqKings');
                let btnA = document.getElementById('btnEqAll');
                if (btnK) {
                    btnK.style.background = '#eab308';
                    btnK.style.color = '#000';
                    btnK.classList.add('active');
                }
                if (btnA) {
                    btnA.style.background = 'transparent';
                    btnA.style.color = '#94a3b8';
                    btnA.classList.remove('active');
                }
                let lbl = document.getElementById('lblActiveEquityScenario');
                if (lbl) {
                    lbl.textContent = p.title || p.name || '👑 سناریوی فیلترشده';
                    lbl.style.borderColor = '#eab308';
                    lbl.style.color = '#fde047';
                    lbl.style.background = '#2a1b00';
                }

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

                // 4B. Configure MT5 Anti-Stop Filters
                let isBase = (p.id === 'preset-base');
                simState.filterNightHours = isBase ? false : (p.hours_name === 'lon_ny' || p.hours_name === 'no_night');
                simState.filterPreLondonHunt = isBase ? false : true;
                simState.filterToxicPatterns = isBase ? false : true;
                simState.filterSingleLS = isBase ? false : true;
                simState.filterPureFlags = isBase ? false : true;

                // 5. Update UI components
                if (typeof renderSimKingsGrid === 'function') renderSimKingsGrid();
                if (typeof renderSimHoursBar === 'function') renderSimHoursBar();
                if (typeof syncMT5FilterCheckboxesUI === 'function') syncMT5FilterCheckboxesUI();

                // 6. Highlight active preset row
                clearPresetActiveState();
                let activeRow = document.getElementById('presetRow' + idx);
                if (activeRow) {
                    activeRow.style.outline = '2px solid #38bdf8';
                    activeRow.style.boxShadow = '0 0 16px rgba(56, 189, 248, 0.4)';
                }
                let activeBtn = document.getElementById('btnApplyPreset' + idx);
                if (activeBtn) {
                    activeBtn.innerHTML = '✅ فعال';
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
                                '<span>🤖 تستر</span>' +
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

            window.currentActivePreset = p;
            window.currentActivePresetId = p.id;
            window.currentActivePresetTitle = p.name || p.title || 'سناریوی شخصی';
            window.currentActiveSimSettings = JSON.parse(JSON.stringify(simState));

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

