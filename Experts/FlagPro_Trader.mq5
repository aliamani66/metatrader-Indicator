//+------------------------------------------------------------------+
//|                                              FlagPro_Trader.mq5  |
//|                         FlagPro Autonomous Strategy Trader EA    |
//|            Executes Real MT5 Orders in Tester & Live Accounts    |
//+------------------------------------------------------------------+
#property copyright   "FlagPro Quantitative Trading Systems"
#property link        "https://github.com/aliamani66/metatrader-Indicator"
#property version     "1.00"
#property description "ربات معامله‌گر مستقل FlagPro - ثبت معاملات رسمی در تب Operations متاتریدر ۵"
#property tester_indicator "FlagPro.ex5"

#include <Trade\Trade.mqh>
#include <FlagPro\Flag_Types.mqh>

//+------------------------------------------------------------------+
//| INPUT PARAMETERS - تنظیمات معامله‌گری و مدیریت سرمایه               |
//+------------------------------------------------------------------+
input group "=== 🤖 تنظیمات معامله‌گری و مدیریت ریسک (Trading & Risk) ==="
input double           InpFixedLot               = 0.10;         // حجم ثابت معامله به لات (Fixed Lot)
input bool             InpUseRiskPercent         = false;        // محاسبه پویای حجم بر اساس درصد ریسک حساب
input double           InpRiskPercent            = 1.0;          // درصد ریسک در هر معامله (% Equity Risk)
input int              InpTargetTPLevel          = 2;            // تارگت خروج برای اعمال در بروکر (1=TP1, 2=TP2, 3=TP3, 4=TP4)
input int              InpMaxOpenPositions       = 1;            // حداکثر پوزیشن‌های باز همزمان (انضباط سرمایه)
input ulong            InpMagicNumber            = 777123;       // شناسه جادویی معامله‌گر (Magic Number)
input int              InpSlippagePoints         = 20;           // حداکثر لغزش قیمت مجاز (Slippage Points)

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

input group "=== Backtest & History Settings (تنظیمات بک‌تست) ==="
input int              InpBacktestDays = 14;         // تعداد روزهای بک‌تست و خروجی گزارش (۱۴ روز)
input bool             InpExportCSV    = false;      // استخراج خودکار فایل CSV (پیش‌فرض خاموش)

input group "=== Active Trading Timeframes (فقط تایم‌های فعال: M15, M5, M1) ==="
input ENUM_TIMEFRAMES InpTF5      = PERIOD_M15;
input bool             InpUseTF5  = true;           // محاسبه ۱۵ دقیقه (M15)
input color            InpColorTF5 = clrLime;
input int              InpM15DaysBack = 14;          // تاریخچه ۱۵ دقیقه (۱۴ روز)

input ENUM_TIMEFRAMES InpTF6      = PERIOD_M5;
input bool             InpUseTF6  = true;           // محاسبه ۵ دقیقه (M5)
input color            InpColorTF6 = clrAqua;
input int              InpM5DaysBack = 7;            // تاریخچه ۵ دقیقه (۷ روز)

input ENUM_TIMEFRAMES InpTF7      = PERIOD_M1;
input bool             InpUseTF7  = true;           // محاسبه ۱ دقیقه (M1)
input color            InpColorTF7 = clrYellow;
input int              InpM1DaysBack = 3;            // تاریخچه ۱ دقیقه (۳ روز)

input group "=== Smart Visibility & Display (نمایش هوشمند چارت) ==="
input bool             InpShowBoxes             = true;    // 👁️ نمایش تمام باکس‌های قیمتی روی چارت (کلید میانبر B در کیبورد)
input bool             InpShowMacroAlways       = false;  // نمایش همیشگی باکس‌های ماکرو (W1, D1, H4)
input bool             InpShowOnlyRSMicroBoxes  = true;   // در تایم‌های ریز فقط باکس‌های دارای شرط RS نمایش داده شوند
input bool             InpShowNormalMicroBoxes  = false;  // رسم کامل همه باکس‌های چارت
input string           InpRSTagPrefix           = "RS";   // پیشوند تگ‌های هوشمند (RS)

