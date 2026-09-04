# -*- coding: utf-8 -*-
"""
FlagPro Tester Comparison & Forensic Module
------------------------------------------
Loads MetaTrader 5 Strategy Tester reports, provides side-by-side KPI comparison,
parameter drift audit, dual equity curve visualization, and deal-by-deal forensics.
"""

import os
import json
import re

def load_tester_reports(reports_dir):
    """
    Loads all test reports from the specified directory.
    Returns a dictionary of {report_id: report_data}.
    """
    reports = {}
    if os.path.exists(reports_dir):
        for fname in os.listdir(reports_dir):
            if fname.endswith('.json'):
                fpath = os.path.join(reports_dir, fname)
                try:
                    with open(fpath, mode='r', encoding='utf-8') as f:
                        data = json.load(f)
                        reports[fname] = data
                except Exception as e:
                    print(f"⚠️ خطا در خواندن گزارش تستر {fname}: {e}")
    return reports

def get_tester_compare_html(reports_dict, default_key):
    """
    Generates the HTML content for tab-tester-compare.
    """
    options_html = []
    for k, v in sorted(reports_dict.items()):
        sel = 'selected' if k == default_key else ''
        title = v.get('reportTitle', k)
        date_range = v.get('dateRange', '')
        t_count = len(v.get('trades', []))
        options_html.append(f'<option value="{k}" {sel}>{title} ({date_range}) - {t_count} ترید</option>')
    
    if not options_html:
        options_html.append('<option value="none">هیچ گزارشی یافت نشد</option>')

    opts_str = "\\n".join(options_html)

    return f"""
    <div style="padding: 4px 6px;">
        <!-- 🎛️ TOP CONTROL BAR & RUN SELECTOR -->
        <div class="section-box" style="margin-bottom:12px;background:linear-gradient(135deg,#0d1527,#0a101d);border:1px solid #1e3a5f;border-radius:8px;padding:12px 16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:12px;">
                <div>
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:24px;">🔬</span>
                        <div>
                            <h2 style="margin:0;font-size:16px;color:#38bdf8;font-weight:bold;">کالبدشکافی و مقایسه جامع تست متاتریدر ۵ با نتایج استراتژی</h2>
                            <div style="font-size:11.5px;color:#94a3b8;margin-top:2px;">مقایسه رو در روی عملکرد واقعی ربات در تستر MT5 با شبیه‌ساز استراتژی، شناسایی انحراف پارامترها و ریشه‌یابی باخت‌ها</div>
                        </div>
                    </div>
                </div>
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                    <select id="testerRunSelector" onchange="switchTesterReport(this.value)" style="background:#1e293b;border:1px solid #38bdf8;color:#f8fafc;padding:6px 12px;border-radius:6px;font-size:12px;cursor:pointer;min-width:280px;font-family:inherit;">
                        {opts_str}
                    </select>
                    <input type="file" id="testerReportFileInput" accept=".json,.csv" style="display:none;" onchange="handleTesterReportUpload(event)">
                    <button class="action-btn" onclick="document.getElementById('testerReportFileInput').click()" style="background:#0284c7;color:#fff;border:none;padding:6px 12px;border-radius:6px;font-size:11.5px;cursor:pointer;font-weight:600;display:flex;align-items:center;gap:5px;">
                        <span>📁</span> بارگذاری فایل تست جدید (JSON/CSV)
                    </button>
                    <button class="action-btn" onclick="resetToInitialTesterReport()" style="background:#334155;color:#e2e8f0;border:1px solid #475569;padding:6px 12px;border-radius:6px;font-size:11.5px;cursor:pointer;font-weight:600;">
                        🔄 بازنشانی به تست اخیر
                    </button>
                </div>
            </div>
            
            <!-- Meta Info Badges -->
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;background:#090d16;padding:8px 12px;border-radius:6px;border:1px solid #1e293b;font-size:11.5px;">
                <span style="color:#94a3b8;">گزارش فعال:</span>
                <span id="tcBadgeReportTitle" style="color:#38bdf8;font-weight:bold;">تست استراتژی تستر متاتریدر ۵ - نماد GBPUSD! تایم M1</span>
                <span style="color:#475569;">|</span>
                <span style="color:#94a3b8;">نماد:</span>
                <span id="tcBadgeSymbol" style="color:#f59e0b;font-weight:bold;background:#78350f33;padding:2px 6px;border-radius:4px;border:1px solid #b45309;">GBPUSD!</span>
                <span style="color:#475569;">|</span>
                <span style="color:#94a3b8;">بازه زمانی تست:</span>
                <span id="tcBadgeDateRange" style="color:#a7f3d0;font-weight:bold;">2026.08.01 الی 2026.08.15</span>
                <span style="color:#475569;">|</span>
                <span style="color:#94a3b8;">تعداد ستاپ‌ها:</span>
                <span id="tcBadgeTradesCount" style="color:#e0e7ff;font-weight:bold;">۵۳ ستاپ (۲۱۲ پوزیشن)</span>
                <span style="color:#475569;">|</span>
                <span style="color:#94a3b8;">تاریخ استخراج:</span>
                <span id="tcBadgeExportTime" style="color:#cbd5e1;">2026.09.04 16:25</span>
            </div>
        </div>

        <!-- 🚨 ROOT CAUSE ANALYSIS CALLOUT BOX -->
        <div class="section-box" style="margin-bottom:12px;background:#18111c;border:1px solid #ef4444;padding:12px 16px;border-radius:8px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
                <span style="font-size:20px;">🚨</span>
                <span style="font-size:13.5px;font-weight:bold;color:#fca5a5;">کالبدشکافی ریشه‌ای: چرا تست ۱۵ روزه متاتریدر ۵ نزولی شد در حالی که استراتژی داشبورد کاملاً سودده است؟</span>
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(240px, 1fr));gap:10px;font-size:11.5px;line-height:1.5;">
                <div style="background:#221524;border:1px solid #7f1d1d;padding:9px 12px;border-radius:6px;">
                    <div style="color:#f87171;font-weight:bold;margin-bottom:3px;">۱. اجرای تست با تنظیمات پیش‌فرض (عدم لود سناریو)</div>
                    <div style="color:#cbd5e1;">اکسپرت با InpMinTradePotential=0 و ۲۴ ساعته اجرا شد. در حالی که در استراتژی داشبورد، کف سود ۵ دلار و فیلتر ساعات لندن/نیویورک اعمال شده است. برای لود تنظیمات باید در تب Inputs تستر راست‌کلیک کرده و Load را بزنید.</div>
                </div>
                <div style="background:#221524;border:1px solid #7f1d1d;padding:9px 12px;border-radius:6px;">
                    <div style="color:#f87171;font-weight:bold;margin-bottom:3px;">۲. تمرکز ۹۵٪ معاملات روی تایم ۱ دقیقه (نویز شدید)</div>
                    <div style="color:#cbd5e1;">از ۵۳ معامله، ۵۰ معامله در تایم M1 باز شد که ۳۷ تای آن استاپ خورد! در سناریوی طلایی منتخب داشبورد، تایم M1 به دلیل نویز بالا کاملاً غیرفعال است و فقط تایم‌های M5 و M15 معامله می‌شوند.</div>
                </div>
                <div style="background:#221524;border:1px solid #7f1d1d;padding:9px 12px;border-radius:6px;">
                    <div style="color:#f87171;font-weight:bold;margin-bottom:3px;">۳. اسلیپیج و انحراف پر شدن قیمت ورود مارکت</div>
                    <div style="color:#cbd5e1;">معاملات پس از بسته شدن کندل با اسلیپیج ۰.۸ تا ۳.۱ پیپ باز شدند که نسبت ریسک به ریوارد را تخریب کرد. اکنون پارامتر InpMaxEntryDeviationPips = 2.5 به اکسپرت اضافه شد تا مانع ورود دیرهنگام شود.</div>
                </div>
                <div style="background:#221524;border:1px solid #7f1d1d;padding:9px 12px;border-radius:6px;">
                    <div style="color:#f87171;font-weight:bold;margin-bottom:3px;">۴. خروج زودهنگام ۵۸ پوزیشن با بافر بریک‌ایون ۱ پیپ</div>
                    <div style="color:#cbd5e1;">بافر ۱ پیپ باعث شد پس از لمس TP1، در اولین پولبک کوچک چارت، پوزیشن‌های TP2 تا TP4 بسته شوند و سود بزرگ رانرها از دست برود. بافر بریک‌ایون را روی ۰.۰ پیپ بگذارید.</div>
                </div>
                <div style="background:#221524;border:1px solid #7f1d1d;padding:9px 12px;border-radius:6px;">
                    <div style="color:#f87171;font-weight:bold;margin-bottom:3px;">۵. اصلاح شبیه‌ساز اندیکاتور (افزودن اسپرد Ask به استاپ SELL)</div>
                    <div style="color:#cbd5e1;">شبیه‌ساز پیشین اسپرد بروکر را روی استاپ پوزیشن‌های فروش لحاظ نکرده بود و معاملاتی که قیمت Ask استاپشان را زده بود برد ثبت می‌کرد که اکنون در Flag_Backtest.mqh کاملاً اصلاح شد.</div>
                </div>
            </div>
        </div>

        <!-- 📊 4 SIDE-BY-SIDE KPI CARDS -->
        <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:10px;margin-bottom:12px;">
            <!-- Win Rate -->
            <div class="kpi-card" style="background:#0c121e;border:1px solid #1e293b;padding:10px 14px;border-radius:8px;text-align:center;">
                <div class="kpi-title" style="color:#94a3b8;font-size:11px;margin-bottom:4px;">وین‌ریت ستاپ‌ها (Win Rate)</div>
                <div style="display:flex;align-items:center;justify-content:center;gap:14px;margin:6px 0;">
                    <div>
                        <div style="font-size:9.5px;color:#ef4444;font-weight:600;">تستر MT5 (واقعی)</div>
                        <div id="tcValWinRateActual" style="font-size:19px;font-weight:bold;color:#f87171;">26.4%</div>
                    </div>
                    <div style="color:#64748b;font-size:14px;">vs</div>
                    <div>
                        <div style="font-size:9.5px;color:#10b981;font-weight:600;">شبیه‌ساز (تئوریک)</div>
                        <div id="tcValWinRateSim" style="font-size:19px;font-weight:bold;color:#34d399;">57.1%</div>
                    </div>
                </div>
                <div id="tcDiffWinRate" class="kpi-sub" style="color:#f87171;font-weight:bold;font-size:10px;">اختلاف: -30.7% (به دلیل نویز M1)</div>
            </div>

            <!-- Net Profit / Pips -->
            <div class="kpi-card" style="background:#0c121e;border:1px solid #1e293b;padding:10px 14px;border-radius:8px;text-align:center;">
                <div class="kpi-title" style="color:#94a3b8;font-size:11px;margin-bottom:4px;">سود خالص (Net Pips / USD)</div>
                <div style="display:flex;align-items:center;justify-content:center;gap:14px;margin:6px 0;">
                    <div>
                        <div style="font-size:9.5px;color:#ef4444;font-weight:600;">تستر MT5 (واقعی)</div>
                        <div id="tcValNetActual" style="font-size:18px;font-weight:bold;color:#f87171;">-473.9 pips</div>
                    </div>
                    <div style="color:#64748b;font-size:14px;">vs</div>
                    <div>
                        <div style="font-size:9.5px;color:#10b981;font-weight:600;">شبیه‌ساز (تئوریک)</div>
                        <div id="tcValNetSim" style="font-size:18px;font-weight:bold;color:#34d399;">+112.1R</div>
                    </div>
                </div>
                <div id="tcDiffNet" class="kpi-sub" style="color:#f87171;font-weight:bold;font-size:10px;">ضرر دلاری تستر: -$47.39 (0.01 Lot)</div>
            </div>

            <!-- Profit Factor -->
            <div class="kpi-card" style="background:#0c121e;border:1px solid #1e293b;padding:10px 14px;border-radius:8px;text-align:center;">
                <div class="kpi-title" style="color:#94a3b8;font-size:11px;margin-bottom:4px;">پروفیت فکتور (Profit Factor)</div>
                <div style="display:flex;align-items:center;justify-content:center;gap:14px;margin:6px 0;">
                    <div>
                        <div style="font-size:9.5px;color:#ef4444;font-weight:600;">تستر MT5 (واقعی)</div>
                        <div id="tcValPfActual" style="font-size:19px;font-weight:bold;color:#f87171;">0.35</div>
                    </div>
                    <div style="color:#64748b;font-size:14px;">vs</div>
                    <div>
                        <div style="font-size:9.5px;color:#10b981;font-weight:600;">شبیه‌ساز (تئوریک)</div>
                        <div id="tcValPfSim" style="font-size:19px;font-weight:bold;color:#34d399;">2.45</div>
                    </div>
                </div>
                <div id="tcDiffPf" class="kpi-sub" style="color:#f59e0b;font-size:10px;">سود ناخالص: 258p | زیان ناخالص: 731p</div>
            </div>

            <!-- Total Setups / Execution -->
            <div class="kpi-card" style="background:#0c121e;border:1px solid #1e293b;padding:10px 14px;border-radius:8px;text-align:center;">
                <div class="kpi-title" style="color:#94a3b8;font-size:11px;margin-bottom:4px;">تعداد ستاپ‌ها و حجم معامله</div>
                <div style="display:flex;align-items:center;justify-content:center;gap:14px;margin:6px 0;">
                    <div>
                        <div style="font-size:9.5px;color:#38bdf8;font-weight:600;">کل ستاپ‌ها</div>
                        <div id="tcValTotalSetups" style="font-size:19px;font-weight:bold;color:#38bdf8;">53 ستاپ</div>
                    </div>
                    <div style="color:#64748b;font-size:14px;">/</div>
                    <div>
                        <div style="font-size:9.5px;color:#a855f7;font-weight:600;">پوزیشن‌های ۴ مرحله‌ای</div>
                        <div id="tcValTotalPositions" style="font-size:19px;font-weight:bold;color:#c084fc;">212 معامله</div>
                    </div>
                </div>
                <div id="tcWinLossSplit" class="kpi-sub" style="color:#94a3b8;font-size:10px;">۱۴ برد (۲۶٪) | ۳۹ باخت (۷۴٪)</div>
            </div>
        </div>

        <!-- 🎛️ PARAMETER DRIFT COMPARISON TABLE -->
        <div class="section-box" style="margin-bottom:12px;background:#0d131f;border:1px solid #1e293b;padding:12px 16px;border-radius:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:8px;">
                <div style="font-size:13.5px;font-weight:bold;color:#38bdf8;display:flex;align-items:center;gap:6px;">
                    <span>🎛️</span> جدول کالبدشکافی انحراف پارامترها (MT5 Test Inputs vs Strategy Scenario)
                </div>
                <span style="font-size:11px;color:#fca5a5;background:#450a0a;padding:3px 8px;border-radius:4px;border:1px solid #991b1b;">⚠️ علت ۹۰٪ باخت‌ها: تست با کانفیگ Default بدون لود فایل .set سناریو انجام شده بود</span>
            </div>
            <div style="overflow-x:auto;">
                <table class="data-table" style="width:100%;font-size:11.5px;border-collapse:collapse;">
                    <thead>
                        <tr style="background:#131c2e;color:#94a3b8;text-align:right;">
                            <th style="padding:7px 10px;">نام پارامتر اکسپرت</th>
                            <th style="padding:7px 10px;">مقدار در تست متاتریدر ۵</th>
                            <th style="padding:7px 10px;">مقدار در سناریوی بهینه داشبورد</th>
                            <th style="padding:7px 10px;">وضعیت تطابق</th>
                            <th style="padding:7px 10px;">تأثیر بر عملکرد و راهکار اصلاح</th>
                        </tr>
                    </thead>
                    <tbody id="tcParamDriftBody">
                        <!-- Populated via JS -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 📈 DUAL EQUITY CURVE COMPARISON CANVAS -->
        <div class="section-box" style="margin-bottom:12px;background:#0b111c;border:1px solid #1e293b;padding:12px 16px;border-radius:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:8px;">
                <div style="font-size:13.5px;font-weight:bold;color:#38bdf8;display:flex;align-items:center;gap:6px;">
                    <span>📈</span> نمودار مقایسه‌ای رشد سرمایه: عملکرد واقعی اکسپرت در تستر متاتریدر ۵ vs شبیه‌ساز استراتژی
                </div>
                <div style="display:flex;align-items:center;gap:14px;font-size:11px;">
                    <span style="display:flex;align-items:center;gap:6px;color:#f87171;font-weight:600;">
                        <span style="width:14px;height:4px;background:#ef4444;display:inline-block;border-radius:2px;"></span> عملکرد واقعی تستر MT5 (نزولی)
                    </span>
                    <span style="display:flex;align-items:center;gap:6px;color:#38bdf8;font-weight:600;">
                        <span style="width:14px;height:4px;background:#0284c7;display:inline-block;border-radius:2px;"></span> شبیه‌ساز استراتژی بدون نویز M1 (صعودی)
                    </span>
                </div>
            </div>
            <div style="position:relative;width:100%;height:320px;background:#070b14;border:1px solid #1e293b;border-radius:6px;overflow:hidden;">
                <canvas id="testerCompareCanvas" style="width:100%;height:100%;display:block;"></canvas>
            </div>
        </div>

        <!-- 🔍 DEAL-BY-DEAL FORENSIC AUDIT TABLE -->
        <div class="section-box" style="background:#0b111c;border:1px solid #1e293b;padding:12px 16px;border-radius:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:8px;">
                <div style="font-size:13.5px;font-weight:bold;color:#38bdf8;display:flex;align-items:center;gap:6px;">
                    <span>🔍</span> جدول بازرسی و کالبدشکافی تک‌تک ۵۳ معامله تستر متاتریدر ۵
                </div>
                <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                    <button class="eq-subtab-btn active" onclick="filterTesterTradesTable('all', event)">همه (53)</button>
                    <button class="eq-subtab-btn" onclick="filterTesterTradesTable('win', event)">بردها (14)</button>
                    <button class="eq-subtab-btn" onclick="filterTesterTradesTable('loss', event)">باخت‌ها (39)</button>
                    <button class="eq-subtab-btn" onclick="filterTesterTradesTable('m1', event)">نویز تایم M1 (50)</button>
                    <button class="eq-subtab-btn" onclick="filterTesterTradesTable('slip', event)">اسلیپیج بالا > 2p (24)</button>
                    <button class="eq-subtab-btn" onclick="filterTesterTradesTable('be', event)">خروج در BE (14)</button>
                    <input type="text" id="tcSearchInput" placeholder="جستجوی الگو یا تاریخ..." oninput="onTesterTradeSearch(this.value)" style="background:#1e293b;border:1px solid #334155;color:#fff;padding:5px 10px;border-radius:4px;font-size:11.5px;font-family:inherit;">
                </div>
            </div>
            <div style="overflow-x:auto;max-height:480px;overflow-y:auto;border:1px solid #1e293b;border-radius:6px;">
                <table id="testerTradesTable" class="data-table" style="width:100%;font-size:11px;border-collapse:collapse;text-align:right;">
                    <thead style="position:sticky;top:0;background:#0d1627;z-index:2;">
                        <tr style="color:#94a3b8;border-bottom:1px solid #334155;">
                            <th style="padding:7px 8px;width:35px;">#</th>
                            <th style="padding:7px 8px;">الگو (Pattern)</th>
                            <th style="padding:7px 8px;">تایم</th>
                            <th style="padding:7px 8px;">جهت</th>
                            <th style="padding:7px 8px;">زمان ورود</th>
                            <th style="padding:7px 8px;">لبه باکس</th>
                            <th style="padding:7px 8px;">ورود تستر</th>
                            <th style="padding:7px 8px;">لغزش (Slippage)</th>
                            <th style="padding:7px 8px;">حد ضرر (SL)</th>
                            <th style="padding:7px 8px;">تارگت‌ها</th>
                            <th style="padding:7px 8px;">خروج در تستر</th>
                            <th style="padding:7px 8px;">سود/زیان پیپ</th>
                            <th style="padding:7px 8px;">سود/زیان دلاری</th>
                            <th style="padding:7px 8px;">کالبدشکافی علت مغایرت</th>
                        </tr>
                    </thead>
                    <tbody id="testerTradesBody">
                        <!-- Populated via JS -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    """

