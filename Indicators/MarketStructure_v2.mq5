//+------------------------------------------------------------------+
//| MarketStructure_v2.mq5                                           |
//| Macro Market Structure (Guaranteed Absolute Extreme Lock)        |
//+------------------------------------------------------------------+
#property copyright "Market Structure v2"
#property link      ""
#property version   "18.00"
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
input bool   InpHideGrid          = true;          // حذف گرید از چارت (Hide Grid)
input bool   InpHideVolumes       = true;          // حذف نمودار حجم پایین چارت (Hide Volumes)

input group "=== Structure Calculation (Macro Scale) ==="
input int    InpSwingBars         = 6;             // عمق امواج ماژور (6 تا 10 برای امواج بزرگ)
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

   IndicatorSetString(INDICATOR_SHORTNAME, "MarketStructure v18.0 (Macro)");
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

   int startBar = MathMax(sBars, rates_total - InpMaxBars);
   int endBar   = rates_total - sBars - 1;

   //--- Step 1: Detect candidate fractal extremes
   SPivot rawList[];
   int rCount = 0;

   for(int i = startBar; i <= endBar; i++)
   {
      bool isH = true;
      bool isL = true;

      for(int k = 1; k <= sBars; k++)
      {
         if(high[i - k] > high[i] || high[i + k] > high[i])
            isH = false;
         if(low[i - k] < low[i] || low[i + k] < low[i])
            isL = false;
      }

      if(isH && !isL)
      {
         ArrayResize(rawList, rCount + 1);
         rawList[rCount].bar    = i;
         rawList[rCount].time   = time[i];
         rawList[rCount].price  = high[i];
         rawList[rCount].isHigh = true;
         rCount++;
      }
      else if(isL && !isH)
      {
         ArrayResize(rawList, rCount + 1);
         rawList[rCount].bar    = i;
         rawList[rCount].time   = time[i];
         rawList[rCount].price  = low[i];
         rawList[rCount].isHigh = false;
         rCount++;
      }
      else if(isH && isL)
      {
         ArrayResize(rawList, rCount + 1);
         rawList[rCount].bar    = i;
         rawList[rCount].time   = time[i];
         if(close[i] >= open[i])
         {
            rawList[rCount].price  = high[i];
            rawList[rCount].isHigh = true;
         }
         else
         {
            rawList[rCount].price  = low[i];
            rawList[rCount].isHigh = false;
         }
         rCount++;
      }
   }

   if(rCount < 2)
      return rates_total;

   //--- Step 2: Build Alternating Swings Sequence
   SPivot swings[];
   int sCount = 0;

   for(int i = 0; i < rCount; i++)
   {
      SPivot cur = rawList[i];

      if(sCount == 0)
      {
         ArrayResize(swings, 1);
         swings[0] = cur;
         sCount = 1;
         continue;
      }

      SPivot last = swings[sCount - 1];

      if(cur.bar == last.bar)
         continue;

      if(cur.isHigh == last.isHigh)
      {
         if(cur.isHigh)
         {
            // Check if there was a real valley between the two highs
            int minB = last.bar;
            double minP = low[last.bar];
            for(int b = last.bar + 1; b < cur.bar; b++)
            {
               if(low[b] < minP)
               {
                  minP = low[b];
                  minB = b;
               }
            }

            if(minB > last.bar && (cur.bar - last.bar >= sBars + 2) && minP < last.price && cur.price > minP)
            {
               ArrayResize(swings, sCount + 2);
               swings[sCount].bar    = minB;
               swings[sCount].time   = time[minB];
               swings[sCount].price  = minP;
               swings[sCount].isHigh = false;

               swings[sCount + 1]    = cur;
               sCount += 2;
            }
            else if(cur.price >= last.price)
            {
               swings[sCount - 1] = cur;
            }
         }
         else // Two consecutive Lows
         {
            int maxB = last.bar;
            double maxP = high[last.bar];
            for(int b = last.bar + 1; b < cur.bar; b++)
            {
               if(high[b] > maxP)
               {
                  maxP = high[b];
                  maxB = b;
               }
            }

            if(maxB > last.bar && (cur.bar - last.bar >= sBars + 2) && maxP > last.price && cur.price < maxP)
            {
               ArrayResize(swings, sCount + 2);
               swings[sCount].bar    = maxB;
               swings[sCount].time   = time[maxB];
               swings[sCount].price  = maxP;
               swings[sCount].isHigh = true;

               swings[sCount + 1]    = cur;
               sCount += 2;
            }
            else if(cur.price <= last.price)
            {
               swings[sCount - 1] = cur;
            }
         }
      }
      else
      {
         if(cur.isHigh && cur.price <= last.price)
            continue;
         if(!cur.isHigh && cur.price >= last.price)
            continue;

         ArrayResize(swings, sCount + 1);
         swings[sCount] = cur;
         sCount++;
      }
   }

   if(sCount < 2)
      return rates_total;

   //--- Step 3: GUARANTEED ABSOLUTE EXTREME LOCK
   // Between any two consecutive peaks, the Low MUST be the absolute lowest wick!
   // Between any two consecutive valleys, the High MUST be the absolute highest wick!
   for(int i = 1; i < sCount - 1; i++)
   {
      int bPrev = swings[i - 1].bar;
      int bNext = swings[i + 1].bar;
      if(bPrev >= bNext) continue;

      if(!swings[i].isHigh) // This is a Low between two Highs
      {
         int minB = swings[i].bar;
         double minP = swings[i].price;
         for(int b = bPrev + 1; b < bNext; b++)
         {
            if(low[b] < minP)
            {
               minP = low[b];
               minB = b;
            }
         }
         swings[i].bar   = minB;
         swings[i].time  = time[minB];
         swings[i].price = minP;
      }
      else // This is a High between two Lows
      {
         int maxB = swings[i].bar;
         double maxP = swings[i].price;
         for(int b = bPrev + 1; b < bNext; b++)
         {
            if(high[b] > maxP)
            {
               maxP = high[b];
               maxB = b;
            }
         }
         swings[i].bar   = maxB;
         swings[i].time  = time[maxB];
         swings[i].price = maxP;
      }
   }

   //--- Step 4: Classify HH / LH / LL / HL
   for(int i = 0; i < sCount; i++)
   {
      if(i >= 2)
      {
         SPivot prevSame = swings[i - 2];
         if(swings[i].isHigh)
         {
            if(swings[i].price >= prevSame.price)
            {
               swings[i].label = "HH";
               swings[i].clr   = InpColorBullish;
            }
            else
            {
               swings[i].label = "LH";
               swings[i].clr   = InpColorBearish;
            }
         }
         else
         {
            if(swings[i].price <= prevSame.price)
            {
               swings[i].label = "LL";
               swings[i].clr   = InpColorBearish;
            }
            else
            {
               swings[i].label = "HL";
               swings[i].clr   = InpColorBullish;
            }
         }
      }
      else
      {
         if(swings[i].isHigh)
         {
            swings[i].label = "H";
            swings[i].clr   = InpColorBullish;
         }
         else
         {
            swings[i].label = "L";
            swings[i].clr   = InpColorBearish;
         }
      }
   }

   //--- Step 5: Render Buffers & Labels
   ObjectsDeleteAll(0, OBJ_PREFIX);

   for(int i = 0; i < sCount; i++)
   {
      int b = swings[i].bar;
      double pr = swings[i].price;

      // Leg color: Upward leg (0 = Blue), Downward leg (1 = Red)
      int legColor = 0;
      if(i > 0)
         legColor = swings[i].isHigh ? 0 : 1;
      else
         legColor = swings[i].isHigh ? 1 : 0;

      // Section line vertex
      BufferLine[b]      = pr;
      BufferLineColor[b] = legColor;

      // Arrow / Dot at pivot
      BufferArrow[b]      = pr;
      BufferArrowColor[b] = (swings[i].clr == InpColorBullish) ? 0 : 1;

      // Draw Text Label if enabled
      if(InpShowLabels)
      {
         string objName = OBJ_PREFIX + "Lbl_" + IntegerToString(i);
         DrawLabel(objName, swings[i].time, pr, swings[i].label, swings[i].clr, swings[i].isHigh);
      }
   }

   return rates_total;
}
//+------------------------------------------------------------------+
