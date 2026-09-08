//+------------------------------------------------------------------+
//| FlagPro.mq5                                                      |
//| Advanced Modular Multi-Timeframe Structure & Flag Indicator      |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""
#property version   "2.60"
#property indicator_chart_window
#property indicator_buffers 2
#property indicator_plots   1
#property indicator_label1  "Ask Price (Spread)"
#property indicator_type1   DRAW_LINE
#property indicator_color1  C'220,75,75'
#property indicator_style1  STYLE_SOLID
#property indicator_width1  1

double g_askBuffer[];
double g_dummyBuffer[];
bool   g_askLineVisible = true;

#include <FlagPro\Flag_Types.mqh>

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                 |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//| ۰. 🔄 همگام‌سازی خودکار با استراتژی تستر (تستر ⇄ اندیکاتور)        |
//+------------------------------------------------------------------+
input group "=== 🔄 همگام‌سازی خودکار با استراتژی تستر (تستر ⇄ اندیکاتور) ==="
input bool              InpAutoSyncWithTester = true;                   // 🔄 همگام‌سازی زنده و لحظه‌ای با تست‌های استراتژی تستر (تستر ⇄ چارت)

//+------------------------------------------------------------------+
//| ۱. 🎯 بازه زمانی تحلیل و عمق تاریخچه                             |
//+------------------------------------------------------------------+
input group "=== 🎯 ۱. بازه زمانی تحلیل و عمق تاریخچه ==="
input ENUM_HISTORY_MODE InpHistoryMode        = HIST_DAYS_BACK;         // ⚙️ مبنای محاسبه بازه تاریخی (تعداد روز گذشته / تاریخ دلخواه / کل دیتای متاتریدر)
input int               InpHistoryDays        = 10;                     // ⏳ تعداد روزهای گذشته جهت بررسی (پیش‌فرض: ۱۰ روز برای پوشش کامل)
input datetime          InpHistoryStartDate   = D'2026.09.01 00:00';    // 📅 تاریخ شروع دلخواه (فقط در حالت انتخاب تاریخ دلخواه)
input bool              InpExportCSV          = true;                   // 📁 استخراج خودکار گزارش معاملات CSV (جهت آنالیز در داشبورد وب)

//+------------------------------------------------------------------+
//| ۲. 👁️ فیلتر نمایش باکس‌ها و گرافیک چارت                          |
//+------------------------------------------------------------------+
input group "=== 👁️ ۲. فیلتر نمایش باکس‌ها و گرافیک چارت ==="
input ENUM_BOX_DISPLAY_FILTER InpBoxDisplayFilter = BOX_FILTER_TRADED_ONLY; // 🎛️ نحوه نمایش باکس‌ها (معامله‌شده / فقط ستاپ‌ها / همه باکس‌ها / مخفی)
input bool              InpShowBoxes          = true;                   // 👁️ فعال‌سازی رسم باکس‌ها روی چارت (کلید B برای سوئیچ سریع)
input bool              InpShowLabel          = true;                   // 🏷️ نمایش برچسب نام الگو و تایم‌فریم روی باکس‌ها
input ENUM_LABEL_FORMAT InpLabelFormat        = LABEL_CONCISE;          // 🔤 فرمت متن برچسب الگو (کوتاه و تمیز / زنجیره کامل ساختار)
input int               InpLineWidth          = 1;                      // ✏️ ضخامت خطوط حاشیه باکس‌ها
input bool              InpRemoveOverlapping  = true;                   // 🧹 حذف هوشمند باکس‌های هم‌پوشان و تکراری هم‌جهت
input bool              InpShowAskLine        = true;                   // 🔴 رسم خط قیمت اسک Ask روی چارت زنده (مشابه استراتژی تستر)
input color             InpAskLineColor       = C'220,75,75';           // 🎨 رنگ خط قیمت اسک Ask
input ENUM_LINE_STYLE   InpAskLineStyle       = STYLE_SOLID;            // 📏 استایل خط قیمت اسک (پیوسته / خط‌چین)
input int               InpAskLineWidth       = 1;                      // ✏️ ضخامت خط قیمت اسک
input bool              InpApplyProTheme      = true;                   // 🌓 تم تاریک اختصاصی و چشم‌نواز برای پس‌زمینه چارت