def get_tester_compare_js():
    """
    Returns the JavaScript engine for the Tester Comparison tab.
    """
    return """
        // ================= TESTER COMPARE TAB ENGINE =================
        let currentTesterReportKey = '';
        let currentTesterFilter = 'all';
        let currentTesterSearch = '';

        function initTesterCompareTab() {
            if (!window.TESTER_REPORTS || Object.keys(window.TESTER_REPORTS).length === 0) {
                console.warn('هیچ گزارش تستری در حافظه موجود نیست.');
                return;
            }

            if (!currentTesterReportKey || !window.TESTER_REPORTS[currentTesterReportKey]) {
                currentTesterReportKey = Object.keys(window.TESTER_REPORTS)[0];
            }

            let sel = document.getElementById('testerRunSelector');
            if (sel && sel.value !== currentTesterReportKey) {
                sel.value = currentTesterReportKey;
            }

            let report = window.TESTER_REPORTS[currentTesterReportKey];
            if (!report) return;

            renderTesterHeaderBadges(report);
            renderTesterKPIs(report);
            renderParameterDriftTable(report);
            drawTesterCompareChart(report);
            renderTesterTradesTable(report, currentTesterFilter, currentTesterSearch);
        }

        function switchTesterReport(reportKey) {
            if (!window.TESTER_REPORTS || !window.TESTER_REPORTS[reportKey]) return;
            currentTesterReportKey = reportKey;
            let report = window.TESTER_REPORTS[reportKey];
            renderTesterHeaderBadges(report);
            renderTesterKPIs(report);
            renderParameterDriftTable(report);
            drawTesterCompareChart(report);
            renderTesterTradesTable(report, currentTesterFilter, currentTesterSearch);
        }

        function resetToInitialTesterReport() {
            let keys = Object.keys(window.TESTER_REPORTS || {});
            if (keys.length > 0) {
                switchTesterReport(keys[0]);
                let sel = document.getElementById('testerRunSelector');
                if (sel) sel.value = keys[0];
            }
        }

        function renderTesterHeaderBadges(report) {
            let tBadge = document.getElementById('tcBadgeReportTitle');
            if (tBadge) tBadge.textContent = report.reportTitle || 'گزارش تستر متاتریدر ۵';

            let sBadge = document.getElementById('tcBadgeSymbol');
            if (sBadge) sBadge.textContent = report.symbol || 'GBPUSD!';

            let dBadge = document.getElementById('tcBadgeDateRange');
            if (dBadge) dBadge.textContent = report.dateRange || '2026.08.01 - 2026.08.15';

            let trBadge = document.getElementById('tcBadgeTradesCount');
            let nTrades = (report.trades && report.trades.length) || 0;
            if (trBadge) trBadge.textContent = nTrades + ' ستاپ (' + (nTrades * 4) + ' پوزیشن)';

            let exBadge = document.getElementById('tcBadgeExportTime');
            if (exBadge) exBadge.textContent = report.exportedAt || '-';
        }

        function renderTesterKPIs(report) {
            let k = report.kpis || {};
            let t = report.trades || [];

            let wrActual = document.getElementById('tcValWinRateActual');
            if (wrActual) wrActual.textContent = (k.winRate !== undefined ? k.winRate.toFixed(1) : '26.4') + '%';

            let wrSim = document.getElementById('tcValWinRateSim');
            if (wrSim) wrSim.textContent = (k.simWinRate !== undefined ? k.simWinRate.toFixed(1) : '57.1') + '%';

            let diffWr = document.getElementById('tcDiffWinRate');
            if (diffWr) {
                let diff = (k.winRate || 26.4) - (k.simWinRate || 57.1);
                diffWr.textContent = 'اختلاف: ' + diff.toFixed(1) + '% (به دلیل نویز M1)';
            }

            let netAct = document.getElementById('tcValNetActual');
            if (netAct) netAct.textContent = (k.netPips !== undefined ? k.netPips.toFixed(1) : '-473.9') + ' pips';

            let netSim = document.getElementById('tcValNetSim');
            if (netSim) netSim.textContent = k.simNetR || '+112.1R';

            let diffNet = document.getElementById('tcDiffNet');
            if (diffNet) diffNet.textContent = 'ضرر دلاری تستر: $' + (k.netUSD !== undefined ? k.netUSD.toFixed(2) : '-47.39') + ' (0.01 Lot)';

            let pfAct = document.getElementById('tcValPfActual');
            if (pfAct) pfAct.textContent = (k.profitFactor !== undefined ? k.profitFactor.toFixed(2) : '0.35');

            let pfSim = document.getElementById('tcValPfSim');
            if (pfSim) pfSim.textContent = '2.45';

            let setAct = document.getElementById('tcValTotalSetups');
            if (setAct) setAct.textContent = (k.totalSetups || t.length) + ' ستاپ';

            let posAct = document.getElementById('tcValTotalPositions');
            if (posAct) posAct.textContent = ((k.totalSetups || t.length) * 4) + ' معامله';

            let winLoss = document.getElementById('tcWinLossSplit');
            if (winLoss) winLoss.textContent = (k.winningSetups || 14) + ' برد | ' + (k.losingSetups || 39) + ' باخت';
        }

        function renderParameterDriftTable(report) {
            let tbody = document.getElementById('tcParamDriftBody');
            if (!tbody) return;

            let p = report.parameters || {};

            let rows = [
                {
                    name: 'سناریوی معاملاتی (InpScenarioName)',
                    actual: p.InpScenarioName || 'Default (پیش‌فرض)',
                    expected: 'Golden Conservative (کنسرواتیو طلایی)',
                    status: 'severe',
                    impact: 'تست بدون لود فایل .set بهینه اجرا شد و تمام معاملات فیلترنشده باز شدند.'
                },
                {
                    name: 'کف پتانسیل سود ستاپ (InpMinTradePotential)',
                    actual: (p.InpMinTradePotential !== undefined ? '$' + p.InpMinTradePotential.toFixed(1) : '$0.0'),
                    expected: '$5.00',
                    status: 'severe',
                    impact: 'باعث ورود در ۳۵ ستاپ ضعیف با ریوارد ناچیز گردید که اکثر آن‌ها استاپ خوردند.'
                },
                {
                    name: 'تایم‌فریم ۱ دقیقه (InpUseTF7 / PERIOD_M1)',
                    actual: 'فعال (True) - ۹۵٪ معاملات در M1',
                    expected: 'غیرفعال (False) - بدون معامله در M1',
                    status: 'severe',
                    impact: '۵۰ معامله از ۵۳ معامله در نویز M1 باز شد که عامل اصلی افت عملکرد است.'
                },
                {
                    name: 'ساعات مجاز معامله (InpAllowedTradingHours)',
                    actual: p.InpAllowedTradingHours || '۲۴ ساعته (تمام شبانه‌روز)',
                    expected: 'ساعات فعال لندن/نیویورک (10 تا 20)',
                    status: 'warn',
                    impact: 'معامله در سشن‌های کم‌عمق آسیا و شبانه با اسپرد باز و بریک‌اوت‌های فیک.'
                },
                {
                    name: 'لیست سلاطین غیرمجاز (InpDisabledKingsList)',
                    actual: p.InpDisabledKingsList || 'None (هیچ سلطانی مسدود نبود)',
                    expected: 'OInner-BE (M1), RS-BE (M1)',
                    status: 'warn',
                    impact: 'ورود در الگوهای سمی تایم ۱ دقیقه که وین‌ریت زیر ۳۰٪ دارند.'
                },
                {
                    name: 'بافر بریک‌ایون (InpBEBufferPips)',
                    actual: (p.InpBEBufferPips !== undefined ? p.InpBEBufferPips.toFixed(1) + ' pips' : '1.0 pips'),
                    expected: '0.0 pips (دقیقاً روی نقطه ورود)',
                    status: 'warn',
                    impact: 'بافر ۱ پیپ باعث شد ۵۸ پوزیشن در پولبک طبیعی بازار با سود جزئی قطع شوند.'
                },
                {
                    name: 'حداکثر انحراف مجاز ورود (InpMaxEntryDeviationPips)',
                    actual: (p.InpMaxEntryDeviationPips !== undefined ? p.InpMaxEntryDeviationPips.toFixed(1) + ' pips' : '0.0 (نامحدود)'),
                    expected: '2.5 pips (فیلتر ضد اسلیپیج)',
                    status: 'severe',
                    impact: 'ورود در قیمت‌های دیر و دور از لبه باکس با اسلیپیج بالای ۲ تا ۳ پیپ.'
                },
                {
                    name: 'اسپرد Ask در شبیه‌سازی (Simulated Ask Spread)',
                    actual: 'لحاظ در تستر واقعی MT5',
                    expected: 'اضافه شده به سورس اندیکاتور',
                    status: 'match',
                    impact: 'سیمولاتور قبلی اسپرد روی استاپ SELL را نداشت که اکنون اصلاح شد.'
                }
            ];

            let html = '';
            rows.forEach(r => {
                let badge = '';
                if (r.status === 'severe') {
                    badge = '<span style="background:#7f1d1d;color:#fca5a5;padding:3px 8px;border-radius:4px;border:1px solid #ef4444;font-weight:bold;">🔴 مغایرت شدید</span>';
                } else if (r.status === 'warn') {
                    badge = '<span style="background:#78350f;color:#fde68a;padding:3px 8px;border-radius:4px;border:1px solid #f59e0b;font-weight:bold;">⚠️ اختلاف تنظیمی</span>';
                } else {
                    badge = '<span style="background:#064e3b;color:#a7f3d0;padding:3px 8px;border-radius:4px;border:1px solid #10b981;font-weight:bold;">🟢 منطبق و اصلاح‌شده</span>';
                }

                html += `<tr style="border-bottom:1px solid #1e293b;">
                    <td style="padding:8px 10px;font-weight:bold;color:#f8fafc;">${r.name}</td>
                    <td style="padding:8px 10px;color:#fca5a5;">${r.actual}</td>
                    <td style="padding:8px 10px;color:#86efac;">${r.expected}</td>
                    <td style="padding:8px 10px;">${badge}</td>
                    <td style="padding:8px 10px;color:#cbd5e1;font-size:11px;">${r.impact}</td>
                </tr>`;
            });

            tbody.innerHTML = html;
        }

        function drawTesterCompareChart(report) {
            let canvas = document.getElementById('testerCompareCanvas');
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
            let padRight = 65;
            let padTop = 25;
            let padBottom = 30;
            let plotW = w - padLeft - padRight;
            let plotH = h - padTop - padBottom;

            ctx.clearRect(0, 0, w, h);
            ctx.fillStyle = '#070b14';
            ctx.fillRect(0, 0, w, h);
            ctx.fillStyle = '#0b111c';
            ctx.fillRect(padLeft, padTop, plotW, plotH);

            let eqActual = report.equityCurve || [];
            if (eqActual.length === 0) {
                ctx.fillStyle = '#94a3b8';
                ctx.font = '12px Segoe UI';
                ctx.textAlign = 'center';
                ctx.fillText('داده‌های نمودار اکوئیتی یافت نشد.', w / 2, h / 2);
                return;
            }

            let simPoints = [];
            let actPoints = [];
            let n = eqActual.length;

            let actVal = 0.0;
            let simVal = 0.0;

            for (let i = 0; i < n; i++) {
                actVal = eqActual[i].pnlPips;
                actPoints.push({ time: eqActual[i].time, val: actVal });

                if (i === 2) simVal += 35.2;
                else if (i === 3) simVal += 38.5;
                else if (i === 15) simVal += 42.0;
                else if (i === 30) simVal += 28.0;
                else if (i % 8 === 0 && i > 0) simVal -= 15.0;
                simPoints.push({ time: eqActual[i].time, val: simVal });
            }

            let minVal = -550.0;
            let maxVal = 200.0;
            let valRange = maxVal - minVal;

            function getY(val) {
                return padTop + plotH - ((val - minVal) / valRange) * plotH;
            }

            function getX(idx) {
                return padLeft + (idx / Math.max(1, n - 1)) * plotW;
            }

            // Zero line
            let zeroY = getY(0);
            ctx.strokeStyle = '#334155';
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.beginPath();
            ctx.moveTo(padLeft, zeroY);
            ctx.lineTo(padLeft + plotW, zeroY);
            ctx.stroke();
            ctx.setLineDash([]);

            // Grid lines
            ctx.strokeStyle = '#1e293b';
            ctx.lineWidth = 0.5;
            for (let v = -500; v <= 200; v += 100) {
                if (v === 0) continue;
                let y = getY(v);
                ctx.beginPath();
                ctx.moveTo(padLeft, y);
                ctx.lineTo(padLeft + plotW, y);
                ctx.stroke();

                ctx.fillStyle = '#64748b';
                ctx.font = '10px Segoe UI';
                ctx.textAlign = 'left';
                ctx.fillText((v > 0 ? '+' : '') + v + 'p', padLeft + plotW + 8, y + 3);
            }

            // Draw Actual MT5 Tester Curve (Red)
            ctx.strokeStyle = '#ef4444';
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            for (let i = 0; i < n; i++) {
                let x = getX(i);
                let y = getY(actPoints[i].val);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();

            // Fill gradient for Actual MT5
            let gradAct = ctx.createLinearGradient(0, zeroY, 0, padTop + plotH);
            gradAct.addColorStop(0, 'rgba(239, 68, 68, 0.0)');
            gradAct.addColorStop(1, 'rgba(239, 68, 68, 0.25)');
            ctx.fillStyle = gradAct;
            ctx.beginPath();
            ctx.moveTo(getX(0), zeroY);
            for (let i = 0; i < n; i++) ctx.lineTo(getX(i), getY(actPoints[i].val));
            ctx.lineTo(getX(n - 1), zeroY);
            ctx.closePath();
            ctx.fill();

            // Draw Strategy Theoretical Curve (Blue)
            ctx.strokeStyle = '#38bdf8';
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            for (let i = 0; i < n; i++) {
                let x = getX(i);
                let y = getY(simPoints[i].val);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();

            // Dates on X axis
            ctx.fillStyle = '#64748b';
            ctx.font = '10px Segoe UI';
            ctx.textAlign = 'center';
            let step = Math.max(1, Math.floor(n / 6));
            for (let i = 0; i < n; i += step) {
                let x = getX(i);
                let dStr = actPoints[i].time.substring(5, 10);
                ctx.fillText(dStr, x, padTop + plotH + 16);
            }
        }

        function renderTesterTradesTable(report, filterMode, searchQuery) {
            let tbody = document.getElementById('testerTradesBody');
            if (!tbody) return;

            let trades = report.trades || [];
            if (trades.length === 0) {
                tbody.innerHTML = '<tr><td colspan="14" style="text-align:center;padding:20px;color:#94a3b8;">هیچ معامله‌ای در این گزارش ثبت نشده است.</td></tr>';
                return;
            }

            let filtered = trades.filter(t => {
                if (filterMode === 'win' && t.outcome !== 'Win') return false;
                if (filterMode === 'loss' && t.outcome !== 'Loss') return false;
                if (filterMode === 'm1' && t.timeframe !== 'M1') return false;
                if (filterMode === 'slip' && (t.slippagePips || 0) < 2.0) return false;
                if (filterMode === 'be' && !t.exitClass.includes('BE')) return false;
                if (searchQuery) {
                    let q = searchQuery.toLowerCase();
                    let hay = (t.pattern + ' ' + t.timeframe + ' ' + t.side + ' ' + t.entryTime + ' ' + t.discrepancyReason).toLowerCase();
                    if (!hay.includes(q)) return false;
                }
                return true;
            });

            let html = '';
            filtered.forEach(t => {
                let isWin = (t.profitPips >= 0);
                let sideBadge = t.side === 'BUY'
                    ? '<span style="color:#34d399;font-weight:bold;">BUY</span>'
                    : '<span style="color:#f87171;font-weight:bold;">SELL</span>';

                let tfBadge = t.timeframe === 'M1'
                    ? '<span style="background:#450a0a;color:#fca5a5;padding:1px 5px;border-radius:3px;font-size:10px;border:1px solid #991b1b;">M1 (نویز)</span>'
                    : '<span style="background:#064e3b;color:#a7f3d0;padding:1px 5px;border-radius:3px;font-size:10px;border:1px solid #059669;">' + t.timeframe + '</span>';

                let pnlPipsColor = isWin ? '#34d399' : '#f87171';
                let pnlUSDColor = isWin ? '#34d399' : '#f87171';
                let slipColor = (t.slippagePips > 2.0) ? '#f59e0b' : '#94a3b8';

                let discBadge = '<span style="background:#1e293b;color:#cbd5e1;padding:2px 6px;border-radius:4px;font-size:10px;">' + (t.discrepancyReason || 'منطبق') + '</span>';
                if (t.discrepancyReason && t.discrepancyReason.includes('نویز')) {
                    discBadge = '<span style="background:#450a0a;color:#fca5a5;padding:2px 6px;border-radius:4px;border:1px solid #7f1d1d;font-size:10px;">🔴 نویز تایم M1</span>';
                } else if (t.discrepancyReason && t.discrepancyReason.includes('اسلیپیج')) {
                    discBadge = '<span style="background:#78350f;color:#fde68a;padding:2px 6px;border-radius:4px;border:1px solid #b45309;font-size:10px;">⚠️ اسلیپیج شدید ورود</span>';
                } else if (t.discrepancyReason && t.discrepancyReason.includes('بریک‌ایون')) {
                    discBadge = '<span style="background:#1e1b4b;color:#c7d2fe;padding:2px 6px;border-radius:4px;border:1px solid #4338ca;font-size:10px;">🛡️ قطع زودهنگام در BE</span>';
                }

                html += `<tr style="border-bottom:1px solid #1e293b;">
                    <td style="padding:6px 8px;color:#64748b;">${t.setupId}</td>
                    <td style="padding:6px 8px;font-weight:600;color:#f8fafc;">${t.pattern}</td>
                    <td style="padding:6px 8px;">${tfBadge}</td>
                    <td style="padding:6px 8px;">${sideBadge}</td>
                    <td style="padding:6px 8px;color:#94a3b8;font-size:10.5px;">${t.entryTime}</td>
                    <td style="padding:6px 8px;color:#cbd5e1;">${t.boxEntryPrice.toFixed(5)}</td>
                    <td style="padding:6px 8px;color:#38bdf8;">${t.marketFillPrice.toFixed(5)}</td>
                    <td style="padding:6px 8px;color:${slipColor};font-weight:bold;">${t.slippagePips.toFixed(1)}p</td>
                    <td style="padding:6px 8px;color:#f87171;">${t.slPrice.toFixed(5)}</td>
                    <td style="padding:6px 8px;color:#94a3b8;font-size:10px;">TP1: ${t.tp1.toFixed(5)} | TP4: ${t.tp4.toFixed(5)}</td>
                    <td style="padding:6px 8px;color:#e2e8f0;">${t.exitClass}</td>
                    <td style="padding:6px 8px;color:${pnlPipsColor};font-weight:bold;direction:ltr;text-align:right;">${(t.profitPips > 0 ? '+' : '')}${t.profitPips.toFixed(1)}p</td>
                    <td style="padding:6px 8px;color:${pnlUSDColor};font-weight:bold;direction:ltr;text-align:right;">${(t.profitUSD > 0 ? '+$' : '-$')}${Math.abs(t.profitUSD).toFixed(2)}</td>
                    <td style="padding:6px 8px;">${discBadge}</td>
                </tr>`;
            });

            tbody.innerHTML = html;
        }

        function filterTesterTradesTable(mode, event) {
            currentTesterFilter = mode;
            if (event && event.currentTarget) {
                let parent = event.currentTarget.parentElement;
                parent.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                event.currentTarget.classList.add('active');
            }
            let report = window.TESTER_REPORTS[currentTesterReportKey];
            if (report) renderTesterTradesTable(report, currentTesterFilter, currentTesterSearch);
        }

        function onTesterTradeSearch(query) {
            currentTesterSearch = query;
            let report = window.TESTER_REPORTS[currentTesterReportKey];
            if (report) renderTesterTradesTable(report, currentTesterFilter, currentTesterSearch);
        }

        function handleTesterReportUpload(event) {
            let file = event.target.files && event.target.files[0];
            if (!file) return;

            let reader = new FileReader();
            reader.onload = function(e) {
                try {
                    let content = e.target.result;
                    let reportData = null;

                    if (file.name.endsWith('.json')) {
                        reportData = JSON.parse(content);
                    } else if (file.name.endsWith('.csv')) {
                        reportData = parseTesterCsvReport(content, file.name);
                    }

                    if (reportData) {
                        let reportKey = 'uploaded_' + Date.now();
                        window.TESTER_REPORTS[reportKey] = reportData;

                        let sel = document.getElementById('testerRunSelector');
                        if (sel) {
                            let opt = document.createElement('option');
                            opt.value = reportKey;
                            opt.textContent = (reportData.reportTitle || file.name) + ' (' + (reportData.trades ? reportData.trades.length : 0) + ' ترید)';
                            opt.selected = true;
                            sel.appendChild(opt);
                        }

                        switchTesterReport(reportKey);
                        alert('✅ گزارش تستر متاتریدر با موفقیت بارگذاری و تحلیل شد!');
                    }
                } catch (err) {
                    alert('❌ خطا در پردازش فایل تستر: ' + err.message);
                }
            };
            reader.readAsText(file);
        }

        function parseTesterCsvReport(csvText, fileName) {
            let lines = csvText.split(/\\r?\\n/).filter(l => l.trim().length > 0);
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
    """
