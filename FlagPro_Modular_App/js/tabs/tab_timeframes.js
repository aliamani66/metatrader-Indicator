window.sortDirections = window.sortDirections || { 'data-score': true };

function sortTableByAttr(tableId, attrName, isNumeric, defaultDesc, btnElem) {
            let table = document.getElementById(tableId);
            if (!table) return;
            let tbody = table.querySelector('tbody');
            if (!tbody) return;
            let rows = Array.from(tbody.querySelectorAll('tr.tf-row, tr.tf-role-row'));

            let sortDirs = window.sortDirections || {};
            let isCurrentDesc = sortDirs[attrName];
            let newDesc = (isCurrentDesc === undefined) ? defaultDesc : !isCurrentDesc;
            sortDirs[attrName] = newDesc;
            window.sortDirections = sortDirs;

            let headers = table.querySelectorAll('th');
            headers.forEach(h => {
                let icon = h.querySelector('.sort-icon');
                if (icon) icon.textContent = ' ⬍';
                h.style.background = '';
            });

            let activeTh = table.querySelector(`th[data-sort="${attrName}"]`);
            if (activeTh) {
                let icon = activeTh.querySelector('.sort-icon');
                if (icon) icon.textContent = newDesc ? ' ▼' : ' ▲';
                activeTh.style.background = '#1e293b';
            }

            if (btnElem) {
                let p = btnElem.parentElement;
                if (p) {
                    p.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                    btnElem.classList.add('active');
                }
            }

            rows.sort((a, b) => {
                let valA = a.getAttribute(attrName) || '';
                let valB = b.getAttribute(attrName) || '';

                if (isNumeric) {
                    let numA = parseFloat(valA) || 0.0;
                    let numB = parseFloat(valB) || 0.0;
                    if (numA !== numB) {
                        return newDesc ? (numB - numA) : (numA - numB);
                    }
                    let evA = parseFloat(a.getAttribute('data-score')) || 0.0;
                    let evB = parseFloat(b.getAttribute('data-score')) || 0.0;
                    return evB - evA;
                } else {
                    let res = valA.localeCompare(valB);
                    if (res !== 0) return newDesc ? -res : res;
                    let evA = parseFloat(a.getAttribute('data-score')) || 0.0;
                    let evB = parseFloat(b.getAttribute('data-score')) || 0.0;
                    return evB - evA;
                }
            });

            rows.forEach((r, i) => {
                let firstTd = r.querySelector('td:first-child');
                if (firstTd && firstTd.textContent.trim().startsWith('#')) {
                    firstTd.textContent = '#' + (i + 1);
                }
                tbody.appendChild(r);
            });
        }

        function filterTF(tf, btnElem) {
            let btns = document.querySelectorAll('.tf-btn');
            btns.forEach(b => b.classList.remove('active'));
            if (btnElem) {
                btnElem.classList.add('active');
            } else if (typeof event !== 'undefined' && event && (event.currentTarget || event.target)) {
                (event.currentTarget || event.target).classList.add('active');
            }

            let rows = document.querySelectorAll('.tf-row, .tf-role-row');
            rows.forEach(r => {
                if(tf === 'ALL' || r.getAttribute('data-tf') === tf) {
                    r.style.display = '';
                } else {
                    r.style.display = 'none';
                }
            });
        }

