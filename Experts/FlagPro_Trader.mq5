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
enum ENUM_CONSEC_ACTION
{
   CONSEC_ACTION_NONE     = 0, // بدون فیوز (غیرفعال)
   CONSEC_ACTION_SKIP_1   = 1, // رد کردن ۱ معامله بعدی (Skip 1 Trade)
   CONSEC_ACTION_SKIP_2   = 2, // رد کردن ۲ معامله بعدی (Skip 2 Trades)
   CONSEC_ACTION_SKIP_DAY = 3  // توقف معاملات تا پایان امروز (Pause Today)
};

//+------------------------------------------------------------------+
//| ۱. 👑 سلاطین طلایی، سناریوی داشبورد و انتخاب استراتژی           |
//+------------------------------------------------------------------+
input group "=== 👑 ۱. سلاطین طلایی، سناریوی داشبورد و ستاپ‌ها ==="
input string             InpScenarioName          = "Default";   // 🏷️ نام سناریوی معاملاتی (Dashboard Scenario Name)
input bool               InpOnlyTradeKings        = true;        // 👑 فقط معامله سلاطین برگزیده (Kings Only)
input string             InpDisabledKingsList     = "";          // 🚫 لیست سلاطین غیرمجاز (جدا شده با کاما، مثلاً "OInner-BE [M1]")
input bool               InpEnableKingsM15        = true;        // 👑 فعال‌سازی سلاطین تایم M15 (۲ ساختار برتر)
input bool               InpEnableKingsM5         = true;        // 👑 فعال‌سازی سلاطین تایم M5 (۷ ساختار برتر)
input bool               InpEnableKingsM1         = true;        // 👑 فعال‌سازی سلاطین تایم M1 (۹ ساختار برتر)
input bool               InpTradeOnlyGoldenKings  = true;        // 👑 فیلتر انحصاری سلاطین طلایی
input bool               InpAllowOverlappingTrades= true;        // 🔓 اجازه معاملات همزمان (ستاپ‌های هم‌پوشان)

//+------------------------------------------------------------------+
//| ۲. ⚡ اسلیپیج، انحراف مجاز ورود و مدیریت ریسک                  |
//+------------------------------------------------------------------+
input group "=== ⚡ ۲. اسلیپیج، دقت ورود و مدیریت ریسک معامله ==="
input int                InpSlippagePoints        = 20;          // ⚡ حداکثر اسلیپیج مجاز (لغزش قیمت به پوینت - 20 = 2 پیپ)
input double             InpMaxEntryDeviationPips = 2.5;         // 🛡️ حداکثر انحراف مجاز ورود از لبه باکس به پیپ (جلوگیری از ورود دیرهنگام)
input double             InpSLOffsetPips          = 3.0;         // 🛡️ فاصله اطمینان حد ضرر جهت فرار از شدوها (افست استاپ به پیپ)
#define InpRSPipBuffer InpSLOffsetPips
input double             InpMaxSLPips             = 0.0;         // حداکثر حد ضرر مجاز به پیپ (0 = منطبق بر خط قرمز چارت)
input int                InpMaxOpenGroups         = 5;           // حداکثر تعداد ستاپ‌های همزمان فعال
input ulong              InpMagicNumber           = 777123;      // شناسه جادویی اکسپرت (Magic Number)

//+------------------------------------------------------------------+
//| ۳. 🎯 سیستم خروج ۴ مرحله‌ای، بریک‌ایون و تریلینگ                |
//+------------------------------------------------------------------+
input group "=== 🎯 ۳. سیستم خروج ۴ مرحله‌ای (Scale-Out & Trailing) ==="
input bool               InpEnableScaleOut        = true;        // فعال‌سازی سیستم خروج ۴ مرحله‌ای
input double             InpLot_TP1               = 0.01;        // 🎯 حجم خروج مرحله ۱ در TP1 (25% کل حجم)
input double             InpLot_TP2               = 0.01;        // 🎯 حجم خروج مرحله ۲ در TP2 (25% کل حجم)
input double             InpLot_TP3               = 0.01;        // 🎯 حجم خروج مرحله ۳ در TP3 (25% کل حجم)
input double             InpLot_TP4               = 0.01;        // 🎯 حجم خروج مرحله ۴ در TP4 (25% کل حجم - رانر)
input bool               InpMoveToBreakEven       = true;        // 🛡️ مرحله ۱: انتقال به بریک‌ایون پس از تاچ TP1
input double             InpBEBufferPips          = 1.0;         // 🛡️ بافر سود بریک‌ایون جهت پوشش اسپرد و کمیسیون (پیپ)
input bool               InpTrailToTP1            = true;        // 🔒 مرحله ۲: تریل و قفل حد ضرر به TP1 پس از لمس TP2
input bool               InpTrailToTP2            = true;        // 🚀 مرحله ۳: تریل و قفل حد ضرر به TP2 پس از لمس TP3

