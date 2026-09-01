//+------------------------------------------------------------------+
//| RSFLAG.mq5                                                        |
//| علامت‌گذاری High هایی که Flag باکس نمی‌کشد                       |
//+------------------------------------------------------------------+
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

input int InpPivotBars = 3;
input int InpMaxBars = 3000;

struct SPivot { datetime time; double price; bool isHigh; };
struct SBox { datetime timeLeft; datetime timeRight; double priceTop; double priceBottom; };
bool processed = false;

//+------------------------------------------------------------------+
bool BuildAlternatingPivots(ENUM_TIMEFRAMES tf, int pivotBars, int maxBars, SPivot &pivots[])
{
   ArrayResize(pivots, 0);
   int availBars = iBars(_Symbol, tf);
   if(availBars <= 0) return false;
   int reqBars = MathMin(availBars, maxBars);
   if(reqBars < pivotBars * 2 + 3) return false;

   double high[], low[]; datetime tm[];
   ArraySetAsSeries(high, true); ArraySetAsSeries(low, true); ArraySetAsSeries(tm, true);

   int copied = CopyHigh(_Symbol, tf, 0, reqBars, high);
   if(copied < pivotBars * 2 + 3) return false;
   CopyLow(_Symbol, tf, 0, copied, low);
   CopyTime(_Symbol, tf, 0, copied, tm);

   ArraySetAsSeries(high, false); ArraySetAsSeries(low, false); ArraySetAsSeries(tm, false);

   SPivot raw[]; int rc = 0;
   for(int i = pivotBars; i < copied - pivotBars; i++)
   {
      bool isH = true, isL = true;
      for(int k = 1; k <= pivotBars; k++)
      {
         if(high[i-k] >= high[i] || high[i+k] >= high[i]) isH = false;
         if(low[i-k] <= low[i] || low[i+k] <= low[i]) isL = false;
      }
      if(isH && !isL) { ArrayResize(raw, rc + 1); raw[rc].time = tm[i]; raw[rc].price = high[i]; raw[rc].isHigh = true; rc++; }
      else if(isL && !isH) { ArrayResize(raw, rc + 1); raw[rc].time = tm[i]; raw[rc].price = low[i]; raw[rc].isHigh = false; rc++; }
   }
   if(rc < 2) return false;

   ArrayResize(pivots, 1); pivots[0] = raw[0]; int pCount = 1;
   for(int i = 1; i < rc; i++)
   {
      SPivot last = pivots[pCount - 1], cur = raw[i];
      if(cur.isHigh == last.isHigh)
      {
         if(cur.isHigh && cur.price > last.price) pivots[pCount - 1] = cur;
         else if(!cur.isHigh && cur.price < last.price) pivots[pCount - 1] = cur;
      }
      else { ArrayResize(pivots, pCount + 1); pivots[pCount] = cur; pCount++; }
   }
   return (pCount >= 2);
}

void DrawArrow(string name, datetime time, double price, color clr)
{
   if(ObjectFind(0, name) >= 0) ObjectDelete(0, name);
   if(!ObjectCreate(0, name, OBJ_ARROW, 0, time, price)) return;
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_ARROWCODE, 159);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, 3);
   ObjectSetInteger(0, name, OBJPROP_BACK, false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
}

void DrawBox(string name, datetime t1, double top, datetime t2, double bottom, color clr)
{
   if(ObjectFind(0, name) >= 0) ObjectDelete(0, name);
   if(!ObjectCreate(0, name, OBJ_RECTANGLE, 0, t1, top, t2, bottom)) return;
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_WIDTH, 2);
   ObjectSetInteger(0, name, OBJPROP_FILL, false);
   ObjectSetInteger(0, name, OBJPROP_BACK, false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
}

