/**
 * FlagPro Dashboard - Tab Navigation & Router
 */
const AppRouter = (function() {
    'use strict';

    function init() {
        document.querySelectorAll('.nav-link[data-tab]').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const tabId = this.getAttribute('data-tab');
                switchTab(tabId);
            });
        });
    }

    function switchTab(tabId) {
        if (!tabId) return;

        // Update nav links
        document.querySelectorAll('.nav-link').forEach(l => {
            l.classList.remove('active');
            if (l.getAttribute('data-tab') === tabId) l.classList.add('active');
        });

        // Update tab panes
        document.querySelectorAll('.tab-pane').forEach(p => {
            p.classList.remove('active');
        });

        const targetPane = document.getElementById('tab-' + tabId);
        if (targetPane) {
            targetPane.classList.add('active');
        }

        AppStateManager.state.activeTab = tabId;

        // Call tab-specific activation hook if defined
        const hookName = 'renderTab_' + tabId;
        if (window[hookName] && typeof window[hookName] === 'function') {
            const symData = AppStateManager.getSymbolData();
            if (symData) window[hookName](symData);
        }
    }

    return {
        init: init,
        switchTab: switchTab
    };
})();
