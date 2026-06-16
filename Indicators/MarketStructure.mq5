//+------------------------------------------------------------------+
//| MarketStructure.mq5 v12                                          |
//+------------------------------------------------------------------+
#property version "12.0"
#property indicator_chart_window
#property indicator_buffers 4
#property indicator_plots   4

#property indicator_label1 "High Line"
#property indicator_type1  DRAW_SECTION
#property indicator_color1 clrDodgerBlue
#property indicator_width1 2

#property indicator_label2 "Low Line"
#property indicator_type2  DRAW_SECTION
#property indicator_color2 clrOrangeRed
#property indicator_width2 2

#property indicator_label3 "High Dot"
#property indicator_type3  DRAW_ARROW
#property indicator_color3 clrDodgerBlue
#property indicator_width3 4

#property indicator_label4 "Low Dot"
#property indicator_type4  DRAW_ARROW
#property indicator_color4 clrOrangeRed
#property indicator_width4 4

input int PivotBars = 5;

double BH[], BL[], BHD[], BLD[];

int OnInit()
{
   SetIndexBuffer(0, BH,  INDICATOR_DATA);
   SetIndexBuffer(1, BL,  INDICATOR_DATA);
   SetIndexBuffer(2, BHD, INDICATOR_DATA);
   SetIndexBuffer(3, BLD, INDICATOR_DATA);

   PlotIndexSetInteger(2, PLOT_ARROW, 108);
   PlotIndexSetInteger(3, PLOT_ARROW, 108);

   PlotIndexSetDouble(0, PLOT_EMPTY_VALUE, 0.0);
   PlotIndexSetDouble(1, PLOT_EMPTY_VALUE, 0.0);
   PlotIndexSetDouble(2, PLOT_EMPTY_VALUE, 0.0);
   PlotIndexSetDouble(3, PLOT_EMPTY_VALUE, 0.0);

   IndicatorSetString(INDICATOR_SHORTNAME, "Market Structure");
   return INIT_SUCCEEDED;
}

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
   if(rates_total < PivotBars * 2 + 3) return 0;

   // پاک کردن همه بافرها
   for(int i = 0; i < rates_total; i++)
   {
      BH[i] = 0.0; BL[i] = 0.0;
      BHD[i] = 0.0; BLD[i] = 0.0;
   }

   // --- مرحله ۱: پیدا کردن همه پیوت‌ها ---
   struct Pivot { int bar; double price; bool isHigh; };
   Pivot pivots[];
   int pivotCount = 0;

   for(int i = PivotBars; i < rates_total - PivotBars; i++)
   {
      bool isH = true, isL = true;

      for(int k = 1; k <= PivotBars; k++)
      {
         if(high[i-k] >= high[i] || high[i+k] >= high[i]) isH = false;
         if(low[i-k]  <= low[i]  || low[i+k]  <= low[i])  isL = false;
      }

      if(isH && !isL)
      {
         ArrayResize(pivots, pivotCount + 1);
         pivots[pivotCount].bar    = i;
         pivots[pivotCount].price  = high[i];
         pivots[pivotCount].isHigh = true;
         pivotCount++;
      }
      else if(isL && !isH)
      {
         ArrayResize(pivots, pivotCount + 1);
         pivots[pivotCount].bar    = i;
         pivots[pivotCount].price  = low[i];
         pivots[pivotCount].isHigh = false;
         pivotCount++;
      }
   }

   if(pivotCount < 2) return rates_total;

   // --- مرحله ۲: فیلتر پیوت‌ها (متناوب High/Low) ---
   Pivot filtered[];
   int fCount = 0;

   ArrayResize(filtered, 1);
   filtered[0] = pivots[0];
   fCount = 1;

   for(int i = 1; i < pivotCount; i++)
   {
      Pivot last = filtered[fCount - 1];
      Pivot cur  = pivots[i];

      if(cur.isHigh == last.isHigh)
      {
         // همنوع → بهترین رو جایگزین کن
         if(cur.isHigh && cur.price > last.price)
            filtered[fCount - 1] = cur;
         else if(!cur.isHigh && cur.price < last.price)
            filtered[fCount - 1] = cur;
      }
      else
      {
         // تناوب درست → اضافه کن
         ArrayResize(filtered, fCount + 1);
         filtered[fCount] = cur;
         fCount++;
      }
   }

   // --- مرحله ۳: رسم خطوط ---
   for(int i = 1; i < fCount; i++)
   {
      int    barA   = filtered[i-1].bar;
      int    barB   = filtered[i].bar;
      double priceA = filtered[i-1].price;
      double priceB = filtered[i].price;

      if(filtered[i].isHigh)
      {
         // Low → High: خط آبی
         BH[barA]  = priceA;
         BH[barB]  = priceB;
         BHD[barB] = priceB;
      }
      else
      {
         // High → Low: خط قرمز
         BL[barA]  = priceA;
         BL[barB]  = priceB;
         BLD[barB] = priceB;
      }
   }

   return rates_total;
}