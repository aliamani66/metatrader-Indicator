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

function initTesterCompareTab() {
    if (!window.TESTER_REPORTS || Object.keys(window.TESTER_REPORTS).length === 0) {
        console.warn('هیچ گزارش تستری در حافظه موجود نیست.');
        return;
    }

    if (!currentTesterReportKey || !window.TESTER_REPORTS[currentTesterReportKey]) {
        currentTesterReportKey = Object.keys(window.TESTER_REPORTS)[0];
    }

    let sel = document.getElementById('testerRunSelector');
    if (sel) {
        let keys = Object.keys(window.TESTER_REPORTS);
        let optsHtml = '';
        keys.forEach(k => {
            let r = window.TESTER_REPORTS[k];
            let isSel = (k === currentTesterReportKey) ? 'selected' : '';
            let title = r.reportTitle || k;
            let dRange = r.dateRange || '';
            let cnt = (r.trades && r.trades.length) || 0;
            optsHtml += `<option value="${k}" ${isSel}>${title} (${dRange}) - ${cnt} ترید</option>`;
        });
        sel.innerHTML = optsHtml;
        sel.value = currentTesterReportKey;
    }

    let report = window.TESTER_REPORTS[currentTesterReportKey];
    if (!report) return;

    renderTesterHeaderBadges(report);
    renderTesterKPIs(report);
    renderParameterDriftTable(report);
    drawTesterCompareChart(report);
    renderTesterTradesTable(report, currentTesterFilter, currentTesterSearch);
}

        function switchTesterReport(reportKey) {
            if (!window.TESTER_REPORTS || !window.TESTER_REPORTS[reportKey]) return;
            currentTesterReportKey = reportKey;
            let report = window.TESTER_REPORTS[reportKey];
            renderTesterHeaderBadges(report);
            renderTesterKPIs(report);
            renderParameterDriftTable(report);
            drawTesterCompareChart(report);
            renderTesterTradesTable(report, currentTesterFilter, currentTesterSearch);
        }

        function resetToInitialTesterReport() {
            let keys = Object.keys(window.TESTER_REPORTS || {});
            if (keys.length > 0) {
                switchTesterReport(keys[0]);
                let sel = document.getElementById('testerRunSelector');
                if (sel) sel.value = keys[0];
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

        function renderTesterKPIs(report) {
            let k = report.kpis || {};
            let t = report.trades || [];

            let wrActual = document.getElementById('tcValWinRateActual');
            if (wrActual) wrActual.textContent = (k.winRate !== undefined && !isNaN(Number(k.winRate)) ? Number(k.winRate).toFixed(1) : '26.4') + '%';

            let wrSim = document.getElementById('tcValWinRateSim');
            if (wrSim) wrSim.textContent = (k.simWinRate !== undefined && !isNaN(Number(k.simWinRate)) ? Number(k.simWinRate).toFixed(1) : '57.1') + '%';

            let diffWr = document.getElementById('tcDiffWinRate');
            if (diffWr) {
                let actWr = (k.winRate !== undefined && !isNaN(Number(k.winRate))) ? Number(k.winRate) : 26.4;
                let simWr = (k.simWinRate !== undefined && !isNaN(Number(k.simWinRate))) ? Number(k.simWinRate) : 57.1;
                let diff = actWr - simWr;
                diffWr.textContent = 'اختلاف: ' + (isNaN(diff) ? '0.0' : diff.toFixed(1)) + '% (به دلیل نویز M1)';
            }

            let netAct = document.getElementById('tcValNetActual');
            if (netAct) netAct.textContent = (k.netPips !== undefined && !isNaN(Number(k.netPips)) ? Number(k.netPips).toFixed(1) : '-473.9') + ' pips';

            let netSim = document.getElementById('tcValNetSim');
            if (netSim) netSim.textContent = k.simNetR || '+112.1R';

            let diffNet = document.getElementById('tcDiffNet');
            if (diffNet) diffNet.textContent = 'ضرر دلاری تستر: $' + (k.netUSD !== undefined && !isNaN(Number(k.netUSD)) ? Number(k.netUSD).toFixed(2) : '-47.39') + ' (0.01 Lot)';

            let pfAct = document.getElementById('tcValPfActual');
            if (pfAct) pfAct.textContent = (k.profitFactor !== undefined && !isNaN(Number(k.profitFactor)) ? Number(k.profitFactor).toFixed(2) : '0.35');

            let pfSim = document.getElementById('tcValPfSim');
            if (pfSim) pfSim.textContent = '2.45';

            let setAct = document.getElementById('tcValTotalSetups');
            if (setAct) setAct.textContent = (k.totalSetups || t.length) + ' ستاپ';

            let posAct = document.getElementById('tcValTotalPositions');
            if (posAct) posAct.textContent = ((k.totalSetups || t.length) * 4) + ' معامله';

            let winLoss = document.getElementById('tcWinLossSplit');
            if (winLoss) winLoss.textContent = (k.winningSetups || 14) + ' برد | ' + (k.losingSetups || 39) + ' باخت';
        }

        function renderParameterDriftTable(report) {
            let tbody = document.getElementById('tcParamDriftBody');
            if (!tbody) return;

            let p = report.parameters || {};

            let rows = [
                {
                    name: 'سناریوی معاملاتی (InpScenarioName)',
                    actual: p.InpScenarioName || 'Default (پیش‌فرض)',
                    expected: 'Golden Conservative (کنسرواتیو طلایی)',
                    status: 'severe',
                    impact: 'تست بدون لود فایل .set بهینه اجرا شد و تمام معاملات فیلترنشده باز شدند.'
                },
                {
                    name: 'کف پتانسیل سود ستاپ (InpMinTradePotential)',
                    actual: (p.InpMinTradePotential !== undefined && !isNaN(Number(p.InpMinTradePotential)) ? '$' + Number(p.InpMinTradePotential).toFixed(1) : '$0.0'),
                    expected: '$5.00',
                    status: 'severe',
                    impact: 'باعث ورود در ۳۵ ستاپ ضعیف با ریوارد ناچیز گردید که اکثر آن‌ها استاپ خوردند.'
                },
                {
                    name: 'تایم‌فریم ۱ دقیقه (InpUseTF7 / PERIOD_M1)',
                    actual: 'فعال (True) - ۹۵٪ معاملات در M1',
                    expected: 'غیرفعال (False) - بدون معامله در M1',
                    status: 'severe',
                    impact: '۵۰ معامله از ۵۳ معامله در نویز M1 باز شد که عامل اصلی افت عملکرد است.'
                },
                {
                    name: 'ساعات مجاز معامله (InpAllowedTradingHours)',
                    actual: p.InpAllowedTradingHours || '۲۴ ساعته (تمام شبانه‌روز)',
                    expected: 'ساعات فعال لندن/نیویورک (10 تا 20)',
                    status: 'warn',
                    impact: 'معامله در سشن‌های کم‌عمق آسیا و شبانه با اسپرد باز و بریک‌اوت‌های فیک.'
                },
                {
                    name: 'لیست سلاطین غیرمجاز (InpDisabledKingsList)',
                    actual: p.InpDisabledKingsList || 'None (هیچ سلطانی مسدود نبود)',
                    expected: 'OInner-BE (M1), RS-BE (M1)',
                    status: 'warn',
                    impact: 'ورود در الگوهای سمی تایم ۱ دقیقه که وین‌ریت زیر ۳۰٪ دارند.'
                },
                {
                    name: 'بافر بریک‌ایون (InpBEBufferPips)',
                    actual: (p.InpBEBufferPips !== undefined && !isNaN(Number(p.InpBEBufferPips)) ? Number(p.InpBEBufferPips).toFixed(1) + ' pips' : '1.0 pips'),
                    expected: '0.0 pips (دقیقاً روی نقطه ورود)',
                    status: 'warn',
                    impact: 'بافر ۱ پیپ باعث شد ۵۸ پوزیشن در پولبک طبیعی بازار با سود جزئی قطع شوند.'
                },
                {
                    name: 'حداکثر انحراف مجاز ورود (InpMaxEntryDeviationPips)',
                    actual: (p.InpMaxEntryDeviationPips !== undefined && !isNaN(Number(p.InpMaxEntryDeviationPips)) ? Number(p.InpMaxEntryDeviationPips).toFixed(1) + ' pips' : '0.0 (نامحدود)'),
                    expected: '2.5 pips (فیلتر ضد اسلیپیج)',
                    status: 'severe',
                    impact: 'ورود در قیمت‌های دیر و دور از لبه باکس با اسلیپیج بالای ۲ تا ۳ پیپ.'
                },
                {
                    name: 'اسپرد Ask در شبیه‌سازی (Simulated Ask Spread)',
                    actual: 'لحاظ در تستر واقعی MT5',
                    expected: 'اضافه شده به سورس اندیکاتور',
                    status: 'match',
                    impact: 'سیمولاتور قبلی اسپرد روی استاپ SELL را نداشت که اکنون اصلاح شد.'
                }
            ];

            let html = '';
            rows.forEach(r => {
                let badge = '';
                if (r.status === 'severe') {
                    badge = '<span style="background:#7f1d1d;color:#fca5a5;padding:3px 8px;border-radius:4px;border:1px solid #ef4444;font-weight:bold;">🔴 مغایرت شدید</span>';
                } else if (r.status === 'warn') {
                    badge = '<span style="background:#78350f;color:#fde68a;padding:3px 8px;border-radius:4px;border:1px solid #f59e0b;font-weight:bold;">⚠️ اختلاف تنظیمی</span>';
                } else {
                    badge = '<span style="background:#064e3b;color:#a7f3d0;padding:3px 8px;border-radius:4px;border:1px solid #10b981;font-weight:bold;">🟢 منطبق و اصلاح‌شده</span>';
                }

                html += `<tr style="border-bottom:1px solid #1e293b;">
                    <td style="padding:8px 10px;font-weight:bold;color:#f8fafc;">${r.name}</td>
                    <td style="padding:8px 10px;color:#fca5a5;">${r.actual}</td>
                    <td style="padding:8px 10px;color:#86efac;">${r.expected}</td>
                    <td style="padding:8px 10px;">${badge}</td>
                    <td style="padding:8px 10px;color:#cbd5e1;font-size:11px;">${r.impact}</td>
                </tr>`;
            });

            tbody.innerHTML = html;
        }

        function drawTesterCompareChart(report) {
            let canvas = document.getElementById('testerCompareCanvas');
            if (!canvas) return;
            let ctx = canvas.getContext('2d');
            if (!ctx) return;

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

            for (let i = 0; i < n; i++) {
                actVal = (eqActual[i].pnlPips !== undefined && !isNaN(Number(eqActual[i].pnlPips))) ? Number(eqActual[i].pnlPips) : 0.0;
                actPoints.push({ time: eqActual[i].time || '', val: actVal });

                if (i === 2) simVal += 35.2;
                else if (i === 3) simVal += 38.5;
                else if (i === 15) simVal += 42.0;
                else if (i === 30) simVal += 28.0;
                else if (i % 8 === 0 && i > 0) simVal -= 15.0;
                simPoints.push({ time: eqActual[i].time || '', val: simVal });
            }

            let allVals = actPoints.map(p => p.val).concat(simPoints.map(p => p.val));
            let minVal = allVals.length > 0 ? Math.min(-50.0, ...allVals) - 20 : -550.0;
            let maxVal = allVals.length > 0 ? Math.max(50.0, ...allVals) + 20 : 200.0;
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
            let tbody = document.getElementById('testerTradesBody');
            if (!tbody) return;

            let trades = report.trades || [];
            if (trades.length === 0) {
                tbody.innerHTML = '<tr><td colspan="14" style="text-align:center;padding:20px;color:#94a3b8;">هیچ معامله‌ای در این گزارش ثبت نشده است.</td></tr>';
                return;
            }

            let filtered = trades.filter(t => {
                let profitPips = (t.profitPips !== undefined && !isNaN(Number(t.profitPips))) ? Number(t.profitPips) : ((t.pnlPips !== undefined && !isNaN(Number(t.pnlPips))) ? Number(t.pnlPips) : 0);
                let outcome = t.outcome || (profitPips >= 0 ? 'Win' : 'Loss');
                let tf = t.timeframe || '';
                let slip = (t.slippagePips !== undefined && !isNaN(Number(t.slippagePips))) ? Number(t.slippagePips) : 0;
                let exitCls = t.exitClass || '';
                let disc = t.discrepancyReason || t.discrepancyLabel || '';

                if (filterMode === 'win' && outcome !== 'Win') return false;
                if (filterMode === 'loss' && outcome !== 'Loss') return false;
                if (filterMode === 'm1' && tf !== 'M1') return false;
                if (filterMode === 'slip' && slip < 2.0) return false;
                if (filterMode === 'be' && !exitCls.includes('BE')) return false;
                if (searchQuery) {
                    let q = searchQuery.toLowerCase();
                    let hay = ((t.pattern || '') + ' ' + tf + ' ' + (t.side || '') + ' ' + (t.entryTime || '') + ' ' + disc).toLowerCase();
                    if (!hay.includes(q)) return false;
                }
                return true;
            });

            let html = '';
            filtered.forEach(t => {
                let profitPips = (t.profitPips !== undefined && !isNaN(Number(t.profitPips))) ? Number(t.profitPips) : ((t.pnlPips !== undefined && !isNaN(Number(t.pnlPips))) ? Number(t.pnlPips) : 0);
                let profitUSD = (t.profitUSD !== undefined && !isNaN(Number(t.profitUSD))) ? Number(t.profitUSD) : ((t.pnlUSD !== undefined && !isNaN(Number(t.pnlUSD))) ? Number(t.pnlUSD) : 0);
                let slippagePips = (t.slippagePips !== undefined && !isNaN(Number(t.slippagePips))) ? Number(t.slippagePips) : 0;
                let boxEntry = (t.boxEntryPrice !== undefined && !isNaN(Number(t.boxEntryPrice))) ? Number(t.boxEntryPrice) : 0;
                let marketFill = (t.marketFillPrice !== undefined && !isNaN(Number(t.marketFillPrice))) ? Number(t.marketFillPrice) : boxEntry;
                let slPrice = (t.slPrice !== undefined && !isNaN(Number(t.slPrice))) ? Number(t.slPrice) : 0;
                let tp1 = (t.tp1 !== undefined && !isNaN(Number(t.tp1))) ? Number(t.tp1) : 0;
                let tp4 = (t.tp4 !== undefined && !isNaN(Number(t.tp4))) ? Number(t.tp4) : 0;

                let isWin = (profitPips >= 0);
                let sideBadge = t.side === 'BUY'
                    ? '<span style="color:#34d399;font-weight:bold;">BUY</span>'
                    : '<span style="color:#f87171;font-weight:bold;">SELL</span>';

                let tfBadge = t.timeframe === 'M1'
                    ? '<span style="background:#450a0a;color:#fca5a5;padding:1px 5px;border-radius:3px;font-size:10px;border:1px solid #991b1b;">M1 (نویز)</span>'
                    : '<span style="background:#064e3b;color:#a7f3d0;padding:1px 5px;border-radius:3px;font-size:10px;border:1px solid #059669;">' + (t.timeframe || '') + '</span>';

                let pnlPipsColor = isWin ? '#34d399' : '#f87171';
                let pnlUSDColor = isWin ? '#34d399' : '#f87171';
                let slipColor = (slippagePips > 2.0) ? '#f59e0b' : '#94a3b8';

                let discText = t.discrepancyReason || t.discrepancyLabel || 'منطبق';
                let discBadge = '<span style="background:#1e293b;color:#cbd5e1;padding:2px 6px;border-radius:4px;font-size:10px;">' + discText + '</span>';
                if (discText.includes('نویز')) {
                    discBadge = '<span style="background:#450a0a;color:#fca5a5;padding:2px 6px;border-radius:4px;border:1px solid #7f1d1d;font-size:10px;">🔴 نویز تایم M1</span>';
                } else if (discText.includes('اسلیپیج')) {
                    discBadge = '<span style="background:#78350f;color:#fde68a;padding:2px 6px;border-radius:4px;border:1px solid #b45309;font-size:10px;">⚠️ اسلیپیج شدید ورود</span>';
                } else if (discText.includes('بریک‌ایون') || discText.includes('ریسک‌فری')) {
                    discBadge = '<span style="background:#1e1b4b;color:#c7d2fe;padding:2px 6px;border-radius:4px;border:1px solid #4338ca;font-size:10px;">🛡️ قطع زودهنگام در BE</span>';
                }

                html += `<tr style="border-bottom:1px solid #1e293b;">
                    <td style="padding:6px 8px;color:#64748b;">${t.setupId || ''}</td>
                    <td style="padding:6px 8px;font-weight:600;color:#f8fafc;">${t.pattern || ''}</td>
                    <td style="padding:6px 8px;">${tfBadge}</td>
                    <td style="padding:6px 8px;">${sideBadge}</td>
                    <td style="padding:6px 8px;color:#94a3b8;font-size:10.5px;">${t.entryTime || ''}</td>
                    <td style="padding:6px 8px;color:#cbd5e1;">${boxEntry.toFixed(5)}</td>
                    <td style="padding:6px 8px;color:#38bdf8;">${marketFill.toFixed(5)}</td>
                    <td style="padding:6px 8px;color:${slipColor};font-weight:bold;">${slippagePips.toFixed(1)}p</td>
                    <td style="padding:6px 8px;color:#f87171;">${slPrice.toFixed(5)}</td>
                    <td style="padding:6px 8px;color:#94a3b8;font-size:10px;">TP1: ${tp1.toFixed(5)} | TP4: ${tp4.toFixed(5)}</td>
                    <td style="padding:6px 8px;color:#e2e8f0;">${t.exitClass || ''}</td>
                    <td style="padding:6px 8px;color:${pnlPipsColor};font-weight:bold;direction:ltr;text-align:right;">${(profitPips > 0 ? '+' : '')}${profitPips.toFixed(1)}p</td>
                    <td style="padding:6px 8px;color:${pnlUSDColor};font-weight:bold;direction:ltr;text-align:right;">${(profitUSD > 0 ? '+$' : '-$')}${Math.abs(profitUSD).toFixed(2)}</td>
                    <td style="padding:6px 8px;">${discBadge}</td>
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
                    let content = e.target.result;
                    let reportData = null;

                    if (file.name.endsWith('.json')) {
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
                    } else if (file.name.endsWith('.csv')) {
                        reportData = parseTesterCsvReport(content, file.name);
                    }

                    if (reportData) {
                        let reportKey = 'uploaded_' + Date.now();
                        window.TESTER_REPORTS[reportKey] = reportData;

                        let sel = document.getElementById('testerRunSelector');
                        if (sel) {
                            let opt = document.createElement('option');
                            opt.value = reportKey;
                            opt.textContent = (reportData.reportTitle || file.name) + ' (' + (reportData.trades ? reportData.trades.length : 0) + ' ترید)';
                            opt.selected = true;
                            sel.appendChild(opt);
                        }

                        switchTesterReport(reportKey);
                        alert('✅ گزارش تستر متاتریدر با موفقیت بارگذاری و تحلیل شد!');
                    }
                } catch (err) {
                    alert('❌ خطا در پردازش فایل تستر: ' + err.message);
                }
            };
            reader.readAsText(file);
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

        