//+------------------------------------------------------------------+
//| ۳. 🏹 شبیه‌ساز معاملات و ترسیم خطوط ترید                         |
//+------------------------------------------------------------------+
input group "=== 🏹 ۳. شبیه‌ساز معاملات و ترسیم خطوط ترید ==="
input bool              InpAutoDrawTrades     = true;                   // 🎯 رسم خودکار معاملات روی چارت (سطوح ورود، حد ضرر و تارگت‌ها)
input bool              InpEnableTradeSetup   = true;                   // ⚡ فعال‌سازی محاسبه و تشخیص ستاپ‌های معاملاتی روی باکس‌ها
input bool              InpUniqueTradeColors  = true;                   // 🎨 رنگ‌های مجزا برای هر معامله (تفکیک آسان معاملات همزمان چارت)
input bool              InpShowTradeShading   = false;                  // 🌈 نمایش پس‌زمینه رنگی معاملات (محدوده سود و زیان)
input color             InpTradeEntryColor    = clrWhite;               // ⚪ رنگ پیش‌فرض خط ورود به معامله (Entry)
input color             InpTradeSLColor       = clrDarkOrange;          // 🟠 رنگ پیش‌فرض خط حد ضرر معامله (Stop Loss)
input color             InpTradeTPColor       = clrDodgerBlue;          // 🔵 رنگ پیش‌فرض خطوط اهداف سود معامله (Take Profit)

//+------------------------------------------------------------------+
//| ۴. 🛡️ قوانین ورود، حد ضرر و مدیریت ریسک                         |
//+------------------------------------------------------------------+
input group "=== 🛡️ ۴. قوانین ورود، حد ضرر و مدیریت ریسک ==="
input double            InpSLOffsetPips       = 8.0;                    // 🛡️ فاصله اطمینان حد ضرر جهت فرار از شدوها (افست استاپ به پیپ)
#define InpRSPipBuffer InpSLOffsetPips
input double            InpMaxEntryDeviationPips = 2.5;                 // 🎯 حداکثر انحراف مجاز ورود از لبه باکس به پیپ (جلوگیری از ورود دیر)
input int               InpLimitExpirationBars   = 40;                  // ⏳ حداکثر طول عمر اردر لیمیت به تعداد کندل (انقضای اردر دست‌نخورده)
input bool              InpAllowOverlappingTrades = true;               // 🔓 اجازه معاملات همزمان (ورود روی ستاپ‌های هم‌پوشان)

//+------------------------------------------------------------------+
//| ۵. ⏱️ تایم‌فریم‌های فعال معامله                                  |
//+------------------------------------------------------------------+
input group "=== ⏱️ ۵. تایم‌فریم‌های فعال معامله ==="
input bool              InpUseTF7             = true;                   // ⚡ تایم‌فریم ۱ دقیقه (M1) فعال باشد
input color             InpColorTF7           = clrYellow;              // 🎨 رنگ باکس‌های تایم‌فریم ۱ دقیقه (M1)
input bool              InpUseTF6             = true;                   // ⚡ تایم‌فریم ۵ دقیقه (M5) فعال باشد
input color             InpColorTF6           = clrAqua;                // 🎨 رنگ باکس‌های تایم‌فریم ۵ دقیقه (M5)
input bool              InpUseTF5             = true;                   // ⚡ تایم‌فریم ۱۵ دقیقه (M15) فعال باشد
input color             InpColorTF5           = clrLime;                // 🎨 رنگ باکس‌های تایم‌فریم ۱۵ دقیقه (M15)
input bool              InpTradeMacroTFs      = false;                  // 🌐 معامله در تایم‌های ماکرو H1, H4, D1, W1 (پیش‌فرض: خاموش)

#define InpTF7 PERIOD_M1
#define InpTF6 PERIOD_M5
#define InpTF5 PERIOD_M15
#define InpTF4 PERIOD_H1
#define InpTF3 PERIOD_H4
#define InpTF2 PERIOD_W1
#define InpTF1 PERIOD_D1
#define InpUseTF4 false
#define InpUseTF3 false
#define InpUseTF2 false
#define InpUseTF1 false
#define InpColorTF4 clrYellow
#define InpColorTF3 clrWhite
#define InpColorTF2 clrDodgerBlue
#define InpColorTF1 clrMagenta

