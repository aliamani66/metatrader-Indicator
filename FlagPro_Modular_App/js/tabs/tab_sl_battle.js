/**
 * FlagPro - Stop Loss Matrix Battle Engine & Renderer
 * Pits all 4 Stop Loss methodologies head-to-head on the active symbol dataset.
 */

function renderSLBattleTab() {
    if (!window.ALL_SYMBOLS_DATA || typeof currentActiveSymbol === 'undefined') return;
    let sData = window.ALL_SYMBOLS_DATA[currentActiveSymbol];
    if (!sData) return;

    let matrix = sData.sl_battle_matrix;
    let trades = sData.trades_sim_list || [];

    // If precalculated matrix not available or empty, calculate dynamically
    if (!matrix || Object.keys(matrix).length === 0) {
        matrix = {};
        for (let sm = 0; sm < 4; sm++) {
            let sm_bal = 100.0, sm_peak = 100.0, sm_max_dd = 0.0;
            let sm_wins = 0, sm_losses = 0, sm_gp = 0.0, sm_gl = 0.0, sm_tot = 0, sm_pts_sum = 0.0;
            let sm_curve = [];

            for (let t of trades) {
                let m_info = (t.modes && t.modes[sm]) ? t.modes[sm] : null;
                let m_p = m_info ? m_info.p : t.p;
                let m_hr = m_info ? m_info.hr : t.hr;
                let m_pts = m_info ? m_info.pts : t.pts;

                sm_tot++;
                sm_pts_sum += m_pts;
                sm_bal += m_p;
                if (sm_bal > sm_peak) sm_peak = sm_bal;
                let sm_dd = sm_peak - sm_bal;
                if (sm_dd > sm_max_dd) sm_max_dd = sm_dd;

                if (m_p > 0) {
                    sm_wins++; sm_gp += m_p;
                } else {
                    sm_losses++; sm_gl += Math.abs(m_p);
                }
                sm_curve.push(Math.round(sm_bal * 100) / 100);
            }

            let sm_pf = sm_gl > 0 ? (sm_gp / sm_gl) : 99.0;
            let sm_wr = sm_tot > 0 ? (sm_wins / sm_tot * 100.0) : 0.0;
            let sm_avg_pts = sm_tot > 0 ? (sm_pts_sum / sm_tot) : 0.0;

            matrix[sm] = {
                name: ['لبه باکس + بافر ثابت (Fixed)', 'لبه باکس + بافر ATR (پیشنهادی ⭐)', 'ای‌تی‌آر خالص ولاتیلیتی (Pure ATR)', 'بافر درصدی الگو (Adaptive)'][sm],
                key: ['fixed', 'atr_buf', 'pure_atr', 'box_pct'][sm],
                total: sm_tot,
                wins: sm_wins,
                losses: sm_losses,
                wr: Math.round(sm_wr * 10) / 10,
                net: Math.round((sm_bal - 100.0) * 100) / 100,
                final_bal: Math.round(sm_bal * 100) / 100,
                max_dd: Math.round(sm_max_dd * 100) / 100,
                pf: Math.round(sm_pf * 100) / 100,
                avg_pts: Math.round(sm_avg_pts * 10) / 10,
                equity_curve: sm_curve
            };
        }
    }

    // Determine winning mode based on composite score: PF * WR / MaxDD
    let bestMode = 0;
    let bestScore = -999999;
    for (let sm = 0; sm < 4; sm++) {
        let m = matrix[sm];
        if (!m) continue;
        let score = (m.pf || 1.0) * (m.wr || 1.0) * Math.max(1, m.net) / Math.max(10, m.max_dd);
        if (score > bestScore) {
            bestScore = score;
            bestMode = sm;
        }
    }

    // 1. Render 4 Hero Comparison Cards
    let cardsContainer = document.getElementById('slBattleCardsGrid');
    if (cardsContainer) {
        let colors = ['#38bdf8', '#10b981', '#c084fc', '#facc15'];
        let badges = ['کلاسیک', 'پیشنهاد طلایی ⭐', 'ولاتیلیتی', 'تطبیقی'];
        let htmlCards = '';

        for (let sm = 0; sm < 4; sm++) {
            let m = matrix[sm] || {};
            let isWinner = (sm === bestMode);
            let borderStyle = isWinner ? '2px solid #facc15; box-shadow:0 0 20px rgba(250,204,21,0.25);' : `1px solid ${colors[sm]}44;`;
            let winnerBadge = isWinner ? `<span style="background:linear-gradient(135deg, #eab308, #ca8a04);color:#000;font-weight:900;font-size:10px;padding:3px 8px;border-radius:12px;box-shadow:0 2px 8px rgba(234,179,8,0.4);">👑 برنده قطعی این نماد</span>` : '';

            htmlCards += `
                <div style="background:#091a2e;border-radius:10px;padding:16px;${borderStyle}position:relative;display:flex;flex-direction:column;justify-content:space-between;transition:transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='none'">
                    <div>
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                            <span style="font-size:11px;color:${colors[sm]};background:${colors[sm]}18;padding:2px 8px;border-radius:6px;border:1px solid ${colors[sm]}44;font-weight:bold;">${badges[sm]}</span>
                            ${winnerBadge}
                        </div>
                        <div style="font-size:13.5px;font-weight:bold;color:#f8fafc;margin-bottom:12px;">${m.name || ''}</div>
                        
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;">
                            <div style="background:#061324;padding:8px 10px;border-radius:6px;border:1px solid #1e3a5f;">
                                <div style="font-size:10.5px;color:#94a3b8;">سود خالص (Net PnL):</div>
                                <div style="font-size:16px;font-weight:900;color:${(m.net || 0) >= 0 ? '#00e676' : '#ef4444'};margin-top:2px;">
                                    ${(m.net || 0) >= 0 ? '+' : ''}$${(m.net || 0).toFixed(2)}
                                </div>
                            </div>
                            <div style="background:#061324;padding:8px 10px;border-radius:6px;border:1px solid #1e3a5f;">
                                <div style="font-size:10.5px;color:#94a3b8;">وین‌ریت (Win Rate):</div>
                                <div style="font-size:16px;font-weight:900;color:#38bdf8;margin-top:2px;">
                                    ${(m.wr || 0).toFixed(1)}٪
                                </div>
                            </div>
                            <div style="background:#061324;padding:8px 10px;border-radius:6px;border:1px solid #1e3a5f;">
                                <div style="font-size:10.5px;color:#94a3b8;">پرافیت فاکتور (PF):</div>
                                <div style="font-size:15px;font-weight:bold;color:#fbbf24;margin-top:2px;">
                                    ${(m.pf || 0) < 90 ? (m.pf || 0).toFixed(2) : 'MAX'}
                                </div>
                            </div>
                            <div style="background:#061324;padding:8px 10px;border-radius:6px;border:1px solid #1e3a5f;">
                                <div style="font-size:10.5px;color:#94a3b8;">حداکثر افت (Max DD):</div>
                                <div style="font-size:15px;font-weight:bold;color:#fca5a5;margin-top:2px;">
                                    $${(m.max_dd || 0).toFixed(1)}
                                </div>
                            </div>
                        </div>
                    </div>

                    <button onclick="applySLModeAndGoToEquity(${sm})" style="background:${isWinner ? 'linear-gradient(135deg, #0284c7, #0369a1)' : '#0f2742'};border:1px solid ${colors[sm]};color:#fff;padding:8px 10px;border-radius:6px;font-size:11.5px;font-weight:bold;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;width:100%;box-shadow:0 2px 8px rgba(0,0,0,0.2);">
                        <span>⚡ فعال‌سازی در شبیه‌ساز</span>
                    </button>
                </div>
            `;
        }
        cardsContainer.innerHTML = htmlCards;
    }

    // 2. Render Comparative Multi-Line Canvas
    drawSLBattleChart(matrix);

    // 3. Render Head-to-Head KPI Table
    let tableBody = document.getElementById('slBattleTableBody');
    if (tableBody) {
        let rowsDef = [
            {
                label: '💵 سود خالص نهایی (پایه $100)',
                val: m => (m.net >= 0 ? '+' : '') + '$' + (m.net || 0).toFixed(2),
                raw: m => m.net || 0,
                best: (vals) => Math.max(...vals),
                color: '#00e676'
            },
            {
                label: '🎯 نرخ موفقیت (Win Rate %)',
                val: m => (m.wr || 0).toFixed(1) + '٪',
                raw: m => m.wr || 0,
                best: (vals) => Math.max(...vals),
                color: '#38bdf8'
            },
            {
                label: '⚡ نسبت سود به زیان (Profit Factor)',
                val: m => (m.pf < 90 ? (m.pf || 0).toFixed(2) : 'MAX'),
                raw: m => m.pf || 0,
                best: (vals) => Math.max(...vals),
                color: '#fbbf24'
            },
            {
                label: '🛡️ کنترل حداکثر افت سرمایه (Lowest DD)',
                val: m => '$' + (m.max_dd || 0).toFixed(1),
                raw: m => -(m.max_dd || 0),
                best: (vals) => Math.max(...vals),
                color: '#4ade80'
            },
            {
                label: '📏 میانگین فاصله ریسک به پیپ (Avg Points)',
                val: m => (m.avg_pts || 0).toFixed(1) + ' pt',
                raw: m => m.avg_pts || 0,
                best: null,
                color: '#cbd5e1'
            },
            {
                label: '🟢 تعداد کل معاملات سودده (Wins)',
                val: m => (m.wins || 0) + ' ترید',
                raw: m => m.wins || 0,
                best: (vals) => Math.max(...vals),
                color: '#34d399'
            },
            {
                label: '🔴 تعداد کل معاملات زیان‌ده (Losses)',
                val: m => (m.losses || 0) + ' ترید',
                raw: m => -(m.losses || 0),
                best: (vals) => Math.max(...vals),
                color: '#f87171'
            }
        ];

        let tableHtml = '';
        for (let r of rowsDef) {
            let vals = [0, 1, 2, 3].map(sm => matrix[sm] ? r.raw(matrix[sm]) : -999999);
            let bestVal = r.best ? r.best(vals) : null;
            let leaderName = '-';

            if (r.best && bestVal !== null) {
                let winIdx = vals.indexOf(bestVal);
                if (winIdx >= 0 && matrix[winIdx]) {
                    leaderName = matrix[winIdx].name.split(' ')[0] + ' ' + (matrix[winIdx].name.split(' ')[1] || '');
                }
            }

            tableHtml += `
                <tr style="border-bottom:1px solid #132742;transition:background 0.15s;" onmouseover="this.style.background='#0d233a'" onmouseout="this.style.background='transparent'">
                    <td style="padding:10px 14px;text-align:right;font-weight:600;color:#e2e8f0;">${r.label}</td>
                    <td style="padding:10px 12px;font-weight:bold;color:${vals[0] === bestVal ? '#38bdf8' : '#94a3b8'};${vals[0] === bestVal ? 'background:rgba(56,189,248,0.08);' : ''}">${matrix[0] ? r.val(matrix[0]) : '-'}</td>
                    <td style="padding:10px 12px;font-weight:bold;color:${vals[1] === bestVal ? '#10b981' : '#94a3b8'};${vals[1] === bestVal ? 'background:rgba(16,185,129,0.08);' : ''}">${matrix[1] ? r.val(matrix[1]) : '-'}</td>
                    <td style="padding:10px 12px;font-weight:bold;color:${vals[2] === bestVal ? '#c084fc' : '#94a3b8'};${vals[2] === bestVal ? 'background:rgba(192,132,252,0.08);' : ''}">${matrix[2] ? r.val(matrix[2]) : '-'}</td>
                    <td style="padding:10px 12px;font-weight:bold;color:${vals[3] === bestVal ? '#facc15' : '#94a3b8'};${vals[3] === bestVal ? 'background:rgba(250,204,21,0.08);' : ''}">${matrix[3] ? r.val(matrix[3]) : '-'}</td>
                    <td style="padding:10px 12px;font-weight:bold;color:#facc15;">${leaderName}</td>
                </tr>
            `;
        }
        tableBody.innerHTML = tableHtml;
    }
}

