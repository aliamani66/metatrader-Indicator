# -*- coding: utf-8 -*-
"""
HTML/CSS Tab Renderers for FlagPro Dashboard
Sever-Side Rendering (SSR) Templates
"""


def render_smart_presets_rows(smart_presets_json_data):
    smart_presets_rows_html = []
    for p in smart_presets_json_data:
        row_border = "border: 2px solid #facc15; background: #1c1806;" if p['is_featured'] else "border-bottom: 1px solid #1e293b;"
        pf = p['pf']
        pf_display = f"{pf:.2f}" if pf < 900 else "∞"
        nt = p['net']
        net_col = "#00e676" if nt >= 0 else "#ef4444"
        featured_tag = f" <span style='background:{p['badge_bg']};color:{p['badge_col']};font-size:9.5px;padding:1px 6px;border-radius:4px;font-weight:bold;'>{p['badge']}</span>"
        c = p['cnt']
        wr = p['wr']
        avg = p['avg']
        max_dd = p['max_dd']

        smart_presets_rows_html.append(f"""
        <tr id="presetRow{p['idx']}" style="{row_border}transition:all 0.2s;" class="preset-table-row {'featured-preset' if p['is_featured'] else ''}">
            <td style="text-align:center;padding:8px 4px;font-weight:bold;font-size:12px;color:#facc15;">#{p['idx']+1}</td>
            <td style="padding:8px 8px;">
                <div style="font-weight:700;color:#f1f5f9;font-size:12.5px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                    <span>{p['title']}</span>
                    {featured_tag}
                </div>
                <div style="color:#94a3b8;font-size:10.5px;margin-top:2px;">{p['strategy_desc']}</div>
            </td>
            <td style="padding:8px 6px;font-size:11px;color:#cbd5e1;text-align:center;white-space:nowrap;">
                <div>{p['filter_desc']}</div>
                <div style="font-weight:bold;color:#38bdf8;font-size:10px;margin-top:2px;">👑 {len(p['kings'])} سلطان فعال</div>
            </td>
            <td style="text-align:center;padding:8px 4px;font-weight:600;font-size:12px;color:#e2e8f0;">
                {c:,}
            </td>
            <td style="text-align:center;padding:8px 4px;font-weight:bold;color:#34d399;font-size:12px;">
                {wr:.1f}٪
            </td>
            <td style="text-align:center;padding:8px 4px;font-weight:bold;color:#38bdf8;font-size:12.5px;">
                {pf_display}
            </td>
            <td style="text-align:center;padding:8px 4px;font-weight:600;color:#facc15;font-size:12px;">
                ${avg:+.2f}
            </td>
            <td style="text-align:center;padding:8px 4px;font-weight:600;color:#fca5a5;font-size:11.5px;">
                ${max_dd:.0f}
            </td>
            <td style="text-align:center;padding:8px 6px;font-weight:800;color:{net_col};font-size:13px;background:#064e3b22;white-space:nowrap;">
                {'+$' if nt>=0 else '-$'}{abs(nt):,.0f}
            </td>
            <td style="text-align:center;padding:8px 6px;white-space:nowrap;">
                <div style="display:inline-flex;gap:4px;align-items:center;justify-content:center;">
                    <button id="btnApplyPreset{p['idx']}" class="apply-preset-btn" onclick="applySmartPreset({p['idx']})" style="background:linear-gradient(135deg, #0284c7, #0369a1);border:1px solid #38bdf8;color:#fff;padding:4px 9px;border-radius:5px;font-size:11px;cursor:pointer;font-weight:bold;transition:all 0.2s;white-space:nowrap;box-shadow:0 2px 6px rgba(2,132,199,0.3);" title="اعمال این سناریو روی نمودار اکوئیتی">
                        ⚡ اعمال
                    </button>
                    <button onclick="exportPresetToMT5({p['idx']})" style="background:linear-gradient(135deg, #065f46, #047857);border:1px solid #34d399;color:#ecfdf5;padding:4px 8px;border-radius:5px;font-size:11px;cursor:pointer;font-weight:bold;transition:all 0.2s;white-space:nowrap;" title="خروجی فایل تنظیمات تستر متاتریدر ۵ (.ini)">
                        🤖 تستر
                    </button>
                </div>
            </td>
        </tr>
        """)

    if not smart_presets_rows_html:
        return '<tr><td colspan="10" style="text-align:center;padding:16px;color:#94a3b8;font-size:12px;">💡 در حال حاضر برای این جفت‌ارز معاملات کافی برای استخراج سناریوهای سلطان ثبت نشده است. لطفاً جفت‌ارز دارای معاملات کامل (مانند GBPUSD) را انتخاب نمایید.</td></tr>'
    return ''.join(smart_presets_rows_html)



def render_scaleout_tab(c):
    be_diff = c['be_diff']
    m1_gross = c['m1_gross']
    m1_net = c['m1_net']
    m2_gross = c['m2_gross']
    m2_net = c['m2_net']
    qualified_kings = c['qualified_kings']
    s1_gross = c['s1_gross']
    s1_net = c['s1_net']
    s1_pf = c['s1_pf']
    s2_diff_dollar = c['s2_diff_dollar']
    s2_diff_pct = c['s2_diff_pct']
    s2_gross = c['s2_gross']
    s2_net = c['s2_net']
    s2_pf = c['s2_pf']
    s3_diff_dollar = c['s3_diff_dollar']
    s3_diff_pct = c['s3_diff_pct']
    s3_gross = c['s3_gross']
    s3_net = c['s3_net']
    s3_pf = c['s3_pf']
    sl_direct = c['sl_direct']
    sl_direct_pct = c['sl_direct_pct']
    tot_k_cnt = c['tot_k_cnt']
    tot_k_fric = c['tot_k_fric']
    tp1_only = c['tp1_only']
    tp1_only_pct = c['tp1_only_pct']
    tp2_only = c['tp2_only']
    tp2_only_pct = c['tp2_only_pct']
    tp3_4 = c['tp3_4']
    tp3_4_pct = c['tp3_4_pct']

    tab_scaleout_html = f"""<div class="section-box" style="border: 2px solid #38bdf8; background: #082136;">
                <div style="border-bottom: 1px solid #0284c7; padding-bottom: 14px; margin-bottom: 16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                        <div>
                            <h3 style="margin:0;color:#38bdf8;font-size:20px;">💎 سیستم خروج پلکانی با حجم عملیاتی 0.04 لات (با اعمال ۳ شرط لایو بازار)</h3>
                            <p style="margin:6px 0 0 0;color:#bae6fd;font-size:13px;">کالبدشکافی رفتار {tot_k_cnt} معامله واقعی سلاطین {len(qualified_kings)} گانه با تایید قطعی پولبک، پرتاب و حجم <b>0.04 لات</b>:</p>
                        </div>
                        <div style="background:#0c4a6e;border:1px solid #0284c7;padding:8px 14px;border-radius:8px;font-size:12px;color:#7dd3fc;text-align:right;">
                            <div>💵 ارزش هر پیپ: <b>$0.40 دلار</b></div>
                            <div>🧾 کل اصطکاک پرداخت‌شده (کمیسیون+اسپرد): <b>${tot_k_fric:.2f} دلار</b></div>
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
                        <div style="color:#34d399;font-weight:bold;font-size:12px;margin-top:6px;">👑 نتیجه: شکار سودهای ۴ برابری در {tp3_4} معامله!</div>
                    </div>
                </div>

                <!-- Table: 0.04 Lot Performance -->
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#0b3353;">
                                <th>استراتژی خروج معامله با حجم 0.04 لات</th>
                                <th style="text-align:center;">سود ناخالص</th>
                                <th style="text-align:center;">کل کمیسیون و اسپرد</th>
                                <th style="text-align:center;">💵 سود خالص دلاری نهایی</th>
                                <th style="text-align:center;">ضریب سود (PF)</th>
                                <th style="text-align:center;">جهش سود خالص دلاری</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="color:#94a3b8;font-weight:bold;">۱. خروج ساده تک‌تارگت در TP 1:1 (بستن ۱۰۰٪ حجم 0.04)</td>
                                <td style="text-align:center;color:#38bdf8;">${s1_gross:+.2f}</td>
                                <td style="text-align:center;color:#f87171;">${tot_k_fric:.2f}</td>
                                <td style="text-align:center;color:{'#00e676' if s1_net >= 0 else '#ef4444'};font-weight:bold;font-size:15px;">${s1_net:+.2f} دلار</td>
                                <td style="text-align:center;color:#cbd5e1;">{s1_pf:.2f}</td>
                                <td style="text-align:center;color:#94a3b8;">مبنا</td>
                            </tr>
                            <tr>
                                <td style="color:#94a3b8;font-weight:bold;">۲. خروج ساده تک‌تارگت در TP 1:2 (بستن ۱۰۰٪ حجم 0.04)</td>
                                <td style="text-align:center;color:#38bdf8;">${s2_gross:+.2f}</td>
                                <td style="text-align:center;color:#f87171;">${tot_k_fric:.2f}</td>
                                <td style="text-align:center;color:{'#00e676' if s2_net >= 0 else '#ef4444'};font-weight:bold;font-size:15px;">${s2_net:+.2f} دلار</td>
                                <td style="text-align:center;color:#cbd5e1;">{s2_pf:.2f}</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">${s2_diff_dollar:+.2f} ({s2_diff_pct:+.1f}%)</td>
                            </tr>
                            <tr style="background:#064e3b33;border:2px solid #10b981;">
                                <td style="color:#00e676;font-weight:bold;font-size:14px;">👑 ۳. خروج چهارپله‌ای متوازن FlagPro (۰.۰۱ در TP1 + ریسک‌فری | ۰.۰۱ در TP2 | ۰.۰۱ در TP3 | ۰.۰۱ در TP4) 🚀</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">${s3_gross:+.2f}</td>
                                <td style="text-align:color:#cbd5e1;">${tot_k_fric:.2f}</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:18px;">${s3_net:+.2f} دلار نقد خالص! 💵</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{s3_pf:.2f} 🚀</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">${s3_diff_dollar:+.2f} سود بیشتر ({s3_diff_pct:+.1f}%) 🚀</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Break-Even Comparison -->
                <div style="margin-top: 24px; border-top: 1px dashed #0284c7; padding-top: 18px;">
                    <h4 style="margin:0 0 10px 0; color:#facc15; font-size:16px;">⚖️ مقایسه بریک‌ایون (ریسک‌فری) با حجم 0.04 لات: انتقال استاپ در TP1 یا در TP2؟ کدام سودده‌تر است؟</h4>
                    <p style="margin:0 0 14px 0; color:#cbd5e1; font-size:12.5px; line-height:1.6;">
                        کالبدشکافی رفتار {tot_k_cnt} معامله سلاطین: <b>{sl_direct} معامله استاپ مستقیم ({sl_direct_pct:.1f}%)</b> | 
                        <b style="color:#facc15;">{tp1_only} معامله ({tp1_only_pct:.1f}%) فقط TP1 را تاچ کردند و برگشتند!</b> | 
                        <b>{tp2_only} معامله ({tp2_only_pct:.1f}%) تا TP2 رفتند</b> | 
                        <b style="color:#00e676;">{tp3_4} معامله ({tp3_4_pct:.1f}%) به TP3 و TP4 رسیدند!</b>
                    </p>

                    <div style="overflow-x:auto;">
                        <table>
                            <thead>
                                <tr style="background:#0b3353;">
                                    <th>روش انتقال استاپ به ورود (Break-Even) با حجم 0.04 لات</th>
                                    <th style="text-align:center;">سرنوشت {tp1_only} معامله‌ای که بعد از TP1 برگشتند</th>
                                    <th style="text-align:center;">سود ناخالص</th>
                                    <th style="text-align:center;">کل کمیسیون و اسپرد</th>
                                    <th style="text-align:center;">💵 سود خالص دلاری نهایی</th>
                                    <th style="text-align:center;">اختلاف و برتری مالی</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style="background:#064e3b44; border: 2px solid #10b981;">
                                    <td style="color:#00e676; font-weight:bold; font-size:13.5px;">🥇 حالت اول: انتقال استاپ به نقطه ورود (BE) در TP1</td>
                                    <td style="text-align:center; color:#a7f3d0; font-size:12px;">سود ۰.۰۲ لات در TP1 ذخیره شد + ۰.۰۲ لات باقیمانده بدون ضرر روی نقطه ورود خارج شد (سود خالص!)</td>
                                    <td style="text-align:center; color:#00e676; font-weight:bold;">${m1_gross:+.2f}</td>
                                    <td style="text-align:center; color:#cbd5e1;">${tot_k_fric:.2f}</td>
                                    <td style="text-align:center; color:#00e676; font-weight:bold;font-size:17px;">${m1_net:+.2f} دلار نقد 🚀</td>
                                    <td style="text-align:center; color:#facc15; font-weight:bold; font-size:14px;">🏆 برنده قطعی! (${be_diff:+.2f} دلار سود بیشتر)</td>
                                </tr>
                                <tr style="background:#450a0a22; border: 1px solid #7f1d1d;">
                                    <td style="color:#f87171; font-weight:bold; font-size:13.5px;">❌ حالت دوم: انتقال استاپ به نقطه ورود (BE) فقط در TP2</td>
                                    <td style="text-align:center; color:#fca5a5; font-size:12px;">سود ۰.۰۲ لات گرفته شد، اما چون استاپ دست نخورده بود، ۰.۰۲ لات باقیمانده برگشت و استاپ اولیه را زد!</td>
                                    <td style="text-align:center; color:#f87171; font-weight:bold;">${m2_gross:+.2f}</td>
                                    <td style="text-align:center; color:#cbd5e1;">${tot_k_fric:.2f}</td>
                                    <td style="text-align:center; color:#f87171; font-weight:bold; font-size:15px;">${m2_net:+.2f} دلار</td>
                                    <td style="text-align:center; color:#ef4444; font-size:13px;">بازنده (${abs(be_diff):.2f} دلار سود کمتر!)</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div style="background:#09304a; border-left:4px solid #38bdf8; padding:10px 14px; border-radius:4px; margin-top:12px; font-size:12px; color:#e0f2fe; line-height:1.5;">
                        💡 <b>نتیجه‌گیری مالی قطعی با حجم 0.04 لات:</b> دقیقاً <b>{tp1_only_pct:.1f}٪ معاملات ({tp1_only} معامله)</b> فقط تا TP1 پیش می‌روند. انتقال استاپ به ورود در TP1 مانع از سوختن {be_diff:.2f} دلار سود شما می‌شود و سود کل سیستم را به <b>${m1_net:+.2f} دلار نقد خالص</b> می‌رساند!
                    </div>
                </div>
            </div>"""
    return tab_scaleout_html



