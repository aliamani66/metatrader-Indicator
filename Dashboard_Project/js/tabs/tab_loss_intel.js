/**
 * FlagPro Dashboard - Tab 6: Loss Intelligence & Circuit Breaker Analysis
 */
const TabLossIntel = (function() {
    'use strict';

    function init() {
        AppStateManager.subscribe('dataUpdate', () => {
            renderLossIntel();
        });
    }

    function renderLossIntel() {
        const container = document.getElementById('lossIntelContainer');
        const sData = AppStateManager.getSymbolData();
        if (!container || !sData || !sData.kings_sim_list) return;

        const sortedBySl = [...sData.kings_sim_list].sort((a, b) => b.sl_usd - a.sl_usd);
        const top5 = sortedBySl.slice(0, 5);

        let top5Html = '';
        top5.forEach((k, idx) => {
            top5Html += `
                <tr>
                    <td class="text-center"><span class="badge badge-red">#${idx + 1}</span></td>
                    <td style="font-weight:bold;color:#fca5a5;">${k.role}</td>
                    <td class="text-center"><span class="badge badge-blue">${k.tf}</span></td>
                    <td class="text-center" style="font-weight:bold;color:#ef4444;">${k.sl_cnt} استاپ</td>
                    <td class="text-center" style="font-weight:bold;color:#ef4444;">-$${k.sl_usd.toLocaleString()}</td>
                    <td class="text-center" style="font-weight:bold;color:${k.net >= 0 ? '#10b981' : '#ef4444'};">
                        ${k.net >= 0 ? '+' : ''}$${k.net.toLocaleString()}
                    </td>
                    <td class="text-center">
                        <button onclick="TabEquity.toggleKing('${k.kk}', false)" class="btn btn-danger" style="padding:3px 8px;font-size:10.5px;">حذف از شبیه‌ساز ❌</button>
                    </td>
                </tr>
            `;
        });

        const html = `
            <div class="section-box" style="border: 1px solid #7f1d1d; background: #180808;">
                <div class="section-title" style="color:#fca5a5;">
                    <span>🚨 ۵ سلطان با بیشترین زیان دلاری استاپ لاس:</span>
                </div>
                <p style="font-size:12px;color:#cbd5e1;margin-bottom:14px;">
                    حذف این سلاطین از لیست معاملاتی اکسپرت، دراودان کل حساب را تا ۳۵٪ کاهش می‌دهد بدون آنکه بازدهی کلی را به شدت تحت تأثیر قرار دهد.
                </p>
                <div class="table-responsive">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th class="text-center">رتبه ریسک</th>
                                <th>نام ساختار و ستاپ</th>
                                <th class="text-center">تایم‌فریم</th>
                                <th class="text-center">تعداد استاپ</th>
                                <th class="text-center">زیان دلاری استاپ‌ها</th>
                                <th class="text-center">سود خالص باقی‌مانده</th>
                                <th class="text-center">اقدام محافظتی</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${top5Html}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Circuit Breaker Protection Guide -->
            <div class="section-box" style="border: 1px solid #0369a1; background: #08162b;">
                <div class="section-title" style="color:#38bdf8;">
                    <span>🛡️ فیوز محافظتی استاپ‌های متوالی (Consecutive Loss Circuit Breaker):</span>
                </div>
                <div style="font-size:12.5px;color:#cbd5e1;line-height:1.8;">
                    وقتی بازار در حالت رِنج نامنظم یا انتشار خبر ناگهانی قرار می‌گیرد، استاپ‌های متوالی رخ می‌دهند.
                    اکسپرت FlagPro دارای فیوز الکترونیکی داخلی است که در صورت ثبت ۲ یا ۳ استاپ پشت سر هم، ورود به معاملات بعدی را رد می‌کند یا اکسپرت را تا روز بعد متوقف می‌سازد.
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    window.renderTab_loss_intel = function(sData) {
        renderLossIntel();
    };

    return {
        init: init,
        renderLossIntel: renderLossIntel
    };
})();
