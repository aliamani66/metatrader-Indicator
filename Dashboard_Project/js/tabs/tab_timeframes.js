/**
 * FlagPro Dashboard - Tab 4: Timeframes Comparative Matrix
 */
const TabTimeframes = (function() {
    'use strict';

    function init() {
        AppStateManager.subscribe('dataUpdate', () => {
            renderTimeframes();
        });
    }

    function renderTimeframes() {
        const container = document.getElementById('timeframesContainer');
        const sData = AppStateManager.getSymbolData();
        if (!container || !sData || !sData.timeframe_summary) return;

        const tfList = sData.timeframe_summary;

        let cardsHtml = '';
        let rowsHtml = '';

        tfList.forEach(tfItem => {
            const total = tfItem.trades || 1;
            const wr = (tfItem.wins / total * 100).toFixed(1);
            const pf = tfItem.grossLoss > 0 ? (tfItem.grossWin / tfItem.grossLoss).toFixed(2) : '999';
            const avg = (tfItem.net / total).toFixed(2);
            const netCol = tfItem.net >= 0 ? '#00e676' : '#ef4444';

            let recTag = '<span class="badge badge-blue">معمولی</span>';
            if (tfItem.tf === 'M5' || tfItem.tf === 'M15') {
                recTag = '<span class="badge badge-green">ثبات عالی ⭐</span>';
            } else if (tfItem.tf === 'M1') {
                recTag = '<span class="badge badge-red">نویز بالا ⚠️</span>';
            }

            cardsHtml += `
                <div class="kpi-card" style="border: 1px solid #1e3a5f;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span class="badge badge-blue" style="font-size:12px;padding:3px 8px;">تایم‌فریم ${tfItem.tf}</span>
                        ${recTag}
                    </div>
                    <div style="font-size:20px;font-weight:bold;color:${netCol};margin-top:6px;">
                        ${tfItem.net >= 0 ? '+' : ''}$${Math.round(tfItem.net).toLocaleString()}
                    </div>
                    <div style="font-size:11.5px;color:#94a3b8;display:flex;justify-content:space-between;margin-top:4px;">
                        <span>تعداد: <b>${tfItem.trades}</b></span>
                        <span>وین‌ریت: <b style="color:#34d399;">${wr}٪</b></span>
                        <span>PF: <b style="color:#38bdf8;">${pf}</b></span>
                    </div>
                </div>
            `;

            rowsHtml += `
                <tr>
                    <td class="text-center"><span class="badge badge-blue">${tfItem.tf}</span></td>
                    <td class="text-center" style="font-weight:bold;">${tfItem.trades.toLocaleString()}</td>
                    <td class="text-center" style="color:#34d399;font-weight:bold;">${tfItem.wins.toLocaleString()}</td>
                    <td class="text-center" style="color:#ef4444;font-weight:bold;">${tfItem.losses.toLocaleString()}</td>
                    <td class="text-center" style="font-weight:bold;color:#38bdf8;">${wr}٪</td>
                    <td class="text-center" style="color:#facc15;font-weight:bold;">${pf}</td>
                    <td class="text-center">${avg >= 0 ? '+' : ''}$${avg}</td>
                    <td class="text-center" style="color:${netCol};font-weight:bold;background:rgba(6,78,59,0.2);">${tfItem.net >= 0 ? '+' : ''}$${Math.round(tfItem.net).toLocaleString()}</td>
                    <td class="text-center">${recTag}</td>
                </tr>
            `;
        });

        const html = `
            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:14px;margin-bottom:20px;">
                ${cardsHtml}
            </div>
            <div class="section-box">
                <div class="section-title">📊 جدول مقایسه جامع شاخص‌های آماری هر تایم‌فریم:</div>
                <div class="table-responsive" style="margin-top:14px;">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th class="text-center">تایم‌فریم</th>
                                <th class="text-center">تعداد کل</th>
                                <th class="text-center">معاملات برنده</th>
                                <th class="text-center">معاملات بازنده</th>
                                <th class="text-center">وین‌ریت (Win Rate)</th>
                                <th class="text-center">پرافیت فاکتور</th>
                                <th class="text-center">میانگین سود ترید</th>
                                <th class="text-center">سود خالص کل</th>
                                <th class="text-center">کیفیت معاملاتی</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rowsHtml}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    window.renderTab_timeframes = function(sData) {
        renderTimeframes();
    };

    return {
        init: init,
        renderTimeframes: renderTimeframes
    };
})();
