//+------------------------------------------------------------------+
//| MarketStructure_v2.mq5                                           |
//| Clean Market Structure Indicator (Lines Only, No Labels/Dots)    |
//+------------------------------------------------------------------+
#property copyright "Market Structure v2"
#property link      ""
#property version   "35.00"
#property indicator_chart_window
#property indicator_buffers 2
#property indicator_plots   1

//--- Plot 1: ZigZag Structure Line (Color Section)
#property indicator_label1  "Structure Line"
#property indicator_type1   DRAW_COLOR_SECTION
#property indicator_color1  clrDodgerBlue, clrCrimson
#property indicator_style1  STYLE_SOLID
#property indicator_width1  2

#include <MarketStructureEngine.mqh>

//--- Inputs
input group "=== Chart Display Settings ==="
input bool   InpHideGrid          = true;          // حذف گرید از چارت (Hide Grid)
input bool   InpHideVolumes       = true;          // حذف نمودار حجم پایین چارت (Hide Volumes)

input group "=== Structure Calculation (matches Flag) ==="
input int    InpSwingBars         = 6;             // عمق امواج ماژور (Swing Bars - پیش‌فرض 6)
input int    InpMaxBars           = 3000;          // حداکثر کندل‌های محاسبه (Max Bars)

input group "=== Visuals ==="
input color  InpColorBullish      = clrDodgerBlue; // رنگ صعودی
input color  InpColorBearish      = clrCrimson;    // رنگ نزولی
input color  InpHighlightColor    = clrYellow;     // رنگ یال انتخاب‌شده با کلیک
input int    InpHighlightWidth    = 4;             // ضخامت یال زرد

//--- Buffers
double BufferLine[];
double BufferLineColor[];

// Global storage for current swings
SPivot g_swings[];
int    g_swingCount = 0;
int    g_clickCount = 0;

//--- Prefix for chart objects
const string OBJ_PREFIX = "MSv2_";

//+------------------------------------------------------------------+
//| Find Bar Index in non-series chartTime array                     |
//+------------------------------------------------------------------+
int FindChartBarIndex(const datetime &chartTime[], int ratesTotal, datetime t)
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
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   SetIndexBuffer(0, BufferLine,       INDICATOR_DATA);
   SetIndexBuffer(1, BufferLineColor,  INDICATOR_COLOR_INDEX);

   PlotIndexSetDouble(0, PLOT_EMPTY_VALUE, 0.0);
   PlotIndexSetDouble(1, PLOT_EMPTY_VALUE, 0.0);

   if(InpHideGrid)
      ChartSetInteger(0, CHART_SHOW_GRID, false);
   if(InpHideVolumes)
      ChartSetInteger(0, CHART_SHOW_VOLUMES, CHART_VOLUME_HIDE);

   ChartSetInteger(0, CHART_EVENT_OBJECT_CREATE, true);
   ChartSetInteger(0, CHART_EVENT_OBJECT_DELETE, true);

   ObjectsDeleteAll(0, OBJ_PREFIX);
   ChartRedraw(0);

   IndicatorSetString(INDICATOR_SHORTNAME, "MarketStructure v35.0 (Clean Lines)");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                       |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, OBJ_PREFIX);
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
   int sBars = MathMax(2, InpSwingBars);
   if(rates_total < sBars * 2 + 5)
      return 0;

   if(InpHideGrid)
      ChartSetInteger(0, CHART_SHOW_GRID, false);
   if(InpHideVolumes)
      ChartSetInteger(0, CHART_SHOW_VOLUMES, CHART_VOLUME_HIDE);

   //--- Clear Buffers
   ArrayInitialize(BufferLine, 0.0);
   ArrayInitialize(BufferLineColor, 0.0);

   SPivot pivots[];
   if(!BuildAlternatingPivots(_Period, sBars, InpMaxBars, pivots))
      return rates_total;

   int sCount = ArraySize(pivots);
   if(sCount < 2)
      return rates_total;

   // Store globally for click handler
   ArrayResize(g_swings, sCount);
   for(int i = 0; i < sCount; i++)
   {
      g_swings[i] = pivots[i];
      if(pivots[i].label == "HH" || pivots[i].label == "HL")
         g_swings[i].clr = InpColorBullish;
      else
         g_swings[i].clr = InpColorBearish;
   }
   g_swingCount = sCount;

   // Clear any leftover labels
   ObjectsDeleteAll(0, OBJ_PREFIX + "Lbl_");

   // Render Clean ZigZag Lines right on the chart bars
   for(int i = 0; i < sCount; i++)
   {
      int chartBar = FindChartBarIndex(time, rates_total, g_swings[i].time);
      if(chartBar < 0 || chartBar >= rates_total) continue;

      double pr = g_swings[i].price;

      int legColor = 0;
      if(i > 0)
         legColor = g_swings[i].isHigh ? 0 : 1;
      else
         legColor = g_swings[i].isHigh ? 1 : 0;

      BufferLine[chartBar]      = pr;
      BufferLineColor[chartBar] = legColor;
   }

   return rates_total;
}

