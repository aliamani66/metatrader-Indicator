//+------------------------------------------------------------------+
//| FlagRZ.mq5                                                        |
//| Combined Flag + ReactionZone Standalone Indicator v4.0           |
//|                                                                    |
//| این اندیکاتور کاملاً مستقل است:                                   |
//| - خودش پیووت‌ها را پیدا می‌کند                                   |
//| - خودش باکس‌های Flag را می‌کشد                                   |
//| - روی آنها ReactionZone اضافه می‌کند                             |
//| - نیازی به اندیکاتور Flag ندارد                                  |
//+------------------------------------------------------------------+
#property version   "4.00"
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

//+------------------------------------------------------------------+
//| Input Parameters                                                  |
//+------------------------------------------------------------------+
// تایم‌فریم‌ها
input bool   InpUseM1  = true;           // نمایش M1
input bool   InpUseM5  = true;           // نمایش M5
input bool   InpUseM15 = true;           // نمایش M15

// تنظیمات پیووت
input int    InpPivotBars  = 3;          // تعداد بارهای پیووت
input int    InpMaxBars    = 3000;       // حداکثر بارهای بررسی

// تنظیمات نمایش
input int    InpLineWidth  = 3;          // ضخامت خط
input bool   InpShowLabel  = true;       // نمایش برچسب
input int    InpLabelFontSize = 8;       // اندازه فونت
input bool   InpShowShortBoxes = true;   // نمایش باکس‌های کوتاه

//--- Pivot structure
struct SPivot { datetime time; double price; bool isHigh; };

//--- ReactionZone structure
struct SReactionZone
{
   string  boxName;
   datetime timeStart;
   double  priceTop;
   double  priceBottom;
   bool    isBullish;
   bool    isBroken;
   datetime breakTime;
   string  label;
};

SReactionZone reactionZones[];
int zoneCount = 0;
bool boxesDrawn = false; // فلگ برای جلوگیری از رفرش

//+------------------------------------------------------------------+
//| Build pivots: returns ALTERNATING High/Low pivots                 |
//+------------------------------------------------------------------+
bool BuildAlternatingPivots(ENUM_TIMEFRAMES tf, int pivotBars, int maxBars, SPivot &pivots[])
{
   ArrayResize(pivots, 0);

   int availBars = iBars(_Symbol, tf);
   if(availBars <= 0) return false;
   int reqBars = MathMin(availBars, maxBars);
   if(reqBars < pivotBars * 2 + 3) return false;

   double high[], low[]; datetime tm[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low,  true);
   ArraySetAsSeries(tm,   true);

   int copied = CopyHigh(_Symbol, tf, 0, reqBars, high);
   if(copied < pivotBars * 2 + 3) return false;
   CopyLow(_Symbol, tf, 0, copied, low);
   CopyTime(_Symbol, tf, 0, copied, tm);

   ArraySetAsSeries(high, false);
   ArraySetAsSeries(low,  false);
   ArraySetAsSeries(tm,   false);

   int n = copied;

   // Find all fractal pivots
   SPivot raw[]; int rc = 0;
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
         ArrayResize(raw, rc + 1);
         raw[rc].time = tm[i]; raw[rc].price = high[i]; raw[rc].isHigh = true;
         rc++;
      }
      else if(isL && !isH)
      {
         ArrayResize(raw, rc + 1);
         raw[rc].time = tm[i]; raw[rc].price = low[i]; raw[rc].isHigh = false;
         rc++;
      }
   }
   if(rc < 2) return false;

   // Alternating filter
   ArrayResize(pivots, 1);
   pivots[0] = raw[0];
   int pCount = 1;

   for(int i = 1; i < rc; i++)
   {
      SPivot last = pivots[pCount - 1];
      SPivot cur  = raw[i];
      if(cur.isHigh == last.isHigh)
      {
         if(cur.isHigh && cur.price > last.price) pivots[pCount - 1] = cur;
         else if(!cur.isHigh && cur.price < last.price) pivots[pCount - 1] = cur;
      }
      else
      {
         ArrayResize(pivots, pCount + 1);
         pivots[pCount] = cur;
         pCount++;
      }
   }
   
   return (pCount >= 2);
}

