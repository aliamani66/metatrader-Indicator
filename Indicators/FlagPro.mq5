//+------------------------------------------------------------------+
//| FlagPro.mq5                                                      |
//| Advanced Modular Multi-Timeframe Structure & Flag Indicator      |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 1
#property indicator_plots   1
#property indicator_label1  "FlagPro Active"
#property indicator_type1   DRAW_NONE

double g_dummyBuffer[];

#include <FlagPro\Flag_Types.mqh>

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                 |
//+------------------------------------------------------------------+
input group "=== Macro Timeframes (غیرفعال) ==="
input ENUM_TIMEFRAMES InpTF1      = PERIOD_D1;
input bool             InpUseTF1  = false;          // محاسبه روزانه (D1)
input color            InpColorTF1 = clrMagenta;

input ENUM_TIMEFRAMES InpTF2      = PERIOD_W1;
input bool             InpUseTF2  = false;          // محاسبه هفتگی (W1)
input color            InpColorTF2 = clrDodgerBlue;

input ENUM_TIMEFRAMES InpTF3      = PERIOD_H4;
input bool             InpUseTF3  = false;          // محاسبه چهارساعته (H4)
input color            InpColorTF3 = clrWhite;

input ENUM_TIMEFRAMES InpTF4      = PERIOD_H1;
input bool             InpUseTF4  = false;          // محاسبه یک‌ساعته (H1)
input color            InpColorTF4 = clrYellow;

input group "=== Backtest & History Settings (تنظیمات بک‌تست از ابتدای ۲۰۲۵) ==="
input datetime         InpBacktestStartDate = D'2025.01.01 00:00'; // 📅 تاریخ شروع محاسبات و معاملات (پیش‌فرض: ابتدای ۲۰۲۵)
input int              InpBacktestDays = 1000;       // تعداد روزهای بک‌تست (۱۰۰۰ روز جهت پوشش کامل از ابتدای ۲۰۲۵ تا اکنون)
input bool             InpExportCSV    = true;       // استخراج خودکار فایل CSV (فعال برای تولید آنی دیتای داشبورد)

input group "=== Active Trading Timeframes (فقط تایم‌های فعال: M15, M5, M1) ==="
input ENUM_TIMEFRAMES InpTF5      = PERIOD_M15;
input bool             InpUseTF5  = true;           // محاسبه ۱۵ دقیقه (M15)
input color            InpColorTF5 = clrLime;
input int              InpM15DaysBack = 1000;        // تاریخچه ۱۵ دقیقه (۱۰۰۰ روز - از ابتدای ۲۰۲۵)

input ENUM_TIMEFRAMES InpTF6      = PERIOD_M5;
input bool             InpUseTF6  = true;           // محاسبه ۵ دقیقه (M5)
input color            InpColorTF6 = clrAqua;
input int              InpM5DaysBack = 1000;         // تاریخچه ۵ دقیقه (۱۰۰۰ روز - از ابتدای ۲۰۲۵)

input ENUM_TIMEFRAMES InpTF7      = PERIOD_M1;
input bool             InpUseTF7  = true;           // محاسبه ۱ دقیقه (M1)
input color            InpColorTF7 = clrYellow;
input int              InpM1DaysBack = 1000;         // تاریخچه ۱ دقیقه (۱۰۰۰ روز - از ابتدای ۲۰۲۵)

input group "=== Smart Visibility & Display (نمایش هوشمند چارت) ==="
input bool             InpShowBoxes             = false;   // 👁️ نمایش تمام باکس‌های قیمتی روی چارت (پیش‌فرض: کاملاً هیدن و خاموش)
input bool             InpShowMacroAlways       = false;  // نمایش همیشگی باکس‌های ماکرو (W1, D1, H4)
input bool             InpShowOnlyRSMicroBoxes  = true;   // در تایم‌های ریز فقط باکس‌های دارای شرط RS نمایش داده شوند
input bool             InpShowNormalMicroBoxes  = false;  // رسم کامل همه باکس‌های چارت
input string           InpRSTagPrefix           = "RS";   // پیشوند تگ‌های هوشمند (RS)

