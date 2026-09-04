/**
 * FlagPro Dashboard - Tab 1: Equity Curve & Strategy Simulator
 */
const TabEquity = (function() {
    'use strict';

    let canvas = null, ctx = null;

    function init() {
        canvas = document.getElementById('equityCanvas');
        if (canvas) {
            ctx = canvas.getContext('2d');
            window.addEventListener('resize', drawEquityChart);
        }

        // Mode buttons
        const btnKings = document.getElementById('btnEqKings');
        const btnAll = document.getElementById('btnEqAll');
        if (btnKings) {
            btnKings.addEventListener('click', () => {
                AppStateManager.updateSimState({ mode: 'kings' });
                btnKings.classList.add('active');
                if (btnAll) btnAll.classList.remove('active');
                simulateAndDraw();
            });
        }
        if (btnAll) {
            btnAll.addEventListener('click', () => {
                AppStateManager.updateSimState({ mode: 'all' });
                btnAll.classList.add('active');
                if (btnKings) btnKings.classList.remove('active');
                simulateAndDraw();
            });
        }

        // Min profit slider
        const slider = document.getElementById('simProfitSlider');
        if (slider) {
            slider.addEventListener('input', function() {
                const val = parseFloat(this.value);
                AppStateManager.updateSimState({ minProfit: val });
                const sliderVal = document.getElementById('simProfitSliderVal');
                if (sliderVal) sliderVal.textContent = '$' + val.toFixed(2);
                simulateAndDraw();
            });
        }

        // Subscribe to data updates
        AppStateManager.subscribe('dataUpdate', () => {
            renderSimKingsGrid();
            renderSimHoursBar();
            simulateAndDraw();
        });
    }

    function renderSimKingsGrid() {
        const grid = document.getElementById('simKingsGrid');
        const sData = AppStateManager.getSymbolData();
        if (!grid || !sData || !sData.kings_sim_list) return;

        const simState = AppStateManager.getSimState();
        let html = '';
        sData.kings_sim_list.forEach(k => {
            const isChecked = simState.enabledKings.has(k.kk) ? 'checked' : '';
            const dangerTag = (k.sl_cnt >= 30 || (sData.top3_sl_cnt_keys && sData.top3_sl_cnt_keys.includes(k.kk))) ? '🔴' : '👑';
            html += `
                <label style="display:inline-flex;align-items:center;gap:4px;background:#1e293b;padding:3px 8px;border-radius:4px;font-size:11px;cursor:pointer;color:#e2e8f0;">
                    <input type="checkbox" data-kk="${k.kk}" ${isChecked} onchange="TabEquity.toggleKing(this.dataset.kk, this.checked)" />
                    <span>${dangerTag} ${k.role} (${k.tf})</span>
                </label>
            `;
        });
        grid.innerHTML = html;
    }

    function toggleKing(kk, enabled) {
        const simState = AppStateManager.getSimState();
        if (enabled) simState.enabledKings.add(kk);
        else simState.enabledKings.delete(kk);
        simulateAndDraw();
    }

    function renderSimHoursBar() {
        const bar = document.getElementById('simHoursBar');
        if (!bar) return;
        const simState = AppStateManager.getSimState();
        let html = '';
        for (let h = 0; h < 24; h++) {
            const isAct = simState.allowedHours[h] ? 'background:#0284c7;color:#fff;' : 'background:#1e293b;color:#64748b;';
            html += `<button type="button" onclick="TabEquity.toggleHour(${h})" style="${isAct}border:none;padding:3px 6px;border-radius:3px;font-size:10.5px;cursor:pointer;font-weight:bold;">${h}</button>`;
        }
        bar.innerHTML = html;
    }

    function toggleHour(h) {
        const simState = AppStateManager.getSimState();
        simState.allowedHours[h] = !simState.allowedHours[h];
        renderSimHoursBar();
        simulateAndDraw();
    }

    function simulateAndDraw() {
        const sData = AppStateManager.getSymbolData();
        if (!sData || !sData.trades_sim_list) return;

        const simState = AppStateManager.getSimState();
        const trades = sData.trades_sim_list;

        let curBal = sData.bal_initial || 10000;
        let peakBal = curBal;
        let maxDD = 0;
        let wins = 0, losses = 0, totalPnl = 0;
        let grossWin = 0, grossLoss = 0;

        const pts = [{ i: 0, b: curBal, t: sData.min_date || '' }];
        let consecLosses = 0;
        let skipRemaining = 0;
        let pausedDate = '';

        trades.forEach(t => {
            if (simState.mode === 'kings' && (!t.k || !simState.enabledKings.has(t.kk))) return;
            if (t.pot < simState.minProfit) return;
            if (!simState.allowedHours[t.h]) return;

            const tDate = t.t ? t.t.substring(0, 10) : '';
            if (simState.consecLossSkipDay && pausedDate === tDate) return;

            if (skipRemaining > 0) {
                skipRemaining--;
                return;
            }

            curBal += t.p;
            totalPnl += t.p;
            if (t.p > 0) {
                wins++;
                grossWin += t.p;
                consecLosses = 0;
            } else {
                losses++;
                grossLoss += Math.abs(t.p);
                consecLosses++;
                if (simState.consecLossTrigger > 0 && consecLosses >= simState.consecLossTrigger) {
                    if (simState.consecLossSkipDay) pausedDate = tDate;
                    else skipRemaining = simState.consecLossSkipCount || 1;
                    consecLosses = 0;
                }
            }

            if (curBal > peakBal) peakBal = curBal;
            const dd = peakBal - curBal;
            if (dd > maxDD) maxDD = dd;

            pts.push({ i: pts.length, b: curBal, t: t.t });
        });

        // Update KPIs in DOM
        const total = wins + losses;
        const wr = total > 0 ? (wins / total * 100) : 0;
        const pf = grossLoss > 0 ? (grossWin / grossLoss) : (grossWin > 0 ? 999 : 0);
        const avgTrade = total > 0 ? (totalPnl / total) : 0;

        const elNet = document.getElementById('eqKpiNetVal');
        const elWr = document.getElementById('eqKpiWR');
        const elPf = document.getElementById('eqKpiPF');
        const elDd = document.getElementById('eqKpiMaxDD');
        const elCnt = document.getElementById('eqKpiCnt');
        const elAvg = document.getElementById('eqKpiAvgTrade');

        if (elNet) {
            elNet.textContent = (totalPnl >= 0 ? '+$' : '-$') + Math.abs(Math.round(totalPnl)).toLocaleString();
            elNet.style.color = totalPnl >= 0 ? '#00e676' : '#ef4444';
        }
        if (elWr) elWr.textContent = wr.toFixed(1) + '٪';
        if (elPf) elPf.textContent = pf < 900 ? pf.toFixed(2) : '∞';
        if (elDd) elDd.textContent = '$' + Math.round(maxDD).toLocaleString();
        if (elCnt) elCnt.textContent = total.toLocaleString();
        if (elAvg) elAvg.textContent = (avgTrade >= 0 ? '+$' : '-$') + Math.abs(avgTrade).toFixed(2);

        drawEquityChart(pts);
    }

    function drawEquityChart(pts) {
        if (!canvas || !ctx) return;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = 360;

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        if (!pts || pts.length < 2) {
            ctx.fillStyle = '#94a3b8';
            ctx.font = '13px Tahoma';
            ctx.textAlign = 'center';
            ctx.fillText('هیچ معامله‌ای با فیلترهای جاری مطابقت ندارد.', canvas.width / 2, canvas.height / 2);
            return;
        }

        let minB = pts[0].b, maxB = pts[0].b;
        pts.forEach(p => {
            if (p.b < minB) minB = p.b;
            if (p.b > maxB) maxB = p.b;
        });

        const padY = Math.max(50, (maxB - minB) * 0.08);
        minB -= padY; maxB += padY;
        const rangeB = maxB - minB || 1;

        const padX = 40;
        const w = canvas.width - padX - 10;
        const h = canvas.height - 40;

        // Grid lines
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = 20 + (h / 4) * i;
            ctx.beginPath();
            ctx.moveTo(padX, y);
            ctx.lineTo(canvas.width - 10, y);
            ctx.stroke();

            const val = maxB - (rangeB / 4) * i;
            ctx.fillStyle = '#64748b';
            ctx.font = '10px Consolas, monospace';
            ctx.textAlign = 'right';
            ctx.fillText('$' + Math.round(val), padX - 6, y + 3);
        }

        // Draw Line
        ctx.beginPath();
        pts.forEach((p, idx) => {
            const x = padX + (idx / (pts.length - 1)) * w;
            const y = 20 + ((maxB - p.b) / rangeB) * h;
            if (idx === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });

        const isProfitable = pts[pts.length - 1].b >= pts[0].b;
        ctx.strokeStyle = isProfitable ? '#00e676' : '#ef4444';
        ctx.lineWidth = 2.2;
        ctx.stroke();

        // Area Gradient
        ctx.lineTo(padX + w, 20 + h);
        ctx.lineTo(padX, 20 + h);
        ctx.closePath();
        const grad = ctx.createLinearGradient(0, 20, 0, 20 + h);
        grad.addColorStop(0, isProfitable ? 'rgba(0, 230, 118, 0.25)' : 'rgba(239, 68, 68, 0.25)');
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = grad;
        ctx.fill();
    }

    window.renderTab_equity = function(sData) {
        renderSimKingsGrid();
        renderSimHoursBar();
        simulateAndDraw();
    };

    return {
        init: init,
        simulateAndDraw: simulateAndDraw,
        toggleKing: toggleKing,
        toggleHour: toggleHour
    };
})();
