//+------------------------------------------------------------------+
//| MarketStructure_v2.mq5                                           |
//| Pure Price-Action Swings (No Fake Swings on Consecutive Bars)   |
//+------------------------------------------------------------------+
#property copyright "Market Structure v2"
#property link      ""
#property version   "12.00"
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
#property indicator_label2  "Structure Pivot"
#property indicator_type2   DRAW_COLOR_ARROW
#property indicator_color2  clrDodgerBlue, clrCrimson
#property indicator_width2  3

//--- Inputs
input group "=== Chart Display Settings ==="
input bool   InpHideGrid          = true;        // حذف گرید از چارت (Hide Grid)
input bool   InpHideVolumes       = true;        // حذف نمودار حجم پایین چارت (Hide Volumes)

input group "=== Structure Calculation ==="
input int    InpMaxBars           = 3000;        // حداکثر کندل‌های محاسبه (Max Bars)

input group "=== Visuals & Labels ==="
input bool   InpShowLabels        = true;        // نمایش برچسب‌های HH, LH, LL, HL
input color  InpColorBullish      = clrDodgerBlue;// رنگ صعودی (HH / HL)
input color  InpColorBearish      = clrCrimson;   // رنگ نزولی (LH / LL)
input int    InpFontSize          = 9;           // اندازه فونت برچسب‌ها
input string InpFontName          = "Trebuchet MS"; // نام فونت

//--- Buffers
double BufferLine[];
double BufferLineColor[];
double BufferArrow[];
double BufferArrowColor[];

//--- Structure for Pivot
struct SPivot
{
   int      bar;
   datetime time;
   double   price;
   bool     isHigh;
   string   label;       // "HH", "LH", "LL", "HL"
   color    clr;
};

//--- Prefix for chart objects
const string OBJ_PREFIX = "MSv2_";

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

   ChartRedraw(0);

   IndicatorSetString(INDICATOR_SHORTNAME, "MarketStructure v12.0");
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
   if(rates_total < 10)
      return 0;

   //--- Enforce chart settings
   if(InpHideGrid)
      ChartSetInteger(0, CHART_SHOW_GRID, false);
   if(InpHideVolumes)
      ChartSetInteger(0, CHART_SHOW_VOLUMES, CHART_VOLUME_HIDE);

   //--- Clear Buffers
   ArrayInitialize(BufferLine, 0.0);
   ArrayInitialize(BufferLineColor, 0.0);
   ArrayInitialize(BufferArrow, 0.0);
   ArrayInitialize(BufferArrowColor, 0.0);

   int startBar = MathMax(2, rates_total - InpMaxBars);
   int endBar   = rates_total - 1;

   //--- Pure Price Action Swing State Machine
   // +1 = UP leg (continuous rise), -1 = DOWN leg (continuous drop)
   int dir = 1;
   int peakBar = startBar;
   double peakPrice = high[startBar];
   int valleyBar = startBar;
   double valleyPrice = low[startBar];

   SPivot pivots[];
   int pCount = 0;

   for(int i = startBar; i <= endBar; i++)
   {
      if(dir == 1) // In Upward Leg
      {
         // If makes new high, leg extends
         if(high[i] >= peakPrice)
         {
            peakPrice = high[i];
            peakBar   = i;
         }

         // A true pullback occurs ONLY when candle makes a lower low than previous candle
         // (and did NOT make a new peak on this candle)
         if(low[i] < low[i - 1] && high[i] < peakPrice)
         {
            // Upward leg is complete: confirm Peak
            ArrayResize(pivots, pCount + 1);
            pivots[pCount].bar    = peakBar;
            pivots[pCount].time   = time[peakBar];
            pivots[pCount].price  = peakPrice;
            pivots[pCount].isHigh = true;
            pCount++;

            // Switch to downward leg
            dir         = -1;
            valleyBar   = i;
            valleyPrice = low[i];
         }
      }
      else // In Downward Leg
      {
         // If makes new low, leg extends
         if(low[i] <= valleyPrice)
         {
            valleyPrice = low[i];
            valleyBar   = i;
         }

         // A true bounce occurs ONLY when candle makes a higher high than previous candle
         // (and did NOT make a new valley on this candle)
         if(high[i] > high[i - 1] && low[i] > valleyPrice)
         {
            // Downward leg is complete: confirm Valley
            ArrayResize(pivots, pCount + 1);
            pivots[pCount].bar    = valleyBar;
            pivots[pCount].time   = time[valleyBar];
            pivots[pCount].price  = valleyPrice;
            pivots[pCount].isHigh = false;
            pCount++;

            // Switch to upward leg
            dir       = 1;
            peakBar   = i;
            peakPrice = high[i];
         }
      }
   }

   // Add active forming leg point at end of chart
   if(pCount > 0)
   {
      int lastBar = (dir == 1) ? peakBar : valleyBar;
      double lastPrice = (dir == 1) ? peakPrice : valleyPrice;
      if(lastBar != pivots[pCount - 1].bar)
      {
         ArrayResize(pivots, pCount + 1);
         pivots[pCount].bar    = lastBar;
         pivots[pCount].time   = time[lastBar];
         pivots[pCount].price  = lastPrice;
         pivots[pCount].isHigh = (dir == 1);
         pCount++;
      }
   }

   if(pCount < 2)
      return rates_total;

   //--- Step 2: Classify HH / LH / LL / HL
   for(int i = 0; i < pCount; i++)
   {
      if(i >= 2)
      {
         SPivot prevSame = pivots[i - 2];
         if(pivots[i].isHigh)
         {
            if(pivots[i].price >= prevSame.price)
            {
               pivots[i].label = "HH";
               pivots[i].clr   = InpColorBullish;
            }
            else
            {
               pivots[i].label = "LH";
               pivots[i].clr   = InpColorBearish;
            }
         }
         else
         {
            if(pivots[i].price <= prevSame.price)
            {
               pivots[i].label = "LL";
               pivots[i].clr   = InpColorBearish;
            }
            else
            {
               pivots[i].label = "HL";
               pivots[i].clr   = InpColorBullish;
            }
         }
      }
      else
      {
         if(pivots[i].isHigh)
         {
            pivots[i].label = "H";
            pivots[i].clr   = InpColorBullish;
         }
         else
         {
            pivots[i].label = "L";
            pivots[i].clr   = InpColorBearish;
         }
      }
   }

   //--- Step 3: Render Buffers & Labels
   ObjectsDeleteAll(0, OBJ_PREFIX);

   for(int i = 0; i < pCount; i++)
   {
      int b = pivots[i].bar;
      double pr = pivots[i].price;

      // Leg color: Upward leg (0 = Blue), Downward leg (1 = Red)
      int legColor = 0;
      if(i > 0)
         legColor = pivots[i].isHigh ? 0 : 1;
      else
         legColor = pivots[i].isHigh ? 1 : 0;

      // Section line vertex
      BufferLine[b]      = pr;
      BufferLineColor[b] = legColor;

      // Arrow / Dot at pivot
      BufferArrow[b]      = pr;
      BufferArrowColor[b] = (pivots[i].clr == InpColorBullish) ? 0 : 1;

      // Draw Text Label if enabled
      if(InpShowLabels)
      {
         string objName = OBJ_PREFIX + "Lbl_" + IntegerToString(i);
         DrawLabel(objName, pivots[i].time, pr, pivots[i].label, pivots[i].clr, pivots[i].isHigh);
      }
   }

   return rates_total;
}
//+------------------------------------------------------------------+