input group "=== 👑 سلاطین برگزیده معاملاتی بر مبنای تایم‌فریم (Golden Kings) ==="
input ENUM_BOX_DISPLAY_FILTER InpBoxDisplayFilter = FILTER_TOP_WINNERS_ONLY; // فیلتر نمایش باکس‌ها (فقط سلاطین برگزیده)
input bool InpOnlyTradeKings      = true; // 👑 فقط معامله و رسم ۱۸ سلطان برگزیده (Kings Only)
input bool InpEnableKingsM15      = true; // 👑 فعال‌سازی سلاطین تایم M15 (۲ ساختار برتر)
input bool InpEnableKingsM5       = true; // 👑 فعال‌سازی سلاطین تایم M5 (۷ ساختار برتر)
input bool InpEnableKingsM1       = true; // 👑 فعال‌سازی سلاطین تایم M1 (۹ ساختار برتر)

input group "=== 🛡️ فیلترهای هوشمند ضد استاپ (Anti-SL Filters) ==="
input bool InpFilterSingleLS     = true;   // 🛡️ فیلتر ۱: حذف باکس‌های منفرد LS
input bool InpFilterNightHours   = true;   // 🛡️ فیلتر ۲: مسدودسازی بازه شب ۲۱ تا ۰۱
input bool InpFilterPreLondonHunt= true;   // 🛡️ فیلتر ۳: مسدودسازی ساعت ۰۷:۰۰ قبل لندن
input bool InpFilterToxicPatterns= true;   // 🛡️ فیلتر ۴: حذف زنجیره‌های سمی
input bool InpFilterPureFlags    = true;   // 🛡️ فیلتر ۵: حذف فلگ‌های بدون تلاقی
input bool InpHideFilteredBoxes  = true;   // مخفی‌سازی باکس‌های فیلترشده از روی چارت (روشن)

input group "=== 💰 فیلتر اقتصادی و اصطکاک کارمزد (Friction & Commission Filter) ==="
input bool   InpFilterLowRewardVsFriction = true;   // 💰 فیلتر عدم ورود اگر سود کمتر از کمیسیون باشد
input double InpBrokerCommissionPerLot    = 6.0;    // کمیسیون بروکر در هر ۱ لات کامل ($)
input double InpEstimatedSpreadPips       = 0.8;    // اسپرد تخمینی معامله (پیپ)
input double InpMinNetProfitRatioTP1      = 1.0;    // حداقل نسبت سود TP1 به کل اصطکاک

input group "=== Structure Calculation (matches MarketStructure_v2) ==="
input int              InpSwingBars   = 6;           // عمق امواج ماژور (Swing Bars)
input int              InpMaxBarsTF   = 2000000;     // حداکثر کندل‌های محاسبه (۲ میلیون کندل - پوشش کامل تمام تایم‌ها از اول ۲۰۲۵)

input group "=== Visuals ==="
input int              InpLineWidth   = 1;           // ضخامت خط باکس‌ها (1 = نازک و ظریف)
input bool             InpShowLabel   = true;        // نمایش برچسب تایم‌فریم
input ENUM_LABEL_FORMAT InpLabelFormat = LABEL_CONCISE; // فرمت برچسب نام (کلاسیک و کوتاه / زنجیره‌ای)
input bool             InpRemoveOverlapping = true;  // حذف باکس‌های هم‌پوشان تکراری

input group "=== Independent Pivots (پیووت‌های مستقل) ==="
input bool             InpHighlightIndepPivots = false;       // هایلایت پیووت‌های مستقل خارج از پرچم (غیرفعال)
input bool             InpOnlyPureIndependent  = false;       // فقط نمایش پیووت‌های خالص و غیر وابسته
input color            InpIndepColorHigh       = clrOrangeRed; // رنگ سقف مستقل
input color            InpIndepColorLow        = clrLime;      // رنگ کف مستقل
input int              InpIndepMarkCode        = 159;          // کد نماد مارکر (دایره توپر)
input int              InpIndepMarkWidth       = 1;            // سایز مارکر
input bool             InpIndepShowLabel       = false;       // نمایش برچسب تایم‌فریم روی پیووت مستقل (غیرفعال)

