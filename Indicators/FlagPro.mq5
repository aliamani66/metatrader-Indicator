//+------------------------------------------------------------------+
//| FlagPro.mq5                                                      |
//| Advanced Modular Multi-Timeframe Structure & Flag Indicator      |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""
#property version   "2.13"
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
//| ۱. 🎯 تنظیم بازه تاریخی و عملکرد                                  |
//+------------------------------------------------------------------+
input group "=== 🎯 ۱. تنظیم بازه تاریخی و عملکرد ==="
input datetime          InpHistoryStartDate   = D'2026.09.01 00:00';    // 📅 تاریخ شروع دلخواه (ابتدای ماه جاری)
input int               InpHistoryDays        = 10;                     // ⏳ یا تعداد روز گذشته (پیش‌فرض: ۱۰ روز برای پوشش کامل هفته و تست‌ها)
input ENUM_HISTORY_MODE InpHistoryMode        = HIST_DAYS_BACK;         // ⚙️ مبنای بازه تاریخی (تعداد روز گذشته / تاریخ شروع دلخواه / کل تاریخچه)
input bool              InpShowBoxes          = false;                  // 👁️ رسم باکس‌های قیمتی روی چارت (کلید B برای سوئیچ سریع)
input bool              InpAutoDrawTrades     = true;                   // 🎯 رسم معاملات (خطوط ورود، حد ضرر، تارگت‌ها و نتیجه) روی چارت
input bool              InpExportCSV          = true;                   // 📁 استخراج خودکار فایل CSV برای داشبورد

//+------------------------------------------------------------------+
//| ۲. 👑 سلاطین طلایی معاملاتی (Golden Kings)                      |
//+------------------------------------------------------------------+
input group "=== 👑 ۲. سلاطین طلایی معاملاتی (Golden Kings) ==="
input bool              InpOnlyTradeKings     = true;                   // 👑 فقط معامله و رسم سلاطین برگزیده (Kings Only)
input bool              InpEnableKingsM15     = true;                   // 👑 فعال‌سازی سلاطین تایم M15 (۲ ساختار برتر)
input bool              InpEnableKingsM5      = true;                   // 👑 فعال‌سازی سلاطین تایم M5 (۷ ساختار برتر)
input bool              InpEnableKingsM1      = true;                   // 👑 فعال‌سازی سلاطین تایم M1 (۹ ساختار برتر)
input bool              InpTradeOnlyGoldenKings = true;                 // 👑 قفل انحصاری سلاطین طلایی
input string            InpAllowedKingsList   = "";                     // 👑 لیست انحصاری سلاطین مجاز (جدا شده با کاما، مثلاً "S-RS|M1, Flag-BE|M1" - خالی = پیش‌فرض)
input bool              InpAllowOverlappingTrades = true;               // 🔓 اجازه معاملات همزمان (ستاپ‌های هم‌پوشان)

//+------------------------------------------------------------------+
//| ۳. 🛡️ فیلترهای ضد استاپ، کمیسیون و حد ضرر                      |
//+------------------------------------------------------------------+
input group "=== 🛡️ ۳. فیلترهای ضد استاپ، اصطکاک و حد ضرر ==="
input bool              InpEnableTradeSetup   = true;                   // فعال‌سازی ستاپ معاملاتی روی باکس‌ها
input double            InpSLOffsetPips       = 8.0;                    // 🛡️ فاصله اطمینان حد ضرر جهت فرار از شدوها (افست استاپ به پیپ)
#define InpRSPipBuffer InpSLOffsetPips
input bool              InpFilterNightHours   = true;                   // 🛡️ فیلتر ۱: مسدودسازی بازه شب ۲۱ تا ۰۱
input bool              InpFilterPreLondonHunt= true;                   // 🛡️ فیلتر ۲: مسدودسازی ساعت ۰۷:۰۰ قبل لندن
input bool              InpFilterToxicPatterns= true;                   // 🛡️ فیلتر ۳: حذف زنجیره‌های سمی
input bool              InpFilterSingleLS     = true;                   // 🛡️ فیلتر ۴: حذف باکس‌های منفرد LS
input bool              InpFilterPureFlags    = true;                   // 🛡️ فیلتر ۵: حذف فلگ‌های بدون تلاقی
input bool              InpFilterLowRewardVsFriction = true;            // 💰 فیلتر عدم ورود اگر سود کمتر از اصطکاک باشد
input double            InpBrokerCommissionPerLot    = 6.0;             // کمیسیون بروکر در هر ۱ لات کامل ($)
input double            InpEstimatedSpreadPips       = 0.8;             // اسپرد تخمینی معامله (پیپ)
input double            InpMinNetProfitRatioTP1      = 1.0;             // حداقل نسبت سود TP1 به کل اصطکاک