bool GetM5BoxesFromFlag(SBox &boxes[])
{
   ArrayResize(boxes, 0);
   int boxCount = 0;
   
   Print("🔍 شروع جستجوی باکس‌های M5 از Flag...");
   Print("📊 تعداد کل اشیاء: ", ObjectsTotal(0, 0, OBJ_RECTANGLE));
   
   // پیدا کردن همه باکس‌های FLAG که M5 هستند
   for(int i = 0; i < ObjectsTotal(0, 0, OBJ_RECTANGLE); i++)
   {
      string objName = ObjectName(0, i, 0, OBJ_RECTANGLE);
      
      Print("  Object #", i, ": ", objName);
      
      // چک کنیم اسم باکس چیه - باید FLAG_BOX باشه
      if(StringFind(objName, "FLAG_BOX_") >= 0)
      {
         Print("    ✓ این یک باکس FLAG است");
         
         // فقط باکس‌های M5
         if(StringFind(objName, "M5") >= 0)
         {
            Print("      ✓ این یک باکس M5 است!");
            
            datetime t1 = (datetime)ObjectGetInteger(0, objName, OBJPROP_TIME, 0);
            datetime t2 = (datetime)ObjectGetInteger(0, objName, OBJPROP_TIME, 1);
            double p1 = ObjectGetDouble(0, objName, OBJPROP_PRICE, 0);
            double p2 = ObjectGetDouble(0, objName, OBJPROP_PRICE, 1);
            
            ArrayResize(boxes, boxCount + 1);
            boxes[boxCount].timeLeft = t1;
            boxes[boxCount].timeRight = t2;
            boxes[boxCount].priceTop = MathMax(p1, p2);
            boxes[boxCount].priceBottom = MathMin(p1, p2);
            
            Print("        ✅ باکس M5 اضافه شد #", boxCount, ": ", objName);
            Print("           t1=", t1, " t2=", t2);
            Print("           top=", boxes[boxCount].priceTop, " bottom=", boxes[boxCount].priceBottom);
            boxCount++;
         }
      }
   }
   
   Print("✅ مجموع باکس‌های M5 پیدا شده: ", boxCount);
   return (boxCount > 0);
}