input group "=== 🏆 فیلتر نمایش الگوهای برنده (Box Display Filter) ==="
input ENUM_BOX_DISPLAY_FILTER InpBoxDisplayFilter = FILTER_TOP_WINNERS_ONLY;
input bool InpShow_LSBU_OInnerBE = true;   // 💎 نمایش الگوی طلایی LS-BU > OInner-BE
input bool InpShow_LSBE          = false;  // 💎 نمایش الگوی طلایی LS-BE
input bool InpShow_OInnerBE_RSBE = false;  // 💎 نمایش الگوی طلایی OInner-BE > RS-BE
input bool InpShow_SLS           = false;  // ⚡ نمایش سواپ‌های ال‌اس S-LS
input bool InpShow_SOInner       = false;  // ⚡ نمایش سواپ‌های او‌اینر S-OInner
input bool InpShow_OtherBoxes    = false;  // 📦 نمایش سایر باکس‌های عادی و فرعی

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
input int              InpMaxBarsTF   = 3000;        // حداکثر کندل‌های محاسبه (پوشش بهینه و سریع)

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
input bool             InpTradeOnlyGoldenKings  = true;         // 👑 معامله منحصراً فقط روی ۷ سلطان طلایی (وین‌ریت بالای ۶۰٪)
input bool             InpPreventOverlappingTrades = true;      // 🛡️ جلوگیری از تداخل معاملات (تا بسته نشدن معامله جاری، معامله جدید باز نشود)
input bool             InpShowTradeShading      = true;         // 🎨 نمایش پس‌زمینه رنگی معاملات (سبز/قرمز)
input double           InpRSPipBuffer           = 2.0;          // بافر حد ضرر برای RS و فلگ‌ها (پیپ)
input color            InpTradeEntryColor       = clrWhite;     // رنگ خط ورود به معامله (Entry)
input color            InpTradeSLColor          = clrRed;       // رنگ خط حد ضرر (SL)
input color            InpTradeTPColor          = clrLimeGreen; // رنگ خطوط تارگت (TP)
input bool             InpTradeMacroTFs         = false;        // معامله در تایم‌های ماکرو H1, H4, D1, W1 (پیش‌فرض: غیرفعال)

input group "=== Neutral Pro Chart Theme ==="
input bool             InpApplyProTheme = true;        // اعمال تم حرفه‌ای خنثی
input bool             InpHideGrid      = true;        // حذف گرید از چارت
input bool             InpHideVolumes   = true;        // حذف نمودار حجم

// ماژول‌های موتور FlagPro
#include <FlagPro\Flag_Pivots.mqh>
#include <FlagPro\Flag_Boxes.mqh>
#include <FlagPro\Flag_Filters.mqh>
#include <FlagPro\Flag_Backtest.mqh>
#include <FlagPro\Flag_Render.mqh>

// متغیرهای گلوبال اکسپرت
CTrade         m_trade;
int            m_indicatorHandle = INVALID_HANDLE;
string         m_executedTradesKeys[];

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   m_trade.SetExpertMagicNumber(InpMagicNumber);
   m_trade.SetDeviationInPoints(InpSlippagePoints);

   uint filling = (uint)SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   if((filling & SYMBOL_FILLING_FOK) != 0)
      m_trade.SetTypeFilling(ORDER_FILLING_FOK);
   else if((filling & SYMBOL_FILLING_IOC) != 0)
      m_trade.SetTypeFilling(ORDER_FILLING_IOC);
   else
      m_trade.SetTypeFilling(ORDER_FILLING_RETURN);

   m_indicatorHandle = iCustom(_Symbol, _Period, "FlagPro");
   if(m_indicatorHandle == INVALID_HANDLE)
   {
      Print("⚠️ هشدار: اندیکاتور بصری FlagPro بارگذاری نشد. موتور معاملاتی فعال است.");
   }

   ArrayResize(m_executedTradesKeys, 0);
   ArrayResize(g_tradeSetups, 0);
   g_tradeCount = 0;
   g_testerStartBase = 0;

   Print("🚀 FlagPro_Trader EA آماده به کار است. ثبت مستقیم معاملات در تب Operations فعال شد.");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(m_indicatorHandle != INVALID_HANDLE)
   {
      IndicatorRelease(m_indicatorHandle);
      m_indicatorHandle = INVALID_HANDLE;
   }
   ArrayResize(m_executedTradesKeys, 0);
   ArrayResize(g_tradeSetups, 0);
   g_tradeCount = 0;
}

//+------------------------------------------------------------------+
//| شمارش پوزیشن‌های باز این اکسپرت                                 |
//+------------------------------------------------------------------+
int CountOpenPositions()
{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) == _Symbol)
      {
         if(PositionGetInteger(POSITION_MAGIC) == (long)InpMagicNumber)
            count++;
      }
   }
   return count;
}

//+------------------------------------------------------------------+
//| محاسبه پویای حجم معامله                                          |
//+------------------------------------------------------------------+
double CalculateTradeLot(double entryPrice, double slPrice)
{
   if(!InpUseRiskPercent || entryPrice <= 0 || slPrice <= 0)
      return InpFixedLot;

   double riskPoints = MathAbs(entryPrice - slPrice) / _Point;
   if(riskPoints <= 0) return InpFixedLot;

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskMoney = equity * (InpRiskPercent / 100.0);

   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0) tickSize = _Point;
   if(tickValue <= 0) tickValue = 1.0;

   double pointValue = tickValue * (_Point / tickSize);
   double riskPerLot = riskPoints * pointValue;
   if(riskPerLot <= 0) return InpFixedLot;

   double lot = riskMoney / riskPerLot;
   double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   lot = MathFloor(lot / lotStep) * lotStep;
   if(lot < minLot) lot = minLot;
   if(lot > maxLot) lot = maxLot;

   return NormalizeDouble(lot, 2);
}