//+------------------------------------------------------------------+
//| ۴. ⏱️ تایم‌فریم‌های فعال معامله                                 |
//+------------------------------------------------------------------+
input group "=== ⏱️ ۴. تایم‌فریم‌های فعال معامله ==="
input bool              InpUseTF7             = true;                   // محاسبه ۱ دقیقه (M1)
input bool              InpUseTF6             = true;                   // محاسبه ۵ دقیقه (M5)
input bool              InpUseTF5             = true;                   // محاسبه ۱۵ دقیقه (M15)
input bool              InpTradeMacroTFs      = false;                  // معامله در تایم‌های ماکرو H1, H4, D1, W1 (پیش‌فرض: غیرفعال)

//+------------------------------------------------------------------+
//| ۵. 🎨 تنظیمات ظاهری، رسم خطوط و رنگ‌های چارت (پایین لیست)       |
//+------------------------------------------------------------------+
input group "=== 🎨 ۵. تنظیمات ظاهری، رسم خطوط و رنگ‌های چارت (پایین لیست) ==="
input ENUM_BOX_DISPLAY_FILTER InpBoxDisplayFilter = FILTER_TOP_WINNERS_ONLY; // فیلتر نمایش باکس‌ها (فقط سلاطین برگزیده)
input bool              InpHideFilteredBoxes  = true;                   // مخفی‌سازی باکس‌های فیلترشده از روی چارت
input bool              InpUniqueTradeColors  = true;                   // 🎨 رنگ مجزا برای هر معامله (تفکیک آسان معاملات همزمان)
input bool              InpShowTradeShading   = false;                  // 🎨 نمایش پس‌زمینه رنگی معاملات
input color             InpTradeEntryColor    = clrWhite;               // رنگ خط ورود به معامله (Entry)
input color             InpTradeSLColor       = clrDarkOrange;          // رنگ خط حد ضرر (SL - متمایز از قرمز تستر)
input color             InpTradeTPColor       = clrDodgerBlue;          // رنگ خطوط تارگت (TP - متمایز از سبز تستر)

input bool              InpShowAskLine        = true;                   // 🔴 رسم خط قیمت اسک Ask روی چارت (مشابه استراتژی تستر)
input color             InpAskLineColor       = C'220,75,75';           // 🎨 رنگ خط اسک (قرمز ملایم / مشابه استراتژی تستر)
input ENUM_LINE_STYLE   InpAskLineStyle       = STYLE_SOLID;            // 📏 استایل خط اسک (پیوسته / خط‌چین)
input int               InpAskLineWidth       = 1;                      // ✏️ ضخامت خط اسک

input ENUM_TIMEFRAMES   InpTF7                = PERIOD_M1;
input color             InpColorTF7           = clrYellow;              // رنگ تایم‌فریم M1
input ENUM_TIMEFRAMES   InpTF6                = PERIOD_M5;
input color             InpColorTF6           = clrAqua;                // رنگ تایم‌فریم M5
input ENUM_TIMEFRAMES   InpTF5                = PERIOD_M15;
input color             InpColorTF5           = clrLime;                // رنگ تایم‌فریم M15

input ENUM_TIMEFRAMES   InpTF4                = PERIOD_H1;
input bool              InpUseTF4             = false;                  // محاسبه یک‌ساعته (H1)
input color             InpColorTF4           = clrYellow;
input ENUM_TIMEFRAMES   InpTF3                = PERIOD_H4;
input bool              InpUseTF3             = false;                  // محاسبه چهارساعته (H4)
input color             InpColorTF3           = clrWhite;
input ENUM_TIMEFRAMES   InpTF2                = PERIOD_W1;
input bool              InpUseTF2             = false;                  // محاسبه هفتگی (W1)
input color             InpColorTF2           = clrDodgerBlue;
input ENUM_TIMEFRAMES   InpTF1                = PERIOD_D1;
input bool              InpUseTF1             = false;                  // محاسبه روزانه (D1)
input color             InpColorTF1           = clrMagenta;

