//+------------------------------------------------------------------+
//|                                              FlagPro_Trader.mq5  |
//|                         FlagPro Autonomous Strategy Trader EA    |
//|            Executes Real MT5 Orders in Tester & Live Accounts    |
//|                 Multi-Stage Scale-Out & Auto Break-Even          |
//+------------------------------------------------------------------+
#property copyright   "FlagPro Quantitative Trading Systems"
#property link        "https://github.com/aliamani66/metatrader-Indicator"
#property version     "1.01"
#property description "ربات معامله‌گر مستقل FlagPro - سیستم خروج چندمرحله‌ای (Scale-Out) و بریک‌ایون خودکار"

#include <Trade\Trade.mqh>
#include <FlagPro\Flag_Types.mqh>

//+------------------------------------------------------------------+
//| INPUT PARAMETERS - تنظیمات معامله‌گری و خروج چندمرحله‌ای            |
//+------------------------------------------------------------------+
input group "=== 🎯 سیستم خروج ۴ مرحله‌ای (4-Stage Scale-Out & Trailing) ==="
input bool             InpEnableScaleOut         = true;         // فعال‌سازی سیستم خروج ۴ مرحله‌ای
input double           InpLot_TP1                = 0.01;         // 🎯 حجم خروج مرحله ۱ در TP1 (25% کل حجم)
input double           InpLot_TP2                = 0.01;         // 🎯 حجم خروج مرحله ۲ در TP2 (25% کل حجم)
input double           InpLot_TP3                = 0.01;         // 🎯 حجم خروج مرحله ۳ در TP3 (25% کل حجم)
input double           InpLot_TP4                = 0.01;         // 🎯 حجم خروج مرحله ۴ در TP4 (25% کل حجم - رانر)
input bool             InpMoveToBreakEven        = true;         // 🛡️ مرحله ۱: انتقال به بریک‌ایون پس از تاچ TP1 (Break-Even)
input double           InpBEBufferPips           = 1.0;          // بافر سود بریک‌ایون جهت پوشش اسپرد و کمیسیون (پیپ)
input bool             InpTrailToTP1             = true;         // 🔒 مرحله ۲: تریل و قفل حد ضرر به TP1 پس از لمس TP2
input bool             InpTrailToTP2             = true;         // 🚀 مرحله ۳: تریل و قفل حد ضرر به TP2 پس از لمس TP3
input double           InpMaxSLPips              = 0.0;          // حداکثر حد ضرر مجاز به پیپ (0 = منطبق بر خط قرمز چارت)
input int              InpMaxOpenGroups          = 5;            // حداکثر تعداد ستاپ‌های همزمان فعال (امکان معاملات هم‌زمان)
input ulong            InpMagicNumber            = 777123;       // شناسه جادویی معامله‌گر (Magic Number)
input int              InpSlippagePoints         = 20;           // حداکثر لغزش قیمت مجاز (Slippage Points)

enum ENUM_CONSEC_ACTION
{
   CONSEC_ACTION_NONE     = 0, // بدون فیوز (غیرفعال)
   CONSEC_ACTION_SKIP_1   = 1, // رد کردن ۱ معامله بعدی (Skip 1 Trade)
   CONSEC_ACTION_SKIP_2   = 2, // رد کردن ۲ معامله بعدی (Skip 2 Trades)
   CONSEC_ACTION_SKIP_DAY = 3  // توقف معاملات تا پایان امروز (Pause Today)
};

