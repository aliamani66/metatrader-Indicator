/**
 * FlagPro Dashboard - Main Bootstrap Application
 */
document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // 1. Initialize Core Router
    AppRouter.init();

    // 2. Initialize All Tab Modules
    TabEquity.init();
    TabKings.init();
    TabScaleout.init();
    TabTimeframes.init();
    TabFilters.init();
    TabLossIntel.init();
    TabWeekly.init();
    TabPresets.init();
    TabTesterCompare.init();
    TabOptimizer.init();
    TabJournal.init();

    // 3. Setup Symbol Selector
    const symSel = document.getElementById('symbolSelector');
    if (symSel) {
        symSel.addEventListener('change', function() {
            AppStateManager.setSymbol(this.value);
        });
    }

    // 4. Setup File Upload
    const fileInput = document.getElementById('csvFileInput');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(evt) {
                try {
                    const csvText = evt.target.result;
                    const sData = DataEngine.processCSVData(csvText, file.name);

                    // Register in state
                    AppStateManager.registerSymbolData(sData.symbol, sData);

                    // Add option if not exists
                    let exists = Array.from(symSel.options).some(o => o.value === sData.symbol);
                    if (!exists) {
                        const opt = document.createElement('option');
                        opt.value = sData.symbol;
                        opt.textContent = `${sData.symbol} (فایل کاربر - ${sData.trades_json_list.length} ترید)`;
                        symSel.appendChild(opt);
                    }
                    symSel.value = sData.symbol;
                    AppStateManager.setSymbol(sData.symbol);

                    // Update Data Health Badge
                    DataValidator.updateHealthBadgeUI(sData.validation_report);

                    alert(`✅ داده‌های نماد ${sData.symbol} با موفقیت پردازش شد و تمام تب‌ها به‌روزرسانی شدند!`);
                } catch(err) {
                    console.error('Error uploading CSV:', err);
                    alert('❌ خطا در پردازش فایل: ' + err.message);
                }
            };
            reader.readAsText(file);
        });
    }

    // 5. Load Default Data (if preloaded in window.DEFAULT_DATA)
    if (window.DEFAULT_DATA) {
        Object.keys(window.DEFAULT_DATA).forEach(sym => {
            AppStateManager.registerSymbolData(sym, window.DEFAULT_DATA[sym]);
        });
        const firstSym = Object.keys(window.DEFAULT_DATA)[0] || 'EURUSD';
        AppStateManager.setSymbol(firstSym);
        const curData = AppStateManager.getSymbolData(firstSym);
        if (curData && curData.validation_report) {
            DataValidator.updateHealthBadgeUI(curData.validation_report);
        }
    }
});
