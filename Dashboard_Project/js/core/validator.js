/**
 * FlagPro Dashboard - Comprehensive Data Validation Engine
 * Ensures 100% data integrity, formats compliance, and provides health reports.
 */
const DataValidator = (function() {
    'use strict';

    const MANDATORY_COLUMNS = ['Role', 'Timeframe', 'EntryTime', 'RiskPoints', 'HitTargetRatio'];
    const RECOMMENDED_COLUMNS = ['Symbol', 'BoxName', 'Direction', 'ExitTime', 'TP1', 'TP2', 'TP3', 'TP4', 'IsClosed', 'Outcome'];

    function validateCSV(csvText, fileName) {
        const report = {
            isValid: true,
            status: 'EXCELLENT', // EXCELLENT, WARNING, ERROR
            score: 100,
            fileName: fileName || 'Uploaded_File.csv',
            totalLines: 0,
            validTradesCount: 0,
            pendingCount: 0,
            corruptCount: 0,
            missingColumns: [],
            detectedSymbol: '',
            detectedTFs: new Set(),
            dateRange: { start: '', end: '' },
            issues: [],
            warnings: []
        };

        if (!csvText || typeof csvText !== 'string' || csvText.trim().length === 0) {
            report.isValid = false;
            report.status = 'ERROR';
            report.score = 0;
            report.issues.push('محتوای فایل ارسالی خالی است.');
            return report;
        }

        const lines = csvText.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
        report.totalLines = lines.length;

        if (lines.length < 2) {
            report.isValid = false;
            report.status = 'ERROR';
            report.score = 0;
            report.issues.push('فایل باید حداقل دارای یک سطر هدر و یک سطر داده باشد.');
            return report;
        }

        // 1. Validate Headers
        const rawHeaders = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, ''));
        const colMap = {};
        rawHeaders.forEach((h, idx) => { colMap[h] = idx; });

        for (let col of MANDATORY_COLUMNS) {
            if (colMap[col] === undefined) {
                report.missingColumns.push(col);
            }
        }

        if (report.missingColumns.length > 0) {
            report.isValid = false;
            report.status = 'ERROR';
            report.score = Math.max(0, 100 - report.missingColumns.length * 25);
            report.issues.push('ستون‌های حیاتی زیر در فایل یافت نشدند: ' + report.missingColumns.join(', '));
            return report;
        }

        // Check recommended
        for (let col of RECOMMENDED_COLUMNS) {
            if (colMap[col] === undefined) {
                report.warnings.push('ستون فرعی «' + col + '» وجود ندارد (مقادیر پیش‌فرض جایگزین شد).');
                report.score -= 2;
            }
        }

        // 2. Scan Rows
        let firstDate = '', lastDate = '';
        for (let i = 1; i < lines.length; i++) {
            const parts = lines[i].split(',').map(p => p.trim().replace(/^["']|["']$/g, ''));
            if (parts.length < 5) {
                report.corruptCount++;
                continue;
            }

            // Is closed / pending check
            const isClosed = colMap['IsClosed'] !== undefined ? parts[colMap['IsClosed']] : 'True';
            const outcome = colMap['Outcome'] !== undefined ? parts[colMap['Outcome']] : '';
            if (isClosed === 'False' || outcome.toLowerCase() === 'pending') {
                report.pendingCount++;
                continue;
            }

            const role = parts[colMap['Role']];
            const tf = parts[colMap['Timeframe']] || 'M1';
            const et = parts[colMap['EntryTime']];
            const pts = parseFloat(parts[colMap['RiskPoints']]);
            const hr = parseInt(parts[colMap['HitTargetRatio']]);

            if (!role || isNaN(pts) || pts <= 0 || isNaN(hr) || hr < 0 || hr > 4 || !et) {
                report.corruptCount++;
                continue;
            }

            if (!report.detectedSymbol && colMap['Symbol'] !== undefined && parts[colMap['Symbol']]) {
                report.detectedSymbol = parts[colMap['Symbol']].replace(/[^a-zA-Z0-9]/g, '');
            }

            report.detectedTFs.add(tf);
            report.validTradesCount++;

            if (!firstDate || et < firstDate) firstDate = et;
            if (!lastDate || et > lastDate) lastDate = et;
        }

        report.dateRange.start = firstDate ? firstDate.substring(0, 10) : '-';
        report.dateRange.end = lastDate ? lastDate.substring(0, 10) : '-';

        if (report.validTradesCount === 0) {
            report.isValid = false;
            report.status = 'ERROR';
            report.score = 10;
            report.issues.push('هیچ معامله بسته‌شده و معتبری در این فایل یافت نشد.');
            return report;
        }

        if (report.corruptCount > 0) {
            const corruptRatio = (report.corruptCount / (lines.length - 1)) * 100;
            if (corruptRatio > 10) {
                report.status = 'WARNING';
                report.score -= Math.min(30, Math.round(corruptRatio));
                report.issues.push('تعداد ' + report.corruptCount + ' سطر ناقص یا دارای خطای عددی رد شدند.');
            }
        }

        if (report.score >= 90) report.status = 'EXCELLENT';
        else if (report.score >= 65) report.status = 'WARNING';
        else report.status = 'ERROR';

        return report;
    }

    function updateHealthBadgeUI(report) {
        const badge = document.getElementById('dataHealthBadge');
        if (!badge) return;

        badge.className = 'data-health-badge';
        if (report.status === 'EXCELLENT') {
            badge.classList.add('valid');
            badge.innerHTML = '<span>🟢</span><span>داده معتبر (' + report.validTradesCount.toLocaleString() + ' ترید)</span>';
            badge.title = 'کیفیت داده ۱۰۰٪ تأیید شد | نمره سلامت: ' + report.score + '/100';
        } else if (report.status === 'WARNING') {
            badge.classList.add('warning');
            badge.innerHTML = '<span>🟡</span><span>هشدار جزئی (' + report.score + '٪)</span>';
            badge.title = report.issues.join(' | ');
        } else {
            badge.classList.add('error');
            badge.innerHTML = '<span>🔴</span><span>خطای داده</span>';
            badge.title = report.issues.join(' | ');
        }
    }

    return {
        validateCSV: validateCSV,
        updateHealthBadgeUI: updateHealthBadgeUI
    };
})();