def render_loss_intel_tab(c):
    night_losses = c['night_losses']
    pure_flag_losses = c['pure_flag_losses']
    single_ls_losses = c['single_ls_losses']
    total_losses = c['total_losses']
    toxic_losses = c['toxic_losses']

    tab_loss_intel_html = f"""<div class="section-box" style="border: 1px solid #ef4444; background: #18111c;">
                <div style="border-bottom: 1px solid #332032; padding-bottom: 14px; margin-bottom: 18px;">
                    <h3 style="margin:0;color:#f87171;font-size:20px;">🔍 تحلیل آماری معاملات استاپ‌شده (Loss Pattern Intelligence)</h3>
                    <p style="margin:4px 0 0 0;color:#fca5a5;font-size:12px;">کالبدشکافی {total_losses} معامله استاپ‌خورده در این دیتاست جهت جلوگیری هوشمند از تکرار باخت:</p>
                </div>

                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));gap:14px;">
                    <div style="background:#261822;border:1px solid #4a1d2e;padding:14px;border-radius:8px;">
                        <div style="color:#f87171;font-weight:bold;font-size:14px;">🌙 باخت‌های ساعات شب (۲۱ تا ۰۱)</div>
                        <div style="font-size:22px;font-weight:bold;color:#fca5a5;margin:6px 0;">{night_losses} معامله <span style="font-size:12px;color:#94a3b8;">({(night_losses/total_losses*100) if total_losses else 0:.1f}%)</span></div>
                        <div style="color:#94a3b8;font-size:11px;">اسپرد بالا و نبود نقدینگی در سشن آسیا منشأ این باخت‌هاست.</div>
                    </div>
                    <div style="background:#261822;border:1px solid #4a1d2e;padding:14px;border-radius:8px;">
                        <div style="color:#f87171;font-weight:bold;font-size:14px;">🚫 باخت‌های باکس‌های تک LS</div>
                        <div style="font-size:22px;font-weight:bold;color:#fca5a5;margin:6px 0;">{single_ls_losses} معامله <span style="font-size:12px;color:#94a3b8;">({(single_ls_losses/total_losses*100) if total_losses else 0:.1f}%)</span></div>
                        <div style="color:#94a3b8;font-size:11px;">باکس‌های LS منفرد بدون تلاقی بیشترین ریسک را به همراه دارند.</div>
                    </div>
                    <div style="background:#261822;border:1px solid #4a1d2e;padding:14px;border-radius:8px;">
                        <div style="color:#f87171;font-weight:bold;font-size:14px;">☣️ باخت‌های زنجیره‌های سمی</div>
                        <div style="font-size:22px;font-weight:bold;color:#fca5a5;margin:6px 0;">{toxic_losses} معامله <span style="font-size:12px;color:#94a3b8;">({(toxic_losses/total_losses*100) if total_losses else 0:.1f}%)</span></div>
                        <div style="color:#94a3b8;font-size:11px;">ورود در روندهای فرسایشی انتهای موج.</div>
                    </div>
                    <div style="background:#261822;border:1px solid #4a1d2e;padding:14px;border-radius:8px;">
                        <div style="color:#f87171;font-weight:bold;font-size:14px;">📦 باخت‌های فلگ‌های ساده</div>
                        <div style="font-size:22px;font-weight:bold;color:#fca5a5;margin:6px 0;">{pure_flag_losses} معامله <span style="font-size:12px;color:#94a3b8;">({(pure_flag_losses/total_losses*100) if total_losses else 0:.1f}%)</span></div>
                        <div style="color:#94a3b8;font-size:11px;">نویزهای میانی چارت بدون شکست ساختار.</div>
                    </div>
                </div>
            </div>"""
    return tab_loss_intel_html



def render_weekly_tab(c):
    qualified_kings = c['qualified_kings']
    sorted_wk_keys = c['sorted_wk_keys']
    top_consistent_box = c['top_consistent_box']
    top_consistent_pct = c['top_consistent_pct']
    tot_kings_green_wks = c['tot_kings_green_wks']
    tot_kings_red_wks = c['tot_kings_red_wks']
    total_weeks = c['total_weeks']
    weekly_consistency_rows_html = c['weekly_consistency_rows_html']
    weekly_details_cards_html = c['weekly_details_cards_html']
    weekly_dropdown_options = c['weekly_dropdown_options']
    weekly_timeline_rows_html = c['weekly_timeline_rows_html']

    tab_weekly_html = f"""<!-- Weekly KPI Banner -->
            <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));margin-bottom:20px;">
                <div class="kpi-card" style="border-color:#38bdf8;">
                    <div class="kpi-title">📅 کل هفته‌های کالبدشکافی‌شده</div>
                    <div class="kpi-value" style="color:#38bdf8;">{len(sorted_wk_keys)} هفته</div>
                    <div class="kpi-sub">پوشش کامل ۶ ماه اخیر</div>
                </div>
                <div class="kpi-card" style="border-color:#00e676;">
                    <div class="kpi-title">🟢 هفته‌های سبز و سودده سلاطین</div>
                    <div class="kpi-value" style="color:#00e676;">{tot_kings_green_wks} از {len(sorted_wk_keys)}</div>
                    <div class="kpi-sub">{(tot_kings_green_wks/len(sorted_wk_keys)*100) if sorted_wk_keys else 0:.1f}٪ هفته‌ها در سود قطعی!</div>
                </div>
                <div class="kpi-card" style="border-color:#ef4444;">
                    <div class="kpi-title">🔴 هفته‌های اصلاحی و استاپ سلاطین</div>
                    <div class="kpi-value" style="color:#ef4444;">{tot_kings_red_wks} از {len(sorted_wk_keys)}</div>
                    <div class="kpi-sub">{(tot_kings_red_wks/len(sorted_wk_keys)*100) if sorted_wk_keys else 0:.1f}٪ هفته‌های نوسانی و رنج</div>
                </div>
                <div class="kpi-card" style="border-color:#facc15;">
                    <div class="kpi-title">👑 باثبات‌ترین سلطان دائمی چارت</div>
                    <div class="kpi-value" style="color:#facc15;font-size:18px;">{top_consistent_box}</div>
                    <div class="kpi-sub">ثبات هفتگی شگفت‌انگیز: {top_consistent_pct:.1f}٪</div>
                </div>
            </div>

            <!-- SECTION 1: Consistency Ranking -->
            <div class="section-box" style="border:1px solid #3b82f6;background:#0d1527;margin-bottom:24px;">
                <div style="border-bottom:1px solid #1e3a8a;padding-bottom:12px;margin-bottom:16px;">
                    <h3 style="margin:0;color:#60a5fa;font-size:19px;">🏆 جدول جامع رتبه‌بندی ثبات دائمی ساختارها (Consistency Leaderboard)</h3>
                    <p style="margin:4px 0 0 0;color:#93c5fd;font-size:12px;">پاسخ به سوال کلیدی شما: کدام باکس‌ها هفته به هفته پایدارترین سودآوری را برای همیشه حفظ کرده‌اند؟</p>
                </div>
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#1e293b;color:#94a3b8;">
                                <th style="text-align:center;">رتبه</th>
                                <th>نام ساختار و تایم‌فریم</th>
                                <th style="text-align:center;">دسته‌بندی</th>
                                <th style="text-align:center;">تعداد کل معامله</th>
                                <th style="text-align:center;">هفته‌های فعال</th>
                                <th style="text-align:center;">هفته‌های سبز 🟢</th>
                                <th style="text-align:center;">هفته‌های قرمز 🔴</th>
                                <th style="text-align:center;">درصد ثبات هفتگی</th>
                                <th style="text-align:center;">وین‌ریت TP1</th>
                                <th style="text-align:center;">نرخ باخت (SL)</th>
                                <th style="text-align:center;">سود کل ۶ ماه ($)</th>
                                <th style="text-align:center;">نشان پایداری</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(weekly_consistency_rows_html)}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- SECTION 2: Master Weekly Timeline -->
            <div class="section-box" style="border:1px solid #10b981;background:#061a14;margin-bottom:24px;">
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #064e3b;padding-bottom:12px;margin-bottom:16px;flex-wrap:wrap;gap:12px;">
                    <div>
                        <h3 style="margin:0;color:#34d399;font-size:19px;">📅 کارنامه کامل هفته به هفته (Master {total_weeks}-Week Timeline)</h3>
                        <p style="margin:4px 0 0 0;color:#a7f3d0;font-size:12px;">کالبدشکافی پیوسته تمام {total_weeks} هفته با تفکیک برد، استاپ و برترین سلطان هفته:</p>
                    </div>
                    <div style="display:flex;gap:8px;">
                        <button id="btnWkTableKings" class="sort-btn active" onclick="filterWeeklyMode('kings')">👑 فقط سلاطین {len(qualified_kings)} گانه</button>
                        <button id="btnWkTableAll" class="sort-btn" onclick="filterWeeklyMode('all')">🌐 کل ساختارهای چارت</button>
                    </div>
                </div>

                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#1e293b;color:#94a3b8;">
                                <th style="text-align:center;">شماره هفته</th>
                                <th style="text-align:center;">بازه تاریخ</th>
                                <th style="text-align:center;">تعداد معامله</th>
                                <th style="text-align:center;">برد (تارگت)</th>
                                <th style="text-align:center;">استاپ (Loss)</th>
                                <th style="text-align:center;">وین‌ریت %</th>
                                <th style="text-align:center;">درصد استاپ %</th>
                                <th style="text-align:center;">سود خالص دلاری ($)</th>
                                <th style="text-align:center;">وضعیت هفته</th>
                                <th style="text-align:center;">برترین سلطان هفته 🏆</th>
                                <th style="text-align:center;">عملیات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(weekly_timeline_rows_html)}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- SECTION 3: Detailed Box Deep Dive per Week -->
            <div class="section-box" style="border:1px solid #eab308;background:#171305;">
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #854d0e;padding-bottom:12px;margin-bottom:16px;flex-wrap:wrap;gap:12px;">
                    <div>
                        <h3 style="margin:0;color:#facc15;font-size:19px;">🔬 کالبدشکافی جزئیات تک‌تک ساختارها در هر هفته انتخابی</h3>
                        <p style="margin:4px 0 0 0;color:#fef08a;font-size:12px;">یک هفته را انتخاب کنید تا ببینید هر باکس در آن هفته مشخص دقیقاً چند سود، چند استاپ و چه مقدار دلار ساخته است:</p>
                    </div>
                    <div>
                        <select onchange="selectWeeklyDetail(this.value)" style="background:#1e293b;color:#f1f5f9;border:1px solid #475569;padding:8px 14px;border-radius:6px;font-size:13px;">
                            <option value="">-- انتخاب هفته جهت مشاهده جدول اختصاصی باکس‌ها --</option>
                            {''.join(weekly_dropdown_options)}
                        </select>
                    </div>
                </div>

                <div id="weeklyDetailsContainer">
                    {''.join(weekly_details_cards_html)}
                </div>
            </div>"""
    return tab_weekly_html



def render_filters_tab(c):
    accepted_trades = c['accepted_trades']
    closed = c['closed']
    ev_a = c['ev_a']
    ev_b = c['ev_b']
    f1_rej = c['f1_rej']
    f1_sl = c['f1_sl']
    f2_rej = c['f2_rej']
    f2_sl = c['f2_sl']
    f3_rej = c['f3_rej']
    f3_sl = c['f3_sl']
    f4_rej = c['f4_rej']
    f4_sl = c['f4_sl']
    f5_rej = c['f5_rej']
    f5_sl = c['f5_sl']
    f7_rej = c['f7_rej']
    f7_sl = c['f7_sl']
    rej_accuracy = c['rej_accuracy']
    rejected_trades = c['rejected_trades']
    sl_cnt_b = c['sl_cnt_b']
    sl_in_rej = c['sl_in_rej']
    sl_rate_a = c['sl_rate_a']
    sl_rate_b = c['sl_rate_b']
    w1_rate_a = c['w1_rate_a']
    w1_rate_b = c['w1_rate_b']
    w2_rate_a = c['w2_rate_a']
    w2_rate_b = c['w2_rate_b']

    tab_filters_html = f"""<div class="section-box" style="border: 1px solid #38bdf8; background: #0c1829;">
                <div style="border-bottom: 1px solid #1e3a8a; padding-bottom: 14px; margin-bottom: 16px;">
                    <h3 style="margin:0;color:#38bdf8;font-size:19px;">🛡️ جدول تفکیکی دقت فیلترهای ضد استاپ اعمال‌شده در FlagPro</h3>
                    <p style="margin:4px 0 0 0;color:#93c5fd;font-size:12px;">عملکرد مجزای هر فیلتر بر مبنای کل {len(closed):,} معامله واقعی این فایل داده:</p>
                </div>

                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr>
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
                                <td style="text-align:center;color:#cbd5e1;">{f1_rej} معامله</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">{f1_sl} استاپ قطعی!</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{(f1_sl/f1_rej*100) if f1_rej else 0:.1f}%</td>
                                <td style="color:#94a3b8;font-size:12px;">حذف تریدهای منفرد با بیشترین نرخ باخت</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#facc15;">⏰ فیلتر ۲: مسدودسازی بازه شبانه (۲۱:۰۰ تا ۰۱:۰۰)</td>
                                <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterNightHours = true</span></td>
                                <td style="text-align:center;color:#cbd5e1;">{f2_rej} معامله</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">{f2_sl} استاپ قطعی!</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{(f2_sl/f2_rej*100) if f2_rej else 0:.1f}%</td>
                                <td style="color:#94a3b8;font-size:12px;">فرار از واید شدن اسپرد و افت نقدینگی شبانه</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#facc15;">⏰ فیلتر ۳: مسدودسازی ساعت ۰۷:۰۰ صبح (شکار استاپ آسیا)</td>
                                <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterPreLondonHunt = true</span></td>
                                <td style="text-align:center;color:#cbd5e1;">{f3_rej} معامله</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">{f3_sl} استاپ قطعی!</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{(f3_sl/f3_rej*100) if f3_rej else 0:.1f}%</td>
                                <td style="color:#94a3b8;font-size:12px;">فرار از شکار نقدینگی قبل از اوپن لندن</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#facc15;">☣️ فیلتر ۴: حذف زنجیره‌های سمی و فرسایشی</td>
                                <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterToxicPatterns = true</span></td>
                                <td style="text-align:center;color:#cbd5e1;">{f4_rej} معامله</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">{f4_sl} استاپ قطعی!</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{(f4_sl/f4_rej*100) if f4_rej else 0:.1f}%</td>
                                <td style="color:#94a3b8;font-size:12px;">جلوگیری از ورود در امواج اشباع بازار</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#facc15;">📦 فیلتر ۵: حذف فلگ‌های ساده بدون تلاقی (نویز)</td>
                                <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterPureFlags = true</span></td>
                                <td style="text-align:center;color:#cbd5e1;">{f5_rej} معامله</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">{f5_sl} استاپ قطعی!</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{(f5_sl/f5_rej*100) if f5_rej else 0:.1f}%</td>
                                <td style="color:#94a3b8;font-size:12px;">تصفیه نویزهای ریز بازار</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#facc15;">💰 فیلتر ۶ (اقتصادی): حذف تریدهای با سود کمتر از اصطکاک</td>
                                <td style="text-align:center;"><span style="background:#065f46;color:#34d399;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:bold;">InpFilterLowRewardVsFriction = true</span></td>
                                <td style="text-align:center;color:#cbd5e1;">{f7_rej} معامله</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;">{f7_sl} زیان قطعی خنثی شد! 🎯</td>
                                <td style="text-align:center;color:#00e676;font-weight:bold;font-size:15px;">{(f7_sl/f7_rej*100) if f7_rej else 0:.1f}%</td>
                                <td style="color:#94a3b8;font-size:12px;">عدم ورود در تریدهایی که سودشان کمتر از کارمزد بروکر است</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Before vs After -->
            <div class="section-box" style="border: 1px solid #10b981; background: #0c1a1a;">
                <div style="border-bottom: 1px solid #134e4a; padding-bottom: 14px; margin-bottom: 16px;">
                    <h3 style="margin:0;color:#2dd4bf;font-size:19px;">⚖️ گزارش اثرگذاری فیلتر ضد استاپ (مقایسه زنده قبل و بعد از فیلترها)</h3>
                    <p style="margin:4px 0 0 0;color:#99f6e4;font-size:12px;">محاسبه دقیق بهبود آماری با فیلتر کردن ساعات پرخطر و الگوهای سمی:</p>
                </div>

                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>شاخص عملکردی کلیدی</th>
                                <th style="text-align:center;">بدون فیلتر (حالت خام)</th>
                                <th style="text-align:center;">با فیلتر ضد استاپ (Flag_Filters)</th>
                                <th style="text-align:center;">میزان بهبود و تغییر</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="font-weight:bold;">تعداد کل معاملات ارزیابی‌شده</td>
                                <td style="text-align:center;color:#94a3b8;">{len(closed):,} معامله</td>
                                <td style="text-align:center;color:#38bdf8;font-weight:bold;">{len(accepted_trades):,} معامله تاییدشده</td>
                                <td style="text-align:center;color:#f59e0b;">{len(rejected_trades)} معامله فیلتر و رد شد</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#10b981;">تعداد باخت‌های حذف‌شده (استاپ‌های نجات‌یافته)</td>
                                <td style="text-align:center;color:#ef4444;">۰ ({sl_cnt_b} معامله استاپ)</td>
                                <td style="text-align:center;color:#10b981;font-weight:bold;">{sl_in_rej} معامله استاپ خورده نجات یافت! 🎯</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">دقت فیلتر: {rej_accuracy:.1f}%</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;">وین‌ریت تارگت اول (TP 1:1)</td>
                                <td style="text-align:center;color:#94a3b8;">{w1_rate_b:.1f}%</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">{w1_rate_a:.1f}%</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">{w1_rate_a - w1_rate_b:+.1f}%</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;">وین‌ریت تارگت دوم (TP 1:2)</td>
                                <td style="text-align:center;color:#94a3b8;">{w2_rate_b:.1f}%</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">{w2_rate_a:.1f}%</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">{w2_rate_a - w2_rate_b:+.1f}%</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;">نرخ استاپ خوردن (Stop Loss Rate)</td>
                                <td style="text-align:center;color:#ef4444;">{sl_rate_b:.1f}%</td>
                                <td style="text-align:center;color:#f87171;font-weight:bold;">{sl_rate_a:.1f}%</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">{sl_rate_a - sl_rate_b:+.1f}% کاهش باخت</td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#38bdf8;">امید ریاضی به ازای هر ترید (EV در نسبت 1:2)</td>
                                <td style="text-align:center;color:#94a3b8;">{ev_b:+.2f} R</td>
                                <td style="text-align:center;color:#38bdf8;font-weight:bold;font-size:15px;">{ev_a:+.2f} R 🚀</td>
                                <td style="text-align:center;color:#38bdf8;font-weight:bold;">{ev_a - ev_b:+.2f} R رشد خالص</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>"""
    return tab_filters_html



