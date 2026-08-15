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
input bool             InpUseTF3  = false;
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
input int              InpLineWidth   = 2;           // ضخامت خط باکس‌ها
input bool             InpShowLabel   = true;        // نمایش برچسب تایم‌فریم

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
//| Helper: Draw Hollow Box on Chart                                 |
//+------------------------------------------------------------------+
void DrawHollowBox(string name, datetime t1, double top, datetime t2, double bottom,
                   color clr, int width)
{
   if(ObjectFind(0, name) >= 0) ObjectDelete(0, name);
   ObjectCreate(0, name, OBJ_RECTANGLE, 0, t1, top, t2, bottom);
   ObjectSetInteger(0, name, OBJPROP_COLOR,      clr);
   ObjectSetInteger(0, name, OBJPROP_WIDTH,      width);
   ObjectSetInteger(0, name, OBJPROP_FILL,       false);
   ObjectSetInteger(0, name, OBJPROP_BACK,       false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_RAY_RIGHT,  false);
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
         // اگر سقف بعدی پایین‌تر از P1 باشد (چرخش به روند نزولی)، این یال موج ریزش اولیه است نه پرچم!
         if(nextH > 0 && nextH < p1.price)
            return false;

         return true;
      }
   }
   // 2. اصلاح صعودی در روند نزولی: Rally (Low -> High)
   else if(!p1.isHigh && p2.isHigh)
   {
      if(prevH > 0 && p2.price < prevH)
      {
         // اگر کف بعدی بالاتر از P1 باشد (چرخش به روند صعودی)، این یال موج صعود اولیه است نه پرچم!
         if(nextL > 0 && nextL > p1.price)
            return false;

         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Process Timeframe Swings & Draw Flag Boxes                       |
//+------------------------------------------------------------------+
void ProcessTF(ENUM_TIMEFRAMES tf, int sBars, color clr,
               const datetime &chartTime[], const double &chartHigh[], const double &chartLow[],
               int ratesTotal, int daysBack)
{
   SPivot pivots[];
   if(!BuildAlternatingPivots(tf, sBars, InpMaxBarsTF, pivots)) return;

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

   for(int i = 0; i < count - 1; i++)
   {
      SPivot p1 = pivots[i];
      SPivot p2 = pivots[i + 1];

      if(daysBack > 0 && p1.time < limitTime)
         continue;

      if(!IsValidFlagLeg(i, pivots, count))
         continue;

      double boxTop    = MathMax(p1.price, p2.price);
      double boxBottom = MathMin(p1.price, p2.price);

      int idx1 = FindBarIndex(chartTime, ratesTotal, p1.time);
      int idx2 = FindBarIndex(chartTime, ratesTotal, p2.time);
      if(idx1 < 0 || idx2 < 0) continue;

      int idxStart = MathMin(idx1, idx2);
      int idxEnd   = MathMax(idx1, idx2);

      int leftIdx = idxStart;

      // Forward extension: extend from end of swing until breakout
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
      if(rightIdx <= idxStart && idxStart < ratesTotal - 1) rightIdx = idxStart + 1;
      if(rightIdx < ratesTotal - 1) rightIdx++;

      datetime t1 = chartTime[leftIdx];
      datetime t2 = chartTime[rightIdx];

      string boxKey = IntegerToString((int)p1.time) + "_" + IntegerToString((int)p2.time);
      string boxName = "FLAG_BOX_" + tfTag + "_" + boxKey;
      DrawHollowBox(boxName, t1, boxTop, t2, boxBottom, clr, InpLineWidth);

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
         if(ObjectFind(0, lblName) >= 0) ObjectDelete(0, lblName);
         ObjectCreate(0, lblName, OBJ_TEXT, 0, labelTime, labelPrice);
         ObjectSetString(0, lblName, OBJPROP_TEXT, tfSymbol);
         ObjectSetInteger(0, lblName, OBJPROP_COLOR, clr);
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