//+------------------------------------------------------------------+
//| ۶. 👑 سلاطین برگزیده و پریست‌های استراتژی (هماهنگ با اکسپرت)      |
//+------------------------------------------------------------------+
input group "=== 👑 ۶. سلاطین برگزیده و پریست‌های استراتژی (هماهنگ با اکسپرت) ==="
input bool              InpOnlyTradeKings     = false;                  // 👑 فقط معامله سلاطین برگزیده (Kings Only)
input bool              InpTradeOnlyGoldenKings = false;                // 👑 قفل انحصاری فقط سلاطین طلایی برنده
input bool              InpEnableKingsM15     = true;                   // 👑 فعال‌سازی سلاطین طلایی تایم M15 (۲ ساختار برتر)
input bool              InpEnableKingsM5      = true;                   // 👑 فعال‌سازی سلاطین طلایی تایم M5 (۷ ساختار برتر)
input bool              InpEnableKingsM1      = true;                   // 👑 فعال‌سازی سلاطین طلایی تایم M1 (۹ ساختار برتر)
input string            InpAllowedKingsList   = "";                     // 👑 لیست انحصاری سلاطین مجاز (جدا با کاما، مثلاً S-RS|M1)
input string            InpDisabledKingsList  = "";                     // 🚫 لیست سیاه سلاطین غیرمجاز (جدا با کاما)

//+------------------------------------------------------------------+
//| ۷. 🚫 فیلترهای هوشمند ضد استاپ و اصطکاک                          |
//+------------------------------------------------------------------+
input group "=== 🚫 ۷. فیلترهای هوشمند ضد استاپ و اصطکاک ==="
input bool              InpFilterNightHours   = false;                  // 🌙 فیلتر ۱: مسدودسازی بازه شبانه ۲۱:۰۰ تا ۰۱:۰۰
input bool              InpFilterPreLondonHunt= false;                  // ⏰ فیلتر ۲: مسدودسازی ساعت هانت قبل از لندن ۰۷:۰۰
input bool              InpFilterToxicPatterns= false;                  // ⚠️ فیلتر ۳: حذف زنجیره‌های فرسایشی سمی
input bool              InpFilterSingleLS     = false;                  // 🔍 فیلتر ۴: حذف باکس‌های منفرد LS بدون تلاقی
input bool              InpFilterPureFlags    = false;                  // 🚩 فیلتر ۵: حذف فلگ‌های ساده بدون تاییدیه
input bool              InpFilterLowRewardVsFriction = false;           // 💰 فیلتر ۶: مسدودسازی ترید در صورت عدم تناسب سود با اصطکاک
input double            InpBrokerCommissionPerLot    = 6.0;             // 💵 کمیسیون بروکر به ازای هر ۱ لات معامله ($)
input double            InpEstimatedSpreadPips       = 0.8;             // 📊 اسپرد تخمینی معامله به پیپ
input double            InpMinNetProfitRatioTP1      = 1.0;             // ⚖️ حداقل نسبت سود تارگت اول (TP1) به کل اصطکاک بروکر
input string            InpAllowedTradingHours       = "";              // ⏰ ساعات مجاز معامله طبق سناریو (خالی = ۲۴ ساعته)
input double            InpMinTradePotential         = 0.0;             // 💰 حداقل کف سود دلاری معامله (اسلایدر داشبورد)

//+------------------------------------------------------------------+
//| ۸. 🎨 استایل و رنگ‌بندی تفکیکی الگوهای ساختاری                    |
//+------------------------------------------------------------------+
input group "=== 🎨 ۸. استایل و رنگ‌بندی تفکیکی الگوهای ساختاری ==="
input int               InpSwingBars          = 6;                      // 📐 عمق کندلی محاسبه سویینگ‌ها (Swing Bars)
input bool              InpHighlightPreIP     = true;                   // 🟢 شناسایی و هایلایت باکس‌های ساختاری ماقبل پیووت (LS)
input color             InpLSColorBull        = clrLimeGreen;           // 🎨 رنگ باکس‌های LS صعودی
input color             InpLSColorBear        = clrCrimson;             // 🎨 رنگ باکس‌های LS نزولی
input int               InpPreIPWidth         = 2;                      // ✏️ ضخامت خط باکس‌های LS

input bool              InpHighlightOInner    = true;                   // 🟣 شناسایی و هایلایت باکس‌های اولین گره بعد از پیووت (OInner)
input color             InpOInnerColorBull    = clrSpringGreen;         // 🎨 رنگ باکس‌های OInner صعودی
input color             InpOInnerColorBear    = clrHotPink;             // 🎨 رنگ باکس‌های OInner نزولی
input int               InpOInnerWidth        = 3;                      // ✏️ ضخامت خط باکس‌های OInner

