//+------------------------------------------------------------------+
//| MarketStructure_MTF_fixed.mq5                                    |
//| Multi-Timeframe Market Structure overlay - fixed mapping/index   |
//+------------------------------------------------------------------+
#property version   "1.11"
#property indicator_chart_window
#property indicator_buffers 16
#property indicator_plots   8

// TF1 (default Daily) - heaviest weight = "most major"
#property indicator_label1  "TF1 Line"
#property indicator_type1   DRAW_COLOR_LINE
#property indicator_color1  clrNavy, clrDarkRed
#property indicator_width1  3
#property indicator_style1  STYLE_SOLID

#property indicator_label2  "TF1 Pivot"
#property indicator_type2   DRAW_COLOR_ARROW
#property indicator_color2  clrNavy, clrDarkRed
#property indicator_width2  4

// TF2 (default H4)
#property indicator_label3  "TF2 Line"
#property indicator_type3   DRAW_COLOR_LINE
#property indicator_color3  clrBlue, clrRed
#property indicator_width3  2
#property indicator_style3  STYLE_SOLID

#property indicator_label4  "TF2 Pivot"
#property indicator_type4   DRAW_COLOR_ARROW
#property indicator_color4  clrBlue, clrRed
#property indicator_width4  3

// TF3 (default H1)
#property indicator_label5  "TF3 Line"
#property indicator_type5   DRAW_COLOR_LINE
#property indicator_color5  clrDeepSkyBlue, clrTomato
#property indicator_width5  1
#property indicator_style5  STYLE_SOLID

#property indicator_label6  "TF3 Pivot"
#property indicator_type6   DRAW_COLOR_ARROW
#property indicator_color6  clrDeepSkyBlue, clrTomato
#property indicator_width6  2

// TF4 (default M5) - lightest weight = "most minor"
#property indicator_label7  "TF4 Line"
#property indicator_type7   DRAW_COLOR_LINE
#property indicator_color7  clrAqua, clrLightPink
#property indicator_width7  1
#property indicator_style7  STYLE_DOT

#property indicator_label8  "TF4 Pivot"
#property indicator_type8   DRAW_COLOR_ARROW
#property indicator_color8  clrAqua, clrLightPink
#property indicator_width8  1

//--- Inputs: source timeframes
input ENUM_TIMEFRAMES InpTF1     = PERIOD_D1;
input bool             InpUseTF1 = true;
input ENUM_TIMEFRAMES InpTF2     = PERIOD_H4;
input bool             InpUseTF2 = true;
input ENUM_TIMEFRAMES InpTF3     = PERIOD_H1;
input bool             InpUseTF3 = true;
input ENUM_TIMEFRAMES InpTF4     = PERIOD_M5;
input bool             InpUseTF4 = true;

input int  InpPivotBars      = 5;     // fractal bars left/right
input int  InpMaxBarsTF      = 3000;  // max history bars scanned per source timeframe
input bool InpShowLines      = false; // draw connecting lines
input bool InpShowLabels     = true;  // show labels
input int  InpMaxLabelsPerTF = 60;    // cap labels per TF

input int InpDedupTolerancePts = 2;   // dedup tolerance in points

// Causal link
input bool             InpShowCausalLink   = false;
input ENUM_TIMEFRAMES  InpCausalChildTF    = PERIOD_M15;
input ENUM_TIMEFRAMES  InpCausalParentTF   = PERIOD_H1;
input color            InpCausalLinkColor  = clrYellow;

//--- Buffers
double TF1_Line[], TF1_LineColor[], TF1_Dot[], TF1_DotColor[];
double TF2_Line[], TF2_LineColor[], TF2_Dot[], TF2_DotColor[];
double TF3_Line[], TF3_LineColor[], TF3_Dot[], TF3_DotColor[];
double TF4_Line[], TF4_LineColor[], TF4_Dot[], TF4_DotColor[];

//--- A raw fractal pivot
struct SPivot
{
   datetime time;
   double   price;
   bool     isHigh;
};

//--- A qualifying "major" pivot
struct SDot
{
   datetime time;
   double   price;
   bool     isHH;
};

