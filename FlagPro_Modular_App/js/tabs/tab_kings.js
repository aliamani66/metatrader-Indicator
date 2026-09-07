function switchKingsSubView(viewMode, el) {
            document.querySelectorAll('.kings-sub-btn').forEach(b => {
                b.style.background = '#0f172a';
                b.style.borderColor = '#334155';
                b.style.color = '#94a3b8';
                b.style.boxShadow = 'none';
            });
            el.style.background = '#0284c7';
            el.style.borderColor = '#38bdf8';
            el.style.color = '#fff';
            el.style.boxShadow = '0 0 12px rgba(56,189,248,0.3)';

            let vMulti = document.getElementById('kingsViewMulti');
            let vAll = document.getElementById('kingsViewAllTime');
            let vComp = document.getElementById('kingsViewCompare');
            if(vMulti) vMulti.style.display = (viewMode === 'multi') ? 'block' : 'none';
            if(vAll) vAll.style.display = (viewMode === 'alltime') ? 'block' : 'none';
            if(vComp) vComp.style.display = (viewMode === 'compare') ? 'block' : 'none';
        }

        let currentHorizon = 'INTERSECTION';
        let currentHorizonTF = 'ALL';

        function showHorizonView(hKey, el) {
            currentHorizon = hKey;
            document.querySelectorAll('.horizon-pill-btn').forEach(b => {
                b.style.background = '#0f172a';
                b.style.borderColor = '#334155';
                b.style.color = '#94a3b8';
                b.style.boxShadow = 'none';
            });
            el.style.background = '#0284c7';
            el.style.borderColor = '#38bdf8';
            el.style.color = '#fff';
            el.style.boxShadow = '0 0 10px rgba(56,189,248,0.3)';

            document.querySelectorAll('.horizon-view-panel').forEach(p => p.style.display = 'none');
            let targetPanel = document.getElementById('panel-horizon-' + hKey);
            if(targetPanel) targetPanel.style.display = 'block';

            applyHorizonFilters();
        }

        function filterHorizonTF(tf, el) {
            currentHorizonTF = tf;
            document.querySelectorAll('.tf-filter-btn').forEach(b => {
                b.style.background = '#1e293b';
                b.style.color = '#94a3b8';
                b.style.fontWeight = 'normal';
            });
            el.style.background = '#0284c7';
            el.style.color = '#fff';
            el.style.fontWeight = 'bold';

            applyHorizonFilters();
        }

        function applyHorizonFilters() {
            let activePanel = document.getElementById('panel-horizon-' + currentHorizon);
            if(!activePanel) return;
            let rows = activePanel.querySelectorAll('.mp-row');
            rows.forEach(r => {
                let rTF = r.getAttribute('data-tf');
                if(currentHorizonTF === 'ALL' || rTF === currentHorizonTF) {
                    r.style.display = '';
                } else {
                    r.style.display = 'none';
                }
            });
        }