input bool              InpHighlightBreakoutFlags = true;               // 🔵 شناسایی و هایلایت فلگ‌های شکست و تلاقی (RS)
input color             InpRSColorBull        = clrDodgerBlue;          // 🎨 رنگ باکس‌های RS صعودی
input color             InpRSColorBear        = clrOrangeRed;           // 🎨 رنگ باکس‌های RS نزولی
input color             InpComboColorBull     = clrYellow;              // 🎨 رنگ باکس‌های ترکیبی (LS+RS) صعودی
input color             InpComboColorBear     = clrMagenta;             // 🎨 رنگ باکس‌های ترکیبی (LS+RS) نزولی
input int               InpBreakoutFlagWidth  = 3;                      // ✏️ ضخامت خط باکس‌های RS

input bool              InpEnableSwapLines    = true;                   // 🔄 شناسایی و هایلایت سطوح و باکس‌های سواپ معکوس (Swap)
input color             InpSwapColorBull      = clrCyan;                // 🎨 رنگ باکس‌های سواپ صعودی
input color             InpSwapColorBear      = clrOrange;              // 🎨 رنگ باکس‌های سواپ نزولی
input int               InpSwapBoxWidth       = 2;                      // ✏️ ضخامت خط باکس‌های سواپ
input int               InpSwapLineWidth      = 1;                      // ✏️ ضخامت خطوط افقی امتداد یافته سواپ
input ENUM_LINE_STYLE   InpSwapLineStyle      = STYLE_DOT;              // 📏 استایل خطوط افقی سواپ (خط‌چین / نقطه)

input bool              InpHighlightIndepPivots = false;                // 📍 نمایش نشانگر پیووت‌های مستقل روی چارت
input bool              InpOnlyPureIndependent = false;                 // 🎯 فقط نمایش پیووت‌های کاملاً خالص و بدون هم‌پوشانی
input color             InpIndepColorHigh     = clrOrangeRed;           // 🎨 رنگ نشانگر سقف‌های مستقل (High Pivots)
input color             InpIndepColorLow      = clrLime;                // 🎨 رنگ نشانگر کف‌های مستقل (Low Pivots)
input int               InpIndepMarkCode      = 159;                    // 🔢 کد آیکون پیووت‌های مستقل (۱۵۹ = دایره پر)
input int               InpIndepMarkWidth     = 1;                      // ✏️ اندازه آیکون نشانگر پیووت‌های مستقل
input bool              InpIndepShowLabel     = false;                  // 🏷️ نمایش نام متنی پیووت روی آیکون

input bool              InpEnableOriginLines  = false;                  // 📏 رسم خطوط افقی منشأ شکست ساختار (RS Origin Lines)
input color             InpOriginColorLow     = clrAqua;                // 🎨 رنگ خطوط منشأ کف (Origin Low)
input color             InpOriginColorHigh    = clrMagenta;             // 🎨 رنگ خطوط منشأ سقف (Origin High)
input int               InpOriginLineWidth    = 1;                      // ✏️ ضخامت خطوط منشأ
input ENUM_LABEL_STYLE  InpOriginLabelStyle   = LABEL_COMPACT;          // 🔤 استایل برچسب خطوط منشأ (کوتاه / کامل / فقط تولتیپ)

