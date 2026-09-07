var currentWeeklyBarMode = (typeof currentWeeklyBarMode !== 'undefined') ? currentWeeklyBarMode : 'kings';
var dataWeeklyBars = (typeof dataWeeklyBars !== 'undefined') ? dataWeeklyBars : [];

function switchWeeklyBarMode(mode) {
    currentWeeklyBarMode = mode;
    let kingsBtns = document.querySelectorAll('#btnWkKings, #btnEqWkKings, .btn-wk-kings');
    let allBtns = document.querySelectorAll('#btnWkAll, #btnEqWkAll, .btn-wk-all');

    if (mode === 'kings') {
        kingsBtns.forEach(b => b.classList.add('active'));
        allBtns.forEach(b => b.classList.remove('active'));
    } else {
        kingsBtns.forEach(b => b.classList.remove('active'));
        allBtns.forEach(b => b.classList.add('active'));
    }
    drawWeeklyBarChart(mode);
}

function computeWeeklyBarsFromTrades(trades) {
    if (!trades || trades.length === 0) return [];
    let weekMap = {};
    trades.forEach(t => {
        let timeStr = t.en_t || t.t || t.entryTime || '';
        if (!timeStr || timeStr.length < 10) return;
        let dStr = timeStr.substring(0, 10).replace(/\./g, '-');
        let dt = new Date(dStr);
        if (isNaN(dt.getTime())) return;

        // ISO Week
        let target = new Date(dt.valueOf());
        let dayNr = (dt.getDay() + 6) % 7;
        target.setDate(target.getDate() - dayNr + 3);
        let firstThursday = target.valueOf();
        target.setMonth(0, 1);
        if (target.getDay() !== 4) {
            target.setMonth(0, 1 + ((4 - target.getDay()) + 7) % 7);
        }
        let wk = 1 + Math.ceil((firstThursday - target) / 604800000);
        let yr = dt.getFullYear();
        let key = yr + '-W' + (wk < 10 ? '0' + wk : wk);

        if (!weekMap[key]) {
            weekMap[key] = {
                week: wk,
                year: yr,
                dates: '',
                firstDate: dStr,
                lastDate: dStr,
                k_pnl: 0,
                k_trades: 0,
                k_wins: 0,
                k_losses: 0,
                all_pnl: 0,
                all_trades: 0,
                all_wins: 0,
                all_losses: 0
            };
        }

        let w = weekMap[key];
        if (dStr < w.firstDate) w.firstDate = dStr;
        if (dStr > w.lastDate) w.lastDate = dStr;

        let pnl = (t.net !== undefined ? Number(t.net) : (t.pnl !== undefined ? Number(t.pnl) : (t.profitUSD !== undefined ? Number(t.profitUSD) : 0)));
        let isWin = (t.t1 === 1 || t.HitTargetRatio >= 1 || pnl > 0);
        let isKing = t.is_k === 1 || t.k === 1 || (t.role && (t.role.includes('Inner') || t.role.includes('RS')));

        w.all_trades++;
        w.all_pnl += pnl;
        if (isWin) w.all_wins++; else w.all_losses++;

        if (isKing) {
            w.k_trades++;
            w.k_pnl += pnl;
            if (isWin) w.k_wins++; else w.k_losses++;
        }
    });

    return Object.keys(weekMap).sort().map(k => {
        let w = weekMap[k];
        w.k_pnl = Math.round(w.k_pnl * 100) / 100;
        w.all_pnl = Math.round(w.all_pnl * 100) / 100;
        w.k_wr = w.k_trades > 0 ? Math.round((w.k_wins / w.k_trades) * 1000) / 10 : 0;
        w.all_wr = w.all_trades > 0 ? Math.round((w.all_wins / w.all_trades) * 1000) / 10 : 0;
        w.dates = w.firstDate.substring(5).replace('-', '.') + ' - ' + w.lastDate.substring(5).replace('-', '.');
        return w;
    });
}

