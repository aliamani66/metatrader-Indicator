//+------------------------------------------------------------------+
//| PrePivotBox_MTF.mq5                                              |
//| Pre-Pivot Impulse Box indicator  v1.10                           |
//|                                                                    |
//| For each HH/LL pivot on H1/H4/D1 finds the M5 impulse leg that  |
//| immediately preceded it and draws a hollow rectangle:             |
//|                                                                    |
//|  Before LL pivot  → last M5 LL→HH leg  → BLUE  box              |
//|  Before HH pivot  → last M5 HH→LL leg  → RED   box              |
//|                                                                    |
//| Box extends right until:                                          |
//|  Bull box (before LL): a candle HIGH breaks above boxTop         |
//|  Bear box (before HH): a candle LOW  breaks below boxBottom      |
//+------------------------------------------------------------------+
#property version   "1.10"
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

//--- Inputs
input ENUM_TIMEFRAMES InpParentTF1    = PERIOD_H1;
input bool            InpUseParent1   = true;
input ENUM_TIMEFRAMES InpParentTF2    = PERIOD_H4;
input bool            InpUseParent2   = true;
input ENUM_TIMEFRAMES InpParentTF3    = PERIOD_D1;
input bool            InpUseParent3   = true;

input ENUM_TIMEFRAMES InpImpulseTF    = PERIOD_M5;
input int             InpPivotBars    = 5;
input int             InpMaxBarsParent= 500;
input int             InpMaxBarsImp   = 3000;

input color  InpColorTF1   = clrGold;          // H1  boxes
input color  InpColorTF2   = clrDodgerBlue;    // H4  boxes
input color  InpColorTF3   = clrMagenta;       // D1  boxes
input int    InpLineWidth  = 2;
input bool   InpShowLabels = true;

//--- Pivot structure
struct SPivot { datetime time; double price; bool isHigh; };

//+------------------------------------------------------------------+
bool GetPivots(ENUM_TIMEFRAMES tf, int pivotBars, int maxBars, SPivot &out[])
{
   ArrayResize(out, 0);
   int avail = iBars(_Symbol, tf);
   if(avail <= 0) return false;
   int n = MathMin(avail, maxBars);
   if(n < pivotBars * 2 + 3) return false;

   double hi[], lo[]; datetime tm[];
   ArraySetAsSeries(hi, true);
   ArraySetAsSeries(lo, true);
   ArraySetAsSeries(tm, true);
   int copied = CopyHigh(_Symbol, tf, 0, n, hi);
   if(copied < pivotBars * 2 + 3) return false;
   CopyLow(_Symbol,  tf, 0, copied, lo);
   CopyTime(_Symbol, tf, 0, copied, tm);
   ArraySetAsSeries(hi, false);
   ArraySetAsSeries(lo, false);
   ArraySetAsSeries(tm, false);

   SPivot raw[]; int rc = 0;
   for(int i = pivotBars; i < copied - pivotBars; i++)
   {
      bool isH = true, isL = true;
      for(int k = 1; k <= pivotBars; k++)
      {
         if(hi[i-k] >= hi[i] || hi[i+k] >= hi[i]) isH = false;
         if(lo[i-k] <= lo[i] || lo[i+k] <= lo[i]) isL = false;
      }
      if(isH && !isL) { ArrayResize(raw,rc+1); raw[rc].time=tm[i]; raw[rc].price=hi[i]; raw[rc].isHigh=true;  rc++; }
      else if(isL && !isH) { ArrayResize(raw,rc+1); raw[rc].time=tm[i]; raw[rc].price=lo[i]; raw[rc].isHigh=false; rc++; }
   }
   if(rc < 1) return false;

   // Alternating filter
   SPivot filt[]; int fc = 0;
   ArrayResize(filt,1); filt[0]=raw[0]; fc=1;
   for(int i = 1; i < rc; i++)
   {
      if(raw[i].isHigh == filt[fc-1].isHigh)
      {
         if( raw[i].isHigh && raw[i].price > filt[fc-1].price) filt[fc-1]=raw[i];
         if(!raw[i].isHigh && raw[i].price < filt[fc-1].price) filt[fc-1]=raw[i];
      }
      else { ArrayResize(filt,fc+1); filt[fc]=raw[i]; fc++; }
   }

   // Keep only HH / LL
   int oc = 0;
   for(int i = 1; i < fc; i++)
   {
      bool isHH =  filt[i].isHigh && filt[i].price > filt[i-1].price;
      bool isLL  = !filt[i].isHigh && filt[i].price < filt[i-1].price;
      if(isHH || isLL)
      {
         ArrayResize(out, oc+1);
         out[oc] = filt[i];
         oc++;
      }
   }
   return (oc > 0);
}