//+------------------------------------------------------------------+
//| Find nearest swing leg to click                                  |
//+------------------------------------------------------------------+
int FindNearestSwingLeg(datetime clickTime, double clickPrice)
{
   if(g_swingCount < 2) return -1;

   int bestIdx = -1;
   double minDistance = DBL_MAX;

   for(int i = 0; i < g_swingCount - 1; i++)
   {
      datetime t1 = g_swings[i].time;
      datetime t2 = g_swings[i + 1].time;
      double   p1 = g_swings[i].price;
      double   p2 = g_swings[i + 1].price;

      datetime tStart = MathMin(t1, t2);
      datetime tEnd   = MathMax(t1, t2);

      if(clickTime >= tStart - PeriodSeconds(_Period)*3 && clickTime <= tEnd + PeriodSeconds(_Period)*3)
      {
         double expectedPrice = p1;
         if(t2 != t1)
         {
            double ratio = (double)(clickTime - t1) / (double)(t2 - t1);
            ratio = MathMax(0.0, MathMin(1.0, ratio));
            expectedPrice = p1 + ratio * (p2 - p1);
         }

         double dist = MathAbs(clickPrice - expectedPrice);
         if(dist < minDistance)
         {
            minDistance = dist;
            bestIdx = i;
         }
      }
   }

   if(bestIdx == -1)
   {
      for(int i = 0; i < g_swingCount - 1; i++)
      {
         datetime midTime = (datetime)((g_swings[i].time + g_swings[i + 1].time) / 2);
         double timeDiff = (double)MathAbs(clickTime - midTime);
         if(timeDiff < minDistance)
         {
            minDistance = timeDiff;
            bestIdx = i;
         }
      }
   }

   return bestIdx;
}

//+------------------------------------------------------------------+
//| Highlight clicked swing leg with Yellow Line & Print Diagnostics |
//+------------------------------------------------------------------+
void HighlightSwingLeg(int idx)
{
   if(idx < 0 || idx >= g_swingCount - 1) return;

   SPivot p1 = g_swings[idx];
   SPivot p2 = g_swings[idx + 1];

   g_clickCount++;
   string lineName = OBJ_PREFIX + "HIGHLIGHT_LEG";
   if(ObjectFind(0, lineName) >= 0)
      ObjectDelete(0, lineName);

   ObjectCreate(0, lineName, OBJ_TREND, 0, p1.time, p1.price, p2.time, p2.price);
   ObjectSetInteger(0, lineName, OBJPROP_COLOR,      InpHighlightColor);
   ObjectSetInteger(0, lineName, OBJPROP_WIDTH,      InpHighlightWidth);
   ObjectSetInteger(0, lineName, OBJPROP_STYLE,      STYLE_SOLID);
   ObjectSetInteger(0, lineName, OBJPROP_RAY_RIGHT,  false);
   ObjectSetInteger(0, lineName, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, lineName, OBJPROP_BACK,       false);

   string legType = (p1.isHigh ? "نزولی (Drop: " + p1.label + " -> " + p2.label + ")" : "صعودی (Rally: " + p1.label + " -> " + p2.label + ")");
   Print("══════════════════════════════════════════════════════════════════════");
   Print("🟡 [یال ماژور زرد انتخاب‌شده #", g_clickCount, "]");
   Print("📍 جهت یال: ", legType);
   Print("📌 شروع (P1): [", p1.label, "] = ", DoubleToString(p1.price, _Digits), " | زمان=", TimeToString(p1.time));
   Print("📌 پایان (P2): [", p2.label, "] = ", DoubleToString(p2.price, _Digits), " | زمان=", TimeToString(p2.time));
   
   Print("--- ⬅️ ۳ پیووت قبل ---");
   if(idx >= 1)
      Print("   ⬅️ ۱ پیووت قبل (P-1): [", g_swings[idx-1].label, "] = ", DoubleToString(g_swings[idx-1].price, _Digits), " | زمان=", TimeToString(g_swings[idx-1].time));
   if(idx >= 2)
      Print("   ⬅️ ۲ پیووت قبل (P-2): [", g_swings[idx-2].label, "] = ", DoubleToString(g_swings[idx-2].price, _Digits), " | زمان=", TimeToString(g_swings[idx-2].time));
   if(idx >= 3)
      Print("   ⬅️ ۳ پیووت قبل (P-3): [", g_swings[idx-3].label, "] = ", DoubleToString(g_swings[idx-3].price, _Digits), " | زمان=", TimeToString(g_swings[idx-3].time));

   Print("--- ➡️ ۳ پیووت بعد ---");
   if(idx + 2 < g_swingCount)
      Print("   ➡️ ۱ پیووت بعد از P2 (P+2): [", g_swings[idx+2].label, "] = ", DoubleToString(g_swings[idx+2].price, _Digits), " | زمان=", TimeToString(g_swings[idx+2].time));
   if(idx + 3 < g_swingCount)
      Print("   ➡️ ۲ پیووت بعد از P2 (P+3): [", g_swings[idx+3].label, "] = ", DoubleToString(g_swings[idx+3].price, _Digits), " | زمان=", TimeToString(g_swings[idx+3].time));
   if(idx + 4 < g_swingCount)
      Print("   ➡️ ۳ پیووت بعد از P2 (P+4): [", g_swings[idx+4].label, "] = ", DoubleToString(g_swings[idx+4].price, _Digits), " | زمان=", TimeToString(g_swings[idx+4].time));

   Print("📋 مشخصات خلاصه:");
   Print("   p1=", p1.price, " (", p1.label, "), p2=", p2.price, " (", p2.label, ")");
   Print("══════════════════════════════════════════════════════════════════════");
   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| ChartEvent: Handle Mouse Click                                   |
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
         int legIdx = FindNearestSwingLeg(dt, price);
         if(legIdx >= 0)
         {
            HighlightSwingLeg(legIdx);
         }
      }
   }
}
//+------------------------------------------------------------------+
