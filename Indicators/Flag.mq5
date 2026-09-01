//+------------------------------------------------------------------+
//| Flag.mq5                                                         |
//| Multi-Timeframe Flag Indicator with 3-Pivot Context Inspector    |
//+------------------------------------------------------------------+
#property copyright "Flag Indicator"
#property link      ""
#property version   "39.00"
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

#include <MarketStructureEngine.mqh>

//--- Inputs : source structure timeframes
//--- Inputs : source structure timeframes
input group "=== Background Timeframes Calculation ==="
input ENUM_TIMEFRAMES InpTF1      = PERIOD_D1;
input bool             InpUseTF1  = true;           // محاسبه روزانه (D1)
input color            InpColorTF1 = clrMagenta;

input ENUM_TIMEFRAMES InpTF2      = PERIOD_W1;
input bool             InpUseTF2  = true;           // محاسبه هفتگی (W1)
input color            InpColorTF2 = clrDodgerBlue;

input ENUM_TIMEFRAMES InpTF3      = PERIOD_H4;
input bool             InpUseTF3  = true;           // محاسبه چهارساعته (H4)
input color            InpColorTF3 = clrWhite;

input ENUM_TIMEFRAMES InpTF4      = PERIOD_H1;
input bool             InpUseTF4  = true;           // محاسبه یک‌ساعته (H1)
input color            InpColorTF4 = clrYellow;

input ENUM_TIMEFRAMES InpTF5      = PERIOD_M15;
input bool             InpUseTF5  = true;           // محاسبه ۱۵ دقیقه (M15)
input color            InpColorTF5 = clrLime;
input int              InpM15DaysBack = 10;          // تاریخچه ۱۵ دقیقه (۱۰ روز)

input ENUM_TIMEFRAMES InpTF6      = PERIOD_M5;
input bool             InpUseTF6  = true;           // محاسبه ۵ دقیقه (M5)
input color            InpColorTF6 = clrAqua;
input int              InpM5DaysBack = 10;          // تاریخچه ۵ دقیقه (۱۰ روز)

input ENUM_TIMEFRAMES InpTF7      = PERIOD_M1;
input bool             InpUseTF7  = true;           // محاسبه ۱ دقیقه (M1)
input color            InpColorTF7 = clrYellow;
input int              InpM1DaysBack = 10;          // تاریخچه ۱ دقیقه (۱۰ روز)

enum ENUM_DISPLAY_FILTER
{
   FILTER_ALL,               // نمایش کامل تمام باکس‌ها (همه الگوها)
   FILTER_ONLY_SRS,          // فقط باکس‌های S-RS (وین‌ریت بالای ۸۳٪)
   FILTER_HIGH_WINRATE,      // باکس‌های طلایی با وین‌ریت بالا (S-RS + OInner + RS)
   FILTER_ALL_SWAPS          // فقط باکس‌های سواپ (S-RS, S-OInner, S-LS)
};

input group "=== Smart Visibility & Box Filter (فیلتر نمایش هوشمند) ==="
input ENUM_DISPLAY_FILTER InpDisplayFilter          = FILTER_ALL;      // فیلتر نمایش باکس‌ها روی چارت (پیش‌فرض: همه باکس‌ها)
input bool             InpShowMacroAlways       = true;  // نمایش همیشگی باکس‌های ماکرو (در حالت All)
input bool             InpShowOnlyRSMicroBoxes  = false; // در تایم‌های ریز فقط باکس‌های دارای شرط RS نمایش داده شوند
input bool             InpShowNormalMicroBoxes  = true;  // رسم کامل همه باکس‌های ۱۰ روز گذشته
input string           InpRSTagPrefix           = "RS";  // پیشوند تگ‌های هوشمند (RS)

input group "=== Structure Calculation (matches MarketStructure_v2) ==="
input int              InpSwingBars   = 6;           // عمق امواج ماژور (Swing Bars)
input int              InpMaxBarsTF   = 20000;       // حداکثر کندل‌های محاسبه (Max Bars)

input group "=== Visuals ==="
input int              InpLineWidth   = 1;           // ضخامت خط باکس‌ها (1 = نازک و ظریف)
input bool             InpShowLabel   = true;        // نمایش برچسب تایم‌فریم

input group "=== Independent Pivots (پیووت‌های مستقل) ==="
input bool             InpShowIndependentPivots = true;        // نمایش پیووت‌های مستقل روی چارت
input bool             InpLabelAllPivots        = false;       // نمایش تمام سوینگ‌ها (false = فقط پیووت‌های مستقل هدفمند)
input color            InpIndepColorHigh        = clrMagenta;  // رنگ سقف مستقل
input color            InpIndepColorLow         = clrAqua;     // رنگ کف مستقل
input int              InpIndepMarkCode         = 159;         // کد علامت (159 = دایره، 168 = دایره باز)
input int              InpIndepMarkWidth        = 3;           // اندازه علامت پیووت مستقل
input bool             InpIndepShowLabel        = true;        // نمایش برچسب IP روی چارت

input group "=== Pre-IP / LS Box (باکس ماقبل پیووت مستقل) ==="
input bool             InpHighlightPreIP        = true;         // مشخص کردن باکس قبل از پیووت مستقل
input color            InpLSColorBull           = clrLimeGreen; // رنگ LS صعودی (منتهی به سقف)
input color            InpLSColorBear           = clrDeepPink;  // رنگ LS نزولی (منتهی به کف)
input int              InpPreIPWidth            = 2;            // ضخامت باکس ماقبل پیووت مستقل
input bool             InpPreIPShowLabel        = true;         // نمایش برچسب Pre-IP روی باکس

enum ENUM_LABEL_STYLE
{
   LABEL_COMPACT,   // کوتاه و تمیز (مانند M15➔H1)
   LABEL_FULL,      // متن کامل
   LABEL_TOOLTIP    // فقط هنگام بردن موس روی خط (چارت کاملاً خلوت و بدون متن)
};

input group "=== Multi-Timeframe Origin Lines (خطوط پیووت منشأ چندگانه) ==="
input bool              InpEnableOriginLines     = false;        // فعال‌سازی رسم خطوط افقی منشأ پیووت‌ها (پیش‌فرض: غیرفعال)
input bool              InpOriginRequireIndep    = false;        // فقط پیووت‌های مستقل منشأ باشند (false = هر کف/سقف ماقبل)
input int               InpOriginDaysBack        = 0;            // روزهای محاسبه خطوط منشأ (0 = همه تاریخچه)

// تایم‌فریم‌های هدف (Target HTF)
input bool              InpTargetD1              = true;         // بررسی پیووت‌های مستقل روزانه (D1)
input bool              InpTargetH4              = true;         // بررسی پیووت‌های مستقل چهارساعته (H4)
input bool              InpTargetH1              = true;         // بررسی پیووت‌های مستقل یک‌ساعته (H1)

// تایم‌فریم‌های منشأ (Source LTF)
input bool              InpSourceH1              = true;         // رسم منشأ یک‌ساعته (H1) برای D1 و H4
input bool              InpSourceM15             = true;         // رسم منشأ ۱۵ دقیقه (M15) برای D1, H4, H1
input bool              InpSourceM5              = true;         // رسم منشأ ۵ دقیقه (M5) برای D1, H4, H1
input bool              InpSourceM1              = true;         // رسم منشأ ۱ دقیقه (M1) برای D1, H4, H1

// استایل و برچسب
input color             InpOriginColorLow        = clrAqua;      // رنگ خط کف منشأ (صعودی)
input color             InpOriginColorHigh       = clrMagenta;   // رنگ خط سقف منشأ (نزولی)
input int               InpOriginLineWidth       = 1;            // ضخامت خط افقی
input ENUM_LABEL_STYLE  InpOriginLabelStyle      = LABEL_COMPACT;// نحوه نمایش برچسب روی خطوط منشأ

input group "=== Breakout Flags / RS Boxes (فلگ‌های واکنش و شکست) ==="
input bool              InpHighlightBreakoutFlags = true;        // هایلایت فلگ‌های نقطه شکست
input color             InpRSColorBull           = clrDodgerBlue;// رنگ RS صعودی (شکست و واکنش رو به بالا)
input color             InpRSColorBear           = clrOrangeRed; // رنگ RS نزولی (شکست و واکنش رو به پایین)
input color             InpComboColorBull        = clrYellow;    // رنگ اشتراک LS+RS صعودی
input color             InpComboColorBear        = clrMagenta;   // رنگ اشتراک LS+RS نزولی
input int               InpBreakoutFlagWidth     = 3;           // ضخامت خط فلگ‌های نقطه شکست
input bool              InpBreakoutFlagShowLabel = true;        // نمایش برچسب BO-Flag روی باکس

input group "=== OInner Box (اولین گره مابعد پیووت مستقل) ==="
input bool             InpHighlightOInner       = true;         // هایلایت اولین گره بعد از پیووت مستقل (OInner)
input color            InpOInnerColorBull       = clrDeepSkyBlue;// رنگ OInner صعودی (حرکت رو به بالا از کف)
input color            InpOInnerColorBear       = clrGold;      // رنگ OInner نزولی (حرکت رو به پایین از سقف)
input int              InpOInnerWidth           = 2;            // ضخامت باکس OInner

input group "=== Universal Box Swap System (سیستم جامع سواپ باکس‌ها) ==="
input bool             InpEnableSwapLines       = true;         // فعال‌سازی رسم امتداد باکس‌های سواپ (پیش‌فرض: فعال)
input bool             InpSwapOnlyKeyBoxes      = true;         // فقط امتداد باکس‌های کلیدی (OInner, RS, LS) جهت خلوت بودن چارت
input color            InpSwapColorBull         = clrDodgerBlue;// رنگ سواپ صعودی (شکست به بالا)
input color            InpSwapColorBear         = clrOrangeRed; // رنگ سواپ نزولی (شکست به پایین)
input int              InpSwapLineWidth         = 1;            // ضخامت خطوط سواپ
input ENUM_LINE_STYLE  InpSwapLineStyle         = STYLE_DOT;    // استایل پیش‌فرض سواپ
input int              InpSwapBoxWidth          = 2;            // ضخامت خط باکس‌های سواپ

input group "=== Visual Trade Simulation (نمایش بصری معاملات و تارگت‌ها) ==="
input bool             InpShowVisualTrades      = true;         // نمایش بصری ستاپ‌های معاملاتی روی چارت
input int              InpMaxVisualTrades       = 10;           // حداکثر معاملات اخیر جهت رسم (خلوت بودن چارت)
input double           InpRSPipBuffer           = 10.0;         // فاصله استاپ RS بر حسب پیپ
input color            InpTradeEntryColor       = clrWhite;     // رنگ خط نقطه ورود
input color            InpTradeSLColor          = clrRed;       // رنگ خط استاپ لاس (SL)
input color            InpTradeTPColor          = clrLimeGreen; // رنگ خطوط تارگت (TP)

input group "=== Chart Theme & Display (تم فوق‌حرفه‌ای چارت) ==="
input bool             InpApplyProTheme = true;        // اعمال تم حرفه‌ای خنثی (کندل‌های نقره‌ای/دودی با کنتراست حداکثری باکس‌ها)
input bool             InpHideGrid      = true;        // حذف گرید از چارت
input bool             InpHideVolumes   = true;        // حذف نمودار حجم

// Storage for drawn boxes and pivots
struct SBoxInfo
{
   string          boxName;
   string          boxKey;
   ENUM_TIMEFRAMES tf;
   string          tfTag;
   int             swingIdx;
   datetime        t1;
   datetime        t2;
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
};

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
};

SPivot      g_pivotsH1[];
int         g_pivotCountH1 = 0;
SBoxInfo    g_drawnBoxes[];
int         g_boxCount = 0;
int         g_clickCounter = 0;
STradeSetup g_tradeSetups[];
int         g_tradeCount = 0;

struct SIndepPivot
{
   datetime time;
   double   price;
   bool     isHigh;
   bool     hasIP;
   string   tfTags[];
   color    clr;
};

SIndepPivot g_indepPivots[];
int         g_indepCount = 0;

//+------------------------------------------------------------------+
//| Find Exact Candle Time on Chart matching Peak/Valley             |
//+------------------------------------------------------------------+
datetime GetExactPivotChartTime(datetime srcBarTime, ENUM_TIMEFRAMES srcTF, double price, bool isHigh,
                                const datetime &chartTime[], const double &chartHigh[], const double &chartLow[], int ratesTotal)
{
   int sec = PeriodSeconds(srcTF);
   datetime srcEndTime = srcBarTime + sec;

   int startIdx = FindBarIndex(chartTime, ratesTotal, srcBarTime);
   int endIdx   = FindBarIndex(chartTime, ratesTotal, srcEndTime);
   if(startIdx < 0) return srcBarTime;
   if(endIdx < 0) endIdx = ratesTotal - 1;

   datetime bestTime = srcBarTime;
   double bestDiff = 1e10;

   for(int k = startIdx; k <= endIdx && k < ratesTotal; k++)
   {
      double candlePrice = isHigh ? chartHigh[k] : chartLow[k];
      double diff = MathAbs(candlePrice - price);
      if(diff < bestDiff)
      {
         bestDiff = diff;
         bestTime = chartTime[k];
         if(diff < _Point * 0.5) break;
      }
   }
   return bestTime;
}

