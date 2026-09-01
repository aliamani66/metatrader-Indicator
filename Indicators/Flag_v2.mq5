//+------------------------------------------------------------------+
//| Flag_v2.mq5                                                      |
//| H1 Flag Box Indicator (Powered by MarketStructure v2 Engine)     |
//+------------------------------------------------------------------+
#property copyright "Flag v2"
#property link      ""
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

//--- Inputs
input group "=== Chart Display Settings ==="
input bool               InpHideGrid          = true;          // حذف گرید از چارت (Hide Grid)
input bool               InpHideVolumes       = true;          // حذف نمودار حجم پایین چارت (Hide Volumes)

input group "=== H1 Flag Settings ==="
input ENUM_TIMEFRAMES    InpTF                = PERIOD_H1;     // تایم‌فریم فلگ (H1)
input int                InpSwingBars         = 6;             // عمق امواج ماژور H1 (Swing Depth)
input int                InpMaxBars           = 1000;          // حداکثر کندل‌های H1 (Max Bars)
input color              InpBoxColor          = clrYellow;     // رنگ باکس‌های فلگ H1
input int                InpBoxWidth          = 1;             // ضخامت خط باکس
input bool               InpShowLabels        = true;          // نمایش متن برچسب H1
input int                InpFontSize          = 9;             // اندازه فونت برچسب
input string             InpFontName          = "Trebuchet MS";// نام فونت

//--- Prefix for chart objects
const string OBJ_PREFIX = "Flag_H1_";

//--- Pivot Structure
struct SPivot
{
   int      bar;
   datetime time;
   double   price;
   bool     isHigh;
};

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   if(InpHideGrid)
      ChartSetInteger(0, CHART_SHOW_GRID, false);
   if(InpHideVolumes)
      ChartSetInteger(0, CHART_SHOW_VOLUMES, CHART_VOLUME_HIDE);

   ChartRedraw(0);

   IndicatorSetString(INDICATOR_SHORTNAME, "Flag_v2 (H1)");
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
//| Helper: Draw Hollow Box on Chart                                 |
//+------------------------------------------------------------------+
void DrawBox(string name, datetime t1, double top, datetime t2, double bottom, color clr, int width)
{
   if(ObjectFind(0, name) >= 0)
      ObjectDelete(0, name);

   if(!ObjectCreate(0, name, OBJ_RECTANGLE, 0, t1, top, t2, bottom))
      return;

   ObjectSetInteger(0, name, OBJPROP_COLOR,      clr);
   ObjectSetInteger(0, name, OBJPROP_WIDTH,      width);
   ObjectSetInteger(0, name, OBJPROP_FILL,       false);
   ObjectSetInteger(0, name, OBJPROP_BACK,       false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN,     true);
   ObjectSetInteger(0, name, OBJPROP_RAY_RIGHT,  false);
}

//+------------------------------------------------------------------+
//| Helper: Draw Label on Chart                                      |
//+------------------------------------------------------------------+
void DrawLabel(string name, datetime t, double price, string text, color clr)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_TEXT, 0, t, price);

   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetString(0, name, OBJPROP_FONT, InpFontName);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, InpFontSize);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN, true);
   ObjectSetDouble(0, name, OBJPROP_PRICE, price);
   ObjectSetInteger(0, name, OBJPROP_TIME, t);
   ObjectSetInteger(0, name, OBJPROP_ANCHOR, ANCHOR_LOWER);
}

//+------------------------------------------------------------------+
//| Extract Alternating Swings for Timeframe                         |
//+------------------------------------------------------------------+
bool ExtractTfSwings(ENUM_TIMEFRAMES tf, int sBars, int maxBars, SPivot &swings[])
{
   ArrayResize(swings, 0);

   int total = iBars(_Symbol, tf);
   if(total <= sBars * 2 + 5)
      return false;

   int count = MathMin(total, maxBars);

   double high[], low[], close[], open[];
   datetime time[];

   ArraySetAsSeries(high, false);
   ArraySetAsSeries(low, false);
   ArraySetAsSeries(close, false);
   ArraySetAsSeries(open, false);
   ArraySetAsSeries(time, false);

   if(CopyHigh(_Symbol, tf, 0, count, high) < count) return false;
   if(CopyLow(_Symbol, tf, 0, count, low) < count) return false;
   if(CopyClose(_Symbol, tf, 0, count, close) < count) return false;
   if(CopyOpen(_Symbol, tf, 0, count, open) < count) return false;
   if(CopyTime(_Symbol, tf, 0, count, time) < count) return false;

   int startBar = sBars;
   int endBar   = count - sBars - 1;

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
      return false;

   //--- Step 2: Alternating Swings Sequence
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
      return false;

   //--- Step 3: Absolute Extreme Guarantee
   for(int i = 1; i < sCount - 1; i++)
   {
      int bPrev = swings[i - 1].bar;
      int bNext = swings[i + 1].bar;
      if(bPrev >= bNext) continue;

      if(!swings[i].isHigh) // Low between two Highs
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
      else // High between two Lows
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

   return (sCount >= 2);
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

   // Extract H1 Swings
   SPivot h1Swings[];
   if(!ExtractTfSwings(InpTF, InpSwingBars, InpMaxBars, h1Swings))
      return rates_total;

   int sCount = ArraySize(h1Swings);
   if(sCount < 2)
      return rates_total;

   //--- Clear previous boxes
   ObjectsDeleteAll(0, OBJ_PREFIX);

   //--- Draw H1 Flag Boxes (High to Low / Low to High)
   for(int i = 0; i < sCount - 1; i++)
   {
      SPivot p1 = h1Swings[i];
      SPivot p2 = h1Swings[i + 1];

      datetime t1 = p1.time;
      datetime t2 = p2.time;

      double top    = MathMax(p1.price, p2.price);
      double bottom = MathMin(p1.price, p2.price);

      string boxName = OBJ_PREFIX + "Box_" + IntegerToString(i);
      DrawBox(boxName, t1, top, t2, bottom, InpBoxColor, InpBoxWidth);

      if(InpShowLabels)
      {
         string lblName = OBJ_PREFIX + "Lbl_" + IntegerToString(i);
         string text = (p1.isHigh) ? "H1 Flag (H->L)" : "H1 Flag (L->H)";
         DrawLabel(lblName, t1, top, text, InpBoxColor);
      }
   }

   ChartRedraw(0);
   return rates_total;
}
//+------------------------------------------------------------------+