//+------------------------------------------------------------------+
int OnInit()
{
   SetIndexBuffer(0,  TF1_Line,      INDICATOR_DATA);
   SetIndexBuffer(1,  TF1_LineColor, INDICATOR_COLOR_INDEX);
   SetIndexBuffer(2,  TF1_Dot,       INDICATOR_DATA);
   SetIndexBuffer(3,  TF1_DotColor,  INDICATOR_COLOR_INDEX);
   SetIndexBuffer(4,  TF2_Line,      INDICATOR_DATA);
   SetIndexBuffer(5,  TF2_LineColor, INDICATOR_COLOR_INDEX);
   SetIndexBuffer(6,  TF2_Dot,       INDICATOR_DATA);
   SetIndexBuffer(7,  TF2_DotColor,  INDICATOR_COLOR_INDEX);
   SetIndexBuffer(8,  TF3_Line,      INDICATOR_DATA);
   SetIndexBuffer(9,  TF3_LineColor, INDICATOR_COLOR_INDEX);
   SetIndexBuffer(10, TF3_Dot,       INDICATOR_DATA);
   SetIndexBuffer(11, TF3_DotColor,  INDICATOR_COLOR_INDEX);
   SetIndexBuffer(12, TF4_Line,      INDICATOR_DATA);
   SetIndexBuffer(13, TF4_LineColor, INDICATOR_COLOR_INDEX);
   SetIndexBuffer(14, TF4_Dot,       INDICATOR_DATA);
   SetIndexBuffer(15, TF4_DotColor,  INDICATOR_COLOR_INDEX);

   PlotIndexSetInteger(1, PLOT_ARROW, 108);
   PlotIndexSetInteger(3, PLOT_ARROW, 108);
   PlotIndexSetInteger(5, PLOT_ARROW, 108);
   PlotIndexSetInteger(7, PLOT_ARROW, 108);

   for(int p = 0; p < 8; p++)
      PlotIndexSetDouble(p, PLOT_EMPTY_VALUE, 0.0);

   IndicatorSetString(INDICATOR_SHORTNAME, "Market Structure MTF v1 (fixed)");
   return INIT_SUCCEEDED;
}
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, "MSM_");
}
//+------------------------------------------------------------------+
string TFName(ENUM_TIMEFRAMES tf)
{
   string s = EnumToString(tf);
   StringReplace(s, "PERIOD_", "");
   return s;
}
//+------------------------------------------------------------------+
// BuildStructure: fractal pivots -> filter -> HH/LL dots
bool BuildStructure(const string symbol, ENUM_TIMEFRAMES tf, int pivotBars, int maxBars,
                     SDot &dots[], SPivot &rawPivots[],
                     datetime &segA[], datetime &segB[],
                     double &prA[], double &prB[], bool &segHH[])
{
   ArrayResize(dots, 0);
   ArrayResize(rawPivots, 0);
   ArrayResize(segA, 0); ArrayResize(segB, 0);
   ArrayResize(prA, 0);  ArrayResize(prB, 0);
   ArrayResize(segHH, 0);

   int availBars = iBars(symbol, tf);
   if(availBars <= 0) return false;
   int reqBars = MathMin(availBars, maxBars);
   if(reqBars < pivotBars * 2 + 3) return false;

   double high[], low[]; datetime tm[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low,  true);
   ArraySetAsSeries(tm,   true);

   int copied = CopyHigh(symbol, tf, 0, reqBars, high);
   if(copied < pivotBars * 2 + 3) return false;
   CopyLow(symbol, tf, 0, copied, low);
   CopyTime(symbol, tf, 0, copied, tm);

   ArraySetAsSeries(high, false);
   ArraySetAsSeries(low,  false);
   ArraySetAsSeries(tm,   false);

   int n = copied;

   // Step 1: raw fractal pivots
   SPivot pivots[]; int pivotCount = 0;
   for(int i = pivotBars; i < n - pivotBars; i++)
   {
      bool isH = true, isL = true;
      for(int k = 1; k <= pivotBars; k++)
      {
         if(high[i-k] >= high[i] || high[i+k] >= high[i]) isH = false;
         if(low[i-k]  <= low[i]  || low[i+k]  <= low[i])  isL = false;
      }
      if(isH && !isL)
      {
         ArrayResize(pivots, pivotCount + 1);
         // tm[i] from CopyTime in MQL5 is the OPEN time of the bar
         pivots[pivotCount].time  = tm[i];
         pivots[pivotCount].price = high[i];
         pivots[pivotCount].isHigh = true;
         pivotCount++;
      }
      else if(isL && !isH)
      {
         ArrayResize(pivots, pivotCount + 1);
         pivots[pivotCount].time  = tm[i];
         pivots[pivotCount].price = low[i];
         pivots[pivotCount].isHigh = false;
         pivotCount++;
      }
   }

   ArrayResize(rawPivots, pivotCount);
   for(int i = 0; i < pivotCount; i++) rawPivots[i] = pivots[i];

   if(pivotCount < 2) return true;

   // Step 2: filter consecutive same-type pivots (keep extreme)
   SPivot filtered[]; int fCount = 0;
   ArrayResize(filtered, 1); filtered[0] = pivots[0]; fCount = 1;

   for(int i = 1; i < pivotCount; i++)
   {
      SPivot last = filtered[fCount - 1];
      SPivot cur  = pivots[i];
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

   // Step 3: tag HH / LL segments
   int segCount = 0, dotCount = 0;
   for(int i = 1; i < fCount; i++)
   {
      SPivot prev = filtered[i - 1];
      SPivot cur  = filtered[i];

      bool isHH = cur.isHigh  && cur.price > prev.price;
      bool isLL = !cur.isHigh && cur.price < prev.price;
      if(!isHH && !isLL) continue;

      ArrayResize(segA, segCount + 1); segA[segCount] = prev.time;
      ArrayResize(segB, segCount + 1); segB[segCount] = cur.time;
      ArrayResize(prA,  segCount + 1); prA[segCount]  = prev.price;
      ArrayResize(prB,  segCount + 1); prB[segCount]  = cur.price;
      ArrayResize(segHH,segCount + 1); segHH[segCount]= isHH;
      segCount++;

      ArrayResize(dots, dotCount + 1);
      dots[dotCount].time  = cur.time;
      dots[dotCount].price = cur.price;
      dots[dotCount].isHH  = isHH;
      dotCount++;
   }
   return true;
}
//+------------------------------------------------------------------+
bool HasHigherPriorityMatch(ENUM_TIMEFRAMES myTF, datetime t, double price, bool isHH,
                             ENUM_TIMEFRAMES otherTF, bool otherEnabled, SDot &otherDots[],
                             double priceTolerance)
{
   if(!otherEnabled) return false;
   int myPeriod    = PeriodSeconds(myTF);
   int otherPeriod = PeriodSeconds(otherTF);
   if(otherPeriod <= myPeriod) return false; // only strictly higher TF can own label

   int n = ArraySize(otherDots);
   for(int i = 0; i < n; i++)
   {
      if(otherDots[i].isHH != isHH) continue;
      if(t < otherDots[i].time || t >= otherDots[i].time + otherPeriod) continue;
      if(MathAbs(otherDots[i].price - price) <= priceTolerance) return true;
   }
   return false;
}
//+------------------------------------------------------------------+
// Map source time to chart TF: return the first chart-TF bar time >= srcTime
datetime MapSourceTime(datetime srcTime, ENUM_TIMEFRAMES srcTF)
{
   // srcTime is OPEN time of the source TF bar (from CopyTime)
   // We want the first chart-TF bar whose time >= srcTime
   int currSec = PeriodSeconds(PERIOD_CURRENT);
   if(currSec <= 0) return srcTime;

   // Round up to the next multiple of currSec (first bar start >= srcTime)
   datetime mapped = ((srcTime + currSec - 1) / currSec) * currSec;
   return mapped;
}
//+------------------------------------------------------------------+
// Find first bar index whose time >= t (works for ascending or descending arrays)
int FindBarIndex(const datetime &chartTime[], int ratesTotal, datetime t)
{
   if(ratesTotal <= 0) return -1;

   // Determine ordering: ascending (oldest..newest) or descending (newest..oldest)
   bool ascending = (chartTime[0] < chartTime[ratesTotal - 1]);

   // Boundary checks
   if(ascending)
   {
      if(t <= chartTime[0]) return 0;
      if(t >  chartTime[ratesTotal - 1]) return ratesTotal - 1;
   }
   else
   {
      if(t >= chartTime[0]) return 0;
      if(t <  chartTime[ratesTotal - 1]) return ratesTotal - 1;
   }

   int lo = 0, hi = ratesTotal - 1;
   while(lo < hi)
   {
      int mid = (lo + hi) / 2;
      if(ascending)
      {
         if(chartTime[mid] < t) lo = mid + 1;
         else hi = mid;
      }
      else
      {
         // descending
         if(chartTime[mid] > t) lo = mid + 1;
         else hi = mid;
      }
   }
   return lo;
}
//+------------------------------------------------------------------+
void DrawSlot(SDot &dots[], datetime &segA[], datetime &segB[], double &prA[], double &prB[], bool &segHH[],
              bool &labelOk[], ENUM_TIMEFRAMES srcTF,
              const datetime &chartTime[], int ratesTotal,
              double &lineBuf[], double &lineColor[], double &dotBuf[], double &dotColor[],
              string tfTag, bool showLines, bool showLabels, int maxLabels)
{
   if(showLines)
   {
      int segCount = ArraySize(segA);
      for(int s = 0; s < segCount; s++)
      {
         datetime mappedA = MapSourceTime(segA[s], srcTF);
         datetime mappedB = MapSourceTime(segB[s], srcTF);

         int idxA = FindBarIndex(chartTime, ratesTotal, mappedA);
         int idxB = FindBarIndex(chartTime, ratesTotal, mappedB);
         if(idxA < 0 || idxB < 0) continue;
         if(idxA > idxB) continue;

         datetime ta = chartTime[idxA];
         datetime tb = chartTime[idxB];
         double   paV = prA[s],  pbV = prB[s];

         for(int k = idxA; k <= idxB; k++)
         {
            double frac = (tb == ta) ? 1.0 : (double)(chartTime[k] - ta) / (double)(tb - ta);
            if(frac < 0) frac = 0; if(frac > 1) frac = 1;
            lineBuf[k]   = paV + frac * (pbV - paV);
            lineColor[k] = segHH[s] ? 0.0 : 1.0;
         }
      }
   }

   // pivot dots
   int dotCount = ArraySize(dots);
   for(int i = 0; i < dotCount; i++)
   {
      datetime mappedTime = MapSourceTime(dots[i].time, srcTF);
      int idx = FindBarIndex(chartTime, ratesTotal, mappedTime);
      if(idx < 0) continue;
      dotBuf[idx]   = dots[i].price;
      dotColor[idx] = dots[i].isHH ? 0.0 : 1.0;
   }

   // labels (most recent first, capped)
   if(showLabels)
   {
      int allowedIdx[]; int allowedCount = 0;
      for(int i = 0; i < dotCount; i++)
      {
         if(!labelOk[i]) continue;
         ArrayResize(allowedIdx, allowedCount + 1);
         allowedIdx[allowedCount] = i;
         allowedCount++;
      }
      int startI = MathMax(0, allowedCount - maxLabels);
      for(int a = startI; a < allowedCount; a++)
      {
         int i = allowedIdx[a];
         datetime mappedTime = MapSourceTime(dots[i].time, srcTF);
         string name = "MSM_LBL_" + tfTag + "_" + IntegerToString((int)dots[i].time);

         // Create or update text object
         if(ObjectFind(0, name) < 0)
         {
            ObjectCreate(0, name, OBJ_TEXT, 0, mappedTime, dots[i].price);
         }
         else
         {
            ObjectSetInteger(0, name, OBJPROP_TIME, mappedTime);
            ObjectSetDouble(0, name, OBJPROP_PRICE, dots[i].price);
         }

         ObjectSetString(0, name, OBJPROP_TEXT, tfTag + (dots[i].isHH ? " HH" : " LL"));
         ObjectSetInteger(0, name, OBJPROP_COLOR, dots[i].isHH ? clrDodgerBlue : clrOrangeRed);
         ObjectSetInteger(0, name, OBJPROP_ANCHOR, dots[i].isHH ? ANCHOR_BOTTOM : ANCHOR_TOP);
         ObjectSetInteger(0, name, OBJPROP_FONTSIZE, 7);
      }
   }
}
//+------------------------------------------------------------------+
void ProcessCausalLinks(ENUM_TIMEFRAMES childTF, ENUM_TIMEFRAMES parentTF,
                         int pivotBars, int maxBars, color lnColor)
{
   SDot pdots[]; SPivot praw[]; datetime pa[], pb2[]; double ppA[], ppB[]; bool phh[];
   if(!BuildStructure(_Symbol, parentTF, pivotBars, maxBars, pdots, praw, pa, pb2, ppA, ppB, phh)) return;

   SDot cdots[]; SPivot craw[]; datetime ca[], cb[]; double cpA[], cpB[]; bool chh[];
   if(!BuildStructure(_Symbol, childTF, pivotBars, maxBars, cdots, craw, ca, cb, cpA, cpB, chh)) return;

   int parentSeconds = PeriodSeconds(parentTF);
   int pdCount  = ArraySize(pdots);
   int rawCount = ArraySize(craw);

   for(int i = 0; i < pdCount; i++)
   {
      datetime tStart = pdots[i].time;
      datetime tEnd   = tStart + parentSeconds;
      bool wantHigh = pdots[i].isHH;

      int bestIdx = -1; double bestDiff = DBL_MAX;
      for(int r = 0; r < rawCount; r++)
      {
         if(craw[r].isHigh != wantHigh) continue;
         if(craw[r].time < tStart || craw[r].time >= tEnd) continue;
         double diff = MathAbs(craw[r].price - pdots[i].price);
         if(diff < bestDiff) { bestDiff = diff; bestIdx = r; }
      }
      if(bestIdx < 0) continue;

      string ln = "MSM_LINK_" + IntegerToString((int)pdots[i].time);
      // Map times for drawing trend
      datetime childMapped = MapSourceTime(craw[bestIdx].time, childTF);
      datetime parentMapped = MapSourceTime(pdots[i].time, parentTF);
      ObjectCreate(0, ln, OBJ_TREND, 0, childMapped, craw[bestIdx].price, parentMapped, pdots[i].price);
      ObjectSetInteger(0, ln, OBJPROP_COLOR, lnColor);
      ObjectSetInteger(0, ln, OBJPROP_STYLE, STYLE_DOT);
      ObjectSetInteger(0, ln, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, ln, OBJPROP_RAY_RIGHT, false);

      string lbl = "MSM_LINKLBL_" + IntegerToString((int)pdots[i].time);
      if(ObjectFind(0, lbl) < 0)
         ObjectCreate(0, lbl, OBJ_TEXT, 0, childMapped, craw[bestIdx].price);
      else
      {
         ObjectSetInteger(0, lbl, OBJPROP_TIME, childMapped);
         ObjectSetDouble(0, lbl, OBJPROP_PRICE, craw[bestIdx].price);
      }
      ObjectSetString(0, lbl, OBJPROP_TEXT, TFName(childTF) + " -> " + TFName(parentTF));
      ObjectSetInteger(0, lbl, OBJPROP_COLOR, lnColor);
      ObjectSetInteger(0, lbl, OBJPROP_FONTSIZE, 7);
      ObjectSetInteger(0, lbl, OBJPROP_ANCHOR, wantHigh ? ANCHOR_BOTTOM : ANCHOR_TOP);
   }
}
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
   if(rates_total < 5) return 0;

   static datetime lastSrcTime[4] = {0,0,0,0};
   static datetime lastChildTime  = 0;
   static datetime lastParentTime = 0;

   ENUM_TIMEFRAMES tfArr[4] = {InpTF1, InpTF2, InpTF3, InpTF4};
   bool useArr[4] = {InpUseTF1, InpUseTF2, InpUseTF3, InpUseTF4};

   bool needRecalc = (prev_calculated == 0);
   for(int s = 0; s < 4; s++)
   {
      if(!useArr[s]) continue;
      datetime t0 = iTime(_Symbol, tfArr[s], 0);
      if(t0 != lastSrcTime[s]) { needRecalc = true; lastSrcTime[s] = t0; }
   }
   if(InpShowCausalLink)
   {
      datetime ct = iTime(_Symbol, InpCausalChildTF, 0);
      datetime pt = iTime(_Symbol, InpCausalParentTF, 0);
      if(ct != lastChildTime)  { needRecalc = true; lastChildTime  = ct; }
      if(pt != lastParentTime) { needRecalc = true; lastParentTime = pt; }
   }

   if(!needRecalc) return rates_total;

   ArrayInitialize(TF1_Line,0.0); ArrayInitialize(TF1_LineColor,0.0); ArrayInitialize(TF1_Dot,0.0); ArrayInitialize(TF1_DotColor,0.0);
   ArrayInitialize(TF2_Line,0.0); ArrayInitialize(TF2_LineColor,0.0); ArrayInitialize(TF2_Dot,0.0); ArrayInitialize(TF2_DotColor,0.0);
   ArrayInitialize(TF3_Line,0.0); ArrayInitialize(TF3_LineColor,0.0); ArrayInitialize(TF3_Dot,0.0); ArrayInitialize(TF3_DotColor,0.0);
   ArrayInitialize(TF4_Line,0.0); ArrayInitialize(TF4_LineColor,0.0); ArrayInitialize(TF4_Dot,0.0); ArrayInitialize(TF4_DotColor,0.0);

   ObjectsDeleteAll(0, "MSM_");

   // compute structure for all slots
   SDot dotsS1[]; SPivot rawS1[]; datetime segAS1[],segBS1[]; double pAS1[],pBS1[]; bool hhS1[];
   bool ok1 = InpUseTF1 && BuildStructure(_Symbol, InpTF1, InpPivotBars, InpMaxBarsTF, dotsS1, rawS1, segAS1, segBS1, pAS1, pBS1, hhS1);

   SDot dotsS2[]; SPivot rawS2[]; datetime segAS2[],segBS2[]; double pAS2[],pBS2[]; bool hhS2[];
   bool ok2 = InpUseTF2 && BuildStructure(_Symbol, InpTF2, InpPivotBars, InpMaxBarsTF, dotsS2, rawS2, segAS2, segBS2, pAS2, pBS2, hhS2);

   SDot dotsS3[]; SPivot rawS3[]; datetime segAS3[],segBS3[]; double pAS3[],pBS3[]; bool hhS3[];
   bool ok3 = InpUseTF3 && BuildStructure(_Symbol, InpTF3, InpPivotBars, InpMaxBarsTF, dotsS3, rawS3, segAS3, segBS3, pAS3, pBS3, hhS3);

   SDot dotsS4[]; SPivot rawS4[]; datetime segAS4[],segBS4[]; double pAS4[],pBS4[]; bool hhS4[];
   bool ok4 = InpUseTF4 && BuildStructure(_Symbol, InpTF4, InpPivotBars, InpMaxBarsTF, dotsS4, rawS4, segAS4, segBS4, pAS4, pBS4, hhS4);

   double tol = InpDedupTolerancePts * _Point;

   // dedup labels
   bool labelOkS1[]; ArrayResize(labelOkS1, ArraySize(dotsS1));
   for(int i = 0; i < ArraySize(dotsS1); i++)
   {
      bool ok = true;
      if(ok && HasHigherPriorityMatch(InpTF1, dotsS1[i].time, dotsS1[i].price, dotsS1[i].isHH, InpTF2, ok2, dotsS2, tol)) ok = false;
      if(ok && HasHigherPriorityMatch(InpTF1, dotsS1[i].time, dotsS1[i].price, dotsS1[i].isHH, InpTF3, ok3, dotsS3, tol)) ok = false;
      if(ok && HasHigherPriorityMatch(InpTF1, dotsS1[i].time, dotsS1[i].price, dotsS1[i].isHH, InpTF4, ok4, dotsS4, tol)) ok = false;
      labelOkS1[i] = ok;
   }

   bool labelOkS2[]; ArrayResize(labelOkS2, ArraySize(dotsS2));
   for(int i = 0; i < ArraySize(dotsS2); i++)
   {
      bool ok = true;
      if(ok && HasHigherPriorityMatch(InpTF2, dotsS2[i].time, dotsS2[i].price, dotsS2[i].isHH, InpTF1, ok1, dotsS1, tol)) ok = false;
      if(ok && HasHigherPriorityMatch(InpTF2, dotsS2[i].time, dotsS2[i].price, dotsS2[i].isHH, InpTF3, ok3, dotsS3, tol)) ok = false;
      if(ok && HasHigherPriorityMatch(InpTF2, dotsS2[i].time, dotsS2[i].price, dotsS2[i].isHH, InpTF4, ok4, dotsS4, tol)) ok = false;
      labelOkS2[i] = ok;
   }

   bool labelOkS3[]; ArrayResize(labelOkS3, ArraySize(dotsS3));
   for(int i = 0; i < ArraySize(dotsS3); i++)
   {
      bool ok = true;
      if(ok && HasHigherPriorityMatch(InpTF3, dotsS3[i].time, dotsS3[i].price, dotsS3[i].isHH, InpTF1, ok1, dotsS1, tol)) ok = false;
      if(ok && HasHigherPriorityMatch(InpTF3, dotsS3[i].time, dotsS3[i].price, dotsS3[i].isHH, InpTF2, ok2, dotsS2, tol)) ok = false;
      if(ok && HasHigherPriorityMatch(InpTF3, dotsS3[i].time, dotsS3[i].price, dotsS3[i].isHH, InpTF4, ok4, dotsS4, tol)) ok = false;
      labelOkS3[i] = ok;
   }

   bool labelOkS4[]; ArrayResize(labelOkS4, ArraySize(dotsS4));
   for(int i = 0; i < ArraySize(dotsS4); i++)
   {
      bool ok = true;
      if(ok && HasHigherPriorityMatch(InpTF4, dotsS4[i].time, dotsS4[i].price, dotsS4[i].isHH, InpTF1, ok1, dotsS1, tol)) ok = false;
      if(ok && HasHigherPriorityMatch(InpTF4, dotsS4[i].time, dotsS4[i].price, dotsS4[i].isHH, InpTF2, ok2, dotsS2, tol)) ok = false;
      if(ok && HasHigherPriorityMatch(InpTF4, dotsS4[i].time, dotsS4[i].price, dotsS4[i].isHH, InpTF3, ok3, dotsS3, tol)) ok = false;
      labelOkS4[i] = ok;
   }

   // draw
   if(ok1) DrawSlot(dotsS1, segAS1, segBS1, pAS1, pBS1, hhS1, labelOkS1, InpTF1, time, rates_total, TF1_Line,TF1_LineColor,TF1_Dot,TF1_DotColor, TFName(InpTF1), InpShowLines, InpShowLabels, InpMaxLabelsPerTF);
   if(ok2) DrawSlot(dotsS2, segAS2, segBS2, pAS2, pBS2, hhS2, labelOkS2, InpTF2, time, rates_total, TF2_Line,TF2_LineColor,TF2_Dot,TF2_DotColor, TFName(InpTF2), InpShowLines, InpShowLabels, InpMaxLabelsPerTF);
   if(ok3) DrawSlot(dotsS3, segAS3, segBS3, pAS3, pBS3, hhS3, labelOkS3, InpTF3, time, rates_total, TF3_Line,TF3_LineColor,TF3_Dot,TF3_DotColor, TFName(InpTF3), InpShowLines, InpShowLabels, InpMaxLabelsPerTF);
   if(ok4) DrawSlot(dotsS4, segAS4, segBS4, pAS4, pBS4, hhS4, labelOkS4, InpTF4, time, rates_total, TF4_Line,TF4_LineColor,TF4_Dot,TF4_DotColor, TFName(InpTF4), InpShowLines, InpShowLabels, InpMaxLabelsPerTF);

   if(InpShowCausalLink)
      ProcessCausalLinks(InpCausalChildTF, InpCausalParentTF, InpPivotBars, InpMaxBarsTF, InpCausalLinkColor);

   return rates_total;
}
//+------------------------------------------------------------------+