def render_timeframes_tab(c):
    symbol_latency_tfs = c['symbol_latency_tfs']
    symbol_latency_all = c['symbol_latency_all']
    tf_kings_rows = c['tf_kings_rows']
    tf_raw_rows = c['tf_raw_rows']
    tf_role_rows = c['tf_role_rows']
    d_tot_kings = c['d_tot_kings']
    d_tot_raw = c['d_tot_raw']
    entered = c['entered']
    qualified_kings = c['qualified_kings']
    tf_map = c['tf_map']

    tab_timeframes_html = f"""<!-- ⏳ BOX-TO-ENTRY LATENCY & PULLBACK SPEED INTELLIGENCE -->
            <div class="section-box" style="border: 1px solid #0284c7; background: #081a2e; margin-bottom: 24px; padding: 18px 20px; border-radius: 10px;">
                <div style="border-bottom: 1px solid #1e3a8a; padding-bottom: 10px; margin-bottom: 14px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div>
                        <h3 style="margin:0; color:#38bdf8; font-size:18px; display:flex; align-items:center; gap:8px;">
                            ⏱️ تحلیل سرعت پولبک و زمان انتظار ورود (Box-to-Entry Latency)
                        </h3>
                        <p style="margin:4px 0 0 0; color:#93c5fd; font-size:12px;">
                            مدت زمان سپری‌شده از لحظه تشکیل باکس الگو تا لمس سطح اردر لیمیت و فعال‌سازی معامله (مبنای تعیین انقضای اردرهای لیمیت)
                        </p>
                    </div>
                    <span style="background:#0369a1; color:#e0f2fe; padding:4px 10px; border-radius:6px; font-size:12px; font-weight:bold;">
                        جامعه آماری: {len(entered):,} ستاپ فعال‌شده
                    </span>
                </div>

                <!-- 4 Latency KPI Cards -->
                <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px; margin-bottom:16px;">
                    <div class="kpi-card" style="border-color:#38bdf8; background:#0e2a47; padding:12px 14px;">
                        <div class="kpi-title" style="font-size:11.5px; color:#93c5fd;">⚡ حداقل زمان انتظار (سریع‌ترین پولبک)</div>
                        <div class="kpi-value" style="color:#38bdf8; font-size:22px;">{symbol_latency_all['min_short']}</div>
                        <div class="kpi-sub" style="color:#94a3b8;">{symbol_latency_all['min_fmt']}</div>
                    </div>
                    <div class="kpi-card" style="border-color:#00e676; background:#0a2c20; padding:12px 14px;">
                        <div class="kpi-title" style="font-size:11.5px; color:#86efac;">⏱️ میانگین زمان انتظار (Average Latency)</div>
                        <div class="kpi-value" style="color:#00e676; font-size:22px;">{symbol_latency_all['avg_short']}</div>
                        <div class="kpi-sub" style="color:#94a3b8;">{symbol_latency_all['avg_fmt']}</div>
                    </div>
                    <div class="kpi-card" style="border-color:#facc15; background:#292208; padding:12px 14px;">
                        <div class="kpi-title" style="font-size:11.5px; color:#fde047;">🎯 میانه انتظار (Median - نصف معاملات)</div>
                        <div class="kpi-value" style="color:#facc15; font-size:22px;">{symbol_latency_all['med_short']}</div>
                        <div class="kpi-sub" style="color:#94a3b8;">۵۰٪ معاملات زیر {symbol_latency_all['med_fmt']} وارد شدند</div>
                    </div>
                    <div class="kpi-card" style="border-color:#c084fc; background:#231138; padding:12px 14px;">
                        <div class="kpi-title" style="font-size:11.5px; color:#d8b4fe;">🛡️ چارک ۹۰٪ (فعال‌سازی ۹۰٪ اردرها)</div>
                        <div class="kpi-value" style="color:#c084fc; font-size:22px;">{symbol_latency_all['p90_short']}</div>
                        <div class="kpi-sub" style="color:#94a3b8;">۹۰٪ اردرها زیر {symbol_latency_all['p90_fmt']} فعال شدند</div>
                    </div>
                </div>

                <!-- Practical Strategy Guidance Box -->
                <div style="background:#0f2238; border-right:4px solid #38bdf8; padding:12px 16px; border-radius:6px; font-size:12px; color:#cbd5e1; line-height:1.8;">
                    <b style="color:#38bdf8;">💡 راهنمای عملی معاملاتی برای اردرهای لیمیت (Limit Order Life Expectancy):</b><br/>
                    • <b>در تایم M1:</b> میانگین زمان تاچ ورود <b>{symbol_latency_tfs['M1']['avg_fmt']}</b> (میانه: {symbol_latency_tfs['M1']['med_fmt']}) است و ۹۰٪ معاملات در کمتر از <b>{symbol_latency_tfs['M1']['p90_fmt']}</b> وارد می‌شوند. اگر اردری بیش از ۱ ساعت فعال نشد، لغو آن کاملاً امن و منطقی است.<br/>
                    • <b>در تایم M5:</b> میانگین انتظار ورود <b>{symbol_latency_tfs['M5']['avg_fmt']}</b> (میانه: {symbol_latency_tfs['M5']['med_fmt']}) است و تا ۳ ساعت ساختار معتبر باقی می‌ماند.<br/>
                    • <b>در تایم M15:</b> ستاپ‌ها سوئینگی هستند و میانگین انتظار تاچ اردر <b>{symbol_latency_tfs['M15']['avg_fmt']}</b> است.
                </div>
            </div>

            <div class="section-box">
                <div style="border-bottom:1px solid #334155;padding-bottom:8px;margin-bottom:10px;">
                    <h3 style="margin:0;color:#38bdf8;font-size:19px;">📊 تفکیک عملکرد تایم‌فریم‌ها در استراتژی سلاطین {len(qualified_kings)} گانه برگزیده</h3>
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
                            {"".join(tf_kings_rows)}
                        </tbody>
                    </table>
                </div>

                <!-- Comparison Banner: Why Filters & Kings Are Essential -->
                <div style="background:#1e1b4b;border:1px solid #4338ca;border-radius:8px;padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
                    <div>
                        <span style="color:#a5b4fc;font-weight:bold;font-size:13px;">💡 تفاوت معاملات سلاطین با کل بازار خام چارت:</span>
                        <div style="color:#cbd5e1;font-size:11px;margin-top:2px;">اگر کل {d_tot_raw['cnt']} معامله خام چارت بدون فیلتر معامله می‌شد، {abs(d_tot_raw['net']):.2f}$ {'زیان' if d_tot_raw['net'] < 0 else 'سود'} تولید می‌شد؛ اما سلاطین {len(qualified_kings)} گانه با فیلتر هوشمند آن را به {d_tot_kings['net']:+.2f}$ سود خالص رسانده‌اند!</div>
                    </div>
                    <button class="sort-btn" style="border-color:#a5b4fc;color:#a5b4fc;" onclick="let el = document.getElementById('rawTfTable'); el.style.display = el.style.display==='none'?'':'none';">👁️ مشاهده جدول کل دیتای خام چارت</button>
                </div>

                <!-- Hidden Comparative Raw Table -->
                <div id="rawTfTable" style="overflow-x:auto;margin-bottom:24px;border:1px dashed #475569;border-radius:8px;padding:10px;">
                    <div style="color:#94a3b8;font-size:12px;margin-bottom:6px;font-weight:bold;">⚠️ عملکرد کل {d_tot_raw['cnt']} معامله خام چارت بدون گزینش سلاطین (Raw Market Noise):</div>
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
                            {"".join(tf_raw_rows)}
                        </tbody>
                    </table>
                </div>

                <!-- Detailed Entity Breakdown by Timeframe -->
                <div style="display:flex;justify-content:space-between;align-items:center;border-top:1px solid #334155;padding-top:14px;flex-wrap:wrap;gap:10px;">
                    <div>
                        <h4 style="margin:0;color:#f8fafc;font-size:15px;">تفکیک جزئی گره‌ها در هر تایم‌فریم:</h4>
                    </div>
                    <div>
                        <button class="sort-btn active tf-btn" onclick="filterTF('ALL')">همه تایم‌ها</button>
                        <button class="sort-btn tf-btn" style="border-color:#38bdf8;color:#38bdf8;" onclick="filterTF('M1')">⚡ M1 ({len(tf_map.get('M1', []))})</button>
                        <button class="sort-btn tf-btn" style="border-color:#00e676;color:#00e676;" onclick="filterTF('M5')">🌟 M5 ({len(tf_map.get('M5', []))})</button>
                        <button class="sort-btn tf-btn" style="border-color:#f59e0b;color:#f59e0b;" onclick="filterTF('M15')">🕒 M15 ({len(tf_map.get('M15', []))})</button>
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
                            {"".join(tf_role_rows)}
                        </tbody>
                    </table>
                </div>
            </div>"""
    return tab_timeframes_html