//+------------------------------------------------------------------+
//| Find bar index                                                    |
//+------------------------------------------------------------------+
int FindBarIndex(const datetime &chartTime[], int ratesTotal, datetime t)
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
//| Draw hollow box                                                   |
//+------------------------------------------------------------------+
void DrawHollowBox(string name, datetime t1, double top, datetime t2, double bottom,
                   color clr, int width, bool rayRight = false)
{
   if(ObjectFind(0, name) >= 0) ObjectDelete(0, name);
   if(!ObjectCreate(0, name, OBJ_RECTANGLE, 0, t1, top, t2, bottom)) return;
   ObjectSetInteger(0, name, OBJPROP_COLOR,      clr);
   ObjectSetInteger(0, name, OBJPROP_WIDTH,      width);
   ObjectSetInteger(0, name, OBJPROP_FILL,       false);
   ObjectSetInteger(0, name, OBJPROP_BACK,       false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_RAY_RIGHT,  rayRight);
}

//+------------------------------------------------------------------+
//| Draw label                                                        |
//+------------------------------------------------------------------+
void DrawLabel(string name, datetime t, double price, string text, color clr)
{
   if(!InpShowLabel) return;
   if(ObjectFind(0, name) >= 0) ObjectDelete(0, name);
   if(!ObjectCreate(0, name, OBJ_TEXT, 0, t, price)) return;
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, InpLabelFontSize);
   ObjectSetInteger(0, name, OBJPROP_BACK, false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
}

//+------------------------------------------------------------------+
//| Generate random bright color                                     |
//+------------------------------------------------------------------+
color GetRandomBrightColor(int seed)
{
   MathSrand(seed);
   
   color colors[] = {
      clrRed, clrLime, clrYellow, clrCyan, clrMagenta,
      clrOrange, clrGold, clrAqua, clrHotPink, clrSpringGreen,
      clrDeepSkyBlue, clrOrangeRed, clrYellowGreen, clrLightCoral,
      clrMediumSpringGreen, clrDodgerBlue, clrTomato, clrLightGreen
   };
   
   int index = MathRand() % ArraySize(colors);
   return colors[index];
}

//+------------------------------------------------------------------+
//| TF Name                                                           |
//+------------------------------------------------------------------+
string TFName(ENUM_TIMEFRAMES tf)
{
   if(tf == PERIOD_M1) return "M1";
   if(tf == PERIOD_M5) return "M5";
   if(tf == PERIOD_M15) return "M15";
   if(tf == PERIOD_H1) return "H1";
   if(tf == PERIOD_H4) return "H4";
   if(tf == PERIOD_D1) return "D1";
   if(tf == PERIOD_W1) return "W1";
   string s = EnumToString(tf);
   StringReplace(s, "PERIOD_", "");
   return s;
}