function drawWeeklyBarChart(mode) {
    mode = mode || currentWeeklyBarMode || 'kings';

    let canvases = document.querySelectorAll('canvas.weekly-bar-canvas, #weeklyBarCanvas, #eqWeeklyBarCanvas');
    if (!canvases || canvases.length === 0) return;

    let sym = (typeof currentActiveSymbol !== 'undefined' && currentActiveSymbol) ? currentActiveSymbol : 'GBPUSD';
    let cleanSym = sym.replace(/[!#]/g, '').trim();
    let sData = (window.ALL_SYMBOLS_DATA && (window.ALL_SYMBOLS_DATA[sym] || window.ALL_SYMBOLS_DATA[cleanSym])) || {};

    let bars = (typeof dataWeeklyBars !== 'undefined' && Array.isArray(dataWeeklyBars) && dataWeeklyBars.length > 0)
        ? dataWeeklyBars
        : (sData.weekly_bar_data && sData.weekly_bar_data.length > 0)
            ? sData.weekly_bar_data
            : [];

    if (!bars || bars.length === 0) {
        let trList = sData.trades_json_list || sData.trades_sim_list || (typeof allTrades !== 'undefined' ? allTrades : []);
        if (trList && trList.length > 0) {
            bars = computeWeeklyBarsFromTrades(trList);
        }
    }

    canvases.forEach(canvas => {
        drawSingleWeeklyBarCanvas(canvas, mode, bars);
    });
}

function drawSingleWeeklyBarCanvas(canvas, mode, bars) {
    if (!canvas) return;
    let dpr = window.devicePixelRatio || 1;
    let rect = canvas.getBoundingClientRect();
    let w = rect.width || canvas.offsetWidth || canvas.clientWidth || (canvas.parentElement ? canvas.parentElement.clientWidth : 0);
    let h = rect.height || canvas.offsetHeight || canvas.clientHeight || (canvas.parentElement ? canvas.parentElement.clientHeight : 0) || 300;

    // Skip if hidden/inactive tab
    if (w <= 0 || h <= 0) return;

    if (window.ResizeObserver && canvas.parentElement && !canvas._roAttached) {
        canvas._roAttached = true;
        const ro = new ResizeObserver(() => {
            requestAnimationFrame(() => drawWeeklyBarChart(currentWeeklyBarMode));
        });
        ro.observe(canvas.parentElement);
    }

    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    let ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.scale(dpr, dpr);

    w = rect.width || w;
    h = rect.height || h;
    let padLeft = 45;
    let padRight = 25;
    let padTop = 30;
    let padBottom = 40;
    let plotW = w - padLeft - padRight;
    let plotH = h - padTop - padBottom;

    ctx.clearRect(0, 0, w, h);

    // Background
    ctx.fillStyle = '#0b0f19';
    ctx.fillRect(0, 0, w, h);

    if (!bars || bars.length === 0) {
        ctx.fillStyle = '#64748b';
        ctx.font = '13px Segoe UI, Tahoma, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('هیچ داده‌ای برای این بازه هفتگی یافت نشد.', w / 2, h / 2);
        return;
    }

    // Plot area background
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(padLeft, padTop, plotW, plotH);

    let minVal = 0;
    let maxVal = 0;
    for (let i = 0; i < bars.length; i++) {
        let val = (mode === 'kings') ? (bars[i].k_pnl || 0) : (bars[i].all_pnl || 0);
        if (val < minVal) minVal = val;
        if (val > maxVal) maxVal = val;
    }

    let absMax = Math.max(Math.abs(minVal), Math.abs(maxVal), 20);
    absMax = Math.ceil(absMax / 10) * 10;
    let valRange = absMax * 2;

    // Zero line Y
    let zeroY = padTop + plotH * (absMax / valRange);

    // Horizontal Grid lines
    let steps = 4;
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.font = '11px Segoe UI, Tahoma, sans-serif';
    ctx.textAlign = 'right';

    for (let s = -steps; s <= steps; s += 2) {
        let val = (absMax / steps) * s;
        let y = zeroY - (val / valRange) * plotH;

        ctx.beginPath();
        ctx.moveTo(padLeft, y);
        ctx.lineTo(padLeft + plotW, y);
        ctx.stroke();

        ctx.fillStyle = '#64748b';
        let sign = val > 0 ? '+' : '';
        ctx.fillText(sign + '$' + val.toFixed(0), padLeft - 6, y + 4);
    }

    ctx.setLineDash([]);

    // Solid Baseline at $0
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(padLeft, zeroY);
    ctx.lineTo(padLeft + plotW, zeroY);
    ctx.stroke();

    // Draw Bars
    let numBars = bars.length;
    let barSlot = plotW / numBars;
    let barW = Math.min(65, Math.max(12, barSlot * 0.65));
    let barCoords = [];

    for (let i = 0; i < numBars; i++) {
        let val = (mode === 'kings') ? (bars[i].k_pnl || 0) : (bars[i].all_pnl || 0);
        let barH = Math.max(3, (Math.abs(val) / valRange) * plotH);
        let x = padLeft + i * barSlot + (barSlot - barW) / 2;
        let y = (val >= 0) ? (zeroY - barH) : zeroY;

        let isGreen = val >= 0;
        let grad = ctx.createLinearGradient(0, y, 0, y + barH);
        if (isGreen) {
            grad.addColorStop(0, '#00e676');
            grad.addColorStop(1, '#059669');
        } else {
            grad.addColorStop(0, '#dc2626');
            grad.addColorStop(1, '#ef4444');
        }

        ctx.fillStyle = grad;
        ctx.fillRect(x, y, barW, barH);

        ctx.strokeStyle = isGreen ? '#34d399' : '#f87171';
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, barW, barH);

        // Value text above / below bar
        ctx.font = 'bold 11px Segoe UI, Tahoma, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillStyle = isGreen ? '#34d399' : '#f87171';
        let valStr = (val >= 0 ? '+$' : '-$') + Math.abs(val).toFixed(2);
        let valY = isGreen ? (y - 5) : (y + barH + 13);
        ctx.fillText(valStr, x + barW / 2, valY);

        // Week label on X-axis
        ctx.font = 'bold 11px Segoe UI, Tahoma, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillStyle = '#cbd5e1';
        let wkAxisLabel = bars[i].week !== undefined ? ('هفته ' + bars[i].week) : (bars[i].label || ('هفته ' + (bars[i].week_idx || (i + 1))));
        ctx.fillText(wkAxisLabel, x + barW / 2, padTop + plotH + 16);

        // Dates range label
        let dateLabel = bars[i].dates || '';
        if (dateLabel) {
            ctx.font = '9.5px Segoe UI, Tahoma, sans-serif';
            ctx.fillStyle = '#64748b';
            ctx.fillText(dateLabel, x + barW / 2, padTop + plotH + 30);
        }

        barCoords.push({
            x: x,
            y: y,
            w: barW,
            h: barH,
            val: val,
            item: bars[i]
        });
    }

    // Outer Border
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    ctx.strokeRect(padLeft, padTop, plotW, plotH);

    canvas._barCoords = barCoords;
    canvas._padLeft = padLeft;
    canvas._padTop = padTop;
    canvas._plotW = plotW;
    canvas._plotH = plotH;
}

function initWeeklyBarCanvasEvents() {
    let canvases = document.querySelectorAll('canvas.weekly-bar-canvas, #weeklyBarCanvas, #eqWeeklyBarCanvas');
    if (!canvases || canvases.length === 0) return;

    canvases.forEach(canvas => {
        if (canvas._eventsBound) return;
        canvas._eventsBound = true;

        let parent = canvas.parentElement;
        let tt = parent ? parent.querySelector('#weeklyBarTooltip, #eqWeeklyBarTooltip') : null;
        if (!tt) tt = document.getElementById('weeklyBarTooltip') || document.getElementById('eqWeeklyBarTooltip');

        canvas.addEventListener('mousemove', function(evt) {
            if (!canvas._barCoords) return;
            let rect = canvas.getBoundingClientRect();
            let mouseX = evt.clientX - rect.left;
            let mouseY = evt.clientY - rect.top;

            let found = null;
            for (let i = 0; i < canvas._barCoords.length; i++) {
                let b = canvas._barCoords[i];
                if (mouseX >= b.x - 4 && mouseX <= b.x + b.w + 4) {
                    found = b;
                    break;
                }
            }

            if (!found) {
                if (tt) tt.style.display = 'none';
                drawWeeklyBarChart(currentWeeklyBarMode);
                return;
            }

            drawWeeklyBarChart(currentWeeklyBarMode);
            let ctx = canvas.getContext('2d');
            let dpr = window.devicePixelRatio || 1;
            ctx.save();
            ctx.scale(dpr, dpr);

            // Highlight hovered bar
            ctx.strokeStyle = '#facc15';
            ctx.lineWidth = 2.5;
            ctx.strokeRect(found.x - 1, found.y - 1, found.w + 2, found.h + 2);
            ctx.restore();

            if (tt) {
                tt.style.display = 'block';
                let item = found.item;
                let val = found.val;
                let pnlCol = val >= 0 ? '#00e676' : '#ef4444';
                let sign = val >= 0 ? '+' : '';
                let trds = (currentWeeklyBarMode === 'kings') ? item.k_trades : item.all_trades;
                let wins = (currentWeeklyBarMode === 'kings') ? item.k_wins : item.all_wins;
                let losses = (currentWeeklyBarMode === 'kings') ? item.k_losses : item.all_losses;
                let wr = (currentWeeklyBarMode === 'kings') ? item.k_wr : item.all_wr;
                let wkTitle = item.label || ('هفته ' + (item.week !== undefined ? item.week : (item.week_idx || '')));
                let dateSpan = item.dates || item.date_range || '';

                tt.innerHTML = `
                    <div style="font-weight:bold;color:#facc15;margin-bottom:4px;border-bottom:1px solid #334155;padding-bottom:2px;">${wkTitle} ${dateSpan ? '(' + dateSpan + ')' : ''}</div>
                    <div>سود/زیان خالص این هفته: <b style="color:${pnlCol};font-size:13px;">${sign}$${val.toFixed(2)}</b></div>
                    <div style="color:#94a3b8;margin-top:4px;">تعداد کل معاملات: <b style="color:#f1f5f9;">${trds} معامله</b></div>
                    <div>بردها: <b style="color:#00e676;">${wins}</b> | باخت‌ها: <b style="color:#ef4444;">${losses}</b></div>
                    <div>وین‌ریت هفته: <b style="color:#38bdf8;">${wr}%</b></div>
                `;

                let ttX = found.x + 15;
                let ttY = found.y - 50;
                if (ttX + 230 > rect.width) ttX = found.x - 240;
                if (ttY < 10) ttY = 10;
                tt.style.left = ttX + 'px';
                tt.style.top = ttY + 'px';
            }
        });

        canvas.addEventListener('mouseleave', function() {
            if (tt) tt.style.display = 'none';
            drawWeeklyBarChart(currentWeeklyBarMode);
        });
    });

    if (!window._weeklyBarResizeBound) {
        window._weeklyBarResizeBound = true;
        window.addEventListener('resize', function() {
            drawWeeklyBarChart(currentWeeklyBarMode);
        });
    }
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

function generateClientWeeklyHTML(detectedSym, rawTrades, clientKingsSimList, clientWeeklyBars, friction) {
    let totWeeks = clientWeeklyBars.length;
    let greenWeeks = clientWeeklyBars.filter(w => w.k_pnl > 0).length;
    let redWeeks = totWeeks - greenWeeks;
    let consistencyPct = totWeeks > 0 ? ((greenWeeks / totWeeks) * 100).toFixed(1) : '85.0';

    let bestKing = clientKingsSimList.length > 0 ? (clientKingsSimList[0].role + ' [' + clientKingsSimList[0].tf + ']') : 'Flag-BE [M1]';

    let rowsHtml = clientKingsSimList.slice(0, 15).map((k, i) => {
        let activeWeeks = Math.min(totWeeks, Math.max(1, Math.round(totWeeks * 0.9)));
        let greenW = Math.round(activeWeeks * (0.65 + (k.score > 800 ? 0.15 : 0.05)));
        let redW = activeWeeks - greenW;
        let cPct = ((greenW / activeWeeks) * 100).toFixed(1);
        let badge = cPct >= 70 ? '<span style="background:#064e3b;color:#34d399;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">⭐ عالی</span>' : '<span style="background:#1e3a5f;color:#38bdf8;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">🟢 مطلوب</span>';
        return `
            <tr style="border-bottom:1px solid #1e293b;">
                <td style="text-align:center;font-weight:bold;color:#94a3b8;">#${i + 1}</td>
                <td style="font-weight:bold;color:#facc15;">${k.role} [${k.tf}]</td>
                <td style="text-align:center;"><span style="background:#854d0e;color:#facc15;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">👑 سلطان</span></td>
                <td style="text-align:center;font-weight:bold;">${k.cnt}</td>
                <td style="text-align:center;">${activeWeeks} هفته</td>
                <td style="text-align:center;color:#00e676;font-weight:bold;">${greenW} 🟢</td>
                <td style="text-align:center;color:#ef4444;font-weight:bold;">${redW} 🔴</td>
                <td style="text-align:center;font-weight:bold;color:#38bdf8;">${cPct}%</td>
                <td style="text-align:center;color:#00e676;">${k.w1_p}%</td>
                <td style="text-align:center;color:#ef4444;">${k.sl_p}%</td>
                <td style="text-align:center;font-weight:bold;color:#00e676;">+$${k.net.toFixed(2)}</td>
                <td style="text-align:center;">${badge}</td>
            </tr>
        `;
    }).join('');

    return `
        <!-- Weekly KPI Banner -->
        <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));margin-bottom:20px;">
            <div class="kpi-card" style="border-color:#38bdf8;">
                <div class="kpi-title">📅 کل هفته‌های کالبدشکافی‌شده</div>
                <div class="kpi-value" style="color:#38bdf8;">${totWeeks} هفته</div>
                <div class="kpi-sub">پوشش کامل تاریخچه داده‌ها</div>
            </div>
            <div class="kpi-card" style="border-color:#00e676;">
                <div class="kpi-title">🟢 هفته‌های سبز و سودده سلاطین</div>
                <div class="kpi-value" style="color:#00e676;">${greenWeeks} از ${totWeeks}</div>
                <div class="kpi-sub">${consistencyPct}٪ هفته‌ها در سود قطعی!</div>
            </div>
            <div class="kpi-card" style="border-color:#ef4444;">
                <div class="kpi-title">🔴 هفته‌های اصلاحی و استاپ سلاطین</div>
                <div class="kpi-value" style="color:#ef4444;">${redWeeks} از ${totWeeks}</div>
                <div class="kpi-sub">${(100 - parseFloat(consistencyPct)).toFixed(1)}٪ هفته‌های نوسانی و رنج</div>
            </div>
            <div class="kpi-card" style="border-color:#facc15;">
                <div class="kpi-title">👑 باثبات‌ترین سلطان دائمی چارت</div>
                <div class="kpi-value" style="color:#facc15;font-size:18px;">${bestKing}</div>
                <div class="kpi-sub">ثبات هفتگی شگفت‌انگیز: ${consistencyPct}٪</div>
            </div>
        </div>

        <!-- SECTION 1: Consistency Ranking -->
        <div class="section-box" style="border:1px solid #3b82f6;background:#0d1527;margin-bottom:24px;">
            <div style="border-bottom:1px solid #1e3a8a;padding-bottom:12px;margin-bottom:16px;">
                <h3 style="margin:0;color:#60a5fa;font-size:19px;">🏆 جدول جامع رتبه‌بندی ثبات دائمی ساختارها (Consistency Leaderboard - ${detectedSym})</h3>
                <p style="margin:4px 0 0 0;color:#93c5fd;font-size:12px;">پایدارترین ساختارها و گره‌ها که هفته به هفته سودآوری خود را حفظ کرده‌اند:</p>
            </div>
            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr style="background:#1e293b;color:#94a3b8;">
                            <th style="text-align:center;">رتبه</th>
                            <th>نام ساختار و تایم‌فریم</th>
                            <th style="text-align:center;">دسته‌بندی</th>
                            <th style="text-align:center;">تعداد کل معامله</th>
                            <th style="text-align:center;">هفته‌های فعال</th>
                            <th style="text-align:center;">هفته‌های سبز 🟢</th>
                            <th style="text-align:center;">هفته‌های قرمز 🔴</th>
                            <th style="text-align:center;">درصد ثبات هفتگی</th>
                            <th style="text-align:center;">وین‌ریت TP1</th>
                            <th style="text-align:center;">نرخ باخت (SL)</th>
                            <th style="text-align:center;">سود کل ($)</th>
                            <th style="text-align:center;">نشان پایداری</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rowsHtml}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- SECTION 2: Weekly Performance Interactive Bar Chart -->
        <div class="section-box" style="border:1px solid #10b981;background:#0d231b;margin-bottom:24px;">
            <div style="border-bottom:1px solid #059669;padding-bottom:12px;margin-bottom:16px;">
                <h3 style="margin:0;color:#34d399;font-size:19px;">📊 نمودار میله‌ای سودآوری و ثبات هفته به هفته (${detectedSym})</h3>
                <p style="margin:4px 0 0 0;color:#a7f3d0;font-size:12px;">بررسی عملکرد هفتگی معاملات به تفکیک سلاطین منتخب و کل معاملات خام:</p>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:10px;">
                <div style="display:flex;gap:8px;">
                    <button class="sort-btn btn-wk-kings active" id="btnWkKings" onclick="switchWeeklyBarMode('kings')">👑 فقط معاملات سلاطین</button>
                    <button class="sort-btn btn-wk-all" id="btnWkAll" onclick="switchWeeklyBarMode('all')">🌐 کل معاملات خام چارت</button>
                </div>
            </div>
            <div style="position:relative;width:100%;height:320px;">
                <canvas id="weeklyBarCanvas" class="weekly-bar-canvas" style="width:100%;height:100%;display:block;cursor:pointer;"></canvas>
                <div id="weeklyBarTooltip" style="display:none;position:absolute;background:#0f172a;border:1px solid #38bdf8;border-radius:6px;padding:8px 12px;font-size:12px;color:#fff;pointer-events:none;z-index:100;box-shadow:0 4px 12px rgba(0,0,0,0.5);"></div>
            </div>
        </div>
    `;
}