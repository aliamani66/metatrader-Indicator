var currentWeeklyBarMode = (typeof currentWeeklyBarMode !== 'undefined') ? currentWeeklyBarMode : 'kings';
var dataWeeklyBars = (typeof dataWeeklyBars !== 'undefined') ? dataWeeklyBars : [];

function switchWeeklyBarMode(mode) {
            currentWeeklyBarMode = mode;
            let btnK = document.getElementById('btnWkKings');
            let btnA = document.getElementById('btnWkAll');
            if(mode === 'kings') {
                if(btnK) btnK.classList.add('active');
                if(btnA) btnA.classList.remove('active');
            } else {
                if(btnK) btnK.classList.remove('active');
                if(btnA) btnA.classList.add('active');
            }
            drawWeeklyBarChart(mode);
        }

        function drawWeeklyBarChart(mode) {
            let canvas = document.getElementById('weeklyBarCanvas');
            if (!canvas) return;
            let ctx = canvas.getContext('2d');
            if (!ctx) return;

            let dpr = window.devicePixelRatio || 1;
            let rect = canvas.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return;

            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            ctx.scale(dpr, dpr);

            let w = rect.width;
            let h = rect.height;
            let padLeft = 45;
            let padRight = 20;
            let padTop = 25;
            let padBottom = 35;
            let plotW = w - padLeft - padRight;
            let plotH = h - padTop - padBottom;

            let bars = (typeof dataWeeklyBars !== 'undefined' && Array.isArray(dataWeeklyBars) && dataWeeklyBars.length > 0)
                ? dataWeeklyBars
                : (window.ALL_SYMBOLS_DATA && typeof currentActiveSymbol !== 'undefined' && (window.ALL_SYMBOLS_DATA[currentActiveSymbol] || window.ALL_SYMBOLS_DATA[currentActiveSymbol.replace(/[!#]/g, '').trim()]))
                    ? (window.ALL_SYMBOLS_DATA[currentActiveSymbol] || window.ALL_SYMBOLS_DATA[currentActiveSymbol.replace(/[!#]/g, '').trim()]).weekly_bar_data
                    : [];
            if (!bars || bars.length === 0) return;

            let minVal = 0;
            let maxVal = 0;
            for (let i = 0; i < bars.length; i++) {
                let val = (mode === 'kings') ? bars[i].k_pnl : bars[i].all_pnl;
                if (val < minVal) minVal = val;
                if (val > maxVal) maxVal = val;
            }

            let absMax = Math.max(Math.abs(minVal), Math.abs(maxVal), 50);
            absMax = Math.ceil(absMax / 25) * 25;
            let valRange = absMax * 2;

            ctx.clearRect(0, 0, w, h);

            // Background
            ctx.fillStyle = '#0b0f19';
            ctx.fillRect(0, 0, w, h);

            // Plot area
            ctx.fillStyle = '#0f172a';
            ctx.fillRect(padLeft, padTop, plotW, plotH);

            // Zero line Y
            let zeroY = padTop + plotH * (absMax / valRange);

            // Grid lines
            let steps = 4;
            ctx.strokeStyle = '#1e293b';
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.font = '11px Segoe UI, Tahoma, sans-serif';
            ctx.textAlign = 'right';

            for (let s = -steps; s <= steps; s += 2) {
                let val = (absMax / steps) * s;
                let y = zeroY - (val / valRange) * plotH;

                ctx.beginPath();
                ctx.moveTo(padLeft, y);
                ctx.lineTo(padLeft + plotW, y);
                ctx.stroke();

                ctx.fillStyle = '#64748b';
                let sign = val > 0 ? '+' : '';
                ctx.fillText(sign + '$' + val.toFixed(0), padLeft - 6, y + 4);
            }

            ctx.setLineDash([]);

            // Solid Baseline at $0
            ctx.strokeStyle = '#64748b';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(padLeft, zeroY);
            ctx.lineTo(padLeft + plotW, zeroY);
            ctx.stroke();

            // Draw Bars
            let numBars = bars.length;
            let barSlot = plotW / numBars;
            let barW = Math.max(4, barSlot * 0.72);
            let barCoords = [];

            for (let i = 0; i < numBars; i++) {
                let val = (mode === 'kings') ? bars[i].k_pnl : bars[i].all_pnl;
                let barH = (Math.abs(val) / valRange) * plotH;
                let x = padLeft + i * barSlot + (barSlot - barW) / 2;
                let y = (val >= 0) ? (zeroY - barH) : zeroY;

                let isGreen = val >= 0;
                let grad = ctx.createLinearGradient(0, y, 0, y + barH);
                if (isGreen) {
                    grad.addColorStop(0, '#00e676');
                    grad.addColorStop(1, '#059669');
                } else {
                    grad.addColorStop(0, '#dc2626');
                    grad.addColorStop(1, '#ef4444');
                }

                ctx.fillStyle = grad;
                ctx.fillRect(x, y, barW, barH);

                ctx.strokeStyle = isGreen ? '#34d399' : '#f87171';
                ctx.lineWidth = 1;
                ctx.strokeRect(x, y, barW, barH);

                // Week label on X-axis
                ctx.font = '10px Segoe UI, Tahoma, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillStyle = '#64748b';
                let wkAxisLabel = bars[i].week !== undefined ? ('W' + bars[i].week) : (bars[i].label || ('W' + (bars[i].week_idx || (i+1))));
                ctx.fillText(wkAxisLabel, x + barW / 2, padTop + plotH + 18);

                barCoords.push({
                    x: x,
                    y: y,
                    w: barW,
                    h: barH,
                    val: val,
                    item: bars[i]
                });
            }

            // Border
            ctx.strokeStyle = '#334155';
            ctx.lineWidth = 1;
            ctx.strokeRect(padLeft, padTop, plotW, plotH);

            canvas._barCoords = barCoords;
            canvas._padLeft = padLeft;
            canvas._padTop = padTop;
            canvas._plotW = plotW;
            canvas._plotH = plotH;
        }

        let weeklyBarEventsInitialized = false;
        function initWeeklyBarCanvasEvents() {
            let canvas = document.getElementById('weeklyBarCanvas');
            if (!canvas || canvas._eventsBound) return;
            canvas._eventsBound = true;

            canvas.addEventListener('mousemove', function(evt) {
                if (!canvas._barCoords) return;
                let rect = canvas.getBoundingClientRect();
                let mouseX = evt.clientX - rect.left;
                let mouseY = evt.clientY - rect.top;

                let tt = document.getElementById('weeklyBarTooltip');
                let found = null;

                for (let i = 0; i < canvas._barCoords.length; i++) {
                    let b = canvas._barCoords[i];
                    if (mouseX >= b.x - 2 && mouseX <= b.x + b.w + 2) {
                        found = b;
                        break;
                    }
                }

                if (!found) {
                    if (tt) tt.style.display = 'none';
                    drawWeeklyBarChart(currentWeeklyBarMode);
                    return;
                }

                drawWeeklyBarChart(currentWeeklyBarMode);
                let ctx = canvas.getContext('2d');
                let dpr = window.devicePixelRatio || 1;
                ctx.save();
                ctx.scale(dpr, dpr);

                // Highlight hovered bar
                ctx.strokeStyle = '#facc15';
                ctx.lineWidth = 2.5;
                ctx.strokeRect(found.x - 1, found.y - 1, found.w + 2, found.h + 2);
                ctx.restore();

                if (tt) {
                    tt.style.display = 'block';
                    let item = found.item;
                    let val = found.val;
                    let pnlCol = val >= 0 ? '#00e676' : '#ef4444';
                    let sign = val >= 0 ? '+' : '';
                    let trds = (currentWeeklyBarMode === 'kings') ? item.k_trades : item.all_trades;
                    let wins = (currentWeeklyBarMode === 'kings') ? item.k_wins : item.all_wins;
                    let losses = (currentWeeklyBarMode === 'kings') ? item.k_losses : item.all_losses;
                    let wr = (currentWeeklyBarMode === 'kings') ? item.k_wr : item.all_wr;
                    let wkTitle = item.label || ('هفته ' + (item.week !== undefined ? item.week : (item.week_idx || '')));
                    let dateSpan = item.dates || item.date_range || '';

                    tt.innerHTML = `
                        <div style="font-weight:bold;color:#facc15;margin-bottom:4px;border-bottom:1px solid #334155;padding-bottom:2px;">${wkTitle} ${dateSpan ? '(' + dateSpan + ')' : ''}</div>
                        <div>سود/زیان خالص این هفته: <b style="color:${pnlCol};font-size:13px;">${sign}$${val.toFixed(2)}</b></div>
                        <div style="color:#94a3b8;margin-top:4px;">تعداد کل معاملات: <b style="color:#f1f5f9;">${trds} معامله</b></div>
                        <div>بردها: <b style="color:#00e676;">${wins}</b> | باخت‌ها: <b style="color:#ef4444;">${losses}</b></div>
                        <div>وین‌ریت هفته: <b style="color:#38bdf8;">${wr}%</b></div>
                    `;

                    let ttX = found.x + 15;
                    let ttY = found.y - 50;
                    if (ttX + 230 > rect.width) ttX = found.x - 240;
                    if (ttY < 10) ttY = 10;
                    tt.style.left = ttX + 'px';
                    tt.style.top = ttY + 'px';
                }
            });

            canvas.addEventListener('mouseleave', function() {
                let tt = document.getElementById('weeklyBarTooltip');
                if (tt) tt.style.display = 'none';
                drawWeeklyBarChart(currentWeeklyBarMode);
            });

            window.addEventListener('resize', function() {
                drawWeeklyBarChart(currentWeeklyBarMode);
            });
        }

function selectWeeklyDetail(cardId) {
            if(!cardId) return;
            document.querySelectorAll('.week-detail-card').forEach(c => c.style.display = 'none');
            let el = document.getElementById(cardId);
            if(el) {
                el.style.display = 'block';
                el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }

        function filterWeeklyMode(mode) {
            let kingsRows = document.querySelectorAll('.wk-row-kings');
            let allRows = document.querySelectorAll('.wk-row-all');
            let btnKings = document.getElementById('btnWkTableKings');
            let btnAll = document.getElementById('btnWkTableAll');
            if(mode === 'kings') {
                kingsRows.forEach(r => r.style.display = '');
                allRows.forEach(r => r.style.display = 'none');
                if(btnKings) btnKings.classList.add('active');
                if(btnAll) btnAll.classList.remove('active');
            } else {
                kingsRows.forEach(r => r.style.display = 'none');
                allRows.forEach(r => r.style.display = '');
                if(btnKings) btnKings.classList.remove('active');
                if(btnAll) btnAll.classList.add('active');
            }
        }

        
        