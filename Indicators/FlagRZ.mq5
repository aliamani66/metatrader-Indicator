//+------------------------------------------------------------------+
//| FlagRZ.mq5                                                        |
//| Combined Flag + ReactionZone Indicator (Simplified)              |
//|                                                                    |
//| این اندیکاتور ترکیبی از Flag و ReactionZone است:                  |
//| - همه تایم‌فریم‌ها و پیووت‌ها فعال هستند                          |
//| - فقط باکس‌های 200 پیپ از قیمت فعلی نمایش داده می‌شوند          |
//| - نوع باکس (صعودی/نزولی) از نام باکس Flag خوانده می‌شود         |
//+------------------------------------------------------------------+
#property version   "2.00"
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

//+------------------------------------------------------------------+
//| Input Parameters - Simplified                                    |
//+------------------------------------------------------------------+
input int   InpPipRange = 200;            // محدوده نمایش (پیپ)
input int   InpRZLineWidth = 3;           // ضخامت خط ReactionZone
input bool  InpRZShowLabel = true;        // نمایش برچسب
input int   InpRZLabelFontSize = 8;       // اندازه فونت برچسب
input bool  InpRZShowShortBoxes = true;   // نمایش باکس‌های کوتاه

//--- Handle for Flag indicator
int flagHandle = INVALID_HANDLE;

//--- Structure to store reaction zones
struct SReactionZone
{
   string  originalBoxName;
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

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   // Load Flag indicator با همه تنظیمات فعال
   flagHandle = iCustom(_Symbol, PERIOD_CURRENT, "Flag",
                        PERIOD_D1, true, clrMagenta,          // TF1: D1
                        PERIOD_W1, true, clrDodgerBlue,       // TF2: W1
                        PERIOD_H4, true, clrWhite,            // TF3: H4
                        PERIOD_H1, true, clrYellow,           // TF4: H1
                        PERIOD_M15, true, clrLime, 50,        // TF5: M15
                        PERIOD_M5, true, clrAqua, 30,         // TF6: M5
                        PERIOD_M1, true, clrYellow, 10,       // TF7: M1
                        3, true,                              // Pivot 3
                        5, true,                              // Pivot 5
                        8, true,                              // Pivot 8
                        3000,                                 // MaxBars
                        1,                                    // LineWidth
                        true);                                // ShowLabel
   
   if(flagHandle == INVALID_HANDLE)
   {
      Print("Error loading Flag indicator!");
      return INIT_FAILED;
   }
   
   IndicatorSetString(INDICATOR_SHORTNAME, "FlagRZ v2.00");
   ChartSetInteger(0, CHART_EVENT_MOUSE_MOVE, true);
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                       |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(flagHandle != INVALID_HANDLE)
      IndicatorRelease(flagHandle);
   
   ObjectsDeleteAll(0, "FLAG_BOX_");
   ObjectsDeleteAll(0, "RZ_");
}

//+------------------------------------------------------------------+
//| رسم باکس توخالی                                                  |
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
//| تولید رنگ رندوم روشن                                             |
//+------------------------------------------------------------------+
color GetRandomBrightColor(int seed)
{
   MathSrand(seed);
   
   color colors[] = {
      clrRed, clrLime, clrYellow, clrCyan, clrMagenta,
      clrOrange, clrGold, clrAqua, clrHotPink, clrSpringGreen,
      clrDeepSkyBlue, clrOrangeRed, clrYellowGreen, clrLightCoral,
      clrMediumSpringGreen, clrDodgerBlue, clrTomato, clrLightGreen,
      clrPaleVioletRed, clrLightSkyBlue, clrSalmon, clrLightSalmon,
      clrTurquoise, clrViolet, clrGreenYellow, clrLightSeaGreen
   };
   
   int index = MathRand() % ArraySize(colors);
   return colors[index];
}

