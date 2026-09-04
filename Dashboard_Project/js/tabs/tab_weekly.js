/**
 * FlagPro Dashboard - Tab 7: Weekly Consistency & Bar Chart
 */
const TabWeekly = (function() {
    'use strict';

    let canvas = null, ctx = null;
    let currentMode = 'kings';

    function init() {
        canvas = document.getElementById('weeklyCanvas');
        if (canvas) {
            ctx = canvas.getContext('2d');
            window.addEventListener('resize', drawChart);
        }

        const btnK = document.getElementById('btnWkKings');
        const btnA = document.getElementById('btnWkAll');
        if (btnK) {
            btnK.addEventListener('click', () => {
                currentMode = 'kings';
                btnK.classList.add('active');
                if (btnA) btnA.classList.remove('active');
                drawChart();
            });
        }
        if (btnA) {
            btnA.addEventListener('click', () => {
                currentMode = 'all';
                btnA.classList.add('active');
                if (btnK) btnK.classList.remove('active');
                drawChart();
            });
        }

        AppStateManager.subscribe('dataUpdate', () => {
            renderTable();
            drawChart();
        });
    }

    function renderTable() {
        const tbody = document.getElementById('weeklyTableTbody');
        const sData = AppStateManager.getSymbolData();
        if (!tbody || !sData || !sData.weekly_bar_data) return;

        const weeks = sData.weekly_bar_data;
        let greenCount = 0;
        let html = '';

        weeks.forEach((w, idx) => {
            const pnl = currentMode === 'kings' ? w.k_pnl : w.all_pnl;
            const wr = currentMode === 'kings' ? w.k_wr : w.all_wr;
            const trades = currentMode === 'kings' ? w.k_trades : w.all_trades;
            const isGreen = pnl >= 0;
            if (isGreen) greenCount++;

            const statusBadge = isGreen
                ? '<span class="badge badge-green">سودده ✅</span>'
                : '<span class="badge badge-red">منفی 🛑</span>';

            html += `
                <tr>
                    <td class="text-center" style="font-weight:bold;color:#facc15;">#${idx + 1}</td>
                    <td class="text-center" style="font-family:Consolas, monospace;">${w.date_range}</td>
                    <td class="text-center" style="font-weight:bold;">${trades}</td>
                    <td class="text-center" style="font-weight:bold;color:#38bdf8;">${wr}٪</td>
                    <td class="text-center" style="font-weight:bold;color:${isGreen ? '#00e676' : '#ef4444'};">
                        ${pnl >= 0 ? '+' : ''}$${pnl.toLocaleString()}
                    </td>
                    <td class="text-center">${statusBadge}</td>
                </tr>
            `;
        });

        tbody.innerHTML = html;

        // Update green ratio badge if present
        const badge = document.getElementById('weeklyGreenRatioBadge');
        if (badge && weeks.length > 0) {
            const ratio = ((greenCount / weeks.length) * 100).toFixed(0);
            badge.textContent = `${greenCount} هفته مثبت از ${weeks.length} هفته (${ratio}٪)`;
        }
    }

    function drawChart() {
        if (!canvas || !ctx) return;
        const sData = AppStateManager.getSymbolData();
        if (!sData || !sData.weekly_bar_data) return;

        const weeks = sData.weekly_bar_data;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = 240;

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        if (weeks.length === 0) return;

        const pnlList = weeks.map(w => currentMode === 'kings' ? w.k_pnl : w.all_pnl);
        const maxVal = Math.max(...pnlList.map(v => Math.abs(v)), 100);

        const padX = 40;
        const padY = 20;
        const chartW = canvas.width - padX - 20;
        const chartH = canvas.height - padY * 2;
        const zeroY = padY + chartH / 2;

        // Zero line
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padX, zeroY);
        ctx.lineTo(canvas.width - 20, zeroY);
        ctx.stroke();

        const barW = Math.max(4, Math.min(24, (chartW / weeks.length) - 4));
        const step = chartW / weeks.length;

        pnlList.forEach((val, idx) => {
            const x = padX + idx * step + (step - barW) / 2;
            const barH = (Math.abs(val) / maxVal) * (chartH / 2 - 10);
            const isPos = val >= 0;
            const y = isPos ? (zeroY - barH) : zeroY;

            ctx.fillStyle = isPos ? '#10b981' : '#ef4444';
            ctx.fillRect(x, y, barW, Math.max(2, barH));
        });
    }

    window.renderTab_weekly = function(sData) {
        renderTable();
        drawChart();
    };

    return {
        init: init,
        renderTable: renderTable,
        drawChart: drawChart
    };
})();
