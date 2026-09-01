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
input group "=== Timeframes to Display ==="
input ENUM_TIMEFRAMES InpTF1      = PERIOD_D1;
input bool             InpUseTF1  = false;
input color            InpColorTF1 = clrMagenta;

input ENUM_TIMEFRAMES InpTF2      = PERIOD_W1;
input bool             InpUseTF2  = false;
input color            InpColorTF2 = clrDodgerBlue;

input ENUM_TIMEFRAMES InpTF3      = PERIOD_H4;
input bool             InpUseTF3  = true;           // چهارساعته (H4) فعال شد
input color            InpColorTF3 = clrWhite;

input ENUM_TIMEFRAMES InpTF4      = PERIOD_H1;
input bool             InpUseTF4  = true;          // فقط H1 به صورت پیش‌فرض فعال است
input color            InpColorTF4 = clrYellow;

input ENUM_TIMEFRAMES InpTF5      = PERIOD_M15;
input bool             InpUseTF5  = false;
input color            InpColorTF5 = clrLime;
input int              InpM15DaysBack = 50;

input ENUM_TIMEFRAMES InpTF6      = PERIOD_M5;
input bool             InpUseTF6  = false;
input color            InpColorTF6 = clrAqua;
input int              InpM5DaysBack = 30;

input ENUM_TIMEFRAMES InpTF7      = PERIOD_M1;
input bool             InpUseTF7  = false;
input color            InpColorTF7 = clrYellow;
input int              InpM1DaysBack = 10;

input group "=== Structure Calculation (matches MarketStructure_v2) ==="
input int              InpSwingBars   = 6;           // عمق امواج ماژور (Swing Bars)
input int              InpMaxBarsTF   = 3000;        // حداکثر کندل‌های محاسبه (Max Bars)

input group "=== Visuals ==="
input int              InpLineWidth   = 1;           // ضخامت خط باکس‌ها (1 = نازک و ظریف)
input bool             InpShowLabel   = true;        // نمایش برچسب تایم‌فریم

input group "=== Independent Pivots (پیووت‌های مستقل) ==="
input bool             InpShowIndependentPivots = true;        // نمایش پیووت‌های مستقل (چرخش ساختار)
input color            InpIndepColorHigh        = clrMagenta;    // رنگ سقف مستقل
input color            InpIndepColorLow         = clrAqua;       // رنگ کف مستقل
input int              InpIndepMarkCode         = 159;          // کد علامت (159 = دایره، 168 = دایره باز)
input int              InpIndepMarkWidth        = 3;            // اندازه علامت پیووت مستقل
input bool             InpIndepShowLabel        = true;         // نمایش برچسب IP روی چارت

input group "=== Pre-IP Box (باکس ماقبل پیووت مستقل) ==="
input bool             InpHighlightPreIP        = true;         // مشخص کردن باکس قبل از پیووت مستقل
input color            InpPreIPColor            = clrGold;      // رنگ اختصاصی باکس ماقبل پیووت مستقل
input int              InpPreIPWidth            = 2;            // ضخامت باکس ماقبل پیووت مستقل
input bool             InpPreIPShowLabel        = true;         // نمایش برچسب Pre-IP روی باکس

enum ENUM_LABEL_STYLE
{
   LABEL_COMPACT,   // کوتاه و تمیز (مانند M15➔H1)
   LABEL_FULL,      // متن کامل
   LABEL_TOOLTIP    // فقط هنگام بردن موس روی خط (چارت کاملاً خلوت و بدون متن)
};

input group "=== Multi-Timeframe Origin Lines (خطوط پیووت منشأ چندگانه) ==="
input bool              InpEnableOriginLines     = true;         // فعال‌سازی رسم خطوط پیووت منشأ
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

input group "=== Chart Display Settings ==="
input bool             InpHideGrid    = true;        // حذف گرید از چارت
input bool             InpHideVolumes = true;        // حذف نمودار حجم

// Storage for drawn boxes and pivots
struct SBoxInfo
{
   string   boxName;
   int      swingIdx;
   datetime t1;
   datetime t2;
   double   top;
   double   bottom;
};

SPivot   g_pivotsH1[];
int      g_pivotCountH1 = 0;
SBoxInfo g_drawnBoxes[];
int      g_boxCount = 0;
int      g_clickCounter = 0;

