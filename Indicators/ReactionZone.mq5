//+------------------------------------------------------------------+
//| ReactionZone.mq5                                                  |
//| Reaction Zone Extension Indicator   v1.00                         |
//|                                                                    |
//| این اندیکاتور باکس‌های Flag را می‌خواند و:                        |
//| - برای باکس‌های صعودی: تا زمان شکست از پایین، امتداد می‌دهد     |
//| - برای باکس‌های نزولی: تا زمان شکست از بالا، امتداد می‌دهد      |
//|                                                                    |
//| v1.00: نسخه اولیه                                                  |
//+------------------------------------------------------------------+
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

//--- Inputs
input bool  InpUseH4 = true;                 // نمایش باکس‌های H4
input bool  InpUseH1 = true;                 // نمایش باکس‌های H1
input bool  InpUseM15 = true;                // نمایش باکس‌های M15
input bool  InpUseM5 = true;                 // نمایش باکس‌های M5
input bool  InpUseM1 = true;                 // نمایش باکس‌های M1
input color InpBullishColor = clrOrange;     // رنگ باکس صعودی
input color InpBearishColor = clrCyan;       // رنگ باکس نزولی
input int   InpLineWidth    = 1;             // ضخامت خط (1 = نازک و ظریف)
input bool  InpShowLabel    = true;          // نمایش برچسب
input int   InpLabelFontSize = 8;            // اندازه فونت برچسب
input int   InpMaxBoxes = 200;               // تعداد باکس‌های آخر برای امتداد
input bool  InpShowShortBoxes = true;        // نمایش باکس‌های کوتاه (شکسته سریع)

//--- Structure to store reaction zones
struct SReactionZone
{
   string   originalBoxName;   // نام باکس اصلی Flag
   datetime timeStart;         // زمان شروع باکس Flag (t1)
   datetime timeRight;         // زمان پایان اولیه باکس Flag (t2)
   double   priceTop;          // قیمت بالای باکس
   double   priceBottom;       // قیمت پایین باکس
   bool     isBullish;         // آیا صعودی است؟
   bool     isBroken;          // آیا شکسته شده؟
   datetime breakTime;         // زمان شکست
   string   label;             // برچسب (مثل 3D-5H1)
   color    boxColor;          // رنگ هماهنگ با تایم‌فریم
};

SReactionZone reactionZones[];
int zoneCount = 0;

//+------------------------------------------------------------------+
//| دریافت رنگ هماهنگ با تایم‌فریم                                    |
//+------------------------------------------------------------------+
color GetTFColor(string objName)
{
   if(StringFind(objName, "H4") >= 0)  return clrWhite;
   if(StringFind(objName, "H1") >= 0)  return clrYellow;
   if(StringFind(objName, "M15") >= 0) return clrLime;
   if(StringFind(objName, "M5") >= 0)  return clrAqua;
   if(StringFind(objName, "M1") >= 0)  return clrOrange;
   return clrYellow;
}

//+------------------------------------------------------------------+
//| رسم باکس توخالی                                                  |
//+------------------------------------------------------------------+
void DrawHollowBox(string name, datetime t1, double top, datetime t2, double bottom,
                   color clr, int width, bool rayRight = false, ENUM_LINE_STYLE style = STYLE_SOLID)
{
   if(ObjectFind(0, name) >= 0) ObjectDelete(0, name);
   if(!ObjectCreate(0, name, OBJ_RECTANGLE, 0, t1, top, t2, bottom)) return;
   ObjectSetInteger(0, name, OBJPROP_COLOR,      clr);
   ObjectSetInteger(0, name, OBJPROP_WIDTH,      width);
   ObjectSetInteger(0, name, OBJPROP_STYLE,      style);
   ObjectSetInteger(0, name, OBJPROP_FILL,       false);
   ObjectSetInteger(0, name, OBJPROP_BACK,       false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, true);
   ObjectSetInteger(0, name, OBJPROP_RAY_RIGHT,  rayRight);
}