function generateClientTimeframesHTML(detectedSym, rawTrades, clientKingsSimList, friction) {
    let sData = (window.ALL_SYMBOLS_DATA && window.ALL_SYMBOLS_DATA[detectedSym]) || {};

    // 1. Box-to-Entry Latency Stats
    let latAll = (sData.latency_all && sData.latency_all.cnt > 0) ? sData.latency_all : calcLatencyStatsFromTrades(rawTrades);
    let latTfs = sData.latency_tfs || {};

    let tfMapKings = {};
    let tfMapRaw = {};

    rawTrades.forEach(t => {
        let tf = t.tf || 'M1';
        if (!tfMapRaw[tf]) {
            tfMapRaw[tf] = { count: 0, w1: 0, w2: 0, w3: 0, w4: 0, sl: 0, net: 0, trades: [] };
        }
        let r = tfMapRaw[tf];
        r.count++;
        r.trades.push(t);
        let hr = t.hr !== undefined ? t.hr : (t.HitTargetRatio !== undefined ? parseInt(t.HitTargetRatio) : 0);
        let pts = t.pts || (t.RiskPoints !== undefined ? parseFloat(t.RiskPoints) : 0);
        if (hr === 0) { r.sl++; r.net += (-pts * 0.04 - friction); }
        else {
            let pnl = -friction;
            if (hr >= 1) { r.w1++; pnl += pts * 0.01 * 1.0; }
            if (hr >= 2) { r.w2++; pnl += pts * 0.01 * 2.0; }
            if (hr >= 3) { r.w3++; pnl += pts * 0.01 * 3.0; }
            if (hr >= 4) { r.w4++; pnl += pts * 0.01 * 4.0; }
            r.net += pnl;
        }
    });

    let totKingsW1 = 0, totKingsW2 = 0, totKingsW3 = 0, totKingsW4 = 0, totKingsSL = 0;
    clientKingsSimList.forEach(k => {
        let tf = k.tf || 'M1';
        if (!tfMapKings[tf]) {
            tfMapKings[tf] = { count: 0, grossWin: 0, friction: 0, net: 0, w1: 0, w2: 0, w3: 0, w4: 0, sl: 0 };
        }
        let g = tfMapKings[tf];
        let k_w1 = k.w1 !== undefined ? k.w1 : Math.round(k.cnt * (k.w1_p / 100));
        let k_w2 = k.w2 !== undefined ? k.w2 : Math.round(k_w1 * 0.65);
        let k_w3 = k.w3 !== undefined ? k.w3 : Math.round(k_w1 * 0.45);
        let k_w4 = k.w4 !== undefined ? k.w4 : Math.round(k_w1 * 0.35);
        let k_sl = k.sl !== undefined ? k.sl : (k.sl_cnt !== undefined ? k.sl_cnt : 0);

        g.count += k.cnt;
        g.net += k.net;
        g.friction += k.cnt * friction;
        g.grossWin += (k.net + k.cnt * friction);
        g.sl += k_sl;
        g.w1 += k_w1;
        g.w2 += k_w2;
        g.w3 += k_w3;
        g.w4 += k_w4;

        totKingsW1 += k_w1;
        totKingsW2 += k_w2;
        totKingsW3 += k_w3;
        totKingsW4 += k_w4;
        totKingsSL += k_sl;
    });

    let tfKeys = Object.keys(tfMapRaw).sort();

    // Ensure latency stats per TF are populated
    tfKeys.forEach(tf => {
        if (!latTfs[tf] || !latTfs[tf].cnt) {
            latTfs[tf] = calcLatencyStatsFromTrades(tfMapRaw[tf].trades);
        }
    });

    // Build Strategy Guidance Box bullet points dynamically
    let guidanceBullets = [];
    tfKeys.forEach(tf => {
        let l = latTfs[tf];
        if (l && l.cnt > 0) {
            if (tf === 'M1') {
                guidanceBullets.push(`• <b>در تایم M1:</b> میانگین زمان تاچ ورود <b>${l.avg_fmt}</b> (میانه: ${l.med_fmt}) است و ۹۰٪ معاملات در کمتر از <b>${l.p90_fmt}</b> وارد می‌شوند. اگر اردری بیش از ۱ ساعت فعال نشد، لغو آن کاملاً امن و منطقی است.`);
            } else if (tf === 'M5') {
                guidanceBullets.push(`• <b>در تایم M5:</b> میانگین انتظار ورود <b>${l.avg_fmt}</b> (میانه: ${l.med_fmt}) است و تا ۳ ساعت ساختار معتبر باقی می‌ماند.`);
            } else if (tf === 'M15') {
                guidanceBullets.push(`• <b>در تایم M15:</b> ستاپ‌ها سوئینگی هستند و میانگین انتظار تاچ اردر <b>${l.avg_fmt}</b> است.`);
            } else {
                guidanceBullets.push(`• <b>در تایم ${tf}:</b> میانگین انتظار ورود <b>${l.avg_fmt}</b> (میانه: ${l.med_fmt}) و ۹۰٪ زیر <b>${l.p90_fmt}</b> فعال می‌شوند.`);
            }
        }
    });
    if (guidanceBullets.length === 0) {
        guidanceBullets.push(`• میانگین کل زمان تاچ ورود به معامله در نماد <b>${detectedSym}</b> برابر با <b>${latAll.avg_fmt}</b> است.`);
    }

    let kingsRows = tfKeys.filter(tf => tfMapKings[tf]).map(tf => {
        let g = tfMapKings[tf];
        let w1_p = g.count > 0 ? (g.w1 / g.count * 100).toFixed(1) : '0.0';
        let w2_p = g.count > 0 ? (g.w2 / g.count * 100).toFixed(1) : '0.0';
        let w3_p = g.count > 0 ? (g.w3 / g.count * 100).toFixed(1) : '0.0';
        let w4_p = g.count > 0 ? (g.w4 / g.count * 100).toFixed(1) : '0.0';
        let sl_p = g.count > 0 ? (g.sl / g.count * 100).toFixed(1) : '0.0';
        let tfLat = latTfs[tf] || { avg_short: '-', min_short: '-', max_short: '-' };
        return `
            <tr>
                <td style="color:#38bdf8;font-weight:bold;font-size:14px;">${tf}</td>
                <td style="text-align:center;font-weight:bold;">${g.count.toLocaleString()} معامله</td>
                <td style="text-align:center;color:#00e676;font-weight:bold;">${w1_p}%</td>
                <td style="text-align:center;color:#00e676;font-weight:bold;">${w2_p}%</td>
                <td style="text-align:center;color:#38bdf8;">${w3_p}%</td>
                <td style="text-align:center;color:#c084fc;">${w4_p}%</td>
                <td style="text-align:center;color:#ef4444;font-weight:bold;">${sl_p}%</td>
                <td style="text-align:center;color:#38bdf8;font-weight:bold;">${g.grossWin >= 0 ? '+' : ''}$${g.grossWin.toFixed(2)}</td>
                <td style="text-align:center;color:#f87171;font-weight:bold;">-$${g.friction.toFixed(2)}</td>
                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;background:#064e3b22;">${g.net >= 0 ? '+' : ''}$${g.net.toFixed(2)} دلار</td>
                <td style="text-align:center;color:#38bdf8;font-weight:bold;">${tfLat.avg_short || '-'}</td>
                <td style="text-align:center;color:#94a3b8;font-size:11px;">${tfLat.min_short || '-'} ~ ${tfLat.max_short || '-'}</td>
            </tr>
        `;
    }).join('');

    let totKingsCount = clientKingsSimList.reduce((s, k) => s + k.cnt, 0);
    let totKingsNet = clientKingsSimList.reduce((s, k) => s + k.net, 0);
    let totKingsFriction = totKingsCount * friction;
    let totKingsGross = totKingsNet + totKingsFriction;

    let totW1_p = totKingsCount > 0 ? (totKingsW1 / totKingsCount * 100).toFixed(1) : '0.0';
    let totW2_p = totKingsCount > 0 ? (totKingsW2 / totKingsCount * 100).toFixed(1) : '0.0';
    let totW3_p = totKingsCount > 0 ? (totKingsW3 / totKingsCount * 100).toFixed(1) : '0.0';
    let totW4_p = totKingsCount > 0 ? (totKingsW4 / totKingsCount * 100).toFixed(1) : '0.0';
    let totSL_p = totKingsCount > 0 ? (totKingsSL / totKingsCount * 100).toFixed(1) : '0.0';

    let rawRows = tfKeys.map(tf => {
        let r = tfMapRaw[tf];
        let w1_p = r.count > 0 ? (r.w1 / r.count * 100).toFixed(1) : '0.0';
        let w2_p = r.count > 0 ? (r.w2 / r.count * 100).toFixed(1) : '0.0';
        let w3_p = r.count > 0 ? (r.w3 / r.count * 100).toFixed(1) : '0.0';
        let w4_p = r.count > 0 ? (r.w4 / r.count * 100).toFixed(1) : '0.0';
        let sl_p = r.count > 0 ? (r.sl / r.count * 100).toFixed(1) : '0.0';
        let netColor = r.net >= 0 ? '#00e676' : '#ef4444';
        let tfLat = latTfs[tf] || { avg_short: '-', min_short: '-', max_short: '-' };
        return `
            <tr style="opacity:0.85;">
                <td style="color:#94a3b8;font-weight:bold;">${tf} (خام)</td>
                <td style="text-align:center;">${r.count.toLocaleString()} معامله</td>
                <td style="text-align:center;">${w1_p}%</td>
                <td style="text-align:center;">${w2_p}%</td>
                <td style="text-align:center;">${w3_p}%</td>
                <td style="text-align:center;">${w4_p}%</td>
                <td style="text-align:center;color:#ef4444;">${sl_p}%</td>
                <td style="text-align:center;color:${netColor};font-weight:bold;">${r.net >= 0 ? '+' : ''}$${r.net.toFixed(2)} دلار</td>
                <td style="text-align:center;color:#38bdf8;">${tfLat.avg_short || '-'}</td>
                <td style="text-align:center;color:#94a3b8;font-size:11px;">${tfLat.min_short || '-'} ~ ${tfLat.max_short || '-'}</td>
            </tr>
        `;
    }).join('');

    let totRawNet = Object.values(tfMapRaw).reduce((s, r) => s + r.net, 0);
    let totRawCount = rawTrades.length;

    // Group all closed rawTrades by (tf, role) for the Detailed Entity Table
    let tfRoleMap = {};
    rawTrades.forEach(t => {
        let tf = t.tf || 'M1';
        let role = t.role || 'Unknown';
        let key = tf + '|' + role;
        if (!tfRoleMap[key]) {
            tfRoleMap[key] = { tf: tf, role: role, trades: [] };
        }
        tfRoleMap[key].trades.push(t);
    });

    let computedTfRoles = [];
    for (let key in tfRoleMap) {
        let item = tfRoleMap[key];
        let m = calc7PillarKingMetrics(item.trades, item.tf, item.role, friction);
        if (m) computedTfRoles.push(m);
    }

    // Sort by King Score descending
    computedTfRoles.sort((a, b) => (b.score !== a.score ? b.score - a.score : b.cnt - a.cnt));

    let tfRoleRows = computedTfRoles.map((item, idx) => {
        let tf = item.tf;
        let role = item.role;
        let cnt = item.cnt;
        let w1_p = item.w1_p;
        let w2_p = item.w2_p;
        let w3_p = item.w3_p;
        let w4_p = item.w4_p;
        let sl_p = item.sl_p;
        let score = item.score;
        let net = item.net;
        let is_king = clientKingsSimList.some(k => k.role === role && k.tf === tf);
        let k_tag = is_king ? "👑 سلطان" : "سایر";
        let k_color = is_king ? "#facc15" : "#94a3b8";
        let net_col = net >= 0 ? "#00e676" : "#ef4444";

        let pf = item.pf;
        let pf_str = pf >= 90 ? "<span style='color:#00e676;'>MAX</span>" : pf.toFixed(2);
        let max_dd = item.max_dd;
        let dd_str = max_dd === 0 ? "<span style='color:#00e676;'>$0.00</span>" : (max_dd <= 25 ? `<span style='color:#fbbf24;'>$${max_dd.toFixed(2)}</span>` : `<span style='color:#f87171;'>$${max_dd.toFixed(2)}</span>`);
        let ret_dd = item.ret_dd;
        let ret_str = `<span style='color:#facc15;font-weight:bold;'>${ret_dd.toFixed(1)}x</span>`;

        let badge_html = "";
        if (item.is_perfect) {
            badge_html += " <span style='background:#064e3b;color:#34d399;font-size:10px;padding:2px 5px;border-radius:4px;border:1px solid #059669;'>💎 ۱۰۰٪ قطعی</span>";
        } else if (item.is_runner) {
            badge_html += " <span style='background:#312e81;color:#a5b4fc;font-size:10px;padding:2px 5px;border-radius:4px;border:1px solid #4338ca;'>🚀 دونده</span>";
        }

        let score_html = "";
        if (score >= 1000) {
            score_html = `<span style='color:#facc15;font-weight:bold;font-size:15px;'>${score.toFixed(1)} 👑</span>`;
        } else if (score >= 500) {
            score_html = `<span style='color:#38bdf8;font-weight:bold;font-size:14px;'>${score.toFixed(1)} ⭐</span>`;
        } else if (score >= 250) {
            score_html = `<span style='color:#00e676;font-weight:bold;font-size:13px;'>${score.toFixed(1)}</span>`;
        } else {
            score_html = `<span style='color:#ef4444;font-size:13px;'>${score.toFixed(1)}</span>`;
        }

        return `
        <tr class="tf-row tf-role-row" data-tf="${tf}" data-role="${role}" data-king="${is_king ? 1 : 0}" data-cnt="${cnt}" data-w1="${w1_p.toFixed(2)}" data-w2="${w2_p.toFixed(2)}" data-w3="${w3_p.toFixed(2)}" data-w4="${w4_p.toFixed(2)}" data-sl="${sl_p.toFixed(2)}" data-net="${net.toFixed(2)}" data-pf="${pf.toFixed(2)}" data-dd="${max_dd.toFixed(2)}" data-retdd="${ret_dd.toFixed(2)}" data-score="${score.toFixed(2)}">
            <td style="text-align:center;font-weight:bold;color:#94a3b8;">#${idx + 1}</td>
            <td style="color:#38bdf8;font-weight:bold;text-align:center;">${tf}</td>
            <td style="color:${k_color};font-weight:bold;">${role}${badge_html}</td>
            <td style="text-align:center;"><span style="background:${is_king ? '#854d0e' : '#1e293b'};color:${k_color};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">${k_tag}</span></td>
            <td style="text-align:center;font-weight:bold;">${cnt}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">${w1_p.toFixed(1)}%</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">${w2_p.toFixed(1)}%</td>
            <td style="text-align:center;color:#38bdf8;">${w3_p.toFixed(1)}%</td>
            <td style="text-align:center;color:#c084fc;">${w4_p.toFixed(1)}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">${sl_p.toFixed(1)}%</td>
            <td style="text-align:center;color:${net_col};font-weight:bold;font-size:14px;background:#064e3b18;">${net >= 0 ? '+' : ''}$${net.toFixed(2)}</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">${pf_str}</td>
            <td style="text-align:center;font-weight:bold;">${dd_str}</td>
            <td style="text-align:center;font-weight:bold;">${ret_str}</td>
            <td style="text-align:center;">${score_html}</td>
        </tr>
        `;
    }).join('');

    let tfCountMap = {};
    computedTfRoles.forEach(it => {
        tfCountMap[it.tf] = (tfCountMap[it.tf] || 0) + 1;
    });

    let tfButtonsHtml = `<button class="sort-btn active tf-btn" onclick="filterTF('ALL', this)">همه تایم‌ها</button>`;
    let tfColors = { 'M1': '#38bdf8', 'M5': '#00e676', 'M15': '#f59e0b', 'M30': '#c084fc', 'H1': '#ec4899' };
    let tfIcons = { 'M1': '⚡', 'M5': '🌟', 'M15': '🕒', 'M30': '⏱️', 'H1': '⏳' };
    tfKeys.forEach(tf => {
        let col = tfColors[tf] || '#38bdf8';
        let icon = tfIcons[tf] || '🕒';
        let count = tfCountMap[tf] || 0;
        tfButtonsHtml += `<button class="sort-btn tf-btn" style="border-color:${col};color:${col};" onclick="filterTF('${tf}', this)">${icon} ${tf} (${count})</button>`;
    });

    return `
        <!-- ⏳ BOX-TO-ENTRY LATENCY & PULLBACK SPEED INTELLIGENCE -->
        <div class="section-box" style="border: 1px solid #0284c7; background: #081a2e; margin-bottom: 24px; padding: 18px 20px; border-radius: 10px;">
            <div style="border-bottom: 1px solid #1e3a8a; padding-bottom: 10px; margin-bottom: 14px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <div>
                    <h3 style="margin:0; color:#38bdf8; font-size:18px; display:flex; align-items:center; gap:8px;">
                        ⏱️ تحلیل سرعت پولبک و زمان انتظار ورود (Box-to-Entry Latency) - نماد <span style="color:#facc15;border-bottom:2px solid #facc15;padding-bottom:2px;">${detectedSym}</span>
                    </h3>
                    <p style="margin:4px 0 0 0; color:#93c5fd; font-size:12px;">
                        مدت زمان سپری‌شده از لحظه تشکیل باکس الگو تا لمس سطح اردر لیمیت و فعال‌سازی معامله (مبنای تعیین انقضای اردرهای لیمیت)
                    </p>
                </div>
                <span style="background:#0369a1; color:#e0f2fe; padding:4px 10px; border-radius:6px; font-size:12px; font-weight:bold;">
                    جامعه آماری: ${totRawCount.toLocaleString()} ستاپ فعال‌شده
                </span>
            </div>

            <!-- 4 Latency KPI Cards -->
            <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px; margin-bottom:16px;">
                <div class="kpi-card" style="border-color:#38bdf8; background:#0e2a47; padding:12px 14px;">
                    <div class="kpi-title" style="font-size:11.5px; color:#93c5fd;">⚡ حداقل زمان انتظار (سریع‌ترین پولبک)</div>
                    <div class="kpi-value" style="color:#38bdf8; font-size:22px;">${latAll.min_short || '-'}</div>
                    <div class="kpi-sub" style="color:#94a3b8;">${latAll.min_fmt || '-'}</div>
                </div>
                <div class="kpi-card" style="border-color:#00e676; background:#0a2c20; padding:12px 14px;">
                    <div class="kpi-title" style="font-size:11.5px; color:#86efac;">⏱️ میانگین زمان انتظار (Average Latency)</div>
                    <div class="kpi-value" style="color:#00e676; font-size:22px;">${latAll.avg_short || '-'}</div>
                    <div class="kpi-sub" style="color:#94a3b8;">${latAll.avg_fmt || '-'}</div>
                </div>
                <div class="kpi-card" style="border-color:#facc15; background:#292208; padding:12px 14px;">
                    <div class="kpi-title" style="font-size:11.5px; color:#fde047;">🎯 میانه انتظار (Median - نصف معاملات)</div>
                    <div class="kpi-value" style="color:#facc15; font-size:22px;">${latAll.med_short || '-'}</div>
                    <div class="kpi-sub" style="color:#94a3b8;">۵۰٪ معاملات زیر ${latAll.med_fmt || '-'} وارد شدند</div>
                </div>
                <div class="kpi-card" style="border-color:#c084fc; background:#231138; padding:12px 14px;">
                    <div class="kpi-title" style="font-size:11.5px; color:#d8b4fe;">🛡️ چارک ۹۰٪ (فعال‌سازی ۹۰٪ اردرها)</div>
                    <div class="kpi-value" style="color:#c084fc; font-size:22px;">${latAll.p90_short || '-'}</div>
                    <div class="kpi-sub" style="color:#94a3b8;">۹۰٪ اردرها زیر ${latAll.p90_fmt || '-'} فعال شدند</div>
                </div>
            </div>

            <!-- Practical Strategy Guidance Box -->
            <div style="background:#0f2238; border-right:4px solid #38bdf8; padding:12px 16px; border-radius:6px; font-size:12px; color:#cbd5e1; line-height:1.8;">
                <b style="color:#38bdf8;">💡 راهنمای عملی معاملاتی برای اردرهای لیمیت نماد ${detectedSym} (Limit Order Life Expectancy):</b><br/>
                ${guidanceBullets.join('<br/>')}
            </div>
        </div>

        <div class="section-box">
            <div style="border-bottom:1px solid #334155;padding-bottom:8px;margin-bottom:10px;">
                <h3 style="margin:0;color:#38bdf8;font-size:19px;">📊 تفکیک عملکرد تایم‌فریم‌ها در استراتژی سلاطین برگزیده (نماد ${detectedSym})</h3>
                <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">بررسی سودآوری واقعی معاملات سلاطین برگزیده (حجم پلکانی 0.04 با کسر اسپرد و کمیسیون):</p>
            </div>

            <!-- Primary: Golden Kings per Timeframe -->
            <div style="overflow-x:auto;margin-bottom:24px;">
                <table>
                    <thead>
                        <tr style="background:#0f172a;">
                            <th>تایم‌فریم (سلاطین برگزیده)</th>
                            <th style="text-align:center;">تعداد معامله</th>
                            <th style="text-align:center;">وین‌ریت TP 1:1</th>
                            <th style="text-align:center;">وین‌ریت TP 1:2</th>
                            <th style="text-align:center;">وین‌ریت TP 1:3</th>
                            <th style="text-align:center;">وین‌ریت TP 1:4</th>
                            <th style="text-align:center;">نرخ باخت (SL)</th>
                            <th style="text-align:center;color:#38bdf8;">سود ناخالص</th>
                            <th style="text-align:center;color:#f87171;">کل اصطکاک (اسپرد)</th>
                            <th style="text-align:center;color:#00e676;">💵 سود خالص واقعی</th>
                            <th style="text-align:center;color:#38bdf8;">⏱️ میانگین انتظار ورود</th>
                            <th style="text-align:center;color:#94a3b8;">⚡ کمترین ~ بیشترین انتظار</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${kingsRows}
                        <tr style="background:#1e293b;border-top:2px solid #38bdf8;">
                            <td style="color:#facc15;font-weight:bold;font-size:15px;">👑 مجموع کل سلاطین برگزیده</td>
                            <td style="text-align:center;font-weight:bold;color:#facc15;font-size:14px;">${totKingsCount.toLocaleString()} معامله</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">${totW1_p}%</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">${totW2_p}%</td>
                            <td style="text-align:center;color:#38bdf8;">${totW3_p}%</td>
                            <td style="text-align:center;color:#c084fc;">${totW4_p}%</td>
                            <td style="text-align:center;color:#ef4444;font-weight:bold;">${totSL_p}%</td>
                            <td style="text-align:center;color:#38bdf8;font-weight:bold;font-size:15px;">${totKingsGross >= 0 ? '+' : ''}$${totKingsGross.toFixed(2)}</td>
                            <td style="text-align:center;color:#f87171;font-weight:bold;font-size:15px;">-$${totKingsFriction.toFixed(2)}</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;font-size:16px;background:#064e3b;">${totKingsNet >= 0 ? '+' : ''}$${totKingsNet.toFixed(2)} دلار نقد</td>
                            <td style="text-align:center;color:#38bdf8;font-weight:bold;">${latAll.avg_short || '-'}</td>
                            <td style="text-align:center;color:#94a3b8;font-size:11px;">${latAll.min_short || '-'} ~ ${latAll.max_short || '-'}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Comparison Banner -->
            <div style="background:#1e1b4b;border:1px solid #4338ca;border-radius:8px;padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
                <div>
                    <span style="color:#a5b4fc;font-weight:bold;font-size:13px;">💡 تفاوت معاملات سلاطین با کل بازار خام چارت:</span>
                    <div style="color:#cbd5e1;font-size:11px;margin-top:2px;">اگر کل ${totRawCount.toLocaleString()} معامله خام چارت بدون فیلتر معامله می‌شد، $${totRawNet.toFixed(2)} سود/زیان تولید می‌شد؛ اما سلاطین منتخب با فیلتر هوشمند آن را به +$${totKingsNet.toFixed(2)} سود خالص رسانده‌اند!</div>
                </div>
                <button class="sort-btn" style="border-color:#a5b4fc;color:#a5b4fc;" onclick="let el = document.getElementById('rawTfTable'); el.style.display = el.style.display==='none'?'':'none';">👁️ مشاهده جدول کل دیتای خام چارت</button>
            </div>

            <!-- Collapsible Raw Table -->
            <div id="rawTfTable" style="display:none;overflow-x:auto;margin-bottom:24px;border:1px dashed #475569;border-radius:8px;padding:10px;">
                <div style="color:#94a3b8;font-size:12px;margin-bottom:6px;font-weight:bold;">⚠️ عملکرد کل ${totRawCount.toLocaleString()} معامله خام چارت بدون گزینش سلاطین:</div>
                <table>
                    <thead>
                        <tr style="background:#1e293b;">
                            <th>تایم‌فریم خام</th>
                            <th style="text-align:center;">کل معاملات</th>
                            <th style="text-align:center;">وین‌ریت 1:1</th>
                            <th style="text-align:center;">وین‌ریت 1:2</th>
                            <th style="text-align:center;">وین‌ریت 1:3</th>
                            <th style="text-align:center;">وین‌ریت 1:4</th>
                            <th style="text-align:center;">نرخ باخت</th>
                            <th style="text-align:center;">سود/زیان کل خام</th>
                            <th style="text-align:center;color:#38bdf8;">میانگین انتظار ورود</th>
                            <th style="text-align:center;color:#94a3b8;">کمترین ~ بیشترین انتظار</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rawRows}
                    </tbody>
                </table>
            </div>

            <!-- Detailed Entity Breakdown by Timeframe -->
            <div style="display:flex;justify-content:space-between;align-items:center;border-top:1px solid #334155;padding-top:14px;flex-wrap:gap;gap:10px;">
                <div>
                    <h4 style="margin:0;color:#f8fafc;font-size:15px;">تفکیک جزئی گره‌ها در هر تایم‌فریم:</h4>
                </div>
                <div>
                    ${tfButtonsHtml}
                </div>
            </div>

            <!-- Formula Explainer Box -->
            <div style="font-size:12px;color:#94a3b8;margin:10px 0;background:#0f172a;padding:10px 14px;border-radius:8px;border-right:4px solid #facc15;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                <div>
                    <b style="color:#facc15;">🏛️ شاخص ۷ ستونه هج‌فاندی سلطان (7-Pillar Institutional King Score):</b>
                    <span style="direction:ltr;display:inline-block;font-family:monospace;background:#1e293b;padding:2px 8px;border-radius:4px;color:#38bdf8;margin:0 6px;">Score = 🛡️خلوص(۵۰۰) + 🎯وین‌ریت ۱:۲(۴۰۰) + ⚡عمق تارگت‌ها + 💰راندمان ترید + 📊اعتبار + ⚖️پرافیت فاکتور(۱۰۰) + 🛡️کنترل افت و ریکاوری(۱۰۰)</span>
                </div>
                <div>
                    <span style="background:#064e3b;color:#34d399;font-size:11px;padding:2px 6px;border-radius:4px;border:1px solid #059669;margin-left:4px;">👑 ۱۰۰٪ وین‌ریت (+۵۰۰ قطعی)</span>
                    <span style="background:#1e3a8a;color:#93c5fd;font-size:11px;padding:2px 6px;border-radius:4px;border:1px solid #3b82f6;">⚖️ کنترل دراوداون و پرافیت فاکتور</span>
                </div>
            </div>

            <!-- Quick Combined Sorting Buttons -->
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:12px 0;background:#0f172a;padding:8px 12px;border-radius:8px;border:1px solid #334155;">
                <span style="color:#94a3b8;font-size:12px;font-weight:bold;">🔀 دکمه‌های سورت هوشمند و ترکیبی:</span>
                <button class="sort-btn active" id="btnSortScore" onclick="sortTableByAttr('tfTable', 'data-score', true, true, this)">👑 بیشترین امتیاز سلطان (Score)</button>
                <button class="sort-btn" id="btnSortNet" style="border-color:#00e676;color:#00e676;" onclick="sortTableByAttr('tfTable', 'data-net', true, true, this)">💵 بیشترین سود خالص دلاری</button>
                <button class="sort-btn" style="border-color:#38bdf8;color:#38bdf8;" onclick="sortTableByAttr('tfTable', 'data-pf', true, true, this)">⚖️ بیشترین پرافیت فاکتور (PF)</button>
                <button class="sort-btn" style="border-color:#f87171;color:#f87171;" onclick="sortTableByAttr('tfTable', 'data-dd', true, false, this)">🛡️ کمترین افت (Max DD)</button>
                <button class="sort-btn" style="border-color:#facc15;color:#facc15;" onclick="sortTableByAttr('tfTable', 'data-retdd', true, true, this)">🚀 نسبت سود به افت (Ret/DD)</button>
                <button class="sort-btn" onclick="sortTableByAttr('tfTable', 'data-w4', true, true, this)">🚀 بیشترین تارگت دونده (TP4)</button>
                <button class="sort-btn" onclick="sortTableByAttr('tfTable', 'data-w2', true, true, this)">🎯 بیشترین وین‌ریت ۱:۲</button>
                <button class="sort-btn" onclick="sortTableByAttr('tfTable', 'data-w1', true, true, this)">🥇 بیشترین وین‌ریت ۱:۱</button>
                <button class="sort-btn" onclick="sortTableByAttr('tfTable', 'data-cnt', true, true, this)">📦 بیشترین تعداد معامله</button>
                <button class="sort-btn" onclick="sortTableByAttr('tfTable', 'data-sl', true, false, this)">🛡️ کمترین باخت (SL)</button>
                <button class="sort-btn" onclick="sortTableByAttr('tfTable', 'data-tf', false, false, this)">🕒 بر اساس تایم‌فریم</button>
            </div>

            <div style="overflow-x:auto;margin-top:6px;">
                <table id="tfTable">
                    <thead>
                        <tr>
                            <th style="text-align:center;width:40px;">#</th>
                            <th onclick="sortTableByAttr('tfTable', 'data-tf', false, false)" data-sort="data-tf" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی صعودی/نزولی">تایم‌فریم <span class="sort-icon">⬍</span></th>
                            <th onclick="sortTableByAttr('tfTable', 'data-role', false, false)" data-sort="data-role" style="cursor:pointer;" title="کلیک برای مرتب‌سازی">موجودیت باکس / سواپ <span class="sort-icon">⬍</span></th>
                            <th onclick="sortTableByAttr('tfTable', 'data-king', true, true)" data-sort="data-king" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی سلاطین">وضعیت <span class="sort-icon">⬍</span></th>
                            <th onclick="sortTableByAttr('tfTable', 'data-cnt', true, true)" data-sort="data-cnt" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی">تعداد معامله <span class="sort-icon">⬍</span></th>
                            <th onclick="sortTableByAttr('tfTable', 'data-w1', true, true)" data-sort="data-w1" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی">TP 1:1 <span class="sort-icon">⬍</span></th>
                            <th onclick="sortTableByAttr('tfTable', 'data-w2', true, true)" data-sort="data-w2" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی">TP 1:2 <span class="sort-icon">⬍</span></th>
                            <th onclick="sortTableByAttr('tfTable', 'data-w3', true, true)" data-sort="data-w3" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی">TP 1:3 <span class="sort-icon">⬍</span></th>
                            <th onclick="sortTableByAttr('tfTable', 'data-w4', true, true)" data-sort="data-w4" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی">TP 1:4 <span class="sort-icon">⬍</span></th>
                            <th onclick="sortTableByAttr('tfTable', 'data-sl', true, false)" data-sort="data-sl" style="cursor:pointer;text-align:center;" title="کلیک برای مرتب‌سازی">باخت (SL) <span class="sort-icon">⬍</span></th>
                            <th onclick="sortTableByAttr('tfTable', 'data-net', true, true)" data-sort="data-net" style="cursor:pointer;text-align:center;color:#00e676;background:#064e3b33;" title="کلیک برای مرتب‌سازی بر اساس سود خالص دلاری">💵 سود خالص دلاری <span class="sort-icon">⬍</span></th>
                            <th onclick="sortTableByAttr('tfTable', 'data-pf', true, true)" data-sort="data-pf" style="cursor:pointer;text-align:center;color:#38bdf8;" title="کلیک برای مرتب‌سازی بر اساس Profit Factor">⚖️ PF <span class="sort-icon">⬍</span></th>
                            <th onclick="sortTableByAttr('tfTable', 'data-dd', true, false)" data-sort="data-dd" style="cursor:pointer;text-align:center;color:#f87171;" title="کلیک برای مرتب‌سازی بر اساس کمترین افت سرمایه (Max DD)">🛡️ Max DD <span class="sort-icon">⬍</span></th>
                            <th onclick="sortTableByAttr('tfTable', 'data-retdd', true, true)" data-sort="data-retdd" style="cursor:pointer;text-align:center;color:#facc15;" title="کلیک برای مرتب‌سازی بر اساس Recovery Factor (سود به افت)">🚀 Ret/DD <span class="sort-icon">⬍</span></th>
                            <th onclick="sortTableByAttr('tfTable', 'data-score', true, true)" data-sort="data-score" style="cursor:pointer;text-align:center;color:#facc15;background:#1e293b;" title="مرتب‌سازی شده بر مبنای فرمول شاخص سلطان">امتیاز سلطان (Score) <span class="sort-icon">▼</span></th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tfRoleRows}
                    </tbody>
                </table>
            </div>
    `;
}