input bool              InpShowMacroAlways    = false;
input bool              InpShowOnlyRSMicroBoxes = true;
input bool              InpShowNormalMicroBoxes = false;
input string            InpRSTagPrefix        = "RS";
input int               InpSwingBars          = 6;
input int               InpLineWidth          = 1;
input bool              InpShowLabel          = true;
input ENUM_LABEL_FORMAT InpLabelFormat        = LABEL_CONCISE;
input bool              InpRemoveOverlapping  = true;

input bool              InpHighlightIndepPivots = false;
input bool              InpOnlyPureIndependent = false;
input color             InpIndepColorHigh     = clrOrangeRed;
input color             InpIndepColorLow      = clrLime;
input int               InpIndepMarkCode      = 159;
input int               InpIndepMarkWidth     = 1;
input bool              InpIndepShowLabel     = false;

input bool              InpHighlightPreIP     = true;
input color             InpLSColorBull        = clrLimeGreen;
input color             InpLSColorBear        = clrCrimson;
input int               InpPreIPWidth         = 2;
input bool              InpPreIPShowLabel     = true;

input bool              InpEnableOriginLines  = false;
input bool              InpOriginRequireIndep = false;
input int               InpOriginDaysBack     = 0;
input bool              InpTargetD1           = true;
input bool              InpTargetH4           = true;
input bool              InpTargetH1           = true;
input bool              InpSourceH1           = true;
input bool              InpSourceM15          = true;
input bool              InpSourceM5           = true;
input bool              InpSourceM1           = true;
input color             InpOriginColorLow     = clrAqua;
input color             InpOriginColorHigh    = clrMagenta;
input int               InpOriginLineWidth    = 1;
input ENUM_LABEL_STYLE  InpOriginLabelStyle   = LABEL_COMPACT;

input bool              InpHighlightBreakoutFlags = true;
input color             InpRSColorBull        = clrDodgerBlue;
input color             InpRSColorBear        = clrOrangeRed;
input color             InpComboColorBull     = clrYellow;
input color             InpComboColorBear     = clrMagenta;
input int               InpBreakoutFlagWidth  = 3;
input bool              InpBreakoutFlagShowLabel = true;

input bool              InpHighlightOInner    = true;
input color             InpOInnerColorBull    = clrSpringGreen;
input color             InpOInnerColorBear    = clrHotPink;
input int               InpOInnerWidth        = 3;
input bool              InpOInnerShowLabel    = true;

input bool              InpEnableSwapLines    = true;
input color             InpSwapColorBull      = clrCyan;
input color             InpSwapColorBear      = clrOrange;
input int               InpSwapLineWidth      = 1;
input int               InpSwapBoxWidth       = 2;
input ENUM_LINE_STYLE   InpSwapLineStyle      = STYLE_DOT;

input bool              InpApplyProTheme      = true;
input bool              InpHideGrid           = true;
input bool              InpHideVolumes        = true;

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
   RenderVersionBadge("FlagPro Indicator", FLAGPRO_VERSION);
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

   // منحصراً ۳ تایم‌فریم M15، M5 و M1 فعال هستند (D1, W1, H4, H1 خاموش)
   useArr[0] = false; // D1
   useArr[1] = false; // W1
   useArr[2] = false; // H4
   useArr[3] = false; // H1

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

   RenderVersionBadge("FlagPro Indicator", FLAGPRO_VERSION);

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
      // فشردن کلید A در کیبورد برای مخفی یا نمایان کردن خط قیمت اسک (Ask)
      else if(lparam == 'A' || lparam == 'a')
      {
         g_askLineVisible = !g_askLineVisible;
         PlotIndexSetInteger(0, PLOT_DRAW_TYPE, g_askLineVisible ? DRAW_LINE : DRAW_NONE);
         ChartRedraw(0);
         Print("FlagPro: وضعیت نمایش خط قیمت اسک (Ask): ", (g_askLineVisible ? "روشن (نمایان)" : "خاموش (مخفی)"));
      }
   }
}
