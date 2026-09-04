/**
 * FlagPro Dashboard - Tab 11: Comprehensive Trades Journal & Pagination
 */
const TabJournal = (function() {
    'use strict';

    let currentPage = 1;
    const pageSize = 50;
    let currentFilter = 'ALL';

    function init() {
        AppStateManager.subscribe('dataUpdate', () => {
            currentPage = 1;
            renderJournal();
        });
    }

    function renderJournal() {
        const tbody = document.getElementById('journalTableTbody');
        const sData = AppStateManager.getSymbolData();
        if (!tbody || !sData || !sData.trades_json_list) return;

        let list = sData.trades_json_list;
        if (currentFilter === 'KINGS') list = list.filter(t => t.is_k === 1);
        else if (currentFilter === 'WIN') list = list.filter(t => t.net > 0);
        else if (currentFilter === 'LOSS') list = list.filter(t => t.net <= 0);

        const totalItems = list.length;
        const totalPages = Math.ceil(totalItems / pageSize) || 1;
        if (currentPage > totalPages) currentPage = totalPages;

        const startIdx = (currentPage - 1) * pageSize;
        const pageItems = list.slice(startIdx, startIdx + pageSize);

        let html = '';
        pageItems.forEach(t => {
            const isWin = t.net > 0;
            const dirBadge = t.dir === 'BUY'
                ? '<span class="badge badge-green">BUY</span>'
                : '<span class="badge badge-red">SELL</span>';

            html += `
                <tr>
                    <td class="text-center" style="color:#facc15;font-weight:bold;">#${t.id}</td>
                    <td class="text-center" style="font-family:Consolas, monospace;font-size:11px;">${t.en_t}</td>
                    <td class="text-center"><span class="badge badge-blue">${t.tf}</span></td>
                    <td class="text-center">${dirBadge}</td>
                    <td style="font-weight:600;">${t.role}</td>
                    <td class="text-center">${t.pts}</td>
                    <td class="text-center">$${t.pot.toFixed(2)}</td>
                    <td class="text-center">
                        <span class="badge ${t.t1 ? 'badge-green' : 'badge-red'}">1R</span>
                        <span class="badge ${t.t2 ? 'badge-green' : 'badge-red'}">2R</span>
                        <span class="badge ${t.t3 ? 'badge-green' : 'badge-red'}">3R</span>
                        <span class="badge ${t.t4 ? 'badge-green' : 'badge-red'}">4R</span>
                    </td>
                    <td class="text-center" style="font-weight:bold;color:${isWin ? '#00e676' : '#ef4444'};">
                        ${t.net >= 0 ? '+' : ''}$${t.net.toFixed(2)}
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = html || '<tr><td colspan="9" class="text-center" style="padding:20px;">معامله‌ای یافت نشد.</td></tr>';

        // Update pagination UI
        const pageInfo = document.getElementById('journalPageInfo');
        if (pageInfo) pageInfo.textContent = `صفحه ${currentPage} از ${totalPages} (${totalItems.toLocaleString()} معامله)`;
    }

    function prevPage() {
        if (currentPage > 1) {
            currentPage--;
            renderJournal();
        }
    }

    function nextPage() {
        const sData = AppStateManager.getSymbolData();
        if (!sData || !sData.trades_json_list) return;
        const totalPages = Math.ceil(sData.trades_json_list.length / pageSize);
        if (currentPage < totalPages) {
            currentPage++;
            renderJournal();
        }
    }

    window.renderTab_journal = function(sData) {
        renderJournal();
    };

    return {
        init: init,
        renderJournal: renderJournal,
        prevPage: prevPage,
        nextPage: nextPage
    };
})();