//+------------------------------------------------------------------+
//| Get distinct Line Style per Timeframe                            |
//+------------------------------------------------------------------+
ENUM_LINE_STYLE GetTFLineStyle(ENUM_TIMEFRAMES tf)
{
   switch(tf)
   {
      case PERIOD_D1:  return STYLE_DASH;       // روزانه: خط‌چین
      case PERIOD_W1:  return STYLE_DASH;       // هفتگی: خط‌چین
      case PERIOD_H4:  return STYLE_DOT;        // چهارساعته: نقطه‌چین
      case PERIOD_H1:  return STYLE_DASH;       // یک‌ساعته: خط‌چین
      case PERIOD_M15: return STYLE_DASH;       // ۱۵ دقیقه: خط‌چین
      case PERIOD_M5:  return STYLE_DOT;        // ۵ دقیقه: نقطه‌چین
      case PERIOD_M1:  return STYLE_DOT;        // ۱ دقیقه: نقطه‌چین
      default:         return STYLE_DASH;
   }
}

//+------------------------------------------------------------------+
//| Find Bar Index in non-series chartTime array                     |
//+------------------------------------------------------------------+
int FindBarIndex(const datetime &chartTime[], int ratesTotal, datetime t)
{
   if(ratesTotal <= 0) return -1;
   if(t <= chartTime[0]) return 0;
   if(t >= chartTime[ratesTotal - 1]) return ratesTotal - 1;

   int lo = 0, hi = ratesTotal - 1;
   while(lo < hi)
   {
      int mid = (lo + hi + 1) / 2;
      if(chartTime[mid] <= t) lo = mid;
      else hi = mid - 1;
   }
   return lo;
}