void ProcessM15()
{
   SPivot pivots[];
   if(!BuildAlternatingPivots(PERIOD_M15, InpPivotBars, InpMaxBars, pivots)) return;

   int count = ArraySize(pivots);
   Print("📊 تعداد pivot M15: ", count);
   
   // دریافت pivot های M5 برای رسم باکس
   SPivot pivotsM5[];
   if(!BuildAlternatingPivots(PERIOD_M5, 3, InpMaxBars, pivotsM5))
   {
      Print("❌ خطا در ساخت pivot های M5");
      return;
   }
   int m5Count = ArraySize(pivotsM5);
   Print("📊 تعداد pivot M5: ", m5Count);
   
   int rejectedHighCount = 0;
   int rejectedLowCount = 0;
   int independentPeakCount = 0;
   int independentValleyCount = 0;

   // پردازش High ها
   for(int i = 1; i < count; i++)
   {
      SPivot cur = pivots[i];
      if(!cur.isHigh) continue;
      
      int lowIdx = -1;
      for(int j = i + 1; j < count; j++) { if(!pivots[j].isHigh) { lowIdx = j; break; } }
      if(lowIdx == -1) continue;
      
      SPivot curLow = pivots[lowIdx];
      double highPrice = cur.price, lowPrice = curLow.price;
      double prevHigh = -1, nextHigh = -1, prevLow = -1, nextLow = -1;
      
      for(int j = i - 1; j >= 0; j--) { if(pivots[j].isHigh) { prevHigh = pivots[j].price; break; } }
      for(int j = i - 1; j >= 0; j--) { if(!pivots[j].isHigh) { prevLow = pivots[j].price; break; } }
      for(int j = lowIdx + 1; j < count; j++) { if(pivots[j].isHigh) { nextHigh = pivots[j].price; break; } }
      for(int j = lowIdx + 1; j < count; j++) { if(!pivots[j].isHigh) { nextLow = pivots[j].price; break; } }
      
      double nextHigh2 = -1, nextLow2 = -1; int nextLowIdx = -1;
      for(int j = lowIdx + 1; j < count; j++) { if(!pivots[j].isHigh) { nextLowIdx = j; break; } }
      if(nextLowIdx > 0)
      {
         for(int j = nextLowIdx + 1; j < count; j++) { if(pivots[j].isHigh) { nextHigh2 = pivots[j].price; break; } }
         for(int j = nextLowIdx + 1; j < count; j++) { if(!pivots[j].isHigh) { nextLow2 = pivots[j].price; break; } }
      }
      
      bool rejected = false;
      string rejectReason = "";
      
      // فیلترها برای High
      if(prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
      {
         if(highPrice > prevHigh && highPrice > nextHigh && lowPrice < nextLow && prevLow < lowPrice)
         {
            rejected = true; rejectReason = "Filter1";
         }
      }
      
      if(!rejected && prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
      {
         if(highPrice > prevHigh && highPrice > nextHigh && lowPrice > prevLow && lowPrice > nextLow)
         {
            rejected = true; rejectReason = "Filter2_HigherHigh";
         }
      }
      
      bool isIndependentPivot = false, isUptrendTop = false;
      if(prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
      {
         // شرط پیووت مستقل V-shape: nextHigh > highPrice AND nextLow > lowPrice AND prevHigh < highPrice AND prevLow > lowPrice
         if(nextHigh > highPrice && nextLow > lowPrice && prevHigh < highPrice && prevLow > lowPrice)
         {
            isIndependentPivot = true;
            Print("✅ قله مستقل: ", cur.time, " H=", highPrice, " prevH=", prevHigh, " nextH=", nextHigh, " prevL=", prevLow, " L=", lowPrice, " nextL=", nextLow);
         }
         if(highPrice > prevHigh && lowPrice > prevLow && nextHigh < highPrice && nextLow > prevLow)
            isUptrendTop = true;
      }
      
      bool skipOldConditions = (isIndependentPivot || isUptrendTop);
      
      if(!rejected && !skipOldConditions)
      {
         if(nextHigh > 0 && prevHigh > 0 && nextHigh < highPrice && prevHigh < highPrice)
         {
            bool downtrend = (prevLow > 0 && highPrice < prevHigh && lowPrice < prevLow);
            if(!downtrend) { rejected = true; rejectReason = "NoDowntrend"; }
            else
            {
               bool reversal1 = (nextLow > 0 && nextHigh > highPrice && nextLow > lowPrice);
               bool reversal2 = false;
               if(nextHigh2 > 0 && nextLow2 > 0) reversal2 = (nextHigh2 > nextHigh && nextLow2 > nextLow);
               
               if(reversal1 && reversal2)
               {
                  double move1 = nextHigh - highPrice, move2 = nextHigh2 - nextHigh;
                  if(move2 >= move1 * 0.5) { rejected = true; rejectReason = "StrongReversal"; }
               }
            }
         }
         
         bool isValidInsideBar = false;
         if(!rejected && prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
         {
            if(highPrice < prevHigh && highPrice < nextHigh && lowPrice > prevLow && lowPrice > nextLow)
               isValidInsideBar = true;
         }
         
         if(!rejected && !isValidInsideBar && prevHigh > 0 && prevLow > 0 && nextLow > 0)
         {
            if(highPrice < prevHigh && lowPrice > prevLow && lowPrice > nextLow)
            {
               rejected = true; rejectReason = "LimitedCandle";
            }
         }
         
         if(!rejected && nextLow > 0 && prevLow > 0 && nextLow > lowPrice && prevLow > lowPrice)
         {
            bool uptrend = (prevHigh > 0 && highPrice > prevHigh && lowPrice > prevLow);
            if(uptrend)
            {
               bool reversal1 = (nextHigh > 0 && nextHigh < highPrice && nextLow < lowPrice);
               bool reversal2 = false;
               if(nextHigh2 > 0 && nextLow2 > 0) reversal2 = (nextHigh2 < nextHigh && nextLow2 < nextLow);
               
               if(reversal1 && reversal2)
               {
                  double move1 = highPrice - nextHigh, move2 = nextHigh - nextHigh2;
                  if(move2 >= move1 * 0.5) { rejected = true; rejectReason = "BearishReversal"; }
               }
            }
         }
         
         if(!rejected && prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
         {
            bool isInsideBar = (highPrice < prevHigh && lowPrice > prevLow);
            if(isInsideBar)
            {
               bool strongBearish = (nextHigh < highPrice && nextLow < lowPrice);
               if(strongBearish && nextHigh2 > 0 && nextLow2 > 0)
               {
                  bool strongBearish2 = (nextHigh2 < nextHigh && nextLow2 < nextLow);
                  if(strongBearish2) { rejected = true; rejectReason = "InsideBarBearish"; }
               }
            }
         }
      }
      
      if(rejected)
      {
         // قله رد شده - علامت قرمز
         string nameHigh = "RSFLAG_REJECT_HIGH_" + IntegerToString(rejectedHighCount);
         DrawArrow(nameHigh, cur.time, highPrice, clrRed);
         rejectedHighCount++;
      }
      else if(isIndependentPivot)
      {
         Print("✅ قله مستقل: ", cur.time, " H=", highPrice);
         
         // پیدا کردن آخرین High M5 قبل از قله
         int lastM5HighIdx = -1;
         for(int m = 0; m < m5Count; m++)
         {
            if(pivotsM5[m].isHigh && pivotsM5[m].time < cur.time)
            {
               lastM5HighIdx = m;
            }
         }
         
         if(lastM5HighIdx >= 0)
         {
            // پیدا کردن Low بعد از این High M5
            int m5LowIdx = -1;
            for(int m = lastM5HighIdx + 1; m < m5Count; m++)
            {
               if(!pivotsM5[m].isHigh)
               {
                  m5LowIdx = m;
                  break;
               }
            }
            
            if(m5LowIdx >= 0)
            {
               Print("  ✅ باکس M5: High=", pivotsM5[lastM5HighIdx].time, " Low=", pivotsM5[m5LowIdx].time);
               string boxName = "RSFLAG_M5BOX_PEAK_" + IntegerToString(independentPeakCount);
               DrawBox(boxName, 
                      pivotsM5[lastM5HighIdx].time, 
                      pivotsM5[lastM5HighIdx].price,
                      pivotsM5[m5LowIdx].time, 
                      pivotsM5[m5LowIdx].price,
                      clrYellow);
               independentPeakCount++;
            }
         }
      }
   }
   
   // پردازش Low ها
   for(int i = 1; i < count; i++)
   {
      SPivot cur = pivots[i];
      if(cur.isHigh) continue;
      
      int highIdx = -1;
      for(int j = i + 1; j < count; j++) { if(pivots[j].isHigh) { highIdx = j; break; } }
      if(highIdx == -1) continue;
      
      SPivot curHigh = pivots[highIdx];
      double lowPrice = cur.price, highPrice = curHigh.price;
      double prevLow = -1, nextLow = -1, prevHigh = -1, nextHigh = -1;
      
      for(int j = i - 1; j >= 0; j--) { if(!pivots[j].isHigh) { prevLow = pivots[j].price; break; } }
      for(int j = i - 1; j >= 0; j--) { if(pivots[j].isHigh) { prevHigh = pivots[j].price; break; } }
      for(int j = highIdx + 1; j < count; j++) { if(!pivots[j].isHigh) { nextLow = pivots[j].price; break; } }
      for(int j = highIdx + 1; j < count; j++) { if(pivots[j].isHigh) { nextHigh = pivots[j].price; break; } }
      
      double nextLow2 = -1, nextHigh2 = -1; int nextHighIdx = -1;
      for(int j = highIdx + 1; j < count; j++) { if(pivots[j].isHigh) { nextHighIdx = j; break; } }
      if(nextHighIdx > 0)
      {
         for(int j = nextHighIdx + 1; j < count; j++) { if(!pivots[j].isHigh) { nextLow2 = pivots[j].price; break; } }
         for(int j = nextHighIdx + 1; j < count; j++) { if(pivots[j].isHigh) { nextHigh2 = pivots[j].price; break; } }
      }
      
      bool rejected = false;
      string rejectReason = "";
      
      if(prevLow > 0 && prevHigh > 0 && nextLow > 0 && nextHigh > 0)
      {
         if(lowPrice < prevLow && lowPrice < nextLow && highPrice > nextHigh && prevHigh > highPrice)
         {
            rejected = true; rejectReason = "Filter1_Inverted";
         }
      }
      
      if(!rejected && prevLow > 0 && prevHigh > 0 && nextLow > 0 && nextHigh > 0)
      {
         if(lowPrice < prevLow && lowPrice < nextLow && highPrice < prevHigh && highPrice < nextHigh)
         {
            rejected = true; rejectReason = "Filter2_LowerLow";
         }
      }
      
      bool isIndependentValley = false, isDowntrendBottom = false;
      if(prevLow > 0 && prevHigh > 0 && nextLow > 0 && nextHigh > 0)
      {
         if(nextLow < lowPrice && nextHigh < highPrice && prevLow > lowPrice && prevHigh < highPrice)
            isIndependentValley = true;
         if(lowPrice < prevLow && highPrice < prevHigh && nextLow > lowPrice && nextHigh < prevHigh)
            isDowntrendBottom = true;
      }
      
      bool skipOldConditions = (isIndependentValley || isDowntrendBottom);
      
      if(!rejected && !skipOldConditions)
      {
         if(nextLow > 0 && prevLow > 0 && nextLow > lowPrice && prevLow > lowPrice)
         {
            bool uptrend = (prevHigh > 0 && lowPrice > prevLow && highPrice > prevHigh);
            if(!uptrend) { rejected = true; rejectReason = "NoUptrend"; }
            else
            {
               bool reversal1 = (nextHigh > 0 && nextLow < lowPrice && nextHigh < highPrice);
               bool reversal2 = false;
               if(nextLow2 > 0 && nextHigh2 > 0) reversal2 = (nextLow2 < nextLow && nextHigh2 < nextHigh);
               
               if(reversal1 && reversal2)
               {
                  double move1 = lowPrice - nextLow, move2 = nextLow - nextLow2;
                  if(move2 >= move1 * 0.5) { rejected = true; rejectReason = "StrongBearishReversal"; }
               }
            }
         }
         
         bool isValidInsideBar = false;
         if(!rejected && prevLow > 0 && prevHigh > 0 && nextLow > 0 && nextHigh > 0)
         {
            if(lowPrice > prevLow && lowPrice > nextLow && highPrice < prevHigh && highPrice < nextHigh)
               isValidInsideBar = true;
         }
         
         if(!rejected && !isValidInsideBar && prevLow > 0 && prevHigh > 0 && nextHigh > 0)
         {
            if(lowPrice > prevLow && highPrice < prevHigh && highPrice < nextHigh)
            {
               rejected = true; rejectReason = "LimitedCandle_Inverted";
            }
         }
         
         if(!rejected && nextHigh > 0 && prevHigh > 0 && nextHigh < highPrice && prevHigh < highPrice)
         {
            bool downtrend = (prevLow > 0 && lowPrice < prevLow && highPrice < prevHigh);
            if(downtrend)
            {
               bool reversal1 = (nextLow > 0 && nextLow > lowPrice && nextHigh > highPrice);
               bool reversal2 = false;
               if(nextLow2 > 0 && nextHigh2 > 0) reversal2 = (nextLow2 > nextLow && nextHigh2 > nextHigh);
               
               if(reversal1 && reversal2)
               {
                  double move1 = nextLow - lowPrice, move2 = nextLow2 - nextLow;
                  if(move2 >= move1 * 0.5) { rejected = true; rejectReason = "BullishReversal"; }
               }
            }
         }
         
         if(!rejected && prevLow > 0 && prevHigh > 0 && nextLow > 0 && nextHigh > 0)
         {
            bool isInsideBar = (lowPrice > prevLow && highPrice < prevHigh);
            if(isInsideBar)
            {
               bool strongBullish = (nextLow > lowPrice && nextHigh > highPrice);
               if(strongBullish && nextLow2 > 0 && nextHigh2 > 0)
               {
                  bool strongBullish2 = (nextLow2 > nextLow && nextHigh2 > nextHigh);
                  if(strongBullish2) { rejected = true; rejectReason = "InsideBarBullish"; }
               }
            }
         }
      }
      
      if(rejected)
      {
         // دره رد شده - علامت آبی
         string nameLow = "RSFLAG_REJECT_LOW_" + IntegerToString(rejectedLowCount);
         DrawArrow(nameLow, cur.time, lowPrice, clrBlue);
         rejectedLowCount++;
      }
      else if(isIndependentValley)
      {
         Print("✅ دره مستقل: ", cur.time, " L=", lowPrice);
         
         // پیدا کردن آخرین Low M5 قبل از دره
         int lastM5LowIdx = -1;
         for(int m = 0; m < m5Count; m++)
         {
            if(!pivotsM5[m].isHigh && pivotsM5[m].time < cur.time)
            {
               lastM5LowIdx = m;
            }
         }
         
         if(lastM5LowIdx >= 0)
         {
            // پیدا کردن High بعد از این Low M5
            int m5HighIdx = -1;
            for(int m = lastM5LowIdx + 1; m < m5Count; m++)
            {
               if(pivotsM5[m].isHigh)
               {
                  m5HighIdx = m;
                  break;
               }
            }
            
            if(m5HighIdx >= 0)
            {
               Print("  ✅ باکس M5: Low=", pivotsM5[lastM5LowIdx].time, " High=", pivotsM5[m5HighIdx].time);
               string boxName = "RSFLAG_M5BOX_VALLEY_" + IntegerToString(independentValleyCount);
               DrawBox(boxName, 
                      pivotsM5[lastM5LowIdx].time, 
                      pivotsM5[m5HighIdx].price,
                      pivotsM5[m5HighIdx].time, 
                      pivotsM5[lastM5LowIdx].price,
                      clrYellow);
               independentValleyCount++;
            }
         }
      }
   }
   
   Print("✅ قله‌های رد شده: ", rejectedHighCount);
   Print("✅ دره‌های رد شده: ", rejectedLowCount);
   Print("✅ قله‌های مستقل با M5: ", independentPeakCount);
   Print("✅ دره‌های مستقل با M5: ", independentValleyCount);
}

int OnInit()
{
   IndicatorSetString(INDICATOR_SHORTNAME, "RSFLAG - قله و دره رد شده");
   processed = false;
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) { ObjectsDeleteAll(0, "RSFLAG_"); processed = false; }

int OnCalculate(const int rates_total, const int prev_calculated, const datetime &time[],
                const double &open[], const double &high[], const double &low[], const double &close[],
                const long &tick_volume[], const long &volume[], const int &spread[])
{
   if(rates_total < 100) return 0;
   if(!processed || prev_calculated == 0)
   {
      Print("🔍 شناسایی قله و دره‌های رد شده توسط Flag...");
      ObjectsDeleteAll(0, "RSFLAG_");
      ProcessM15();
      processed = true;
   }
   return rates_total;
}

void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
   if(id == CHARTEVENT_KEYDOWN && lparam == 116) { processed = false; ChartRedraw(); }
}