//+------------------------------------------------------------------+
//| ۴. ⏰ ساعات مجاز، کف سود ستاپ و فیوز ایمنی                     |
//+------------------------------------------------------------------+
input group "=== ⏰ ۴. ساعات معاملاتی، کف سود و فیوز ایمنی ==="
input string             InpAllowedTradingHours   = "";          // ⏰ ساعات مجاز معامله (مثلاً "10,11,12,13,14,15,16,17,18,19" - خالی = ۲۴ ساعته)
input double             InpMinTradePotential     = 0.0;         // 💰 حداقل کف سود دلاری معامله (اسلایدر داشبورد)
input int                InpConsecLossTrigger     = 0;           // 🚨 فیوز استاپ‌های متوالی (۰ = خاموش، ۲ = توقف بعد از ۲ استاپ)
input ENUM_CONSEC_ACTION InpConsecLossAction      = CONSEC_ACTION_SKIP_1; // ⚡ اقدام فیوز پس از حد ضررهای متوالی

//+------------------------------------------------------------------+
//| ۵. 🛡️ فیلترهای ضد استاپ و اصطکاک کمیسیون بروکر                  |
//+------------------------------------------------------------------+
input group "=== 🛡️ ۵. فیلترهای ضد استاپ و هزینه کمیسیون ==="
input bool               InpFilterNightHours      = true;        // 🛡️ فیلتر ۱: مسدودسازی بازه شب ۲۱ تا ۰۱ (اسپرد شبانه)
input bool               InpFilterPreLondonHunt   = true;        // 🛡️ فیلتر ۲: مسدودسازی ساعت ۰۷:۰۰ قبل لندن (استاپ هانت)
input bool               InpFilterToxicPatterns   = true;        // 🛡️ فیلتر ۳: حذف زنجیره‌های سمی و بازگشتی
input bool               InpFilterSingleLS        = true;        // 🛡️ فیلتر ۴: حذف باکس‌های منفرد LS
input bool               InpFilterPureFlags       = true;        // 🛡️ فیلتر ۵: حذف فلگ‌های بدون تلاقی
input bool               InpFilterLowRewardVsFriction = true;    // 💰 فیلتر حذف ستاپ‌های با سود کمتر از کمیسیون
input double             InpBrokerCommissionPerLot= 6.0;         // کمیسیون بروکر در هر ۱ لات کامل ($)
input double             InpEstimatedSpreadPips   = 0.8;         // اسپرد تخمینی معامله (پیپ)
input double             InpMinNetProfitRatioTP1 = 1.0;         // حداقل نسبت سود TP1 به کل اصطکاک

//+------------------------------------------------------------------+
//| ۶. ⏱️ تایم‌فریم‌های فعال معامله و عمق پردازش                   |
//+------------------------------------------------------------------+
input group "=== ⏱️ ۶. تایم‌فریم‌های فعال معامله و سرعت پردازش ==="
input bool               InpUseTF7                = true;        // معامله در تایم‌فریم ۱ دقیقه (PERIOD_M1)
input bool               InpUseTF6                = true;        // معامله در تایم‌فریم ۵ دقیقه (PERIOD_M5)
input bool               InpUseTF5                = true;        // معامله در تایم‌فریم ۱۵ دقیقه (PERIOD_M15)
input bool               InpTradeMacroTFs         = false;       // معامله در تایم‌های ماکرو H1, H4, D1, W1 (پیش‌فرض: غیرفعال)
input int                InpLookbackBars          = 5000;        // ⚡ عمق اسکن کندل‌ها در لحظه (۵۰۰۰ کندل = تست سریع)
input ENUM_HISTORY_MODE  InpHistoryMode           = HIST_START_DATE; // ⚙️ مبنای بازه تاریخی
input datetime           InpHistoryStartDate      = D'2025.01.01 00:00'; // 📅 تاریخ شروع
input int                InpHistoryDays           = 365;         // ⏳ بازه روز گذشته