input group "=== Pre-IP Box Highlight (باکس ماقبل پیووت مستقل - LS) ==="
input bool             InpHighlightPreIP        = true;         // فعال‌سازی تگ و هایلایت باکس LS
input color            InpLSColorBull           = clrLimeGreen; // رنگ LS صعودی (منتهی به سقف)
input color            InpLSColorBear           = clrCrimson;   // رنگ LS نزولی (منتهی به کف)
input int              InpPreIPWidth            = 2;            // ضخامت باکس ماقبل پیووت مستقل
input bool             InpPreIPShowLabel        = true;         // نمایش برچسب Pre-IP روی باکس

input group "=== Multi-Timeframe Origin Lines (خطوط پیووت منشأ چندگانه) ==="
input bool             InpEnableOriginLines     = false;        // فعال‌سازی رسم خطوط افقی منشأ پیووت‌ها
input bool             InpOriginRequireIndep    = false;        // فقط پیووت‌های مستقل منشأ باشند
input int              InpOriginDaysBack        = 0;            // روزهای محاسبه خطوط منشأ (0 = همه)

input bool             InpTargetD1              = true;         // بررسی پیووت‌های مستقل روزانه (D1)
input bool             InpTargetH4              = true;         // بررسی پیووت‌های مستقل چهارساعته (H4)
input bool             InpTargetH1              = true;         // بررسی پیووت‌های مستقل یک‌ساعته (H1)

input bool             InpSourceH1              = true;         // رسم منشأ یک‌ساعته (H1)
input bool             InpSourceM15             = true;         // رسم منشأ ۱۵ دقیقه (M15)
input bool             InpSourceM5              = true;         // رسم منشأ ۵ دقیقه (M5)
input bool             InpSourceM1              = true;         // رسم منشأ ۱ دقیقه (M1)

input color            InpOriginColorLow        = clrAqua;      // رنگ خط کف منشأ (صعودی)
input color            InpOriginColorHigh       = clrMagenta;   // رنگ خط سقف منشأ (نزولی)
input int              InpOriginLineWidth       = 1;            // ضخامت خط افقی
input ENUM_LABEL_STYLE InpOriginLabelStyle      = LABEL_COMPACT;// نحوه نمایش برچسب روی خطوط منشأ

input group "=== Breakout Flags / RS Boxes (فلگ‌های واکنش و شکست) ==="
input bool             InpHighlightBreakoutFlags = true;        // هایلایت فلگ‌های نقطه شکست
input color            InpRSColorBull           = clrDodgerBlue;// رنگ RS صعودی
input color            InpRSColorBear           = clrOrangeRed; // رنگ RS نزولی
input color            InpComboColorBull        = clrYellow;    // رنگ اشتراک LS+RS صعودی
input color            InpComboColorBear        = clrMagenta;   // رنگ اشتراک LS+RS نزولی
input int              InpBreakoutFlagWidth     = 3;            // ضخامت خط فلگ‌های نقطه شکست
input bool             InpBreakoutFlagShowLabel = true;         // نمایش برچسب BO-Flag روی باکس

input group "=== OInner Boxes (گره بعد از پیووت مستقل) ==="
input bool             InpHighlightOInner       = true;         // هایلایت اولین گره بعد از پیووت مستقل
input color            InpOInnerColorBull       = clrSpringGreen; // رنگ OInner صعودی
input color            InpOInnerColorBear       = clrHotPink;     // رنگ OInner نزولی
input int              InpOInnerWidth           = 3;            // ضخامت خط باکس OInner
input bool             InpOInnerShowLabel       = true;         // نمایش برچسب OInner روی باکس

input group "=== Universal Swap Lines (امتداد باکس‌ها و سواپ) ==="
input bool             InpEnableSwapLines       = true;         // فعال‌سازی رسم امتداد باکس‌های سواپ
input color            InpSwapColorBull         = clrCyan;      // رنگ خط سواپ صعودی
input color            InpSwapColorBear         = clrOrange;    // رنگ خط سواپ نزولی
input int              InpSwapLineWidth         = 1;            // ضخامت خط شکست سواپ
input int              InpSwapBoxWidth          = 2;            // ضخامت کادر باکس‌های سواپ
input ENUM_LINE_STYLE  InpSwapLineStyle         = STYLE_DOT;    // استایل پیش‌فرض سواپ

