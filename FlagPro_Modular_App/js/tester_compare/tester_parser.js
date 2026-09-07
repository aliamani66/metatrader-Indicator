        function handleTesterReportUpload(event) {
            let file = event.target.files && event.target.files[0];
            if (!file) return;

            let reader = new FileReader();
            reader.onload = function(e) {
                try {
                    let buffer = e.target.result;
                    let uint8 = new Uint8Array(buffer);
                    let decoder;
                    if (uint8.length >= 2 && uint8[0] === 0xFF && uint8[1] === 0xFE) {
                        decoder = new TextDecoder('utf-16le');
                    } else if (uint8.length >= 2 && uint8[0] === 0xFE && uint8[1] === 0xFF) {
                        decoder = new TextDecoder('utf-16be');
                    } else if (uint8.length >= 4 && uint8[1] === 0 && uint8[3] === 0) {
                        decoder = new TextDecoder('utf-16le');
                    } else {
                        decoder = new TextDecoder('utf-8');
                    }
                    let content = decoder.decode(buffer);
                    if (content.charCodeAt(0) === 0xFEFF) {
                        content = content.slice(1);
                    }
                    content = content.trim();

                    let reportData = null;

                    if (file.name.toLowerCase().endsWith('.json') || content.startsWith('{')) {
                        reportData = JSON.parse(content);
                        if (reportData && Array.isArray(reportData.trades)) {
                            reportData.trades.forEach(t => {
                                if (t.pnlPips !== undefined && t.profitPips === undefined) t.profitPips = t.pnlPips;
                                if (t.pnlUSD !== undefined && t.profitUSD === undefined) t.profitUSD = t.pnlUSD;
                                if (t.profitPips !== undefined && t.pnlPips === undefined) t.pnlPips = t.profitPips;
                                if (t.profitUSD !== undefined && t.pnlUSD === undefined) t.pnlUSD = t.profitUSD;
                                if (t.discrepancyLabel && !t.discrepancyReason) t.discrepancyReason = t.discrepancyLabel;
                                if (!t.outcome) t.outcome = (((t.profitPips !== undefined ? t.profitPips : t.pnlPips) || 0) >= 0) ? 'Win' : 'Loss';
                            });
                        }
                    } else if (file.name.toLowerCase().endsWith('.csv') || content.includes(',')) {
                        reportData = parseTesterCsvReport(content, file.name);
                    }

                    if (reportData) {
                        let dt = new Date(file.lastModified);
                        let y = dt.getFullYear();
                        let mon = String(dt.getMonth() + 1).padStart(2, '0');
                        let d = String(dt.getDate()).padStart(2, '0');
                        let h = String(dt.getHours()).padStart(2, '0');
                        let min = String(dt.getMinutes()).padStart(2, '0');
                        let fileTime = `${y}.${mon}.${d} ${h}:${min}`;
                        reportData.executionTime = fileTime;
                        reportData.fileTime = fileTime;

                        window.TESTER_REPORTS = window.TESTER_REPORTS || {};
                        let reportKey = 'uploaded_' + Date.now();
                        window.TESTER_REPORTS[reportKey] = reportData;

                        let sel = document.getElementById('testerRunSelector');
                        if (sel) {
                            let opt = document.createElement('option');
                            opt.value = reportKey;
                            opt.textContent = formatTesterOptionLabel(reportKey, reportData);
                            opt.selected = true;
                            sel.insertBefore(opt, sel.firstChild);
                            sel.value = reportKey;
                        }

                        switchTesterReport(reportKey);
                        alert('✅ گزارش تستر متاتریدر با موفقیت بارگذاری و تحلیل شد!');
                    } else {
                        alert('❌ فرمت فایل قابل پردازش نبود. لطفاً فایل خروجی JSON یا CSV تستر را انتخاب فرمایید.');
                    }
                } catch (err) {
                    alert('❌ خطا در پردازش فایل تستر: ' + err.message);
                }
            };
            reader.readAsArrayBuffer(file);
        }

        function parseTesterCsvReport(csvText, fileName) {
            let lines = csvText.split(/\r?\n/).filter(l => l.trim().length > 0);
            if (lines.length < 2) return null;

            let header = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
            let trades = [];
            let totalNetPips = 0.0;
            let totalNetUSD = 0.0;
            let winCnt = 0;
            let lossCnt = 0;
            let grossProfit = 0.0;
            let grossLoss = 0.0;

            for (let i = 1; i < lines.length; i++) {
                let cols = lines[i].split(',').map(c => c.trim().replace(/^"|"$/g, ''));
                if (cols.length < 5) continue;

                let setupId = i;
                let pattern = cols[1] || 'Setup ' + i;
                let tf = cols[2] || 'M1';
                let side = cols[3] || 'BUY';
                let entryTime = cols[4] || '';
                let closeTime = cols[5] || '';
                let boxEntry = parseFloat(cols[6]) || 0.0;
                let fillEntry = parseFloat(cols[7]) || boxEntry;
                let slip = parseFloat(cols[8]) || 0.0;
                let sl = parseFloat(cols[9]) || 0.0;
                let tp1 = parseFloat(cols[10]) || 0.0;
                let tp4 = parseFloat(cols[13]) || 0.0;
                let exitClass = cols[15] || 'Full SL ❌';
                let profitUSD = parseFloat(cols[16]) || 0.0;
                let profitPips = parseFloat(cols[17]) || 0.0;
                let outcome = cols[18] || (profitPips >= 0 ? 'Win' : 'Loss');

                totalNetPips += profitPips;
                totalNetUSD += profitUSD;
                if (profitPips >= 0) {
                    winCnt++;
                    grossProfit += profitPips;
                } else {
                    lossCnt++;
                    grossLoss += Math.abs(profitPips);
                }

                trades.push({
                    setupId: setupId,
                    pattern: pattern,
                    timeframe: tf,
                    side: side,
                    entryTime: entryTime,
                    closeTime: closeTime,
                    boxEntryPrice: boxEntry,
                    marketFillPrice: fillEntry,
                    slippagePips: slip,
                    slPrice: sl,
                    tp1: tp1,
                    tp2: 0,
                    tp3: 0,
                    tp4: tp4,
                    exitClass: exitClass,
                    outcome: outcome,
                    profitPips: profitPips,
                    profitUSD: profitUSD,
                    discrepancyReason: (tf === 'M1' ? 'تایم نویز M1' : (slip > 2.0 ? 'اسلیپیج شدید' : 'منطبق'))
                });
            }

            let wr = (trades.length > 0) ? (winCnt / trades.length * 100.0) : 0.0;
            let pf = (grossLoss > 0) ? (grossProfit / grossLoss) : 0.0;

            return {
                reportTitle: 'گزارش تستر بارگذاری‌شده: ' + fileName,
                symbol: 'Uploaded',
                timeframe: 'Custom',
                dateRange: (trades.length > 0 ? trades[0].entryTime.substring(0, 10) + ' - ' + trades[trades.length - 1].closeTime.substring(0, 10) : ''),
                exportedAt: new Date().toLocaleString('fa-IR'),
                parameters: {
                    InpScenarioName: 'Custom CSV Export'
                },
                kpis: {
                    totalSetups: trades.length,
                    winningSetups: winCnt,
                    losingSetups: lossCnt,
                    winRate: wr,
                    netPips: totalNetPips,
                    netUSD: totalNetUSD,
                    profitFactor: pf,
                    simWinRate: 57.1,
                    simNetR: '+112.1R'
                },
                equityCurve: trades.map((t, idx) => ({
                    time: t.closeTime || t.entryTime,
                    pnlPips: t.profitPips,
                    pnlUSD: t.profitUSD
                })),
                trades: trades
            };
        }

        