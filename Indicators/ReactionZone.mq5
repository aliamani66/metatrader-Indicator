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
input bool  InpUseH1 = true;                 // نمایش باکس‌های H1
input bool  InpUseM15 = true;                // نمایش باکس‌های M15
input bool  InpUseM5 = true;                 // نمایش باکس‌های M5
input bool  InpUseM1 = true;                 // نمایش باکس‌های M1
input color InpBullishColor = clrOrange;     // رنگ باکس صعودی
input color InpBearishColor = clrCyan;       // رنگ باکس نزولی
input int   InpLineWidth    = 3;             // ضخامت خط
input bool  InpShowLabel    = true;          // نمایش برچسب
input int   InpLabelFontSize = 8;            // اندازه فونت برچسب
input int   InpMaxBoxes = 200;               // تعداد باکس‌های آخر برای امتداد
input bool  InpShowShortBoxes = true;        // نمایش باکس‌های کوتاه (شکسته سریع)

//--- Structure to store reaction zones
struct SReactionZone
{
   string  originalBoxName;   // نام باکس اصلی Flag
   datetime timeStart;        // زمان شروع باکس اصلی
   double  priceTop;          // قیمت بالای باکس
   double  priceBottom;       // قیمت پایین باکس
   bool    isBullish;         // آیا صعودی است؟
   bool    isBroken;          // آیا شکسته شده؟
   datetime breakTime;        // زمان شکست
   string  label;             // برچسب (مثل 3D-5H1)
};