def render_equity_tab(c):
    avg_trade_k = c['avg_trade_k']
    bal_a = c['bal_a']
    bal_initial = c['bal_initial']
    bal_k = c['bal_k']
    d_tot_kings = c['d_tot_kings']
    date_end_str = c['date_end_str']
    date_start_str = c['date_start_str']
    init_avg_concurrent = c['init_avg_concurrent']
    init_max_concurrent = c['init_max_concurrent']
    max_dd_a = c['max_dd_a']
    max_dd_a_pct = c['max_dd_a_pct']
    max_dd_k = c['max_dd_k']
    max_dd_k_pct = c['max_dd_k_pct']
    net_a = c['net_a']
    net_a_pct = c['net_a_pct']
    net_k = c['net_k']
    net_k_pct = c['net_k_pct']
    peak_k = c['peak_k']
    pts_all = c['pts_all']
    pts_kings = c['pts_kings']
    qualified_kings = c['qualified_kings']
    s3_pf = c['s3_pf']
    smart_presets_table_rows_str = c['smart_presets_table_rows_str']
    tot_kings_green_wks = c['tot_kings_green_wks']
    tot_kings_red_wks = c['tot_kings_red_wks']
    total_weeks = c['total_weeks']
    w1_p = c['w1_p']

    tab_equity_html = f"""<!-- Equity Metrics Banner (Dynamically updated by simulation) -->
            <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));gap:8px;margin-bottom:10px;">
                <div class="kpi-card" style="border-color:#38bdf8;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">💵 بالانس شروع حساب</div>
                    <div class="kpi-value" style="color:#f1f5f9;font-size:16px;">${bal_initial:,.0f}</div>
                    <div class="kpi-sub" style="font-size:9.5px;">شروع از {date_start_str}</div>
                </div>
                <div class="kpi-card" style="border-color:#00e676;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">📈 سود خالص کل</div>
                    <div class="kpi-value" id="eqKpiNetVal" style="color:#00e676;font-size:16px;">{'+$' if net_k>=0 else '-$'}{abs(net_k):,.0f}</div>
                    <div class="kpi-sub" id="eqKpiNetSub" style="font-size:9.5px;">نرخ رشد حساب: {net_k_pct:+.1f}٪</div>
                </div>
                <div class="kpi-card" style="border-color:#facc15;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">🏁 بالانس نهایی حساب</div>
                    <div class="kpi-value" id="eqKpiFinalBal" style="color:#facc15;font-size:16px;">${bal_k:,.0f}</div>
                    <div class="kpi-sub" id="eqKpiPeakSub" style="font-size:9.5px;">سقف سرمایه: ${peak_k:,.0f}</div>
                </div>
                <div class="kpi-card" style="border-color:#ef4444;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">🛡️ حداکثر افت (Max DD)</div>
                    <div class="kpi-value" id="eqKpiMaxDD" style="color:#fca5a5;font-size:16px;">${max_dd_k:.0f} ({max_dd_k_pct:.1f}٪)</div>
                    <div class="kpi-sub" id="eqKpiMaxDDSub" style="font-size:9.5px;">مدیریت ریسک کنترل‌شده</div>
                </div>
                <div class="kpi-card" style="border-color:#38bdf8;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">⚖️ پرافیت فاکتور (PF)</div>
                    <div class="kpi-value" id="eqKpiPF" style="color:#38bdf8;font-size:16px;">{s3_pf:.2f}</div>
                    <div class="kpi-sub" id="eqKpiPFSub" style="font-size:9.5px;">نسبت سود ناخالص به ضرر</div>
                </div>
                <div class="kpi-card" style="border-color:#10b981;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">🎯 وین‌ریت پله ۱ (WinRate)</div>
                    <div class="kpi-value" id="eqKpiWR" style="color:#34d399;font-size:16px;">{d_tot_kings['w1_p']:.1f}%</div>
                    <div class="kpi-sub" id="eqKpiWRSub" style="font-size:9.5px;">نرخ موفقیت حداقل ۱R</div>
                </div>
                <div class="kpi-card" style="border-color:#eab308;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">📊 تعداد معاملات فعال</div>
                    <div class="kpi-value" id="eqKpiCnt" style="color:#facc15;font-size:16px;">{len(pts_kings)-1} معامله</div>
                    <div class="kpi-sub" id="eqKpiCntSub" style="font-size:9.5px;">معاملات منطبق با فیلتر</div>
                </div>
                <div class="kpi-card" style="border-color:#a855f7;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">⚡ متوسط سود هر ترید</div>
                    <div class="kpi-value" id="eqKpiAvgTrade" style="color:#c084fc;font-size:16px;">{'+$' if avg_trade_k>=0 else '-$'}{abs(avg_trade_k):.2f}</div>
                    <div class="kpi-sub" id="eqKpiAvgTradeSub" style="font-size:9.5px;">میانگین خروجی هر ترید</div>
                </div>
                <div class="kpi-card" style="border-color:#0284c7;padding:6px 10px;">
                    <div class="kpi-title" style="font-size:9.5px;">⚡ معامله باز همزمان</div>
                    <div class="kpi-value" id="eqKpiConcVal" style="color:#38bdf8;font-size:16px;">{init_max_concurrent} معامله</div>
                    <div class="kpi-sub" id="eqKpiConcSub" style="font-size:9.5px;">میانگین: {init_avg_concurrent:.1f} همزمان</div>
                </div>
            </div>

                                    <!-- 🌟 2-COLUMN MAIN WORKSPACE GRID -->
            <div class="equity-two-col-container" id="eqTwoColContainer">

                <!-- 🔹 COLUMN 1: CHART SECTION (HALF-WIDTH) -->
                <div class="equity-col-chart" id="eqColChart">
                    <!-- 📈 INTERACTIVE EQUITY CANVAS GRAPH (AT THE VERY TOP) -->
            <!-- Interactive Canvas Graph Container -->
            <div class="section-box" style="border:1px solid #38bdf8;background:#0b0f19;padding:10px 14px;border-radius:8px;height:100%;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between;margin-bottom:0;">
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e293b;padding-bottom:8px;margin-bottom:8px;gap:8px;">
                    <div>
                        <h3 style="margin:0;color:#38bdf8;font-size:14px;display:flex;align-items:center;gap:6px;">
                            <span>📈 منحنی تعاملی رشد بالانس و اکوئیتی</span>
                        </h3>
                        <p style="margin:3px 0 0 0;color:#94a3b8;font-size:11px;">رسم دقیق معامله به معامله با حرکت موس روی نقاط</p>
                    </div>
                    <div style="display:flex;align-items:center;gap:6px;">
                        <button onclick="toggleDrawdownOverlay()" id="btnToggleDrawdown" style="background:#1e1b4b;border:1px solid #6366f1;color:#c7d2fe;padding:4px 9px;border-radius:5px;font-size:11px;cursor:pointer;display:flex;align-items:center;gap:4px;" title="نمایش یا پنهان‌سازی افت سرمایه (Drawdown) و خط سقف روی نمودار">
                            <span>🛡️ افت سرمایه (DD): <b id="lblToggleDrawdownState" style="color:#4ade80;">روشن</b></span>
                        </button>
                        <button onclick="toggleTwoColLayout()" id="btnToggleTwoCol" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:4px 8px;border-radius:5px;font-size:11px;cursor:pointer;display:flex;align-items:center;gap:4px;" title="تغییر حالت بین دو ستونی و تمام‌صفحه">
                            <span>⛶</span><span>تمام‌صفحه / ستونی</span>
                        </button>
                    </div>
                </div>

                <!-- Canvas Box -->
                <div style="position:relative;width:100%;height:400px;background:#0f172a;border:1px solid #1e293b;border-radius:10px;overflow:hidden;">
                    <!-- ⚡ Live & Peak Concurrent Trades Corner Badge -->
                    <div id="eqConcurrentBadge" style="position:absolute;top:12px;left:12px;background:rgba(15,23,42,0.92);backdrop-filter:blur(8px);border:1px solid #0284c7;border-radius:8px;padding:6px 12px;z-index:15;box-shadow:0 6px 20px rgba(0,0,0,0.6);display:flex;align-items:center;gap:10px;direction:rtl;pointer-events:none;">
                        <div style="width:26px;height:26px;border-radius:6px;background:#0369a1;border:1px solid #38bdf8;display:flex;align-items:center;justify-content:center;font-size:13px;">
                            ⚡
                        </div>
                        <div>
                            <div style="font-size:9.5px;color:#94a3b8;font-weight:600;display:flex;align-items:center;gap:4px;">
                                <span>تعداد معامله باز همزمان</span>
                                <span id="lblLiveConcurrentTag" style="display:none;background:#22c55e;color:#052e16;padding:1px 5px;border-radius:3px;font-size:8.5px;font-weight:bold;">روی نقطه</span>
                            </div>
                            <div style="font-size:13.5px;color:#f8fafc;font-weight:bold;display:flex;align-items:baseline;gap:6px;margin-top:1px;">
                                <span>حداکثر: <b id="lblMaxConcurrentTrades" style="color:#38bdf8;font-size:15px;">{init_max_concurrent}</b></span>
                                <span style="color:#475569;font-size:10px;">|</span>
                                <span style="font-size:11px;color:#94a3b8;">میانگین: <b id="lblAvgConcurrentTrades" style="color:#facc15;">{init_avg_concurrent:.1f}</b></span>
                            </div>
                        </div>
                    </div>

                    <canvas id="equityCanvas" style="width:100%;height:100%;display:block;cursor:crosshair;"></canvas>
                    <div id="equityTooltip" style="display:none;position:absolute;pointer-events:none;background:rgba(15,23,42,0.95);border:1px solid #38bdf8;padding:10px 14px;border-radius:8px;font-size:12px;color:#f1f5f9;box-shadow:0 8px 24px rgba(0,0,0,0.7);z-index:20;direction:rtl;min-width:210px;"></div>
                </div>

                <!-- Graph Legend & Stats Bar -->
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;font-size:11px;color:#94a3b8;flex-wrap:wrap;gap:8px;">
                    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                        <span style="display:flex;align-items:center;gap:4px;"><span style="display:inline-block;width:12px;height:3px;background:#38bdf8;border-radius:2px;"></span> رشد بالانس</span>
                        <span style="display:flex;align-items:center;gap:4px;"><span style="display:inline-block;width:12px;height:3px;background:#facc15;border-radius:2px;border-top:1px dashed #facc15;"></span> سقف سرمایه (HWM)</span>
                        <span style="display:flex;align-items:center;gap:4px;"><span style="display:inline-block;width:8px;height:10px;background:#ef4444;border-radius:2px;"></span> میله‌های افت (Underwater DD)</span>
                        <span style="display:flex;align-items:center;gap:4px;"><span style="display:inline-block;width:12px;height:3px;background:#475569;border-radius:2px;"></span> تراز پایه ($100)</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span>نقاط: <b id="lblEqPts" style="color:#facc15;">{len(pts_kings)-1}</b></span>
                        <span>|</span>
                        <span>{date_start_str} تا {date_end_str}</span>
                    </div>
                </div>
            </div>
                </div>

                <!-- 🔹 COLUMN 2: SUBTABS & CONTROLS (PRESETS / FILTERS / RISK) -->
                <div class="equity-col-controls" id="eqColControls">
                    <div style="background:#080d1a;border:1px solid #1e3a5f;border-radius:10px;padding:10px 12px;height:100%;box-sizing:border-box;display:flex;flex-direction:column;">
                        <!-- Subtabs Navigation Bar -->
                        <!-- 📑 SUB-NAVIGATION FOR CONTROLS & PRESETS -->
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;margin-bottom:10px;border-bottom:2px solid #1e3a5f;padding-bottom:8px;flex-wrap:wrap;gap:8px;">
                <div style="display:flex;gap:4px;flex-wrap:wrap;">
                    <button class="eq-subtab-btn active" onclick="openEqSubtab(event, 'eq-sub-presets')">
                        ⚡ سناریوهای استراتژی
                    </button>
                    <button class="eq-subtab-btn" onclick="openEqSubtab(event, 'eq-sub-filters')">
                        🎛️ شبیه‌ساز فیلترها
                    </button>
                    <button class="eq-subtab-btn" onclick="openEqSubtab(event, 'eq-sub-risk')">
                        🚨 کالبدشکافی استاپ‌ها
                    </button>
                    <button class="eq-subtab-btn" onclick="openEqSubtab(event, 'eq-sub-weekly')">
                        📊 کارنامه هفتگی
                    </button>
                    <button class="eq-subtab-btn" onclick="openEqSubtab(event, 'eq-sub-compare')">
                        ⚖️ مقایسه با کل چارت
                    </button>
                </div>
                <div style="display:flex;gap:5px;align-items:center;">
                    <button onclick="runClientAutoOptimizer()" style="background:linear-gradient(135deg, #7c3aed, #a855f7);border:1px solid #c084fc;color:#fff;font-size:11.5px;padding:5px 11px;border-radius:6px;cursor:pointer;font-weight:bold;box-shadow:0 2px 10px rgba(168,85,247,0.4);display:flex;align-items:center;gap:5px;">
                        <span>🤖 بهینه‌ساز خودکار (AI)</span>
                    </button>
                    <button onclick="openSavePresetModal()" style="background:#064e3b;border:1px solid #10b981;color:#6ee7b7;padding:5px 10px;border-radius:6px;font-size:11px;cursor:pointer;font-weight:bold;">💾 ذخیره چیدمان</button>
                    <button onclick="exportCurrentStateToMT5()" style="background:linear-gradient(135deg, #059669, #10b981);border:1px solid #34d399;color:#fff;padding:5px 10px;border-radius:6px;font-size:11px;cursor:pointer;font-weight:bold;display:flex;align-items:center;gap:4px;" title="خروجی مستقیم تنظیمات برای Strategy Tester متاتریدر (.ini) و اکسپرت (.set)">
                        <span>🤖 تنظیمات تستر (.ini)</span>
                    </button>
                    <button onclick="resetAllSimFilters()" style="background:#1e293b;border:1px solid #ef4444;color:#fca5a5;padding:5px 10px;border-radius:6px;font-size:11px;cursor:pointer;font-weight:bold;">🔄 بازنشانی</button>
                </div>
            </div>

                        <!-- Subpanels Scrollable Wrapper -->
                        <div class="eq-subpanels-wrapper">
                            <!-- SUBPANEL 1: PRESETS -->
            <div id="eq-sub-presets" class="eq-subpanel active">
                <!-- ⚡ SMART PRESETS & CUSTOM STRATEGY PORTFOLIOS -->
            <div class="section-box" style="border: 2px solid #facc15; background: #0b1528; padding: 12px; margin-bottom: 12px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #1e3a5f; padding-bottom: 10px; margin-bottom: 10px; flex-wrap:wrap; gap:8px;">
                    <div>
                        <h3 style="margin:0;color:#facc15;font-size:16px;display:flex;align-items:center;gap:6px;">
                            <span>⚡ پیشنهادات استراتژیک سیستم و سناریوهای شخصی شما</span>
                        </h3>
                        <p style="margin:3px 0 0 0;color:#94a3b8;font-size:11.5px;">با زدن دکمه «اعمال»، فیلترها روی چارت اعمال می‌شوند. با دکمه سبز می‌توانید هر چیدمانی را ذخیره کنید:</p>
                    </div>
                    <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
                        <button onclick="openSavePresetModal()" style="background:linear-gradient(135deg, #059669, #10b981);border:1px solid #34d399;color:#fff;font-size:11.5px;padding:5px 11px;border-radius:5px;cursor:pointer;font-weight:bold;box-shadow:0 2px 8px rgba(16,185,129,0.3);display:flex;align-items:center;gap:4px;">
                            <span>💾 ذخیره چیدمان فعلی</span>
                        </button>
                        <button onclick="exportCustomPresets()" style="background:#1e293b;border:1px solid #38bdf8;color:#7dd3fc;font-size:11px;padding:5px 8px;border-radius:5px;cursor:pointer;" title="خروجی فایل پشتیبان JSON">
                            📥 بکاپ (JSON)
                        </button>
                        <button onclick="document.getElementById('importPresetsInput').click()" style="background:#1e293b;border:1px solid #ca8a04;color:#fef08a;font-size:11px;padding:5px 8px;border-radius:5px;cursor:pointer;" title="بارگذاری سناریوهای ذخیره‌شده">
                            📤 بارگذاری
                        </button>
                        <input type="file" id="importPresetsInput" accept=".json" style="display:none;" onchange="importCustomPresets(event)" />
                    </div>
                </div>

                <div style="overflow-x:auto;">
                    <table style="width:100%;border-collapse:collapse;font-size:11.5px;text-align:right;">
                        <thead>
                            <tr style="background:#1e293b;color:#94a3b8;border-bottom:2px solid #334155;font-size:11.5px;">
                                <th style="padding:7px 5px;text-align:center;">#</th>
                                <th style="padding:7px 8px;">نام و سناریو</th>
                                <th style="padding:7px 6px;text-align:center;">تنظیمات کلیدی</th>
                                <th style="padding:7px 4px;text-align:center;">تعداد</th>
                                <th style="padding:7px 4px;text-align:center;">وین‌ریت</th>
                                <th style="padding:7px 4px;text-align:center;">PF</th>
                                <th style="padding:7px 4px;text-align:center;">متوسط سود</th>
                                <th style="padding:7px 4px;text-align:center;">افت DD</th>
                                <th style="padding:7px 6px;text-align:center;">سود خالص</th>
                                <th style="padding:7px 6px;text-align:center;">عملیات</th>
                            </tr>
                        </thead>
                        <!-- 1. SYSTEM BUILT-IN PRESETS -->
                        <tbody id="systemPresetsTbody">
                            {smart_presets_table_rows_str}
                        </tbody>
                        <!-- 2. USER SAVED CUSTOM PRESETS HEADER -->
                        <tbody id="customPresetsHeaderTbody">
                            <tr style="background:#131d2e;border-top:2px solid #38bdf8;border-bottom:1px solid #1e3a5f;">
                                <td colspan="10" style="padding:7px 10px;">
                                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                                        <div style="font-weight:bold;color:#38bdf8;font-size:12px;display:flex;align-items:center;gap:6px;">
                                            <span>⭐ سناریوهای شخصی ذخیره‌شده شما:</span>
                                            <span id="customPresetsCountBadge" style="background:#0c4a6e;color:#7dd3fc;font-size:10.5px;padding:1px 6px;border-radius:8px;">0 سناریو</span>
                                        </div>
                                        <div style="font-size:10.5px;color:#94a3b8;">
                                            این سناریوها در مرورگر شما پایدارند و با هر دیتای جدید فوراً با همان شرایط بازمحاسبه می‌شوند.
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                        <!-- 3. USER SAVED CUSTOM PRESETS ROWS -->
                        <tbody id="customPresetsTbody">
                            <!-- Populated dynamically by loadCustomPresets() -->
                        </tbody>
                    </table>
                </div>
            </div>
            </div>

            <!-- SUBPANEL 2: FILTERS (SLIDER, HOURS, KINGS) -->
            <div id="eq-sub-filters" class="eq-subpanel" style="display:none;">
                <!-- 🎛️ REAL-TIME FILTER SIMULATOR CONTROL PANEL -->
            <div class="section-box" style="border: 2px solid #0284c7; background: #081a2e; padding: 18px; margin-bottom: 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #1e4976; padding-bottom: 12px; margin-bottom: 16px; flex-wrap:wrap; gap:10px;">
                    <div>
                        <h3 style="margin:0;color:#38bdf8;font-size:18px;display:flex;align-items:center;gap:8px;">
                            <span>🎛️ شبیه‌ساز تعاملی فیلترها و بهینه‌ساز نمودار رشد (Real-time Strategy Optimizer)</span>
                        </h3>
                        <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">با حذف/اضافه هر سلطان، تغییر ساعات معاملاتی یا حداقل سود، نمودار و تمام شاخص‌های بالا به صورت آنی بازرسم می‌شوند:</p>
                    </div>
                    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                        <button onclick="openSavePresetModal()" style="background:#064e3b;border:1px solid #10b981;color:#6ee7b7;padding:6px 12px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;transition:all 0.2s;display:flex;align-items:center;gap:5px;">
                            <span>💾 ذخیره این ترکیب (Save Preset)</span>
                        </button>
                        <button onclick="resetAllSimFilters()" style="background:#1e293b;border:1px solid #ef4444;color:#fca5a5;padding:6px 12px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;transition:all 0.2s;">🔄 بازنشانی تمام فیلترها (Reset)</button>
                    </div>
                </div>

                <!-- 1. KINGS SELECTOR SECTION -->
                <div style="margin-bottom:18px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:8px;">
                        <div style="font-weight:bold;color:#facc15;font-size:13px;display:flex;align-items:center;gap:6px;">
                            <span>👑 فیلتر سلاطین منتخب (انتخاب تک‌تک یا گروهی {len(qualified_kings)} گره برتر):</span>
                            <span id="simKingsCountLabel" style="background:#854d0e;color:#fef08a;font-size:11px;padding:2px 8px;border-radius:10px;">{len(qualified_kings)} از {len(qualified_kings)} سلطان فعال</span>
                        </div>
                        <div style="display:flex;gap:6px;flex-wrap:wrap;">
                            <button onclick="selectAllKings(true)" style="background:#064e3b;border:1px solid #059669;color:#34d399;font-size:11px;padding:4px 10px;border-radius:5px;cursor:pointer;font-weight:bold;">🟢 انتخاب همه</button>
                            <button onclick="selectAllKings(false)" style="background:#450a0a;border:1px solid #dc2626;color:#fca5a5;font-size:11px;padding:4px 10px;border-radius:5px;cursor:pointer;font-weight:bold;">🔴 لغو همه</button>
                            <button onclick="selectOnlyPerfectKings()" style="background:#1e3a8a;border:1px solid #3b82f6;color:#93c5fd;font-size:11px;padding:4px 10px;border-radius:5px;cursor:pointer;">💎 فقط ۱۰۰٪ وین‌ریت</button>
                            <button onclick="selectOnlyRunnerKings()" style="background:#3b0764;border:1px solid #a855f7;color:#e9d5ff;font-size:11px;padding:4px 10px;border-radius:5px;cursor:pointer;">🚀 فقط الگوهای دونده</button>
                        </div>
                    </div>
                    <!-- Kings Chips Grid -->
                    <div id="simKingsGrid" style="display:grid;grid-template-columns:repeat(auto-fill, minmax(215px, 1fr));gap:8px;max-height:220px;overflow-y:auto;padding-right:4px;">
                        <!-- Dynamically filled by JS -->
                    </div>
                </div>

                <!-- 2. TRADING HOURS & PROFIT FILTER ROW -->
                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(320px, 1fr));gap:16px;background:#061424;padding:14px;border-radius:10px;border:1px solid #133352;">
                    
                    <!-- 2A. TRADING HOURS -->
                    <div>
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                            <div style="color:#38bdf8;font-weight:bold;font-size:12.5px;display:flex;align-items:center;gap:6px;">
                                <span>⏰ فیلتر ساعات معاملاتی و سشن‌ها:</span>
                            </div>
                            <span id="simHoursActiveBadge" style="font-size:11px;color:#7dd3fc;background:#0c4a6e;padding:2px 8px;border-radius:6px;">۲۴ ساعت فعال</span>
                        </div>
                        
                        <!-- Hour Presets -->
                        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
                            <button id="btnHAll" class="hour-preset-btn active" onclick="applyHourPreset('all', this)">🌍 ۲۴ ساعته</button>
                            <button id="btnHNoNight" class="hour-preset-btn" onclick="applyHourPreset('no_night', this)" title="بسته شدن معاملات از ۲۲:۰۰ شب تا ۰۴:۰۰ صبح (دقیقاً سناریوی درخواستی)">🛡️ بستن شب (۲۲ تا ۰۴)</button>
                            <button id="btnHLonNy" class="hour-preset-btn" onclick="applyHourPreset('lon_ny', this)">☀️ سشن لندن/نیویورک (۰۷ تا ۲۰)</button>
                            <button id="btnHAsia" class="hour-preset-btn" onclick="applyHourPreset('asia', this)">🌙 سشن آسیا (۰۰ تا ۰۸)</button>
                        </div>

                        <!-- 24-Hour Visual Buttons Bar -->
                        <div style="font-size:11px;color:#64748b;margin-bottom:4px;">کلیک روی هر ساعت برای فعال/غیرفعال کردن تکی:</div>
                        <div id="simHoursBar" style="display:grid;grid-template-columns:repeat(12, 1fr);gap:4px;">
                            <!-- 24 buttons 00 to 23 -->
                        </div>
                    </div>

                    <!-- 2B. MINIMUM TARGET PROFIT FILTER -->
                    <div>
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                            <div style="color:#34d399;font-weight:bold;font-size:12.5px;display:flex;align-items:center;gap:6px;">
                                <span>💰 فیلتر حداقل سود پتانسیل معامله (Min 1R Target $):</span>
                            </div>
                            <span id="simProfitBadge" style="font-size:11px;color:#6ee7b7;background:#064e3b;padding:2px 8px;border-radius:6px;">بدون فیلتر ($0)</span>
                        </div>

                        <!-- Presets -->
                        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
                            <button class="profit-preset-btn active" data-val="0" onclick="applyProfitPreset(0.0, this)">همه ($0)</button>
                            <button class="profit-preset-btn" data-val="1.5" onclick="applyProfitPreset(1.5, this)">$1.50+</button>
                            <button class="profit-preset-btn" data-val="2" onclick="applyProfitPreset(2.0, this)" title="اگر سود تارگت زیر ۲ دلار بود معامله نشود">$2.00+ ⭐</button>
                            <button class="profit-preset-btn" data-val="2.5" onclick="applyProfitPreset(2.5, this)">$2.50+</button>
                            <button class="profit-preset-btn" data-val="3" onclick="applyProfitPreset(3.0, this)">$3.00+</button>
                        </div>

                        <!-- Slider / Number Input -->
                        <div style="display:flex;align-items:center;gap:12px;margin-top:10px;">
                            <span style="font-size:12px;color:#94a3b8;">حداقل سود ۱R معامله (0.04 لات):</span>
                            <input type="range" id="simProfitSlider" min="0" max="6" step="0.25" value="0" oninput="onProfitSliderInput(this.value)" style="flex:1;cursor:pointer;accent-color:#10b981;" />
                            <span id="simProfitSliderVal" style="color:#34d399;font-family:monospace;font-weight:bold;font-size:14px;min-width:50px;text-align:left;">$0.00</span>
                        </div>
                        <div style="font-size:11px;color:#64748b;margin-top:6px;">
                            💡 در حجم 0.04 لات، سود تارگت اول معامله (1R) باید حداقل برابر این مبلغ باشد تا هزینه اسپرد/کمیسیون ($0.48) توجیه‌پذیر باشد.
                        </div>
                    </div>

                </div>

                                <!-- 2C. CONSECUTIVE LOSS FILTER ROW -->
                <div style="margin-top:12px;background:#061424;padding:12px 14px;border-radius:10px;border:1px solid #133352;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:8px;">
                        <div style="color:#ef4444;font-weight:bold;font-size:12.5px;display:flex;align-items:center;gap:6px;">
                            <span>🛡️ فیلتر وقفه بعد از استاپ‌های متوالی (Consecutive Loss Breaker):</span>
                        </div>
                        <span id="simConsecBadge2" style="font-size:11px;color:#cbd5e1;background:#1e293b;padding:2px 8px;border-radius:6px;">بدون وقفه (خاموش)</span>
                    </div>
                    <div style="display:flex;flex-wrap:wrap;gap:6px;">
                        <button class="consec-btn-filter active" data-trig="0" data-sk="0" data-day="0" onclick="applyConsecFromFilterTab(0, 0, false, this)">همه معاملات (عادی)</button>
                        <button class="consec-btn-filter" data-trig="2" data-sk="1" data-day="0" onclick="applyConsecFromFilterTab(2, 1, false, this)" title="دقیقاً سناریوی درخواستی: اگر ۲ استاپ متوالی خورد، معامله سوم گرفته نمی‌شود">🎯 بعد از ۲ استاپ 👈 رد معامله سوم</button>
                        <button class="consec-btn-filter" data-trig="2" data-sk="2" data-day="0" onclick="applyConsecFromFilterTab(2, 2, false, this)">🛑 بعد از ۲ استاپ 👈 رد ۲ معامله</button>
                        <button class="consec-btn-filter" data-trig="3" data-sk="1" data-day="0" onclick="applyConsecFromFilterTab(3, 1, false, this)">⚠️ بعد از ۳ استاپ 👈 رد ۱ معامله</button>
                        <button class="consec-btn-filter" data-trig="2" data-sk="0" data-day="1" onclick="applyConsecFromFilterTab(2, 0, true, this)">🌙 بعد از ۲ استاپ 👈 توقف تا فردا</button>
                    </div>
                </div>

                <!-- Status Footer -->
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;padding-top:10px;border-top:1px solid #133352;font-size:12px;color:#94a3b8;flex-wrap:wrap;gap:8px;">
                    <div>
                        وضعیت فیلتر جاری: <b id="simActiveTradesCount" style="color:#facc15;">{len(pts_kings)-1}</b> معامله فعال از مجموع <span id="simTotalBaseCount">{len(pts_kings)-1}</span> معامله (<span id="simFilteredOutCount" style="color:#f87171;">0 معامله حذف شده</span>)
                    </div>
                    <div style="display:flex;gap:14px;color:#cbd5e1;">
                        <span>وین‌ریت فیلترشده: <b id="simWinRateVal" style="color:#34d399;">66.5%</b></span>
                        <span>پرافیت فاکتور فیلترشده: <b id="simPfVal" style="color:#38bdf8;">2.44</b></span>
                    </div>
                </div>
            </div>
            </div>

            <!-- SUBPANEL 3: STOP LOSS RISK -->
            <div id="eq-sub-risk" class="eq-subpanel" style="display:none;">
                <!-- 🚨 STOP LOSS CONTROLLER & RISK ANALYZER -->
                    <!-- 🛡️ CONSECUTIVE LOSSES ANALYZER & COOLDOWN CIRCUIT BREAKER -->
                <div style="background: linear-gradient(135deg, #131b2e, #0c1222); border: 2px solid #38bdf8; border-radius: 10px; padding: 14px; margin-bottom: 14px; box-shadow: 0 4px 15px rgba(56, 189, 248, 0.15);">
                    <!-- Header -->
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #1e3a5f; padding-bottom: 8px; margin-bottom: 12px; flex-wrap:wrap; gap:8px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="font-size:20px;">🛡️</span>
                            <div>
                                <span style="font-weight:bold; color:#38bdf8; font-size:14px;">تحلیل تخصصی استاپ‌های پشت سر هم و فیلتر وقفه هوشمند (Consecutive Loss Breaker):</span>
                                <div style="font-size:11px; color:#94a3b8; margin-top:2px;">بررسی آماری طول رگه‌های باخت و شبیه‌سازی زنده قانون «توقف بعد از استاپ‌های متوالی»</div>
                            </div>
                        </div>
                        <!-- Quick Badge -->
                        <div id="consecLossSummaryBadge" style="background:#0f2d4a; border:1px solid #0284c7; color:#7dd3fc; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:bold;">
                            وضعیت: فیلتر خاموش (ترید عادی)
                        </div>
                    </div>

                    <!-- Row 1: KPI Stats for Streaks -->
                    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:8px; margin-bottom:12px;">
                        <div class="kpi-card" style="border-color:#ef4444; padding:8px 10px; background:#1e1420;">
                            <div class="kpi-title" style="color:#fca5a5; font-size:10.5px;">🚨 سقف استاپ پشت هم</div>
                            <div class="kpi-value" id="kpiMaxConsecLoss" style="color:#ef4444; font-size:18px;">۶ معامله</div>
                            <div class="kpi-sub" id="kpiMaxLossSub" style="color:#cbd5e1; font-size:9.5px;">در کل بازه ۶ ماهه</div>
                        </div>
                        <div class="kpi-card" style="border-color:#10b981; padding:8px 10px; background:#0f241d;">
                            <div class="kpi-title" style="color:#86efac; font-size:10.5px;">🏆 سقف برد پشت هم</div>
                            <div class="kpi-value" id="kpiMaxConsecWin" style="color:#34d399; font-size:18px;">۱۳ معامله</div>
                            <div class="kpi-sub" style="color:#cbd5e1; font-size:9.5px;">طولانی‌ترین رگه سود</div>
                        </div>
                        <div class="kpi-card" style="border-color:#f59e0b; padding:8px 10px; background:#241c0e;">
                            <div class="kpi-title" style="color:#fcd34d; font-size:10.5px;">📊 تعداد رگه‌های باخت</div>
                            <div class="kpi-value" id="kpiTotalLossStreaks" style="color:#facc15; font-size:18px;">۲۵۷ رگه</div>
                            <div class="kpi-sub" style="color:#cbd5e1; font-size:9.5px;">توالی‌های منتهی به برد</div>
                        </div>
                        <div class="kpi-card" style="border-color:#a855f7; padding:8px 10px; background:#1c1328;">
                            <div class="kpi-title" style="color:#d8b4fe; font-size:10.5px;">⚡ میانگین طول باخت‌ها</div>
                            <div class="kpi-value" id="kpiAvgLossStreak" style="color:#c084fc; font-size:18px;">۱.۸ معامله</div>
                            <div class="kpi-sub" style="color:#cbd5e1; font-size:9.5px;">اکثراً تک‌استاپ برمی‌گردد</div>
                        </div>
                    </div>

                    <!-- Row 2: Distribution Bars (1 SL, 2 SL, 3 SL, 4 SL, 5 SL, 6+ SL) -->
                    <div style="background:#090e1a; border:1px solid #1e293b; border-radius:8px; padding:10px 12px; margin-bottom:12px;">
                        <div style="font-size:11.5px; font-weight:bold; color:#cbd5e1; margin-bottom:8px; display:flex; justify-content:space-between;">
                            <span>📊 فراوانی و توزیع رگه‌های استاپ متوالی در چیدمان فعال:</span>
                            <span style="color:#64748b; font-size:10.5px;">(بررسی احتمال وقوع استاپ سوم بعد از خوردن ۲ استاپ)</span>
                        </div>
                        <div id="consecLossBarsGrid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(100px, 1fr)); gap:6px;">
                            <!-- Filled dynamically by JS -->
                        </div>
                    </div>

                    <!-- Row 3: Interactive Filter Controller -->
                    <div style="background:#090e1a; border:1px solid #1e293b; border-radius:8px; padding:12px 14px;">
                        <div style="font-size:12px; font-weight:bold; color:#38bdf8; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                            <span>🎛️ انتخاب سناریوی فیلتر استاپ متوالی (شبیه‌ساز آنی روی چارت):</span>
                        </div>
                        <div style="display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:10px;">
                            <button class="consec-btn active" id="btnConsecNone" onclick="setConsecLossFilter(0, 0, false, this)">
                                ⚪ بدون فیلتر (ترید عادی)
                            </button>
                            <button class="consec-btn" id="btnConsec2Skip1" onclick="setConsecLossFilter(2, 1, false, this)" title="دقیقاً سناریوی درخواستی: اگر ۲ استاپ متوالی خورد، معامله سوم گرفته نمی‌شود">
                                🎯 ۲ استاپ پشت‌هم 👈 معامله سوم رد شود (Skip 1)
                            </button>
                            <button class="consec-btn" id="btnConsec2Skip2" onclick="setConsecLossFilter(2, 2, false, this)">
                                🛑 ۲ استاپ پشت‌هم 👈 ۲ معامله بعدی رد شود (Skip 2)
                            </button>
                            <button class="consec-btn" id="btnConsec3Skip1" onclick="setConsecLossFilter(3, 1, false, this)">
                                ⚠️ ۳ استاپ پشت‌هم 👈 ۱ معامله بعدی رد شود
                            </button>
                            <button class="consec-btn" id="btnConsec2Daily" onclick="setConsecLossFilter(2, 0, true, this)" title="قانون شرکت‌های پراپ: اگر امروز ۲ استاپ خورد، کل باقی معاملات همان روز بسته شود">
                                🌙 ۲ استاپ پشت‌هم 👈 توقف معاملات تا روز بعد
                            </button>
                        </div>

                        <!-- Custom Controls Toggle / Inputs -->
                        <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; background:#070b14; padding:8px 12px; border-radius:6px; border:1px solid #1e293b; font-size:11.5px;">
                            <span style="color:#94a3b8;">تنظیم دستی دلخواه:</span>
                            <span>اگر</span>
                            <select id="selConsecTrigger" onchange="onCustomConsecChange()" style="background:#0f172a; color:#f1f5f9; border:1px solid #334155; border-radius:4px; padding:3px 6px; font-size:11px;">
                                <option value="0">خاموش</option>
                                <option value="1">۱ استاپ</option>
                                <option value="2">۲ استاپ</option>
                                <option value="3">۳ استاپ</option>
                                <option value="4">۴ استاپ</option>
                            </select>
                            <span>پشت‌هم خورد،</span>
                            <select id="selConsecAction" onchange="onCustomConsecChange()" style="background:#0f172a; color:#f1f5f9; border:1px solid #334155; border-radius:4px; padding:3px 6px; font-size:11px;">
                                <option value="skip_1">۱ معامله بعدی رد شود</option>
                                <option value="skip_2">۲ معامله بعدی رد شود</option>
                                <option value="skip_3">۳ معامله بعدی رد شود</option>
                                <option value="skip_day">تا روز بعد ترید متوقف شود</option>
                            </select>
                        </div>

                        <!-- Impact Result Box -->
                        <div id="consecFilterImpactBox" style="margin-top:10px; padding:8px 12px; border-radius:6px; background:#0d1829; border:1px solid #1e3a5f; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; font-size:11px;">
                            <div style="color:#cbd5e1;">
                                📌 تأثیر فیلتر روی چارت: <b id="consecSkippedTradesVal" style="color:#facc15;">0</b> معامله اسکیپ شد (<span id="consecSavedLossesVal" style="color:#00e676; font-weight:bold;">0 استاپ نجات یافت</span> | <span id="consecMissedWinsVal" style="color:#f87171;">0 برد از دست رفت</span>)
                            </div>
                            <div style="color:#38bdf8;">
                                🛡️ وضعیت دراودان: <b id="consecDDImpactVal">افت سرمایه فعلی: $42.75</b>
                            </div>
                        </div>
                    </div>
                </div>

                <div id="slRiskPanel" style="background: linear-gradient(135deg, #1c0808, #110505); border: 2px solid #ef4444; border-radius: 10px; padding: 14px; margin-bottom: 14px; box-shadow: 0 4px 15px rgba(239, 68, 68, 0.2);">
                        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #450a0a; padding-bottom: 8px; margin-bottom: 10px; flex-wrap:wrap; gap:8px;">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span style="font-size:18px;">🚨</span>
                                <div>
                                    <span style="font-weight:bold; color:#fca5a5; font-size:13.5px;">کالبدشکافی پرریسک‌ترین سلاطین (بیشترین تعداد استاپ و زیان دلاری):</span>
                                    <span style="font-size:11px; color:#cbd5e1; margin-right:6px;">سلاطین قرمز رنگ زیر بیشترین حجم ضرر را تولید می‌کنند؛ با یک کلیک می‌توانید آنها را حذف کنید:</span>
                                </div>
                            </div>
                            <div style="display:flex; gap:6px; flex-wrap:wrap;">
                                <button id="btnRemoveTop3Cnt" onclick="toggleTop3SL('cnt')" style="background:#7f1d1d; border:1px solid #ef4444; color:#fff; font-size:11px; padding:5px 12px; border-radius:5px; cursor:pointer; font-weight:bold; transition:all 0.2s;">
                                    🚫 حذف ۳ سلطان با بیشترین استاپ (تعداد)
                                </button>
                                <button id="btnRemoveTop3Usd" onclick="toggleTop3SL('usd')" style="background:#450a0a; border:1px solid #dc2626; color:#fca5a5; font-size:11px; padding:5px 12px; border-radius:5px; cursor:pointer; font-weight:bold; transition:all 0.2s;">
                                    💸 حذف ۳ سلطان با بیشترین زیان دلاری
                                </button>
                                <button id="btnRemoveWorstRate" onclick="toggleWorstRateKings()" style="background:#3b0764; border:1px solid #a855f7; color:#e9d5ff; font-size:11px; padding:5px 12px; border-radius:5px; cursor:pointer; font-weight:bold; transition:all 0.2s;" title="حذف الگوهایی با نرخ باخت نزدیک به ۵۰٪ مثل S-RS و RS-BE">
                                    🛡️ حذف سلاطین کم‌دقت (باخت > ۴۵٪)
                                </button>
                            </div>
                        </div>

                        <!-- Top Stop Loss Cards Grid -->
                        <div id="slTop3CardsContainer" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:10px;">
                            <!-- Dynamically generated by JS -->
                        </div>
                    </div>
            </div>

            <!-- SUBPANEL 4: WEEKLY P&L BARS -->
            <div id="eq-sub-weekly" class="eq-subpanel" style="display:none;">
                <!-- Interactive Weekly P&L Bar Chart Container -->
            <div class="section-box" style="border:1px solid #10b981;background:#0b0f19;padding:10px 14px;margin-bottom:10px;border-radius:8px;">
                <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e293b;padding-bottom:8px;margin-bottom:10px;flex-wrap:wrap;gap:12px;">
                    <div>
                        <h3 style="margin:0;color:#10b981;font-size:15px;display:flex;align-items:center;gap:6px;">
                            <span>📊 نمودار میله‌ای سود و زیان هفته به هفته (Weekly Net Profit & Loss)</span>
                        </h3>
                        <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">توزیع عملکرد دلاری {total_weeks} هفته متوالی - میله‌های سبز نشان‌دهنده سوددهی هفتگی و میله‌های قرمز نشان‌دهنده هفته‌های اصلاحی هستند:</p>
                    </div>
                    <div style="display:flex;gap:8px;">
                        <button id="btnWkKings" class="sort-btn active" onclick="switchWeeklyBarMode('kings')">👑 سلاطین {len(qualified_kings)} گانه</button>
                        <button id="btnWkAll" class="sort-btn" onclick="switchWeeklyBarMode('all')">🌐 کل معاملات چارت</button>
                    </div>
                </div>

                <!-- Canvas Box -->
                <div style="position:relative;width:100%;height:340px;background:#0f172a;border:1px solid #1e293b;border-radius:10px;overflow:hidden;">
                    <canvas id="weeklyBarCanvas" style="width:100%;height:100%;display:block;cursor:pointer;"></canvas>
                    <div id="weeklyBarTooltip" style="display:none;position:absolute;pointer-events:none;background:rgba(15,23,42,0.95);border:1px solid #10b981;padding:10px 14px;border-radius:8px;font-size:12px;color:#f1f5f9;box-shadow:0 8px 24px rgba(0,0,0,0.7);z-index:20;direction:rtl;min-width:220px;"></div>
                </div>

                <!-- Legend & Summary -->
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:14px;font-size:12px;color:#94a3b8;flex-wrap:wrap;gap:10px;">
                    <div style="display:flex;align-items:center;gap:16px;">
                        <span style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:12px;height:12px;background:#00e676;border-radius:2px;"></span> هفته سودده (Green Week)</span>
                        <span style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:12px;height:12px;background:#ef4444;border-radius:2px;"></span> هفته زیان‌ده (Red Week)</span>
                        <span style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:14px;height:2px;background:#64748b;"></span> خط تراز صفر ($0)</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:12px;">
                        <span>تعداد کل هفته‌ها: <b style="color:#f1f5f9;">{total_weeks} هفته</b></span>
                        <span>|</span>
                        <span>هفته‌های سودده: <b style="color:#00e676;">{tot_kings_green_wks} هفته ({tot_kings_green_wks/(total_weeks or 1)*100:.1f}٪)</b></span>
                        <span>|</span>
                        <span>هفته‌های زیان‌ده: <b style="color:#ef4444;">{tot_kings_red_wks} هفته ({tot_kings_red_wks/(total_weeks or 1)*100:.1f}٪)</b></span>
                    </div>
                </div>
            </div>
            </div>

            <!-- SUBPANEL 5: COMPARISON TABLE -->
            <div id="eq-sub-compare" class="eq-subpanel" style="display:none;">
                <!-- Comparison Table: Kings vs All -->
            <div class="section-box" style="border:1px solid #475569;background:#1e293b;">
                <div style="border-bottom:1px solid #334155;padding-bottom:10px;margin-bottom:14px;">
                    <h4 style="margin:0;color:#e2e8f0;font-size:16px;">⚖️ مقایسه شاخص‌های کلیدی منحنی رشد: سلاطین منتخب در برابر کل معاملات خام چارت</h4>
                </div>
                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#0f172a;color:#94a3b8;">
                                <th>استراتژی و دامنه ساختارها</th>
                                <th style="text-align:center;">تعداد کل معامله</th>
                                <th style="text-align:center;">بالانس اولیه</th>
                                <th style="text-align:center;">بالانس نهایی</th>
                                <th style="text-align:center;">سود خالص دلاری ($)</th>
                                <th style="text-align:center;">درصد رشد حساب</th>
                                <th style="text-align:center;">حداکثر افت (Max Drawdown)</th>
                                <th style="text-align:center;">قضاوت عملکرد</th>
                            </tr>
                        </thead>
                        <tbody id="eqCompareTableBody">
                            <tr style="border-bottom:1px solid #334155;">
                                <td style="font-weight:bold;color:#facc15;">👑 سبد سلاطین {len(qualified_kings)} گانه (گزینش هوشمند)</td>
                                <td style="text-align:center;font-weight:bold;">{len(pts_kings)-1}</td>
                                <td style="text-align:center;">${bal_initial:,.0f}</td>
                                <td style="text-align:center;font-weight:bold;color:#00e676;">${bal_k:,.0f}</td>
                                <td style="text-align:center;font-weight:bold;color:#00e676;">{'+$' if net_k>=0 else '-$'}{abs(net_k):,.0f}</td>
                                <td style="text-align:center;font-weight:bold;color:#00e676;">{net_k_pct:+.1f}٪</td>
                                <td style="text-align:center;color:#34d399;font-weight:bold;">${max_dd_k:.0f} ({max_dd_k_pct:.1f}٪)</td>
                                <td style="text-align:center;"><span style="background:#064e3b;color:#34d399;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">💎 رشد مستمر و اکوئیتی صعودی</span></td>
                            </tr>
                            <tr>
                                <td style="font-weight:bold;color:#94a3b8;">🌐 کل ساختارهای خام چارت (بدون فیلتر)</td>
                                <td style="text-align:center;font-weight:bold;">{len(pts_all)-1}</td>
                                <td style="text-align:center;">${bal_initial:,.0f}</td>
                                <td style="text-align:center;font-weight:bold;color:{'#00e676' if net_a>=0 else '#ef4444'};">${bal_a:,.0f}</td>
                                <td style="text-align:center;font-weight:bold;color:{'#00e676' if net_a>=0 else '#ef4444'};">{'+$' if net_a>=0 else '-$'}{abs(net_a):,.0f}</td>
                                <td style="text-align:center;font-weight:bold;color:{'#00e676' if net_a>=0 else '#ef4444'};">{net_a_pct:+.1f}٪</td>
                                <td style="text-align:center;color:#ef4444;font-weight:bold;">${max_dd_a:.0f} ({max_dd_a_pct:.1f}٪)</td>
                                <td style="text-align:center;"><span style="background:#451a03;color:#fca5a5;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">⚠️ فرسایش ناشی از نویزها</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
</div>
</div>"""
    return tab_equity_html



