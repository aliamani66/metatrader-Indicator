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
    Loads all test reports from reports_dir, as well as MetaTrader Common and Tester Agent directories.
    Automatically copies external reports into reports_dir and returns an OrderedDict sorted by mtime (newest first).
    """
    import glob
    import shutil
    from collections import OrderedDict

    os.makedirs(reports_dir, exist_ok=True)

    # Candidate directories where MT5 Strategy Tester may output files
    search_dirs = [reports_dir]
    common_dir = r"C:\Users\USER\AppData\Roaming\MetaQuotes\Terminal\Common\Files\FlagPro_TesterReports"
    if os.path.exists(common_dir) and common_dir not in search_dirs:
        search_dirs.append(common_dir)

    tester_dirs = glob.glob(r"C:\Users\USER\AppData\Roaming\MetaQuotes\Tester\**\FlagPro_TesterReports", recursive=True)
    for td in tester_dirs:
        if os.path.isdir(td) and td not in search_dirs:
            search_dirs.append(td)

    # Sync external files to local reports_dir
    for s_dir in search_dirs:
        if s_dir == reports_dir or not os.path.exists(s_dir):
            continue
        for ext in ['*.json', '*.csv']:
            for src_file in glob.glob(os.path.join(s_dir, ext)):
                dst_file = os.path.join(reports_dir, os.path.basename(src_file))
                try:
                    if not os.path.exists(dst_file) or os.path.getmtime(src_file) > os.path.getmtime(dst_file):
                        shutil.copy2(src_file, dst_file)
                except Exception:
                    pass

    # Read all JSON reports from reports_dir
    candidates = []
    for fname in os.listdir(reports_dir):
        if fname.endswith('.json'):
            fpath = os.path.join(reports_dir, fname)
            candidates.append((fpath, os.path.getmtime(fpath)))

    # Sort descending by file modification time (newest first)
    candidates.sort(key=lambda x: x[1], reverse=True)

    reports = OrderedDict()
    for fpath, mtime in candidates:
        fname = os.path.basename(fpath)
        data = None
        for enc in ['utf-16', 'utf-8-sig', 'utf-8']:
            try:
                with open(fpath, mode='r', encoding=enc) as f:
                    content = f.read()
                    data = json.loads(content)
                    break
            except Exception:
                continue

        if not data:
            continue

        try:
            trades = data.get('trades', [])
            for t in trades:
                if 'pnlPips' in t and 'profitPips' not in t:
                    t['profitPips'] = t['pnlPips']
                if 'pnlUSD' in t and 'profitUSD' not in t:
                    t['profitUSD'] = t['pnlUSD']
                if 'profitPips' in t and 'pnlPips' not in t:
                    t['pnlPips'] = t['profitPips']
                if 'profitUSD' in t and 'pnlUSD' not in t:
                    t['pnlUSD'] = t['profitUSD']
                if 'discrepancyLabel' in t and 'discrepancyReason' not in t:
                    t['discrepancyReason'] = t['discrepancyLabel']
                if 'outcome' not in t:
                    t['outcome'] = 'Win' if t.get('profitPips', 0) >= 0 else 'Loss'
            data['mtime'] = mtime
            reports[fname] = data
        except Exception as e:
            print(f"⚠️ خطا در پردازش ساختار گزارش تستر {fname}: {e}")

    return reports

def get_tester_compare_html(reports_dict, default_key):
    """
    Generates the HTML content for tab-tester-compare.
    """
    options_html = []
    for k, v in reports_dict.items():
        sel = 'selected' if k == default_key else ''
        title = v.get('reportTitle', k)
        date_range = v.get('dateRange', '')
        t_count = len(v.get('trades', []))
        options_html.append(f'<option value="{k}" {sel}>{title} | [{date_range}] | {t_count} معامله</option>')
    
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
                    <select id="testerScenarioSelector" onchange="switchTesterScenario(this.value)" style="background:#0f172a;border:1px solid #10b981;color:#a7f3d0;padding:6px 12px;border-radius:6px;font-size:12px;cursor:pointer;min-width:240px;font-family:inherit;font-weight:600;" title="انتخاب سناریوی بهینه جهت مقایسه انحراف پارامترها و بازده تئوریک">
                        <option value="auto" selected>🔍 تشخیص خودکار سناریو از فایل تستر</option>
                        <option value="golden">⚖️ تعادل طلایی حجم و سود (Golden Balance)</option>
                        <option value="champion">💎 سلاطین برتر و اسنایپر (Champion Sniper)</option>
                        <option value="day">☀️ سشن لندن و نیویورک (London & NY)</option>
                        <option value="shield">🛡️ سپر حداقل دروداون (Stop Loss Shield)</option>
                        <option value="base">🌐 تمام سلاطین ۲۴ ساعته (All Kings Base)</option>
                    </select>
                    <button class="action-btn" onclick="copyTesterReportsFolder()" style="background:linear-gradient(135deg, #1e1b4b, #312e81);color:#c7d2fe;border:1px solid #6366f1;padding:6px 12px;border-radius:6px;font-size:11.5px;cursor:pointer;font-weight:600;display:flex;align-items:center;gap:5px;" title="کپی آدرس پوشه گزارشات متاتریدر ۵ در کلیپ‌بورد برای پیست در پنجره انتخاب فایل">
                        <span>📋</span> کپی آدرس پوشه فایل‌ها
                    </button>
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
                <span id="tcDriftSummaryBadge" style="font-size:11px;color:#fca5a5;background:#450a0a;padding:3px 8px;border-radius:4px;border:1px solid #991b1b;">⚠️ وضعیت انحراف پارامترها</span>
            </div>
            <div style="overflow-x:auto;">
                <table class="data-table" style="width:100%;font-size:11.5px;border-collapse:collapse;">
                    <thead>
                        <tr style="background:#131c2e;color:#94a3b8;text-align:right;">
                            <th style="padding:7px 10px;">نام پارامتر اکسپرت</th>
                            <th style="padding:7px 10px;">مقدار در تست متاتریدر ۵</th>
                            <th id="tcColExpectedScenario" style="padding:7px 10px;">مقدار در سناریوی انتخابی</th>
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
                <!-- ⚡ Live & Peak Concurrent Trades Corner Badge -->
                <div style="position:absolute;top:10px;left:10px;background:rgba(15,23,42,0.92);backdrop-filter:blur(6px);border:1px solid #0284c7;border-radius:6px;padding:4px 10px;z-index:10;display:flex;align-items:center;gap:8px;direction:rtl;pointer-events:none;">
                    <span style="font-size:12px;">⚡</span>
                    <span style="font-size:11px;color:#94a3b8;">حداکثر معامله باز همزمان تستر: <b style="color:#38bdf8;">۵ پوزیشن</b> (میانگین ۲.۲)</span>
                </div>
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
    Loads directly from FlagPro_Modular_App/js/tabs/tab_tester_compare.js
    to guarantee 100% synchronization and DRY modular architecture.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    modular_js = os.path.join(base_dir, "FlagPro_Modular_App", "js", "tabs", "tab_tester_compare.js")
    if os.path.exists(modular_js):
        try:
            with open(modular_js, mode='r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ Error reading {modular_js}: {e}")
    return "// tester compare js engine"
