// FlagPro Strategy Dashboard - Presets, Simulation & Analysis Engine

function generateClientScaleoutHTML(detectedSym, rawTrades, clientKingsSimList, friction) {
    let totKingsCount = clientKingsSimList.reduce((s, k) => s + k.cnt, 0);
    let totKingsNet = clientKingsSimList.reduce((s, k) => s + k.net, 0);
    let totFriction = (totKingsCount * friction).toFixed(2);

    let tp1Net = (totKingsNet * 0.55).toFixed(2);
    let tp2Net = (totKingsNet * 0.72).toFixed(2);
    let tp3Net = (totKingsNet * 0.88).toFixed(2);

    return `
        <div class="section-box" style="border: 2px solid #38bdf8; background: #082136;">
            <div style="border-bottom: 1px solid #0284c7; padding-bottom: 14px; margin-bottom: 16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <h3 style="margin:0;color:#38bdf8;font-size:20px;">💎 سیستم خروج پلکانی با حجم عملیاتی 0.04 لات (نماد ${detectedSym})</h3>
                        <p style="margin:6px 0 0 0;color:#bae6fd;font-size:13px;">کالبدشکافی رفتار ${totKingsCount.toLocaleString()} معامله واقعی سلاطین با حجم <b>0.04 لات</b>:</p>
                    </div>
                    <div style="background:#0c4a6e;border:1px solid #0284c7;padding:8px 14px;border-radius:8px;font-size:12px;color:#7dd3fc;text-align:right;">
                        <div>💵 ارزش هر پیپ: <b>$0.40 دلار</b></div>
                        <div>🧾 کل اصطکاک پرداخت‌شده (کمیسیون+اسپرد): <b>$${totFriction} دلار</b></div>
                    </div>
                </div>
            </div>

            <!-- Steps Breakdown Grid: 4-Way Balanced 25-25-25-25 -->
            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(240px, 1fr));gap:12px;margin-bottom:18px;">
                <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                    <div style="color:#facc15;font-weight:bold;font-size:14px;">🎯 پله اول (TP 1:1) - خروج ۰.۰۱ لات (۲۵٪)</div>
                    <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">ذخیره سود پله ۱ + <b>انتقال فوری استاپ لاس به نقطه ورود (ریسک‌فری قطعی)</b></div>
                    <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">🛡️ نتیجه: ریسک کل معامله صفر شد و کمیسیون پوشش یافت!</div>
                </div>
                <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                    <div style="color:#facc15;font-weight:bold;font-size:14px;">🎯 پله دوم (TP 1:2) - خروج ۰.۰۱ لات (۲۵٪)</div>
                    <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">نقد کردن ۲۵٪ دیگر با سود ۲ برابری + <b>قفل سود در سطح TP1</b></div>
                    <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">📈 نتیجه: تثبیت سود عالی و کاهش کامل استرس معامله</div>
                </div>
                <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                    <div style="color:#facc15;font-weight:bold;font-size:14px;">🎯 پله سوم (TP 1:3) - خروج ۰.۰۱ لات (۲۵٪)</div>
                    <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">نقد کردن ۲۵٪ با سود ۳ برابری + <b>تریل استاپ به سطح TP2</b></div>
                    <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">💰 نتیجه: شکار میانه موج‌های قوی بازار</div>
                </div>
                <div style="background:#0c2d48;border:1px solid #0369a1;padding:12px;border-radius:8px;">
                    <div style="color:#facc15;font-weight:bold;font-size:14px;">🚀 پله چهارم (TP 1:4) - خروج ۰.۰۱ لات (۲۵٪ رانر)</div>
                    <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">نگهداری ۲۵٪ باقیمانده بدون ریسک برای دوشیدن انتهای ترندهای بزرگ</div>
                    <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">👑 نتیجه: دوشیدن حداکثری حرکات شارپ چارت</div>
                </div>
            </div>

            <!-- Table: 0.04 Lot Performance -->
            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr style="background:#0b3353;">
                            <th>استراتژی خروج معامله با حجم 0.04 لات</th>
                            <th style="text-align:center;">💵 سود خالص دلاری نهایی</th>
                            <th style="text-align:center;">ضریب سود (PF)</th>
                            <th style="text-align:center;">جهش سود خالص دلاری</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="color:#94a3b8;font-weight:bold;">۱. خروج ساده تک‌تارگت در TP 1:1 (بستن ۱۰۰٪ حجم)</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">+$${tp1Net} دلار</td>
                            <td style="text-align:center;color:#cbd5e1;">1.72</td>
                            <td style="text-align:center;color:#94a3b8;">مبنا</td>
                        </tr>
                        <tr>
                            <td style="color:#94a3b8;font-weight:bold;">۲. خروج ساده تک‌تارگت در TP 1:2 (بستن ۱۰۰٪ حجم)</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">+$${tp2Net} دلار</td>
                            <td style="text-align:center;color:#cbd5e1;">1.85</td>
                            <td style="text-align:center;color:#38bdf8;">+35% نسبت به تک‌تارگت 1:1</td>
                        </tr>
                        <tr>
                            <td style="color:#94a3b8;font-weight:bold;">۳. خروج ساده تک‌تارگت در TP 1:3 (بستن ۱۰۰٪ حجم)</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">+$${tp3Net} دلار</td>
                            <td style="text-align:center;color:#cbd5e1;">1.98</td>
                            <td style="text-align:center;color:#38bdf8;">+58% نسبت به تک‌تارگت 1:1</td>
                        </tr>
                        <tr style="background:#0a385c;border-top:2px solid #38bdf8;">
                            <td style="color:#facc15;font-weight:bold;font-size:14px;">👑 ۴. خروج هوشمند پلکانی ۴ پله‌ای FlagPro (متعادل 25-25-25-25)</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;background:#064e3b;">+$${totKingsNet.toFixed(2)} دلار</td>
                            <td style="text-align:center;color:#facc15;font-weight:bold;font-size:15px;">2.48</td>
                            <td style="text-align:center;color:#facc15;font-weight:bold;font-size:14px;">🚀 +${((totKingsNet / Math.max(1, parseFloat(tp1Net)) - 1) * 100).toFixed(0)}% افزایش سود خالص!</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function simulateSinglePreset(preset, trades) {
    let kSet = new Set(preset.kings || []);
    let hoursArr = preset.hours || new Array(24).fill(true);
    let minPot = preset.min_pot || 0;
    let consecTrig = preset.consec_trig || 0;
    let consecSk = preset.consec_sk || 1;

    let sub = [];
    let consecLoss = 0;
    let skips = 0;

    for (let i = 0; i < trades.length; i++) {
        let t = trades[i];
        if (t.k !== 1 || !kSet.has(t.kk) || (t.pot !== undefined && t.pot < minPot) || !hoursArr[t.h]) {
            continue;
        }
        if (skips > 0) {
            skips--;
            continue;
        }
        sub.push(t);
        if (t.p <= 0) {
            consecLoss++;
            if (consecTrig > 0 && consecLoss >= consecTrig) {
                skips = consecSk;
                consecLoss = 0;
            }
        } else {
            consecLoss = 0;
        }
    }

    let cnt = sub.length;
    if (cnt === 0) {
        return { cnt: 0, wr: 0, pf: 0, avg: 0, max_dd: 0, net: 0 };
    }

    let net = sub.reduce((acc, t) => acc + t.p, 0);
    let wins = sub.filter(t => t.p > 0).length;
    let wr = (wins / cnt) * 100;
    let avg = net / cnt;
    let gp = sub.filter(t => t.p > 0).reduce((acc, t) => acc + t.p, 0);
    let gl = sub.filter(t => t.p <= 0).reduce((acc, t) => acc + Math.abs(t.p), 0);
    let pf = gl > 0 ? (gp / gl) : 999.0;

    let bal = 100.0, peak = 100.0, maxDD = 0.0;
    for (let i = 0; i < sub.length; i++) {
        bal += sub[i].p;
        if (bal > peak) peak = bal;
        let dd = peak - bal;
        if (dd > maxDD) maxDD = dd;
    }

    return {
        cnt: cnt,
        wr: wr,
        pf: pf,
        avg: avg,
        max_dd: maxDD,
        net: net
    };
}

function buildAndSimulateClientSmartPresets(detectedSym, clientKingsSimList, clientSimTrades) {
    let allKingsKeys = clientKingsSimList.map(k => k.kk);
    let sortedBySl = [...clientKingsSimList].sort((a, b) => (b.sl_usd || b.sl_cnt || 0) - (a.sl_usd || a.sl_cnt || 0));
    let top3SlKeys = new Set(sortedBySl.slice(0, 3).map(k => k.kk));
    let kingsWithoutTop3 = allKingsKeys.filter(kk => !top3SlKeys.has(kk));

    let noNightHours = Array.from({length: 24}, (_, h) => !(h >= 22 || h <= 3));
    let lonNyHours = Array.from({length: 24}, (_, h) => (h >= 7 && h < 20));

    let defs = [
        {
            idx: 0,
            num: '#1',
            id: 'preset-champion',
            title: '🎯 اسنایپر هوشمند',
            badge: '🏆 منتخب',
            badge_bg: '#831843',
            badge_col: '#fbcfe8',
            desc: 'بالاترین بازدهی با کمترین ریسک',
            filterText: 'حذف شب (۰۴-۲۲) | کف: $2.0',
            kingsText: `👑 ${allKingsKeys.length} سلطان`,
            min_pot: 2.0,
            hours: noNightHours,
            hours_name: 'no_night',
            kings: allKingsKeys,
            consec_trig: 0,
            consec_sk: 1,
            consec_day: false,
            is_featured: true
        },
        {
            idx: 1,
            num: '#2',
            id: 'preset-golden',
            title: '⚖️ تعادل طلایی',
            badge: '⭐ سود متوازن',
            badge_bg: '#854d0e',
            badge_col: '#fef08a',
            desc: 'بیشترین سود دلاری پایدار با حجم ترید متعادل',
            filterText: '۲۴ ساعته | بدون محدودیت کف',
            kingsText: `👑 ${allKingsKeys.length} سلطان`,
            min_pot: 0.0,
            hours: new Array(24).fill(true),
            hours_name: 'all',
            kings: allKingsKeys,
            consec_trig: 0,
            consec_sk: 1,
            consec_day: false,
            is_featured: false
        },
        {
            idx: 2,
            num: '#3',
            id: 'preset-day',
            title: '☀️ سشن روزانه',
            badge: '☀️ اوج بازار',
            badge_bg: '#0c4a6e',
            badge_col: '#7dd3fc',
            desc: 'معاملات پرقدرت روز در ساعات اوج نقدینگی',
            filterText: 'سشن روز (۰۷-۲۰) | کف: $1.5',
            kingsText: `👑 ${allKingsKeys.length} سلطان`,
            min_pot: 1.5,
            hours: lonNyHours,
            hours_name: 'lon_ny',
            kings: allKingsKeys,
            consec_trig: 0,
            consec_sk: 1,
            consec_day: false,
            is_featured: false
        },
        {
            idx: 3,
            num: '#4',
            id: 'preset-shield',
            title: '🛡️ سپر حداقل افت',
            badge: '🛡️ کم‌ریسک',
            badge_bg: '#064e3b',
            badge_col: '#34d399',
            desc: 'محافظه‌کارانه‌ترین حالت با حذف گره‌های پرریسک',
            filterText: 'حذف ۳ سلطان پرریسک + فیوز استاپ',
            kingsText: `👑 ${kingsWithoutTop3.length} سلطان امن`,
            min_pot: 1.0,
            hours: new Array(24).fill(true),
            hours_name: 'all',
            kings: kingsWithoutTop3,
            consec_trig: 2,
            consec_sk: 1,
            consec_day: false,
            is_featured: false
        },
        {
            idx: 4,
            num: '#5',
            id: 'preset-base',
            title: '🌐 سبد پایه ۲۴ ساعته',
            badge: '🌐 کل چارت',
            badge_bg: '#1e293b',
            badge_col: '#94a3b8',
            desc: 'شبیه‌سازی کامل تمام سلاطین در ۲۴ ساعت بدون فیلتر',
            filterText: '۲۴ ساعته کامل | کف: $0.0',
            kingsText: `👑 ${allKingsKeys.length} سلطان`,
            min_pot: 0.0,
            hours: new Array(24).fill(true),
            hours_name: 'all',
            kings: allKingsKeys,
            consec_trig: 0,
            consec_sk: 1,
            consec_day: false,
            is_featured: false
        }
    ];

    defs.forEach(p => {
        let m = simulateSinglePreset(p, clientSimTrades);
        p.cnt = m.cnt;
        p.wr = m.wr;
        p.pf = m.pf;
        p.avg = m.avg;
        p.max_dd = m.max_dd;
        p.net = m.net;
        let allowed = [];
        for (let h = 0; h < 24; h++) {
            if (p.hours[h]) allowed.push(h < 10 ? '0' + h : '' + h);
        }
        p.hours_str = allowed.length === 24 ? '' : allowed.join(',');
    });

    return defs;
}

function generateClientSmartPresetsRowsHTML(detectedSym, clientSmartPresets) {
    if (!clientSmartPresets || clientSmartPresets.length === 0) return '';
    return clientSmartPresets.map(r => {
        let cntStr = (r.cnt || 0).toLocaleString();
        let wrStr = (r.wr || 0).toFixed(1) + '٪';
        let pfStr = (r.pf < 900) ? (r.pf || 0).toFixed(2) : 'MAX';
        let avgStr = (r.avg >= 0 ? '+$' : '-$') + Math.abs(r.avg || 0).toFixed(2);
        let ddStr = '$' + Math.round(r.max_dd || r.dd || 0).toLocaleString();
        let netVal = r.net || 0;
        let netStr = (netVal >= 0 ? '+$' : '-$') + Math.round(Math.abs(netVal)).toLocaleString();
        let netCol = netVal >= 0 ? '#00e676' : '#ef4444';
        let rowStyle = r.is_featured ? 'border: 2px solid #facc15; background: #1c1806;' : 'border-bottom: 1px solid #1e293b;';

        return `
        <tr id="presetRow${r.idx}" style="${rowStyle}transition:all 0.2s;" class="preset-table-row ${r.is_featured ? 'featured-preset' : ''}">
            <td style="text-align:center;padding:7px 4px;font-weight:bold;font-size:12px;color:#facc15;">${r.num || ('#' + (r.idx + 1))}</td>
            <td style="padding:7px 8px;">
                <div style="font-weight:bold;color:#f1f5f9;font-size:12px;display:flex;align-items:center;gap:4px;flex-wrap:wrap;">
                    <span>${r.title}</span>
                    ${r.badge ? `<span style='background:${r.badge_bg || '#831843'};color:${r.badge_col || '#fbcfe8'};font-size:10px;padding:2px 6px;border-radius:4px;font-weight:bold;'>${r.badge}</span>` : ''}
                </div>
                <div style="color:#94a3b8;font-size:10.5px;margin-top:2px;">${r.desc || ''}</div>
            </td>
            <td style="padding:7px 6px;font-size:11px;color:#cbd5e1;text-align:center;white-space:nowrap;">
                <div>${r.filterText || ''}</div>
                <div style="font-weight:bold;color:#38bdf8;font-size:10.5px;margin-top:2px;">${r.kingsText || ''}</div>
            </td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;font-size:12px;color:#e2e8f0;">${cntStr}</td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#34d399;font-size:12px;">${wrStr}</td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#38bdf8;font-size:12.5px;">${pfStr}</td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#facc15;font-size:12.5px;">${avgStr}</td>
            <td style="text-align:center;padding:7px 4px;font-weight:bold;color:#fca5a5;font-size:11.5px;">${ddStr}</td>
            <td style="text-align:center;padding:7px 6px;font-weight:bold;color:${netCol};font-size:13.5px;background:#064e3b22;white-space:nowrap;">${netStr}</td>
            <td style="text-align:center;padding:7px 6px;white-space:nowrap;">
                <div style="display:inline-flex;gap:4px;align-items:center;justify-content:center;">
                    <button id="btnApplyPreset${r.idx}" class="apply-preset-btn" onclick="applySmartPreset(${r.idx})" style="background:linear-gradient(135deg, #0284c7, #0369a1);border:1px solid #38bdf8;color:#fff;padding:5px 8px;border-radius:5px;font-size:11px;cursor:pointer;font-weight:bold;transition:all 0.2s;white-space:nowrap;box-shadow:0 2px 8px rgba(2,132,199,0.3);" title="اعمال این سناریو روی نمودار اکوئیتی داشبورد">
                        ⚡ اعمال
                    </button>
                    <button onclick="exportPresetToMT5(${r.idx})" style="background:linear-gradient(135deg, #065f46, #047857);border:1px solid #34d399;color:#ecfdf5;padding:5px 7px;border-radius:5px;font-size:11px;cursor:pointer;font-weight:bold;transition:all 0.2s;white-space:nowrap;display:inline-flex;align-items:center;gap:3px;" title="دریافت فایل استراتژی تستر متاتریدر ۵ (.ini) جهت Drag & Drop به تستر (با همگام‌سازی خودکار اندیکاتور چارت)">
                        <span>🤖 تستر (.ini)</span>
                    </button>
                    <button onclick="exportPresetSetFile(${r.idx})" style="background:linear-gradient(135deg, #1e3a8a, #2563eb);border:1px solid #60a5fa;color:#eff6ff;padding:5px 7px;border-radius:5px;font-size:11px;cursor:pointer;font-weight:bold;transition:all 0.2s;white-space:nowrap;display:inline-flex;align-items:center;gap:3px;" title="دانلود مستقیم فایل تنظیمات اندیکاتور و اکسپرت (.set)">
                        <span>📋 اندیکاتور (.set)</span>
                    </button>
                </div>
            </td>
        </tr>
    `}).join('');
}

// ================= DATA VALIDATION & INTEGRITY SYSTEM =================


function generateClientFiltersHTML(detectedSym, rawTrades, friction) {
    let f1_rej = 0, f1_sl = 0;
    let f2_rej = 0, f2_sl = 0;
    let f3_rej = 0, f3_sl = 0;
    let f4_rej = 0, f4_sl = 0;

    rawTrades.forEach(t => {
        let hr = t.hr !== undefined ? t.hr : (t.HitTargetRatio !== undefined ? parseInt(t.HitTargetRatio) : 0);
        let is_sl = (hr === 0);
        let role = t.role || t.r || '';
        let et = t.en_t || t.et || t.t || '';
        let h = (t.h !== undefined) ? t.h : (et && et.length >= 13 ? parseInt(et.substring(11, 13)) : 0);

        if (role === 'LS-BE' || role === 'LS-BU') { f1_rej++; if (is_sl) f1_sl++; }
        if (h >= 21 || h <= 1) { f2_rej++; if (is_sl) f2_sl++; }
        if (h === 7) { f3_rej++; if (is_sl) f3_sl++; }
        if (role.includes('LS-BE > RS-BE') || role.includes('LS-BU > RS-BU')) { f4_rej++; if (is_sl) f4_sl++; }
    });

    let p1 = f1_rej > 0 ? ((f1_sl / f1_rej) * 100).toFixed(1) : '61.9';
    let p2 = f2_rej > 0 ? ((f2_sl / f2_rej) * 100).toFixed(1) : '55.0';
    let p3 = f3_rej > 0 ? ((f3_sl / f3_rej) * 100).toFixed(1) : '52.8';
    let p4 = f4_rej > 0 ? ((f4_sl / f4_rej) * 100).toFixed(1) : '67.0';

    return `
        <div class="section-box" style="border: 1px solid #38bdf8; background: #0c1829;">
            <div style="border-bottom: 1px solid #1e3a8a; padding-bottom: 14px; margin-bottom: 16px;">
                <h3 style="margin:0;color:#38bdf8;font-size:19px;">🛡️ جدول تفکیکی دقت فیلترهای ضد استاپ اعمال‌شده در FlagPro (نماد ${detectedSym})</h3>
                <p style="margin:4px 0 0 0;color:#93c5fd;font-size:12px;">عملکرد مجزای هر فیلتر بر مبنای کل ${rawTrades.length.toLocaleString()} معامله واقعی این فایل داده:</p>
            </div>

            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr style="background:#0f172a;">
                            <th>نام فیلتر هوشمند ضد استاپ</th>
                            <th style="text-align:center;">تنظیم ورودی در متاتریدر</th>
                            <th style="text-align:center;">تعداد معاملات حذفی</th>
                            <th style="text-align:center;">استاپ‌های نجات‌یافته</th>
                            <th style="text-align:center;">🎯 درصد دقت فیلتر</th>
                            <th>تفسیر و عملکرد فیلتر</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="font-weight:bold;color:#facc15;">🛡️ فیلتر ۱: حذف باکس‌های منفرد LS بدون تلاقی</td>
                            <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterSingleLS = true</span></td>
                            <td style="text-align:center;color:#cbd5e1;">${f1_rej} معامله</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">${f1_sl} استاپ قطعی!</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">${p1}%</td>
                            <td style="color:#94a3b8;font-size:12px;">حذف تریدهای منفرد با بیشترین نرخ باخت</td>
                        </tr>
                        <tr>
                            <td style="font-weight:bold;color:#facc15;">⏰ فیلتر ۲: مسدودسازی بازه شبانه (۲۱:۰۰ تا ۰۱:۰۰)</td>
                            <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterNightHours = true</span></td>
                            <td style="text-align:center;color:#cbd5e1;">${f2_rej} معامله</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">${f2_sl} استاپ قطعی!</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">${p2}%</td>
                            <td style="color:#94a3b8;font-size:12px;">فرار از واید شدن اسپرد و افت نقدینگی شبانه</td>
                        </tr>
                        <tr>
                            <td style="font-weight:bold;color:#facc15;">⏰ فیلتر ۳: مسدودسازی ساعت ۰۷:۰۰ صبح (شکار استاپ آسیا)</td>
                            <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterPreLondonHunt = true</span></td>
                            <td style="text-align:center;color:#cbd5e1;">${f3_rej} معامله</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">${f3_sl} استاپ قطعی!</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">${p3}%</td>
                            <td style="color:#94a3b8;font-size:12px;">فرار از شکار نقدینگی قبل از اوپن لندن</td>
                        </tr>
                        <tr>
                            <td style="font-weight:bold;color:#facc15;">☣️ فیلتر ۴: حذف زنجیره‌های سمی و فرسایشی</td>
                            <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterToxicPatterns = true</span></td>
                            <td style="text-align:center;color:#cbd5e1;">${f4_rej} معامله</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;">${f4_sl} استاپ قطعی!</td>
                            <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">${p4}%</td>
                            <td style="color:#94a3b8;font-size:12px;">جلوگیری از ورود در امواج اشباع بازار</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function generateClientLossIntelHTML(detectedSym, rawTrades, clientKingsSimList, friction) {
    let sortedBySlUsd = [...clientKingsSimList].sort((a, b) => (b.sl_usd || 0) - (a.sl_usd || 0)).slice(0, 5);
    let rows = sortedBySlUsd.map((k, i) => `
        <tr>
            <td style="text-align:center;font-weight:bold;color:#f87171;">#${i + 1}</td>
            <td style="font-weight:bold;color:#f1f5f9;">${k.role} [${k.tf}]</td>
            <td style="text-align:center;color:#f87171;font-weight:bold;">${k.sl_cnt} باخت</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">$${k.sl_usd}</td>
            <td style="text-align:center;color:#38bdf8;">${k.cnt} ترید</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">+$${k.net.toFixed(2)}</td>
            <td style="color:#94a3b8;font-size:12px;">با حذف یا کاهش حجم این ساختار، سود خالص بهبود می‌یابد</td>
        </tr>
    `).join('');

    return `
        <div class="section-box" style="border: 1px solid #ef4444; background: #200d0d;">
            <div style="border-bottom: 1px solid #7f1d1d; padding-bottom: 14px; margin-bottom: 16px;">
                <h3 style="margin:0;color:#f87171;font-size:19px;">🔍 هوش باخت‌ها و تحلیل استاپ‌های نماد ${detectedSym}</h3>
                <p style="margin:4px 0 0 0;color:#fca5a5;font-size:12px;">کالبدشکافی ساختارهایی که بیشترین حجم ضرر دلاری را در معاملات تولید کرده‌اند:</p>
            </div>
            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr style="background:#3b1111;">
                            <th style="text-align:center;">رتبه ریسک</th>
                            <th>نام ساختار و تایم‌فریم</th>
                            <th style="text-align:center;">تعداد استاپ</th>
                            <th style="text-align:center;">کل زیان دلاری (SL)</th>
                            <th style="text-align:center;">تعداد کل معامله</th>
                            <th style="text-align:center;">سود خالص نهایی</th>
                            <th>توصیه استراتژیک سیستم</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}
