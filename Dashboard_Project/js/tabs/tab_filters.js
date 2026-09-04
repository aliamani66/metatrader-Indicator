/**
 * FlagPro Dashboard - Tab 5: Strategic Filters & Time/Day Optimization
 */
const TabFilters = (function() {
    'use strict';

    function init() {
        AppStateManager.subscribe('dataUpdate', () => {
            renderFilters();
        });
    }

    function renderFilters() {
        const container = document.getElementById('filtersContainer');
        const sData = AppStateManager.getSymbolData();
        if (!container || !sData || !sData.hourly_summary) return;

        const dayNames = ['یک‌شنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه', 'شنبه'];

        // Hourly heat bars
        let hourlyHtml = '';
        sData.hourly_summary.forEach(hItem => {
            const wr = hItem.count > 0 ? (hItem.wins / hItem.count * 100).toFixed(0) : 0;
            const netCol = hItem.net >= 0 ? '#10b981' : '#ef4444';
            hourlyHtml += `
                <div style="background:#0f172a;border:1px solid #1e293b;border-radius:6px;padding:8px 6px;text-align:center;">
                    <div style="font-size:11px;color:#94a3b8;font-weight:bold;">${hItem.hour}:00</div>
                    <div style="font-size:12px;font-weight:bold;color:${netCol};margin:2px 0;">${hItem.net >= 0 ? '+' : ''}$${Math.round(hItem.net)}</div>
                    <div style="font-size:10px;color:#cbd5e1;">${hItem.count} ترید</div>
                    <div style="font-size:10px;color:#38bdf8;">WR ${wr}٪</div>
                </div>
            `;
        });

        // Daily summary
        let dailyHtml = '';
        sData.daily_summary.forEach(dItem => {
            if (dItem.count === 0 && (dItem.day === 0 || dItem.day === 6)) return; // Skip empty weekends
            const wr = dItem.count > 0 ? (dItem.wins / dItem.count * 100).toFixed(1) : 0;
            const netCol = dItem.net >= 0 ? '#10b981' : '#ef4444';
            dailyHtml += `
                <tr>
                    <td style="font-weight:bold;">${dayNames[dItem.day]}</td>
                    <td class="text-center" style="font-weight:bold;">${dItem.count.toLocaleString()}</td>
                    <td class="text-center" style="color:#34d399;font-weight:bold;">${dItem.wins.toLocaleString()}</td>
                    <td class="text-center" style="color:#ef4444;font-weight:bold;">${(dItem.count - dItem.wins).toLocaleString()}</td>
                    <td class="text-center" style="color:#38bdf8;font-weight:bold;">${wr}٪</td>
                    <td class="text-center" style="color:${netCol};font-weight:bold;">${dItem.net >= 0 ? '+' : ''}$${Math.round(dItem.net).toLocaleString()}</td>
                </tr>
            `;
        });

        const html = `
            <div class="section-box">
                <div class="section-title">⏰ عملکرد ۲۴ ساعته نماد (سودآوری و وین‌ریت بر حسب ساعت سرور):</div>
                <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(85px, 1fr));gap:8px;margin-top:14px;">
                    ${hourlyHtml}
                </div>
            </div>

            <div class="section-box">
                <div class="section-title">📅 بازدهی تفکیکی روزهای هفته:</div>
                <div class="table-responsive" style="margin-top:14px;">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>روز هفته</th>
                                <th class="text-center">تعداد معاملات</th>
                                <th class="text-center">معاملات برنده</th>
                                <th class="text-center">معاملات بازنده</th>
                                <th class="text-center">وین‌ریت (Win Rate)</th>
                                <th class="text-center">سود خالص کل</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${dailyHtml}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    window.renderTab_filters = function(sData) {
        renderFilters();
    };

    return {
        init: init,
        renderFilters: renderFilters
    };
})();