def render_kings_tab(c):
    qualified_kings = c['qualified_kings']
    inter_map = c['inter_map']
    master_map = c['master_map']
    mp_intersection_list = c['mp_intersection_list']
    mp_period_data = c['mp_period_data']
    period_configs = c['period_configs']
    history_span_title = c['history_span_title']
    date_start_str = c['date_start_str']
    date_end_str = c['date_end_str']
    total_setups = c['total_setups']
    pending = c['pending']
    in_trade = c['in_trade']
    closed = c['closed']
    tot_k_cnt = c['tot_k_cnt']
    tot_k_gross = c['tot_k_gross']
    tot_k_fric = c['tot_k_fric']
    tot_k_net = c['tot_k_net']
    s3_net = c['s3_net']
    d_tot_kings = c['d_tot_kings']
    ev_a = c['ev_a']
    ev_b = c['ev_b']
    symbol_latency_all = c['symbol_latency_all']
    w1_p = c['w1_p']
    overlap_count = c.get('overlap_count', 0)
    master_only_count = c.get('master_only_count', 0)
    overlap_ratio = c.get('overlap_ratio', 0.0)

    kings_rows_html = []
    medals = ['🥇', '🥈', '🥉', '👑', '👑', '⭐', '⭐', '⭐', '⭐', '⭐']
    for idx, k in enumerate(qualified_kings, 1):
        rank_icon = medals[idx-1] if idx <= len(medals) else f"#{idx}"
        kk_cur = f"{k['role']}|{k['tf']}"
        badge_html = ""
        if kk_cur in inter_map:
            i_idx, _ = inter_map[kk_cur]
            badge_html += f" <span style='background:#064e3b;color:#34d399;font-size:10px;padding:2px 6px;border-radius:4px;border:1px solid #059669;' title='تایید استقامت در تمام فصول (رتبه #{i_idx})'>💎 اشتراک طلایی #{i_idx}</span>"
        else:
            badge_html += " <span style='background:#451a03;color:#fca5a5;font-size:10px;padding:2px 6px;border-radius:4px;border:1px solid #991b1b;' title='سودآور در کل تاریخچه، دارای نوسان یا افت در برخی فصول'>⚠️ نوسان فصلی</span>"

        if k['is_perfect']:
            badge_html += " <span style='background:#064e3b;color:#34d399;font-size:10px;padding:2px 5px;border-radius:4px;border:1px solid #059669;'>💎 ۱۰۰٪ قطعی</span>"
        elif k['is_runner']:
            badge_html += " <span style='background:#312e81;color:#a5b4fc;font-size:10px;padding:2px 5px;border-radius:4px;border:1px solid #4338ca;'>🚀 دونده</span>"

        net_col = "#00e676" if k['net'] >= 0 else "#ef4444"
        pf = k['pf']
        pf_str = "<span style='color:#00e676;'>MAX</span>" if pf >= 90 else f"{pf:.2f}"
        max_dd = k['max_dd']
        dd_col = "#00e676" if max_dd == 0 else ("#fbbf24" if max_dd <= 25 else "#f87171")
        ret_dd = k['ret_dd']
        ret_str = f"{ret_dd:.1f}x"

        kings_rows_html.append(f"""
        <tr>
            <td style="text-align:center;font-size:16px;font-weight:bold;">{rank_icon}</td>
            <td style="color:#38bdf8;font-weight:bold;text-align:center;font-size:14px;">{k['tf']}</td>
            <td style="color:#facc15;font-weight:bold;font-size:14px;">{k['role']}{badge_html}</td>
            <td style="text-align:center;color:#facc15;font-weight:bold;font-size:14px;background:#1e293b;">{k['score']:.1f}</td>
            <td style="text-align:center;font-weight:bold;">{k['cnt']}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{k['w1_p']:.1f}%</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{k['w2_p']:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;">{k['w3_p']:.1f}%</td>
            <td style="text-align:center;color:#c084fc;">{k['w4_p']:.1f}%</td>
            <td style="text-align:center;color:#ef4444;font-weight:bold;">{k['sl_p']:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;font-size:13px;">{pf_str}</td>
            <td style="text-align:center;color:{dd_col};font-weight:bold;font-size:13px;">${max_dd:.2f}</td>
            <td style="text-align:center;color:#facc15;font-weight:bold;font-size:13px;">{ret_str}</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;font-size:13px;">${k['gross']:+.2f}</td>
            <td style="text-align:center;color:#f87171;font-weight:bold;font-size:13px;">${k['fric']:.2f}-</td>
            <td style="text-align:center;color:{net_col};font-weight:bold;font-size:15px;background:#064e3b22;">${k['net']:+.2f} دلار</td>
        </tr>
        """)

    # 2. Generate HTML for Intersection Table Rows with Master Rank Column
    mp_intersection_rows_html = []
    for idx, k in enumerate(mp_intersection_list, 1):
        k_tag = "👑 سلطان" if k['is_king'] else "سایر"
        k_color = "#facc15" if k['is_king'] else "#94a3b8"
        pnl_col = "#00e676" if k['net'] >= 0 else "#ef4444"
        badge = "💎 الماس ضدضربه" if k['score'] >= 90 else ("⭐ طلایی همه‌فصول" if k['score'] >= 80 else "🟢 باثبات دائم")
        badge_bg = "#064e3b" if k['score'] >= 90 else ("#1e3a8a" if k['score'] >= 80 else "#451a03")
        badge_col = "#34d399" if k['score'] >= 90 else ("#93c5fd" if k['score'] >= 80 else "#fca5a5")

        m_idx, m_info = master_map.get(k['kk'], (None, None))
        if m_idx:
            m_rank_html = f'<span style="color:#facc15;font-weight:bold;">👑 رتبه #{m_idx} <span style="font-size:11px;color:#94a3b8;">({m_info["score"]:.1f})</span></span>'
        else:
            m_rank_html = '<span style="color:#94a3b8;">---</span>'

        mp_intersection_rows_html.append(f"""
        <tr class="mp-row" data-tf="{k['tf']}" style="border-bottom:1px solid #1e293b;">
            <td style="text-align:center;font-weight:bold;color:#94a3b8;">#{idx}</td>
            <td style="text-align:center;">{m_rank_html}</td>
            <td style="font-weight:bold;color:{k_color};">{k['b_key']}</td>
            <td style="text-align:center;"><span style="background:{'#854d0e' if k['is_king'] else '#1e293b'};color:{k_color};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">{k_tag}</span></td>
            <td style="text-align:center;font-weight:bold;color:#38bdf8;font-size:14px;background:#0c253d;">{k['score']:.1f}</td>
            <td style="text-align:center;color:#34d399;font-weight:bold;">{k['b1']['green']}/{k['b1']['active_p']} ({k['b1']['cons']:.0f}%)</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">{k['b3']['green']}/{k['b3']['active_p']} ({k['b3']['cons']:.0f}%)</td>
            <td style="text-align:center;color:#c084fc;font-weight:bold;">{k['b6']['green']}/{k['b6']['active_p']} ({k['b6']['cons']:.0f}%)</td>
            <td style="text-align:center;color:#fbbf24;font-weight:bold;">{k['b1y']['green']}/{k['b1y']['active_p']} ({k['b1y']['cons']:.0f}%)</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{k['wr']:.1f}%</td>
            <td style="text-align:center;color:#ef4444;">{k['sl_r']:.1f}%</td>
            <td style="text-align:center;font-weight:bold;">{k['trades']}</td>
            <td style="text-align:center;font-weight:bold;color:{pnl_col};font-size:13.5px;">${k['net']:+.2f}</td>
            <td style="text-align:center;"><span style="background:{badge_bg};color:{badge_col};padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">{badge}</span></td>
        </tr>
        """)

    if not mp_intersection_rows_html:
        mp_intersection_rows_html.append(f"""
        <tr>
            <td colspan="14" style="text-align:center;padding:26px 14px;color:#94a3b8;font-size:12.5px;background:#0d1527;">
                <div style="font-size:22px;margin-bottom:6px;">ℹ️</div>
                <b>در بازه تاریخی فعلی ({history_span_title})، افق‌های بلندمدت چندگانه به دلیل کوتاه‌تر بودن تاریخچه آزمون فعال نشده‌اند.</b><br>
                <span style="color:#facc15;display:inline-block;margin-top:6px;font-size:12px;">برای مشاهده {len(qualified_kings)} سلطان منتخب و عملکرد سودآوری آنها، از دکمه تب <b>«🏛️ جدول جامع رتبه‌بندی شاخص سلطان ({len(qualified_kings)} سلطان)»</b> در بالای همین جدول استفاده کنید.</span>
            </td>
        </tr>
        """)

    # 3. Generate HTML for Comparison Matrix View (All-Time vs All-Weather)
    compare_rows_html = []
    for m_idx, k in enumerate(qualified_kings, 1):
        kk = f"{k['role']}|{k['tf']}"
        b_name = f"{k['role']} [{k['tf']}]"
        in_inter = kk in inter_map
        pnl_col = "#00e676" if k['net'] >= 0 else "#ef4444"

        if in_inter:
            i_idx, i_k = inter_map[kk]
            status_html = '<span style="background:#064e3b;color:#34d399;padding:3px 8px;border-radius:5px;font-size:11px;font-weight:bold;border:1px solid #059669;">💎 تایید دوگانه (سلطان الماس)</span>'
            i_rank_html = f'<span style="color:#38bdf8;font-weight:bold;font-size:13px;">#{i_idx}</span>'
            score_all_w = f"{i_k['score']:.1f}"
            cons_1m = f"{i_k['b1']['cons']:.0f}% ({i_k['b1']['green']}/{i_k['b1']['active_p']})"
            cons_3m = f"{i_k['b3']['cons']:.0f}% ({i_k['b3']['green']}/{i_k['b3']['active_p']})"
            diag_reason = "✅ سودآوری پیوسته در تمام فصول، استقامت بالا در برابر تغییر فاز بازار"
            ea_rec = '<span style="background:#064e3b;color:#34d399;padding:3px 8px;border-radius:5px;font-size:11px;font-weight:bold;">🟢 تایید لایو (سپر ضدضربه)</span>'
        else:
            status_html = '<span style="background:#451a03;color:#fca5a5;padding:3px 8px;border-radius:5px;font-size:11px;font-weight:bold;border:1px solid #991b1b;">⚠️ فقط جدول جامع (نوسان فصلی)</span>'
            i_rank_html = '<span style="color:#94a3b8;">---</span>'
            score_all_w = '<span style="color:#94a3b8;">---</span>'
            b1 = next((x for x in mp_period_data['1M']['boxes'] if x['kk'] == kk), None)
            b3 = next((x for x in mp_period_data['3M']['boxes'] if x['kk'] == kk), None)
            cons_1m = f"{b1['cons']:.0f}%" if b1 else "---"
            cons_3m = f"{b3['cons']:.0f}%" if b3 else "---"
            if k['net'] < 20:
                diag_reason = f"⚠️ سود خالص دلاری (${k['net']:.2f}) زیر آستانه ۲۰ دلار اشتراک"
            elif k['sl_p'] >= 40:
                diag_reason = f"⚠️ نرخ استاپ بالا ({k['sl_p']:.1f}٪) و آسیب‌پذیری در فصول رکود"
            elif k['pf'] < 1.6:
                diag_reason = f"⚠️ پرافیت فاکتور لب‌مرزی ({k['pf']:.2f})"
            else:
                diag_reason = "⚠️ افت بازدهی در دوره‌های رکود فصلی (ثبات فصلی زیر ۶۰٪)"
            ea_rec = '<span style="background:#854d0e;color:#fef08a;padding:3px 8px;border-radius:5px;font-size:11px;font-weight:bold;">🟡 فقط مد تهاجمی (Aggressive)</span>'

        compare_rows_html.append(f"""
        <tr class="mp-row" data-tf="{k['tf']}" style="border-bottom:1px solid #1e293b;">
            <td style="text-align:center;font-weight:bold;color:#facc15;font-size:13.5px;">#{m_idx}</td>
            <td style="text-align:center;">{i_rank_html}</td>
            <td style="font-weight:bold;color:#e2e8f0;">{b_name}</td>
            <td style="text-align:center;">{status_html}</td>
            <td style="text-align:center;color:#facc15;font-weight:bold;background:#1e293b;">{k['score']:.1f}</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">{score_all_w}</td>
            <td style="text-align:center;color:#34d399;font-weight:bold;">{cons_1m}</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">{cons_3m}</td>
            <td style="text-align:center;color:#00e676;font-weight:bold;">{k['w1_p']:.1f}%</td>
            <td style="text-align:center;color:#38bdf8;font-weight:bold;">{k['pf']:.2f}</td>
            <td style="text-align:center;font-weight:bold;color:{pnl_col};">${k['net']:+.2f}</td>
            <td style="font-size:11.5px;color:#cbd5e1;line-height:1.4;">{diag_reason}</td>
            <td style="text-align:center;">{ea_rec}</td>
        </tr>
        """)

    # 4. Generate HTML for each Horizon's Table Rows (1M, 2M, 3M, 6M, 9M, 1Y, 2Y, 3Y)
    mp_tables_html = {}
    for pt, _, _ in period_configs:
        b_rows = []
        for idx, b in enumerate(mp_period_data[pt]['boxes'], 1):
            k_tag = "👑 سلطان" if b['is_king'] else "سایر"
            k_color = "#facc15" if b['is_king'] else "#94a3b8"
            pnl_col = "#00e676" if b['net'] >= 0 else "#ef4444"
            prog_col = "#10b981" if b['cons'] >= 75 else ("#38bdf8" if b['cons'] >= 60 else "#f59e0b")
            badge = "💎 عالی" if b['cons'] >= 80 else ("⭐ خوب" if b['cons'] >= 65 else "⚠️ نوسانی")
            badge_bg = "#064e3b" if b['cons'] >= 80 else ("#1e3a8a" if b['cons'] >= 65 else "#451a03")
            badge_col = "#34d399" if b['cons'] >= 80 else ("#93c5fd" if b['cons'] >= 65 else "#fca5a5")

            b_rows.append(f"""
            <tr class="mp-row" data-tf="{b['tf']}" style="border-bottom:1px solid #1e293b;">
                <td style="text-align:center;font-weight:bold;color:#94a3b8;">#{idx}</td>
                <td style="font-weight:bold;color:{k_color};">{b['b_key']}</td>
                <td style="text-align:center;"><span style="background:{'#854d0e' if b['is_king'] else '#1e293b'};color:{k_color};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">{k_tag}</span></td>
                <td style="text-align:center;">
                    <div style="display:flex;align-items:center;gap:8px;justify-content:center;">
                        <span style="font-weight:bold;color:{prog_col};min-width:42px;">{b['cons']:.1f}%</span>
                        <div style="width:70px;background:#1e293b;border-radius:10px;height:7px;overflow:hidden;border:1px solid #334155;">
                            <div style="width:{b['cons']}%;background:{prog_col};height:100%;"></div>
                        </div>
                    </div>
                </td>
                <td style="text-align:center;color:#34d399;font-weight:bold;">{b['green']} از {b['active_p']} دوره 🟢</td>
                <td style="text-align:center;color:#ef4444;font-weight:bold;">{b['red']} 🔴</td>
                <td style="text-align:center;color:#00e676;font-weight:bold;">{b['wr']:.1f}%</td>
                <td style="text-align:center;color:#ef4444;">{b['sl_r']:.1f}%</td>
                <td style="text-align:center;font-weight:bold;">{b['trades']}</td>
                <td style="text-align:center;font-weight:bold;color:{pnl_col};font-size:13.5px;">${b['net']:+.2f}</td>
                <td style="text-align:center;"><span style="background:{badge_bg};color:{badge_col};padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">{badge}</span></td>
            </tr>
            """)
        
        mp_tables_html[pt] = "".join(b_rows)

    # 5. Build Horizon Panels List
    mp_panels_list = []
    for pt, _, _ in period_configs:
        p_info = mp_period_data[pt]
        mp_panels_list.append(f"""
        <div id="panel-horizon-{pt}" class="horizon-view-panel" style="display:none;">
            <div class="section-box" style="border: 1px solid #38bdf8; background: #0c182c; margin-bottom: 0;">
                <div style="border-bottom: 1px solid #1e3a5f; padding-bottom: 14px; margin-bottom: 16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <h3 style="margin:0;color:#38bdf8;font-size:18px;display:flex;align-items:center;gap:8px;">
                            <span>📅</span> جدول رتبه‌بندی سلاطین در {p_info['title']} ({p_info['tot_p']} دوره)
                        </h3>
                        <p style="margin:4px 0 0 0;color:#94a3b8;font-size:12px;">{p_info['desc']}:</p>
                    </div>
                    <span style="background:#0c4a6e;color:#7dd3fc;font-size:12px;padding:4px 10px;border-radius:8px;font-weight:bold;">
                        📊 {len(p_info['boxes'])} الگوی فعال در این افق
                    </span>
                </div>

                <div style="overflow-x:auto;">
                    <table style="width:100%;font-size:12.5px;">
                        <thead>
                            <tr style="background:#1e293b;">
                                <th style="text-align:center;">رتبه</th>
                                <th>نام ساختار / تلاقی گره</th>
                                <th style="text-align:center;">وضعیت</th>
                                <th style="text-align:center;color:#38bdf8;">پایداری دوره‌ای (Consistency)</th>
                                <th style="text-align:center;color:#34d399;">دوره‌های مثبت (سبز)</th>
                                <th style="text-align:center;color:#ef4444;">دوره‌های منفی (قرمز)</th>
                                <th style="text-align:center;color:#00e676;">وین‌ریت TP1</th>
                                <th style="text-align:center;color:#ef4444;">نرخ باخت (SL)</th>
                                <th style="text-align:center;">تعداد ترید</th>
                                <th style="text-align:center;color:#00e676;background:#064e3b44;">سود خالص واقعی</th>
                                <th style="text-align:center;">ارزیابی</th>
                            </tr>
                        </thead>
                        <tbody>
                            {mp_tables_html[pt]}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        """)

    # 6. Horizon Pill Buttons (Dynamic for 1M to 3Y)
    horizon_pills_html = f"""
                <button class="horizon-pill-btn active" onclick="showHorizonView('INTERSECTION', this)" style="background:#0284c7;border:1px solid #38bdf8;color:#fff;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;box-shadow:0 0 10px rgba(56,189,248,0.3);">
                    🌟 اشتراک طلایی (همه‌فصول)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('1M', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۱ ماهه ({mp_period_data['1M']['tot_p']} دوره)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('2M', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۲ ماهه ({mp_period_data['2M']['tot_p']} دوره)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('3M', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۳ ماهه / فصلی ({mp_period_data['3M']['tot_p']} فصل)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('6M', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۶ ماهه / نیم‌سال ({mp_period_data['6M']['tot_p']} دوره)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('9M', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۹ ماهه ({mp_period_data['9M']['tot_p']} دوره)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('1Y', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۱ ساله ({mp_period_data['1Y']['tot_p']} دوره)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('2Y', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۲ ساله ({mp_period_data['2Y']['tot_p']} دوره)
                </button>
                <button class="horizon-pill-btn" onclick="showHorizonView('3Y', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;font-weight:bold;">
                    📅 ۳ ساله ({mp_period_data['3Y']['tot_p']} دوره)
                </button>
    """

    has_intersection = (len(mp_intersection_list) > 0)
    btn_multi_cls = "kings-sub-btn active" if has_intersection else "kings-sub-btn"
    btn_multi_style = "background:#0284c7;border:1px solid #38bdf8;color:#fff;box-shadow:0 0 12px rgba(56,189,248,0.3);" if has_intersection else "background:#0f172a;border:1px solid #334155;color:#94a3b8;box-shadow:none;"

    btn_all_cls = "kings-sub-btn" if has_intersection else "kings-sub-btn active"
    btn_all_style = "background:#0f172a;border:1px solid #334155;color:#94a3b8;box-shadow:none;" if has_intersection else "background:#0284c7;border:1px solid #38bdf8;color:#fff;box-shadow:0 0 12px rgba(56,189,248,0.3);"

    disp_multi = "block" if has_intersection else "none"
    disp_all = "none" if has_intersection else "block"

    mp_full_html_section = f"""
    <!-- Sub-Navigation Toggle for Kings View (3 Sub-Views) -->
    <div style="display:flex;gap:10px;margin-bottom:18px;border-bottom:1px solid #334155;padding-bottom:12px;flex-wrap:wrap;align-items:center;justify-content:space-between;">
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button class="{btn_multi_cls}" id="btnKingsMulti" onclick="switchKingsSubView('multi', this)" style="{btn_multi_style}padding:8px 16px;border-radius:6px;font-size:12.5px;cursor:pointer;font-weight:bold;display:flex;align-items:center;gap:6px;">
                <span>🌟</span> کالبدشکافی چندبازه‌ای و اشتراک طلایی (1M تا 3Y)
            </button>
            <button class="{btn_all_cls}" id="btnKingsAllTime" onclick="switchKingsSubView('alltime', this)" style="{btn_all_style}padding:8px 16px;border-radius:6px;font-size:12.5px;cursor:pointer;font-weight:bold;display:flex;align-items:center;gap:6px;">
                <span>🏛️</span> جدول جامع رتبه‌بندی شاخص سلطان ({len(qualified_kings)} سلطان - {history_span_title})
            </button>
            <button class="kings-sub-btn" id="btnKingsCompare" onclick="switchKingsSubView('compare', this)" style="background:#0f172a;border:1px solid #334155;color:#94a3b8;padding:8px 16px;border-radius:6px;font-size:12.5px;cursor:pointer;font-weight:bold;display:flex;align-items:center;gap:6px;">
                <span>⚖️</span> ماتریس تطبیق و مقایسه دو جدول (All-Time vs All-Weather)
            </button>
        </div>
        <div style="font-size:11.5px;color:#94a3b8;">
            کالبدشکافی پیوسته تمام دوره‌ها از <b>{date_start_str} تا {date_end_str}</b> ({history_span_title})
        </div>
    </div>

    <!-- VIEW 1: MULTI-PERIOD & GOLDEN INTERSECTION -->
    <div id="kingsViewMulti" style="display:{disp_multi};">
        <!-- Controls Bar: Horizon Switcher & Timeframe Filter -->
        <div style="background:#0b1322;border:1px solid #1e3a5f;border-radius:10px;padding:14px;margin-bottom:18px;box-shadow:0 4px 15px rgba(0,0,0,0.3);">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:12px;">
                <div>
                    <h4 style="margin:0;color:#facc15;font-size:15px;display:flex;align-items:center;gap:6px;">
                        <span>⏱️</span> انتخاب افق زمانی کالبدشکافی پایداری سلاطین (۱ ماه تا ۳ سال):
                    </h4>
                    <p style="margin:4px 0 0 0;color:#94a3b8;font-size:11.5px;">
                        سنجش استقامت و ثبات سودآوری الگوها در دوره‌های ۱ ماهه، ۲ ماهه، فصلی، نیم‌سال، ۹ ماهه، سالانه، ۲ ساله، ۳ ساله و اشتراک همه‌فصول:
                    </p>
                </div>
                <!-- Timeframe Filter Pills -->
                <div style="display:flex;align-items:center;gap:6px;background:#081424;padding:4px 8px;border-radius:6px;border:1px solid #1e293b;">
                    <span style="font-size:11px;color:#94a3b8;font-weight:bold;">فیلتر تایم:</span>
                    <button class="tf-filter-btn active" onclick="filterHorizonTF('ALL', this)" style="background:#0284c7;color:#fff;border:none;padding:3px 9px;border-radius:4px;font-size:11px;cursor:pointer;font-weight:bold;">همه</button>
                    <button class="tf-filter-btn" onclick="filterHorizonTF('M15', this)" style="background:#1e293b;color:#94a3b8;border:none;padding:3px 9px;border-radius:4px;font-size:11px;cursor:pointer;">M15</button>
                    <button class="tf-filter-btn" onclick="filterHorizonTF('M5', this)" style="background:#1e293b;color:#94a3b8;border:none;padding:3px 9px;border-radius:4px;font-size:11px;cursor:pointer;">M5</button>
                    <button class="tf-filter-btn" onclick="filterHorizonTF('M1', this)" style="background:#1e293b;color:#94a3b8;border:none;padding:3px 9px;border-radius:4px;font-size:11px;cursor:pointer;">M1</button>
                </div>
            </div>

            <!-- Horizon Pill Buttons -->
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
                {horizon_pills_html}
            </div>
        </div>

        <!-- Panel: All-Weather Golden Intersection -->
        <div id="panel-horizon-INTERSECTION" class="horizon-view-panel" style="display:block;">
            <div class="section-box" style="border: 1px solid #facc15; background: #131b2e; margin-bottom: 0;">
                <div style="border-bottom: 1px solid #854d0e; padding-bottom: 14px; margin-bottom: 16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <h3 style="margin:0;color:#facc15;font-size:19px;display:flex;align-items:center;gap:8px;">
                            <span>👑</span> جدول اشتراک طلایی سلاطین همه‌فصول (All-Weather Golden Intersection)
                        </h3>
                        <p style="margin:4px 0 0 0;color:#fef08a;font-size:12px;">
                            این الگوها در <b>تک‌تک افق‌های کوتاه‌مدت (۱ ماهه)، فصلی (۳ ماهه)، نیم‌سال (۶ ماهه) و سالانه (۱ ساله)</b> همواره سبز، پایدار و با کمترین نوسان دراداون بوده‌اند:
                        </p>
                    </div>
                    <span style="background:#854d0e;color:#fef08a;font-size:12px;padding:4px 10px;border-radius:8px;font-weight:bold;">
                        🏆 {len(mp_intersection_list)} سلطان ضدضربه
                    </span>
                </div>

                <div style="overflow-x:auto;">
                    <table style="width:100%;font-size:12.5px;">
                        <thead>
                            <tr style="background:#1e293b;">
                                <th style="text-align:center;">رتبه اشتراک</th>
                                <th style="text-align:center;">رتبه در جدول جامع</th>
                                <th>نام ساختار / تلاقی گره</th>
                                <th style="text-align:center;">وضعیت</th>
                                <th style="text-align:center;color:#38bdf8;" title="امتیاز پایداری ترکیبی در تمام افق‌های زمانی">شاخص همه‌فصول (Score)</th>
                                <th style="text-align:center;color:#34d399;">ثبات ۱ ماهه (1M)</th>
                                <th style="text-align:center;color:#38bdf8;">ثبات فصلی (3M)</th>
                                <th style="text-align:center;color:#c084fc;">ثبات نیم‌سال (6M)</th>
                                <th style="text-align:center;color:#fbbf24;">ثبات سالانه (1Y)</th>
                                <th style="text-align:center;color:#00e676;">وین‌ریت کلی</th>
                                <th style="text-align:center;color:#ef4444;">نرخ استاپ</th>
                                <th style="text-align:center;">تعداد ترید</th>
                                <th style="text-align:center;color:#00e676;background:#064e3b44;">سود خالص واقعی</th>
                                <th style="text-align:center;">ارزیابی پایداری</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(mp_intersection_rows_html)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        {''.join(mp_panels_list)}
    </div> <!-- End kingsViewMulti -->

    <!-- VIEW 3: DEDICATED CROSS-VERIFICATION & OVERLAP MATRIX -->
    <div id="kingsViewCompare" style="display:none;">
        <!-- KPI Comparison Summary Cards -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:14px;margin-bottom:18px;">
            <div style="background:#07271e;border:1px solid #059669;border-radius:10px;padding:16px;box-shadow:0 4px 15px rgba(0,0,0,0.3);">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <span style="font-size:24px;">💎</span>
                    <div>
                        <div style="font-size:12px;color:#34d399;font-weight:bold;">سلاطین الماس مشترک (هردو جدول)</div>
                        <div style="font-size:22px;color:#fff;font-weight:bold;">{overlap_count} الگو ({overlap_ratio:.0f}٪ کل سلاطین)</div>
                    </div>
                </div>
                <div style="font-size:11.5px;color:#a7f3d0;line-height:1.6;">
                    <b>۱۰۰٪ سلاطین اشتراک طلایی در جدول جامع هم حضور دارند!</b> این الگوها آزمون استقامت سودآوری را در تمام ماه‌ها، فصول و سال‌ها با درخشش کامل پاس کرده‌اند.
                </div>
            </div>

            <div style="background:#2a1b05;border:1px solid #d97706;border-radius:10px;padding:16px;box-shadow:0 4px 15px rgba(0,0,0,0.3);">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <span style="font-size:24px;">⚠️</span>
                    <div>
                        <div style="font-size:12px;color:#fcd34d;font-weight:bold;">سلاطین تک‌جدولی (فقط جدول جامع)</div>
                        <div style="font-size:22px;color:#fff;font-weight:bold;">{master_only_count} الگو (سودآور با نوسان فصلی)</div>
                    </div>
                </div>
                <div style="font-size:11.5px;color:#fde68a;line-height:1.6;">
                    در کل تاریخچه بازدهی مثبت ساخته‌اند، اما به دلیل افت در ۱ یا ۲ فصل خاص یا حجم ترید پایین‌تر، در اشتراک فصلی سخت‌گیرانه قرار نگرفتند.
                </div>
            </div>

            <div style="background:#0b1d3a;border:1px solid #0284c7;border-radius:10px;padding:16px;box-shadow:0 4px 15px rgba(0,0,0,0.3);">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <span style="font-size:24px;">🎯</span>
                    <div>
                        <div style="font-size:12px;color:#38bdf8;font-weight:bold;">توصیه اجرایی برای اکسپرت متاتریدر</div>
                        <div style="font-size:20px;color:#fff;font-weight:bold;">سپر کم‌ریسک (Conservative)</div>
                    </div>
                </div>
                <div style="font-size:11.5px;color:#bae6fd;line-height:1.6;">
                    برای حساب‌های لایو با حداقل دراوداون: <b>فقط {overlap_count} سلطان الماس مشترک</b> فعال شوند؛ ۶ الگوی دیگر برای مدهای تهاجمی مناسبند.
                </div>
            </div>
        </div>

        <!-- Analytical Explainer Box -->
        <div style="background:#131c2e;border:1px solid #38bdf8;border-radius:10px;padding:16px;margin-bottom:18px;">
            <h4 style="margin:0 0 8px 0;color:#facc15;font-size:15px;display:flex;align-items:center;gap:8px;">
                <span>🔍</span> کالبدشکافی تطبیق: آیا سلاطین اشتراک طلایی در جدول جامع حضور دارند؟
            </h4>
            <p style="margin:0;color:#cbd5e1;font-size:12.5px;line-height:1.7;">
                <b>پاسخ قطعی و مستند: بله! ۱۰۰٪ سلاطین اشتراک طلایی (تک‌تک {len(mp_intersection_list)} الگو) در جدول جامع سلاطین منتخب نیز رتبه برتر دارند.</b> 
                جدول تطبیقی زیر کالبدشکافی یک‌به‌یک تمام {len(qualified_kings)} سلطان را با رتبه جامع، رتبه اشتراک طلایی، شاخص همه‌فصول، درصد ثبات ماهانه و فصلی، و علت فنی تفاوت نمایش می‌دهد:
            </p>
        </div>

        <!-- Comparison Table -->
        <div class="section-box" style="border:1px solid #38bdf8;background:#0c182c;margin-bottom:0;">
            <div style="overflow-x:auto;">
                <table style="width:100%;font-size:12.5px;">
                    <thead>
                        <tr style="background:#1e293b;">
                            <th style="text-align:center;">رتبه جامع</th>
                            <th style="text-align:center;">رتبه اشتراک</th>
                            <th>نام ساختار / تلاقی گره</th>
                            <th style="text-align:center;">وضعیت انطباق دو جدول</th>
                            <th style="text-align:center;color:#facc15;">امتیاز جامع</th>
                            <th style="text-align:center;color:#38bdf8;">شاخص همه‌فصول</th>
                            <th style="text-align:center;color:#34d399;">ثبات ۱ ماهه</th>
                            <th style="text-align:center;color:#38bdf8;">ثبات فصلی</th>
                            <th style="text-align:center;color:#00e676;">وین‌ریت TP1</th>
                            <th style="text-align:center;color:#38bdf8;">پرافیت فاکتور</th>
                            <th style="text-align:center;color:#00e676;background:#064e3b44;">سود خالص ($)</th>
                            <th>کالبدشکافی فنی و دلیل</th>
                            <th style="text-align:center;">توصیه لایو برای اکسپرت</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(compare_rows_html)}
                    </tbody>
                </table>
            </div>
        </div>
    </div> <!-- End kingsViewCompare -->
    """

    tab_kings_html = f"""<!-- Global Performance KPI Cards (Placed inside Tab 1) -->
            <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(170px, 1fr));gap:10px;margin-bottom:20px;">
                <div class="kpi-card" style="border-top: 4px solid #38bdf8;">
                    <div class="kpi-title">📦 کل الگوهای شناسایی‌شده چارت</div>
                    <div class="kpi-value" style="color:#38bdf8;">{total_setups:,} باکس</div>
                    <div class="kpi-sub">{len(pending):,} منقضی بدون ورود{f" | {len(in_trade)} فعال باز" if len(in_trade) > 0 else ""}</div>
                </div>
                <div class="kpi-card" style="border-top: 4px solid #94a3b8;">
                    <div class="kpi-title">🌐 کل معاملات بسته‌شده چارت</div>
                    <div class="kpi-value" style="color:#e2e8f0;">{len(closed):,} معامله</div>
                    <div class="kpi-sub">مجموع تمام الگوهای فعال چارت</div>
                </div>
                <div class="kpi-card" style="border-top: 4px solid #facc15;background:linear-gradient(180deg, #1c1917, #281d04);">
                    <div class="kpi-title" style="color:#fde047;font-weight:bold;">👑 معاملات ۵ سلطان برگزیده</div>
                    <div class="kpi-value" style="color:#facc15;font-weight:900;">{tot_k_cnt:,} معامله</div>
                    <div class="kpi-sub" style="color:#fef08a;">سود: ${s3_net:+.2f} | وین‌ریت: {d_tot_kings['w1_p']:.1f}٪</div>
                </div>
                <div class="kpi-card" style="border-top: 4px solid #ef4444;">
                    <div class="kpi-title">🚫 الگوهای ردشده با فیلتر سلاطین</div>
                    <div class="kpi-value" style="color:#f87171;">{len(closed) - tot_k_cnt:,} معامله</div>
                    <div class="kpi-sub">حذف الگوهای ناموفق و زیان‌ده چارت</div>
                </div>
                <div class="kpi-card" style="border-top: 4px solid #10b981;">
                    <div class="kpi-title">🚀 جهش امید ریاضی (EV)</div>
                    <div class="kpi-value" style="color:#10b981;">{ev_a:+.2f} R</div>
                    <div class="kpi-sub">قبل از فیلتر: {ev_b:+.2f} R</div>
                </div>
                <div class="kpi-card" style="border-top: 4px solid #a855f7;">
                    <div class="kpi-title">⏱️ میانگین انتظار تا ورود (پولبک)</div>
                    <div class="kpi-value" style="color:#c084fc;">{symbol_latency_all['avg_short']}</div>
                    <div class="kpi-sub">سریع‌ترین: {symbol_latency_all['min_short']} | ۹۰٪ زیر {symbol_latency_all['p90_short']}</div>
                </div>
            </div>

            {mp_full_html_section}

            <!-- VIEW 2: ALL-TIME 7-PILLAR SCORE -->
            <div id="kingsViewAllTime" style="display:{disp_all};">
            <div class="section-box" style="border: 1px solid #eab308; background: #1a1608;">
                <div style="border-bottom: 1px solid #854d0e; padding-bottom: 14px; margin-bottom: 16px;">
                    <h3 style="margin:0;color:#facc15;font-size:20px;">👑 جدول جامع سلاطین منتخب بر مبنای شاخص ترکیبی و تفکیک تایم‌فریم</h3>
                    <p style="margin:4px 0 0 0;color:#fef08a;font-size:12px;">کالبدشکافی پویا از {tot_k_cnt} معامله واقعی سلاطین برتر FlagPro (گزینش با فرمول شاخص سلطان، بونوس ۱۰۰٪ قطعی و الگوهای دونده):</p>
                </div>

                <!-- Formula Highlight Banner -->
                <div style="font-size:12px;color:#fef08a;margin-bottom:16px;background:#261e07;padding:12px 16px;border-radius:8px;border-right:4px solid #facc15;display:flex;align-items:center;justify-content:space-between;flex-wrap:gap;gap:10px;">
                    <div>
                        <b style="color:#facc15;font-size:13px;">🏛️ شاخص ۷ ستونه هج‌فاندی سلطان (7-Pillar Institutional King Score):</b>
                        <span style="direction:ltr;display:inline-block;font-family:monospace;background:#1e293b;padding:3px 10px;border-radius:5px;color:#38bdf8;margin:0 8px;font-size:11.5px;font-weight:bold;">Score = 🛡️خلوص(۵۰۰) + 🎯تارگت۲(۴۰۰) + ⚡پیشروی(۲۵۰) + 💰بهره‌وری(۲۰۰) + 📊اعتبار(۵۰) + ⚖️پرافیت فاکتور(۱۰۰) + 🛡️کنترل افت و ریکاوری(۱۰۰)</span>
                    </div>
                    <div style="display:flex;gap:6px;">
                        <span style="background:#064e3b;color:#34d399;font-size:11px;padding:3px 8px;border-radius:4px;border:1px solid #059669;">👑 ۱۰۰٪ وین‌ریت (+۵۰۰ امتیاز قطعی)</span>
                        <span style="background:#1e3a8a;color:#93c5fd;font-size:11px;padding:3px 8px;border-radius:4px;border:1px solid #3b82f6;">⚖️ کنترل دراوداون و پرافیت فاکتور</span>
                    </div>
                </div>

                <div style="overflow-x:auto;">
                    <table>
                        <thead>
                            <tr style="background:#261e07;">
                                <th style="text-align:center;">رتبه</th>
                                <th style="text-align:center;">تایم‌فریم</th>
                                <th>نام ساختار / تلاقی گره‌ها</th>
                                <th style="text-align:center;color:#facc15;">امتیاز سلطان (Score)</th>
                                <th style="text-align:center;">تعداد معامله</th>
                                <th style="text-align:center;">وین‌ریت TP 1:1</th>
                                <th style="text-align:center;">وین‌ریت TP 1:2</th>
                                <th style="text-align:center;">وین‌ریت TP 1:3</th>
                                <th style="text-align:center;">وین‌ریت TP 1:4</th>
                                <th style="text-align:center;">نرخ باخت (SL)</th>
                                <th style="text-align:center;color:#38bdf8;" title="نسبت سود ناخالص به زیان ناخالص (Profit Factor)">⚖️ پرافیت فاکتور (PF)</th>
                                <th style="text-align:center;color:#f87171;" title="حداکثر افت موقت بالانس در طول معاملات (Max Drawdown)">🛡️ حداکثر افت (Max DD)</th>
                                <th style="text-align:center;color:#facc15;" title="نسبت سود خالص نهایی به حداکثر افت (Recovery Factor)">🚀 بازدهی/افت (Ret/DD)</th>
                                <th style="text-align:center;color:#38bdf8;" title="مجموع سود بدون کسر اسپرد">سود ناخالص (Gross)</th>
                                <th style="text-align:center;color:#f87171;" title="مجموع کل اسپرد و کمیسیون پرداخت شده به ازای هر ترید 0.04 لات ($0.48)">🧾 کل اصطکاک (اسپرد)</th>
                                <th style="text-align:center;color:#00e676;background:#064e3b44;" title="سود قطعی واریزی به حساب بعد از پرداخت کل اسپرد و کمیسیون">💵 سود خالص واقعی (Net)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(kings_rows_html)}
                        </tbody>
                        <tfoot>
                            <tr style="background:#261e07;border-top:2px solid #facc15;font-weight:bold;">
                                <td colspan="4" style="text-align:center;color:#facc15;font-size:14px;">👑 مجموع عملکرد کل سلاطین برگزیده ({len(qualified_kings)} گره برتر)</td>
                                <td style="text-align:center;color:#facc15;font-size:15px;">{tot_k_cnt}</td>
                                <td colspan="8" style="text-align:center;color:#94a3b8;font-size:11px;">مبتنی بر استراتژی خروج چهارپله‌ای 0.04 لات و پایش دقیق دراوداون</td>
                                <td style="text-align:center;color:#38bdf8;font-size:14px;">${tot_k_gross:+.2f}</td>
                                <td style="text-align:center;color:#f87171;font-size:14px;">${tot_k_fric:.2f}-</td>
                                <td style="text-align:center;color:#00e676;font-size:16px;background:#064e3b;">${tot_k_net:+.2f} دلار نقد خالص</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            </div>
            </div> <!-- End kingsViewAllTime -->"""

    return tab_kings_html