//+------------------------------------------------------------------+
//| Process timeframe and create boxes - با منطق کامل Flag           |
//+------------------------------------------------------------------+
void ProcessTF(ENUM_TIMEFRAMES tf, int pivotBars, color boxColor,
               const datetime &chartTime[], const double &chartHigh[], const double &chartLow[],
               int ratesTotal)
{
   SPivot pivots[];
   if(!BuildAlternatingPivots(tf, pivotBars, InpMaxBars, pivots)) return;

   string tfTag = TFName(tf);
   int count = ArraySize(pivots);
   
   if(count < 3) return;

   // پردازش هر High که Low بعد از آن دارد
   for(int i = 1; i < count; i++)
   {
      SPivot cur = pivots[i];
      
      // فقط High ها را در نظر بگیر
      if(!cur.isHigh) continue;
      
      // Low بعد از این High را پیدا کن
      int lowIdx = -1;
      for(int j = i + 1; j < count; j++)
      {
         if(!pivots[j].isHigh) 
         {
            lowIdx = j;
            break;
         }
      }
      
      if(lowIdx == -1) continue;
      
      SPivot curLow = pivots[lowIdx];
      double highPrice = cur.price;
      double lowPrice = curLow.price;
      
      // High قبلی و بعدی را پیدا کن
      double prevHigh = -1, nextHigh = -1;
      double prevLow = -1, nextLow = -1;
      datetime prevLowTime = 0;
      
      // High قبلی
      for(int j = i - 1; j >= 0; j--)
      {
         if(pivots[j].isHigh) 
         {
            prevHigh = pivots[j].price;
            break;
         }
      }
      
      // Low قبلی
      for(int j = i - 1; j >= 0; j--)
      {
         if(!pivots[j].isHigh) 
         {
            prevLow = pivots[j].price;
            prevLowTime = pivots[j].time;
            break;
         }
      }
      
      // High بعدی
      for(int j = lowIdx + 1; j < count; j++)
      {
         if(pivots[j].isHigh) 
         {
            nextHigh = pivots[j].price;
            break;
         }
      }
      
      // Low بعدی
      for(int j = lowIdx + 1; j < count; j++)
      {
         if(!pivots[j].isHigh) 
         {
            nextLow = pivots[j].price;
            break;
         }
      }
      
      // High و Low دوم بعدی
      double nextHigh2 = -1, nextLow2 = -1;
      int nextLowIdx = -1;
      
      for(int j = lowIdx + 1; j < count; j++)
      {
         if(!pivots[j].isHigh) 
         {
            nextLowIdx = j;
            break;
         }
      }
      
      if(nextLowIdx > 0)
      {
         for(int j = nextLowIdx + 1; j < count; j++)
         {
            if(pivots[j].isHigh) 
            {
               nextHigh2 = pivots[j].price;
               break;
            }
         }
         
         for(int j = nextLowIdx + 1; j < count; j++)
         {
            if(!pivots[j].isHigh) 
            {
               nextLow2 = pivots[j].price;
               break;
            }
         }
      }
      
      // ========== شرط‌های جدید: ابتدا بررسی می‌شوند ==========
      
      // فیلتر 1: اگر High جاری از قبلی و بعدی بالاتر، Low جاری از بعدی پایین‌تر، و Low قبلی از جاری پایین‌تر → باکس نکش
      if(prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
      {
         if(highPrice > prevHigh && highPrice > nextHigh && lowPrice < nextLow && prevLow < lowPrice)
         {
            continue;
         }
      }
      
      // فیلتر 2: اگر High جاری از همه بالاتر و Low جاری هم از همه بالاتر → Higher High معمولی → باکس نکش
      if(prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
      {
         if(highPrice > prevHigh && highPrice > nextHigh && lowPrice > prevLow && lowPrice > nextLow)
         {
            continue;
         }
      }
      
      // شرط جدید 1: پیووت مستقل V-shape
      bool isIndependentPivot = false;
      if(prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
      {
         if(nextHigh > highPrice && nextLow > lowPrice && prevHigh < highPrice && prevLow > lowPrice)
         {
            isIndependentPivot = true;
         }
      }
      
      // شرط جدید 2: پیووت top در روند صعودی
      bool isUptrendTop = false;
      if(prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
      {
         if(highPrice > prevHigh && lowPrice > prevLow && nextHigh < highPrice && nextLow > prevLow)
         {
            isUptrendTop = true;
         }
      }
      
      bool skipOldConditions = (isIndependentPivot || isUptrendTop);
      
      // ========== شرط‌های قبلی (فقط اگر شرط‌های جدید برقرار نباشند) ==========
      
      if(!skipOldConditions)
      {
         // شرط 1: بررسی downtrend و reversal
         if(nextHigh > 0 && prevHigh > 0 && nextHigh < highPrice && prevHigh < highPrice)
         {
            bool downtrend = (prevLow > 0 && highPrice < prevHigh && lowPrice < prevLow);
            
            if(!downtrend)
            {
               continue;
            }
            
            bool reversal1 = (nextLow > 0 && nextHigh > highPrice && nextLow > lowPrice);
            bool reversal2 = false;
            if(nextHigh2 > 0 && nextLow2 > 0)
            {
               reversal2 = (nextHigh2 > nextHigh && nextLow2 > nextLow);
            }
            
            if(reversal1 && reversal2)
            {
               double move1 = nextHigh - highPrice;
               double move2 = nextHigh2 - nextHigh;
               
               if(move2 >= move1 * 0.5)
               {
                  continue;
               }
            }
         }
         
         // شرط استثنا: inside bar معتبر
         bool isValidInsideBar = false;
         if(prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
         {
            if(highPrice < prevHigh && highPrice < nextHigh && lowPrice > prevLow && lowPrice > nextLow)
            {
               isValidInsideBar = true;
            }
         }
         
         // فیلتر کندل محدود
         if(!isValidInsideBar && !isIndependentPivot && !isUptrendTop && prevHigh > 0 && prevLow > 0 && nextLow > 0)
         {
            if(highPrice < prevHigh && lowPrice > prevLow && lowPrice > nextLow)
            {
               continue;
            }
         }
         
         // شرط 2: بررسی uptrend و reversal نزولی
         if(nextLow > 0 && prevLow > 0 && nextLow > lowPrice && prevLow > lowPrice)
         {
            bool uptrend = (prevHigh > 0 && highPrice > prevHigh && lowPrice > prevLow);
            
            if(uptrend)
            {
               bool reversal1 = (nextHigh > 0 && nextHigh < highPrice && nextLow < lowPrice);
               bool reversal2 = false;
               if(nextHigh2 > 0 && nextLow2 > 0)
               {
                  reversal2 = (nextHigh2 < nextHigh && nextLow2 < nextLow);
               }
               
               if(reversal1 && reversal2)
               {
                  double move1 = highPrice - nextHigh;
                  double move2 = nextHigh - nextHigh2;
                  
                  if(move2 >= move1 * 0.5)
                  {
                     continue;
                  }
               }
            }
         }
         
         // شرط 3: Inside bar نزولی
         if(prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
         {
            bool isInsideBar = (highPrice < prevHigh && lowPrice > prevLow);
            
            if(isInsideBar)
            {
               bool strongBearish = (nextHigh < highPrice && nextLow < lowPrice);
               
               if(strongBearish && nextHigh2 > 0 && nextLow2 > 0)
               {
                  bool strongBearish2 = (nextHigh2 < nextHigh && nextLow2 < nextLow);
                  
                  if(strongBearish2)
                  {
                     continue;
                  }
               }
            }
         }
      }
      
      // تعیین نوع روند و محدوده باکس
      bool isBullish = false;
      double boxTop = highPrice;
      double boxBottom = lowPrice;
      
      if(isIndependentPivot || isUptrendTop)
      {
         isBullish = isUptrendTop;
         boxTop = highPrice;
         boxBottom = lowPrice;
      }
      else if(!skipOldConditions)
      {
         // شرط ویژه: اگر High جاری < High قبلی و Low جاری < Low قبلی
         if(prevHigh > 0 && prevLow > 0 && highPrice < prevHigh && lowPrice < prevLow)
         {
            isBullish = false;
            boxTop = highPrice;
            boxBottom = prevLow;
         }
         else if(nextHigh > 0 && nextLow > 0)
         {
            if(nextHigh > highPrice)
            {
               isBullish = true;
            }
            else if(nextHigh < highPrice)
            {
               isBullish = false;
            }
            else
            {
               continue;
            }
            
            boxTop = highPrice;
            boxBottom = lowPrice;
         }
         else
         {
            continue;
         }
      }
      
      double boxHeight = boxTop - boxBottom;
      if(boxHeight <= 0) continue;
      
      int idxHigh = FindBarIndex(chartTime, ratesTotal, cur.time);
      int idxLow = FindBarIndex(chartTime, ratesTotal, curLow.time);
      if(idxHigh < 0 || idxLow < 0) continue;
      
      int idxPrevLow = -1;
      if(!isBullish && boxBottom == prevLow && prevLow > 0 && prevLowTime > 0)
      {
         idxPrevLow = FindBarIndex(chartTime, ratesTotal, prevLowTime);
      }

      // امتداد به عقب
      int leftIdx = idxHigh;
      for(int k = idxHigh - 1; k >= 0; k--)
      {
         bool candleInsideBox = (chartLow[k] >= boxBottom && chartHigh[k] <= boxTop);
         if(!candleInsideBox)
         {
            leftIdx = k + 1;
            break;
         }
         leftIdx = k;
      }
      if(leftIdx > 0) leftIdx--;

      // امتداد به جلو
      int rightIdx = idxLow;
      
      if(idxPrevLow >= 0 && !isBullish && boxBottom == prevLow)
      {
         rightIdx = idxPrevLow;
         for(int k = idxPrevLow + 1; k < ratesTotal; k++)
         {
            if(chartLow[k] < prevLow)
            {
               rightIdx = k - 1;
               break;
            }
            rightIdx = k;
         }
      }
      else
      {
         for(int k = idxLow + 1; k < ratesTotal; k++)
         {
            if(chartHigh[k] < boxBottom)
            {
               rightIdx = k - 1;
               break;
            }
            bool candleInsideBox = (chartLow[k] >= boxBottom && chartHigh[k] <= boxTop);
            if(!candleInsideBox)
            {
               rightIdx = k - 1;
               break;
            }
            rightIdx = k;
         }
      }
      if(rightIdx < ratesTotal - 1) rightIdx++;

      datetime t1 = chartTime[leftIdx];
      datetime t2 = chartTime[rightIdx];
      
      string boxType = isBullish ? "B" : "R";
      string boxName = "FLAGRZ_BOX_" + tfTag + "_P" + IntegerToString(InpPivotBars) + "_" + boxType + "_" + IntegerToString((int)cur.time);
      
      // رسم باکس Flag
      DrawHollowBox(boxName, t1, boxTop, t2, boxBottom, boxColor, 1, false);
      
      // اضافه به ReactionZones
      ArrayResize(reactionZones, zoneCount + 1);
      reactionZones[zoneCount].boxName = boxName;
      reactionZones[zoneCount].timeStart = t2;
      reactionZones[zoneCount].priceTop = boxTop;
      reactionZones[zoneCount].priceBottom = boxBottom;
      reactionZones[zoneCount].isBullish = isBullish;
      reactionZones[zoneCount].isBroken = false;
      reactionZones[zoneCount].breakTime = 0;
      reactionZones[zoneCount].label = IntegerToString(InpPivotBars) + tfTag;
      
      zoneCount++;
   }
}

//+------------------------------------------------------------------+
//| Check breakouts                                                   |
//+------------------------------------------------------------------+
void CheckBreakouts(const double &high[], const double &low[], const datetime &time[], int rates_total)
{
   for(int i = 0; i < zoneCount; i++)
   {
      if(reactionZones[i].isBroken) continue;
      
      datetime startTime = reactionZones[i].timeStart;
      
      int startIdx = -1;
      for(int t = 0; t < rates_total; t++)
      {
         if(time[t] >= startTime)
         {
            startIdx = t;
            break;
         }
      }
      
      if(startIdx < 0) continue;
      
      for(int bar = startIdx; bar < rates_total; bar++)
      {
         double barHigh = high[bar];
         double barLow = low[bar];
         
         if(reactionZones[i].isBullish)
         {
            if(barLow < reactionZones[i].priceBottom)
            {
               reactionZones[i].isBroken = true;
               reactionZones[i].breakTime = time[bar];
               break;
            }
         }
         else
         {
            if(barHigh > reactionZones[i].priceTop)
            {
               reactionZones[i].isBroken = true;
               reactionZones[i].breakTime = time[bar];
               break;
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Draw reaction zones                                               |
//+------------------------------------------------------------------+
void DrawReactionZones(const datetime &time[], int rates_total)
{
   datetime liveTime = time[rates_total - 1];
   
   for(int i = 0; i < zoneCount; i++)
   {
      string zoneName = "RZ_" + reactionZones[i].boxName;
      
      datetime startTime = reactionZones[i].timeStart;
      datetime endTime;
      
      if(reactionZones[i].isBroken)
      {
         endTime = reactionZones[i].breakTime;
      }
      else
      {
         endTime = liveTime;
      }
      
      int timeDiff = (int)(endTime - startTime);
      if(timeDiff < 900 && !InpShowShortBoxes) continue;
      
      int seed = (int)reactionZones[i].timeStart + i;
      color boxColor = GetRandomBrightColor(seed);
      
      DrawHollowBox(zoneName,
                    startTime,
                    reactionZones[i].priceTop,
                    endTime,
                    reactionZones[i].priceBottom,
                    boxColor,
                    InpLineWidth,
                    false);
      
      string labelName = zoneName + "_LBL";
      double labelPrice = (reactionZones[i].priceTop + reactionZones[i].priceBottom) / 2;
      DrawLabel(labelName, endTime, labelPrice, reactionZones[i].label, boxColor);
   }
}

//+------------------------------------------------------------------+
//| Initialization                                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   IndicatorSetString(INDICATOR_SHORTNAME, "FlagRZ Standalone v4.0");
   boxesDrawn = false;
   Print("✅ FlagRZ v4.0 - اندیکاتور مستقل آماده است");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Deinitialization                                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, "FLAGRZ_");
   ObjectsDeleteAll(0, "RZ_");
   boxesDrawn = false;
}

//+------------------------------------------------------------------+
//| OnCalculate                                                       |
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
   
   // فقط یک بار باکس‌ها را بکش
   if(!boxesDrawn || prev_calculated == 0)
   {
      Print("🎨 FlagRZ: شروع رسم باکس‌ها...");
      
      ObjectsDeleteAll(0, "FLAGRZ_");
      ObjectsDeleteAll(0, "RZ_");
      ArrayResize(reactionZones, 0);
      zoneCount = 0;
      
      // پردازش M1
      if(InpUseM1)
      {
         Print("🔍 پردازش M1...");
         ProcessTF(PERIOD_M1, InpPivotBars, clrYellow, time, high, low, rates_total);
      }
      
      // پردازش M5
      if(InpUseM5)
      {
         Print("🔍 پردازش M5...");
         ProcessTF(PERIOD_M5, InpPivotBars, clrAqua, time, high, low, rates_total);
      }
      
      // پردازش M15
      if(InpUseM15)
      {
         Print("🔍 پردازش M15...");
         ProcessTF(PERIOD_M15, InpPivotBars, clrLime, time, high, low, rates_total);
      }
      
      Print("✅ ", zoneCount, " باکس رسم شد");
      
      if(zoneCount > 0)
      {
         CheckBreakouts(high, low, time, rates_total);
         DrawReactionZones(time, rates_total);
      }
      
      boxesDrawn = true;
   }
   else if(prev_calculated < rates_total && zoneCount > 0)
   {
      // فقط بررسی شکست‌ها در کندل‌های جدید
      CheckBreakouts(high, low, time, rates_total);
      DrawReactionZones(time, rates_total);
   }
   
   return rates_total;
}

//+------------------------------------------------------------------+
//| Chart event                                                       |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
{
   // رفرش با F5
   if(id == CHARTEVENT_KEYDOWN && lparam == 116)
   {
      boxesDrawn = false;
      Print("🔄 رفرش دستی...");
      ChartRedraw();
   }
}
//+------------------------------------------------------------------+