//+------------------------------------------------------------------+
//| MODULAR INCLUDES (ماژول‌های تفکیک‌شده)                            |
//+------------------------------------------------------------------+
#include <FlagPro\Flag_Pivots.mqh>
#include <FlagPro\Flag_Boxes.mqh>
#include <FlagPro\Flag_Filters.mqh>
#include <FlagPro\Flag_Backtest.mqh>
#include <FlagPro\Flag_Render.mqh>

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   InitMasterHistory(InpHistoryMode, InpHistoryStartDate, InpHistoryDays);
   g_testerStartBase = 0;
   g_boxesVisible = InpShowBoxes;
   g_askLineVisible = InpShowAskLine;

   SetIndexBuffer(0, g_askBuffer, INDICATOR_DATA);
   SetIndexBuffer(1, g_dummyBuffer, INDICATOR_CALCULATIONS);

   PlotIndexSetString(0, PLOT_LABEL, "Ask Price (Spread)");
   PlotIndexSetDouble(0, PLOT_EMPTY_VALUE, EMPTY_VALUE);
   if(!InpShowAskLine)
   {
      PlotIndexSetInteger(0, PLOT_DRAW_TYPE, DRAW_NONE);
   }
   else
   {
      PlotIndexSetInteger(0, PLOT_DRAW_TYPE, DRAW_LINE);
      PlotIndexSetInteger(0, PLOT_LINE_COLOR, InpAskLineColor);
      PlotIndexSetInteger(0, PLOT_LINE_STYLE, InpAskLineStyle);
      PlotIndexSetInteger(0, PLOT_LINE_WIDTH, InpAskLineWidth);
   }

   ApplyProChartTheme();

   ArrayResize(g_tradeSetups, 0);
   g_tradeCount = 0;
   ObjectsDeleteAll(0, FP_PREFIX);
   ChartRedraw(0);
   g_forceRecalc = true;
   IndicatorSetString(INDICATOR_SHORTNAME, "FlagPro " + FLAGPRO_VERSION);
   PrintFormat("🚀 [FlagPro %s] بازه فعال: از تاریخ %s (%d روز گذشته) | کندل‌های پردازش: %d | باکس‌ها: %s | خط اسک: %s | معاملات: %s",
               FLAGPRO_VERSION,
               (g_effectiveStartDate > 0 ? TimeToString(g_effectiveStartDate, TIME_DATE) : "کل تاریخچه"),
               g_effectiveDaysBack, g_effectiveTargetBars,
               (InpShowBoxes ? "روشن" : "خاموش"),
               (InpShowAskLine ? "روشن" : "خاموش"),
               (InpAutoDrawTrades ? "روشن" : "خاموش"));
   if(InpAutoSyncWithTester)
   {
      CheckAndLoadActiveScenario(true);
      EventSetTimer(2);
   }
   RenderVersionBadge("FlagPro Indicator", FLAGPRO_VERSION);
   RenderSyncStatusBadge();
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                       |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(InpAutoSyncWithTester)
      EventKillTimer();
   ArrayResize(g_tradeSetups, 0);
   g_tradeCount = 0;
   ObjectsDeleteAll(0, FP_PREFIX);
   ChartRedraw(0);
   g_testerStartBase = 0;
}