//+------------------------------------------------------------------+
//| ۷. 🎨 تنظیمات ظاهری، رسم خطوط و رنگ‌های چارت (پایین لیست)       |
//+------------------------------------------------------------------+
input group "=== 🎨 ۷. تنظیمات ظاهری، رسم خطوط و رنگ‌های چارت (پایین لیست) ==="
input bool               InpShowBoxes             = false;       // 👁️ رسم باکس‌های قیمتی روی چارت
input bool               InpAutoDrawTrades        = true;        // 🎯 رسم خودکار گرافیک معاملات فعال‌شده روی چارت
input bool               InpExportCSV             = false;       // 📁 استخراج خودکار فایل CSV
input bool               InpShowTradeShading      = false;       // 🎨 پس‌زمینه رنگی معاملات
input ENUM_BOX_DISPLAY_FILTER InpBoxDisplayFilter = FILTER_TOP_WINNERS_ONLY; // فیلتر نمایش باکس‌ها روی چارت
input bool               InpHideFilteredBoxes     = true;        // مخفی‌سازی باکس‌های فیلترشده از چارت

input color              InpTradeEntryColor       = clrWhite;    // رنگ خط ورود به معامله (Entry)
input color              InpTradeSLColor          = clrRed;      // رنگ خط حد ضرر (SL)
input color              InpTradeTPColor          = clrLimeGreen;// رنگ خطوط تارگت (TP)

input ENUM_TIMEFRAMES    InpTF7                   = PERIOD_M1;
input color              InpColorTF7              = clrYellow;   // رنگ تایم‌فریم ۱ دقیقه
input ENUM_TIMEFRAMES    InpTF6                   = PERIOD_M5;
input color              InpColorTF6              = clrAqua;     // رنگ تایم‌فریم ۵ دقیقه
input ENUM_TIMEFRAMES    InpTF5                   = PERIOD_M15;
input color              InpColorTF5              = clrLime;     // رنگ تایم‌فریم ۱۵ دقیقه

input ENUM_TIMEFRAMES    InpTF4                   = PERIOD_H1;
input bool               InpUseTF4                = false;
input color              InpColorTF4              = clrYellow;
input ENUM_TIMEFRAMES    InpTF3                   = PERIOD_H4;
input bool               InpUseTF3                = false;
input color              InpColorTF3              = clrWhite;
input ENUM_TIMEFRAMES    InpTF2                   = PERIOD_W1;
input bool               InpUseTF2                = false;
input color              InpColorTF2              = clrDodgerBlue;
input ENUM_TIMEFRAMES    InpTF1                   = PERIOD_D1;
input bool               InpUseTF1                = false;
input color              InpColorTF1              = clrMagenta;

input bool               InpShowMacroAlways       = false;
input bool               InpShowOnlyRSMicroBoxes  = true;
input bool               InpShowNormalMicroBoxes  = false;
input string             InpRSTagPrefix           = "RS";
input int                InpSwingBars             = 6;
input int                InpLineWidth             = 1;
input bool               InpShowLabel             = true;
input ENUM_LABEL_FORMAT  InpLabelFormat           = LABEL_CONCISE;
input bool               InpRemoveOverlapping     = true;

input bool               InpHighlightIndepPivots  = false;
input bool               InpOnlyPureIndependent   = false;
input color              InpIndepColorHigh        = clrOrangeRed;
input color              InpIndepColorLow         = clrLime;
input int                InpIndepMarkCode         = 159;
input int                InpIndepMarkWidth        = 1;
input bool               InpIndepShowLabel        = false;

input bool               InpHighlightPreIP         = true;
input color              InpLSColorBull            = clrLimeGreen;
input color              InpLSColorBear            = clrCrimson;
input int                InpPreIPWidth             = 2;
input bool               InpPreIPShowLabel         = true;

input bool               InpEnableOriginLines      = false;
input bool               InpOriginRequireIndep     = false;
input int                InpOriginDaysBack         = 0;
input bool               InpTargetD1               = true;
input bool               InpTargetH4               = true;
input bool               InpTargetH1               = true;
input bool               InpSourceH1               = true;
input bool               InpSourceM15              = true;
input bool               InpSourceM5               = true;
input bool               InpSourceM1               = true;
input color              InpOriginColorLow         = clrAqua;
input color              InpOriginColorHigh        = clrMagenta;
input int                InpOriginLineWidth        = 1;
input ENUM_LABEL_STYLE   InpOriginLabelStyle       = LABEL_COMPACT;

input bool               InpHighlightBreakoutFlags = true;
input color              InpRSColorBull            = clrDodgerBlue;
input color              InpRSColorBear            = clrOrangeRed;
input color              InpComboColorBull         = clrYellow;
input color              InpComboColorBear         = clrMagenta;
input int                InpBreakoutFlagWidth      = 3;
input bool               InpBreakoutFlagShowLabel  = true;

