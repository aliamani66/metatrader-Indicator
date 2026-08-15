//+------------------------------------------------------------------+
//| MarketStructure_v2.mq5                                           |
//| Market Structure Indicator (Direct Shared Engine)                |
//+------------------------------------------------------------------+
#property copyright "Market Structure v2"
#property link      ""
#property version   "33.00"
#property indicator_chart_window
#property indicator_buffers 4
#property indicator_plots   2

//--- Plot 1: ZigZag Structure Line (Color Section)
#property indicator_label1  "Structure Line"
#property indicator_type1   DRAW_COLOR_SECTION
#property indicator_color1  clrDodgerBlue, clrCrimson
#property indicator_style1  STYLE_SOLID
#property indicator_width1  2

//--- Plot 2: Pivot Points (Color Arrow)
#property indicator_label2  "Pivot Dot"
#property indicator_type2   DRAW_COLOR_ARROW
#property indicator_color2  clrDodgerBlue, clrCrimson
#property indicator_width2  3

#include <MarketStructureEngine.mqh>

//--- Inputs
input group "=== Chart Display Settings ==="
input bool   InpHideGrid          = true;          // حذف گرید از چارت (Hide Grid)
input bool   InpHideVolumes       = true;          // حذف نمودار حجم پایین چارت (Hide Volumes)

input group "=== Structure Calculation (matches Flag) ==="
input int    InpSwingBars         = 6;             // عمق امواج ماژور (Swing Bars - پیش‌فرض 6)
input int    InpMaxBars           = 3000;          // حداکثر کندل‌های محاسبه (Max Bars)

input group "=== Visuals & Labels ==="
input bool   InpShowLabels        = true;          // نمایش برچسب‌های HH, LH, LL, HL
input color  InpColorBullish      = clrDodgerBlue; // رنگ صعودی (HH / HL)
input color  InpColorBearish      = clrCrimson;    // رنگ نزولی (LH / LL)
input int    InpFontSize          = 10;            // اندازه فونت برچسب‌ها
input string InpFontName          = "Trebuchet MS";// نام فونت

//--- Buffers
double BufferLine[];
double BufferLineColor[];
double BufferArrow[];
double BufferArrowColor[];

// Global storage for current swings
SPivot g_swings[];
int    g_swingCount = 0;

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
   SetIndexBuffer(2, BufferArrow,      INDICATOR_DATA);
   SetIndexBuffer(3, BufferArrowColor, INDICATOR_COLOR_INDEX);

   PlotIndexSetInteger(1, PLOT_ARROW, 159); // Dot arrow

   PlotIndexSetDouble(0, PLOT_EMPTY_VALUE, 0.0);
   PlotIndexSetDouble(1, PLOT_EMPTY_VALUE, 0.0);
   PlotIndexSetDouble(2, PLOT_EMPTY_VALUE, 0.0);
   PlotIndexSetDouble(3, PLOT_EMPTY_VALUE, 0.0);

   if(InpHideGrid)
      ChartSetInteger(0, CHART_SHOW_GRID, false);
   if(InpHideVolumes)
      ChartSetInteger(0, CHART_SHOW_VOLUMES, CHART_VOLUME_HIDE);

   ObjectsDeleteAll(0, OBJ_PREFIX);
   ChartRedraw(0);

   IndicatorSetString(INDICATOR_SHORTNAME, "MarketStructure v33.0");
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
//| Helper: Create or update text label on chart                     |
//+------------------------------------------------------------------+
void DrawLabel(string name, datetime t, double price, string text, color clr, bool above)
{
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_TEXT, 0, t, price);
   }
   
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetString(0, name, OBJPROP_FONT, InpFontName);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, InpFontSize);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN, true);
   ObjectSetDouble(0, name, OBJPROP_PRICE, price);
   ObjectSetInteger(0, name, OBJPROP_TIME, t);

   if(above)
      ObjectSetInteger(0, name, OBJPROP_ANCHOR, ANCHOR_LOWER);
   else
      ObjectSetInteger(0, name, OBJPROP_ANCHOR, ANCHOR_UPPER);
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
   ArrayInitialize(BufferArrow, 0.0);
   ArrayInitialize(BufferArrowColor, 0.0);

   SPivot pivots[];
   if(!BuildAlternatingPivots(_Period, sBars, InpMaxBars, pivots))
      return rates_total;

   int sCount = ArraySize(pivots);
   if(sCount < 2)
      return rates_total;

   // Store globally
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

   // Clear old labels
   ObjectsDeleteAll(0, OBJ_PREFIX + "Lbl_");

   // Render ZigZag Lines and Points
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

      BufferArrow[chartBar]      = pr;
      BufferArrowColor[chartBar] = (g_swings[i].clr == InpColorBullish) ? 0 : 1;

      if(InpShowLabels)
      {
         string objName = OBJ_PREFIX + "Lbl_" + IntegerToString(i);
         DrawLabel(objName, g_swings[i].time, pr, g_swings[i].label, g_swings[i].clr, g_swings[i].isHigh);
      }
   }

   return rates_total;
}
//+------------------------------------------------------------------+