input group "=== Trade Setup & Simulator (ستاپ معامله و بک‌تست) ==="
input bool             InpEnableTradeSetup      = true;         // فعال‌سازی ستاپ معاملاتی روی باکس‌ها
input bool             InpAutoDrawTrades        = true;         // 🎯 رسم خودکار گرافیک معاملات فعال‌شده (Entry/SL/TP) روی چارت
input bool             InpTradeOnlyGoldenKings  = true;         // 👑 فقط معامله سلاطین طلایی برگزیده (سلاطین ۲۰ گانه)
input bool             InpAllowOverlappingTrades = true;        // 🔓 اجازه معاملات همزمان (هر ستاپ معتبری مستقل معامله می‌شود)
input bool             InpShowTradeShading      = false;        // 🎨 نمایش پس‌زمینه رنگی معاملات (پیش‌فرض: خاموش)
input double           InpSLOffsetPips          = 3.0;          // 🛡️ فاصله اطمینان حد ضرر جهت فرار از شدوها (افست استاپ به پیپ - پیش‌فرض ۳ پیپ)
#define InpRSPipBuffer InpSLOffsetPips
input color            InpTradeEntryColor       = clrWhite;     // رنگ خط ورود به معامله (Entry)
input color            InpTradeSLColor          = clrRed;       // رنگ خط حد ضرر (SL)
input color            InpTradeTPColor          = clrLimeGreen; // رنگ خطوط تارگت (TP)
input bool             InpTradeMacroTFs         = false;        // معامله در تایم‌های ماکرو H1, H4, D1, W1 (پیش‌فرض: غیرفعال)

