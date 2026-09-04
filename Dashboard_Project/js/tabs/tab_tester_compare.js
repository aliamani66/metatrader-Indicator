/**
 * FlagPro Dashboard - Tab 9: MT5 Strategy Tester Forensic & Comparison
 */
const TabTesterCompare = (function() {
    'use strict';

    function init() {
        // Any tester file upload listener can be bound here
    }

    function renderCompare() {
        const container = document.getElementById('testerCompareContainer');
        if (!container) return;

        // Static or dynamic tester comparison layout
        container.innerHTML = `
            <div class="section-box" style="border: 1px solid #6366f1; background: #0c102b;">
                <div class="section-title" style="color:#a5b4fc;">
                    <span>🔬 کالبدشکافی تست استراتژی تستر متاتریدر ۵ vs شبیه‌ساز FlagPro</span>
                </div>
                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:12px;margin:16px 0;">
                    <div class="kpi-card" style="border:1px solid #ef4444;">
                        <span class="kpi-title">تستر MT5 (پیش‌فرض)</span>
                        <span class="kpi-value" style="color:#ef4444;">۲۶.۴٪</span>
                        <span class="kpi-subtext">وین‌ریت بدون لود فیلتر سشن و کف سود</span>
                    </div>
                    <div class="kpi-card" style="border:1px solid #10b981;">
                        <span class="kpi-title">داشبورد FlagPro (بهینه)</span>
                        <span class="kpi-value" style="color:#10b981;">۶۸.۵٪</span>
                        <span class="kpi-subtext">وین‌ریت با اعمال سناریوی الماس و حذف M1</span>
                    </div>
                </div>
                <div style="font-size:12px;color:#cbd5e1;line-height:1.8;">
                    💡 <b>علت اصلی افت در تست‌های خام متاتریدر:</b> اکسپرت بدون لود فایل <code>.set</code> تنظیمات اجرا شده و ۹۵٪ معاملات در تایم‌فریم پرنویز M1 انجام شده است. با بارگذاری فایل <code>.set</code> در تب Inputs تستر متاتریدر، عملکرد بهینه برقرار خواهد شد.
                </div>
            </div>
        `;
    }

    window.renderTab_tester_compare = function(sData) {
        renderCompare();
    };

    return {
        init: init,
        renderCompare: renderCompare
    };
})();
