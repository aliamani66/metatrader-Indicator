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

        function syncMT5FilterCheckboxesUI() {
            const filterDefs = [
                { id: 'chkFilterNight', lbl: 'lblFilterNight', key: 'filterNightHours', activeBorder: '#38bdf8' },
                { id: 'chkFilterPreLondon', lbl: 'lblFilterPreLondon', key: 'filterPreLondonHunt', activeBorder: '#38bdf8' },
                { id: 'chkFilterToxic', lbl: 'lblFilterToxic', key: 'filterToxicPatterns', activeBorder: '#f87171' },
                { id: 'chkFilterSingleLS', lbl: 'lblFilterSingleLS', key: 'filterSingleLS', activeBorder: '#facc15' },
                { id: 'chkFilterPureFlags', lbl: 'lblFilterPureFlags', key: 'filterPureFlags', activeBorder: '#34d399' }
            ];
            filterDefs.forEach(item => {
                let el = document.getElementById(item.id);
                let lbl = document.getElementById(item.lbl);
                let on = !!simState[item.key];
                if (el) el.checked = on;
                if (lbl) {
                    lbl.style.borderColor = on ? item.activeBorder : '#1e293b';
                    lbl.style.background = on ? '#0c223a' : '#091422';
                    lbl.style.boxShadow = on ? ('0 0 10px ' + item.activeBorder + '33') : 'none';
                }
            });
        }

        function toggleMT5Filter(key, isChecked) {
            clearPresetActiveState();
            simState[key] = !!isChecked;
            syncMT5FilterCheckboxesUI();
            runEquitySimulation();
        }

        function setAllMT5Filters(enableAll) {
            clearPresetActiveState();
            simState.filterNightHours = !!enableAll;
            simState.filterPreLondonHunt = !!enableAll;
            simState.filterToxicPatterns = !!enableAll;
            simState.filterSingleLS = !!enableAll;
            simState.filterPureFlags = !!enableAll;
            syncMT5FilterCheckboxesUI();
            runEquitySimulation();
        }
        window.syncMT5FilterCheckboxesUI = syncMT5FilterCheckboxesUI;
        window.toggleMT5Filter = toggleMT5Filter;
        window.setAllMT5Filters = setAllMT5Filters;

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
            simState.mode = 'all'; // Reset to Raw Test (All Trades)
            if (Array.isArray(kingsSimList)) {
                kingsSimList.forEach(k => simState.enabledKings.add(k.kk));
            }
            simState.allowedHours.fill(true);
            simState.minProfit = 0.0;
            window.currentActivePreset = null;
            window.currentActivePresetIdx = -1;
            window.currentActivePresetTitle = '📊 نتیجه تست خام (کل معاملات چارت)';
            window.currentActiveSimSettings = JSON.parse(JSON.stringify(simState));

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
            if (btnK) {
                btnK.style.background = 'transparent';
                btnK.style.color = '#94a3b8';
                btnK.classList.remove('active');
            }
            if (btnA) {
                btnA.style.background = '#0284c7';
                btnA.style.color = '#fff';
                btnA.classList.add('active');
            }
            let lbl = document.getElementById('lblActiveEquityScenario');
            if (lbl) {
                lbl.textContent = '📊 نتیجه تست خام (کل معاملات چارت)';
                lbl.style.borderColor = '#0284c7';
                lbl.style.color = '#38bdf8';
                lbl.style.background = '#0f2942';
            }

            simState.consecLossTrigger = 0;
            simState.consecLossSkipCount = 1;
            simState.consecLossSkipDay = false;
            let selTrig = document.getElementById('selConsecTrigger');
            if (selTrig) selTrig.value = 0;
            let selAct = document.getElementById('selConsecAction');
            if (selAct) selAct.value = 'skip_1';
            syncConsecButtonsUI();

            simState.filterNightHours = false;
            simState.filterPreLondonHunt = false;
            simState.filterToxicPatterns = false;
            simState.filterSingleLS = false;
            simState.filterPureFlags = false;
            syncMT5FilterCheckboxesUI();

            renderSimKingsGrid();
            renderSimHoursBar();
            runEquitySimulation();
        }

        function switchEquityMode(mode) {
            simState.mode = mode;
            let btnK = document.getElementById('btnEqKings');
            let btnA = document.getElementById('btnEqAll');
            let lbl = document.getElementById('lblActiveEquityScenario');
            if(mode === 'kings') {
                if(btnK) {
                    btnK.style.background = '#eab308';
                    btnK.style.color = '#000';
                    btnK.classList.add('active');
                }
                if(btnA) {
                    btnA.style.background = 'transparent';
                    btnA.style.color = '#94a3b8';
                    btnA.classList.remove('active');
                }
                if(lbl) {
                    lbl.textContent = window.currentActivePresetTitle || '👑 سناریوی فیلترشده';
                    lbl.style.borderColor = '#eab308';
                    lbl.style.color = '#fde047';
                    lbl.style.background = '#2a1b00';
                }
            } else {
                if(btnK) {
                    btnK.style.background = 'transparent';
                    btnK.style.color = '#94a3b8';
                    btnK.classList.remove('active');
                }
                if(btnA) {
                    btnA.style.background = '#0284c7';
                    btnA.style.color = '#fff';
                    btnA.classList.add('active');
                }
                if(lbl) {
                    lbl.textContent = '📊 نتیجه تست خام (کل معاملات چارت)';
                    lbl.style.borderColor = '#0284c7';
                    lbl.style.color = '#38bdf8';
                    lbl.style.background = '#0f2942';
                }
                window.currentActivePreset = null;
                window.currentActivePresetIdx = -1;
                window.currentActivePresetTitle = '📊 نتیجه تست خام (کل معاملات چارت)';
                clearPresetActiveState();
            }
            runEquitySimulation();
        }

