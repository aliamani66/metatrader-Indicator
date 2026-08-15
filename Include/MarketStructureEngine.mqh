//+------------------------------------------------------------------+
//| MarketStructureEngine.mqh                                        |
//| Shared Core Engine for MarketStructure_v2 and Flag Indicators    |
//| Balanced Macro Swings Engine                                     |
//+------------------------------------------------------------------+
#property copyright "Market Structure Engine"
#property link      ""
#property version   "3.00"

struct SPivot
{
   int      bar;
   datetime time;
   double   price;
   bool     isHigh;
   string   label;       // "HH", "LH", "LL", "HL"
   color    clr;
};

//+------------------------------------------------------------------+
//| Universal Alternating Swings Engine                              |
//+------------------------------------------------------------------+
bool BuildAlternatingPivots(ENUM_TIMEFRAMES tf, int sBars, int maxBars, SPivot &pivots[])
{
   ArrayResize(pivots, 0);

   datetime time[];
   double   high[], low[], close[], open[];
   ArraySetAsSeries(time,  false);
   ArraySetAsSeries(high,  false);
   ArraySetAsSeries(low,   false);
   ArraySetAsSeries(close, false);
   ArraySetAsSeries(open,  false);

   int rates_total = CopyTime(_Symbol, tf, 0, maxBars, time);
   if(rates_total < sBars * 2 + 5) return false;
   CopyHigh(_Symbol, tf, 0, rates_total, high);
   CopyLow(_Symbol, tf, 0, rates_total, low);
   CopyClose(_Symbol, tf, 0, rates_total, close);
   CopyOpen(_Symbol, tf, 0, rates_total, open);

   int startBar = MathMax(sBars, rates_total - maxBars);
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

   if(rCount < 2) return false;

   //--- Step 2: Build Alternating Swings Sequence (Balanced Intra-Swing Recovery)
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

            // Real pullback valley between two Highs
            if(minB > last.bar && minP < last.price && cur.price > minP && (cur.bar - last.bar >= 3))
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

            // Real bounce peak between two Lows
            if(maxB > last.bar && maxP > last.price && cur.price < maxP && (cur.bar - last.bar >= 3))
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

   if(sCount < 2) return false;

   //--- Step 3: GUARANTEED ABSOLUTE EXTREME LOCK
   for(int i = 1; i < sCount - 1; i++)
   {
      int bPrev = swings[i - 1].bar;
      int bNext = swings[i + 1].bar;
      if(bPrev >= bNext) continue;

      if(!swings[i].isHigh)
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
      else
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
               swings[i].label = "HH";
            else
               swings[i].label = "LH";
         }
         else
         {
            if(swings[i].price <= prevSame.price)
               swings[i].label = "LL";
            else
               swings[i].label = "HL";
         }
      }
      else
      {
         swings[i].label = swings[i].isHigh ? "H" : "L";
      }
   }

   ArrayResize(pivots, sCount);
   for(int i = 0; i < sCount; i++)
      pivots[i] = swings[i];

   return (sCount >= 2);
}
