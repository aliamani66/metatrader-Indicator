//+------------------------------------------------------------------+
//| MarketStructure.mq5 v13                                          |
//+------------------------------------------------------------------+
#property version "13.0"
#property indicator_chart_window
#property indicator_buffers 4
#property indicator_plots   4

#property indicator_label1 "HH Line"
#property indicator_type1  DRAW_LINE
#property indicator_color1 clrDodgerBlue
#property indicator_width1 2
#property indicator_style1 STYLE_SOLID

#property indicator_label2 "LL Line"
#property indicator_type2  DRAW_LINE
#property indicator_color2 clrOrangeRed
#property indicator_width2 2
#property indicator_style2 STYLE_SOLID

#property indicator_label3 "HH Dot"
#property indicator_type3  DRAW_ARROW
#property indicator_color3 clrDodgerBlue
#property indicator_width3 4

#property indicator_label4 "LL Dot"
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

   IndicatorSetString(INDICATOR_SHORTNAME, "Market Structure v13");
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

   // ??? ???? ??? ??????
   ArrayInitialize(BH,  0.0);
   ArrayInitialize(BL,  0.0);
   ArrayInitialize(BHD, 0.0);
   ArrayInitialize(BLD, 0.0);

   // --- ????? ?: ???? ???? ??? ??????? ---
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
         pivots[pivotCount].bar = i; pivots[pivotCount].price = high[i]; pivots[pivotCount].isHigh = true;
         pivotCount++;
      }
      else if(isL && !isH)
      {
         ArrayResize(pivots, pivotCount + 1);
         pivots[pivotCount].bar = i; pivots[pivotCount].price = low[i]; pivots[pivotCount].isHigh = false;
         pivotCount++;
      }
   }

   if(pivotCount < 2) return rates_total;

   // --- ????? ?: ????? ??????? (?????? High/Low) ---
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
         if(cur.isHigh && cur.price > last.price) filtered[fCount - 1] = cur;
         else if(!cur.isHigh && cur.price < last.price) filtered[fCount - 1] = cur;
      }
      else
      {
         ArrayResize(filtered, fCount + 1);
         filtered[fCount] = cur;
         fCount++;
      }
   }

   // --- ????? ?: ??? ??? HH ? LL ---
   // ???? ?????: ?? DRAW_LINE ??????? ??????
   // ???? ??? ?? ????? ??? ????? interpolate ??? ?? ?? ?????? ????

   for(int i = 1; i < fCount; i++)
   {
      Pivot prev = filtered[i - 1];
      Pivot cur  = filtered[i];

      bool isHH = cur.isHigh  && cur.price > prev.price;  // Higher High
      bool isLL = !cur.isHigh && cur.price < prev.price;  // Lower Low

      if(!isHH && !isLL) continue;  // HL ?? LH ? ??? ???

      int barA = prev.bar;
      int barB = cur.bar;
      double priceA = prev.price;
      double priceB = cur.price;

      // interpolation ??? ??? ?? ???? (?? ???? ???? ???)
      for(int b = barA; b <= barB; b++)
      {
         double t = (barB == barA) ? 1.0 : (double)(b - barA) / (double)(barB - barA);
         double interp = priceA + t * (priceB - priceA);

         if(isHH) BH[b] = interp;
         else     BL[b] = interp;
      }

      // ???? (dot) ??? ???? ???
      if(isHH) BHD[barB] = priceB;
      else     BLD[barB] = priceB;
   }

   return rates_total;
}