//+------------------------------------------------------------------+
// Find last M5 impulse leg ending at or before tPivot
// pivotIsHH=true  → want bear leg (HH→LL): prev=HH, cur=LL
// pivotIsHH=false → want bull leg (LL→HH): prev=LL, cur=HH
//+------------------------------------------------------------------+
bool FindImpulseLeg(datetime tPivot, bool pivotIsHH,
                    datetime &legStart, datetime &legEnd,
                    double &legLow,   double &legHigh)
{
   SPivot imp[];
   if(!GetPivots(InpImpulseTF, InpPivotBars, InpMaxBarsImp, imp)) return false;
   int n = ArraySize(imp);

   for(int i = n-1; i >= 1; i--)
   {
      if(imp[i].time > tPivot) continue;

      bool legIsBull = imp[i].isHigh && !imp[i-1].isHigh;  // LL→HH
      bool wantBull  = !pivotIsHH;

      if(wantBull != legIsBull) continue;

      legStart = imp[i-1].time;
      legEnd   = imp[i].time;
      if(imp[i].isHigh)   // bull leg
      {
         legLow  = imp[i-1].price;
         legHigh = imp[i].price;
      }
      else                 // bear leg
      {
         legHigh = imp[i-1].price;
         legLow  = imp[i].price;
      }
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
void DrawHollowBox(string name, datetime t1, double top,
                   datetime t2, double bottom,
                   color clr, int width)
{
   if(ObjectFind(0, name) >= 0) ObjectDelete(0, name);
   if(!ObjectCreate(0, name, OBJ_RECTANGLE, 0, t1, top, t2, bottom)) return;
   ObjectSetInteger(0, name, OBJPROP_COLOR,     clr);
   ObjectSetInteger(0, name, OBJPROP_WIDTH,     width);
   ObjectSetInteger(0, name, OBJPROP_FILL,      false);   // hollow
   ObjectSetInteger(0, name, OBJPROP_BACK,      false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE,false);
   ObjectSetInteger(0, name, OBJPROP_RAY_RIGHT, false);
}

//+------------------------------------------------------------------+
int OnInit()
{
   IndicatorSetString(INDICATOR_SHORTNAME, "PrePivotBox MTF v1.10");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, "PPB_");
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
   if(rates_total < 10) return 0;

   static datetime lastBar[3] = {0,0,0};
   ENUM_TIMEFRAMES tfs[3]  = {InpParentTF1, InpParentTF2, InpParentTF3};
   bool            uses[3] = {InpUseParent1, InpUseParent2, InpUseParent3};

   bool needRecalc = (prev_calculated == 0);
   for(int s = 0; s < 3; s++)
   {
      if(!uses[s]) continue;
      datetime t0 = iTime(_Symbol, tfs[s], 0);
      if(t0 != lastBar[s]) { needRecalc = true; lastBar[s] = t0; }
   }
   if(!needRecalc) return rates_total;

   ObjectsDeleteAll(0, "PPB_");

   for(int s = 0; s < 3; s++)
   {
      if(!uses[s]) continue;
      ENUM_TIMEFRAMES ptf = tfs[s];
      string tfTag = EnumToString(ptf);
      StringReplace(tfTag, "PERIOD_", "");

      SPivot pivots[];
      if(!GetPivots(ptf, InpPivotBars, InpMaxBarsParent, pivots)) continue;

      color clr = (s==0) ? InpColorTF1 : (s==1) ? InpColorTF2 : InpColorTF3;
      int pCount = ArraySize(pivots);
      for(int p = 0; p < pCount; p++)
      {
         datetime tPivot  = pivots[p].time;
         bool     pivotHH = pivots[p].isHigh;

         datetime legStart, legEnd;
         double   legLow, legHigh;
         if(!FindImpulseLeg(tPivot, pivotHH, legStart, legEnd, legLow, legHigh)) continue;

         double boxTop    = legHigh;
         double boxBottom = legLow;


         // Find box right edge:
         // Bull box (before LL): extend until any candle HIGH > boxTop
         // Bear box (before HH): extend until any candle LOW  < boxBottom
         datetime boxRight = time[rates_total - 1]; // default: current bar
         for(int i = 0; i < rates_total; i++)
         {
            if(time[i] < legEnd) continue;  // search from leg end onwards

            if(!pivotHH && high[i] > boxTop)    // bull box broken upward
            {
               boxRight = time[i];
               break;
            }
            if(pivotHH  && low[i]  < boxBottom) // bear box broken downward
            {
               boxRight = time[i];
               break;
            }
         }

         string boxName = "PPB_BOX_" + tfTag + "_" + IntegerToString((int)tPivot);
         DrawHollowBox(boxName, legStart, boxTop, boxRight, boxBottom, clr, InpLineWidth);

         if(InpShowLabels)
         {
            string lblName = "PPB_LBL_" + tfTag + "_" + IntegerToString((int)tPivot);
            if(ObjectFind(0, lblName) >= 0) ObjectDelete(0, lblName);
            ObjectCreate(0, lblName, OBJ_TEXT, 0, legStart, boxTop);
            ObjectSetString(0, lblName, OBJPROP_TEXT,
                            tfTag + (pivotHH ? " HH" : " LL"));
            ObjectSetInteger(0, lblName, OBJPROP_COLOR,    clr);
            ObjectSetInteger(0, lblName, OBJPROP_FONTSIZE, 7);
            ObjectSetInteger(0, lblName, OBJPROP_ANCHOR,   ANCHOR_BOTTOM);
         }
      }
   }
   return rates_total;
}
//+------------------------------------------------------------------+