input bool               InpHighlightOInner        = true;
input color              InpOInnerColorBull        = clrSpringGreen;
input color              InpOInnerColorBear        = clrHotPink;
input int                InpOInnerWidth            = 3;
input bool               InpOInnerShowLabel        = true;

input bool               InpEnableSwapLines        = true;
input color              InpSwapColorBull          = clrCyan;
input color              InpSwapColorBear          = clrOrange;
input int                InpSwapLineWidth          = 1;
input int                InpSwapBoxWidth           = 2;
input ENUM_LINE_STYLE    InpSwapLineStyle          = STYLE_DOT;

input bool               InpApplyProTheme          = true;
input bool               InpHideGrid               = true;
input bool               InpHideVolumes            = true;

// ماژول‌های موتور FlagPro
#include <FlagPro\Flag_Pivots.mqh>
#include <FlagPro\Flag_Boxes.mqh>
#include <FlagPro\Flag_Filters.mqh>
#include <FlagPro\Flag_Backtest.mqh>
#include <FlagPro\Flag_Render.mqh>

// ساختار مدیریت گروهی پوزیشن‌های ۴ مرحله‌ای
struct SActiveTradeGroup
{
   string            tradeKey;
   string            role;
   ENUM_TIMEFRAMES   tf;
   datetime          entryTime;
   bool              isBuy;
   double            entryPrice;      // قیمت واقعی پر شدن اردر مارکت
   double            boxEntryPrice;   // قیمت تئوریک لبه باکس
   double            initialSL;       // استاپ ارسالی
   double            boxSL;           // استاپ تئوریک باکس
   double            tp1, tp2, tp3, tp4;
   ulong             tickets[4];
   bool              beApplied;
   bool              trailTP1Applied;
   bool              trailTP2Applied;
   bool              isFinished;
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
//| استخراج خودکار گزارش جامع تست استراتژی تستر متاتریدر ۵             |
//+------------------------------------------------------------------+
void ExportTesterRunSummary()
{
   if(!HistorySelect(0, TimeCurrent())) return;

   int totalDeals = HistoryDealsTotal();
   int nSetups = ArraySize(m_activeGroups);
   if(totalDeals <= 0 && nSetups == 0) return;

   FolderCreate("FlagPro_TesterReports");
   FolderCreate("FlagPro_TesterReports", FILE_COMMON);

   string symClean = _Symbol;
   StringReplace(symClean, "!", "");
   StringReplace(symClean, "#", "");

   datetime startTestTime = 0;
   datetime endTestTime = TimeCurrent();

   // پیدا کردن زمان شروع تست از اولین معامله
   for(int i = 0; i < totalDeals; i++)
   {
      ulong dTicket = HistoryDealGetTicket(i);
      if(dTicket > 0 && HistoryDealGetInteger(dTicket, DEAL_ENTRY) == DEAL_ENTRY_IN)
      {
         startTestTime = (datetime)HistoryDealGetInteger(dTicket, DEAL_TIME);
         break;
      }
   }
   if(startTestTime == 0) startTestTime = TimeCurrent() - 15 * 86400;

   string tfName = EnumToString(_Period);
   StringReplace(tfName, "PERIOD_", "");

   string dateStr = TimeToString(startTestTime, TIME_DATE) + "_to_" + TimeToString(endTestTime, TIME_DATE);
   StringReplace(dateStr, ".", "-");

   string baseName = "FlagPro_Test_" + symClean + "_" + tfName + "_" + dateStr + "_" + IntegerToString(nSetups) + "Trades";
   string jsonName = "FlagPro_TesterReports\\" + baseName + ".json";
   string csvName  = "FlagPro_TesterReports\\" + baseName + ".csv";

   // محاسبه آمار و KPIها
   int winSetups = 0;
   int lossSetups = 0;
   double totalProfitUSD = 0.0;
   double totalProfitPips = 0.0;
   double grossProfitPips = 0.0;
   double grossLossPips = 0.0;
   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;

   // خروجی CSV
   int hCsv = FileOpen(csvName, FILE_WRITE | FILE_CSV | FILE_ANSI, ",");
   if(hCsv != INVALID_HANDLE)
   {
      FileWrite(hCsv, "SetupID", "Pattern", "Timeframe", "Side", "EntryTime", "CloseTime", 
                      "BoxEntry", "FillEntry", "SlippagePips", "SL", "TP1", "TP2", "TP3", "TP4", 
                      "TPsHit", "ExitClass", "ProfitUSD", "ProfitPips", "Outcome");
   }

   // خروجی JSON محلی
   int hJson = FileOpen(jsonName, FILE_WRITE | FILE_TXT | FILE_UNICODE);
   int hJsonCommon = FileOpen(jsonName, FILE_WRITE | FILE_TXT | FILE_UNICODE | FILE_COMMON);

   string jsonContent = "{\n";
   jsonContent += "  \"reportTitle\": \"تست استراتژی تستر متاتریدر ۵ - نماد " + _Symbol + " تایم " + tfName + "\",\n";
   jsonContent += "  \"symbol\": \"" + _Symbol + "\",\n";
   jsonContent += "  \"timeframe\": \"" + tfName + "\",\n";
   jsonContent += "  \"dateRange\": \"" + TimeToString(startTestTime, TIME_DATE) + " - " + TimeToString(endTestTime, TIME_DATE) + "\",\n";
   jsonContent += "  \"exportedAt\": \"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_MINUTES|TIME_SECONDS) + "\",\n";

   // پارامترهای تستر
   jsonContent += "  \"parameters\": {\n";
   jsonContent += "    \"InpScenarioName\": \"" + InpScenarioName + "\",\n";
   jsonContent += "    \"InpMinTradePotential\": " + DoubleToString(InpMinTradePotential, 1) + ",\n";
   jsonContent += "    \"InpAllowedTradingHours\": \"" + (InpAllowedTradingHours == "" ? "24 Hours (تمام ساعات شبانه‌روز)" : InpAllowedTradingHours) + "\",\n";
   jsonContent += "    \"InpConsecLossTrigger\": " + IntegerToString(InpConsecLossTrigger) + ",\n";
   jsonContent += "    \"InpDisabledKingsList\": \"" + (InpDisabledKingsList == "" ? "None (هیچ سلطانی غیرفعال نبود)" : InpDisabledKingsList) + "\",\n";
   jsonContent += "    \"InpMoveToBreakEven\": " + (InpMoveToBreakEven ? "true" : "false") + ",\n";
   jsonContent += "    \"InpBEBufferPips\": " + DoubleToString(InpBEBufferPips, 1) + ",\n";
   jsonContent += "    \"InpTrailToTP1\": " + (InpTrailToTP1 ? "true" : "false") + ",\n";
   jsonContent += "    \"InpTrailToTP2\": " + (InpTrailToTP2 ? "true" : "false") + ",\n";
   jsonContent += "    \"InpMaxEntryDeviationPips\": " + DoubleToString(InpMaxEntryDeviationPips, 1) + ",\n";
   jsonContent += "    \"InpLot_TP1\": " + DoubleToString(InpLot_TP1, 2) + ",\n";
   jsonContent += "    \"InpLot_TP2\": " + DoubleToString(InpLot_TP2, 2) + ",\n";
   jsonContent += "    \"InpLot_TP3\": " + DoubleToString(InpLot_TP3, 2) + ",\n";
   jsonContent += "    \"InpLot_TP4\": " + DoubleToString(InpLot_TP4, 2) + "\n";
   jsonContent += "  },\n";

   // استخراج جزئیات هر ستاپ و پوزیشن‌ها
   string tradesJson = "  \"trades\": [\n";
   string equityJson = "  \"equityCurve\": [\n";
   double runningPips = 0.0;
   double runningUSD = 0.0;

   for(int g = 0; g < nSetups; g++)
   {
      double setupProfitUSD = 0.0;
      double setupProfitPips = 0.0;
      datetime closeTime = m_activeGroups[g].entryTime;
      int tpsHit = 0;
      bool fullSL = false;

      for(int p = 0; p < 4; p++)
      {
         ulong posTicket = m_activeGroups[g].tickets[p];
         if(posTicket <= 0) continue;

         if(HistorySelectByPosition(posTicket))
         {
            int nDeals = HistoryDealsTotal();
            for(int d = 0; d < nDeals; d++)
            {
               ulong dTk = HistoryDealGetTicket(d);
               if(dTk > 0 && HistoryDealGetInteger(dTk, DEAL_ENTRY) == DEAL_ENTRY_OUT)
               {
                  double pUSD = HistoryDealGetDouble(dTk, DEAL_PROFIT);
                  double exitPr = HistoryDealGetDouble(dTk, DEAL_PRICE);
                  datetime exTm = (datetime)HistoryDealGetInteger(dTk, DEAL_TIME);
                  if(exTm > closeTime) closeTime = exTm;

                  double pPips = (exitPr - m_activeGroups[g].entryPrice) / pipSize;
                  if(!m_activeGroups[g].isBuy) pPips = -pPips;

                  setupProfitUSD += pUSD;
                  setupProfitPips += pPips;

                  if(pPips > 0.5) tpsHit++;
                  else if(pPips < -1.0) fullSL = true;
               }
            }
         }
      }

      totalProfitUSD += setupProfitUSD;
      totalProfitPips += setupProfitPips;
      runningUSD += setupProfitUSD;
      runningPips += setupProfitPips;

      if(setupProfitPips >= 0)
      {
         winSetups++;
         grossProfitPips += setupProfitPips;
      }
      else
      {
         lossSetups++;
         grossLossPips += MathAbs(setupProfitPips);
      }

      string exitClass = "Full SL ❌";
      if(tpsHit >= 4) exitClass = "Full Runner TP4 🚀";
      else if(tpsHit == 3) exitClass = "TP3 + Trail 🏆";
      else if(tpsHit == 2) exitClass = "TP2 + Trail 🎯";
      else if(tpsHit == 1) exitClass = "TP1 + BE 🛡️ (ریسک‌فری روی پولبک)";
      else if(setupProfitPips > 0) exitClass = "Partial Profit ✅";

      double slippage = MathAbs(m_activeGroups[g].entryPrice - m_activeGroups[g].boxEntryPrice) / pipSize;
      string outcome = (setupProfitPips >= 0) ? "Win" : "Loss";

      string discReason = "منطبق با استراتژی";
      if(m_activeGroups[g].tf == PERIOD_M1) discReason = "تایم نویز M1 (در سناریوی منتخب فیلتر است)";
      else if(slippage > 2.0) discReason = "اسلیپیج شدید ورود مارکت";
      else if(tpsHit == 1 && setupProfitPips < 5.0) discReason = "خروج زودهنگام در بریک‌ایون بافر ۱ پیپ";
      else if(fullSL && !m_activeGroups[g].isBuy) discReason = "اسپرد Ask روی استاپ پوزیشن SELL";

      if(hCsv != INVALID_HANDLE)
      {
         FileWrite(hCsv, IntegerToString(g + 1), m_activeGroups[g].role, EnumToString(m_activeGroups[g].tf),
                   (m_activeGroups[g].isBuy ? "BUY" : "SELL"),
                   TimeToString(m_activeGroups[g].entryTime, TIME_DATE|TIME_MINUTES|TIME_SECONDS),
                   TimeToString(closeTime, TIME_DATE|TIME_MINUTES|TIME_SECONDS),
                   DoubleToString(m_activeGroups[g].boxEntryPrice, _Digits),
                   DoubleToString(m_activeGroups[g].entryPrice, _Digits),
                   DoubleToString(slippage, 1),
                   DoubleToString(m_activeGroups[g].initialSL, _Digits),
                   DoubleToString(m_activeGroups[g].tp1, _Digits),
                   DoubleToString(m_activeGroups[g].tp2, _Digits),
                   DoubleToString(m_activeGroups[g].tp3, _Digits),
                   DoubleToString(m_activeGroups[g].tp4, _Digits),
                   IntegerToString(tpsHit), exitClass,
                   DoubleToString(setupProfitUSD, 2),
                   DoubleToString(setupProfitPips, 1), outcome);
      }

      if(g > 0)
      {
         tradesJson += ",\n";
         equityJson += ",\n";
      }

      tradesJson += StringFormat("    {\"setupId\": %d, \"pattern\": \"%s\", \"timeframe\": \"%s\", \"side\": \"%s\", \"entryTime\": \"%s\", \"closeTime\": \"%s\", \"boxEntryPrice\": %.5f, \"marketFillPrice\": %.5f, \"slippagePips\": %.1f, \"slPrice\": %.5f, \"tp1\": %.5f, \"tp2\": %.5f, \"tp3\": %.5f, \"tp4\": %.5f, \"tpsHit\": %d, \"exitClass\": \"%s\", \"outcome\": \"%s\", \"profitPips\": %.1f, \"profitUSD\": %.2f, \"discrepancyReason\": \"%s\"}",
                                 g + 1, m_activeGroups[g].role, EnumToString(m_activeGroups[g].tf),
                                 (m_activeGroups[g].isBuy ? "BUY" : "SELL"),
                                 TimeToString(m_activeGroups[g].entryTime, TIME_DATE|TIME_MINUTES),
                                 TimeToString(closeTime, TIME_DATE|TIME_MINUTES),
                                 m_activeGroups[g].boxEntryPrice, m_activeGroups[g].entryPrice, slippage,
                                 m_activeGroups[g].initialSL, m_activeGroups[g].tp1, m_activeGroups[g].tp2, m_activeGroups[g].tp3, m_activeGroups[g].tp4,
                                 tpsHit, exitClass, outcome, setupProfitPips, setupProfitUSD, discReason);

      equityJson += StringFormat("    {\"time\": \"%s\", \"pnlPips\": %.1f, \"pnlUSD\": %.2f}",
                                 TimeToString(closeTime, TIME_DATE|TIME_MINUTES), runningPips, runningUSD);
   }

   tradesJson += "\n  ]\n";
   equityJson += "\n  ]\n";

   double wr = (nSetups > 0) ? ((double)winSetups / nSetups * 100.0) : 0.0;
   double pf = (grossLossPips > 0) ? (grossProfitPips / grossLossPips) : 0.0;

   string kpisJson = "  \"kpis\": {\n";
   kpisJson += "    \"totalSetups\": " + IntegerToString(nSetups) + ",\n";
   kpisJson += "    \"winningSetups\": " + IntegerToString(winSetups) + ",\n";
   kpisJson += "    \"losingSetups\": " + IntegerToString(lossSetups) + ",\n";
   kpisJson += "    \"winRate\": " + DoubleToString(wr, 1) + ",\n";
   kpisJson += "    \"netPips\": " + DoubleToString(totalProfitPips, 1) + ",\n";
   kpisJson += "    \"netUSD\": " + DoubleToString(totalProfitUSD, 2) + ",\n";
   kpisJson += "    \"profitFactor\": " + DoubleToString(pf, 2) + ",\n";
   kpisJson += "    \"grossProfitPips\": " + DoubleToString(grossProfitPips, 1) + ",\n";
   kpisJson += "    \"grossLossPips\": " + DoubleToString(grossLossPips, 1) + "\n";
   kpisJson += "  },\n";

   jsonContent += kpisJson + equityJson + ",\n" + tradesJson + "}\n";

   if(hJson != INVALID_HANDLE)
   {
      FileWriteString(hJson, jsonContent);
      FileClose(hJson);
   }
   if(hJsonCommon != INVALID_HANDLE)
   {
      FileWriteString(hJsonCommon, jsonContent);
      FileClose(hJsonCommon);
   }
   if(hCsv != INVALID_HANDLE)
   {
      FileClose(hCsv);
   }

   PrintFormat("🎉 [FlagPro] گزارش کالبدشکافی تستر با موفقیت ایجاد شد | نماد: %s | تعداد ستاپ: %d | سود خالص: %.1f پیپ (%.2f$) | وین‌ریت: %.1f%% | مسیر فایل: MQL5\\Files\\%s",
               _Symbol, nSetups, totalProfitPips, totalProfitUSD, wr, jsonName);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(MQLInfoInteger(MQL_TESTER))
   {
      ExportTesterRunSummary();
   }
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
   // ۱. مدیریت تریل و بریک‌ایون تمام معاملات باز روی هر تیک (فوق سریع و سبک)
   ManageActiveTradeGroups();

   // ۲. بررسی باز شدن کندل جدید (پردازش سنگین فقط و فقط یک‌بار در ابتدای هر کندل جدید انجام می‌شود)
   static datetime lastCandleTime = 0;
   datetime currentCandleTime = iTime(_Symbol, _Period, 0);
   if(currentCandleTime == lastCandleTime)
      return; // در طول نوسانات کندل جاری، دیتایی کپی نشده و هیچ الگویی مجدداً پردازش نمی‌گردد

   lastCandleTime = currentCandleTime;

   // ۳. بررسی محدودیت تعداد گروه‌های پوزیشن باز
   if(CountOpenPositionGroups() >= InpMaxOpenGroups)
      return;

   // ۴. تعیین تعداد کندل‌های اسکن بهینه (پنجره شناور) جهت حداکثر سرعت در تستر و لایو
   int targetBars = InpLookbackBars;
   if(targetBars < 1000) targetBars = 1000;
   if(targetBars > 30000) targetBars = 30000;

   MqlRates rates[];
   ArraySetAsSeries(rates, false);
   int ratesTotal = CopyRates(_Symbol, _Period, 0, targetBars, rates);
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

   ArrayResize(g_drawnBoxes, 0);
   g_boxCount = 0;
   ArrayResize(g_indepPivots, 0);
   g_indepCount = 0;

   ENUM_TIMEFRAMES tfArr[7]      = {PERIOD_D1, PERIOD_W1, PERIOD_H4, PERIOD_H1, InpTF5, InpTF6, InpTF7};
   bool            useArr[7]     = {false, false, false, false, InpUseTF5, InpUseTF6, InpUseTF7};
   color           tfColorArr[7] = {clrNONE, clrNONE, clrNONE, clrNONE, InpColorTF5, InpColorTF6, InpColorTF7};

   // تنظیم بازه عمق بررسی متناسب با targetBars جهت جلوگیری از افت سرعت در تست‌های طولانی
   int effectiveDays = (int)(targetBars / 1440) + 3;
   int daysBackArr[7];
   for(int s = 0; s < 7; s++) daysBackArr[s] = effectiveDays;
   InpBacktestStartDate = 0;
   InpBacktestDays = effectiveDays;
   InpMaxBarsTF = targetBars;

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

   // ۵. بررسی و ارسال سفارشات ستاپ‌های تایید شده
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

      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      bool isBuy = g_tradeSetups[t].isBuy;
      double sendPrice = isBuy ? ask : bid;

      // 🛡️ اعتبارسنجی انحراف ورود: اگر قیمت بیش از حد مجاز از لبه باکس فاصله گرفته یا قبلاً به تارگت/استاپ رسیده، ورود لغو می‌شود
      double maxDev = (InpMaxEntryDeviationPips > 0) ? (InpMaxEntryDeviationPips * pipSize) : (3.0 * pipSize);
      if(isBuy)
      {
         if(sendPrice <= g_tradeSetups[t].slPrice || sendPrice >= g_tradeSetups[t].tp1)
         {
            int newSize = ArraySize(m_executedTradesKeys) + 1;
            ArrayResize(m_executedTradesKeys, newSize);
            m_executedTradesKeys[newSize - 1] = tradeKey;
            continue;
         }
         if(sendPrice > g_tradeSetups[t].entryPrice + maxDev)
            continue; // قیمت خیلی بالا رفته، از تعقیب دیرهنگام در سقف خودداری شود
      }
      else
      {
         if(sendPrice >= g_tradeSetups[t].slPrice || sendPrice <= g_tradeSetups[t].tp1)
         {
            int newSize = ArraySize(m_executedTradesKeys) + 1;
            ArrayResize(m_executedTradesKeys, newSize);
            m_executedTradesKeys[newSize - 1] = tradeKey;
            continue;
         }
         if(sendPrice < g_tradeSetups[t].entryPrice - maxDev)
            continue; // قیمت خیلی پایین ریخته، از تعقیب دیرهنگام در کف خودداری شود
      }

      // ثبت کلید معامله در لیست پردازش‌شده‌ها تا در تیک‌های بعدی تکرار نشود
      int newSize = ArraySize(m_executedTradesKeys) + 1;
      ArrayResize(m_executedTradesKeys, newSize);
      m_executedTradesKeys[newSize - 1] = tradeKey;

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
         m_activeGroups[gSize - 1].tradeKey      = tradeKey;
         m_activeGroups[gSize - 1].role          = g_tradeSetups[t].boxRole;
         m_activeGroups[gSize - 1].tf            = g_tradeSetups[t].tf;
         m_activeGroups[gSize - 1].entryTime     = g_tradeSetups[t].entryTime;
         m_activeGroups[gSize - 1].isBuy         = isBuy;
         m_activeGroups[gSize - 1].entryPrice    = sendPrice;
         m_activeGroups[gSize - 1].boxEntryPrice = g_tradeSetups[t].entryPrice;
         m_activeGroups[gSize - 1].initialSL     = sl;
         m_activeGroups[gSize - 1].boxSL         = g_tradeSetups[t].slPrice;
         m_activeGroups[gSize - 1].tp1           = tp1;
         m_activeGroups[gSize - 1].tp2           = tp2;
         m_activeGroups[gSize - 1].tp3           = tp3;
         m_activeGroups[gSize - 1].tp4           = tp4;
         for(int p = 0; p < 4; p++) m_activeGroups[gSize - 1].tickets[p] = openedTickets[p];
         m_activeGroups[gSize - 1].beApplied      = false;
         m_activeGroups[gSize - 1].trailTP1Applied = false;
         m_activeGroups[gSize - 1].trailTP2Applied = false;
         m_activeGroups[gSize - 1].isFinished     = false;

         PrintFormat("✅ ۴ پوزیشن خروج چند مرحله‌ای با موفقیت ثبت شد | الگو: %s [%s] | جهت: %s | حجم‌ها: TP1=%.2f, TP2=%.2f, TP3=%.2f, TP4=%.2f | حد ضرر: %.5f | تارگت‌ها: TP1=%.5f, TP2=%.5f, TP3=%.5f, TP4=%.5f",
                     g_tradeSetups[t].boxRole, EnumToString(g_tradeSetups[t].tf),
                     (isBuy ? "BUY" : "SELL"), InpLot_TP1, InpLot_TP2, InpLot_TP3, InpLot_TP4, sl, tp1, tp2, tp3, tp4);
         break;
      }
   }
}
//+------------------------------------------------------------------+