//+------------------------------------------------------------------+
//| تایمر دوره‌ای جهت همگام‌سازی خودکار و زنده با استراتژی تستر       |
//+------------------------------------------------------------------+
void OnTimer()
{
   if(!InpAutoSyncWithTester) return;

   if(CheckAndLoadActiveScenario(false))
   {
      g_forceRecalc = true;
      datetime tArr[];
      CopyTime(_Symbol, _Period, 0, 1, tArr);
      RenderFinalBoxes(tArr, 1);
      RenderSyncStatusBadge();
      ChartRedraw(0);
   }
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   if(rates_total < 10) return 0;

   // به‌روزرسانی خط قیمت اسک (Ask Price Overlay - مطابق استراتژی تستر متاتریدر)
   int askStart = (prev_calculated > 1) ? (prev_calculated - 1) : 0;
   double pt = _Point;
   int fallbackSpread = (int)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   if(fallbackSpread <= 0) fallbackSpread = (int)MathRound(InpEstimatedSpreadPips * 10);
   double curAsk = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

   for(int i = askStart; i < rates_total; i++)
   {
      if(i == rates_total - 1 && curAsk > 0)
         g_askBuffer[i] = curAsk;
      else
      {
         int sp = (i < ArraySize(spread) && spread[i] > 0) ? spread[i] : fallbackSpread;
         g_askBuffer[i] = close[i] + (sp * pt);
      }
   }

   g_dummyBuffer[rates_total - 1] = close[rates_total - 1];

   static datetime lastBarTime = 0;
   datetime currentBarTime = time[rates_total - 1];
   if(prev_calculated > 0 && currentBarTime == lastBarTime && !g_forceRecalc)
   {
      return rates_total;
   }
   lastBarTime = currentBarTime;
   g_forceRecalc = false;
   if(!InpShowBoxes) g_boxesVisible = false;

   // به‌روزرسانی بازه واحد تاریخی
   InitMasterHistory(InpHistoryMode, InpHistoryStartDate, InpHistoryDays);

   Print("DEBUG: OnCalculate start rates_total=", rates_total, " prev=", prev_calculated, " targetBars=", g_effectiveTargetBars);

   // پاکسازی اشیاء گرافیکی قبلی FlagPro
   ObjectsDeleteAll(0, FP_PREFIX + "BOX_");
   ObjectsDeleteAll(0, FP_PREFIX + "LBL_");
   ObjectsDeleteAll(0, FP_PREFIX + "IP_");
   ObjectsDeleteAll(0, FP_PREFIX + "RS_");
   ObjectsDeleteAll(0, FP_PREFIX + "SWAP_");
   ObjectsDeleteAll(0, FP_PREFIX + "STRUCT_");
   ObjectsDeleteAll(0, FP_PREFIX + "PIVOT_");
   ObjectsDeleteAll(0, FP_PREFIX + "ORIGIN_");

   ArrayResize(g_drawnBoxes, 0);
   g_boxCount = 0;
   ArrayResize(g_indepPivots, 0);
   g_indepCount = 0;

   ENUM_TIMEFRAMES tfArr[7]       = {InpTF1, InpTF2, InpTF3, InpTF4, InpTF5, InpTF6, InpTF7};
   bool            useArr[7]      = {InpUseTF1, InpUseTF2, InpUseTF3, InpUseTF4, InpUseTF5, InpUseTF6, InpUseTF7};
   color           tfColorArr[7]  = {InpColorTF1, InpColorTF2, InpColorTF3, InpColorTF4, InpColorTF5, InpColorTF6, InpColorTF7};
   int daysBackArr[7];

   // تنظیم خودکار و واحد تعداد روزهای تاریخچه برای تمام تایم‌فریم‌ها
   for(int s = 0; s < 7; s++)
      daysBackArr[s] = g_effectiveDaysBack;

   // تایم‌فریم‌های فعال معامله (با پشتیبانی از Auto-Sync با تستر)
   useArr[0] = false; // D1
   useArr[1] = false; // W1
   useArr[2] = false; // H4
   useArr[3] = false; // H1
   useArr[4] = ActiveUseTF5(); // M15
   useArr[5] = ActiveUseTF6(); // M5
   useArr[6] = ActiveUseTF7(); // M1

   // بارگذاری عمیق تاریخچه با محاسبه خودکار تعداد کندل‌ها جهت پوشش کامل بازه
   datetime fullTime[];
   double   fullHigh[], fullLow[], fullClose[];
   ArraySetAsSeries(fullTime,  false);
   ArraySetAsSeries(fullHigh,  false);
   ArraySetAsSeries(fullLow,   false);
   ArraySetAsSeries(fullClose, false);

   int targetBars = g_effectiveTargetBars;
   if(InpHistoryMode == HIST_ALL_AVAILABLE) targetBars = rates_total;
   if(targetBars > rates_total) targetBars = rates_total;

   int totalCopied = CopyTime(_Symbol, _Period, 0, targetBars, fullTime);
   if(totalCopied > 0)
   {
      CopyHigh(_Symbol, _Period, 0, totalCopied, fullHigh);
      CopyLow(_Symbol, _Period, 0, totalCopied, fullLow);
      CopyClose(_Symbol, _Period, 0, totalCopied, fullClose);
   }
   else
   {
      ArrayResize(fullTime, rates_total);
      ArrayResize(fullHigh, rates_total);
      ArrayResize(fullLow, rates_total);
      ArrayResize(fullClose, rates_total);
      ArrayCopy(fullTime, time);
      ArrayCopy(fullHigh, high);
      ArrayCopy(fullLow, low);
      ArrayCopy(fullClose, close);
      totalCopied = rates_total;
   }

   for(int s = 0; s < 7; s++)
   {
      if(!useArr[s]) continue;
      ProcessTF(tfArr[s], InpSwingBars, tfColorArr[s], fullTime, fullHigh, fullLow, totalCopied, daysBackArr[s]);
   }

   // پردازش خطوط شکست RS و برچسب‌گذاری گره‌ها
   ProcessRSLinesFromLSBoxes(fullTime, fullHigh, fullLow, totalCopied);

   // پردازش اولین گره بعد از پیووت مستقل به عنوان OInner
   ProcessOInnerBoxes();

   ProcessUniversalSwapLines(fullTime, fullHigh, fullLow, totalCopied);
   RenderAutoTradeSetups(fullTime, fullHigh, fullLow, fullClose, totalCopied);
   RenderFinalBoxes(fullTime, totalCopied);
   RenderFinalIndependentPivots(fullTime, fullHigh, fullLow, totalCopied);

   // حفظ و بازترسیم ستاپ باکس انتخاب‌شده تا با آمدن کندل‌های جدید پاک نشود
   if(g_selectedBoxName != "" || IsFocusModeActive())
   {
      for(int b = 0; b < g_boxCount; b++)
      {
         if(g_drawnBoxes[b].boxName == g_selectedBoxName)
         {
            HighlightBox(b, false);
            break;
         }
      }
   }

   // اکسپورت خودکار گزارش جامع ستاپ‌ها به فایل CSV
   ExportAllTradesToCSV();

   RenderVersionBadge("FlagPro Indicator", FLAGPRO_VERSION);
   RenderSyncStatusBadge();

   if(!(bool)MQLInfoInteger(MQL_TESTER)) ChartRedraw(0);
   return rates_total;
}