//+------------------------------------------------------------------+
//| Get distinct Line Style per Timeframe                            |
//+------------------------------------------------------------------+
ENUM_LINE_STYLE GetTFLineStyle(ENUM_TIMEFRAMES tf)
{
   switch(tf)
   {
      case PERIOD_D1:  return STYLE_SOLID;       // روزانه: خط ممتد
      case PERIOD_W1:  return STYLE_SOLID;       // هفتگی: خط ممتد
      case PERIOD_H4:  return STYLE_SOLID;       // چهارساعته: خط ممتد
      case PERIOD_H1:  return STYLE_SOLID;       // یک‌ساعته: خط ممتد
      case PERIOD_M15: return STYLE_DASH;        // ۱۵ دقیقه: خط‌چین
      case PERIOD_M5:  return STYLE_DOT;         // ۵ دقیقه: نقطه‌چین
      case PERIOD_M1:  return STYLE_DASHDOT;     // ۱ دقیقه: خط و نقطه
      default:         return STYLE_SOLID;
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
   ArrayResize(isPreIPBox, count);
   ArrayInitialize(isPreIPBox, false);

   if(InpHighlightPreIP)
   {
      for(int p = 0; p < count; p++)
      {
         if(!pivotInBox[p]) // این یک پیووت مستقل است
         {
            // جستجوی نزدیک‌ترین باکس قبل از این پیووت
            for(int j = p - 1; j >= 0; j--)
            {
               if(isLegBox[j])
               {
                  isPreIPBox[j] = true;
                  break; // فقط آخرین باکس قبل از پیووت مستقل
               }
            }
         }
      }
   }

   //--- مرحله ۳: علامت‌گذاری اختصاصی پیووت‌های مستقل (پیووت‌هایی که هیچ باکسی ندارند)
   if(InpShowIndependentPivots)
   {
      for(int p = 0; p < count; p++)
      {
         if(daysBack > 0 && pivots[p].time < limitTime)
            continue;

         // اگر این پیووت در هیچ باکسی قرار نگرفته باشد -> پیووت مستقل است
         if(!pivotInBox[p])
         {
            string ipName = "FLAG_IP_" + tfTag + "_" + IntegerToString((int)pivots[p].time);
            color ipColor = pivots[p].isHigh ? InpIndepColorHigh : InpIndepColorLow;
            DrawIndependentPivot(ipName, pivots[p].time, pivots[p].price, pivots[p].isHigh, ipColor, tfSymbol);
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
      
      color drawClr = clr;
      int drawWidth = InpLineWidth;
      if(isPreIPBox[i] && InpHighlightPreIP)
      {
         drawClr = InpPreIPColor;
         drawWidth = InpPreIPWidth;
      }

      ENUM_LINE_STYLE tfStyle = GetTFLineStyle(tf);
      DrawHollowBox(boxName, t1, boxTop, t2, boxBottom, drawClr, drawWidth, tfStyle);

      // Register box for click inspection
      if(tf == PERIOD_H1)
      {
         ArrayResize(g_drawnBoxes, g_boxCount + 1);
         g_drawnBoxes[g_boxCount].boxName  = boxName;
         g_drawnBoxes[g_boxCount].swingIdx = i;
         g_drawnBoxes[g_boxCount].t1       = t1;
         g_drawnBoxes[g_boxCount].t2       = t2;
         g_drawnBoxes[g_boxCount].top      = boxTop;
         g_drawnBoxes[g_boxCount].bottom   = boxBottom;
         g_boxCount++;
      }

      // Draw Label directly
      if(InpShowLabel)
      {
         double labelPrice = boxTop + (boxTop - boxBottom) * 0.08;
         datetime labelTime = (datetime)((t1 + t2) / 2);
         string lblName = "FLAG_LBL_" + tfTag + "_" + boxKey;
         string lblText = (isPreIPBox[i] && InpHighlightPreIP && InpPreIPShowLabel) ? ("Pre-IP " + tfSymbol) : tfSymbol;
         if(ObjectFind(0, lblName) >= 0) ObjectDelete(0, lblName);
         ObjectCreate(0, lblName, OBJ_TEXT, 0, labelTime, labelPrice);
         ObjectSetString(0, lblName, OBJPROP_TEXT, lblText);
         ObjectSetInteger(0, lblName, OBJPROP_COLOR, drawClr);
         ObjectSetInteger(0, lblName, OBJPROP_FONTSIZE, 9);
         ObjectSetInteger(0, lblName, OBJPROP_ANCHOR, ANCHOR_CENTER);
      }
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

   // Highlight clicked box in Magenta to show it was selected
   ObjectSetInteger(0, g_drawnBoxes[bIdx].boxName, OBJPROP_COLOR, clrMagenta);
   ObjectSetInteger(0, g_drawnBoxes[bIdx].boxName, OBJPROP_WIDTH, 4);

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
//| Find Nearest Drawn Box to Click                                  |
//+------------------------------------------------------------------+
int FindNearestBox(datetime clickTime, double clickPrice)
{
   if(g_boxCount <= 0) return -1;

   int bestIdx = -1;
   double minDistance = DBL_MAX;

   for(int i = 0; i < g_boxCount; i++)
   {
      datetime t1 = g_drawnBoxes[i].t1;
      datetime t2 = g_drawnBoxes[i].t2;
      double top = g_drawnBoxes[i].top;
      double bottom = g_drawnBoxes[i].bottom;

      if(clickTime >= t1 - PeriodSeconds(_Period)*3 && clickTime <= t2 + PeriodSeconds(_Period)*3)
      {
         double midPrice = (top + bottom) / 2.0;
         double dist = MathAbs(clickPrice - midPrice);
         if(dist < minDistance)
         {
            minDistance = dist;
            bestIdx = i;
         }
      }
   }

   return bestIdx;
}

//+------------------------------------------------------------------+
//| Helper: Process Origin Pivot Breakout Lines for a TF Pair        |
//+------------------------------------------------------------------+
void ProcessOriginFromPivots(const SPivot &targetPivots[], ENUM_TIMEFRAMES targetTF,
                             const SPivot &sourcePivots[], ENUM_TIMEFRAMES sourceTF,
                             const datetime &chartTime[], const double &chartHigh[], const double &chartLow[],
                             int ratesTotal, int daysBack)
{
   int targetCount = ArraySize(targetPivots);
   int sourceCount = ArraySize(sourcePivots);
   if(targetCount < 2 || sourceCount < 2) return;

   // تشخیص پیووت‌های مستقل تایم هدف
   bool targetPivotInBox[];
   ArrayResize(targetPivotInBox, targetCount);
   ArrayInitialize(targetPivotInBox, false);
   for(int i = 0; i < targetCount - 1; i++)
   {
      if(IsValidFlagLeg(i, targetPivots, targetCount))
      {
         targetPivotInBox[i] = true;
         targetPivotInBox[i + 1] = true;
      }
   }

   // تشخیص پیووت‌های مستقل تایم منشأ
   bool sourcePivotInBox[];
   ArrayResize(sourcePivotInBox, sourceCount);
   ArrayInitialize(sourcePivotInBox, false);
   for(int i = 0; i < sourceCount - 1; i++)
   {
      if(IsValidFlagLeg(i, sourcePivots, sourceCount))
      {
         sourcePivotInBox[i] = true;
         sourcePivotInBox[i + 1] = true;
      }
   }

   datetime limitTime = 0;
   if(daysBack > 0)
      limitTime = TimeCurrent() - daysBack * 24 * 60 * 60;

   string targetTFStr = TFName(targetTF);
   string sourceTFStr = TFName(sourceTF);
   ENUM_LINE_STYLE sourceStyle = GetTFLineStyle(sourceTF);

   for(int p = 0; p < targetCount; p++)
   {
      if(daysBack > 0 && targetPivots[p].time < limitTime)
         continue;

      // فقط پیووت‌های مستقل تایم هدف
      if(targetPivotInBox[p])
         continue;

      bool targetIsHigh = targetPivots[p].isHigh;
      datetime targetTime = targetPivots[p].time;

      int foundSourceIdx = -1;
      for(int s = sourceCount - 1; s >= 0; s--)
      {
         if(sourcePivots[s].time < targetTime)
         {
            if(sourcePivots[s].isHigh != targetIsHigh)
            {
               if(!InpOriginRequireIndep || !sourcePivotInBox[s])
               {
                  foundSourceIdx = s;
                  break;
               }
            }
         }
      }

      if(foundSourceIdx < 0)
         continue;

      SPivot originP = sourcePivots[foundSourceIdx];
      datetime originTime = originP.time;
      double originPrice = originP.price;
      bool originIsHigh = originP.isHigh;

      int startIdx = FindBarIndex(chartTime, ratesTotal, originTime);
      if(startIdx < 0) continue;

      int breakIdx = ratesTotal - 1;
      for(int k = startIdx + 1; k < ratesTotal; k++)
      {
         if(originIsHigh)
         {
            if(chartHigh[k] > originPrice)
            {
               breakIdx = k;
               break;
            }
         }
         else
         {
            if(chartLow[k] < originPrice)
            {
               breakIdx = k;
               break;
            }
         }
      }

      datetime endTime = chartTime[breakIdx];
      string lineName = "FLAG_ORIGIN_" + targetTFStr + "_" + sourceTFStr + "_" + IntegerToString((int)originTime);
      color lineColor = originIsHigh ? InpOriginColorHigh : InpOriginColorLow;

      if(ObjectFind(0, lineName) >= 0) ObjectDelete(0, lineName);
      ObjectCreate(0, lineName, OBJ_TREND, 0, originTime, originPrice, endTime, originPrice);
      ObjectSetInteger(0, lineName, OBJPROP_COLOR, lineColor);
      ObjectSetInteger(0, lineName, OBJPROP_STYLE, sourceStyle);
      ObjectSetInteger(0, lineName, OBJPROP_WIDTH, InpOriginLineWidth);
      ObjectSetInteger(0, lineName, OBJPROP_RAY_RIGHT, false);
      ObjectSetInteger(0, lineName, OBJPROP_SELECTABLE, false);

      string tooltip = "Origin " + sourceTFStr + (originIsHigh ? " High" : " Low") + " -> Target IP " + targetTFStr +
                       "\nPrice: " + DoubleToString(originPrice, _Digits) +
                       "\nTime: " + TimeToString(originTime);
      ObjectSetString(0, lineName, OBJPROP_TOOLTIP, tooltip);

      if(InpOriginLabelStyle != LABEL_TOOLTIP)
      {
         string lblName = lineName + "_LBL";
         string lblText = (InpOriginLabelStyle == LABEL_COMPACT) ? (sourceTFStr + "->" + targetTFStr) : ("Origin " + sourceTFStr + (originIsHigh ? " H" : " L") + " -> " + targetTFStr);
         
         if(ObjectFind(0, lblName) >= 0) ObjectDelete(0, lblName);
         // قرار دادن برچسب در انتهای سمت راست خط (endTime) تا با پیووت و خطوط دیگر تداخل نداشته باشد
         ObjectCreate(0, lblName, OBJ_TEXT, 0, endTime, originPrice);
         ObjectSetString(0, lblName, OBJPROP_TEXT, lblText);
         ObjectSetInteger(0, lblName, OBJPROP_COLOR, lineColor);
         ObjectSetInteger(0, lblName, OBJPROP_FONTSIZE, 7);
         ObjectSetInteger(0, lblName, OBJPROP_ANCHOR, (originIsHigh ? ANCHOR_LEFT_LOWER : ANCHOR_LEFT_UPPER));
         ObjectSetInteger(0, lblName, OBJPROP_SELECTABLE, false);
      }
   }
}

//+------------------------------------------------------------------+
//| Process Multi-Timeframe Origin Lines                             |
//+------------------------------------------------------------------+
void ProcessMultiOriginLines(const datetime &chartTime[], const double &chartHigh[], const double &chartLow[],
                             int ratesTotal, int daysBack)
{
   if(!InpEnableOriginLines) return;

   // کش کردن پیووت‌های تایم‌فریم‌های مورد نیاز
   SPivot pivotsD1[], pivotsH4[], pivotsH1[], pivotsM15[], pivotsM5[], pivotsM1[];

   if(InpTargetD1)
      BuildAlternatingPivots(PERIOD_D1, InpSwingBars, InpMaxBarsTF, pivotsD1);

   if(InpTargetH4)
      BuildAlternatingPivots(PERIOD_H4, InpSwingBars, InpMaxBarsTF, pivotsH4);

   if(InpTargetH1 || InpSourceH1)
      BuildAlternatingPivots(PERIOD_H1, InpSwingBars, InpMaxBarsTF, pivotsH1);

   if(InpSourceM15)
      BuildAlternatingPivots(PERIOD_M15, InpSwingBars, MathMax(InpMaxBarsTF, 15000), pivotsM15);

   if(InpSourceM5)
      BuildAlternatingPivots(PERIOD_M5, InpSwingBars, MathMax(InpMaxBarsTF, 20000), pivotsM5);

   if(InpSourceM1)
      BuildAlternatingPivots(PERIOD_M1, InpSwingBars, MathMax(InpMaxBarsTF, 30000), pivotsM1);

   // 1. پردازش منشأها برای پیووت‌های مستقل D1
   if(InpTargetD1)
   {
      if(InpSourceH1)  ProcessOriginFromPivots(pivotsD1, PERIOD_D1, pivotsH1,  PERIOD_H1,  chartTime, chartHigh, chartLow, ratesTotal, daysBack);
      if(InpSourceM15) ProcessOriginFromPivots(pivotsD1, PERIOD_D1, pivotsM15, PERIOD_M15, chartTime, chartHigh, chartLow, ratesTotal, daysBack);
      if(InpSourceM5)  ProcessOriginFromPivots(pivotsD1, PERIOD_D1, pivotsM5,  PERIOD_M5,  chartTime, chartHigh, chartLow, ratesTotal, daysBack);
      if(InpSourceM1)  ProcessOriginFromPivots(pivotsD1, PERIOD_D1, pivotsM1,  PERIOD_M1,  chartTime, chartHigh, chartLow, ratesTotal, daysBack);
   }

   // 2. پردازش منشأها برای پیووت‌های مستقل H4
   if(InpTargetH4)
   {
      if(InpSourceH1)  ProcessOriginFromPivots(pivotsH4, PERIOD_H4, pivotsH1,  PERIOD_H1,  chartTime, chartHigh, chartLow, ratesTotal, daysBack);
      if(InpSourceM15) ProcessOriginFromPivots(pivotsH4, PERIOD_H4, pivotsM15, PERIOD_M15, chartTime, chartHigh, chartLow, ratesTotal, daysBack);
      if(InpSourceM5)  ProcessOriginFromPivots(pivotsH4, PERIOD_H4, pivotsM5,  PERIOD_M5,  chartTime, chartHigh, chartLow, ratesTotal, daysBack);
      if(InpSourceM1)  ProcessOriginFromPivots(pivotsH4, PERIOD_H4, pivotsM1,  PERIOD_M1,  chartTime, chartHigh, chartLow, ratesTotal, daysBack);
   }

   // 3. پردازش منشأها برای پیووت‌های مستقل H1
   if(InpTargetH1)
   {
      if(InpSourceM15) ProcessOriginFromPivots(pivotsH1, PERIOD_H1, pivotsM15, PERIOD_M15, chartTime, chartHigh, chartLow, ratesTotal, daysBack);
      if(InpSourceM5)  ProcessOriginFromPivots(pivotsH1, PERIOD_H1, pivotsM5,  PERIOD_M5,  chartTime, chartHigh, chartLow, ratesTotal, daysBack);
      if(InpSourceM1)  ProcessOriginFromPivots(pivotsH1, PERIOD_H1, pivotsM1,  PERIOD_M1,  chartTime, chartHigh, chartLow, ratesTotal, daysBack);
   }
}

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   if(InpHideGrid)
      ChartSetInteger(0, CHART_SHOW_GRID, false);
   if(InpHideVolumes)
      ChartSetInteger(0, CHART_SHOW_VOLUMES, CHART_VOLUME_HIDE);

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

   if(InpHideGrid)
      ChartSetInteger(0, CHART_SHOW_GRID, false);
   if(InpHideVolumes)
      ChartSetInteger(0, CHART_SHOW_VOLUMES, CHART_VOLUME_HIDE);

   ObjectsDeleteAll(0, "FLAG_");
   ArrayResize(g_drawnBoxes, 0);
   g_boxCount = 0;

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

   //--- Process and draw Multi-Timeframe Origin Pivot Breakout Lines
   ProcessMultiOriginLines(time, high, low, rates_total, InpOriginDaysBack);

   ChartRedraw(0);
   return rates_total;
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
            PrintBoxRemovalInfo(boxIdx);
         }
      }
   }
}
//+------------------------------------------------------------------+