input group "=== 🎛️ اعمال سناریوهای فیلتر داشبورد (Dashboard Scenario Config) ==="
input string             InpScenarioName          = "Default";   // 🏷️ نام سناریوی تنظیمی (جهت لاگ)
input double             InpMinTradePotential     = 0.0;         // 💰 حداقل کف سود دلاری معامله (اسلایدر داشبورد)
input string             InpAllowedTradingHours   = "";          // ⏰ ساعات مجاز معامله (مثلاً "10,11,12,13,14,15,16,17,18,19" - خالی = ۲۴ ساعته)
input int                InpConsecLossTrigger     = 0;           // 🚨 فیوز استاپ‌های متوالی (۰ = خاموش، ۲ = توقف بعد از ۲ استاپ)
input ENUM_CONSEC_ACTION InpConsecLossAction      = CONSEC_ACTION_SKIP_1; // ⚡ اقدام فیوز پس از حد ضررهای متوالی
input string             InpDisabledKingsList     = "";          // 🚫 لیست سلاطین غیرمجاز (جدا شده با کاما، مثلاً "OInner-BE [M1]")

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
input bool             InpExportCSV    = true;       // استخراج خودکار فایل CSV (فعال برای همگام‌سازی داشبورد)

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
input bool             InpShowBoxes             = false;   // 👁️ نمایش تمام باکس‌های قیمتی روی چارت (پیش‌فرض: خاموش)
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

// ماژول‌های موتور FlagPro
#include <FlagPro\Flag_Pivots.mqh>
#include <FlagPro\Flag_Boxes.mqh>
#include <FlagPro\Flag_Filters.mqh>
#include <FlagPro\Flag_Backtest.mqh>
#include <FlagPro\Flag_Render.mqh>

// ساختار مدیریت گروهی پوزیشن‌های ۴ مرحله‌ای
struct SActiveTradeGroup
{
   string   tradeKey;
   bool     isBuy;
   double   entryPrice;
   double   initialSL;
   double   tp1, tp2, tp3, tp4;
   ulong    tickets[4];
   bool     beApplied;
   bool     trailTP1Applied;
   bool     trailTP2Applied;
   bool     isFinished;
};

// متغیرهای گلوبال اکسپرت
CTrade            m_trade;
string            m_executedTradesKeys[];
SActiveTradeGroup m_activeGroups[];

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

   // اعمال تم شیک چارت (حذف چهارخونه‌های گرید و تنظیم رنگ‌های نرم)
   ApplyProChartTheme();

   g_boxesVisible = InpShowBoxes;
   if(!InpShowBoxes)
   {
      ObjectsDeleteAll(0, FP_PREFIX + "BOX_");
      ObjectsDeleteAll(0, FP_PREFIX + "LBL_");
   }
   if(!InpShowTradeShading)
   {
      DeleteAllTradeShadings();
   }

   ArrayResize(m_executedTradesKeys, 0);
   ArrayResize(m_activeGroups, 0);
   ArrayResize(g_tradeSetups, 0);
   g_tradeCount = 0;
   g_testerStartBase = 0;

   Print("🚀 FlagPro_Trader EA آماده به کار است. سیستم خروج ۴ مرحله‌ای (Scale-Out) و بریک‌ایون فعال شد.");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   ArrayResize(m_executedTradesKeys, 0);
   ArrayResize(m_activeGroups, 0);
   ArrayResize(g_tradeSetups, 0);
   g_tradeCount = 0;
   g_testerStartBase = 0;
}