//+------------------------------------------------------------------+
//| رسم برچسب                                                         |
//+------------------------------------------------------------------+
void DrawLabel(string name, datetime t, double price, string text, color clr)
{
   if(!InpRZShowLabel) return;
   if(ObjectFind(0, name) >= 0) ObjectDelete(0, name);
   if(!ObjectCreate(0, name, OBJ_TEXT, 0, t, price)) return;
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, InpRZLabelFontSize);
   ObjectSetInteger(0, name, OBJPROP_BACK, false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
}

//+------------------------------------------------------------------+
//| خواندن باکس‌های Flag با فیلتر محدوده قیمت                        |
//+------------------------------------------------------------------+
void ReadFlagBoxes()
{
   ArrayResize(reactionZones, 0);
   zoneCount = 0;
   
   // محاسبه محدوده قیمت (200 پیپ)
   double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   
   // تبدیل پیپ به قیمت
   double pipValue = point;
   if(digits == 3 || digits == 5) pipValue = point * 10; // برای 3 و 5 رقمی
   
   double priceRangeUp = currentPrice + (InpPipRange * pipValue);
   double priceRangeDown = currentPrice - (InpPipRange * pipValue);
   
   struct STempBox {
      string name;
      datetime rightTime;
      datetime t1;
      datetime t2;
      double top;
      double bottom;
   };
   
   STempBox tempBoxes[];
   int tempCount = 0;
   
   // پیدا کردن تمام باکس‌های FLAG_BOX
   for(int i = ObjectsTotal(0, 0, OBJ_RECTANGLE) - 1; i >= 0; i--)
   {
      string objName = ObjectName(0, i, 0, OBJ_RECTANGLE);
      
      if(StringFind(objName, "FLAG_BOX_") != 0) continue;
      
      datetime t1 = (datetime)ObjectGetInteger(0, objName, OBJPROP_TIME, 0);
      datetime t2 = (datetime)ObjectGetInteger(0, objName, OBJPROP_TIME, 1);
      double price1 = ObjectGetDouble(0, objName, OBJPROP_PRICE, 0);
      double price2 = ObjectGetDouble(0, objName, OBJPROP_PRICE, 1);
      
      double top = MathMax(price1, price2);
      double bottom = MathMin(price1, price2);
      datetime rightTime = MathMax(t1, t2);
      
      // فیلتر محدوده قیمت: فقط باکس‌هایی که بخشی از آنها در محدوده 200 پیپ هستند
      bool inRange = false;
      if(top >= priceRangeDown && bottom <= priceRangeUp)
      {
         inRange = true;
      }
      
      if(!inRange) continue; // باکس خارج از محدوده است
      
      ArrayResize(tempBoxes, tempCount + 1);
      tempBoxes[tempCount].name = objName;
      tempBoxes[tempCount].rightTime = rightTime;
      tempBoxes[tempCount].t1 = t1;
      tempBoxes[tempCount].t2 = t2;
      tempBoxes[tempCount].top = top;
      tempBoxes[tempCount].bottom = bottom;
      tempCount++;
   }
   
   // مرتب‌سازی
   for(int i = 0; i < tempCount - 1; i++)
   {
      for(int j = i + 1; j < tempCount; j++)
      {
         if(tempBoxes[i].rightTime > tempBoxes[j].rightTime)
         {
            STempBox temp = tempBoxes[i];
            tempBoxes[i] = tempBoxes[j];
            tempBoxes[j] = temp;
         }
      }
   }
   
   for(int i = 0; i < tempCount; i++)
   {
      string boxName = tempBoxes[i].name;
      bool isBullish = true; // پیش‌فرض صعودی
      
      // تشخیص نوع باکس از نام باکس Flag
      // اگر نام باکس شامل "_B_" است → صعودی
      // اگر نام باکس شامل "_R_" است → نزولی
      if(StringFind(boxName, "_B_") >= 0)
      {
         isBullish = true;
      }
      else if(StringFind(boxName, "_R_") >= 0)
      {
         isBullish = false;
      }
      
      ArrayResize(reactionZones, zoneCount + 1);
      reactionZones[zoneCount].originalBoxName = tempBoxes[i].name;
      reactionZones[zoneCount].timeStart = tempBoxes[i].rightTime;
      reactionZones[zoneCount].priceTop = tempBoxes[i].top;
      reactionZones[zoneCount].priceBottom = tempBoxes[i].bottom;
      reactionZones[zoneCount].isBullish = isBullish;
      reactionZones[zoneCount].isBroken = false;
      reactionZones[zoneCount].breakTime = 0;
      reactionZones[zoneCount].label = ExtractLabel(tempBoxes[i].name);
      
      zoneCount++;
   }
}