//+------------------------------------------------------------------+
//| بررسی اینکه آیا این معامله قبلاً تیکت گرفته است یا خیر            |
//+------------------------------------------------------------------+
bool IsTradeAlreadyExecuted(const string tradeKey)
{
   for(int i = 0; i < ArraySize(m_executedTradesKeys); i++)
   {
      if(m_executedTradesKeys[i] == tradeKey)
         return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   static datetime lastCandleTime = 0;
   datetime currentCandleTime = iTime(_Symbol, _Period, 0);

   MqlRates rates[];
   ArraySetAsSeries(rates, false);
   int ratesTotal = CopyRates(_Symbol, _Period, 0, InpMaxBarsTF, rates);
   if(ratesTotal < 20) return;

   datetime chartTime[];
   double chartHigh[], chartLow[], chartClose[];
   ArrayResize(chartTime, ratesTotal);
   ArrayResize(chartHigh, ratesTotal);
   ArrayResize(chartLow, ratesTotal);
   ArrayResize(chartClose, ratesTotal);

   for(int i = 0; i < ratesTotal; i++)
   {
      chartTime[i]  = rates[i].time;
      chartHigh[i]  = rates[i].high;
      chartLow[i]   = rates[i].low;
      chartClose[i] = rates[i].close;
   }

   if(currentCandleTime != lastCandleTime)
   {
      lastCandleTime = currentCandleTime;

      ArrayResize(g_drawnBoxes, 0);
      g_boxCount = 0;
      ArrayResize(g_indepPivots, 0);
      g_indepCount = 0;

      ENUM_TIMEFRAMES tfArr[7]      = {PERIOD_D1, PERIOD_W1, PERIOD_H4, PERIOD_H1, InpTF5, InpTF6, InpTF7};
      bool            useArr[7]     = {false, false, false, false, InpUseTF5, InpUseTF6, InpUseTF7};
      color           tfColorArr[7] = {clrNONE, clrNONE, clrNONE, clrNONE, InpColorTF5, InpColorTF6, InpColorTF7};
      int             daysBackArr[7]= {0, 0, 0, 0, InpM15DaysBack, InpM5DaysBack, InpM1DaysBack};

      for(int i = 0; i < 7; i++)
      {
         if(!useArr[i]) continue;
         ProcessTF(tfArr[i], InpSwingBars, tfColorArr[i],
                   chartTime, chartHigh, chartLow, ratesTotal, daysBackArr[i]);
      }

      ProcessRSLinesFromLSBoxes(chartTime, chartHigh, chartLow, ratesTotal);
      ProcessOInnerBoxes();
      ProcessUniversalSwapLines(chartTime, chartHigh, chartLow, ratesTotal);

      RenderAutoTradeSetups(chartTime, chartHigh, chartLow, chartClose, ratesTotal);
   }

   // بررسی ارسال سفارش جدید به تب Operations
   if(CountOpenPositions() >= InpMaxOpenPositions)
      return;

   for(int t = 0; t < g_tradeCount; t++)
   {
      if(g_tradeSetups[t].isClosed)
         continue;

      string tradeKey = g_tradeSetups[t].boxName + "_" + IntegerToString((int)g_tradeSetups[t].entryTime);
      if(IsTradeAlreadyExecuted(tradeKey))
         continue;

      double targetTP = g_tradeSetups[t].tp2;
      if(InpTargetTPLevel == 1)      targetTP = g_tradeSetups[t].tp1;
      else if(InpTargetTPLevel == 2) targetTP = g_tradeSetups[t].tp2;
      else if(InpTargetTPLevel == 3) targetTP = g_tradeSetups[t].tp3;
      else if(InpTargetTPLevel == 4) targetTP = g_tradeSetups[t].tp4;

      double sl = NormalizeDouble(g_tradeSetups[t].slPrice, _Digits);
      double tp = NormalizeDouble(targetTP, _Digits);
      double lot = CalculateTradeLot(g_tradeSetups[t].entryPrice, sl);

      string comment = "FlagPro [" + g_tradeSetups[t].boxRole + "]";

      bool success = false;
      if(g_tradeSetups[t].isBuy)
      {
         double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         success = m_trade.Buy(lot, _Symbol, ask, sl, tp, comment);
      }
      else
      {
         double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         success = m_trade.Sell(lot, _Symbol, bid, sl, tp, comment);
      }

      if(success)
      {
         int newSize = ArraySize(m_executedTradesKeys) + 1;
         ArrayResize(m_executedTradesKeys, newSize);
         m_executedTradesKeys[newSize - 1] = tradeKey;

         PrintFormat("✅ معامله رسمی در تب Operations ثبت شد | تیکت: %d | جهت: %s | حجم: %.2f | ورود: %.5f | حد ضرر: %.5f | حد سود: %.5f | الگو: %s",
                     m_trade.ResultOrder(),
                     (g_tradeSetups[t].isBuy ? "BUY" : "SELL"),
                     lot,
                     (g_tradeSetups[t].isBuy ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID)),
                     sl, tp, g_tradeSetups[t].boxRole);
         break;
      }
      else
      {
         PrintFormat("❌ خطا در ثبت سفارش متاتریدر: کد %d", m_trade.ResultRetcode());
      }
   }
}
//+------------------------------------------------------------------+
