//+------------------------------------------------------------------+
//| Flag_Types.mqh                                                   |
//| FlagPro Data Structures and Global Types                         |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""

#include <MarketStructureEngine.mqh>

// پیشوند اختصاصی اشیاء گرافیکی FlagPro جهت جلوگیری از هرگونه تداخل با سایر اندیکاتورها
#define FP_PREFIX "FLAGPRO_"
#define FLAGPRO_VERSION "v2.14"

enum ENUM_LABEL_STYLE
{
   LABEL_COMPACT,   // کوتاه و تمیز (مانند M15➔H1)
   LABEL_FULL,      // متن کامل
   LABEL_TOOLTIP    // فقط هنگام بردن موس روی خط (چارت کاملاً خلوت و بدون متن)
};

enum ENUM_BOX_DISPLAY_FILTER
{
   FILTER_TOP_WINNERS_ONLY = 0,        // فقط برترین الگوهای طلایی برنده (Top Winners Only - پیش‌فرض)
   FILTER_SHOW_ALL = 1                 // نمایش همه باکس‌ها (بدون فیلتر)
};

enum ENUM_LABEL_FORMAT
{
   LABEL_CONCISE,   // نام کوتاه و تمیز (مثل چارت کلاسیک: OInner-BE, S-LS)
   LABEL_FULL_CHAIN // زنجیره کامل مسیر الگو (LS > OInner > RS > Swap)
};

enum ENUM_HISTORY_MODE
{
   HIST_START_DATE,    // 📅 از تاریخ شروع مشخص (Start Date)
   HIST_DAYS_BACK,     // ⏳ بر اساس تعداد روز گذشته (Days Back)
   HIST_ALL_AVAILABLE  // 🌐 تمام تاریخچه موجود در متاتریدر (All Available)
};

// متغیرهای سراسری و یکپارچه بازه زمانی تحلیل
datetime g_effectiveStartDate  = 0;
int      g_effectiveDaysBack   = 1000;
int      g_effectiveTargetBars = 2000000;

// متغیرهای مشترک موتور شبیه‌ساز و رسم
datetime InpBacktestStartDate = 0;
int      InpBacktestDays      = 1000;
int      InpMaxBarsTF         = 2000000;

void InitMasterHistory(ENUM_HISTORY_MODE mode, datetime startDate, int daysBack)
{
   datetime now = TimeCurrent();
   if(now <= 0) now = TimeTradeServer();
   if(now <= 0) now = TimeLocal();
   datetime lastBar[1];
   if(CopyTime(_Symbol, _Period, 0, 1, lastBar) > 0 && lastBar[0] > 0)
   {
      if(lastBar[0] > now || now <= 0) now = lastBar[0];
   }

   // در محیط متاتستر متاتریدر ۵، دیتای تست از ابتدای دوره آزمون باید حفظ شود
   if((bool)MQLInfoInteger(MQL_TESTER) || mode == HIST_ALL_AVAILABLE)
   {
      g_effectiveStartDate = 0;
      g_effectiveDaysBack  = 5000;
   }
   else if(mode == HIST_DAYS_BACK)
   {
      g_effectiveDaysBack  = (daysBack > 0) ? daysBack : 10;
      g_effectiveStartDate = (now > g_effectiveDaysBack * 86400) ? (now - g_effectiveDaysBack * 86400) : 0;
   }
   else // HIST_START_DATE
   {
      g_effectiveStartDate = (startDate > 0) ? startDate : D'2025.01.01 00:00';
      if(now > g_effectiveStartDate)
         g_effectiveDaysBack = (int)((now - g_effectiveStartDate) / 86400) + 1;
      else
         g_effectiveDaysBack = 10;
   }

   InpBacktestStartDate = g_effectiveStartDate;
   InpBacktestDays      = g_effectiveDaysBack;

   int secPerBar = PeriodSeconds(_Period);
   if(secPerBar <= 0) secPerBar = 60;

   long neededBars = 0;
   if(mode == HIST_ALL_AVAILABLE)
   {
      neededBars = 5000000;
   }
   else
   {
      neededBars = (long)((g_effectiveDaysBack * 86400) / secPerBar) + 3000;
   }

   if(neededBars < 3000) neededBars = 3000;
   g_effectiveTargetBars = (int)MathMin(neededBars, 5000000);
   InpMaxBarsTF = g_effectiveTargetBars;
}

// ساختار نگهداری مشخصات باکس‌ها
struct SBoxInfo
{
   string          boxName;
   string          boxKey;
   ENUM_TIMEFRAMES tf;
   string          tfTag;
   int             swingIdx;
   datetime        t1;
   datetime        t2;
   datetime        formationTime; // زمان تشکیل اولیه گره (بدون امتداد)
   datetime        confirmationTime; // زمان تایید قطعی هویت گره در لایو بازار
   double          top;
   double          bottom;
   color           baseColor;
   int             baseWidth;
   ENUM_LINE_STYLE baseStyle;
   bool            isBullish;
   bool            isPreIP;
   bool            isLSBull;
   bool            isBOFlag;
   bool            isRSBull;
   bool            isOInner;
   bool            isOInnerBull;
   bool            isSwap;
   bool            isSwapBull;
   string          swapSourceRole;
   string          rsTags[];
   bool            isMacro;
   datetime        targetIPTime;
   bool            targetIPIsHigh;
   bool            hasTradeEntered; // آیا روی این باکس معامله واقعی فعال شده است؟
};

// ساختار نگهداری معاملات بک‌تست
struct STradeSetup
{
   string   boxName;
   string   boxRole;
   ENUM_TIMEFRAMES tf;
   string   tfTag;
   bool     isBuy;
   datetime entryTime;
   double   entryPrice;
   double   slPrice;
   double   risk;
   double   tp1;
   double   tp2;
   double   tp3;
   double   tp4;
   datetime exitTime;
   int      hitTP; // 0=SL hit, 1=TP1, 2=TP2, 3=TP3, 4=TP4, -1=Open
   bool     isClosed;
   datetime tp1Time; // زمان دقیق لمس TP1 جهت خاتمه خط
   datetime tp2Time; // زمان دقیق لمس TP2 جهت خاتمه خط
   datetime tp3Time; // زمان دقیق لمس TP3 جهت خاتمه خط
   datetime tp4Time; // زمان دقیق لمس TP4 جهت خاتمه خط
};

// ساختار نگهداری پیووت‌های مستقل
struct SIndepPivot
{
   datetime time;
   double   price;
   bool     isHigh;
   bool     hasIP;
   string   tfTags[];
   color    clr;
};

// متغیرها و آرایه‌های سراسری FlagPro
SPivot          g_pivotsH1[];
int             g_pivotCountH1 = 0;
SBoxInfo        g_drawnBoxes[];
int             g_boxCount = 0;
int             g_clickCounter = 0;
STradeSetup     g_tradeSetups[];
int             g_tradeCount = 0;
SIndepPivot     g_indepPivots[];
int             g_indepCount = 0;

string          g_selectedBoxName = "";
string          g_selectedExtBoxName = "";
color           g_origBoxColor = clrNONE;
int             g_origBoxWidth = 1;
ENUM_LINE_STYLE g_origBoxStyle = STYLE_SOLID;
bool            g_forceRecalc = true;
datetime        g_sessionStartTime = 0;
datetime        g_testerStartBase = 0;
bool            g_boxesVisible = true; // وضعیت فعال/مخفی بودن باکس‌های چارت
