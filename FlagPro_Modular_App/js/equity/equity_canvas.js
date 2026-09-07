        function drawEquityChart() {
            let canvas = document.getElementById('equityCanvas');
            if (!canvas) return;
            let ctx = canvas.getContext('2d');
            if (!ctx) return;

            let dpr = window.devicePixelRatio || 1;
            let rect = canvas.getBoundingClientRect();
            let w = rect.width || canvas.offsetWidth || canvas.clientWidth || (canvas.parentElement ? canvas.parentElement.clientWidth : 0);
            let h = rect.height || canvas.offsetHeight || canvas.clientHeight || (canvas.parentElement ? canvas.parentElement.clientHeight : 0) || 450;

            if (w <= 0 || h <= 0) {
                if (!canvas._retryCount) canvas._retryCount = 0;
                if (canvas._retryCount < 40) {
                    canvas._retryCount++;
                    requestAnimationFrame(() => setTimeout(drawEquityChart, 50));
                }
                return;
            }
            canvas._retryCount = 0;

            if (window.ResizeObserver && canvas.parentElement && !canvas._roAttached) {
                canvas._roAttached = true;
                const ro = new ResizeObserver(() => {
                    requestAnimationFrame(() => drawEquityChart());
                });
                ro.observe(canvas.parentElement);
            }

            canvas.width = Math.round(w * dpr);
            canvas.height = Math.round(h * dpr);
            ctx.scale(dpr, dpr);

            let padLeft = 30;
            let padRight = 75;
            let padTop = 20;
            let padBottom = 28;
            let plotW = w - padLeft - padRight;
            let totalAvailableH = h - padTop - padBottom;

            let pts = currentSimPts;
            if (!pts || pts.length <= 1) {
                if (typeof runEquitySimulation === 'function' && typeof simTrades !== 'undefined' && simTrades.length > 0 && !canvas._simRanOnce) {
                    canvas._simRanOnce = true;
                    runEquitySimulation();
                    return;
                }
                ctx.clearRect(0, 0, w, h);
                ctx.fillStyle = '#0b0f19';
                ctx.fillRect(0, 0, w, h);
                ctx.fillStyle = '#94a3b8';
                ctx.font = '13px Segoe UI, Tahoma, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('هیچ معامله‌ای با این ترکیب فیلترها وجود ندارد! لطفاً فیلترها را تسهیل کنید.', w / 2, h / 2);
                canvas._coords = [];
                return;
            }
            canvas._simRanOnce = false;

            let minBal = Infinity;
            let maxBal = -Infinity;
            let totalPts = pts.length;

            for (let i = 0; i < totalPts; i++) {
                if (pts[i].b < minBal) minBal = pts[i].b;
                if (pts[i].b > maxBal) maxBal = pts[i].b;
                if (pts[i].peak !== undefined && pts[i].peak > maxBal) maxBal = pts[i].peak;
            }
            let balRange = maxBal - minBal;
            if (balRange < 50) balRange = 50;
            minBal = Math.floor((minBal - balRange * 0.05) / 50) * 50;
            maxBal = Math.ceil((maxBal + balRange * 0.05) / 50) * 50;
            balRange = maxBal - minBal;

            ctx.clearRect(0, 0, w, h);

            // Background
            ctx.fillStyle = '#0b0f19';
            ctx.fillRect(0, 0, w, h);

            // Determine Pane Dimensions
            let showDD = simState.showDrawdown;
            let curveH = showDD ? Math.floor(totalAvailableH * 0.68) : totalAvailableH;
            let ddTop = showDD ? (padTop + curveH + 24) : 0;
            let ddH = showDD ? (padTop + totalAvailableH - ddTop) : 0;

            // Plot area background for Curve
            ctx.fillStyle = '#0f172a';
            ctx.fillRect(padLeft, padTop, plotW, curveH);

            // Horizontal Grid & Price Labels for Curve
            let gridSteps = 5;
            ctx.strokeStyle = '#1e293b';
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.font = '11px Segoe UI, Tahoma, sans-serif';
            ctx.textAlign = 'left';

            for (let s = 0; s <= gridSteps; s++) {
                let val = minBal + (balRange / gridSteps) * s;
                let y = padTop + curveH - ((val - minBal) / balRange) * curveH;

                ctx.beginPath();
                ctx.moveTo(padLeft, y);
                ctx.lineTo(padLeft + plotW, y);
                ctx.stroke();

                ctx.fillStyle = '#94a3b8';
                ctx.fillText('$' + val.toFixed(0), padLeft + plotW + 10, y + 4);
            }

            // Vertical Grid & Dates spanning available height
            let dateSteps = 6;
            ctx.textAlign = 'center';

            for (let s = 0; s <= dateSteps; s++) {
                let idx = Math.min(Math.floor((totalPts - 1) * (s / dateSteps)), totalPts - 1);
                let x = padLeft + (idx / (totalPts - 1)) * plotW;

                ctx.beginPath();
                ctx.moveTo(x, padTop);
                ctx.lineTo(x, padTop + totalAvailableH);
                ctx.stroke();

                let dStr = pts[idx].t ? pts[idx].t.substring(5, 10) : '';
                ctx.fillStyle = '#64748b';
                ctx.fillText(dStr, x, padTop + totalAvailableH + 18);
            }

            ctx.setLineDash([]);

            // Baseline ($100) on Curve
            let baseVal = 100.0;
            if (baseVal >= minBal && baseVal <= maxBal) {
                let baseY = padTop + curveH - ((baseVal - minBal) / balRange) * curveH;
                ctx.strokeStyle = '#475569';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(padLeft, baseY);
                ctx.lineTo(padLeft + plotW, baseY);
                ctx.stroke();
            }

            // Build Coordinates & Track Drawdowns
            let coords = [];
            let maxDDPt = null;
            let maxDDVal = 0;

            for (let i = 0; i < totalPts; i++) {
                let pt = pts[i];
                let x = padLeft + (i / (totalPts - 1)) * plotW;
                let y = padTop + curveH - ((pt.b - minBal) / balRange) * curveH;
                let pVal = (pt.peak !== undefined) ? pt.peak : pt.b;
                let peakY = padTop + curveH - ((pVal - minBal) / balRange) * curveH;
                let ddVal = (pt.dd !== undefined) ? pt.dd : Math.max(0, pVal - pt.b);
                let ddPctVal = (pt.ddPct !== undefined) ? pt.ddPct : (pVal > 0 ? (ddVal / pVal * 100) : 0);

                let cObj = {
                    idx: i,
                    x: x,
                    y: y,
                    peakY: peakY,
                    peakVal: pVal,
                    ddVal: ddVal,
                    ddPctVal: ddPctVal,
                    pt: pt
                };
                coords.push(cObj);

                if (ddVal > maxDDVal) {
                    maxDDVal = ddVal;
                    maxDDPt = cObj;
                }
            }

            // 🛡️ Drawdown Shaded Valleys on Upper Curve
            if (showDD && coords.length > 1) {
                ctx.save();
                ctx.beginPath();
                ctx.moveTo(coords[0].x, coords[0].y);
                for (let i = 0; i < coords.length; i++) {
                    ctx.lineTo(coords[i].x, coords[i].y);
                }
                for (let i = coords.length - 1; i >= 0; i--) {
                    ctx.lineTo(coords[i].x, coords[i].peakY);
                }
                ctx.closePath();

                let ddGrad = ctx.createLinearGradient(0, padTop, 0, padTop + curveH);
                ddGrad.addColorStop(0, 'rgba(239, 68, 68, 0.25)');
                ddGrad.addColorStop(1, 'rgba(239, 68, 68, 0.08)');
                ctx.fillStyle = ddGrad;
                ctx.fill();

                // 🏆 High-Water Mark (Cumulative Peak) Dashed Line
                ctx.strokeStyle = '#facc15';
                ctx.lineWidth = 1.6;
                ctx.setLineDash([5, 4]);
                ctx.beginPath();
                for (let i = 0; i < coords.length; i++) {
                    if (i === 0) ctx.moveTo(coords[i].x, coords[i].peakY);
                    else ctx.lineTo(coords[i].x, coords[i].peakY);
                }
                ctx.stroke();
                ctx.restore();
            }

            // Gradient Fill below Equity Curve
            let grad = ctx.createLinearGradient(0, padTop, 0, padTop + curveH);
            if (simState.mode === 'kings') {
                grad.addColorStop(0, 'rgba(56, 189, 248, 0.30)');
                grad.addColorStop(1, 'rgba(56, 189, 248, 0.0)');
            } else {
                grad.addColorStop(0, 'rgba(168, 85, 247, 0.30)');
                grad.addColorStop(1, 'rgba(168, 85, 247, 0.0)');
            }

            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.moveTo(coords[0].x, padTop + curveH);
            for (let i = 0; i < coords.length; i++) {
                ctx.lineTo(coords[i].x, coords[i].y);
            }
            ctx.lineTo(coords[coords.length - 1].x, padTop + curveH);
            ctx.closePath();
            ctx.fill();

            // Equity Line
            ctx.strokeStyle = (simState.mode === 'kings') ? '#38bdf8' : '#a855f7';
            ctx.lineWidth = 2.2;
            ctx.beginPath();
            for (let i = 0; i < coords.length; i++) {
                if (i === 0) ctx.moveTo(coords[i].x, coords[i].y);
                else ctx.lineTo(coords[i].x, coords[i].y);
            }
            ctx.stroke();

            // 🚨 Highlight Maximum Drawdown on Curve
            if (showDD && maxDDPt && maxDDVal > 0) {
                ctx.save();
                ctx.strokeStyle = 'rgba(239, 68, 68, 0.75)';
                ctx.lineWidth = 1.4;
                ctx.setLineDash([2, 2]);
                ctx.beginPath();
                ctx.moveTo(maxDDPt.x, maxDDPt.peakY);
                ctx.lineTo(maxDDPt.x, maxDDPt.y);
                ctx.stroke();

                ctx.fillStyle = '#facc15';
                ctx.beginPath();
                ctx.arc(maxDDPt.x, maxDDPt.peakY, 3, 0, Math.PI * 2);
                ctx.fill();

                ctx.setLineDash([]);
                ctx.fillStyle = '#ef4444';
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 1.8;
                ctx.beginPath();
                ctx.arc(maxDDPt.x, maxDDPt.y, 5, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();

                let badgeTxt = '🚨 Max DD: -$' + Math.round(maxDDVal).toLocaleString('en-US') + ' (' + maxDDPt.ddPctVal.toFixed(1) + '%)';
                ctx.font = 'bold 10px Segoe UI, Tahoma, sans-serif';
                let txtW = ctx.measureText(badgeTxt).width;
                let bW = txtW + 14;
                let bH = 20;
                let bX = maxDDPt.x - bW / 2;
                let bY = maxDDPt.y + 10;

                if (bX < padLeft + 4) bX = padLeft + 4;
                if (bX + bW > padLeft + plotW - 4) bX = padLeft + plotW - bW - 4;
                if (bY + bH > padTop + curveH - 4) bY = maxDDPt.y - bH - 10;

                ctx.fillStyle = 'rgba(15, 23, 42, 0.94)';
                ctx.strokeStyle = '#ef4444';
                ctx.lineWidth = 1;
                ctx.beginPath();
                if (typeof ctx.roundRect === 'function') {
                    ctx.roundRect(bX, bY, bW, bH, 4);
                } else {
                    ctx.rect(bX, bY, bW, bH);
                }
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = '#fca5a5';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(badgeTxt, bX + bW / 2, bY + bH / 2);
                ctx.restore();
            }

            // Border for Curve
            ctx.strokeStyle = '#334155';
            ctx.lineWidth = 1;
            ctx.strokeRect(padLeft, padTop, plotW, curveH);

            // =================================================================
            // 📊 LOWER PANE: UNDERWATER DRAWDOWN BARS (میله‌های افت سرمایه)
            // =================================================================
            if (showDD && ddH > 25) {
                ctx.save();

                // Separator Line & Label
                let sepY = ddTop - 10;
                ctx.strokeStyle = '#1e293b';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(padLeft, sepY);
                ctx.lineTo(padLeft + plotW, sepY);
                ctx.stroke();

                ctx.font = 'bold 10px Segoe UI, Tahoma, sans-serif';
                ctx.fillStyle = '#fca5a5';
                ctx.textAlign = 'left';
                ctx.fillText('📊 عمق تمام افت‌های سرمایه (Underwater Drawdown Bars)', padLeft + 6, sepY - 2);

                // Lower Pane Background
                ctx.fillStyle = 'rgba(15, 23, 42, 0.65)';
                ctx.fillRect(padLeft, ddTop, plotW, ddH);

                // Y-Axis Scale for Drawdown Pane
                let ddScale = Math.max(10, Math.ceil(maxDDVal / 10) * 10);

                // Drawdown Grid Lines & Axis Labels
                ctx.font = '10px Segoe UI, Tahoma, sans-serif';
                ctx.textAlign = 'left';

                // $0 baseline at ddTop
                ctx.strokeStyle = '#334155';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(padLeft, ddTop);
                ctx.lineTo(padLeft + plotW, ddTop);
                ctx.stroke();
                ctx.fillStyle = '#34d399';
                ctx.fillText('$0', padLeft + plotW + 10, ddTop + 3);

                // Mid DD grid line
                let midY = ddTop + ddH * 0.5;
                ctx.strokeStyle = '#1e293b';
                ctx.setLineDash([3, 3]);
                ctx.beginPath();
                ctx.moveTo(padLeft, midY);
                ctx.lineTo(padLeft + plotW, midY);
                ctx.stroke();
                ctx.fillStyle = '#94a3b8';
                ctx.fillText('-$' + (ddScale / 2).toFixed(0), padLeft + plotW + 10, midY + 3);

                // Max DD grid line
                let bottomY = ddTop + ddH;
                ctx.strokeStyle = 'rgba(239, 68, 68, 0.4)';
                ctx.beginPath();
                ctx.moveTo(padLeft, bottomY);
                ctx.lineTo(padLeft + plotW, bottomY);
                ctx.stroke();
                ctx.fillStyle = '#f87171';
                ctx.fillText('-$' + ddScale.toFixed(0), padLeft + plotW + 10, bottomY + 3);
                ctx.setLineDash([]);

                // Draw Bars for EVERY point with drawdown
                let barW = Math.max(1.5, (plotW / totalPts) * 0.95);

                for (let i = 0; i < totalPts; i++) {
                    let c = coords[i];
                    if (c.ddVal > 0) {
                        let bH = (c.ddVal / ddScale) * ddH;
                        let bX = c.x - barW / 2;
                        let intensity = Math.min(1.0, c.ddVal / (maxDDVal || 1));
                        let alpha = 0.45 + intensity * 0.45;
                        ctx.fillStyle = 'rgba(239, 68, 68, ' + alpha.toFixed(2) + ')';
                        ctx.fillRect(bX, ddTop, barW, bH);
                    }
                }

                // Find and Label Top Prominent Local Drawdown Troughs
                let candidatePeaks = [];
                for (let i = 1; i < totalPts - 1; i++) {
                    let dd = coords[i].ddVal;
                    if (dd >= 5.0 && dd >= coords[i - 1].ddVal && dd >= coords[i + 1].ddVal) {
                        candidatePeaks.push(coords[i]);
                    }
                }
                candidatePeaks.sort((a, b) => b.ddVal - a.ddVal);

                let labeledPeaks = [];
                for (let cp of candidatePeaks) {
                    let tooClose = false;
                    for (let lp of labeledPeaks) {
                        if (Math.abs(cp.x - lp.x) < 38) {
                            tooClose = true;
                            break;
                        }
                    }
                    if (!tooClose) {
                        labeledPeaks.push(cp);
                        if (labeledPeaks.length >= 7) break;
                    }
                }

                // Draw numeric tags at the tip of each prominent drawdown bar
                for (let lp of labeledPeaks) {
                    let bH = (lp.ddVal / ddScale) * ddH;
                    let isMax = (lp === maxDDPt);
                    let tagY = ddTop + bH + 11;
                    if (tagY > ddTop + ddH + 2) tagY = ddTop + bH - 6;

                    ctx.font = isMax ? 'bold 10px Segoe UI, Tahoma, sans-serif' : 'bold 9px Segoe UI, Tahoma, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.fillStyle = isMax ? '#ef4444' : '#fca5a5';
                    ctx.fillText('-$' + Math.round(lp.ddVal), lp.x, tagY);

                    // Small circle at tip
                    ctx.fillStyle = isMax ? '#ef4444' : '#f87171';
                    ctx.beginPath();
                    ctx.arc(lp.x, ddTop + bH, isMax ? 3 : 2, 0, Math.PI * 2);
                    ctx.fill();
                }

                // Border for Drawdown Pane
                ctx.strokeStyle = '#334155';
                ctx.lineWidth = 1;
                ctx.strokeRect(padLeft, ddTop, plotW, ddH);

                ctx.restore();
            }

            canvas._coords = coords;
            canvas._padLeft = padLeft;
            canvas._padTop = padTop;
            canvas._plotW = plotW;
            canvas._plotH = totalAvailableH;
            canvas._curveH = curveH;
            canvas._ddTop = ddTop;
            canvas._ddH = ddH;
            canvas._showDD = showDD;
            canvas._maxDDVal = maxDDVal;
        }

        function initEquityCanvasEvents() {
            let canvas = document.getElementById('equityCanvas');
            if (!canvas || canvas._eventsBound) return;
            canvas._eventsBound = true;
            simCanvasEventsInitialized = true;

            canvas.addEventListener('mousemove', function(evt) {
                if (!canvas._coords || canvas._coords.length === 0) return;
                let rect = canvas.getBoundingClientRect();
                let mouseX = evt.clientX - rect.left;
                let mouseY = evt.clientY - rect.top;

                let tt = document.getElementById('equityTooltip');
                if (mouseX < canvas._padLeft || mouseX > canvas._padLeft + canvas._plotW ||
                    mouseY < canvas._padTop || mouseY > canvas._padTop + canvas._plotH) {
                    if(tt) tt.style.display = 'none';
                    let liveTag = document.getElementById('lblLiveConcurrentTag');
                    if (liveTag) liveTag.style.display = 'none';
                    return;
                }

                let coords = canvas._coords;
                let ratio = (mouseX - canvas._padLeft) / canvas._plotW;
                let idx = Math.round(ratio * (coords.length - 1));
                if (idx < 0) idx = 0;
                if (idx >= coords.length) idx = coords.length - 1;

                let target = coords[idx];
                let pt = target.pt;

                let liveTag = document.getElementById('lblLiveConcurrentTag');
                if (liveTag) {
                    if (pt && pt.concurrent !== undefined && pt.concurrent > 0) {
                        liveTag.textContent = pt.concurrent + ' همزمان در این نقطه';
                        liveTag.style.display = 'inline-block';
                    } else {
                        liveTag.style.display = 'none';
                    }
                }

                drawEquityChart();
                let ctx = canvas.getContext('2d');
                let dpr = window.devicePixelRatio || 1;
                ctx.save();
                ctx.scale(dpr, dpr);

                // Crosshair vertical
                ctx.strokeStyle = 'rgba(248, 250, 252, 0.4)';
                ctx.lineWidth = 1;
                ctx.setLineDash([2, 2]);
                ctx.beginPath();
                ctx.moveTo(target.x, canvas._padTop);
                ctx.lineTo(target.x, canvas._padTop + canvas._plotH);
                ctx.stroke();

                // Target Circle on Curve
                ctx.setLineDash([]);
                ctx.fillStyle = '#facc15';
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(target.x, target.y, 5, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();

                // If drawdown overlay is active, show vertical drop to Peak on curve
                if (simState.showDrawdown && target.peakY !== undefined && target.ddVal > 0) {
                    ctx.strokeStyle = 'rgba(239, 68, 68, 0.8)';
                    ctx.lineWidth = 1;
                    ctx.setLineDash([2, 2]);
                    ctx.beginPath();
                    ctx.moveTo(target.x, target.peakY);
                    ctx.lineTo(target.x, target.y);
                    ctx.stroke();

                    ctx.fillStyle = '#facc15';
                    ctx.beginPath();
                    ctx.arc(target.x, target.peakY, 3, 0, Math.PI * 2);
                    ctx.fill();
                }

                // Highlight active bar in the Lower Drawdown Pane
                if (canvas._showDD && canvas._ddH > 25) {
                    let ddScale = Math.max(10, Math.ceil(canvas._maxDDVal / 10) * 10);
                    let barH = (target.ddVal / ddScale) * canvas._ddH;
                    let barW = Math.max(3, (canvas._plotW / canvas._coords.length) * 1.8);

                    // Glowing bar highlight
                    ctx.fillStyle = '#facc15';
                    ctx.fillRect(target.x - barW / 2, canvas._ddTop, barW, barH);

                    // Pin dot at bottom of bar
                    if (target.ddVal > 0) {
                        ctx.fillStyle = '#ffffff';
                        ctx.beginPath();
                        ctx.arc(target.x, canvas._ddTop + barH, 3, 0, Math.PI * 2);
                        ctx.fill();

                        // Floating tooltip near bar
                        ctx.font = 'bold 10px Segoe UI, Tahoma, sans-serif';
                        ctx.fillStyle = '#facc15';
                        ctx.textAlign = 'center';
                        let tagY = canvas._ddTop + barH + 12;
                        if (tagY > canvas._ddTop + canvas._ddH + 4) tagY = canvas._ddTop + barH - 6;
                        ctx.fillText('-$' + Math.round(target.ddVal) + ' (' + target.ddPctVal.toFixed(1) + '%)', target.x, tagY);
                    }
                }
                ctx.restore();

                if (tt) {
                    tt.style.display = 'block';
                    let pnlCol = pt.p >= 0 ? '#00e676' : '#ef4444';
                    let pnlSign = pt.p >= 0 ? '+' : '';
                    let totProfit = pt.b - 100.0;
                    let totCol = totProfit >= 0 ? '#00e676' : '#ef4444';
                    let totSign = totProfit >= 0 ? '+' : '';

                    let ddVal = (target.ddVal !== undefined) ? target.ddVal : ((pt.dd !== undefined) ? pt.dd : Math.max(0, (pt.peak || pt.b) - pt.b));
                    let ddPct = (target.ddPctVal !== undefined) ? target.ddPctVal : ((pt.ddPct !== undefined) ? pt.ddPct : 0);
                    let peakVal = (target.peakVal !== undefined) ? target.peakVal : ((pt.peak !== undefined) ? pt.peak : pt.b);

                    let ddHtml = ddVal > 0 
                        ? '<b style="color:#f87171;">-$' + Math.round(ddVal).toLocaleString('en-US') + ' (' + ddPct.toFixed(1) + '٪)</b>'
                        : '<b style="color:#34d399;">$0 (سقف جدید ✨)</b>';

                    let concHtml = (pt && pt.concurrent !== undefined && pt.concurrent > 0)
                        ? `<div style="color:#e2e8f0;font-size:11.5px;margin-top:2px;">⚡ پوزیشن‌های همزمان باز: <b style="color:#38bdf8;">${pt.concurrent} معامله</b></div>`
                        : '';

                    tt.innerHTML = `
                        <div style="font-weight:bold;color:#facc15;margin-bottom:4px;border-bottom:1px solid #334155;padding-bottom:2px;">معامله #${pt.idx} - ${pt.n}</div>
                        <div style="color:#94a3b8;font-size:11px;">🕒 زمان: <span style="direction:ltr;display:inline-block;font-family:monospace;color:#f1f5f9;">${pt.t}</span></div>
                        <div style="margin-top:4px;">سود این معامله: <b style="color:${pnlCol};">${pnlSign}$${pt.p.toFixed(2)}</b></div>
                        <div>بالانس حساب: <b style="color:#38bdf8;">$${Math.round(pt.b).toLocaleString()}</b></div>
                        ${concHtml}
                        <div>سود خالص کل: <b style="color:${totCol};">${totSign}$${Math.round(totProfit).toLocaleString()} (${(totProfit).toFixed(1)}٪)</b></div>
                        <div style="margin-top:4px;border-top:1px solid #1e293b;padding-top:4px;">
                            <div>🏆 سقف تا این لحظه: <b style="color:#facc15;">$${Math.round(peakVal).toLocaleString()}</b></div>
                            <div>🛡️ افت از سقف (DD): ${ddHtml}</div>
                        </div>
                    `;

                    let ttX = target.x + 15;
                    let ttY = target.y - 40;
                    if (ttX + 220 > rect.width) ttX = target.x - 230;
                    if (ttY < 10) ttY = 10;
                    tt.style.left = ttX + 'px';
                    tt.style.top = ttY + 'px';
                }
            });

            canvas.addEventListener('mouseleave', function() {
                let tt = document.getElementById('equityTooltip');
                if (tt) tt.style.display = 'none';
                let liveTag = document.getElementById('lblLiveConcurrentTag');
                if (liveTag) liveTag.style.display = 'none';
                drawEquityChart();
            });

            window.addEventListener('resize', function() {
                drawEquityChart();
            });
        }




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

        
        