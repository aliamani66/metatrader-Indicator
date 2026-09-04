/**
 * FlagPro Dashboard - Tab 3: Scale-out Targets Breakdown (TP1..4)
 */
const TabScaleout = (function() {
    'use strict';

    function init() {
        AppStateManager.subscribe('dataUpdate', () => {
            renderScaleout();
        });
    }

    function renderScaleout() {
        const container = document.getElementById('scaleoutContainer');
        const sData = AppStateManager.getSymbolData();
        if (!container || !sData || !sData.scaleout_summary) return;

        const so = sData.scaleout_summary;
        const total = so.total || 1;

        const pTp1 = (so.tp1Count / total * 100).toFixed(1);
        const pTp2 = (so.tp2Count / total * 100).toFixed(1);
        const pTp3 = (so.tp3Count / total * 100).toFixed(1);
        const pTp4 = (so.tp4Count / total * 100).toFixed(1);
        const pSl = (so.slCount / total * 100).toFixed(1);

        let html = `
            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:14px;margin-bottom:20px;">
                <div class="kpi-card" style="border-top:3px solid #10b981;">
                    <span class="kpi-title">🎯 تارگت اول TP 1:1</span>
                    <span class="kpi-value" style="color:#34d399;">${pTp1}٪</span>
                    <span class="kpi-subtext">${so.tp1Count.toLocaleString()} معامله با لمس حداقل ۱R</span>
                </div>
                <div class="kpi-card" style="border-top:3px solid #0284c7;">
                    <span class="kpi-title">🎯 تارگت دوم TP 1:2</span>
                    <span class="kpi-value" style="color:#38bdf8;">${pTp2}٪</span>
                    <span class="kpi-subtext">${so.tp2Count.toLocaleString()} معامله با لمس حداقل ۲R</span>
                </div>
                <div class="kpi-card" style="border-top:3px solid #6366f1;">
                    <span class="kpi-title">🎯 تارگت سوم TP 1:3</span>
                    <span class="kpi-value" style="color:#818cf8;">${pTp3}٪</span>
                    <span class="kpi-subtext">${so.tp3Count.toLocaleString()} معامله با لمس حداقل ۳R</span>
                </div>
                <div class="kpi-card" style="border-top:3px solid #a855f7;">
                    <span class="kpi-title">🚀 رانر نهایی TP 1:4</span>
                    <span class="kpi-value" style="color:#c084fc;">${pTp4}٪</span>
                    <span class="kpi-subtext">${so.tp4Count.toLocaleString()} معامله رانر کامل</span>
                </div>
                <div class="kpi-card" style="border-top:3px solid #ef4444;">
                    <span class="kpi-title">🛑 حد ضرر کامل (Full SL)</span>
                    <span class="kpi-value" style="color:#f87171;">${pSl}٪</span>
                    <span class="kpi-subtext">${so.slCount.toLocaleString()} معامله با استاپ کامل</span>
                </div>
            </div>

            <!-- Visual Progress Funnel -->
            <div class="section-box">
                <div class="section-title">📊 قیف پیشروی پوزیشن‌ها تا تارگت نهایی:</div>
                <div style="margin-top:14px;display:flex;flex-direction:column;gap:12px;">
                    <div>
                        <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
                            <span>تارگت اول (TP1 - خروج ۲۵٪ حجم اولیه و بریک‌ایون):</span>
                            <b>${so.tp1Count} ترید (${pTp1}٪)</b>
                        </div>
                        <div style="height:10px;background:#1e293b;border-radius:5px;overflow:hidden;">
                            <div style="width:${pTp1}%;height:100%;background:#10b981;"></div>
                        </div>
                    </div>
                    <div>
                        <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
                            <span>تارگت دوم (TP2 - خروج ۲۵٪ حجم دوم):</span>
                            <b>${so.tp2Count} ترید (${pTp2}٪)</b>
                        </div>
                        <div style="height:10px;background:#1e293b;border-radius:5px;overflow:hidden;">
                            <div style="width:${pTp2}%;height:100%;background:#0284c7;"></div>
                        </div>
                    </div>
                    <div>
                        <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
                            <span>تارگت سوم (TP3 - تریلینگ استاپ فعال):</span>
                            <b>${so.tp3Count} ترید (${pTp3}٪)</b>
                        </div>
                        <div style="height:10px;background:#1e293b;border-radius:5px;overflow:hidden;">
                            <div style="width:${pTp3}%;height:100%;background:#6366f1;"></div>
                        </div>
                    </div>
                    <div>
                        <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
                            <span>رانر نهایی (TP4 - شکار روندهای بزرگ):</span>
                            <b>${so.tp4Count} ترید (${pTp4}٪)</b>
                        </div>
                        <div style="height:10px;background:#1e293b;border-radius:5px;overflow:hidden;">
                            <div style="width:${pTp4}%;height:100%;background:#a855f7;"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    window.renderTab_scaleout = function(sData) {
        renderScaleout();
    };

    return {
        init: init,
        renderScaleout: renderScaleout
    };
})();