SReactionZone reactionZones[];
int zoneCount = 0;

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
//| تولید رنگ رندوم روشن (برای بک‌گراند مشکی)                       |
//+------------------------------------------------------------------+
color GetRandomBrightColor(int seed)
{
   // استفاده از seed برای تولید رنگ ثابت برای هر باکس
   MathSrand(seed);
   
   // رنگ‌های روشن و متنوع برای بک‌گراند مشکی
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
   
   // ساختار موقت برای مرتب‌سازی
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
   
   // پیدا کردن تمام باکس‌های FLAG_BOX فقط برای H1, M15, M5, M1
   for(int i = ObjectsTotal(0, 0, OBJ_RECTANGLE) - 1; i >= 0; i--)
   {
      string objName = ObjectName(0, i, 0, OBJ_RECTANGLE);
      
      // فقط باکس‌های FLAG_BOX را در نظر بگیر
      if(StringFind(objName, "FLAG_BOX_") != 0) continue;
      
      // فقط باکس‌های H1, M15, M5, M1 (بر اساس تنظیمات کاربر)
      bool isH1 = (StringFind(objName, "H1") >= 0);
      bool isM15 = (StringFind(objName, "M15") >= 0);
      bool isM5 = (StringFind(objName, "M5") >= 0);
      bool isM1 = (StringFind(objName, "M1_") >= 0); // M1_ برای جلوگیری از match با M15
      
      // بررسی اینکه آیا این تایم‌فریم فعال است
      if(isH1 && !InpUseH1) continue;
      if(isM15 && !InpUseM15) continue;
      if(isM5 && !InpUseM5) continue;
      if(isM1 && !InpUseM1) continue;
      
      // اگه هیچکدوم نبودن، skip
      if(!isH1 && !isM15 && !isM5 && !isM1) continue;
      
      // خواندن اطلاعات باکس
      datetime t1 = (datetime)ObjectGetInteger(0, objName, OBJPROP_TIME, 0);
      datetime t2 = (datetime)ObjectGetInteger(0, objName, OBJPROP_TIME, 1);
      double price1 = ObjectGetDouble(0, objName, OBJPROP_PRICE, 0);
      double price2 = ObjectGetDouble(0, objName, OBJPROP_PRICE, 1);
      
      double top = MathMax(price1, price2);
      double bottom = MathMin(price1, price2);
      
      // زمان راست باکس (جدیدترین زمان)
      datetime rightTime = MathMax(t1, t2);
      
      ArrayResize(tempBoxes, tempCount + 1);
      tempBoxes[tempCount].name = objName;
      tempBoxes[tempCount].rightTime = rightTime;
      tempBoxes[tempCount].t1 = t1;
      tempBoxes[tempCount].t2 = t2;
      tempBoxes[tempCount].top = top;
      tempBoxes[tempCount].bottom = bottom;
      tempCount++;
   }
   
   // مرتب‌سازی بر اساس rightTime (از قدیمی به جدید)
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
   
   // انتخاب فقط N باکس آخر
   int startIdx = MathMax(0, tempCount - InpMaxBoxes);
   
   for(int i = startIdx; i < tempCount; i++)
   {
      // تشخیص نوع باکس
      bool isBullish = DetectBoxType(tempBoxes[i].rightTime, tempBoxes[i].top, tempBoxes[i].bottom);
      
      // ذخیره zone
      ArrayResize(reactionZones, zoneCount + 1);
      reactionZones[zoneCount].originalBoxName = tempBoxes[i].name;
      reactionZones[zoneCount].timeStart = tempBoxes[i].rightTime; // از سمت راست باکس
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
//| تشخیص نوع باکس (صعودی یا نزولی)                                  |
//| منطق: بررسی قیمت در لحظه تشکیل باکس                              |
//| اگر قیمت بعد از باکس بالا رفته → باکس صعودی (support)           |
//| اگر قیمت بعد از باکس پایین رفته → باکس نزولی (resistance)        |
//+------------------------------------------------------------------+
bool DetectBoxType(datetime afterTime, double top, double bottom)
{
   // پیدا کردن قیمت در لحظه afterTime و چند کندل بعدش
   int afterBar = iBarShift(_Symbol, PERIOD_CURRENT, afterTime);
   if(afterBar < 0) return true; // پیش‌فرض صعودی
   
   // بررسی 5 کندل بعد از باکس
   int checkBars = MathMin(5, afterBar);
   
   double avgPriceAfter = 0;
   int count = 0;
   
   // محاسبه میانگین قیمت 5 کندل بعد از باکس
   for(int i = MathMax(0, afterBar - checkBars); i < afterBar; i++)
   {
      avgPriceAfter += iClose(_Symbol, PERIOD_CURRENT, i);
      count++;
   }
   
   if(count > 0) avgPriceAfter /= count;
   
   double boxMiddle = (top + bottom) / 2;
   
   // اگر قیمت بعد از باکس بالاتر از وسط باکس → صعودی
   if(avgPriceAfter > boxMiddle)
      return true; // صعودی - قیمت بعد از باکس بالا رفته
   
   // اگر قیمت بعد از باکس پایین‌تر از وسط باکس → نزولی  
   return false; // نزولی - قیمت بعد از باکس پایین رفته
}

//+------------------------------------------------------------------+
//| استخراج label از نام باکس                                        |
//+------------------------------------------------------------------+
string ExtractLabel(string boxName)
{
   // نام باکس به این صورت است: FLAG_BOX_TF_P#_timestamp1_timestamp2
   // مثلاً: FLAG_BOX_D1_P3_1234567890_1234567900
   
   string parts[];
   int count = StringSplit(boxName, '_', parts);
   
   if(count < 3) return "";
   
   // استخراج TF و Pivot
   string tf = "";
   string pivot = "";
   
   for(int i = 0; i < count; i++)
   {
      if(parts[i] == "BOX" && i + 1 < count)
      {
         tf = parts[i + 1]; // timeframe
      }
      if(StringFind(parts[i], "P") == 0 && StringLen(parts[i]) > 1)
      {
         pivot = StringSubstr(parts[i], 1); // حذف P
      }
   }
   
   // ساخت label
   if(pivot != "" && tf != "")
      return pivot + tf;
   
   return "RZ";
}

//+------------------------------------------------------------------+
//| بررسی شکست باکس‌ها                                               |
//+------------------------------------------------------------------+
void CheckBreakouts(const double &high[], const double &low[], const datetime &time[], int rates_total)
{
   int brokenCount = 0;
   
   Print("=== Checking breakouts for ", zoneCount, " boxes ===");
   
   for(int i = 0; i < zoneCount; i++)
   {
      if(reactionZones[i].isBroken) continue; // قبلاً شکسته شده
      
      datetime startTime = reactionZones[i].timeStart;
      
      // پیدا کردن index شروع در آرایه time[]
      int startIdx = -1;
      for(int t = 0; t < rates_total; t++)
      {
         if(time[t] >= startTime)
         {
            startIdx = t;
            break;
         }
      }
      
      if(startIdx < 0)
      {
         Print("Box ", i, " - startIdx not found for startTime: ", startTime);
         continue;
      }
      
      Print("Box ", i, " (", reactionZones[i].isBullish ? "BULLISH" : "BEARISH", ") - Checking from idx:", startIdx, " to ", rates_total-1, " | Top:", reactionZones[i].priceTop, " Bottom:", reactionZones[i].priceBottom);
      
      // بررسی تمام کندل‌های بعد از startTime
      for(int bar = startIdx; bar < rates_total; bar++)
      {
         double barHigh = high[bar];
         double barLow = low[bar];
         
         // بررسی شکست بر اساس نوع باکس
         if(reactionZones[i].isBullish)
         {
            // باکس صعودی: بررسی شکست از پایین (کف)
            if(barLow < reactionZones[i].priceBottom)
            {
               reactionZones[i].isBroken = true;
               reactionZones[i].breakTime = time[bar];
               brokenCount++;
               Print("  -> BULLISH Box ", i, " BROKEN at bar ", bar, " time:", time[bar], " - Low: ", barLow, " < Bottom: ", reactionZones[i].priceBottom);
               break;
            }
         }
         else
         {
            // باکس نزولی: بررسی شکست از بالا (سقف)
            if(barHigh > reactionZones[i].priceTop)
            {
               reactionZones[i].isBroken = true;
               reactionZones[i].breakTime = time[bar];
               brokenCount++;
               Print("  -> BEARISH Box ", i, " BROKEN at bar ", bar, " time:", time[bar], " - High: ", barHigh, " > Top: ", reactionZones[i].priceTop);
               break;
            }
         }
      }
   }
   
   Print("=== Total broken boxes: ", brokenCount, " ===");
}

//+------------------------------------------------------------------+
//| رسم reaction zones                                                |
//+------------------------------------------------------------------+
void DrawReactionZones(const datetime &time[], int rates_total)
{
   // زمان آخرین کندل لایو (آخرین عنصر آرایه)
   datetime liveTime = time[rates_total - 1];
   
   Print("=== Drawing zones - liveTime: ", liveTime, " ===");
   
   int brokenCount = 0;
   int activeCount = 0;
   int skippedCount = 0;
   
   for(int i = 0; i < zoneCount; i++)
   {
      string zoneName = "RZ_" + reactionZones[i].originalBoxName;
      
      // رسم باکس: از سمت راست باکس Flag
      datetime startTime = reactionZones[i].timeStart; // سمت راست باکس Flag
      datetime endTime;
      
      // اگر شکسته شده، تا زمان شکست امتداد بده
      // اگر نشکسته، تا آخرین کندل لایو امتداد بده
      if(reactionZones[i].isBroken)
      {
         endTime = reactionZones[i].breakTime; // تا نقطه شکست
         brokenCount++;
         Print("Box ", i, " (", reactionZones[i].isBullish ? "BULLISH" : "BEARISH", ") is BROKEN at ", endTime, " - Top:", reactionZones[i].priceTop, " Bottom:", reactionZones[i].priceBottom);
      }
      else
      {
         endTime = liveTime; // تا آخرین کندل لایو
         activeCount++;
      }
      
      // اگر startTime و endTime خیلی نزدیک هم هستند، بررسی کن آیا باید نمایش داده بشه
      int timeDiff = (int)(endTime - startTime);
      if(timeDiff < 900) // کمتر از 15 دقیقه (یک کندل M15)
      {
         // اگر نمایش باکس‌های کوتاه خاموش باشه، skip کن
         if(!InpShowShortBoxes)
         {
            Print("Skipping box ", i, " - time difference too small: ", timeDiff, " seconds (", timeDiff/60, " minutes)");
            skippedCount++;
            continue;
         }
         // اگه روشنه، ادامه بده و بکش
      }
      
      // تولید رنگ رندوم برای هر باکس (با seed ثابت برای ثبات رنگ)
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
      
      // رسم برچسب در انتهای باکس (breakTime یا liveTime)
      string labelName = zoneName + "_LBL";
      double labelPrice = (reactionZones[i].priceTop + reactionZones[i].priceBottom) / 2;
      DrawLabel(labelName, endTime, labelPrice, reactionZones[i].label, boxColor);
   }
   
   Print("Total: ", zoneCount, " boxes - Active: ", activeCount, " Broken: ", brokenCount, " Skipped: ", skippedCount);
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
   
   // خواندن باکس‌های Flag
   ReadFlagBoxes();
   
   Print("Total boxes found: ", zoneCount);
   if(zoneCount > 0)
   {
      Print("First box timeStart: ", reactionZones[0].timeStart, " Last box timeStart: ", reactionZones[zoneCount-1].timeStart);
      Print("time[0] (oldest): ", time[0], " time[last] (newest): ", time[rates_total-1]);
   }
   
   // بررسی شکست‌ها
   CheckBreakouts(high, low, time, rates_total);
   
   // رسم reaction zones
   DrawReactionZones(time, rates_total);
   
   return rates_total;
}
//+------------------------------------------------------------------+
