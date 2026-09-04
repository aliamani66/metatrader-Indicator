function openTab(evt, tabId) {
            let contents = document.querySelectorAll('.tab-content');
            contents.forEach(c => c.classList.remove('active'));

            let btns = document.querySelectorAll('.tab-btn');
            btns.forEach(b => b.classList.remove('active'));

            document.getElementById(tabId).classList.add('active');
            evt.currentTarget.classList.add('active');

            if (tabId === 'tab-equity') {
                setTimeout(() => {
                    initEquityCanvasEvents();
                    initSimUI();
                    initWeeklyBarCanvasEvents();
                    drawWeeklyBarChart(currentWeeklyBarMode);
                }, 50);
            }

            if (tabId === 'tab-trades') {
                setTimeout(() => {
                    renderTrades();
                }, 30);
            }

            if (tabId === 'tab-tester-compare') {
                setTimeout(() => {
                    initTesterCompareTab();
                }, 50);
            }
        }

        let sortDirections = { 'data-score': true };

        
function toggleSidebar() {
            let sb = document.getElementById('mainSidebar');
            let icon = document.getElementById('btnToggleSidebarIcon');
            let txt = document.getElementById('btnToggleSidebarText');
            if (!sb) return;
            sb.classList.toggle('collapsed');
            let isCollapsed = sb.classList.contains('collapsed');
            try {
                localStorage.setItem('flagpro_sidebar_collapsed', isCollapsed ? 'true' : 'false');
            } catch(e) {}
            if (icon) icon.textContent = isCollapsed ? '📑' : '☰';
            if (txt) txt.textContent = isCollapsed ? 'نمایش منو' : 'منو';

            // Re-render charts on resize
            setTimeout(() => {
                if (typeof drawEquityChart === 'function') drawEquityChart();
                if (typeof drawWeeklyBarChart === 'function' && typeof currentWeeklyBarMode !== 'undefined') drawWeeklyBarChart(currentWeeklyBarMode);
            }, 260);
        }

        function toggleDrawdownOverlay() {
            simState.showDrawdown = !simState.showDrawdown;
            let btn = document.getElementById('btnToggleDrawdown');
            let lbl = document.getElementById('lblToggleDrawdownState');
            if (btn && lbl) {
                if (simState.showDrawdown) {
                    lbl.textContent = 'روشن';
                    lbl.style.color = '#4ade80';
                    btn.style.background = '#1e1b4b';
                    btn.style.borderColor = '#6366f1';
                    btn.style.color = '#c7d2fe';
                } else {
                    lbl.textContent = 'خاموش';
                    lbl.style.color = '#94a3b8';
                    btn.style.background = '#0f172a';
                    btn.style.borderColor = '#334155';
                    btn.style.color = '#94a3b8';
                }
            }
            drawEquityChart();
        }

        function toggleTwoColLayout() {
            let container = document.getElementById('eqTwoColContainer');
            let btn = document.getElementById('btnToggleTwoCol');
            if (!container) return;
            if (container.classList.contains('single-col')) {
                container.classList.remove('single-col');
                if (btn) { btn.textContent = '⛶'; btn.title = 'حالت تمام‌صفحه'; }
            } else {
                container.classList.add('single-col');
                if (btn) { btn.textContent = '🗗'; btn.title = 'حالت دو ستونی'; }
            }
            setTimeout(() => {
                drawEquityChart();
            }, 50);
        }

        
        
// App Initialization
function initApp() {
    try {
        if (localStorage.getItem('flagpro_sidebar_collapsed') === 'true') {
            let sb = document.getElementById('mainSidebar');
            let icon = document.getElementById('btnToggleSidebarIcon');
            let txt = document.getElementById('btnToggleSidebarText');
            if (sb) sb.classList.add('collapsed');
            if (icon) icon.textContent = '📑';
            if (txt) txt.textContent = 'نمایش منو';
        }
    } catch(e) {}

    if (typeof initPersistedSymbols === 'function') initPersistedSymbols();
    if (typeof switchDashboardSymbol === 'function' && typeof currentActiveSymbol !== 'undefined') {
        switchDashboardSymbol(currentActiveSymbol);
    }
    if (typeof initEquityCanvasEvents === 'function') initEquityCanvasEvents();
    if (typeof initSimUI === 'function') initSimUI();
    if (typeof renderTrades === 'function') renderTrades();
    if (typeof initTesterCompareTab === 'function') initTesterCompareTab();
    if (typeof drawEquityChart === 'function') drawEquityChart();
    if (typeof drawWeeklyBarChart === 'function' && typeof currentWeeklyBarMode !== 'undefined') {
        drawWeeklyBarChart(currentWeeklyBarMode);
    }
}

window.addEventListener('DOMContentLoaded', initApp);
window.addEventListener('load', initApp);