//+------------------------------------------------------------------+
//| شمارش تعداد گروه‌های فعال معاملاتی                                |
//+------------------------------------------------------------------+
int CountOpenPositionGroups()
{
   int count = 0;
   for(int g = 0; g < ArraySize(m_activeGroups); g++)
   {
      if(m_activeGroups[g].isFinished) continue;
      bool hasOpen = false;
      for(int p = 0; p < 4; p++)
      {
         if(m_activeGroups[g].tickets[p] > 0)
         {
            if(PositionSelectByTicket(m_activeGroups[g].tickets[p]))
            {
               hasOpen = true;
               break;
            }
         }
      }
      if(hasOpen) count++;
      else m_activeGroups[g].isFinished = true;
   }
   return count;
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
//| ارسال ایمن سفارش با مدیریت حالت‌های پر شدن بروکر (Filling Modes)  |
//+------------------------------------------------------------------+
ulong SafeSendOrder(bool isBuy, double lot, double price, double sl, double tp, string comment)
{
   bool success = false;
   if(isBuy)
      success = m_trade.Buy(lot, _Symbol, price, sl, tp, comment);
   else
      success = m_trade.Sell(lot, _Symbol, price, sl, tp, comment);

   if(!success && (m_trade.ResultRetcode() == 10030 || m_trade.ResultRetcode() == TRADE_RETCODE_INVALID_FILL))
   {
      m_trade.SetTypeFilling(ORDER_FILLING_IOC);
      price = isBuy ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
      success = isBuy ? m_trade.Buy(lot, _Symbol, price, sl, tp, comment)
                      : m_trade.Sell(lot, _Symbol, price, sl, tp, comment);
      if(!success)
      {
         m_trade.SetTypeFilling(ORDER_FILLING_FOK);
         price = isBuy ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
         success = isBuy ? m_trade.Buy(lot, _Symbol, price, sl, tp, comment)
                         : m_trade.Sell(lot, _Symbol, price, sl, tp, comment);
      }
   }

   if(success)
      return m_trade.ResultOrder();
   return 0;
}

//+------------------------------------------------------------------+
//| مدیریت بریک‌ایون و تریل سود پوزیشن‌های فعال (Scale-Out Management) |
//+------------------------------------------------------------------+
void ManageActiveTradeGroups()
{
   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;
   double currentBid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double currentAsk = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

   for(int g = 0; g < ArraySize(m_activeGroups); g++)
   {
      if(m_activeGroups[g].isFinished) continue;

      bool anyOpen = false;
      bool ticketOpen[4] = {false, false, false, false};

      for(int p = 0; p < 4; p++)
      {
         if(m_activeGroups[g].tickets[p] > 0)
         {
            if(PositionSelectByTicket(m_activeGroups[g].tickets[p]))
            {
               ticketOpen[p] = true;
               anyOpen = true;
            }
         }
      }

      if(!anyOpen)
      {
         m_activeGroups[g].isFinished = true;
         continue;
      }

      bool isBuy = m_activeGroups[g].isBuy;
      double currentP = isBuy ? currentBid : currentAsk;

      // مرحله ۱: انتقال به بریک‌ایون (Break-Even) پس از تاچ TP1 یا خروج پوزیشن اول
      if(InpMoveToBreakEven && !m_activeGroups[g].beApplied)
      {
         bool tp1Reached = (!ticketOpen[0] && m_activeGroups[g].tickets[0] > 0) ||
                           (isBuy ? (currentP >= m_activeGroups[g].tp1) : (currentP <= m_activeGroups[g].tp1));

         if(tp1Reached)
         {
            double beBuffer = InpBEBufferPips * pipSize;
            double bePrice = isBuy ? (m_activeGroups[g].entryPrice + beBuffer) : (m_activeGroups[g].entryPrice - beBuffer);
            bePrice = NormalizeDouble(bePrice, _Digits);

            double targetTPs[4] = {m_activeGroups[g].tp1, m_activeGroups[g].tp2, m_activeGroups[g].tp3, m_activeGroups[g].tp4};
            for(int p = 1; p < 4; p++)
            {
               if(ticketOpen[p])
               {
                  m_trade.PositionModify(m_activeGroups[g].tickets[p], bePrice, targetTPs[p]);
               }
            }
            m_activeGroups[g].beApplied = true;
            PrintFormat("🛡️ [FlagPro BE] تارگت TP1 لمس شد! حد ضرر پوزیشن‌های باقی‌مانده به نقطه ورود (%.5f) منتقل گردید.", bePrice);
         }
      }

      // مرحله ۲: تریل حد ضرر به TP1 پس از لمس TP2 جهت قفل سود قطعی
      if(InpTrailToTP1 && m_activeGroups[g].beApplied && !m_activeGroups[g].trailTP1Applied)
      {
         bool tp2Reached = (!ticketOpen[1] && m_activeGroups[g].tickets[1] > 0) ||
                           (isBuy ? (currentP >= m_activeGroups[g].tp2) : (currentP <= m_activeGroups[g].tp2));

         if(tp2Reached)
         {
            double trailSL = NormalizeDouble(m_activeGroups[g].tp1, _Digits);
            double targetTPs[4] = {m_activeGroups[g].tp1, m_activeGroups[g].tp2, m_activeGroups[g].tp3, m_activeGroups[g].tp4};
            for(int p = 2; p < 4; p++)
            {
               if(ticketOpen[p])
               {
                  m_trade.PositionModify(m_activeGroups[g].tickets[p], trailSL, targetTPs[p]);
               }
            }
            m_activeGroups[g].trailTP1Applied = true;
            PrintFormat("🔒 [FlagPro Profit Lock] تارگت TP2 لمس شد! حد ضرر پوزیشن‌های ۳ و ۴ به TP1 (%.5f) تریل شد.", trailSL);
         }
      }

      // مرحله ۳: تریل حد ضرر به TP2 پس از لمس TP3 تا پوزیشن ۴ تارگت نهایی ۱:۴ را بدود
      if(InpTrailToTP2 && m_activeGroups[g].trailTP1Applied && !m_activeGroups[g].trailTP2Applied)
      {
         bool tp3Reached = (!ticketOpen[2] && m_activeGroups[g].tickets[2] > 0) ||
                           (isBuy ? (currentP >= m_activeGroups[g].tp3) : (currentP <= m_activeGroups[g].tp3));

         if(tp3Reached)
         {
            double trailSL = NormalizeDouble(m_activeGroups[g].tp2, _Digits);
            if(ticketOpen[3])
            {
               m_trade.PositionModify(m_activeGroups[g].tickets[3], trailSL, m_activeGroups[g].tp4);
            }
            m_activeGroups[g].trailTP2Applied = true;
            PrintFormat("🚀 [FlagPro Runner Lock] تارگت TP3 لمس شد! حد ضرر پوزیشن ۴ به TP2 (%.5f) تریل شد تا تارگت ۱:۴ شکار شود.", trailSL);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//| فیلتر ۱ سناریو: بررسی مجاز بودن سلطان معاملاتی                    |
//+------------------------------------------------------------------+
bool IsKingAllowedByScenario(ENUM_TIMEFRAMES tf, string role)
{
   if(StringLen(InpDisabledKingsList) == 0) return true;
   string kKey1 = role + "|" + TFName(tf);
   string kKey2 = role + " [" + TFName(tf) + "]";
   if(StringFind(InpDisabledKingsList, kKey1) >= 0 || StringFind(InpDisabledKingsList, kKey2) >= 0)
      return false;
   return true;
}

//+------------------------------------------------------------------+
//| فیلتر ۲ سناریو: بررسی ساعات مجاز معامله طبق سناریو                |
//+------------------------------------------------------------------+
bool IsHourAllowedByScenario(datetime t)
{
   if(StringLen(InpAllowedTradingHours) == 0) return true;
   MqlDateTime dt;
   TimeToStruct(t, dt);
   string h2 = StringFormat("%02d", dt.hour);
   string h1 = IntegerToString(dt.hour);

   if(StringFind(InpAllowedTradingHours, h2) >= 0 || StringFind(InpAllowedTradingHours, h1) >= 0)
      return true;

   return false;
}

//+------------------------------------------------------------------+
//| فیلتر ۳ سناریو: بررسی حداقل پتانسیل سود معامله (اسلایدر کف سود)  |
//+------------------------------------------------------------------+
bool IsPotentialAllowedByScenario(double riskPoints)
{
   if(InpMinTradePotential <= 0.0) return true;
   double pot = (riskPoints * 0.04) * 2.5 - 0.44;
   return (pot >= InpMinTradePotential);
}

//+------------------------------------------------------------------+
//| فیلتر ۴ سناریو: بررسی فیوز استاپ‌های متوالی (Circuit Breaker)     |
//+------------------------------------------------------------------+
int      g_skippedSetupsCount = 0;
datetime g_lastLossTradeTime = 0;

bool IsConsecutiveLossAllowed()
{
   if(InpConsecLossTrigger <= 0) return true;

   HistorySelect(TimeCurrent() - 14 * 86400, TimeCurrent());
   int totalDeals = HistoryDealsTotal();
   int consecLoss = 0;
   datetime latestDealTime = 0;

   for(int i = totalDeals - 1; i >= 0; i--)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket <= 0) continue;
      long magic = HistoryDealGetInteger(ticket, DEAL_MAGIC);
      if(magic != InpMagicNumber) continue;
      long entryType = HistoryDealGetInteger(ticket, DEAL_ENTRY);
      if(entryType != DEAL_ENTRY_OUT && entryType != DEAL_ENTRY_INOUT) continue;

      double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT) 
                    + HistoryDealGetDouble(ticket, DEAL_SWAP) 
                    + HistoryDealGetDouble(ticket, DEAL_COMMISSION);

      if(profit < -0.001)
      {
         consecLoss++;
         if(latestDealTime == 0)
            latestDealTime = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
      }
      else if(profit > 0.001)
      {
         break;
      }
   }

   if(consecLoss >= InpConsecLossTrigger)
   {
      if(InpConsecLossAction == CONSEC_ACTION_SKIP_DAY)
      {
         MqlDateTime dtDeal, dtNow;
         TimeToStruct(latestDealTime, dtDeal);
         TimeToStruct(TimeCurrent(), dtNow);
         if(dtDeal.day == dtNow.day && dtDeal.mon == dtNow.mon && dtDeal.year == dtNow.year)
         {
            return false;
         }
      }
      else if(InpConsecLossAction == CONSEC_ACTION_SKIP_1 || InpConsecLossAction == CONSEC_ACTION_SKIP_2)
      {
         int maxSkips = (InpConsecLossAction == CONSEC_ACTION_SKIP_1) ? 1 : 2;
         if(latestDealTime != g_lastLossTradeTime)
         {
            g_lastLossTradeTime = latestDealTime;
            g_skippedSetupsCount = 0;
         }

         if(g_skippedSetupsCount < maxSkips)
         {
            g_skippedSetupsCount++;
            PrintFormat("🚨 فیوز هوشمند فعال شد: %d استاپ متوالی! ستاپ جاری رد شد (%d از %d معافیت).",
                        consecLoss, g_skippedSetupsCount, maxSkips);
            return false;
         }
      }
   }
   else
   {
      g_skippedSetupsCount = 0;
   }

   return true;
}

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
      int effectiveDays = InpBacktestDays;
      if(InpBacktestStartDate > 0)
      {
         int startDays = (int)((TimeCurrent() - InpBacktestStartDate) / 86400) + 15;
         if(startDays > effectiveDays) effectiveDays = startDays;
      }
      int             daysBackArr[7]= {0, 0, 0, 0, MathMax(InpM15DaysBack, effectiveDays), MathMax(InpM5DaysBack, effectiveDays), MathMax(InpM1DaysBack, effectiveDays)};

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

      if(!InpShowBoxes)
      {
         ObjectsDeleteAll(0, FP_PREFIX + "BOX_");
         ObjectsDeleteAll(0, FP_PREFIX + "LBL_");
      }
      if(!InpShowTradeShading)
      {
         DeleteAllTradeShadings();
      }
   }

   // مدیریت تریل و بریک‌ایون تمام معاملات باز روی هر تیک
   ManageActiveTradeGroups();

   // بررسی ارسال پوزیشن‌های جدید
   if(CountOpenPositionGroups() >= InpMaxOpenGroups)
      return;

   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;

   for(int t = 0; t < g_tradeCount; t++)
   {
      // 👑 فیلتر سلاطین برگزیده بر مبنای تایم‌فریم (Kings Only Filter)
      if((InpOnlyTradeKings || InpTradeOnlyGoldenKings) && !IsQualifiedKing(g_tradeSetups[t].tf, g_tradeSetups[t].boxRole))
         continue;

      // 🚫 فیلتر سناریوی داشبورد: بررسی سلاطین غیرمجاز انتخابی کاربر
      if(!IsKingAllowedByScenario(g_tradeSetups[t].tf, g_tradeSetups[t].boxRole))
         continue;

      // ⏰ فیلتر سناریوی داشبورد: ساعات مجاز معامله
      if(!IsHourAllowedByScenario(g_tradeSetups[t].entryTime))
         continue;

      // 💰 فیلتر سناریوی داشبورد: کف سود دلاری معامله
      if(!IsPotentialAllowedByScenario(g_tradeSetups[t].risk / _Point))
         continue;

      // 🚨 فیلتر سناریوی داشبورد: فیوز قطع معاملات پس از استاپ‌های متوالی
      if(!IsConsecutiveLossAllowed())
         continue;

      // 🛡️ فیلترهای تکمیلی ضد استاپ (فیلتر شبانه، اصطکاک و نویزها)
      if(IsSetupFilteredOut(g_tradeSetups[t].boxRole, g_tradeSetups[t].entryTime, g_tradeSetups[t].risk / _Point))
         continue;

      // فقط ستاپ‌هایی که در کندل جاری یا کندل قبلی فعال شده‌اند مجاز به اجرا هستند (نه ستاپ‌های تاریخچه!)
      if(g_tradeSetups[t].entryTime < chartTime[ratesTotal - 2])
         continue;

      string tradeKey = g_tradeSetups[t].boxName + "_" + IntegerToString((int)g_tradeSetups[t].entryTime);
      if(IsTradeAlreadyExecuted(tradeKey))
         continue;

      // ثبت کلید معامله در لیست پردازش‌شده‌ها تا در تیک‌های بعدی تکرار نشود
      int newSize = ArraySize(m_executedTradesKeys) + 1;
      ArrayResize(m_executedTradesKeys, newSize);
      m_executedTradesKeys[newSize - 1] = tradeKey;

      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      bool isBuy = g_tradeSetups[t].isBuy;
      double sendPrice = isBuy ? ask : bid;

      // حد ضرر دقیقاً مطابق با خط قرمز چارت (بدون هیچ مغایرت و تفاوتی)
      double sl = NormalizeDouble(g_tradeSetups[t].slPrice, _Digits);
      double riskDist = MathAbs(sendPrice - sl);

      double minStops = (double)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;
      if(minStops < 15.0 * _Point) minStops = 15.0 * _Point;

      if(InpMaxSLPips > 0 && riskDist > InpMaxSLPips * pipSize)
      {
         riskDist = InpMaxSLPips * pipSize;
         sl = NormalizeDouble(isBuy ? (sendPrice - riskDist) : (sendPrice + riskDist), _Digits);
      }
      else if(riskDist < minStops)
      {
         riskDist = minStops + 5.0 * _Point;
         sl = NormalizeDouble(isBuy ? (sendPrice - riskDist) : (sendPrice + riskDist), _Digits);
      }

      // تارگت‌ها دقیقاً منطبق بر خطوط سبز چارت (بدون هیچ مغایرت و تفاوتی)
      double tp1 = NormalizeDouble(g_tradeSetups[t].tp1, _Digits);
      double tp2 = NormalizeDouble(g_tradeSetups[t].tp2, _Digits);
      double tp3 = NormalizeDouble(g_tradeSetups[t].tp3, _Digits);
      double tp4 = NormalizeDouble(g_tradeSetups[t].tp4, _Digits);

      // اعتبارسنجی حداقل فاصله قانونی با بروکر
      if(isBuy)
      {
         if(tp1 <= sendPrice + minStops) tp1 = NormalizeDouble(sendPrice + minStops + 5.0 * _Point, _Digits);
         if(tp2 <= tp1) tp2 = NormalizeDouble(tp1 + 10.0 * _Point, _Digits);
         if(tp3 <= tp2) tp3 = NormalizeDouble(tp2 + 10.0 * _Point, _Digits);
         if(tp4 <= tp3) tp4 = NormalizeDouble(tp3 + 10.0 * _Point, _Digits);
      }
      else
      {
         if(tp1 >= sendPrice - minStops) tp1 = NormalizeDouble(sendPrice - minStops - 5.0 * _Point, _Digits);
         if(tp2 >= tp1) tp2 = NormalizeDouble(tp1 - 10.0 * _Point, _Digits);
         if(tp3 >= tp2) tp3 = NormalizeDouble(tp2 - 10.0 * _Point, _Digits);
         if(tp4 >= tp3) tp4 = NormalizeDouble(tp3 - 10.0 * _Point, _Digits);
      }

      double stageLots[4] = {InpLot_TP1, InpLot_TP2, InpLot_TP3, InpLot_TP4};
      double tps[4] = {tp1, tp2, tp3, tp4};
      ulong openedTickets[4] = {0, 0, 0, 0};
      int successfulOrders = 0;

      // باز کردن ۴ پوزیشن همزمان (هر کدام با تارگت‌های TP1 تا TP4 و حجم‌های تفکیکی)
      for(int p = 0; p < 4; p++)
      {
         if(stageLots[p] <= 0) continue;
         string comment = StringFormat("FP [%s] TP%d", g_tradeSetups[t].boxRole, p + 1);
         openedTickets[p] = SafeSendOrder(isBuy, stageLots[p], sendPrice, sl, tps[p], comment);
         if(openedTickets[p] > 0)
            successfulOrders++;
      }

      if(successfulOrders > 0)
      {
         // ثبت گروه معاملاتی جهت مدیریت بریک‌ایون و تریلینگ
         int gSize = ArraySize(m_activeGroups) + 1;
         ArrayResize(m_activeGroups, gSize);
         m_activeGroups[gSize - 1].tradeKey = tradeKey;
         m_activeGroups[gSize - 1].isBuy = isBuy;
         m_activeGroups[gSize - 1].entryPrice = sendPrice;
         m_activeGroups[gSize - 1].initialSL = sl;
         m_activeGroups[gSize - 1].tp1 = tp1;
         m_activeGroups[gSize - 1].tp2 = tp2;
         m_activeGroups[gSize - 1].tp3 = tp3;
         m_activeGroups[gSize - 1].tp4 = tp4;
         for(int p = 0; p < 4; p++) m_activeGroups[gSize - 1].tickets[p] = openedTickets[p];
         m_activeGroups[gSize - 1].beApplied = false;
         m_activeGroups[gSize - 1].trailTP1Applied = false;
         m_activeGroups[gSize - 1].trailTP2Applied = false;
         m_activeGroups[gSize - 1].isFinished = false;

         PrintFormat("✅ ۴ پوزیشن خروج چند مرحله‌ای با موفقیت ثبت شد | الگو: %s [%s] | جهت: %s | حجم‌ها: TP1=%.2f, TP2=%.2f, TP3=%.2f, TP4=%.2f | حد ضرر: %.5f | تارگت‌ها: TP1=%.5f, TP2=%.5f, TP3=%.5f, TP4=%.5f",
                     g_tradeSetups[t].boxRole, EnumToString(g_tradeSetups[t].tf),
                     (isBuy ? "BUY" : "SELL"), InpLot_TP1, InpLot_TP2, InpLot_TP3, InpLot_TP4, sl, tp1, tp2, tp3, tp4);
         break;
      }
   }
}
//+------------------------------------------------------------------+