function applySLModeAndGoToEquity(mode) {
    if (typeof switchSimSLMode === 'function') {
        switchSimSLMode(mode);
    }
    // Switch to tab-equity
    let btn = document.querySelector(".tab-btn[onclick*='tab-equity']");
    if (btn) btn.click();
    if (typeof showSaveNotification === 'function') {
        let names = ['ثابت با آفست', 'بافر داینامیک ATR', 'ای‌تی‌آر خالص ولاتیلیتی', 'بافر درصدی الگو'];
        showSaveNotification('✅ مدل استاپ‌لاس [' + names[mode] + '] روی نمودار اکوئیتی فعال شد.');
    }
}

function drawSLBattleChart(matrix) {
    let canvas = document.getElementById('slBattleCanvas');
    if (!canvas) return;
    let ctx = canvas.getContext('2d');
    if (!ctx) return;

    let rect = canvas.getBoundingClientRect();
    let dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    let w = rect.width;
    let h = rect.height;
    ctx.clearRect(0, 0, w, h);

    let curves = [];
    for (let sm = 0; sm < 4; sm++) {
        let c = (matrix[sm] && matrix[sm].equity_curve) ? matrix[sm].equity_curve : [100.0];
        curves.push(c);
    }

    let maxPoints = Math.max(...curves.map(c => c.length));
    if (maxPoints <= 1) {
        ctx.fillStyle = '#64748b';
        ctx.font = '13px Vazirmatn, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('داده کافی برای رسم نمودار مقایسه‌ای در این نماد وجود ندارد.', w / 2, h / 2);
        return;
    }

    // Find global min and max across all 4 curves
    let minVal = 100.0, maxVal = 100.0;
    for (let c of curves) {
        for (let v of c) {
            if (v < minVal) minVal = v;
            if (v > maxVal) maxVal = v;
        }
    }
    let pad = (maxVal - minVal) * 0.1 || 10.0;
    minVal -= pad;
    maxVal += pad;

    let padLeft = 60, padRight = 20, padTop = 20, padBottom = 30;
    let chartW = w - padLeft - padRight;
    let chartH = h - padTop - padBottom;

    // Draw Grid & Y-Axis Labels
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#64748b';
    ctx.font = '10px Vazirmatn, sans-serif';
    ctx.textAlign = 'right';

    let steps = 5;
    for (let i = 0; i <= steps; i++) {
        let yVal = minVal + (maxVal - minVal) * (i / steps);
        let yPos = padTop + chartH - (i / steps) * chartH;
        ctx.beginPath();
        ctx.moveTo(padLeft, yPos);
        ctx.lineTo(w - padRight, yPos);
        ctx.stroke();
        ctx.fillText('$' + Math.round(yVal), padLeft - 8, yPos + 3);
    }

    // Baseline ($100)
    let y100 = padTop + chartH - ((100.0 - minVal) / (maxVal - minVal)) * chartH;
    ctx.strokeStyle = '#334155';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padLeft, y100);
    ctx.lineTo(w - padRight, y100);
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw 4 Curves
    let colors = ['#38bdf8', '#10b981', '#c084fc', '#facc15'];
    for (let sm = 0; sm < 4; sm++) {
        let curve = curves[sm];
        if (!curve || curve.length === 0) continue;

        ctx.strokeStyle = colors[sm];
        ctx.lineWidth = (sm === 1) ? 2.5 : 1.8; // Give ATR buffer prominent emphasis
        ctx.beginPath();

        for (let i = 0; i < curve.length; i++) {
            let x = padLeft + (i / (maxPoints - 1)) * chartW;
            let y = padTop + chartH - ((curve[i] - minVal) / (maxVal - minVal)) * chartH;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();
    }
}