//+------------------------------------------------------------------+
//| تولید رنگ رندوم روشن (برای بک‌گراند مشکی)                       |
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
//| خواندن باکس‌های Flag و تشخیص نوع آنها                            |
//+------------------------------------------------------------------+
void ReadFlagBoxes()
{
   ArrayResize(reactionZones, 0);
   zoneCount = 0;
   
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
   
   for(int i = ObjectsTotal(0, 0, OBJ_RECTANGLE) - 1; i >= 0; i--)
   {
      string objName = ObjectName(0, i, 0, OBJ_RECTANGLE);
      
      if(StringFind(objName, "FLAG_BOX_") != 0) continue;
      
      bool isH4 = (StringFind(objName, "H4") >= 0);
      bool isH1 = (StringFind(objName, "H1") >= 0);
      bool isM15 = (StringFind(objName, "M15") >= 0);
      bool isM5 = (StringFind(objName, "M5") >= 0);
      bool isM1 = (StringFind(objName, "M1_") >= 0);
      
      if(isH4 && !InpUseH4) continue;
      if(isH1 && !InpUseH1) continue;
      if(isM15 && !InpUseM15) continue;
      if(isM5 && !InpUseM5) continue;
      if(isM1 && !InpUseM1) continue;
      
      if(!isH4 && !isH1 && !isM15 && !isM5 && !isM1) continue;
      
      datetime t1 = (datetime)ObjectGetInteger(0, objName, OBJPROP_TIME, 0);
      datetime t2 = (datetime)ObjectGetInteger(0, objName, OBJPROP_TIME, 1);
      double price1 = ObjectGetDouble(0, objName, OBJPROP_PRICE, 0);
      double price2 = ObjectGetDouble(0, objName, OBJPROP_PRICE, 1);
      
      double top = MathMax(price1, price2);
      double bottom = MathMin(price1, price2);
      
      datetime leftTime  = MathMin(t1, t2);
      datetime rightTime = MathMax(t1, t2);
      
      ArrayResize(tempBoxes, tempCount + 1);
      tempBoxes[tempCount].name = objName;
      tempBoxes[tempCount].rightTime = rightTime;
      tempBoxes[tempCount].t1 = leftTime;
      tempBoxes[tempCount].t2 = rightTime;
      tempBoxes[tempCount].top = top;
      tempBoxes[tempCount].bottom = bottom;
      tempCount++;
   }
   
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
   
   int startIdx = MathMax(0, tempCount - InpMaxBoxes);
   
   for(int i = startIdx; i < tempCount; i++)
   {
      string boxName = tempBoxes[i].name;
      bool isBullish = true;
      
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
      reactionZones[zoneCount].timeStart = tempBoxes[i].t1;        // شروع از اول باکس اصلی Flag
      reactionZones[zoneCount].timeRight = tempBoxes[i].rightTime; // زمان شروع شکست
      reactionZones[zoneCount].priceTop = tempBoxes[i].top;
      reactionZones[zoneCount].priceBottom = tempBoxes[i].bottom;
      reactionZones[zoneCount].isBullish = isBullish;
      reactionZones[zoneCount].isBroken = false;
      reactionZones[zoneCount].breakTime = 0;
      reactionZones[zoneCount].label = ExtractLabel(tempBoxes[i].name);
      reactionZones[zoneCount].boxColor = GetTFColor(tempBoxes[i].name);
      
      zoneCount++;
   }
}

//+------------------------------------------------------------------+
//| استخراج label از نام باکس                                        |
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
      
      datetime startTime = reactionZones[i].timeRight; // شروع بررسی شکست از انتهای اولیه باکس Flag
      
      int startIdx = -1;
      for(int bar = rates_total - 1; bar >= 0; bar--)
      {
         if(time[bar] >= startTime)
         {
            startIdx = bar;
         }
         else
         {
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
//| رسم reaction zones (یکپارچه و متصل از ابتدا تا انتها)            |
//+------------------------------------------------------------------+
void DrawReactionZones(const datetime &time[], int rates_total)
{
   datetime liveTime = time[rates_total - 1];
   
   for(int i = 0; i < zoneCount; i++)
   {
      string zoneName = "RZ_" + reactionZones[i].originalBoxName;
      
      datetime startTime = reactionZones[i].timeStart; // شروع از ابتدای باکس پرچم
      datetime endTime;
      
      if(reactionZones[i].isBroken)
      {
         endTime = reactionZones[i].breakTime;
      }
      else
      {
         endTime = liveTime;
      }
      
      int seed = (int)reactionZones[i].timeStart + i * 37;
      color boxColor = GetRandomBrightColor(seed);
      
      // همرنگ کردن باکس اولیه Flag با رنگ رندوم تا کاملاً یکپارچه و یک‌دست شود
      ObjectSetInteger(0, reactionZones[i].originalBoxName, OBJPROP_COLOR, boxColor);
      
      ENUM_LINE_STYLE boxStyle = STYLE_SOLID;
      if(StringFind(reactionZones[i].originalBoxName, "M15") >= 0) boxStyle = STYLE_DASH;
      else if(StringFind(reactionZones[i].originalBoxName, "M5") >= 0) boxStyle = STYLE_DOT;
      else if(StringFind(reactionZones[i].originalBoxName, "M1_") >= 0) boxStyle = STYLE_DASHDOT;
      
      DrawHollowBox(zoneName,
                    startTime,
                    reactionZones[i].priceTop,
                    endTime,
                    reactionZones[i].priceBottom,
                    boxColor,
                    InpLineWidth,
                    false,
                    boxStyle);
      
      string labelName = zoneName + "_LBL";
      double labelPrice = (reactionZones[i].priceTop + reactionZones[i].priceBottom) / 2;
      DrawLabel(labelName, endTime, labelPrice, reactionZones[i].label, boxColor);
   }
}

//+------------------------------------------------------------------+
int OnInit()
{
   IndicatorSetString(INDICATOR_SHORTNAME, "ReactionZone v1.00");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // حذف تمام باکس‌های RZ
   ObjectsDeleteAll(0, "RZ_");
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
   
   ReadFlagBoxes();
   CheckBreakouts(high, low, time, rates_total);
   DrawReactionZones(time, rates_total);
   
   return rates_total;
}

//+------------------------------------------------------------------+
//| رویداد کلیک روی چارت                                             |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
{
   // بررسی کلیک روی آبجکت
   if(id == CHARTEVENT_OBJECT_CLICK)
   {
      string clickedObj = sparam;
      
      // اگر روی یک باکس RZ کلیک شده
      if(StringFind(clickedObj, "RZ_FLAG_BOX_") == 0)
      {
         // پیدا کردن باکس در آرایه reactionZones
         for(int i = 0; i < zoneCount; i++)
         {
            string zoneName = "RZ_" + reactionZones[i].originalBoxName;
            
            if(zoneName == clickedObj)
            {
               // نمایش فقط نوع باکس
               string boxType = reactionZones[i].isBullish ? "صعودی" : "نزولی";
               Print("باکس ", boxType);
               break;
            }
         }
      }
   }
}
//+------------------------------------------------------------------+