//+------------------------------------------------------------------+
//| ChartEvent function: Click on Box for On-Demand Trade Inspection |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
{
   if(id == CHARTEVENT_OBJECT_CLICK)
   {
      if(StringFind(sparam, FP_PREFIX + "BOX_") >= 0)
      {
         for(int b = 0; b < g_boxCount; b++)
         {
            if(g_drawnBoxes[b].boxName == sparam)
            {
               HighlightBox(b, true);
               break;
            }
         }
      }
   }
   else if(id == CHARTEVENT_CLICK)
   {
      // با کلیک روی فضای خالی چارت، حالت تمرکز بسته می‌شود
      if(IsFocusModeActive() || g_selectedBoxName != "")
      {
         ExitFocusMode();
         g_clickCounter = 0;
         ChartRedraw(0);
      }
   }
   else if(id == CHARTEVENT_KEYDOWN)
   {
      // فشردن کلید Escape در کیبورد برای خروج فوری از حالت تمرکز (Focus Mode)
      if(lparam == 27)
      {
         if(IsFocusModeActive() || g_selectedBoxName != "")
         {
            ExitFocusMode();
            ChartRedraw(0);
            Print("FlagPro: خروج از حالت تمرکز (Focus Mode) با فشردن کلید Escape.");
         }
      }
      // فشردن کلید B در کیبورد برای مخفی یا نمایان کردن فوری تمام باکس‌ها
      else if(lparam == 'B' || lparam == 'b')
      {
         g_boxesVisible = !g_boxesVisible;
         Print("FlagPro: وضعیت نمایش باکس‌ها: ", (g_boxesVisible ? "روشن (نمایان)" : "خاموش (مخفی)"));
         datetime tArr[];
         CopyTime(_Symbol, _Period, 0, 1, tArr);
         RenderFinalBoxes(tArr, 1);
         ChartRedraw(0);
      }
      // فشردن کلید A در کیبورد برای مخفی یا نمایان کردن خط قیمت اسک (Ask)
      else if(lparam == 'A' || lparam == 'a')
      {
         g_askLineVisible = !g_askLineVisible;
         PlotIndexSetInteger(0, PLOT_DRAW_TYPE, g_askLineVisible ? DRAW_LINE : DRAW_NONE);
         ChartRedraw(0);
         Print("FlagPro: وضعیت نمایش خط قیمت اسک (Ask): ", (g_askLineVisible ? "روشن (نمایان)" : "خاموش (مخفی)"));
      }
      // فشردن کلید S در کیبورد برای همگام‌سازی فوری با آخرین تست فعال استراتژی تستر (Sync)
      else if(lparam == 'S' || lparam == 's')
      {
         Print("🔄 FlagPro: درخواست همگام‌سازی دستی با آخرین تنظیمات استراتژی تستر...");
         if(CheckAndLoadActiveScenario(true))
         {
            g_forceRecalc = true;
            datetime tArr[];
            CopyTime(_Symbol, _Period, 0, 1, tArr);
            RenderFinalBoxes(tArr, 1);
            RenderSyncStatusBadge();
            ChartRedraw(0);
            PrintFormat("✅ FlagPro: با موفقیت با سناریوی تستر «%s» همگام شد.", g_syncScenarioName);
         }
         else
         {
            Print("⚠️ FlagPro: هیچ فایلی از استراتژی تستر یافت نشد یا تغییری نکرده است.");
         }
      }
   }
}