//+------------------------------------------------------------------+
//| Helper: Draw Hollow Box on Chart with Custom Style               |
//+------------------------------------------------------------------+
void DrawHollowBox(string name, datetime t1, double top, datetime t2, double bottom,
                   color clr, int width, ENUM_LINE_STYLE style = STYLE_SOLID)
{
   if(ObjectFind(0, name) >= 0) ObjectDelete(0, name);
   ObjectCreate(0, name, OBJ_RECTANGLE, 0, t1, top, t2, bottom);
   ObjectSetInteger(0, name, OBJPROP_COLOR,      clr);
   ObjectSetInteger(0, name, OBJPROP_WIDTH,      width);
   ObjectSetInteger(0, name, OBJPROP_STYLE,      style);
   ObjectSetInteger(0, name, OBJPROP_FILL,       false);
   ObjectSetInteger(0, name, OBJPROP_BACK,       false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
}

//+------------------------------------------------------------------+
//| Helper: Friendly Timeframe Name                                  |
//+------------------------------------------------------------------+
string TFName(ENUM_TIMEFRAMES tf)
{
   string s = EnumToString(tf);
   StringReplace(s, "PERIOD_", "");
   return s;
}

//+------------------------------------------------------------------+
//| Evaluate Corrective Pullback Flag Swings                         |
//+------------------------------------------------------------------+
bool IsValidFlagLeg(int idx, const SPivot &pivots[], int totalCount)
{
   if(idx < 0 || idx >= totalCount - 1) return false;

   SPivot p1 = pivots[idx];     // شروع یال جاری
   SPivot p2 = pivots[idx + 1]; // پایان یال جاری

   // Extract previous High and previous Low before idx
   double prevH = -1, prevL = -1;
   for(int j = idx - 1; j >= 0; j--)
   {
      if(pivots[j].isHigh && prevH < 0) prevH = pivots[j].price;
      if(!pivots[j].isHigh && prevL < 0) prevL = pivots[j].price;
      if(prevH > 0 && prevL > 0) break;
   }

   // Extract next High and next Low after idx+1
   double nextH = -1, nextL = -1;
   for(int j = idx + 2; j < totalCount; j++)
   {
      if(pivots[j].isHigh && nextH < 0) nextH = pivots[j].price;
      if(!pivots[j].isHigh && nextL < 0) nextL = pivots[j].price;
      if(nextH > 0 && nextL > 0) break;
   }

   // 1. اصلاح نزولی در روند صعودی: Drop (High -> Low)
   if(p1.isHigh && !p2.isHigh)
   {
      if(prevL > 0 && p2.price > prevL)
      {
         // شرط ۱: اگر سقف بعد و کف بعد هر دو پایین‌تر بیایند -> چرخش روند
         if(nextH > 0 && nextH < p1.price && nextL > 0 && nextL < p2.price)
            return false;

         // شرط ۲: تأیید ادامه روند صعودی (شکست سقف P1 در سوینگ‌های بعد)
         bool brokeAboveP1 = false;
         bool hasFutureHighs = false;
         for(int j = idx + 2; j < totalCount && j <= idx + 8; j++)
         {
            if(pivots[j].isHigh)
            {
               hasFutureHighs = true;
               if(pivots[j].price > p1.price)
               {
                  brokeAboveP1 = true;
                  break;
               }
            }
         }
         // اگر سوینگ‌های بعدی شکل گرفته‌اند ولی هیچ‌کدام نتوانسته‌اند بالای P1 بروند -> سقف مستقل
         if(hasFutureHighs && !brokeAboveP1)
            return false;

         return true;
      }
   }
   // 2. اصلاح صعودی در روند نزولی: Rally (Low -> High)
   else if(!p1.isHigh && p2.isHigh)
   {
      if(prevH > 0 && p2.price < prevH)
      {
         // شرط ۱: اگر کف بعد و سقف بعد هر دو بالاتر بیایند -> چرخش روند
         if(nextL > 0 && nextL > p1.price && nextH > 0 && nextH > p2.price)
            return false;

         // شرط ۲: تأیید ادامه روند نزولی (شکست کف P1 در سوینگ‌های بعد)
         bool brokeBelowP1 = false;
         bool hasFutureLows = false;
         for(int j = idx + 2; j < totalCount && j <= idx + 8; j++)
         {
            if(!pivots[j].isHigh)
            {
               hasFutureLows = true;
               if(pivots[j].price < p1.price)
               {
                  brokeBelowP1 = true;
                  break;
               }
            }
         }
         // اگر سوینگ‌های بعدی شکل گرفته‌اند ولی هیچ‌کدام نتوانسته‌اند زیر P1 بروند -> کف مستقل
         if(hasFutureLows && !brokeBelowP1)
            return false;

         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Helper: Draw Independent Pivot Marker                            |
//+------------------------------------------------------------------+
void DrawIndependentPivot(string name, datetime t, double price, bool isHigh, color clr, string tfTag)
{
   if(ObjectFind(0, name) >= 0) ObjectDelete(0, name);
   ObjectCreate(0, name, OBJ_ARROW, 0, t, price);
   ObjectSetInteger(0, name, OBJPROP_ARROWCODE, InpIndepMarkCode);
   ObjectSetInteger(0, name, OBJPROP_COLOR,      clr);
   ObjectSetInteger(0, name, OBJPROP_WIDTH,      InpIndepMarkWidth);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_ANCHOR, (isHigh ? ANCHOR_BOTTOM : ANCHOR_TOP));

   if(InpIndepShowLabel)
   {
      string lblName = name + "_LBL";
      if(ObjectFind(0, lblName) >= 0) ObjectDelete(0, lblName);
      ObjectCreate(0, lblName, OBJ_TEXT, 0, t, price);
      ObjectSetString(0, lblName, OBJPROP_TEXT, "IP " + tfTag);
      ObjectSetInteger(0, lblName, OBJPROP_COLOR, clr);
      ObjectSetInteger(0, lblName, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, lblName, OBJPROP_ANCHOR, (isHigh ? ANCHOR_LOWER : ANCHOR_UPPER));
   }
}

//+------------------------------------------------------------------+
//| Process Timeframe Swings & Draw Flag Boxes                       |
//+------------------------------------------------------------------+
void ProcessTF(ENUM_TIMEFRAMES tf, int sBars, color clr,
               const datetime &chartTime[], const double &chartHigh[], const double &chartLow[],
               int ratesTotal, int daysBack)
{
   SPivot pivots[];
   if(!BuildAlternatingPivots(tf, sBars, InpMaxBarsTF, pivots))
   {
      return;
   }

   int count = ArraySize(pivots);
   if(count < 2) return;

   if(tf == PERIOD_H1)
   {
      ArrayResize(g_pivotsH1, count);
      for(int i = 0; i < count; i++) g_pivotsH1[i] = pivots[i];
      g_pivotCountH1 = count;
   }

   string tfTag = TFName(tf);
   string tfSymbol = (tf == PERIOD_H1) ? "H1" : tfTag;

   datetime limitTime = 0;
   if(daysBack > 0)
      limitTime = TimeCurrent() - daysBack * 24 * 60 * 60;

   //--- مرحله ۱: مشخص کردن اینکه کدام یال‌ها و پیووت‌ها متعلق به باکس‌های پرچم هستند
   bool isLegBox[];
   ArrayResize(isLegBox, count);
   ArrayInitialize(isLegBox, false);

   bool pivotInBox[];
   ArrayResize(pivotInBox, count);
   ArrayInitialize(pivotInBox, false);

   for(int i = 0; i < count - 1; i++)
   {
      if(IsValidFlagLeg(i, pivots, count))
      {
         isLegBox[i] = true;
         pivotInBox[i] = true;
         pivotInBox[i + 1] = true;
      }
   }

   //--- مرحله ۲: مشخص کردن باکس‌های ماقبل پیووت مستقل (Pre-IP Boxes)
   bool isPreIPBox[];
   datetime targetIPTimeArr[];
   bool targetIPIsHighArr[];
   ArrayResize(isPreIPBox, count);
   ArrayInitialize(isPreIPBox, false);
   ArrayResize(targetIPTimeArr, count);
   ArrayInitialize(targetIPTimeArr, 0);
   ArrayResize(targetIPIsHighArr, count);
   ArrayInitialize(targetIPIsHighArr, false);

   if(InpHighlightPreIP)
   {
      for(int p = 0; p < count; p++)
      {
         if(!pivotInBox[p]) // این یک پیووت مستقل است
         {
            // جستجوی نزدیک‌ترین باکس قبل از این پیووت
            for(int j = p - 1; j >= MathMax(0, p - 8); j--)
            {
               if(isLegBox[j])
               {
                  if(!isPreIPBox[j])
                  {
                     isPreIPBox[j] = true;
                     targetIPTimeArr[j]   = pivots[p].time;
                     targetIPIsHighArr[j] = pivots[p].isHigh;
                  }
                  break; // فقط نزدیک‌ترین باکس قبل از این پیووت مستقل
               }
            }
         }
      }
   }

   //--- مرحله ۳: ثبت و ادغام پیووت‌ها
   if(InpShowIndependentPivots)
   {
      for(int p = 0; p < count; p++)
      {
         if(daysBack > 0 && pivots[p].time < limitTime)
            continue;

         bool isIndependent = !pivotInBox[p];
         if(!isIndependent && !InpLabelAllPivots)
            continue;

         // پیدا کردن زمان دقیق کندل در تایم‌فریم جاری چارت
         datetime exactTime = GetExactPivotChartTime(pivots[p].time, tf, pivots[p].price, pivots[p].isHigh,
                                                    chartTime, chartHigh, chartLow, ratesTotal);

         // جستجو در لیست پیووت‌های ثبت‌شده برای ادغام پیووت‌های واقعاً یکسان
         int foundIdx = -1;
         for(int k = 0; k < g_indepCount; k++)
         {
            if(g_indepPivots[k].isHigh == pivots[p].isHigh)
            {
               if(MathAbs(g_indepPivots[k].time - exactTime) <= 7200 &&
                  MathAbs(g_indepPivots[k].price - pivots[p].price) <= 10 * _Point)
               {
                  foundIdx = k;
                  break;
               }
            }
         }

         if(foundIdx >= 0)
         {
            if(isIndependent) g_indepPivots[foundIdx].hasIP = true;
            bool exists = false;
            for(int t = 0; t < ArraySize(g_indepPivots[foundIdx].tfTags); t++)
            {
               if(g_indepPivots[foundIdx].tfTags[t] == tfSymbol) { exists = true; break; }
            }
            if(!exists)
            {
               int len = ArraySize(g_indepPivots[foundIdx].tfTags);
               ArrayResize(g_indepPivots[foundIdx].tfTags, len + 1);
               g_indepPivots[foundIdx].tfTags[len] = tfSymbol;
            }
         }
         else
         {
            ArrayResize(g_indepPivots, g_indepCount + 1);
            g_indepPivots[g_indepCount].time   = exactTime;
            g_indepPivots[g_indepCount].price  = pivots[p].price;
            g_indepPivots[g_indepCount].isHigh = pivots[p].isHigh;
            g_indepPivots[g_indepCount].hasIP  = isIndependent;
            g_indepPivots[g_indepCount].clr    = pivots[p].isHigh ? InpIndepColorHigh : InpIndepColorLow;
            ArrayResize(g_indepPivots[g_indepCount].tfTags, 1);
            g_indepPivots[g_indepCount].tfTags[0] = tfSymbol;
            g_indepCount++;
         }
      }
   }

   //--- مرحله ۴: رسم باکس‌های پرچم
   for(int i = 0; i < count - 1; i++)
   {
      if(!isLegBox[i])
         continue;

      SPivot p1 = pivots[i];
      SPivot p2 = pivots[i + 1];

      if(daysBack > 0 && p1.time < limitTime)
         continue;

      double boxTop    = MathMax(p1.price, p2.price);
      double boxBottom = MathMin(p1.price, p2.price);

      int idx1 = FindBarIndex(chartTime, ratesTotal, p1.time);
      int idx2 = FindBarIndex(chartTime, ratesTotal, p2.time);
      if(idx1 < 0 || idx2 < 0) continue;

      int idxStart = MathMin(idx1, idx2);
      int idxEnd   = MathMax(idx1, idx2);

      // ===== امتداد به عقب (Backward Extension) =====
      int leftIdx = idxStart;
      for(int k = idxStart - 1; k >= 0; k--)
      {
         bool candleInsideBox = (chartLow[k] >= boxBottom && chartHigh[k] <= boxTop);
         if(!candleInsideBox)
         {
            leftIdx = k + 1;
            break;
         }
         leftIdx = k;
      }
      if(leftIdx > 0) leftIdx--;

      // ===== امتداد به جلو (Forward Extension) =====
      int rightIdx = idxEnd;
      for(int k = idxEnd + 1; k < ratesTotal; k++)
      {
         if(chartHigh[k] > boxTop || chartLow[k] < boxBottom)
         {
            rightIdx = k;
            break;
         }
         rightIdx = k;
      }
      if(rightIdx <= leftIdx && leftIdx < ratesTotal - 1) rightIdx = leftIdx + 1;
      if(rightIdx < ratesTotal - 1) rightIdx++;

      datetime t1 = chartTime[leftIdx];
      datetime t2 = chartTime[rightIdx];

      string boxKey = IntegerToString((int)p1.time) + "_" + IntegerToString((int)p2.time);
      string boxType = (p1.isHigh ? "B" : "R");
      string preTag = (isPreIPBox[i] && InpHighlightPreIP) ? "_PREIP_" : "_";
      string boxName = "FLAG_BOX_" + tfTag + preTag + boxType + "_" + boxKey;
      
      // Register box for multi-tagging, filtering, and final rendering
      ArrayResize(g_drawnBoxes, g_boxCount + 1);
      g_drawnBoxes[g_boxCount].boxName   = boxName;
      g_drawnBoxes[g_boxCount].boxKey    = boxKey;
      g_drawnBoxes[g_boxCount].tf        = tf;
      g_drawnBoxes[g_boxCount].tfTag     = tfSymbol;
      g_drawnBoxes[g_boxCount].swingIdx  = i;
      g_drawnBoxes[g_boxCount].t1        = t1;
      g_drawnBoxes[g_boxCount].t2        = t2;
      g_drawnBoxes[g_boxCount].top       = boxTop;
      g_drawnBoxes[g_boxCount].bottom    = boxBottom;
      g_drawnBoxes[g_boxCount].baseColor      = clr;
      g_drawnBoxes[g_boxCount].baseWidth      = InpLineWidth;
      g_drawnBoxes[g_boxCount].baseStyle      = GetTFLineStyle(tf);
      bool isBullish = (!p1.isHigh && p2.isHigh);
      g_drawnBoxes[g_boxCount].isBullish      = isBullish;
      g_drawnBoxes[g_boxCount].isPreIP        = isPreIPBox[i];
      g_drawnBoxes[g_boxCount].isLSBull       = targetIPIsHighArr[i];
      g_drawnBoxes[g_boxCount].targetIPTime   = targetIPTimeArr[i];
      g_drawnBoxes[g_boxCount].targetIPIsHigh = targetIPIsHighArr[i];
      g_drawnBoxes[g_boxCount].isBOFlag       = false;
      g_drawnBoxes[g_boxCount].isRSBull       = false;
      g_drawnBoxes[g_boxCount].isOInner       = false;
      g_drawnBoxes[g_boxCount].isOInnerBull   = false;
      g_drawnBoxes[g_boxCount].isSwap         = false;
      g_drawnBoxes[g_boxCount].isSwapBull     = false;
      g_drawnBoxes[g_boxCount].swapSourceRole = "";
      ArrayResize(g_drawnBoxes[g_boxCount].rsTags, 0);
      if(isPreIPBox[i] && InpHighlightPreIP)
      {
         int tagLen = ArraySize(g_drawnBoxes[g_boxCount].rsTags);
         ArrayResize(g_drawnBoxes[g_boxCount].rsTags, tagLen + 1);
         g_drawnBoxes[g_boxCount].rsTags[tagLen] = "LS";
      }
      g_drawnBoxes[g_boxCount].isMacro        = (tf == PERIOD_W1 || tf == PERIOD_D1 || tf == PERIOD_H4);
      g_boxCount++;
   }
}

//+------------------------------------------------------------------+
//| Print Box Diagnostic Data for Targeted Removal (3-Pivots Deep)   |
//+------------------------------------------------------------------+
void PrintBoxRemovalInfo(int bIdx)
{
   if(bIdx < 0 || bIdx >= g_boxCount) return;

   int swIdx = g_drawnBoxes[bIdx].swingIdx;
   if(swIdx < 0 || swIdx >= g_pivotCountH1 - 1) return;

   SPivot p1 = g_pivotsH1[swIdx];
   SPivot p2 = g_pivotsH1[swIdx + 1];

   g_clickCounter++;
   string legType = (p1.isHigh ? "نزولی (Drop: " + p1.label + " -> " + p2.label + ")" : "صعودی (Rally: " + p1.label + " -> " + p2.label + ")");

   Print("══════════════════════════════════════════════════════════════════════");
   Print("❌ [باکس انتخاب‌شده جهت بررسی و حذف #", g_clickCounter, "]");
   Print("📍 جهت یال: ", legType);
   Print("📌 شروع یال (P1): [", p1.label, "] = ", DoubleToString(p1.price, _Digits), " | زمان=", TimeToString(p1.time));
   Print("📌 پایان یال (P2): [", p2.label, "] = ", DoubleToString(p2.price, _Digits), " | زمان=", TimeToString(p2.time));
   
   Print("--- ⬅️ ۳ پیووت قبلی ---");
   if(swIdx >= 1)
      Print("   ⬅️ ۱ پیووت قبل (P-1): [", g_pivotsH1[swIdx-1].label, "] = ", DoubleToString(g_pivotsH1[swIdx-1].price, _Digits), " | زمان=", TimeToString(g_pivotsH1[swIdx-1].time));
   if(swIdx >= 2)
      Print("   ⬅️ ۲ پیووت قبل (P-2): [", g_pivotsH1[swIdx-2].label, "] = ", DoubleToString(g_pivotsH1[swIdx-2].price, _Digits), " | زمان=", TimeToString(g_pivotsH1[swIdx-2].time));
   if(swIdx >= 3)
      Print("   ⬅️ ۳ پیووت قبل (P-3): [", g_pivotsH1[swIdx-3].label, "] = ", DoubleToString(g_pivotsH1[swIdx-3].price, _Digits), " | زمان=", TimeToString(g_pivotsH1[swIdx-3].time));

   Print("--- ➡️ ۳ پیووت بعدی ---");
   if(swIdx + 2 < g_pivotCountH1)
      Print("   ➡️ ۱ پیووت بعد از P2 (P+2): [", g_pivotsH1[swIdx+2].label, "] = ", DoubleToString(g_pivotsH1[swIdx+2].price, _Digits), " | زمان=", TimeToString(g_pivotsH1[swIdx+2].time));
   if(swIdx + 3 < g_pivotCountH1)
      Print("   ➡️ ۲ پیووت بعد از P2 (P+3): [", g_pivotsH1[swIdx+3].label, "] = ", DoubleToString(g_pivotsH1[swIdx+3].price, _Digits), " | زمان=", TimeToString(g_pivotsH1[swIdx+3].time));
   if(swIdx + 4 < g_pivotCountH1)
      Print("   ➡️ ۳ پیووت بعد از P2 (P+4): [", g_pivotsH1[swIdx+4].label, "] = ", DoubleToString(g_pivotsH1[swIdx+4].price, _Digits), " | زمان=", TimeToString(g_pivotsH1[swIdx+4].time));

   Print("📋 مشخصات خلاصه:");
   Print("   p1=", p1.price, " (", p1.label, "), p2=", p2.price, " (", p2.label, ")");
   Print("══════════════════════════════════════════════════════════════════════");
   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| Find Nearest Drawn Box to Click (Strict Inner Box Priority)      |
//+------------------------------------------------------------------+
int FindNearestBox(datetime clickTime, double clickPrice)
{
   if(g_boxCount <= 0) return -1;

   int matchedIndices[];
   int matchCount = 0;

   for(int i = 0; i < g_boxCount; i++)
   {
      datetime t1 = g_drawnBoxes[i].t1;
      datetime t2 = g_drawnBoxes[i].t2;
      double top = g_drawnBoxes[i].top;
      double bottom = g_drawnBoxes[i].bottom;

      // بررسی محدوده زمانی و قیمتی باکس
      if(clickTime >= t1 - PeriodSeconds(_Period)*2 && clickTime <= t2 + PeriodSeconds(_Period)*150)
      {
         if(clickPrice >= bottom - (top - bottom) * 0.3 && clickPrice <= top + (top - bottom) * 0.3)
         {
            ArrayResize(matchedIndices, matchCount + 1);
            matchedIndices[matchCount] = i;
            matchCount++;
         }
      }
   }

   if(matchCount == 0) return -1;
   if(matchCount == 1) return matchedIndices[0];

   // مرتب‌سازی باکس‌های همپوشان بر اساس مساحت (کوچکترین باکس داخلی در اولویت اول)
   for(int i = 0; i < matchCount - 1; i++)
   {
      for(int j = i + 1; j < matchCount; j++)
      {
         int idx1 = matchedIndices[i];
         int idx2 = matchedIndices[j];
         double area1 = MathAbs(g_drawnBoxes[idx1].top - g_drawnBoxes[idx1].bottom) * (double)(g_drawnBoxes[idx1].t2 - g_drawnBoxes[idx1].t1 + 1);
         double area2 = MathAbs(g_drawnBoxes[idx2].top - g_drawnBoxes[idx2].bottom) * (double)(g_drawnBoxes[idx2].t2 - g_drawnBoxes[idx2].t1 + 1);
         if(area2 < area1)
         {
            int temp = matchedIndices[i];
            matchedIndices[i] = matchedIndices[j];
            matchedIndices[j] = temp;
         }
      }
   }

   return matchedIndices[0];
}

//+------------------------------------------------------------------+
//| Draw RS Breakout Lines directly from LS Launch Boxes             |
//+------------------------------------------------------------------+
void ProcessRSLinesFromLSBoxes(const datetime &chartTime[], const double &chartHigh[], const double &chartLow[], int ratesTotal)
{
   for(int b = 0; b < g_boxCount; b++)
   {
      if(!g_drawnBoxes[b].isPreIP) continue;

      bool targetIsHigh   = g_drawnBoxes[b].targetIPIsHigh;
      datetime targetTime = g_drawnBoxes[b].targetIPTime;
      datetime startTime  = targetTime;

      // اگر برای سقف مستقل است -> خط RS از کف باکس LS شروع می‌شود
      // اگر برای کف مستقل است -> خط RS از سقف باکس LS شروع می‌شود
      double linePrice = targetIsHigh ? g_drawnBoxes[b].bottom : g_drawnBoxes[b].top;
      color lineColor  = targetIsHigh ? InpOriginColorLow : InpOriginColorHigh;

      int targetBarIdx = FindBarIndex(chartTime, ratesTotal, targetTime);
      int searchStart  = targetBarIdx >= 0 ? targetBarIdx : FindBarIndex(chartTime, ratesTotal, startTime);
      if(searchStart < 0) searchStart = 0;

      int breakIdx = ratesTotal - 1;
      for(int k = searchStart + 1; k < ratesTotal; k++)
      {
         if(targetIsHigh)
         {
            if(chartLow[k] < linePrice)
            {
               breakIdx = k;
               break;
            }
         }
         else
         {
            if(chartHigh[k] > linePrice)
            {
               breakIdx = k;
               break;
            }
         }
      }

      datetime endTime = chartTime[breakIdx];
      if(endTime <= startTime && ratesTotal > 0) endTime = chartTime[ratesTotal - 1];

      if(InpEnableOriginLines)
      {
         string lineName = "FLAG_RS_LINE_" + g_drawnBoxes[b].tfTag + "_" + IntegerToString((int)startTime);

         if(ObjectFind(0, lineName) >= 0) ObjectDelete(0, lineName);
         ObjectCreate(0, lineName, OBJ_TREND, 0, startTime, linePrice, endTime, linePrice);
         ObjectSetInteger(0, lineName, OBJPROP_COLOR, lineColor);
         ObjectSetInteger(0, lineName, OBJPROP_STYLE, g_drawnBoxes[b].baseStyle);
         ObjectSetInteger(0, lineName, OBJPROP_WIDTH, InpOriginLineWidth);
         ObjectSetInteger(0, lineName, OBJPROP_RAY_RIGHT, false);
         ObjectSetInteger(0, lineName, OBJPROP_SELECTABLE, false);

         string tooltip = "RS Line " + g_drawnBoxes[b].tfTag + (targetIsHigh ? " Low" : " High") +
                          "\nPrice: " + DoubleToString(linePrice, _Digits) +
                          "\nStart: " + TimeToString(startTime);
         ObjectSetString(0, lineName, OBJPROP_TOOLTIP, tooltip);

         if(InpOriginLabelStyle != LABEL_TOOLTIP)
         {
            string lblName = lineName + "_LBL";
            string lblText = "RS " + g_drawnBoxes[b].tfTag;
            
            if(ObjectFind(0, lblName) >= 0) ObjectDelete(0, lblName);
            
            double posRatio = 0.50;
            if(g_drawnBoxes[b].tf == PERIOD_H1)  posRatio = 0.25;
            if(g_drawnBoxes[b].tf == PERIOD_M15) posRatio = 0.45;
            if(g_drawnBoxes[b].tf == PERIOD_M5)  posRatio = 0.65;
            if(g_drawnBoxes[b].tf == PERIOD_M1)  posRatio = 0.85;

            datetime lblTime = (datetime)(startTime + (endTime - startTime) * posRatio);
            ObjectCreate(0, lblName, OBJ_TEXT, 0, lblTime, linePrice);
            ObjectSetString(0, lblName, OBJPROP_TEXT, lblText);
            ObjectSetInteger(0, lblName, OBJPROP_COLOR, lineColor);
            ObjectSetInteger(0, lblName, OBJPROP_FONTSIZE, 8);
            ObjectSetInteger(0, lblName, OBJPROP_ANCHOR, (targetIsHigh ? ANCHOR_LOWER : ANCHOR_UPPER));
            ObjectSetInteger(0, lblName, OBJPROP_SELECTABLE, false);
         }
      }

      // هایلایت و ثبت تگ RS برای گره در لحظه شکست یا اولین گره بعد از شکست خط
      if(InpHighlightBreakoutFlags && breakIdx < ratesTotal - 1)
      {
         int matchedBoxIdx = -1;

         // حالت ۱: اگر شکست واقعاً داخل گره رخ داده باشد (هم زمانی و هم قیمتی)
         for(int ob = 0; ob < g_boxCount; ob++)
         {
            if(g_drawnBoxes[ob].t1 >= targetTime - 60)
            {
               if(endTime >= g_drawnBoxes[ob].t1 && endTime <= g_drawnBoxes[ob].t2)
               {
                  // شرط قیمتی: خط شکست باید داخل سقف و کف باکس قرار داشته باشد
                  if(linePrice >= g_drawnBoxes[ob].bottom && linePrice <= g_drawnBoxes[ob].top)
                  {
                     matchedBoxIdx = ob;
                     break;
                  }
               }
            }
         }

         // حالت ۲: اگر شکست داخل گره نبود (یا کندل از گره بیرون زده بود)، اولین گره بعدی بعد از زمان شکست
         if(matchedBoxIdx < 0)
         {
            datetime minNextTime = 0;
            for(int ob = 0; ob < g_boxCount; ob++)
            {
               if(g_drawnBoxes[ob].t1 >= endTime)
               {
                  if(matchedBoxIdx < 0 || g_drawnBoxes[ob].t1 < minNextTime)
                  {
                     minNextTime = g_drawnBoxes[ob].t1;
                     matchedBoxIdx = ob;
                  }
               }
            }
         }

         // ثبت تگ RS برای گره منتخب
         if(matchedBoxIdx >= 0)
         {
            g_drawnBoxes[matchedBoxIdx].isBOFlag = true;
            g_drawnBoxes[matchedBoxIdx].isRSBull = !targetIsHigh;
            bool alreadyTagged = false;
            for(int tg = 0; tg < ArraySize(g_drawnBoxes[matchedBoxIdx].rsTags); tg++)
            {
               if(g_drawnBoxes[matchedBoxIdx].rsTags[tg] == "RS") { alreadyTagged = true; break; }
            }
            if(!alreadyTagged)
            {
               int tagLen = ArraySize(g_drawnBoxes[matchedBoxIdx].rsTags);
               ArrayResize(g_drawnBoxes[matchedBoxIdx].rsTags, tagLen + 1);
               g_drawnBoxes[matchedBoxIdx].rsTags[tagLen] = "RS";
            }
         }
      }
   }

   // ۲. رسم خطوط منشأ تایم‌های بالاتر (M15, M5, H1) برای پیووت‌های مستقل چند‌تایم‌فریمه
   ENUM_TIMEFRAMES checkTFs[3] = {PERIOD_H1, PERIOD_M15, PERIOD_M5};
   for(int k = 0; k < g_indepCount; k++)
   {
      bool isHigh        = g_indepPivots[k].isHigh;
      datetime pivotTime = g_indepPivots[k].time;

      for(int s = 0; s < 3; s++)
      {
         ENUM_TIMEFRAMES srcTF = checkTFs[s];
         string tfStr = TFName(srcTF);

         // بررسی اینکه آیا این تایم جزو تگ‌های این پیووت مستقل است یا خیر
         bool tfInPivot = false;
         for(int tg = 0; tg < ArraySize(g_indepPivots[k].tfTags); tg++)
         {
            if(g_indepPivots[k].tfTags[tg] == tfStr) { tfInPivot = true; break; }
         }
         if(!tfInPivot) continue;

         // بررسی اینکه آیا قبلاً باکسی از این تایم خط کشیده است یا خیر
         bool boxAlreadyDrew = false;
         for(int b = 0; b < g_boxCount; b++)
         {
            if(g_drawnBoxes[b].tf == srcTF && g_drawnBoxes[b].isPreIP && g_drawnBoxes[b].targetIPTime == pivotTime)
            {
               boxAlreadyDrew = true;
               break;
            }
         }
         if(boxAlreadyDrew) continue;

         // پیدا کردن آخرین سوینگ منشأ در آن تایم‌فریم قبل از پیووت
         SPivot srcPivots[];
         if(!BuildAlternatingPivots(srcTF, InpSwingBars, InpMaxBarsTF, srcPivots)) continue;
         int nP = ArraySize(srcPivots);
         datetime originStartTime = 0;
         double   originPrice     = 0;

         for(int sp = nP - 1; sp >= 0; sp--)
         {
            if(srcPivots[sp].time < pivotTime && srcPivots[sp].isHigh != isHigh)
            {
               originStartTime = srcPivots[sp].time;
               originPrice     = srcPivots[sp].price;
               break;
            }
         }

         if(originStartTime == 0 || originPrice == 0) continue;

         // محاسبه نقطه شکست بعد از پیووت
         int pivotBarIdx = FindBarIndex(chartTime, ratesTotal, pivotTime);
         if(pivotBarIdx < 0) continue;

         int breakIdx = ratesTotal - 1;
         for(int bar = pivotBarIdx + 1; bar < ratesTotal; bar++)
         {
            if(isHigh)
            {
               if(chartLow[bar] < originPrice)
               {
                  breakIdx = bar;
                  break;
               }
            }
            else
            {
               if(chartHigh[bar] > originPrice)
               {
                  breakIdx = bar;
                  break;
               }
            }
         }

         datetime endTime = chartTime[breakIdx];
         if(endTime <= pivotTime && ratesTotal > 0) endTime = chartTime[ratesTotal - 1];

         if(InpEnableOriginLines)
         {
            string lineName = "FLAG_RS_LINE_" + tfStr + "_" + IntegerToString((int)pivotTime);
            color lineColor = isHigh ? InpOriginColorLow : InpOriginColorHigh;
            ENUM_LINE_STYLE lineStyle = GetTFLineStyle(srcTF);

            if(ObjectFind(0, lineName) >= 0) ObjectDelete(0, lineName);
            ObjectCreate(0, lineName, OBJ_TREND, 0, pivotTime, originPrice, endTime, originPrice);
            ObjectSetInteger(0, lineName, OBJPROP_COLOR, lineColor);
            ObjectSetInteger(0, lineName, OBJPROP_STYLE, lineStyle);
            ObjectSetInteger(0, lineName, OBJPROP_WIDTH, InpOriginLineWidth);
            ObjectSetInteger(0, lineName, OBJPROP_RAY_RIGHT, false);
            ObjectSetInteger(0, lineName, OBJPROP_SELECTABLE, false);

            string tooltip = "RS Line " + tfStr + (isHigh ? " Low" : " High") +
                             "\nPrice: " + DoubleToString(originPrice, _Digits) +
                             "\nStart: " + TimeToString(pivotTime);
            ObjectSetString(0, lineName, OBJPROP_TOOLTIP, tooltip);

            if(InpOriginLabelStyle != LABEL_TOOLTIP)
            {
               string lblName = lineName + "_LBL";
               string lblText = "RS " + tfStr;
               
               if(ObjectFind(0, lblName) >= 0) ObjectDelete(0, lblName);
               
               double posRatio = 0.50;
               if(srcTF == PERIOD_H1)  posRatio = 0.25;
               if(srcTF == PERIOD_M15) posRatio = 0.45;
               if(srcTF == PERIOD_M5)  posRatio = 0.65;

               datetime lblTime = (datetime)(pivotTime + (endTime - pivotTime) * posRatio);
               ObjectCreate(0, lblName, OBJ_TEXT, 0, lblTime, originPrice);
               ObjectSetString(0, lblName, OBJPROP_TEXT, lblText);
               ObjectSetInteger(0, lblName, OBJPROP_COLOR, lineColor);
               ObjectSetInteger(0, lblName, OBJPROP_FONTSIZE, 8);
               ObjectSetInteger(0, lblName, OBJPROP_ANCHOR, (isHigh ? ANCHOR_LOWER : ANCHOR_UPPER));
               ObjectSetInteger(0, lblName, OBJPROP_SELECTABLE, false);
            }
         }

         // هایلایت و ثبت تگ RS برای اولین گره در محل شکست یا بعد از شکست
         if(InpHighlightBreakoutFlags && breakIdx < ratesTotal - 1)
         {
            int matchedBoxIdx = -1;
            for(int ob = 0; ob < g_boxCount; ob++)
            {
               if(g_drawnBoxes[ob].t1 >= pivotTime - 60)
               {
                  if(endTime >= g_drawnBoxes[ob].t1 && endTime <= g_drawnBoxes[ob].t2)
                  {
                     if(originPrice >= g_drawnBoxes[ob].bottom && originPrice <= g_drawnBoxes[ob].top)
                     {
                        matchedBoxIdx = ob;
                        break;
                     }
                  }
               }
            }

            if(matchedBoxIdx < 0)
            {
               datetime minNextTime = 0;
               for(int ob = 0; ob < g_boxCount; ob++)
               {
                  if(g_drawnBoxes[ob].t1 >= endTime)
                  {
                     if(matchedBoxIdx < 0 || g_drawnBoxes[ob].t1 < minNextTime)
                     {
                        minNextTime = g_drawnBoxes[ob].t1;
                        matchedBoxIdx = ob;
                     }
                  }
               }
            }

            if(matchedBoxIdx >= 0)
            {
               g_drawnBoxes[matchedBoxIdx].isBOFlag = true;
               g_drawnBoxes[matchedBoxIdx].isRSBull = !isHigh;
               bool alreadyTagged = false;
               for(int tg = 0; tg < ArraySize(g_drawnBoxes[matchedBoxIdx].rsTags); tg++)
               {
                  if(g_drawnBoxes[matchedBoxIdx].rsTags[tg] == "RS") { alreadyTagged = true; break; }
               }
               if(!alreadyTagged)
               {
                  int tagLen = ArraySize(g_drawnBoxes[matchedBoxIdx].rsTags);
                  ArrayResize(g_drawnBoxes[matchedBoxIdx].rsTags, tagLen + 1);
                  g_drawnBoxes[matchedBoxIdx].rsTags[tagLen] = "RS";
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Tag First Post-IP Flag Box as OInner                             |
//+------------------------------------------------------------------+
void ProcessOInnerBoxes()
{
   if(!InpHighlightOInner) return;

   for(int k = 0; k < g_indepCount; k++)
   {
      datetime pivotTime = g_indepPivots[k].time;
      bool isHigh        = g_indepPivots[k].isHigh;

      for(int t = 0; t < ArraySize(g_indepPivots[k].tfTags); t++)
      {
         string tfStr = g_indepPivots[k].tfTags[t];
         
         int firstBoxIdx = -1;
         datetime minBoxTime = 0;
         for(int ob = 0; ob < g_boxCount; ob++)
         {
            if(g_drawnBoxes[ob].tfTag == tfStr && g_drawnBoxes[ob].t1 >= pivotTime - 60)
            {
               if(firstBoxIdx < 0 || g_drawnBoxes[ob].t1 < minBoxTime)
               {
                  minBoxTime = g_drawnBoxes[ob].t1;
                  firstBoxIdx = ob;
               }
            }
         }

         if(firstBoxIdx >= 0)
         {
            g_drawnBoxes[firstBoxIdx].isOInner     = true;
            g_drawnBoxes[firstBoxIdx].isOInnerBull = !isHigh;

            bool alreadyTagged = false;
            for(int tg = 0; tg < ArraySize(g_drawnBoxes[firstBoxIdx].rsTags); tg++)
            {
               if(g_drawnBoxes[firstBoxIdx].rsTags[tg] == "OInner") { alreadyTagged = true; break; }
            }
            if(!alreadyTagged)
            {
               int tagLen = ArraySize(g_drawnBoxes[firstBoxIdx].rsTags);
               ArrayResize(g_drawnBoxes[firstBoxIdx].rsTags, tagLen + 1);
               g_drawnBoxes[firstBoxIdx].rsTags[tagLen] = "OInner";
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Universal Box Swap System (S-Prefix Breakout & Reaction Flags)   |
//+------------------------------------------------------------------+
void ProcessUniversalSwapLines(const datetime &chartTime[], const double &chartHigh[], const double &chartLow[], int ratesTotal)
{
   if(!InpEnableSwapLines) return;

   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;
   int initialBoxCount = g_boxCount;
   for(int b = 0; b < initialBoxCount; b++)
   {
      // مشخص کردن جهت اصلی باکس (صعودی یا نزولی)
      bool isBull = g_drawnBoxes[b].isBullish;
      if(g_drawnBoxes[b].isPreIP) isBull = g_drawnBoxes[b].isLSBull;
      else if(g_drawnBoxes[b].isOInner) isBull = g_drawnBoxes[b].isOInnerBull;
      else if(g_drawnBoxes[b].isBOFlag) isBull = g_drawnBoxes[b].isRSBull;

      // ۱. اگر باکس صعودی است -> خط از کف باکس شروع شده و شکست به زیر کف بررسی می‌شود
      // ۲. اگر باکس نزولی است -> خط از سقف باکس شروع شده و شکست به بالای سقف بررسی می‌شود
      double linePrice = isBull ? g_drawnBoxes[b].bottom : g_drawnBoxes[b].top;
      color lineColor  = isBull ? InpSwapColorBear : InpSwapColorBull;
      datetime startTime = g_drawnBoxes[b].t2;

      int startSearchIdx = FindBarIndex(chartTime, ratesTotal, g_drawnBoxes[b].t2);
      if(startSearchIdx < 0) startSearchIdx = FindBarIndex(chartTime, ratesTotal, startTime);
      if(startSearchIdx < 0) startSearchIdx = 0;

      bool isBroken = false;
      int breakIdx = ratesTotal - 1;
      for(int k = startSearchIdx + 1; k < ratesTotal; k++)
      {
         if(isBull)
         {
            if(chartLow[k] < linePrice)
            {
               isBroken = true;
               breakIdx = k;
               break;
            }
         }
         else
         {
            if(chartHigh[k] > linePrice)
            {
               isBroken = true;
               breakIdx = k;
               break;
            }
         }
      }

      datetime liveTime = (ratesTotal > 0) ? chartTime[ratesTotal - 1] : 0;
      datetime endTime = isBroken ? chartTime[breakIdx] : liveTime;
      if(endTime <= g_drawnBoxes[b].t1 && ratesTotal > 0) endTime = liveTime;

      // امتداد باکس به صورت مستطیل یکپارچه تا زمان شکست یا تا لایو بازار
      g_drawnBoxes[b].t2 = endTime;

      // نام و نقش باکس مبدأ جهت تولید پیشوند S-
      string srcRole = "Flag";
      for(int tg = 0; tg < ArraySize(g_drawnBoxes[b].rsTags); tg++)
      {
         if(g_drawnBoxes[b].rsTags[tg] == "OInner") { srcRole = "OInner"; break; }
         if(g_drawnBoxes[b].rsTags[tg] == "RS")     { srcRole = "RS";     break; }
         if(g_drawnBoxes[b].rsTags[tg] == "LS")     { srcRole = "LS";     break; }
      }

      // فقط باکس‌های کلیدی منشأ سواپ می‌شوند
      if(InpSwapOnlyKeyBoxes && srcRole == "Flag") continue;

      // پیدا کردن و ثبت باکس سواپ متناظر (گره واقعی تشکیل‌شده در سطح و زمان شکست)
      if(breakIdx < ratesTotal - 1)
      {
         int matchedBoxIdx = -1;

         for(int ob = 0; ob < initialBoxCount; ob++)
         {
            if(ob == b) continue;
            // گره باید همپوشانی زمانی با شکست داشته باشد و قیمت خط شکست را شامل شود
            if(endTime >= g_drawnBoxes[ob].t1 - PeriodSeconds(g_drawnBoxes[ob].tf) * 2 &&
               endTime <= g_drawnBoxes[ob].t2 + PeriodSeconds(g_drawnBoxes[ob].tf) * 2)
            {
               if(linePrice >= g_drawnBoxes[ob].bottom - 2 * pipSize && linePrice <= g_drawnBoxes[ob].top + 2 * pipSize)
               {
                  matchedBoxIdx = ob;
                  break;
               }
            }
         }

         if(matchedBoxIdx >= 0)
         {
            g_drawnBoxes[matchedBoxIdx].isSwap         = true;
            g_drawnBoxes[matchedBoxIdx].isSwapBull     = !isBull;
            g_drawnBoxes[matchedBoxIdx].swapSourceRole = srcRole;

            string sTag = "S-" + srcRole;
            bool alreadyTagged = false;
            for(int tg = 0; tg < ArraySize(g_drawnBoxes[matchedBoxIdx].rsTags); tg++)
            {
               if(g_drawnBoxes[matchedBoxIdx].rsTags[tg] == sTag) { alreadyTagged = true; break; }
            }
            if(!alreadyTagged)
            {
               int tagLen = ArraySize(g_drawnBoxes[matchedBoxIdx].rsTags);
               ArrayResize(g_drawnBoxes[matchedBoxIdx].rsTags, tagLen + 1);
               g_drawnBoxes[matchedBoxIdx].rsTags[tagLen] = sTag;
            }
         }
      }
   }

   // مرحله ۲: امتداد تمامی باکس‌های سواپ (S-OInner, S-RS, S-LS) تا زمان شکست یا تا لایو بازار
   for(int sb = 0; sb < g_boxCount; sb++)
   {
      if(!g_drawnBoxes[sb].isSwap) continue;

      bool isBull = g_drawnBoxes[sb].isSwapBull;
      double linePrice = isBull ? g_drawnBoxes[sb].bottom : g_drawnBoxes[sb].top;
      datetime origT2  = g_drawnBoxes[sb].t2;

      int startSearchIdx = FindBarIndex(chartTime, ratesTotal, origT2);
      if(startSearchIdx < 0) startSearchIdx = 0;

      bool isBroken = false;
      int breakIdx = ratesTotal - 1;
      for(int k = startSearchIdx + 1; k < ratesTotal; k++)
      {
         if(isBull)
         {
            if(chartLow[k] < linePrice)
            {
               isBroken = true;
               breakIdx = k;
               break;
            }
         }
         else
         {
            if(chartHigh[k] > linePrice)
            {
               isBroken = true;
               breakIdx = k;
               break;
            }
         }
      }

      datetime liveTime = (ratesTotal > 0) ? chartTime[ratesTotal - 1] : 0;
      datetime endTime = isBroken ? chartTime[breakIdx] : liveTime;
      if(endTime <= g_drawnBoxes[sb].t1 && ratesTotal > 0) endTime = liveTime;

      g_drawnBoxes[sb].t2 = endTime;
   }
}

//+------------------------------------------------------------------+
//| Render Final Boxes with Smart Filtering and Multi-Tagging        |
//+------------------------------------------------------------------+
void RenderFinalBoxes()
{
   for(int b = 0; b < g_boxCount; b++)
   {
      bool isMacro = g_drawnBoxes[b].isMacro;
      bool hasRSTags = (ArraySize(g_drawnBoxes[b].rsTags) > 0);

      bool isSRS     = (g_drawnBoxes[b].isSwap && g_drawnBoxes[b].swapSourceRole == "RS");
      bool isOI      = g_drawnBoxes[b].isOInner;
      bool isRS      = g_drawnBoxes[b].isBOFlag;
      bool isAnySwap = g_drawnBoxes[b].isSwap;

      for(int t = 0; t < ArraySize(g_drawnBoxes[b].rsTags); t++)
      {
         string tg = g_drawnBoxes[b].rsTags[t];
         if(StringFind(tg, "S-RS") >= 0) isSRS = true;
         if(tg == "OInner") isOI = true;
         if(tg == "RS") isRS = true;
         if(StringFind(tg, "S-") == 0) isAnySwap = true;
      }

      if(InpDisplayFilter == FILTER_ONLY_SRS)
      {
         if(!isSRS) continue;
      }
      else if(InpDisplayFilter == FILTER_HIGH_WINRATE)
      {
         if(!isSRS && !isOI && !isRS) continue;
      }
      else if(InpDisplayFilter == FILTER_ALL_SWAPS)
      {
         if(!isAnySwap) continue;
      }
      else // FILTER_ALL
      {
         bool shouldDraw = false;
         if(isMacro)
         {
            if(InpShowMacroAlways)
               shouldDraw = true;
         }
         else
         {
            // برای تایم‌های میکرو (H1, M15, M5, M1)
            if(hasRSTags && InpShowOnlyRSMicroBoxes)
               shouldDraw = true;
            else if(InpShowNormalMicroBoxes)
               shouldDraw = true;
         }

         if(!shouldDraw)
            continue;
      }

      // تعیین رنگ، ضخامت و برچسب تفکیک‌شده برای صعودی و نزولی
      color drawClr = g_drawnBoxes[b].baseColor;
      int drawWidth = g_drawnBoxes[b].baseWidth;
      string roleTag = "";

      ENUM_LINE_STYLE drawStyle = g_drawnBoxes[b].baseStyle;

      if(hasRSTags)
      {
         bool isLS = false;
         bool isRS = false;
         bool isOI = false;
         bool isSwap = false;
         string swapTag = "";

         for(int t = 0; t < ArraySize(g_drawnBoxes[b].rsTags); t++)
         {
            string tg = g_drawnBoxes[b].rsTags[t];
            if(tg == "LS") isLS = true;
            else if(tg == "RS") isRS = true;
            else if(tg == "OInner") isOI = true;
            else if(StringFind(tg, "S-") == 0)
            {
               isSwap = true;
               swapTag += (swapTag == "" ? "" : "+") + tg;
            }
         }

         string tagCombo = "";
         if(isLS) tagCombo += (tagCombo == "" ? "LS" : "+LS");
         if(isOI) tagCombo += (tagCombo == "" ? "OInner" : "+OInner");
         if(isRS) tagCombo += (tagCombo == "" ? "RS" : "+RS");
         if(isSwap) tagCombo += (tagCombo == "" ? swapTag : "+" + swapTag);

         bool isBull = false;
         if(isSwap) isBull = g_drawnBoxes[b].isSwapBull;
         else if(isLS) isBull = g_drawnBoxes[b].isLSBull;
         else if(isOI) isBull = g_drawnBoxes[b].isOInnerBull;
         else if(isRS) isBull = g_drawnBoxes[b].isRSBull;
         else isBull = g_drawnBoxes[b].isBullish;

         roleTag = tagCombo + (isBull ? " Bull" : " Bear");

         if(isSwap)
         {
            if(StringFind(swapTag, "S-OInner") >= 0)
               drawClr = isBull ? clrMediumSpringGreen : clrTomato;
            else if(StringFind(swapTag, "S-RS") >= 0)
               drawClr = isBull ? clrCyan : clrCoral;
            else if(StringFind(swapTag, "S-LS") >= 0)
               drawClr = isBull ? clrSpringGreen : clrHotPink;
            else
               drawClr = isBull ? InpSwapColorBull : InpSwapColorBear;

            drawWidth = InpSwapBoxWidth;
            drawStyle = STYLE_DOT; // خط نقطه‌چین شیک برای سواپ‌ها
         }
         else if(isLS && isRS)
         {
            drawClr   = isBull ? InpComboColorBull : InpComboColorBear;
            drawWidth = 3;
            drawStyle = STYLE_DASH; // خط‌چین برای کمبو
         }
         else if(isOI && isRS)
         {
            drawClr   = isBull ? InpRSColorBull : InpRSColorBear;
            drawWidth = InpBreakoutFlagWidth;
            drawStyle = STYLE_DASH; // خط‌چین برای OInner+RS
         }
         else if(isLS)
         {
            drawClr   = isBull ? InpLSColorBull : InpLSColorBear;
            drawWidth = InpPreIPWidth;
            drawStyle = STYLE_DASH; // خط‌چین برای LS
         }
         else if(isOI)
         {
            drawClr   = isBull ? InpOInnerColorBull : InpOInnerColorBear;
            drawWidth = InpOInnerWidth;
            drawStyle = STYLE_DASH; // خط‌چین برای OInner
         }
         else if(isRS)
         {
            drawClr   = isBull ? InpRSColorBull : InpRSColorBear;
            drawWidth = InpBreakoutFlagWidth;
            drawStyle = STYLE_DOT; // نقطه‌چین برای RS
         }
      }

      DrawHollowBox(g_drawnBoxes[b].boxName,
                    g_drawnBoxes[b].t1,
                    g_drawnBoxes[b].top,
                    g_drawnBoxes[b].t2,
                    g_drawnBoxes[b].bottom,
                    drawClr,
                    drawWidth,
                    drawStyle);

      // برچسب هوشمند متصل به بالای باکس
      if(InpShowLabel)
      {
         datetime labelTime = (datetime)((g_drawnBoxes[b].t1 + g_drawnBoxes[b].t2) / 2);
         double labelPrice = g_drawnBoxes[b].top + (g_drawnBoxes[b].top - g_drawnBoxes[b].bottom) * 0.05;

         string lblName = "FLAG_LBL_" + g_drawnBoxes[b].boxName;
         string lblText = (roleTag != "") ? (roleTag + " [" + g_drawnBoxes[b].tfTag + "]") : g_drawnBoxes[b].tfTag;

         if(ObjectFind(0, lblName) >= 0) ObjectDelete(0, lblName);
         ObjectCreate(0, lblName, OBJ_TEXT, 0, labelTime, labelPrice);
         ObjectSetString(0, lblName, OBJPROP_TEXT, lblText);
         ObjectSetInteger(0, lblName, OBJPROP_COLOR, drawClr);
         ObjectSetInteger(0, lblName, OBJPROP_FONTSIZE, 8);
         ObjectSetInteger(0, lblName, OBJPROP_ANCHOR, ANCHOR_CENTER);
         ObjectSetInteger(0, lblName, OBJPROP_SELECTABLE, false);
      }
   }
}

//+------------------------------------------------------------------+
//| Render Final Aggregated Independent Pivots (No Overlapping)      |
//+------------------------------------------------------------------+
void RenderFinalIndependentPivots()
{
   if(InpDisplayFilter == FILTER_ONLY_SRS || !InpShowIndependentPivots) return;

   for(int k = 0; k < g_indepCount; k++)
   {
      string combinedTFs = "";
      for(int t = 0; t < ArraySize(g_indepPivots[k].tfTags); t++)
      {
         combinedTFs += (t > 0 ? "/" : "") + g_indepPivots[k].tfTags[t];
      }

      string lblText = (g_indepPivots[k].hasIP ? "IP " : "") + combinedTFs;

      string ipName = "FLAG_IP_" + IntegerToString((int)g_indepPivots[k].time) + "_" + (g_indepPivots[k].isHigh ? "H" : "L") + "_" + IntegerToString(k);
      
      if(ObjectFind(0, ipName) >= 0) ObjectDelete(0, ipName);
      ObjectCreate(0, ipName, OBJ_ARROW, 0, g_indepPivots[k].time, g_indepPivots[k].price);
      ObjectSetInteger(0, ipName, OBJPROP_ARROWCODE, InpIndepMarkCode);
      ObjectSetInteger(0, ipName, OBJPROP_COLOR,      g_indepPivots[k].clr);
      ObjectSetInteger(0, ipName, OBJPROP_WIDTH,      InpIndepMarkWidth);
      ObjectSetInteger(0, ipName, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, ipName, OBJPROP_ANCHOR, (g_indepPivots[k].isHigh ? ANCHOR_BOTTOM : ANCHOR_TOP));

      if(InpIndepShowLabel)
      {
         string lblName = ipName + "_LBL";
         if(ObjectFind(0, lblName) >= 0) ObjectDelete(0, lblName);
         ObjectCreate(0, lblName, OBJ_TEXT, 0, g_indepPivots[k].time, g_indepPivots[k].price);
         ObjectSetString(0, lblName, OBJPROP_TEXT, lblText);
         ObjectSetInteger(0, lblName, OBJPROP_COLOR, g_indepPivots[k].clr);
         ObjectSetInteger(0, lblName, OBJPROP_FONTSIZE, 8);
         ObjectSetInteger(0, lblName, OBJPROP_ANCHOR, (g_indepPivots[k].isHigh ? ANCHOR_LOWER : ANCHOR_UPPER));
         ObjectSetInteger(0, lblName, OBJPROP_SELECTABLE, false);
      }
   }
}

//+------------------------------------------------------------------+
//| Apply High-Contrast Neutral Pro Chart Theme                      |
//+------------------------------------------------------------------+
void ApplyProChartTheme()
{
   if(!InpApplyProTheme) return;

   // پس‌زمینه زغالی مدرن و ملایم (کنتراست حداکثری بدون خستگی چشم)
   color darkCharcoal = (color)0x181512; // TradingView Deep Slate
   
   ChartSetInteger(0, CHART_COLOR_BACKGROUND, darkCharcoal);
   ChartSetInteger(0, CHART_COLOR_FOREGROUND, clrSilver);
   ChartSetInteger(0, CHART_COLOR_GRID, clrNONE);
   ChartSetInteger(0, CHART_SHOW_GRID, false);
   ChartSetInteger(0, CHART_SHOW_VOLUMES, CHART_VOLUME_HIDE);

   // کندل‌های خنثی متالیک: صعودی نقره‌ای/سفید، نزولی دودی/خاکستری تیره
   ChartSetInteger(0, CHART_COLOR_CHART_UP,    clrSilver);
   ChartSetInteger(0, CHART_COLOR_CHART_DOWN,  clrDimGray);
   ChartSetInteger(0, CHART_COLOR_CANDLE_BULL, clrWhite);
   ChartSetInteger(0, CHART_COLOR_CANDLE_BEAR, (color)0x352B28); // دودی تیره
   ChartSetInteger(0, CHART_COLOR_CHART_LINE,  clrLightSlateGray);
   ChartSetInteger(0, CHART_MODE, CHART_CANDLES);
}

//+------------------------------------------------------------------+
//| Interactive On-Demand Trade Simulation for Clicked Box in History |
//+------------------------------------------------------------------+
void ShowTradeSetupForBox(int boxIdx)
{
   ObjectsDeleteAll(0, "FLAG_CLICK_TRADE_");
   if(boxIdx < 0 || boxIdx >= g_boxCount) return;

   datetime chartTime[];
   double chartHigh[], chartLow[];
   ArraySetAsSeries(chartTime, false);
   ArraySetAsSeries(chartHigh, false);
   ArraySetAsSeries(chartLow, false);

   int copied = CopyTime(_Symbol, _Period, 0, 30000, chartTime);
   CopyHigh(_Symbol, _Period, 0, 30000, chartHigh);
   CopyLow(_Symbol, _Period, 0, 30000, chartLow);
   if(copied < 10) return;

   string role = "Flag";
   for(int tg = 0; tg < ArraySize(g_drawnBoxes[boxIdx].rsTags); tg++)
   {
      if(g_drawnBoxes[boxIdx].rsTags[tg] == "OInner") { role = "OInner"; break; }
      if(g_drawnBoxes[boxIdx].rsTags[tg] == "RS")     { role = "RS";     break; }
      if(g_drawnBoxes[boxIdx].rsTags[tg] == "LS")     { role = "LS";     break; }
      if(StringFind(g_drawnBoxes[boxIdx].rsTags[tg], "S-") == 0) { role = g_drawnBoxes[boxIdx].rsTags[tg]; break; }
   }

   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;

   // ۱. جهت معامله و استاپ لاس بر اساس نوع باکس
   bool   isBull     = true;
   double entryPrice = 0;
   double slPrice    = 0;

   if(role == "OInner")
   {
      // پیدا کردن نزدیک‌ترین پیووت مستقل قبل از این باکس OInner
      double   pivotP = 0;
      datetime closestPivotTime = 0;
      bool     pivotIsHigh = false;

      for(int ip = 0; ip < g_indepCount; ip++)
      {
         if(g_indepPivots[ip].time <= g_drawnBoxes[boxIdx].t1 + 60)
         {
            if(g_indepPivots[ip].time > closestPivotTime)
            {
               closestPivotTime = g_indepPivots[ip].time;
               pivotP           = g_indepPivots[ip].price;
               pivotIsHigh      = g_indepPivots[ip].isHigh;
            }
         }
      }

      if(pivotP == 0)
      {
         // در صورت عدم یافتن، از سقف/کف خود باکس با بافر استفاده می‌شود
         pivotIsHigh = !g_drawnBoxes[boxIdx].isOInnerBull;
         pivotP      = pivotIsHigh ? g_drawnBoxes[boxIdx].top : g_drawnBoxes[boxIdx].bottom;
      }

      if(pivotIsHigh)
      {
         // حرکت رو به پایین از قله -> معامله فروش (SELL)
         isBull     = false;
         entryPrice = g_drawnBoxes[boxIdx].bottom;
         slPrice    = pivotP + 2 * pipSize; // استاپ دقیقاً بالای قله پیووت مستقل
      }
      else
      {
         // حرکت رو به بالا از کف -> معامله خرید (BUY)
         isBull     = true;
         entryPrice = g_drawnBoxes[boxIdx].top;
         slPrice    = pivotP - 2 * pipSize; // استاپ دقیقاً پایین دره پیووت مستقل
      }
   }
   else
   {
      isBull = g_drawnBoxes[boxIdx].isBullish;
      if(g_drawnBoxes[boxIdx].isPreIP) isBull = g_drawnBoxes[boxIdx].isLSBull;
      else if(g_drawnBoxes[boxIdx].isBOFlag) isBull = g_drawnBoxes[boxIdx].isRSBull;
      else if(g_drawnBoxes[boxIdx].isSwap) isBull = g_drawnBoxes[boxIdx].isSwapBull;

      if(isBull)
      {
         entryPrice = g_drawnBoxes[boxIdx].top;
         slPrice    = g_drawnBoxes[boxIdx].bottom - InpRSPipBuffer * pipSize; // ۱۰ پیپ زیر کف
      }
      else
      {
         entryPrice = g_drawnBoxes[boxIdx].bottom;
         slPrice    = g_drawnBoxes[boxIdx].top + InpRSPipBuffer * pipSize; // ۱۰ پیپ بالای سقف
      }
   }

   double risk = MathAbs(entryPrice - slPrice);
   if(risk <= 0) return;

   // ۲. پیدا کردن اولین بازگشت و لمس به باکس در گذشته (First Touch)
   int boxEndIdx = -1;
   for(int i = 0; i < copied; i++)
   {
      if(chartTime[i] >= g_drawnBoxes[boxIdx].t2) { boxEndIdx = i; break; }
   }
   if(boxEndIdx < 0) return;

   int entryBar = -1;
   bool hasDeparted = false;

   for(int k = boxEndIdx + 1; k < copied; k++)
   {
      if(!hasDeparted)
      {
         if(isBull && chartHigh[k] > g_drawnBoxes[boxIdx].top + 1 * pipSize) hasDeparted = true;
         else if(!isBull && chartLow[k] < g_drawnBoxes[boxIdx].bottom - 1 * pipSize) hasDeparted = true;
         else if(k > boxEndIdx + 2) hasDeparted = true;
      }

      if(hasDeparted)
      {
         if(isBull)
         {
            if(chartLow[k] <= g_drawnBoxes[boxIdx].top && chartHigh[k] >= g_drawnBoxes[boxIdx].bottom)
            {
               entryBar = k;
               break;
            }
         }
         else
         {
            if(chartHigh[k] >= g_drawnBoxes[boxIdx].bottom && chartLow[k] <= g_drawnBoxes[boxIdx].top)
            {
               entryBar = k;
               break;
            }
         }
      }
   }

   // ۳. محاسبه دقیق تارگت‌های ۱:۱ تا ۱:۴ بر اساس نسبت ریسک
   double tp1 = isBull ? (entryPrice + 1.0 * risk) : (entryPrice - 1.0 * risk);
   double tp2 = isBull ? (entryPrice + 2.0 * risk) : (entryPrice - 2.0 * risk);
   double tp3 = isBull ? (entryPrice + 3.0 * risk) : (entryPrice - 3.0 * risk);
   double tp4 = isBull ? (entryPrice + 4.0 * risk) : (entryPrice - 4.0 * risk);

   datetime entryTime = 0;
   datetime exitTime  = chartTime[copied - 1];
   int      hitTP     = 0;
   bool     isClosed  = false;
   bool     isPending = false;

   if(entryBar < 0)
   {
      // ستاپ معلق برای لایو / هنوز لمس نشده (طرح معامله پیش‌رو)
      isPending = true;
      entryTime = g_drawnBoxes[boxIdx].t2;
      exitTime  = chartTime[copied - 1] + PeriodSeconds(_Period) * 20;
   }
   else
   {
      entryTime = chartTime[entryBar];

      for(int k = entryBar + 1; k < copied; k++)
      {
         if(isBull)
         {
            if(chartLow[k] <= slPrice)
            {
               isClosed = true;
               exitTime = chartTime[k];
               break;
            }
            if(chartHigh[k] >= tp4) { hitTP = 4; isClosed = true; exitTime = chartTime[k]; break; }
            else if(chartHigh[k] >= tp3 && hitTP < 3) { hitTP = 3; }
            else if(chartHigh[k] >= tp2 && hitTP < 2) { hitTP = 2; }
            else if(chartHigh[k] >= tp1 && hitTP < 1) { hitTP = 1; }
         }
         else
         {
            if(chartHigh[k] >= slPrice)
            {
               isClosed = true;
               exitTime = chartTime[k];
               break;
            }
            if(chartLow[k] <= tp4) { hitTP = 4; isClosed = true; exitTime = chartTime[k]; break; }
            else if(chartLow[k] <= tp3 && hitTP < 3) { hitTP = 3; }
            else if(chartLow[k] <= tp2 && hitTP < 2) { hitTP = 2; }
            else if(chartLow[k] <= tp1 && hitTP < 1) { hitTP = 1; }
         }
      }
   }

   datetime t1 = entryTime;
   datetime t2 = exitTime;
   if(t2 <= t1) t2 = t1 + PeriodSeconds(_Period) * 10;

   string pfx = "FLAG_CLICK_TRADE_";

   // ۱. خط نقطه ورود
   string entryLine = pfx + "ENTRY";
   ObjectCreate(0, entryLine, OBJ_TREND, 0, t1, entryPrice, t2, entryPrice);
   ObjectSetInteger(0, entryLine, OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, entryLine, OBJPROP_WIDTH, 2);
   ObjectSetInteger(0, entryLine, OBJPROP_STYLE, STYLE_SOLID);
   ObjectSetInteger(0, entryLine, OBJPROP_RAY_RIGHT, false);
   ObjectSetInteger(0, entryLine, OBJPROP_SELECTABLE, false);

   // ۲. خط استاپ لاس
   string slLine = pfx + "SL";
   ObjectCreate(0, slLine, OBJ_TREND, 0, t1, slPrice, t2, slPrice);
   ObjectSetInteger(0, slLine, OBJPROP_COLOR, clrRed);
   ObjectSetInteger(0, slLine, OBJPROP_WIDTH, 1);
   ObjectSetInteger(0, slLine, OBJPROP_STYLE, STYLE_DASH);
   ObjectSetInteger(0, slLine, OBJPROP_RAY_RIGHT, false);
   ObjectSetInteger(0, slLine, OBJPROP_SELECTABLE, false);

   // ۳. خطوط تارگت‌های ۱ تا ۴
   double tps[4] = {tp1, tp2, tp3, tp4};
   string tpLabels[4] = {"1:1", "1:2", "1:3", "1:4"};

   for(int tp = 0; tp < 4; tp++)
   {
      string tpLine = pfx + "TP" + IntegerToString(tp + 1);
      ObjectCreate(0, tpLine, OBJ_TREND, 0, t1, tps[tp], t2, tps[tp]);
      ObjectSetInteger(0, tpLine, OBJPROP_COLOR, clrLimeGreen);
      ObjectSetInteger(0, tpLine, OBJPROP_WIDTH, (hitTP >= tp + 1 ? 2 : 1));
      ObjectSetInteger(0, tpLine, OBJPROP_STYLE, (hitTP >= tp + 1 ? STYLE_SOLID : STYLE_DOT));
      ObjectSetInteger(0, tpLine, OBJPROP_RAY_RIGHT, false);
      ObjectSetInteger(0, tpLine, OBJPROP_SELECTABLE, false);

      string tpLbl = tpLine + "_LBL";
      ObjectCreate(0, tpLbl, OBJ_TEXT, 0, t2, tps[tp]);
      ObjectSetString(0, tpLbl, OBJPROP_TEXT, "TP " + tpLabels[tp]);
      ObjectSetInteger(0, tpLbl, OBJPROP_COLOR, clrLimeGreen);
      ObjectSetInteger(0, tpLbl, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, tpLbl, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(0, tpLbl, OBJPROP_SELECTABLE, false);
   }

   // ۴. برچسب نتیجه
   string resName = pfx + "RES";
   string resText = "";
   color  resColor = clrGray;

   if(hitTP == 4)        { resText = "WIN 1:4 🎯"; resColor = clrLime; }
   else if(hitTP == 3)   { resText = "WIN 1:3 🚀"; resColor = clrMediumSpringGreen; }
   else if(hitTP == 2)   { resText = "WIN 1:2 ✅"; resColor = clrDodgerBlue; }
   else if(hitTP == 1)   { resText = "WIN 1:1 👍"; resColor = clrCyan; }
   else if(isClosed)     { resText = "LOSS ❌";   resColor = clrRed; }
   else if(isPending)    { resText = "PENDING ⏳"; resColor = clrYellow; }
   else                  { resText = "OPEN ⏳";   resColor = clrGold; }

   string fullBadge = (isBull ? "🟢 BUY " : "🔴 SELL ") + role + " -> " + resText;
   ObjectCreate(0, resName, OBJ_TEXT, 0, t1, entryPrice);
   ObjectSetString(0, resName, OBJPROP_TEXT, fullBadge);
   ObjectSetInteger(0, resName, OBJPROP_COLOR, resColor);
   ObjectSetInteger(0, resName, OBJPROP_FONTSIZE, 9);
   ObjectSetInteger(0, resName, OBJPROP_ANCHOR, (isBull ? ANCHOR_LOWER : ANCHOR_UPPER));
   ObjectSetInteger(0, resName, OBJPROP_SELECTABLE, false);

   Print("══════════════════════════════════════════════════════════════════════");
   Print("📊 [ستاپ معاملاتی باکس انتخاب‌شده در گذشته چارت]");
   Print("📌 نوع باکس: ", role, " (", g_drawnBoxes[boxIdx].tfTag, ")");
   Print("📍 نوع معامله: ", (isBull ? "BUY (خرید)" : "SELL (فروش)"));
   Print("⏱ زمان لمس و ورود در گذشته: ", TimeToString(entryTime));
   Print("🎯 قیمت ورود (Entry): ", DoubleToString(entryPrice, _Digits));
   Print("🛑 حد ضرر (SL): ", DoubleToString(slPrice, _Digits), " (ریسک: ", DoubleToString(risk/pipSize, 1), " پیپ)");
   Print("🏁 تارگت‌ها: TP1=", DoubleToString(tp1, _Digits), " | TP2=", DoubleToString(tp2, _Digits), " | TP3=", DoubleToString(tp3, _Digits), " | TP4=", DoubleToString(tp4, _Digits));
   Print("🏆 نتیجه در تاریخچه: ", resText);
   Print("══════════════════════════════════════════════════════════════════════");
}

//+------------------------------------------------------------------+
//| Export All Simulated Trades for All Boxes to CSV for Python      |
//+------------------------------------------------------------------+
void ExportAllTradesToCSV()
{
   string filename = "flag_trades_export.csv";
   int fileHandle = FileOpen(filename, FILE_WRITE | FILE_CSV | FILE_ANSI, ",");
   if(fileHandle == INVALID_HANDLE) return;

   FileWrite(fileHandle, "BoxID", "Timeframe", "Role", "Direction", "StartTime", "EndTime", "TopPrice", "BottomPrice", "EntryTime", "EntryPrice", "SLPrice", "RiskPips", "TP1", "TP2", "TP3", "TP4", "ExitTime", "HitTP", "IsClosed", "Result");

   datetime chartTime[];
   double chartHigh[], chartLow[];
   ArraySetAsSeries(chartTime, false);
   ArraySetAsSeries(chartHigh, false);
   ArraySetAsSeries(chartLow, false);

   int copied = CopyTime(_Symbol, _Period, 0, 30000, chartTime);
   CopyHigh(_Symbol, _Period, 0, 30000, chartHigh);
   CopyLow(_Symbol, _Period, 0, 30000, chartLow);
   if(copied < 10) { FileClose(fileHandle); return; }

   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;
   int exportedCount = 0;

   for(int b = 0; b < g_boxCount; b++)
   {
      string role = "Flag";
      for(int tg = 0; tg < ArraySize(g_drawnBoxes[b].rsTags); tg++)
      {
         if(g_drawnBoxes[b].rsTags[tg] == "OInner") { role = "OInner"; break; }
         if(g_drawnBoxes[b].rsTags[tg] == "RS")     { role = "RS";     break; }
         if(g_drawnBoxes[b].rsTags[tg] == "LS")     { role = "LS";     break; }
         if(StringFind(g_drawnBoxes[b].rsTags[tg], "S-") == 0) { role = g_drawnBoxes[b].rsTags[tg]; break; }
      }

      bool isBull = true;
      double entryPrice = 0;
      double slPrice = 0;

      if(role == "OInner")
      {
         double pivotP = 0;
         datetime closestPivotTime = 0;
         bool pivotIsHigh = false;

         for(int ip = 0; ip < g_indepCount; ip++)
         {
            if(g_indepPivots[ip].time <= g_drawnBoxes[b].t1 + 60)
            {
               if(g_indepPivots[ip].time > closestPivotTime)
               {
                  closestPivotTime = g_indepPivots[ip].time;
                  pivotP = g_indepPivots[ip].price;
                  pivotIsHigh = g_indepPivots[ip].isHigh;
               }
            }
         }

         if(pivotP == 0)
         {
            pivotIsHigh = !g_drawnBoxes[b].isOInnerBull;
            pivotP = pivotIsHigh ? g_drawnBoxes[b].top : g_drawnBoxes[b].bottom;
         }

         if(pivotIsHigh)
         {
            isBull = false;
            entryPrice = g_drawnBoxes[b].bottom;
            slPrice = pivotP + 2 * pipSize;
         }
         else
         {
            isBull = true;
            entryPrice = g_drawnBoxes[b].top;
            slPrice = pivotP - 2 * pipSize;
         }
      }
      else
      {
         isBull = g_drawnBoxes[b].isBullish;
         if(g_drawnBoxes[b].isPreIP) isBull = g_drawnBoxes[b].isLSBull;
         else if(g_drawnBoxes[b].isBOFlag) isBull = g_drawnBoxes[b].isRSBull;
         else if(g_drawnBoxes[b].isSwap) isBull = g_drawnBoxes[b].isSwapBull;

         if(isBull)
         {
            entryPrice = g_drawnBoxes[b].top;
            slPrice = g_drawnBoxes[b].bottom - InpRSPipBuffer * pipSize;
         }
         else
         {
            entryPrice = g_drawnBoxes[b].bottom;
            slPrice = g_drawnBoxes[b].top + InpRSPipBuffer * pipSize;
         }
      }

      double risk = MathAbs(entryPrice - slPrice);
      if(risk <= 0) continue;

      int boxEndIdx = -1;
      for(int i = 0; i < copied; i++)
      {
         if(chartTime[i] >= g_drawnBoxes[b].t1) { boxEndIdx = i; break; }
      }
      if(boxEndIdx < 0) continue;

      int entryBar = -1;
      bool hasDeparted = false;

      for(int k = boxEndIdx + 1; k < copied; k++)
      {
         if(!hasDeparted)
         {
            if(isBull && chartHigh[k] > g_drawnBoxes[b].top + 1 * pipSize) hasDeparted = true;
            else if(!isBull && chartLow[k] < g_drawnBoxes[b].bottom - 1 * pipSize) hasDeparted = true;
            else if(k > boxEndIdx + 2) hasDeparted = true;
         }

         if(hasDeparted)
         {
            if(isBull)
            {
               if(chartLow[k] <= g_drawnBoxes[b].top && chartHigh[k] >= g_drawnBoxes[b].bottom)
               {
                  entryBar = k;
                  break;
               }
            }
            else
            {
               if(chartHigh[k] >= g_drawnBoxes[b].bottom && chartLow[k] <= g_drawnBoxes[b].top)
               {
                  entryBar = k;
                  break;
               }
            }
         }
      }

      double tp1 = isBull ? (entryPrice + 1.0 * risk) : (entryPrice - 1.0 * risk);
      double tp2 = isBull ? (entryPrice + 2.0 * risk) : (entryPrice - 2.0 * risk);
      double tp3 = isBull ? (entryPrice + 3.0 * risk) : (entryPrice - 3.0 * risk);
      double tp4 = isBull ? (entryPrice + 4.0 * risk) : (entryPrice - 4.0 * risk);

      datetime entryTime = 0;
      datetime exitTime  = chartTime[copied - 1];
      int      hitTP     = 0;
      bool     isClosed  = false;
      string   resText   = "PENDING";

      if(entryBar >= 0)
      {
         entryTime = chartTime[entryBar];

         for(int k = entryBar + 1; k < copied; k++)
         {
            if(isBull)
            {
               if(chartLow[k] <= slPrice)
               {
                  isClosed = true;
                  exitTime = chartTime[k];
                  break;
               }
               if(chartHigh[k] >= tp4) { hitTP = 4; isClosed = true; exitTime = chartTime[k]; break; }
               else if(chartHigh[k] >= tp3 && hitTP < 3) { hitTP = 3; }
               else if(chartHigh[k] >= tp2 && hitTP < 2) { hitTP = 2; }
               else if(chartHigh[k] >= tp1 && hitTP < 1) { hitTP = 1; }
            }
            else
            {
               if(chartHigh[k] >= slPrice)
               {
                  isClosed = true;
                  exitTime = chartTime[k];
                  break;
               }
               if(chartLow[k] <= tp4) { hitTP = 4; isClosed = true; exitTime = chartTime[k]; break; }
               else if(chartLow[k] <= tp3 && hitTP < 3) { hitTP = 3; }
               else if(chartLow[k] <= tp2 && hitTP < 2) { hitTP = 2; }
               else if(chartLow[k] <= tp1 && hitTP < 1) { hitTP = 1; }
            }
         }

         if(hitTP == 4)      resText = "WIN 1:4";
         else if(hitTP == 3) resText = "WIN 1:3";
         else if(hitTP == 2) resText = "WIN 1:2";
         else if(hitTP == 1) resText = "WIN 1:1";
         else if(isClosed)   resText = "LOSS";
         else                resText = "OPEN";
      }

      FileWrite(fileHandle,
                g_drawnBoxes[b].boxName,
                g_drawnBoxes[b].tfTag,
                role,
                (isBull ? "BUY" : "SELL"),
                TimeToString(g_drawnBoxes[b].t1),
                TimeToString(g_drawnBoxes[b].t2),
                DoubleToString(g_drawnBoxes[b].top, _Digits),
                DoubleToString(g_drawnBoxes[b].bottom, _Digits),
                (entryTime > 0 ? TimeToString(entryTime) : "-"),
                DoubleToString(entryPrice, _Digits),
                DoubleToString(slPrice, _Digits),
                DoubleToString(risk / pipSize, 1),
                DoubleToString(tp1, _Digits),
                DoubleToString(tp2, _Digits),
                DoubleToString(tp3, _Digits),
                DoubleToString(tp4, _Digits),
                TimeToString(exitTime),
                IntegerToString(hitTP),
                (isClosed ? "TRUE" : "FALSE"),
                resText);
      exportedCount++;
   }

   FileClose(fileHandle);
   Print("📁 تعداد ", exportedCount, " موقعیت معاملاتی با موفقیت در فایل MQL5/Files/flag_trades_export.csv ذخیره شد.");
}

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   ApplyProChartTheme();

   ChartSetInteger(0, CHART_EVENT_OBJECT_CREATE, true);
   ChartSetInteger(0, CHART_EVENT_OBJECT_DELETE, true);

   ObjectsDeleteAll(0, "FLAG_");
   ChartRedraw(0);
   IndicatorSetString(INDICATOR_SHORTNAME, "Flag v39.00 (3-Pivot Inspector)");
   Print("🎯 Flag v39 آماده است: روی هر باکسی کلیک کنید، اطلاعات کامل ۳ پیووت قبل و ۳ پیووت بعد در تب Experts چاپ می‌شود.");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                       |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, "FLAG_");
   ChartRedraw(0);
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

   //--- Only recalculate on a new bar or initial load to prevent chart flickering and high CPU usage
   static datetime lastBarTime = 0;
   datetime currentBarTime = time[rates_total - 1];
   if(prev_calculated > 0 && currentBarTime == lastBarTime)
   {
      return rates_total;
   }
   lastBarTime = currentBarTime;

   ApplyProChartTheme();

   ObjectsDeleteAll(0, "FLAG_BOX_");
   ObjectsDeleteAll(0, "FLAG_LBL_");
   ObjectsDeleteAll(0, "FLAG_IP_");
   ObjectsDeleteAll(0, "FLAG_RS_");
   ObjectsDeleteAll(0, "FLAG_SWAP_");
   ObjectsDeleteAll(0, "FLAG_STRUCT_");
   ObjectsDeleteAll(0, "FLAG_PIVOT_");
   ObjectsDeleteAll(0, "FLAG_ORIGIN_");

   ArrayResize(g_drawnBoxes, 0);
   g_boxCount = 0;
   ArrayResize(g_indepPivots, 0);
   g_indepCount = 0;

   ENUM_TIMEFRAMES tfArr[7]  = {InpTF1, InpTF2, InpTF3, InpTF4, InpTF5, InpTF6, InpTF7};
   bool            useArr[7] = {InpUseTF1, InpUseTF2, InpUseTF3, InpUseTF4, InpUseTF5, InpUseTF6, InpUseTF7};
   color           tfColorArr[7] = {InpColorTF1, InpColorTF2, InpColorTF3, InpColorTF4, InpColorTF5, InpColorTF6, InpColorTF7};
   int             daysBackArr[7] = {0, 0, 0, 0, InpM15DaysBack, InpM5DaysBack, InpM1DaysBack};

   for(int s = 0; s < 7; s++)
   {
      if(!useArr[s]) continue;

      ENUM_TIMEFRAMES currentTF = tfArr[s];
      color currentColor = tfColorArr[s];
      int daysBack = daysBackArr[s];

      ProcessTF(currentTF, InpSwingBars, currentColor, time, high, low, rates_total, daysBack);
   }

   //--- Process and draw RS Breakout Lines directly from LS Launch Boxes
   ProcessRSLinesFromLSBoxes(time, high, low, rates_total);

   //--- Process and tag First Post-IP Nodes as OInner
   ProcessOInnerBoxes();

   //--- Process and draw Universal Box Swap Lines and Reaction Boxes
   ProcessUniversalSwapLines(time, high, low, rates_total);

   //--- Render Final Filtered Boxes with RS Multi-Tag Labels
   RenderFinalBoxes();

   //--- Render Final Merged Independent Pivot Markers (No Overlapping)
   RenderFinalIndependentPivots();

   //--- ذخیره خودکار کل اطلاعات معاملات ۲ روز در فایل CSV برای آنالیزور پایتون
   ExportAllTradesToCSV();

   //--- بازنشانی هایلایت و ستاپ معامله برای باکس انتخابی در صورت وجود
   if(g_selectedBoxName != "")
   {
      for(int b = 0; b < g_boxCount; b++)
      {
         if(g_drawnBoxes[b].boxName == g_selectedBoxName)
         {
            ObjectSetInteger(0, g_selectedBoxName, OBJPROP_COLOR, clrGold);
            ObjectSetInteger(0, g_selectedBoxName, OBJPROP_WIDTH, 3);
            ObjectSetInteger(0, g_selectedBoxName, OBJPROP_STYLE, STYLE_SOLID);
            ObjectSetInteger(0, g_selectedBoxName, OBJPROP_FILL,  false);
            ShowTradeSetupForBox(b);
            break;
         }
      }
   }

   ChartRedraw(0);
   return rates_total;
}

// Global variables to track highlighted box state
string g_selectedBoxName    = "";
string g_selectedExtBoxName = "";
color  g_origBoxColor       = clrNONE;
int    g_origBoxWidth       = 1;
ENUM_LINE_STYLE g_origBoxStyle = STYLE_SOLID;

//+------------------------------------------------------------------+
//| Clear Box Highlight and Restore Original Styles                  |
//+------------------------------------------------------------------+
void ClearBoxHighlight()
{
   ObjectsDeleteAll(0, "FLAG_CLICK_TRADE_");
   ObjectsDeleteAll(0, "FLAG_TRADE_");

   if(g_selectedBoxName != "" && ObjectFind(0, g_selectedBoxName) >= 0)
   {
      ObjectSetInteger(0, g_selectedBoxName, OBJPROP_COLOR, g_origBoxColor);
      ObjectSetInteger(0, g_selectedBoxName, OBJPROP_WIDTH, g_origBoxWidth);
      ObjectSetInteger(0, g_selectedBoxName, OBJPROP_STYLE, g_origBoxStyle);
      ObjectSetInteger(0, g_selectedBoxName, OBJPROP_FILL,  false);
      ObjectSetInteger(0, g_selectedBoxName, OBJPROP_BACK,  false);
   }
   if(g_selectedExtBoxName != "" && ObjectFind(0, g_selectedExtBoxName) >= 0)
   {
      ObjectSetInteger(0, g_selectedExtBoxName, OBJPROP_FILL, false);
      ObjectSetInteger(0, g_selectedExtBoxName, OBJPROP_BACK, false);
      ObjectSetInteger(0, g_selectedExtBoxName, OBJPROP_WIDTH, InpSwapBoxWidth);
   }
   g_selectedBoxName = "";
   g_selectedExtBoxName = "";
   Comment("");
}

//+------------------------------------------------------------------+
//| Highlight Box on Click with Glowing Illumination & Fill          |
//+------------------------------------------------------------------+
void HighlightBox(int boxIdx)
{
   if(boxIdx < 0 || boxIdx >= g_boxCount) return;

   string boxName = g_drawnBoxes[boxIdx].boxName;
   if(boxName == g_selectedBoxName)
   {
      // کلیک مجدد روی همان باکس -> خاموش کردن هایلایت و ستاپ معامله
      ClearBoxHighlight();
      ChartRedraw(0);
      return;
   }

   // پاکسازی هایلایت قبلی
   ClearBoxHighlight();

   if(ObjectFind(0, boxName) >= 0)
   {
      g_selectedBoxName = boxName;
      g_origBoxColor    = (color)ObjectGetInteger(0, boxName, OBJPROP_COLOR);
      g_origBoxWidth    = (int)ObjectGetInteger(0, boxName, OBJPROP_WIDTH);
      g_origBoxStyle    = (ENUM_LINE_STYLE)ObjectGetInteger(0, boxName, OBJPROP_STYLE);

      // روشن و طلایی کردن خطوط کادر باکس بدون تغییر پس‌زمینه
      ObjectSetInteger(0, boxName, OBJPROP_COLOR, clrGold);
      ObjectSetInteger(0, boxName, OBJPROP_WIDTH, 3);
      ObjectSetInteger(0, boxName, OBJPROP_STYLE, STYLE_SOLID);
      ObjectSetInteger(0, boxName, OBJPROP_FILL,  false);
      ObjectSetInteger(0, boxName, OBJPROP_BACK,  false);

      // هایلایت کردن باکس امتدادیافته متناظر به رنگ طلایی
      string extBoxName = "FLAG_SWAP_EXTBOX_" + g_drawnBoxes[boxIdx].tfTag + "_" + IntegerToString((int)g_drawnBoxes[boxIdx].t1);
      if(ObjectFind(0, extBoxName) >= 0)
      {
         g_selectedExtBoxName = extBoxName;
         ObjectSetInteger(0, extBoxName, OBJPROP_COLOR, clrGold);
         ObjectSetInteger(0, extBoxName, OBJPROP_WIDTH, 2);
         ObjectSetInteger(0, extBoxName, OBJPROP_FILL,  false);
         ObjectSetInteger(0, extBoxName, OBJPROP_BACK,  false);
      }

      // نمایش ستاپ معامله در گذشته فقط برای همین باکس انتخاب‌شده
      ShowTradeSetupForBox(boxIdx);

      string info = "⚡ Box Selected: " + g_drawnBoxes[boxIdx].tfTag +
                    " | Top: " + DoubleToString(g_drawnBoxes[boxIdx].top, _Digits) +
                    " | Bottom: " + DoubleToString(g_drawnBoxes[boxIdx].bottom, _Digits) +
                    " | Start: " + TimeToString(g_drawnBoxes[boxIdx].t1);
      Comment(info);
   }

   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| ChartEvent: Handle User Click on Box                             |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
{
   if(id == CHARTEVENT_CLICK)
   {
      static ulong lastClickMs = 0;
      ulong now = GetTickCount64();
      if(now - lastClickMs < 200) return;
      lastClickMs = now;

      int x = (int)lparam;
      int y = (int)dparam;

      datetime dt;
      double price;
      int window = 0;

      if(ChartXYToTimePrice(0, x, y, window, dt, price))
      {
         int boxIdx = FindNearestBox(dt, price);
         if(boxIdx >= 0)
         {
            HighlightBox(boxIdx);
            PrintBoxRemovalInfo(boxIdx);
         }
         else
         {
            ClearBoxHighlight();
            ChartRedraw(0);
         }
      }
   }
}
//+------------------------------------------------------------------+