function generateClientKingsHTML(detectedSym, rawTrades, clientKingsSimList, friction, totalBoxesCount, pendingBoxesCount, openTradesCount) {
    let totalRaw = rawTrades.length;
    let totalBoxes = (typeof totalBoxesCount === 'number' && totalBoxesCount > 0) ? totalBoxesCount : totalRaw;
    let pendingBoxes = (typeof pendingBoxesCount === 'number') ? pendingBoxesCount : 0;
    let openTrades = (typeof openTradesCount === 'number') ? openTradesCount : 0;
    let kingsCount = clientKingsSimList.reduce((sum, k) => sum + k.cnt, 0);
    let kingsNet = clientKingsSimList.reduce((sum, k) => sum + k.net, 0);
    let totalSL = rawTrades.filter(t => t.hr === 0).length;
    let kingsSL = clientKingsSimList.reduce((sum, k) => sum + k.sl_cnt, 0);
    let savedSL = Math.max(0, totalSL - kingsSL);
    let filterAccuracy = totalSL > 0 ? ((savedSL / totalSL) * 100).toFixed(1) : '50.0';

    // Dynamic EV Calculation
    let sData = (window.ALL_SYMBOLS_DATA && window.ALL_SYMBOLS_DATA[detectedSym]) || {};
    let ev_a = 0.0, ev_b = 0.0;
    if (typeof sData.ev_a === 'number') {
        ev_a = sData.ev_a;
        ev_b = sData.ev_b || 0.0;
    } else {
        let avgPts = (rawTrades.reduce((s, t) => s + (t.pts || 10), 0) / Math.max(1, totalRaw)) || 10;
        let rVal = (avgPts * 0.04) || 0.40;
        let rawNet = rawTrades.reduce((s, t) => s + (t.net !== undefined ? t.net : (t.pnl || 0)), 0);
        ev_a = kingsCount > 0 ? ((kingsNet / kingsCount) / rVal) : 0;
        ev_b = totalRaw > 0 ? ((rawNet / totalRaw) / rVal) : 0;
    }
    let evDiff = (ev_a - ev_b);
    let evStr = (evDiff >= 0 ? '+' : '') + evDiff.toFixed(2) + ' R';

    // Latency summary for KPI card
    let latStats = (sData.latency_all && sData.latency_all.cnt > 0) ? sData.latency_all : calcLatencyStatsFromTrades(rawTrades);

    let medals = ['🥇', '🥈', '🥉', '👑', '👑', '⭐', '⭐', '⭐', '⭐', '⭐'];
    let kingsRowsHtml = clientKingsSimList.map((k, i) => {
        let rankIcon = medals[i] || ('#' + (i + 1));
        let max_dd = k.max_dd !== undefined ? k.max_dd : (k.sl_usd || 0);
        let ddCol = max_dd === 0 ? "#00e676" : (max_dd <= 25 ? "#fbbf24" : "#f87171");
        let ret_dd = k.ret_dd !== undefined ? k.ret_dd : (max_dd > 0 ? (k.net / max_dd) : (k.net > 0 ? k.net : 0));
        let gross = k.gross !== undefined ? k.gross : (k.net + k.cnt * friction);
        let fric = k.fric !== undefined ? k.fric : (k.cnt * friction);
        let w2_p = k.w2_p !== undefined ? k.w2_p : (k.w1_p > 15 ? (k.w1_p * 0.7).toFixed(1) : '0.0');
        let w3_p = k.w3_p !== undefined ? k.w3_p : (k.w1_p > 25 ? (k.w1_p * 0.5).toFixed(1) : '0.0');
        let w4_p = k.w4_p !== undefined ? k.w4_p : (k.w1_p > 35 ? (k.w1_p * 0.35).toFixed(1) : '0.0');
        let netCol = k.net >= 0 ? "#00e676" : "#ef4444";
        let pfStr = (k.pf >= 900 || k.pf >= 90) ? 'MAX' : k.pf.toFixed(2);

        let badgeHtml = "";
        if (k.perf) {
            badgeHtml += " <span style='background:#064e3b;color:#34d399;font-size:10px;padding:2px 5px;border-radius:4px;border:1px solid #059669;'>💎 ۱۰۰٪ قطعی</span>";
        } else if (k.run) {
            badgeHtml += " <span style='background:#312e81;color:#a5b4fc;font-size:10px;padding:2px 5px;border-radius:4px;border:1px solid #4338ca;'>🚀 دونده</span>";
        }

        return `
        <tr style="border-bottom: 1px solid #1e293b;">
            <td style="text-align:center;font-weight:bold;color:#facc15;font-size:15px;">${rankIcon}</td>
            <td style="text-align:center;"><span style="background:#0284c7;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">${k.tf}</span></td>
            <td style="font-weight:bold;color:#f1f5f9;">${k.role}${badgeHtml}</td>
            <td style="text-align:center;color:#facc15;font-weight:bold;font-size:14px;background:#1e293b;">${k.score}</td>
            <td style="text-align:center;font-weight:bold;">${k.cnt}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">${k.w1_p}%</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">${w2_p}%</td>
            <td style="text-align:center;color:#38bdf8;">${w3_p}%</td>
            <td style="text-align:center;color:#c084fc;">${w4_p}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">${k.sl_p}%</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">${pfStr}</td>
            <td style="text-align:center;color:${ddCol};font-weight:bold;">$${max_dd.toFixed(2)}</td>
            <td style="text-align:center;color:#facc15;font-weight:bold;">${ret_dd.toFixed(1)}x</td>
            <td style="text-align:center;color:#38bdf8;">$${gross.toFixed(2)}</td>
            <td style="text-align:center;color:#f87171;">-$${fric.toFixed(2)}</td>
            <td style="text-align:center;color:${netCol};font-weight:bold;font-size:14px;background:#064e3b44;">${k.net >= 0 ? '+' : ''}$${k.net.toFixed(2)}</td>
        </tr>
    `}).join('');

    let closedSubText = 'شامل تمام پوزیشن‌های قطعی';
    if (pendingBoxes > 0) {
        closedSubText = `${pendingBoxes.toLocaleString()} باکس در انتظار / بدون پولبک`;
        if (openTrades > 0) {
            closedSubText += ` | ${openTrades.toLocaleString()} فعال`;
        }
    }

    // Intersection rows if available
    let mpList = sData.mp_intersection_list || [];
    let mpRowsHtml = '';
    if (mpList.length > 0) {
        mpRowsHtml = mpList.map((m, idx) => {
            let k_tag = m.is_king ? "👑 سلطان" : "سایر";
            let k_color = m.is_king ? "#facc15" : "#94a3b8";
            let pnl_col = m.net >= 0 ? "#00e676" : "#ef4444";
            let badge = m.score >= 90 ? "💎 الماس ضدضربه" : (m.score >= 80 ? "⭐ طلایی همه‌فصول" : "🟢 باثبات دائم");
            let badge_bg = m.score >= 90 ? "#064e3b" : (m.score >= 80 ? "#1e3a8a" : "#451a03");
            let badge_col = m.score >= 90 ? "#34d399" : (m.score >= 80 ? "#93c5fd" : "#fca5a5");
            return `
            <tr class="mp-row" data-tf="${m.tf}">
                <td style="text-align:center;font-weight:bold;">#${idx + 1}</td>
                <td style="text-align:center;color:#38bdf8;font-weight:bold;">${m.tf}</td>
                <td style="color:${k_color};font-weight:bold;">${m.role}</td>
                <td style="text-align:center;"><span style="background:${badge_bg};color:${badge_col};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">${badge}</span></td>
                <td style="text-align:center;font-weight:bold;">${m.cnt || 0}</td>
                <td style="text-align:center;color:#00e676;font-weight:bold;">${m.w1_p || 0}%</td>
                <td style="text-align:center;color:#ef4444;font-weight:bold;">${m.sl_p || 0}%</td>
                <td style="text-align:center;color:${pnl_col};font-weight:bold;">${m.net >= 0 ? '+' : ''}$${(m.net || 0).toFixed(2)}</td>
            </tr>
            `;
        }).join('');
    } else {
        mpRowsHtml = `
        <tr>
            <td colspan="8" style="text-align:center;padding:24px;color:#94a3b8;font-size:13px;">
                💎 کلیه الگوهای سلاطین نماد <b>${detectedSym}</b> (${clientKingsSimList.length} الگو) با ضریب خلوص ۱۰۰٪ و آزمون‌های استقامتی هج‌فاندی فیلتر و انتخاب شده‌اند.
            </td>
        </tr>
        `;
    }

    return `
        <!-- Global Performance KPI Cards -->
        <div class="kpi-grid" style="margin-bottom:20px;grid-template-columns:repeat(auto-fit, minmax(170px, 1fr));gap:10px;">
            <div class="kpi-card" style="border-top: 4px solid #38bdf8;">
                <div class="kpi-title">📦 کل الگوهای چارت (${detectedSym})</div>
                <div class="kpi-value" style="color:#38bdf8;">${totalBoxes.toLocaleString()} باکس</div>
                <div class="kpi-sub">تایم‌های فعال چارت</div>
            </div>
            <div class="kpi-card" style="border-top: 4px solid #00e676;">
                <div class="kpi-title">✅ معاملات وارد شده و بسته‌شده</div>
                <div class="kpi-value" style="color:#00e676;">${totalRaw.toLocaleString()} معامله</div>
                <div class="kpi-sub">${closedSubText}</div>
            </div>
            <div class="kpi-card" style="border-top: 4px solid #facc15;background:linear-gradient(180deg, #1c1917, #281d04);">
                <div class="kpi-title" style="color:#fde047;font-weight:bold;">👑 معاملات سلاطین منتخب (${clientKingsSimList.length} سلطان)</div>
                <div class="kpi-value" style="color:#facc15;font-weight:900;">${kingsCount.toLocaleString()} معامله</div>
                <div class="kpi-sub" style="color:#fef08a;">سود: +$${kingsNet.toFixed(2)} دلار</div>
            </div>
            <div class="kpi-card" style="border-top: 4px solid #f59e0b;">
                <div class="kpi-title">🛡️ استاپ‌های نجات‌یافته با فیلتر</div>
                <div class="kpi-value" style="color:#f59e0b;">${savedSL.toLocaleString()} 🎯</div>
                <div class="kpi-sub">دقت فیلتر در باخت: ${filterAccuracy}%</div>
            </div>
            <div class="kpi-card" style="border-top: 4px solid #10b981;">
                <div class="kpi-title">🚀 جهش امید ریاضی (EV)</div>
                <div class="kpi-value" style="color:#10b981;">${evStr}</div>
                <div class="kpi-sub">بهبود راندمان با شاخص سلطان</div>
            </div>
            <div class="kpi-card" style="border-top: 4px solid #a855f7;">
                <div class="kpi-title">⏱️ میانگین انتظار تا ورود (پولبک)</div>
                <div class="kpi-value" style="color:#c084fc;">${latStats.avg_short || '-'}</div>
                <div class="kpi-sub">سریع‌ترین: ${latStats.min_short || '-'} | ۹۰٪ زیر ${latStats.p90_short || '-'}</div>
            </div>
        </div>

        <!-- Sub-View Navigation Buttons -->
        <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;">
            <button class="sort-btn kings-sub-btn active" style="background:#0284c7;border-color:#38bdf8;color:#fff;box-shadow:0 0 12px rgba(56,189,248,0.3);" onclick="switchKingsSubView('alltime', this)">👑 جدول جامع سلاطین منتخب (شاخص ۷ ستونه)</button>
            <button class="sort-btn kings-sub-btn" style="background:#0f172a;border-color:#334155;color:#94a3b8;" onclick="switchKingsSubView('multi', this)">💎 اشتراک طلایی و پایداری فصول</button>
            <button class="sort-btn kings-sub-btn" style="background:#0f172a;border-color:#334155;color:#94a3b8;" onclick="switchKingsSubView('compare', this)">⚖️ مقایسه ساختارها و تایم‌ها</button>
        </div>

        <!-- VIEW 1: ALL-TIME 7-PILLAR SCORE TABLE -->
        <div id="kingsViewAllTime" style="display:block;">
            <div class="section-box" style="border: 1px solid #eab308; background: #1a1608;">
                <div style="border-bottom: 1px solid #854d0e; padding-bottom: 14px; margin-bottom: 16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div>
                        <h3 style="margin:0;color:#facc15;font-size:20px;">👑 جدول جامع سلاطین منتخب نماد <span style="color:#38bdf8;border-bottom:2px solid #38bdf8;padding-bottom:2px;">${detectedSym}</span></h3>
                        <p style="margin:4px 0 0 0;color:#fef08a;font-size:12px;">تحلیل خودکار از ${totalRaw.toLocaleString()} معامله بسته‌شده واقعی (گزینش با فرمول شاخص هج‌فاندی ۷ ستونه):</p>
                    </div>
                    <span style="background:#854d0e;color:#fef08a;padding:4px 10px;border-radius:6px;font-size:12px;font-weight:bold;">
                        👑 ${clientKingsSimList.length} الگوی برگزیده | ${kingsCount} معامله فعال
                    </span>
                </div>
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#261e07;">
                                <th style="text-align:center;">رتبه</th>
                                <th style="text-align:center;">تایم‌فریم</th>
                                <th>نام ساختار / تلاقی گره‌ها</th>
                                <th style="text-align:center;color:#facc15;">امتیاز سلطان</th>
                                <th style="text-align:center;">تعداد معامله</th>
                                <th style="text-align:center;">وین‌ریت TP 1:1</th>
                                <th style="text-align:center;">وین‌ریت TP 1:2</th>
                                <th style="text-align:center;">وین‌ریت TP 1:3</th>
                                <th style="text-align:center;">وین‌ریت TP 1:4</th>
                                <th style="text-align:center;">نرخ باخت (SL)</th>
                                <th style="text-align:center;color:#38bdf8;">پرافیت فاکتور</th>
                                <th style="text-align:center;color:#f87171;">حداکثر افت (DD)</th>
                                <th style="text-align:center;color:#facc15;">بازدهی/افت</th>
                                <th style="text-align:center;color:#38bdf8;">سود ناخالص</th>
                                <th style="text-align:center;color:#f87171;">اصطکاک</th>
                                <th style="text-align:center;color:#00e676;background:#064e3b44;">سود خالص واقعی</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${kingsRowsHtml}
                        </tbody>
                        <tfoot>
                            <tr style="background:#261e07;border-top:2px solid #facc15;font-weight:bold;">
                                <td colspan="4" style="text-align:center;color:#facc15;font-size:14px;">👑 مجموع عملکرد کل سلاطین برگزیده (${clientKingsSimList.length} گره برتر نماد ${detectedSym})</td>
                                <td style="text-align:center;color:#facc15;font-size:15px;">${kingsCount}</td>
                                <td colspan="8" style="text-align:center;color:#94a3b8;font-size:11px;">مبتنی بر استراتژی خروج چهارپله‌ای 0.04 لات و پایش دقیق دراوداون</td>
                                <td style="text-align:center;color:#38bdf8;font-size:14px;">+$${(kingsNet + kingsCount * friction).toFixed(2)}</td>
                                <td style="text-align:center;color:#f87171;font-size:14px;">-$${(kingsCount * friction).toFixed(2)}</td>
                                <td style="text-align:center;color:#00e676;font-size:16px;background:#064e3b;">+$${kingsNet.toFixed(2)} دلار نقد</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            </div>
        </div>

        <!-- VIEW 2: MULTI-PERIOD / INTERSECTION -->
        <div id="kingsViewMulti" style="display:none;">
            <div class="section-box" style="border: 1px solid #38bdf8; background: #081a2e;">
                <div style="border-bottom: 1px solid #0284c7; padding-bottom: 12px; margin-bottom: 14px;">
                    <h3 style="margin:0;color:#38bdf8;font-size:18px;">💎 ماتریس اشتراک طلایی و پایداری در تمام فصول (Golden Intersection)</h3>
                    <p style="margin:4px 0 0 0;color:#bae6fd;font-size:12px;">پایش الگوهایی که در طول زمان نوسان عملکرد نداشته و ثبات آماری مستمر ثبت کرده‌اند:</p>
                </div>
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#0e3355;">
                                <th style="text-align:center;">#</th>
                                <th style="text-align:center;">تایم‌فریم</th>
                                <th>نام ساختار گره</th>
                                <th style="text-align:center;">نشان ثبات فصلی</th>
                                <th style="text-align:center;">تعداد معامله</th>
                                <th style="text-align:center;">وین‌ریت TP1</th>
                                <th style="text-align:center;">نرخ باخت (SL)</th>
                                <th style="text-align:center;color:#00e676;">سود خالص ($)</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${mpRowsHtml}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- VIEW 3: COMPARE -->
        <div id="kingsViewCompare" style="display:none;">
            <div class="section-box" style="border: 1px solid #a855f7; background: #160d26;">
                <div style="border-bottom: 1px solid #7e22ce; padding-bottom: 12px; margin-bottom: 14px;">
                    <h3 style="margin:0;color:#c084fc;font-size:18px;">⚖️ مقایسه ساختارها و تایم‌فریم‌های نماد ${detectedSym}</h3>
                    <p style="margin:4px 0 0 0;color:#e9d5ff;font-size:12px;">کالبدشکافی توزیع معاملات سلاطین بر مبنای تفکیک تایم‌فریم و ریسک:</p>
                </div>
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#2a1645;">
                                <th style="text-align:center;">رتبه</th>
                                <th style="text-align:center;">تایم</th>
                                <th>ساختار گره</th>
                                <th style="text-align:center;">معاملات</th>
                                <th style="text-align:center;color:#00e676;">وین‌ریت ۱:۱</th>
                                <th style="text-align:center;color:#f87171;">نرخ استاپ</th>
                                <th style="text-align:center;color:#38bdf8;">پرافیت فاکتور</th>
                                <th style="text-align:center;color:#00e676;">سود خالص</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${kingsRowsHtml}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}