input group "=== Neutral Pro Chart Theme ==="
input bool             InpApplyProTheme = true;        // اعمال تم حرفه‌ای خنثی
input bool             InpHideGrid      = true;        // حذف گرید از چارت
input bool             InpHideVolumes   = true;        // حذف نمودار حجم

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
   g_testerStartBase = 0;
   g_boxesVisible = InpShowBoxes;
   SetIndexBuffer(0, g_dummyBuffer, INDICATOR_DATA);
   ApplyProChartTheme();

   ArrayResize(g_tradeSetups, 0);
   g_tradeCount = 0;
   ObjectsDeleteAll(0, FP_PREFIX);
   ChartRedraw(0);
   g_forceRecalc = true;
   IndicatorSetString(INDICATOR_SHORTNAME, "FlagPro v1.00");
   Print("🚀 FlagPro v1.00 آماده است: معماری کاملاً ماژولار و تمیز.");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                       |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   ArrayResize(g_tradeSetups, 0);
   g_tradeCount = 0;
   ObjectsDeleteAll(0, FP_PREFIX);
   ChartRedraw(0);
   g_testerStartBase = 0;
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

   Print("DEBUG: OnCalculate start rates_total=", rates_total, " prev=", prev_calculated);

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
   int effectiveDays = InpBacktestDays;
   if(InpBacktestStartDate > 0)
   {
      int startDays = (int)((TimeCurrent() - InpBacktestStartDate) / 86400) + 15;
      if(startDays > effectiveDays) effectiveDays = startDays;
   }

   if((bool)MQLInfoInteger(MQL_TESTER))
   {
      daysBackArr[0] = 0;
      daysBackArr[1] = 0;
      daysBackArr[2] = 0;
      daysBackArr[3] = 0;
      daysBackArr[4] = MathMin(InpM15DaysBack, effectiveDays);
      daysBackArr[5] = MathMin(InpM5DaysBack, effectiveDays);
      daysBackArr[6] = MathMin(InpM1DaysBack, effectiveDays);
   }
   else
   {
      daysBackArr[0] = 0;
      daysBackArr[1] = 0;
      daysBackArr[2] = 0;
      daysBackArr[3] = 0;
      daysBackArr[4] = MathMax(InpM15DaysBack, effectiveDays);
      daysBackArr[5] = MathMax(InpM5DaysBack, effectiveDays);
      daysBackArr[6] = MathMax(InpM1DaysBack, effectiveDays);
   }

   // منحصراً ۳ تایم‌فریم M15، M5 و M1 فعال هستند (D1, W1, H4, H1 خاموش)
   useArr[0] = false; // D1
   useArr[1] = false; // W1
   useArr[2] = false; // H4
   useArr[3] = false; // H1

   for(int s = 0; s < 7; s++)
   {
      if(!useArr[s]) continue;
      ProcessTF(tfArr[s], InpSwingBars, tfColorArr[s], time, high, low, rates_total, daysBackArr[s]);
   }

   // پردازش خطوط شکست RS و برچسب‌گذاری گره‌ها
   ProcessRSLinesFromLSBoxes(time, high, low, rates_total);

   // پردازش اولین گره بعد از پیووت مستقل به عنوان OInner
   ProcessOInnerBoxes();

   // بارگذاری عمیق تاریخچه یک‌ماهه جهت پوشش کامل تمام ۳۰ روز (حتی اگر کاربر در چارت اسکرول نکرده باشد)
   datetime fullTime[];
   double   fullHigh[], fullLow[], fullClose[];
   ArraySetAsSeries(fullTime,  false);
   ArraySetAsSeries(fullHigh,  false);
   ArraySetAsSeries(fullLow,   false);
   ArraySetAsSeries(fullClose, false);

   int targetBars = MathMax(InpMaxBarsTF, rates_total);
   int totalCopied = CopyTime(_Symbol, _Period, 0, targetBars, fullTime);
   if(totalCopied > rates_total)
   {
      CopyHigh(_Symbol, _Period, 0, totalCopied, fullHigh);
      CopyLow(_Symbol, _Period, 0, totalCopied, fullLow);
      CopyClose(_Symbol, _Period, 0, totalCopied, fullClose);

      ProcessUniversalSwapLines(fullTime, fullHigh, fullLow, totalCopied);
      RenderAutoTradeSetups(fullTime, fullHigh, fullLow, fullClose, totalCopied);
      RenderFinalBoxes(fullTime, totalCopied);
      RenderFinalIndependentPivots(fullTime, fullHigh, fullLow, totalCopied);
   }
   else
   {
      ProcessUniversalSwapLines(time, high, low, rates_total);
      RenderAutoTradeSetups(time, high, low, close, rates_total);
      RenderFinalBoxes(time, rates_total);
      RenderFinalIndependentPivots(time, high, low, rates_total);
   }

   // حفظ و بازترسیم ستاپ باکس انتخاب‌شده تا با آمدن کندل‌های جدید پاک نشود
   if(g_selectedBoxName != "")
   {
      for(int b = 0; b < g_boxCount; b++)
      {
         if(g_drawnBoxes[b].boxName == g_selectedBoxName)
         {
            HighlightBox(b);
            break;
         }
      }
   }

   // اکسپورت خودکار گزارش جامع ستاپ‌ها به فایل CSV
   ExportAllTradesToCSV();

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
               HighlightBox(b);
               break;
            }
         }
      }
   }
   else if(id == CHARTEVENT_CLICK)
   {
      if(g_selectedBoxName != "")
      {
         g_clickCounter++;
         if(g_clickCounter >= 2)
         {
            ClearBoxHighlight();
            g_clickCounter = 0;
            ChartRedraw(0);
         }
      }
   }
   else if(id == CHARTEVENT_KEYDOWN)
   {
      // فشردن کلید B در کیبورد برای مخفی یا نمایان کردن فوری تمام باکس‌ها
      if(lparam == 'B' || lparam == 'b')
      {
         g_boxesVisible = !g_boxesVisible;
         Print("FlagPro: وضعیت نمایش باکس‌ها: ", (g_boxesVisible ? "روشن (نمایان)" : "خاموش (مخفی)"));
         datetime tArr[];
         CopyTime(_Symbol, _Period, 0, 1, tArr);
         RenderFinalBoxes(tArr, 1);
         ChartRedraw(0);
      }
   }
}
