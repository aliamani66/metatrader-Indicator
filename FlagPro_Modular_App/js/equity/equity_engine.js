        function getTfRank(tf) {
            if (!tf) return 1;
            let s = String(tf).toUpperCase().replace('PERIOD_', '').trim();
            if (s === 'MN' || s === 'MN1') return 8;
            if (s === 'W1') return 7;
            if (s === 'D1') return 6;
            if (s === 'H4') return 5;
            if (s === 'H1') return 4;
            if (s === 'M30') return 3.5;
            if (s === 'M15') return 3;
            if (s === 'M5') return 2;
            if (s === 'M1') return 1;
            let num = parseInt(s.replace(/\D/g, ''), 10);
            return isNaN(num) ? 1 : num;
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
            let activeOpenPositions = [];
            let htfSuppressedCount = 0;
            let concurrencySuppressedCount = 0;

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

                // MT5 Smart Anti-Stop & Pattern Filters (Filters 1-5)
                if (simState.filterNightHours && (t.h >= 21 || t.h <= 1)) continue;
                if (simState.filterPreLondonHunt && t.h === 7) continue;
                if (simState.filterToxicPatterns && t.r && (t.r.includes('LS-BE > RS-BE') || t.r.includes('LS-BU > RS-BU'))) continue;
                if (simState.filterSingleLS && (t.r === 'LS-BE' || t.r === 'LS-BU' || t.r === 'LS')) continue;
                if (simState.filterPureFlags && t.r && (t.r.startsWith('Flag-') || t.r === 'Flag' || (!t.r.includes('LS') && !t.r.includes('RS') && !t.r.includes('OInner') && !t.r.includes('S-')))) continue;

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

                // Active positions concurrency and HTF dominance checks (Task 7)
                let enTime = t.t || '';
                let exTime = t.xt || t.t || '';
                if (!exTime || exTime <= enTime) {
                    exTime = enTime + "z";
                }
                // 1. Purge closed positions prior to or at enTime
                activeOpenPositions = activeOpenPositions.filter(p => p.exitTime > enTime);

                // 2. HTF Trade Dominance Filter (Task 7)
                // If a position in a higher timeframe is already open, suppress incoming lower timeframe trades
                if (simState.enableHTFDominance) {
                    let candRank = getTfRank(t.tf);
                    let hasHigherActive = activeOpenPositions.some(p => p.tfRank > candRank);
                    if (hasHigherActive) {
                        htfSuppressedCount++;
                        continue;
                    }
                }

                // 3. Max Concurrent Open Positions Filter (Task 7)
                if (simState.maxConcurrentLimit > 0 && activeOpenPositions.length >= simState.maxConcurrentLimit) {
                    concurrencySuppressedCount++;
                    continue;
                }

                // Trade accepted!
                activeOpenPositions.push({
                    exitTime: exTime,
                    tf: t.tf,
                    tfRank: getTfRank(t.tf)
                });
                let curConcurrent = activeOpenPositions.length;
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

            // Globally expose live simulation stats for Tester Compare sync
            window.currentActiveSimStats = {
                wr: wr,
                pf: pf,
                net: net,
                totalTrades: totalTrades,
                winCnt: winCnt,
                maxDD: maxDD,
                grossProfit: grossP,
                grossLoss: grossL,
                htfSuppressed: htfSuppressedCount,
                concurrencySuppressed: concurrencySuppressedCount,
                maxConcurrent: maxConcurrent
            };
            window.currentActiveSimSettings = JSON.parse(JSON.stringify(simState));

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

            // Update HTF Dominance & Concurrency Badges (Task 7)
            let elHTFBadge = document.getElementById('simHTFActiveBadge');
            if (elHTFBadge) {
                if (simState.enableHTFDominance) {
                    elHTFBadge.textContent = 'روشن (' + htfSuppressedCount + ' نویز M1/M5 حذف شد)';
                    elHTFBadge.style.background = '#064e3b';
                    elHTFBadge.style.color = '#34d399';
                } else {
                    elHTFBadge.textContent = 'خاموش (معاملات آزاد)';
                    elHTFBadge.style.background = '#1e293b';
                    elHTFBadge.style.color = '#94a3b8';
                }
            }
            let elConcBadge = document.getElementById('simConcLimitBadge');
            if (elConcBadge) {
                if (simState.maxConcurrentLimit > 0) {
                    elConcBadge.textContent = 'سقف ' + simState.maxConcurrentLimit + ' پوزیشن (' + concurrencySuppressedCount + ' مازاد مسدود شد)';
                    elConcBadge.style.background = '#0c4a6e';
                    elConcBadge.style.color = '#38bdf8';
                } else {
                    elConcBadge.textContent = 'نامحدود (بدون سقف)';
                    elConcBadge.style.background = '#1e293b';
                    elConcBadge.style.color = '#94a3b8';
                }
            }

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
            updateEqCompareTable();
            drawEquityChart();
            requestAnimationFrame(() => { drawEquityChart(); });
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
        }

        function updateEqCompareTable() {
            let tbody = document.getElementById('eqCompareTableBody');
            if (!tbody) return;

            // 1. Raw Baseline (All chart trades without any filter)
            let rawTrades = (typeof simTrades !== 'undefined' && simTrades) ? simTrades : [];
            let balRaw = 100.0;
            let peakRaw = 100.0;
            let maxDDRaw = 0.0;

            for (let i = 0; i < rawTrades.length; i++) {
                let p = rawTrades[i].p || 0.0;
                balRaw += p;
                if (balRaw > peakRaw) peakRaw = balRaw;
                let dd = peakRaw - balRaw;
                if (dd > maxDDRaw) maxDDRaw = dd;
            }
            let netRaw = balRaw - 100.0;
            let netRawPct = (netRaw / 100.0) * 100.0;
            let maxDDRawPct = peakRaw > 0 ? (maxDDRaw / peakRaw) * 100.0 : 0.0;

            // 2. Filtered / Kings Strategy (Current active simulation)
            let curTrades = (typeof currentSimPts !== 'undefined' && currentSimPts && currentSimPts.length > 1) ? (currentSimPts.length - 1) : 0;
            let curBal = (typeof currentSimPts !== 'undefined' && currentSimPts && currentSimPts.length > 0) ? currentSimPts[currentSimPts.length - 1].b : 100.0;
            let curNet = curBal - 100.0;
            let curNetPct = (curNet / 100.0) * 100.0;

            let curPeak = 100.0;
            let curMaxDD = 0.0;
            if (typeof currentSimPts !== 'undefined' && currentSimPts) {
                for (let i = 0; i < currentSimPts.length; i++) {
                    let b = currentSimPts[i].b;
                    if (b > curPeak) curPeak = b;
                    let dd = curPeak - b;
                    if (dd > curMaxDD) curMaxDD = dd;
                }
            }
            let curMaxDDPct = curPeak > 0 ? (curMaxDD / curPeak) * 100.0 : 0.0;

            // Strategy Title
            let stratName = "👑 سبد سلاطین منتخب (گزینش هوشمند)";
            if (typeof simState !== 'undefined' && simState) {
                if (simState.mode === 'kings') {
                    let kCount = simState.enabledKings ? simState.enabledKings.size : 0;
                    stratName = `👑 سبد سلاطین ${kCount} گانه (گزینش هوشمند)`;
                } else if (simState.mode === 'all') {
                    stratName = "📊 تست خام چارت (معاملات فیلترشده جاری)";
                } else {
                    stratName = "📊 استراتژی فیلترشده جاری";
                }
            }

            let curNetColor = curNet >= 0 ? '#00e676' : '#ef4444';
            let curNetSign = curNet >= 0 ? '+$' : '-$';
            let curPctSign = curNetPct >= 0 ? '+' : '';
            let curBadge = curNet >= 0 
                ? '<span style="background:#064e3b;color:#34d399;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">💎 رشد مستمر و اکوئیتی صعودی</span>'
                : '<span style="background:#451a03;color:#fca5a5;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">⚠️ نیاز به بهینه‌سازی فیلترها</span>';

            let rawNetColor = netRaw >= 0 ? '#00e676' : '#ef4444';
            let rawNetSign = netRaw >= 0 ? '+$' : '-$';
            let rawPctSign = netRawPct >= 0 ? '+' : '';
            let rawBadge = netRaw >= 0
                ? '<span style="background:#064e3b;color:#34d399;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">✅ سودآور در کل چارت</span>'
                : '<span style="background:#451a03;color:#fca5a5;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">⚠️ فرسایش ناشی از نویزها</span>';

            tbody.innerHTML = `
                <tr style="border-bottom:1px solid #334155;">
                    <td style="font-weight:bold;color:#facc15;">${stratName}</td>
                    <td style="text-align:center;font-weight:bold;color:#38bdf8;">${curTrades}</td>
                    <td style="text-align:center;">$100</td>
                    <td style="text-align:center;font-weight:bold;color:${curNetColor};">$${Math.round(curBal).toLocaleString()}</td>
                    <td style="text-align:center;font-weight:bold;color:${curNetColor};">${curNetSign}${Math.abs(Math.round(curNet)).toLocaleString()}</td>
                    <td style="text-align:center;font-weight:bold;color:${curNetColor};">${curPctSign}${curNetPct.toFixed(1)}٪</td>
                    <td style="text-align:center;color:#34d399;font-weight:bold;">$${Math.round(curMaxDD)} (${curMaxDDPct.toFixed(1)}٪)</td>
                    <td style="text-align:center;">${curBadge}</td>
                </tr>
                <tr>
                    <td style="font-weight:bold;color:#94a3b8;">🌐 کل ساختارهای خام چارت (بدون فیلتر)</td>
                    <td style="text-align:center;font-weight:bold;color:#94a3b8;">${rawTrades.length}</td>
                    <td style="text-align:center;">$100</td>
                    <td style="text-align:center;font-weight:bold;color:${rawNetColor};">$${Math.round(balRaw).toLocaleString()}</td>
                    <td style="text-align:center;font-weight:bold;color:${rawNetColor};">${rawNetSign}${Math.abs(Math.round(netRaw)).toLocaleString()}</td>
                    <td style="text-align:center;font-weight:bold;color:${rawNetColor};">${rawPctSign}${netRawPct.toFixed(1)}٪</td>
                    <td style="text-align:center;color:#ef4444;font-weight:bold;">$${Math.round(maxDDRaw)} (${maxDDRawPct.toFixed(1)}٪)</td>
                    <td style="text-align:center;">${rawBadge}</td>
                </tr>
            `;
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
                                        <span>🤖 تستر</span>
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

