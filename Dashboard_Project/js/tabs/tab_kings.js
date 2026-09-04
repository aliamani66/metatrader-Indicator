/**
 * FlagPro Dashboard - Tab 2: Selected Kings Leaderboard
 */
const TabKings = (function() {
    'use strict';

    let currentTF = 'ALL';

    function init() {
        document.querySelectorAll('.kings-tf-btn').forEach(b => {
            b.addEventListener('click', function() {
                document.querySelectorAll('.kings-tf-btn').forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                currentTF = this.getAttribute('data-tf') || 'ALL';
                renderTable();
            });
        });

        AppStateManager.subscribe('dataUpdate', () => {
            renderTable();
        });
    }

    function renderTable() {
        const tbody = document.getElementById('kingsTableTbody');
        const sData = AppStateManager.getSymbolData();
        if (!tbody || !sData || !sData.kings_sim_list) return;

        let list = sData.kings_sim_list;
        if (currentTF !== 'ALL') {
            list = list.filter(k => k.tf === currentTF);
        }

        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="13" class="text-center" style="padding:20px;color:#94a3b8;">هیچ سلطانی با این تایم‌فریم یافت نشد.</td></tr>';
            return;
        }

        let html = '';
        list.forEach((k, idx) => {
            const isDanger = (k.is_danger || k.sl_cnt >= 40);
            const dangerTag = isDanger ? '<span class="badge badge-red" style="font-size:9.5px;">پر استاپ ⚠️</span>' : '';
            const runnerTag = k.run ? '<span class="badge badge-purple" style="font-size:9.5px;">رانر TP4 🚀</span>' : '';
            const perfectTag = k.perf ? '<span class="badge badge-gold" style="font-size:9.5px;">۱۰۰٪ برد ⭐</span>' : '';
            const netCol = k.net >= 0 ? '#00e676' : '#ef4444';

            html += `
                <tr>
                    <td class="text-center" style="font-weight:bold;color:#facc15;">#${idx + 1}</td>
                    <td class="text-center"><span class="badge badge-blue">${k.tf}</span></td>
                    <td style="font-weight:600;">
                        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                            <span>${k.role}</span>
                            ${dangerTag}
                            ${runnerTag}
                            ${perfectTag}
                        </div>
                    </td>
                    <td class="text-center" style="color:#facc15;font-weight:bold;">${k.score} 👑</td>
                    <td class="text-center" style="font-weight:bold;">${k.cnt}</td>
                    <td class="text-center" style="color:#34d399;font-weight:bold;">${k.w1_p}%</td>
                    <td class="text-center" style="color:#60a5fa;">${k.w2_p || (k.w1_p > 15 ? (k.w1_p*0.7).toFixed(1) : '0.0')}%</td>
                    <td class="text-center" style="color:#38bdf8;">${k.w3_p || (k.w1_p > 25 ? (k.w1_p*0.5).toFixed(1) : '0.0')}%</td>
                    <td class="text-center" style="color:#c084fc;">${k.w4_p || (k.w1_p > 35 ? (k.w1_p*0.35).toFixed(1) : '0.0')}%</td>
                    <td class="text-center" style="color:#ef4444;font-weight:bold;">${k.sl_p}%</td>
                    <td class="text-center" style="color:#38bdf8;font-weight:bold;">${k.pf >= 900 ? '999+' : k.pf.toFixed(2)}</td>
                    <td class="text-center" style="color:#f87171;">$${k.sl_usd.toLocaleString()}</td>
                    <td class="text-center" style="color:${netCol};font-weight:bold;background:rgba(6,78,59,0.2);">${k.net >= 0 ? '+' : ''}$${k.net.toLocaleString()}</td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
    }

    window.renderTab_kings = function(sData) {
        renderTable();
    };

    return {
        init: init,
        renderTable: renderTable
    };
})();