//+------------------------------------------------------------------+
//| استخراج label                                                    |
//+------------------------------------------------------------------+
string ExtractLabel(string boxName)
{
   string parts[];
   int count = StringSplit(boxName, '_', parts);
   
   if(count < 3) return "";
   
   string tf = "";
   string pivot = "";
   
   for(int i = 0; i < count; i++)
   {
      if(parts[i] == "BOX" && i + 1 < count)
      {
         tf = parts[i + 1];
      }
      if(StringFind(parts[i], "P") == 0 && StringLen(parts[i]) > 1)
      {
         pivot = StringSubstr(parts[i], 1);
      }
   }
   
   if(pivot != "" && tf != "")
      return pivot + tf;
   
   return "RZ";
}

//+------------------------------------------------------------------+
//| بررسی شکست باکس‌ها                                               |
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
//| رسم reaction zones                                                |
//+------------------------------------------------------------------+
void DrawReactionZones(const datetime &time[], int rates_total)
{
   datetime liveTime = time[rates_total - 1];
   
   for(int i = 0; i < zoneCount; i++)
   {
      string zoneName = "RZ_" + reactionZones[i].originalBoxName;
      
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
      if(timeDiff < 900)
      {
         if(!InpRZShowShortBoxes)
         {
            continue;
         }
      }
      
      int seed = (int)reactionZones[i].timeStart + i;
      color boxColor = GetRandomBrightColor(seed);
      
      DrawHollowBox(zoneName,
                    startTime,
                    reactionZones[i].priceTop,
                    endTime,
                    reactionZones[i].priceBottom,
                    boxColor,
                    InpRZLineWidth,
                    false);
      
      string labelName = zoneName + "_LBL";
      double labelPrice = (reactionZones[i].priceTop + reactionZones[i].priceBottom) / 2;
      DrawLabel(labelName, endTime, labelPrice, reactionZones[i].label, boxColor);
   }
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
   if(rates_total < 10) return 0;
   
   // Force Flag indicator to calculate
   double dummy[];
   ArraySetAsSeries(dummy, true);
   if(CopyBuffer(flagHandle, 0, 0, 10, dummy) > 0)
   {
      // Flag محاسبه شد
   }
   
   static int calcCount = 0;
   calcCount++;
   
   // هر 10 بار یکبار ReactionZone را به‌روزرسانی کن
   if(calcCount % 10 == 0)
   {
      ReadFlagBoxes();
      
      if(zoneCount > 0)
      {
         CheckBreakouts(high, low, time, rates_total);
         DrawReactionZones(time, rates_total);
      }
   }
   
   return rates_total;
}

//+------------------------------------------------------------------+
//| رویداد کلیک                                                      |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
{
   if(id == CHARTEVENT_OBJECT_CLICK)
   {
      // بررسی کلیک روی باکس RZ
      if(StringFind(sparam, "RZ_FLAG_BOX_") == 0)
      {
         for(int i = 0; i < zoneCount; i++)
         {
            string zoneName = "RZ_" + reactionZones[i].originalBoxName;
            
            if(zoneName == sparam)
            {
               string boxType = reactionZones[i].isBullish ? "صعودی" : "نزولی";
               Print("باکس ", boxType);
               break;
            }
         }
      }
   }
}
//+------------------------------------------------------------------+
