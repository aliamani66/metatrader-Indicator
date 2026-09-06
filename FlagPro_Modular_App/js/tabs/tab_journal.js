var trFilters = {
    basket: 'kings',
    tf: 'ALL',
    dir: 'ALL',
    outcome: 'ALL',
    search: '',
    page: 1,
    pageSize: 50
};

function setTrFilter(key, val, btnElem) {
    trFilters[key] = val;
            trFilters.page = 1;
            if (btnElem && btnElem.parentElement) {
                btnElem.parentElement.querySelectorAll('button').forEach(b => {
                    b.classList.remove('active');
                    b.style.background = '#1e293b';
                    b.style.color = '#94a3b8';
                });
                btnElem.classList.add('active');
                btnElem.style.background = '#0284c7';
                btnElem.style.color = '#ffffff';
            }
            renderTrades();
        }

        function onTrSearch(val) {
            trFilters.search = val.trim().toLowerCase();
            trFilters.page = 1;
            renderTrades();
        }

        function changeTrPageSize(sz) {
            trFilters.pageSize = parseInt(sz) || 50;
            trFilters.page = 1;
            renderTrades();
        }

        function prevTrPage() {
            if (trFilters.page > 1) {
                trFilters.page--;
                renderTrades();
            }
        }

        function nextTrPage() {
            let list = getFilteredTrades();
            let maxPage = Math.ceil(list.length / trFilters.pageSize) || 1;
            if (trFilters.page < maxPage) {
                trFilters.page++;
                renderTrades();
            }
        }

        function getFilteredTrades() {
            return allTrades.filter(t => {
                if (trFilters.basket === 'kings' && !t.is_k) return false;
                if (trFilters.tf !== 'ALL' && t.tf !== trFilters.tf) return false;
                if (trFilters.dir !== 'ALL' && t.dir !== trFilters.dir) return false;
                let isT1 = t.t1 === 1 || t.hr >= 1;
                let isT2 = t.t2 === 1 || t.hr >= 2;
                let isT4 = t.t4 === 1 || t.hr >= 4;
                if (trFilters.outcome === 'TP4' && !isT4) return false;
                if (trFilters.outcome === 'TP2_PLUS' && !isT2) return false;
                if (trFilters.outcome === 'TP1_PLUS' && !isT1) return false;
                if (trFilters.outcome === 'LOSS' && isT1) return false;
                if (trFilters.search) {
                    let s = trFilters.search;
                    let hay = (t.role + ' ' + t.bname + ' ' + t.en_t + ' ' + t.ex_t).toLowerCase();
                    if (!hay.includes(s)) return false;
                }
                return true;
            });
        }

        function renderTrades() {
            let list = getFilteredTrades();
            let total = list.length;
            let pageSize = trFilters.pageSize;
            let totalPages = Math.ceil(total / pageSize) || 1;
            if (trFilters.page > totalPages) trFilters.page = totalPages;
            let curPage = trFilters.page;

            let startIdx = (curPage - 1) * pageSize;
            let endIdx = Math.min(startIdx + pageSize, total);
            let pageTrades = list.slice(startIdx, endIdx);

            let sumNet = 0;
            let cntWin1 = 0;
            let cntWin4 = 0;
            let cntLoss = 0;
            let sumWait = 0;
            let cntWait = 0;
            let minWait = 999999;
            let maxWait = 0;
            for (let i = 0; i < total; i++) {
                let tr = list[i];
                sumNet += tr.net;
                if (tr.t1 === 1) cntWin1++;
                else cntLoss++;
                if (tr.t4 === 1) cntWin4++;
                let wVal = (tr.wait_m !== undefined && tr.wait_m !== null && !isNaN(Number(tr.wait_m))) ? Number(tr.wait_m) : NaN;
                if (isNaN(wVal) && tr.box_t && tr.en_t) {
                    try {
                        let d1 = new Date(tr.box_t.substring(0, 16).replace(/[.]/g, '-').replace(' ', 'T') + ':00Z');
                        let d2 = new Date(tr.en_t.substring(0, 16).replace(/[.]/g, '-').replace(' ', 'T') + ':00Z');
                        let diffSec = (d2.getTime() - d1.getTime()) / 1000;
                        if (!isNaN(diffSec) && diffSec >= 0) {
                            wVal = Math.round((diffSec / 60) * 10) / 10;
                            tr.wait_m = wVal;
                            tr.wait_fmt = wVal < 60 ? Math.round(wVal) + ' دقیقه' : (wVal / 60).toFixed(1) + ' ساعت';
                        }
                    } catch(e) {}
                }
                if (!isNaN(wVal) && wVal >= 0) {
                    sumWait += wVal;
                    cntWait++;
                    if (wVal < minWait) minWait = wVal;
                    if (wVal > maxWait) maxWait = wVal;
                }
            }

            let kpiCount = document.getElementById('trKpiCount');
            let kpiNet = document.getElementById('trKpiNet');
            let kpiWin1 = document.getElementById('trKpiWin1');
            let kpiWin4 = document.getElementById('trKpiWin4');
            let kpiLoss = document.getElementById('trKpiLoss');
            let kpiAvgWait = document.getElementById('trKpiAvgWait');
            let kpiAvgWaitSub = document.getElementById('trKpiAvgWaitSub');

            if (kpiCount) kpiCount.textContent = total.toLocaleString() + ' معامله';
            if (kpiNet) {
                let sign = sumNet >= 0 ? '+' : '';
                kpiNet.textContent = '$' + sign + sumNet.toFixed(2);
                kpiNet.style.color = sumNet >= 0 ? '#34d399' : '#f87171';
            }
            if (kpiWin1) {
                let p1 = total > 0 ? ((cntWin1 / total) * 100).toFixed(1) : '0.0';
                kpiWin1.textContent = p1 + '٪ (' + cntWin1 + ')';
            }
            if (kpiWin4) {
                let p4 = total > 0 ? ((cntWin4 / total) * 100).toFixed(1) : '0.0';
                kpiWin4.textContent = p4 + '٪ (' + cntWin4 + ')';
            }
            if (kpiLoss) {
                let pL = total > 0 ? ((cntLoss / total) * 100).toFixed(1) : '0.0';
                kpiLoss.textContent = pL + '٪ (' + cntLoss + ')';
            }
            if (kpiAvgWait) {
                if (cntWait > 0) {
                    let avgM = sumWait / cntWait;
                    let fmt = avgM < 60 ? Math.round(avgM) + ' دقیقه' : (avgM / 60).toFixed(1) + ' ساعت';
                    kpiAvgWait.textContent = fmt;
                    if (kpiAvgWaitSub) {
                        let minFmt = minWait < 60 ? Math.round(minWait) + 'm' : (minWait / 60).toFixed(1) + 'h';
                        let maxFmt = maxWait < 60 ? Math.round(maxWait) + 'm' : (maxWait / 60).toFixed(1) + 'h';
                        kpiAvgWaitSub.textContent = 'بازه: ' + minFmt + ' تا ' + maxFmt;
                    }
                } else {
                    kpiAvgWait.textContent = '-';
                    if (kpiAvgWaitSub) kpiAvgWaitSub.textContent = 'از تشکیل باکس تا ورود';
                }
            }

            let tbody = document.getElementById('tradesTableBody');
            if (!tbody) return;

            let rowsHtml = '';
            for (let i = 0; i < pageTrades.length; i++) {
                let t = pageTrades[i];
                let rowNum = startIdx + i + 1;
                let dirBadge = t.dir === 'BUY' 
                    ? '<span style="background:#064e3b;color:#34d399;padding:2px 8px;border-radius:4px;font-weight:bold;">BUY 🟢</span>' 
                    : '<span style="background:#450a0a;color:#f87171;padding:2px 8px;border-radius:4px;font-weight:bold;">SELL 🔴</span>';
                
                let kingBadge = t.is_k 
                    ? '<span style="background:#854d0e;color:#fef08a;font-size:10px;padding:1px 6px;border-radius:4px;margin-right:4px;">👑 سلطان</span>' 
                    : '';

                let tfBadge = '<span style="background:#1e293b;color:#93c5fd;font-weight:bold;padding:2px 6px;border-radius:4px;">' + t.tf + '</span>';

                function tpPill(val, hit, label, col) {
                    let border = hit ? 'border:1px solid ' + col + ';' : 'opacity:0.35;';
                    let check = hit ? ' <b style="color:' + col + ';">✓</b>' : '';
                    let bg = hit ? 'background:#0f172a;' : 'background:transparent;';
                    return '<div style="' + bg + 'padding:2px 6px;border-radius:4px;font-family:monospace;font-size:11px;' + border + '">' +
                           '<span style="color:' + col + ';font-size:9.5px;display:block;">' + label + '</span>' +
                           val.toFixed(5) + check + '</div>';
                }

                let isT1 = t.t1 === 1 || t.hr >= 1;
                let isT2 = t.t2 === 1 || t.hr >= 2;
                let isT3 = t.t3 === 1 || t.hr >= 3;
                let isT4 = t.t4 === 1 || t.hr >= 4;

                let tp1Html = tpPill(t.tp1, isT1, 'TP1 (1:1)', '#fbbf24');
                let tp2Html = tpPill(t.tp2, isT2, 'TP2 (1:2)', '#60a5fa');
                let tp3Html = tpPill(t.tp3, isT3, 'TP3 (1:3)', '#38bdf8');
                let tp4Html = tpPill(t.tp4, isT4, 'TP4 (1:4)', '#c084fc');

                let exitDesc = '';
                if (isT4) {
                    exitDesc = '<span style="background:#3b0764;color:#e9d5ff;padding:3px 8px;border-radius:4px;border:1px solid #a855f7;font-weight:bold;">💎 تارگت ۴ (فول تارگت)</span>';
                } else if (isT3) {
                    exitDesc = '<span style="background:#075985;color:#bae6fd;padding:3px 8px;border-radius:4px;border:1px solid #0284c7;">🎯 خروج تا پله ۳ (SL+2)</span>';
                } else if (isT2) {
                    exitDesc = '<span style="background:#1e3a8a;color:#bfdbfe;padding:3px 8px;border-radius:4px;border:1px solid #3b82f6;">🎯 خروج تا پله ۲ (SL+1)</span>';
                } else if (isT1) {
                    exitDesc = '<span style="background:#854d0e;color:#fef08a;padding:3px 8px;border-radius:4px;border:1px solid #eab308;">🛡️ خروج پله ۱ + BE</span>';
                } else {
                    exitDesc = '<span style="background:#450a0a;color:#fca5a5;padding:3px 8px;border-radius:4px;border:1px solid #dc2626;">🛑 حد زیان اولیه (SL)</span>';
                }

                let netColor = t.net >= 0 ? '#34d399' : '#f87171';
                let netBg = t.net >= 0 ? '#064e3b33' : '#450a0a33';
                let netSign = t.net >= 0 ? '+' : '';
                let netHtml = '<span style="background:' + netBg + ';color:' + netColor + ';padding:3px 10px;border-radius:4px;font-weight:bold;font-family:monospace;font-size:12.5px;">$' + netSign + t.net.toFixed(2) + '</span>';

                let rowBg = i % 2 === 0 ? 'background:#081c30;' : 'background:#0a233c;';

                rowsHtml += '<tr style="' + rowBg + 'border-bottom:1px solid #133352;text-align:center;">' +
                    '<td style="padding:8px 6px;color:#64748b;font-size:11px;">' + rowNum + '</td>' +
                    '<td style="padding:8px 6px;font-size:11px;direction:ltr;font-family:monospace;color:#94a3b8;">' +
                        '<div>🟢 ' + t.en_t + '</div>' +
                        '<div style="color:#64748b;font-size:10px;">🔴 ' + t.ex_t + '</div>' +
                        (() => {
                            let wTxt = (t.wait_fmt && t.wait_fmt !== '-') ? t.wait_fmt : (t.wait_m > 0 ? (t.wait_m < 60 ? Math.round(t.wait_m) + ' دقیقه' : (t.wait_m / 60).toFixed(1) + ' ساعت') : '');
                            return wTxt ? '<div style="color:#38bdf8;font-size:10px;margin-top:2px;direction:rtl;font-family:sans-serif;">⏱️ انتظار: ' + wTxt + '</div>' : '';
                        })() +
                    '</td>' +
                    '<td style="padding:8px 6px;">' + tfBadge + '</td>' +
                    '<td style="padding:8px 10px;text-align:right;">' +
                        '<div>' + kingBadge + '<b style="color:#e2e8f0;font-size:12.5px;">' + t.role + '</b></div>' +
                        '<div style="color:#94a3b8;font-size:10.5px;margin-top:2px;">' + t.bname + '</div>' +
                    '</td>' +
                    '<td style="padding:8px 6px;">' + dirBadge + '</td>' +
                    '<td style="padding:8px 6px;font-family:monospace;color:#e2e8f0;">' + t.en_p.toFixed(5) + '</td>' +
                    '<td style="padding:8px 6px;font-family:monospace;color:#fca5a5;background:#2d121733;">' + t.sl.toFixed(5) + '</td>' +
                    '<td style="padding:8px 6px;">' + tp1Html + '</td>' +
                    '<td style="padding:8px 6px;">' + tp2Html + '</td>' +
                    '<td style="padding:8px 6px;">' + tp3Html + '</td>' +
                    '<td style="padding:8px 6px;">' + tp4Html + '</td>' +
                    '<td style="padding:8px 8px;">' + exitDesc + '</td>' +
                    '<td style="padding:8px 10px;">' + netHtml + '</td>' +
                '</tr>';
            }

            tbody.innerHTML = rowsHtml;

            let pInfo = document.getElementById('trPaginationInfo');
            let pCur = document.getElementById('trPageCurrent');
            let btnP = document.getElementById('trBtnPrev');
            let btnN = document.getElementById('trBtnNext');

            if (pInfo) {
                if (total === 0) {
                    pInfo.textContent = 'هیچ معامله‌ای با این فیلترها یافت نشد.';
                } else {
                    pInfo.textContent = 'نمایش ' + (startIdx + 1) + ' تا ' + endIdx + ' از مجموع ' + total.toLocaleString() + ' معامله';
                }
            }
            if (pCur) pCur.textContent = 'صفحه ' + curPage + ' از ' + totalPages;
            if (btnP) btnP.disabled = (curPage <= 1);
            if (btnN) btnN.disabled = (curPage >= totalPages);
        }
    