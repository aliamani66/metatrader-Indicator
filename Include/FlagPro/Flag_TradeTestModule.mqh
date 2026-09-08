//+------------------------------------------------------------------+
//| Flag_TradeTestModule.mqh                                         |
//| Dedicated Interactive Trade Test Module & Box Focus Mode Engine  |
//| FlagPro Quantitative Trading Systems                             |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""

// متغیرهای وضعیت حالت تمرکز (Focus Mode)
bool   g_focusModeActive       = false;
int    g_focusBoxIdx           = -1;
string g_origFocusBoxName      = "";
color  g_origFocusColor        = clrNONE;
int    g_origFocusWidth        = 1;
ENUM_LINE_STYLE g_origFocusStyle = STYLE_SOLID;

//+------------------------------------------------------------------+
//| بررسی فعال بودن حالت تمرکز                                      |
//+------------------------------------------------------------------+
bool IsFocusModeActive()
{
   return g_focusModeActive;
}

//+------------------------------------------------------------------+
//| دریافت اندیس باکس فوکوس‌شده                                      |
//+------------------------------------------------------------------+
int GetFocusBoxIndex()
{
   return g_focusBoxIdx;
}

// Forward declarations
void ShowTradeSetupForBox(int boxIdx);
void RenderFocusHUD(int boxIdx, string role, bool isBull, bool isEntered,
                    string resText, color resColor, double entryPrice, double slPrice,
                    double riskPips, double &tps[], int hitTP, datetime entryTime,
                    int entryBarIdx, datetime exitTime, int smartScore, string scoreTier,
                    string filterReason, string exitPlan, string cancelReasonStr);
void CleanupFocusHUD();

//+------------------------------------------------------------------+
//| ورود به حالت تمرکز برای یک باکس (Focus Mode Activation)           |
//+------------------------------------------------------------------+
void EnterFocusMode(int boxIdx, bool toggle = true)
{
   if(boxIdx < 0 || boxIdx >= g_boxCount) return;

   string boxName = g_drawnBoxes[boxIdx].boxName;

   // اگر قبلاً روی همین باکس کلیک شده بود، در صورت فعال بودن toggle خروج از حالت تمرکز
   if(g_focusModeActive && g_focusBoxIdx == boxIdx)
   {
      if(toggle)
      {
         ExitFocusMode();
         return;
      }
   }

   // اگر روی باکس دیگری بودیم ابتدا پاکسازی شود
   if(g_focusModeActive)
   {
      ExitFocusMode();
   }

   g_focusModeActive  = true;
   g_focusBoxIdx      = boxIdx;
   g_selectedBoxName  = boxName;
   g_origFocusBoxName = boxName;

   if(ObjectFind(0, boxName) >= 0)
   {
      g_origFocusColor = (color)ObjectGetInteger(0, boxName, OBJPROP_COLOR);
      g_origFocusWidth = (int)ObjectGetInteger(0, boxName, OBJPROP_WIDTH);
      g_origFocusStyle = (ENUM_LINE_STYLE)ObjectGetInteger(0, boxName, OBJPROP_STYLE);
   }

   // ۱. پنهان‌سازی تمامی سایر باکس‌ها و برچسب‌ها روی چارت
   for(int b = 0; b < g_boxCount; b++)
   {
      if(b == boxIdx)
      {
         // هایلایت طلایی برجسته برای باکس انتخابی
         ObjectSetInteger(0, g_drawnBoxes[b].boxName, OBJPROP_TIMEFRAMES, OBJ_ALL_PERIODS);
         ObjectSetInteger(0, g_drawnBoxes[b].boxName, OBJPROP_COLOR, clrGold);
         ObjectSetInteger(0, g_drawnBoxes[b].boxName, OBJPROP_WIDTH, 3);
         ObjectSetInteger(0, g_drawnBoxes[b].boxName, OBJPROP_STYLE, STYLE_SOLID);
         ObjectSetInteger(0, g_drawnBoxes[b].boxName, OBJPROP_FILL,  false);
         ObjectSetInteger(0, g_drawnBoxes[b].boxName, OBJPROP_BACK,  false);

         string lblName = FP_PREFIX + "LBL_" + g_drawnBoxes[b].boxName;
         if(ObjectFind(0, lblName) >= 0)
            ObjectSetInteger(0, lblName, OBJPROP_TIMEFRAMES, OBJ_ALL_PERIODS);
      }
      else
      {
         // سایر باکس‌ها و برچسب‌های آنها موقتاً محو می‌شوند
         ObjectSetInteger(0, g_drawnBoxes[b].boxName, OBJPROP_TIMEFRAMES, OBJ_NO_PERIODS);
         string lblName = FP_PREFIX + "LBL_" + g_drawnBoxes[b].boxName;
         if(ObjectFind(0, lblName) >= 0)
            ObjectSetInteger(0, lblName, OBJPROP_TIMEFRAMES, OBJ_NO_PERIODS);
         string extName = FP_PREFIX + "EXT_" + g_drawnBoxes[b].boxName;
         if(ObjectFind(0, extName) >= 0)
            ObjectSetInteger(0, extName, OBJPROP_TIMEFRAMES, OBJ_NO_PERIODS);
      }
   }

   // ۲. موقتاً محو کردن خطوط معاملات اسکن خودکار قبلی
   int totalObjs = ObjectsTotal(0, 0, -1);
   for(int i = totalObjs - 1; i >= 0; i--)
   {
      string oName = ObjectName(0, i);
      if(StringFind(oName, FP_PREFIX + "AUTOTRADE_") == 0)
         ObjectSetInteger(0, oName, OBJPROP_TIMEFRAMES, OBJ_NO_PERIODS);
   }

   // ۳. شبیه‌سازی دقیق و رسم سطوح معامله باکس و پنل HUD
   ShowTradeSetupForBox(boxIdx);

   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| خروج از حالت تمرکز و بازگردانی چارت به وضعیت عادی (Exit Focus)   |
//+------------------------------------------------------------------+
void ExitFocusMode()
{
   if(!g_focusModeActive && g_selectedBoxName == "") return;

   // ۱. بازگردانی تمامی باکس‌ها و خطوط به وضعیت عادی
   for(int b = 0; b < g_boxCount; b++)
   {
      ObjectSetInteger(0, g_drawnBoxes[b].boxName, OBJPROP_TIMEFRAMES, OBJ_ALL_PERIODS);
      ObjectSetInteger(0, g_drawnBoxes[b].boxName, OBJPROP_COLOR, g_drawnBoxes[b].baseColor);
      ObjectSetInteger(0, g_drawnBoxes[b].boxName, OBJPROP_WIDTH, g_drawnBoxes[b].baseWidth);
      ObjectSetInteger(0, g_drawnBoxes[b].boxName, OBJPROP_STYLE, g_drawnBoxes[b].baseStyle);

      string lblName = FP_PREFIX + "LBL_" + g_drawnBoxes[b].boxName;
      if(ObjectFind(0, lblName) >= 0)
         ObjectSetInteger(0, lblName, OBJPROP_TIMEFRAMES, OBJ_ALL_PERIODS);

      string extName = FP_PREFIX + "EXT_" + g_drawnBoxes[b].boxName;
      if(ObjectFind(0, extName) >= 0)
         ObjectSetInteger(0, extName, OBJPROP_TIMEFRAMES, OBJ_ALL_PERIODS);
   }

   // ۲. بازگردانی خطوط معاملات اسکن خودکار
   int totalObjs = ObjectsTotal(0, 0, -1);
   for(int i = totalObjs - 1; i >= 0; i--)
   {
      string oName = ObjectName(0, i);
      if(StringFind(oName, FP_PREFIX + "AUTOTRADE_") == 0)
         ObjectSetInteger(0, oName, OBJPROP_TIMEFRAMES, OBJ_ALL_PERIODS);
   }

   // ۳. حذف تمام اشیاء معامله تعاملی و پنل اطلاعاتی
   ObjectsDeleteAll(0, FP_PREFIX + "CLICK_TRADE_");
   CleanupFocusHUD();
   Comment("");

   g_focusModeActive  = false;
   g_focusBoxIdx      = -1;
   g_selectedBoxName  = "";
   g_origFocusBoxName = "";

   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| پاکسازی پنل اطلاعاتی HUD                                         |
//+------------------------------------------------------------------+
void CleanupFocusHUD()
{
   ObjectsDeleteAll(0, FP_PREFIX + "FOCUS_HUD_");
}

//+------------------------------------------------------------------+
//| رسم پنل شیک اطلاعاتی HUD در بالای چارت                          |
//+------------------------------------------------------------------+
void RenderFocusHUD(int boxIdx, string role, bool isBull, bool isEntered,
                    string resText, color resColor, double entryPrice, double slPrice,
                    double riskPips, double &tps[], int hitTP, datetime entryTime,
                    int entryBarIdx, datetime exitTime, int smartScore, string scoreTier,
                    string filterReason, string exitPlan, string cancelReasonStr)
{
   CleanupFocusHUD();

   string pfx = FP_PREFIX + "FOCUS_HUD_";

   // ۱. پس‌زمینه پنل (OBJ_RECTANGLE_LABEL)
   string bgName = pfx + "BG";
   ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, bgName, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE, 20);
   ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE, 30);
   ObjectSetInteger(0, bgName, OBJPROP_XSIZE, 500);
   ObjectSetInteger(0, bgName, OBJPROP_YSIZE, 155);
   ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR, C'18,22,28');
   ObjectSetInteger(0, bgName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, bgName, OBJPROP_COLOR, clrGold);
   ObjectSetInteger(0, bgName, OBJPROP_WIDTH, 2);
   ObjectSetInteger(0, bgName, OBJPROP_BACK, false);
   ObjectSetInteger(0, bgName, OBJPROP_SELECTABLE, false);

   // ۲. ردیف ۰: عنوان پنل و نام باکس
   string l0 = pfx + "TITLE";
   ObjectCreate(0, l0, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, l0, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, l0, OBJPROP_XDISTANCE, 32);
   ObjectSetInteger(0, l0, OBJPROP_YDISTANCE, 38);
   string titleStr = StringFormat("🔍 حالت تمرکز (Focus) | باکس %s [%s] | %s",
                                  g_drawnBoxes[boxIdx].tfTag, role,
                                  isBull ? "BUY 🔵 (صعودی)" : "SELL 🟠 (نزولی)");
   ObjectSetString(0, l0, OBJPROP_TEXT, titleStr);
   ObjectSetString(0, l0, OBJPROP_FONT, "Segoe UI");
   ObjectSetInteger(0, l0, OBJPROP_FONTSIZE, 9);
   ObjectSetInteger(0, l0, OBJPROP_COLOR, clrGold);
   ObjectSetInteger(0, l0, OBJPROP_SELECTABLE, false);

   // ۳. ردیف ۱: نتیجه و وضعیت ورود
   string l1 = pfx + "STATUS";
   ObjectCreate(0, l1, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, l1, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, l1, OBJPROP_XDISTANCE, 32);
   ObjectSetInteger(0, l1, OBJPROP_YDISTANCE, 58);
   string statusStr = "";
   if(isEntered)
   {
      double rMultiple = (hitTP > 0) ? (double)hitTP : -1.0;
      statusStr = StringFormat("📊 وضعیت: %s | ریسک: %.1f پیپ | R:R معادل: 1:%.0f",
                               resText, riskPips, (hitTP > 0 ? (double)hitTP : 0.0));
   }
   else
   {
      statusStr = StringFormat("⚠️ وضعیت عدم ورود: %s",
                               (cancelReasonStr != "" ? cancelReasonStr : "در انتظار پولبک معتبر"));
   }
   ObjectSetString(0, l1, OBJPROP_TEXT, statusStr);
   ObjectSetString(0, l1, OBJPROP_FONT, "Segoe UI");
   ObjectSetInteger(0, l1, OBJPROP_FONTSIZE, 9);
   ObjectSetInteger(0, l1, OBJPROP_COLOR, resColor);
   ObjectSetInteger(0, l1, OBJPROP_SELECTABLE, false);

   // ۴. ردیف ۲: سطوح قیمتی ورود و استاپ
   string l2 = pfx + "PRICES";
   ObjectCreate(0, l2, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, l2, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, l2, OBJPROP_XDISTANCE, 32);
   ObjectSetInteger(0, l2, OBJPROP_YDISTANCE, 78);
   string priceStr = StringFormat("📍 ورود: %s  |  🛑 استاپ: %s  |  🎯 TP1: %s  |  TP2: %s",
                                  DoubleToString(entryPrice, _Digits),
                                  DoubleToString(slPrice, _Digits),
                                  DoubleToString(tps[0], _Digits),
                                  DoubleToString(tps[1], _Digits));
   ObjectSetString(0, l2, OBJPROP_TEXT, priceStr);
   ObjectSetString(0, l2, OBJPROP_FONT, "Consolas");
   ObjectSetInteger(0, l2, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, l2, OBJPROP_COLOR, clrWhiteSmoke);
   ObjectSetInteger(0, l2, OBJPROP_SELECTABLE, false);

   // ۵. ردیف ۳: اطلاعات زمانی و کندلی
   string l3 = pfx + "TIMING";
   ObjectCreate(0, l3, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, l3, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, l3, OBJPROP_XDISTANCE, 32);
   ObjectSetInteger(0, l3, OBJPROP_YDISTANCE, 98);
   string timeStr = "";
   if(isEntered && entryTime > 0)
   {
      timeStr = StringFormat("⏱ تاچ ورود: %s (کندل #%d)  |  خروج: %s",
                             TimeToString(entryTime, TIME_DATE|TIME_MINUTES),
                             entryBarIdx,
                             (exitTime > 0 ? TimeToString(exitTime, TIME_DATE|TIME_MINUTES) : "در جریان"));
   }
   else
   {
      datetime baseTime = (g_drawnBoxes[boxIdx].formationTime > 0) ? g_drawnBoxes[boxIdx].formationTime : g_drawnBoxes[boxIdx].t1;
      timeStr = StringFormat("⏱ تشکیل باکس: %s  |  تایید ساختار: %s",
                             TimeToString(baseTime, TIME_DATE|TIME_MINUTES),
                             (g_drawnBoxes[boxIdx].confirmationTime > 0 ? TimeToString(g_drawnBoxes[boxIdx].confirmationTime, TIME_DATE|TIME_MINUTES) : "همزمان"));
   }
   ObjectSetString(0, l3, OBJPROP_TEXT, timeStr);
   ObjectSetString(0, l3, OBJPROP_FONT, "Segoe UI");
   ObjectSetInteger(0, l3, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, l3, OBJPROP_COLOR, clrDarkGray);
   ObjectSetInteger(0, l3, OBJPROP_SELECTABLE, false);

   // ۶. ردیف ۴: امتیاز سلاطین و فیلتر
   string l4 = pfx + "SCORE";
   ObjectCreate(0, l4, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, l4, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, l4, OBJPROP_XDISTANCE, 32);
   ObjectSetInteger(0, l4, OBJPROP_YDISTANCE, 118);
   string scoreStr = StringFormat("👑 شاخص سلاطین: %d/100 [%s]  |  فیلتر ضد استاپ: %s",
                                  smartScore, scoreTier, filterReason);
   ObjectSetString(0, l4, OBJPROP_TEXT, scoreStr);
   ObjectSetString(0, l4, OBJPROP_FONT, "Segoe UI");
   ObjectSetInteger(0, l4, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, l4, OBJPROP_COLOR, clrMediumTurquoise);
   ObjectSetInteger(0, l4, OBJPROP_SELECTABLE, false);

   // ۷. ردیف ۵: راهنمای کلیدها جهت خروج
   string l5 = pfx + "HINT";
   ObjectCreate(0, l5, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, l5, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, l5, OBJPROP_XDISTANCE, 32);
   ObjectSetInteger(0, l5, OBJPROP_YDISTANCE, 138);
   ObjectSetString(0, l5, OBJPROP_TEXT, "⌨️ کلید [Esc] یا کلیک روی فضای خالی چارت: بازگشت به نمای عادی همه باکس‌ها");
   ObjectSetString(0, l5, OBJPROP_FONT, "Segoe UI");
   ObjectSetInteger(0, l5, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, l5, OBJPROP_COLOR, clrDarkGoldenrod);
   ObjectSetInteger(0, l5, OBJPROP_SELECTABLE, false);
}

//+------------------------------------------------------------------+
//| شبیه‌سازی کامل معامله باکس و ترسیم سطوح روی چارت                  |
//+------------------------------------------------------------------+
void ShowTradeSetupForBox(int boxIdx)
{
   ObjectsDeleteAll(0, FP_PREFIX + "CLICK_TRADE_");
   if(boxIdx < 0 || boxIdx >= g_boxCount) return;

   // غیرفعال‌سازی معامله برای تایم‌های ماکرو H1 و بالاتر
   if(!InpTradeMacroTFs && g_drawnBoxes[boxIdx].tf >= PERIOD_H1)
   {
      Comment(StringFormat("\n📦 باکس %s [%s]\n⚠️ معامله در تایم‌های ماکرو (H1 و بالاتر) غیرفعال است (فقط تایم‌های M1, M5, M15 مجازند).",
                           g_drawnBoxes[boxIdx].tfTag, g_drawnBoxes[boxIdx].boxName));
      PrintFormat("FlagPro: معامله برای تایم %s غیرفعال است (فقط M1, M5, M15 فعال هستند).", g_drawnBoxes[boxIdx].tfTag);
      return;
   }

   datetime chartTime[];
   double chartHigh[], chartLow[], chartClose[];
   int chartSpread[];
   ArraySetAsSeries(chartTime, false);
   ArraySetAsSeries(chartHigh, false);
   ArraySetAsSeries(chartLow, false);
   ArraySetAsSeries(chartClose, false);
   ArraySetAsSeries(chartSpread, false);

   int copied = CopyTime(_Symbol, _Period, 0, 250000, chartTime);
   CopyHigh(_Symbol, _Period, 0, 250000, chartHigh);
   CopyLow(_Symbol, _Period, 0, 250000, chartLow);
   CopyClose(_Symbol, _Period, 0, 250000, chartClose);
   CopySpread(_Symbol, _Period, 0, 250000, chartSpread);
   if(copied < 10) return;

   string role = "Flag";
   bool isSwap = g_drawnBoxes[boxIdx].isSwap;
   bool isLS   = false;
   bool isRS   = false;
   bool isOI   = false;
   string swapTag = "";

   if(isSwap)
   {
      role = "S-" + g_drawnBoxes[boxIdx].swapSourceRole;
   }
   else
   {
      for(int tg = 0; tg < ArraySize(g_drawnBoxes[boxIdx].rsTags); tg++)
      {
         string tgName = g_drawnBoxes[boxIdx].rsTags[tg];
         if(tgName == "LS") isLS = true;
         else if(tgName == "RS") isRS = true;
         else if(tgName == "OInner") isOI = true;
         else if(StringFind(tgName, "S-") == 0)
         {
            isSwap = true;
            swapTag += (swapTag == "" ? "" : "+") + tgName;
         }
      }

      string tagCombo = "";
      if(isLS)
      {
         string lsDir = g_drawnBoxes[boxIdx].isLSBull ? "-BU" : "-BE";
         tagCombo += (tagCombo == "" ? "LS" + lsDir : " > LS" + lsDir);
      }
      if(isOI)
      {
         string oiDir = g_drawnBoxes[boxIdx].isOInnerBull ? "-BU" : "-BE";
         tagCombo += (tagCombo == "" ? "OInner" + oiDir : " > OInner" + oiDir);
      }
      if(isRS)
      {
         string rsDir = g_drawnBoxes[boxIdx].isRSBull ? "-BU" : "-BE";
         tagCombo += (tagCombo == "" ? "RS" + rsDir : " > RS" + rsDir);
      }
      if(isSwap)
      {
         string swDir = g_drawnBoxes[boxIdx].isSwapBull ? "-BU" : "-BE";
         string fullSwap = swapTag + swDir;
         tagCombo += (tagCombo == "" ? fullSwap : " > " + fullSwap);
      }
      if(tagCombo != "") role = tagCombo;
      else role = "Flag-" + (g_drawnBoxes[boxIdx].isBullish ? "BU" : "BE");
   }

   // بررسی شرط سلاطین طلایی در صورت فعال بودن فیلتر سلاطین
   if((InpOnlyTradeKings || InpTradeOnlyGoldenKings) && !IsQualifiedKing(g_drawnBoxes[boxIdx].tf, role))
   {
      string noTradeMsg = StringFormat(
         "═══════════════════════════════════════════════════\n"
         "📦 باکس %s [%s]\n"
         "⚠️ این ساختار جزو سلاطین برگزیده معامله نیست.\n"
         "👑 فیلتر سلاطین روشن است و معامله فقط روی الگوهای برتر مجاز است.\n"
         "═══════════════════════════════════════════════════",
         g_drawnBoxes[boxIdx].tfTag, role);
      Comment(noTradeMsg);
      Print(noTradeMsg);
      return;
   }

   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;
   double bufferPips = ActiveSLOffsetPips() * pipSize;

   bool isBull = true;
   double entryPrice = 0;
   double slPrice    = 0;

   double pivotP = 0;
   if(isOI)
   {
      isBull = g_drawnBoxes[boxIdx].isOInnerBull; // جهت ترید حتماً جهت خود گره OInner است

      datetime closestPivotTime = 0;
      for(int k = 0; k < g_indepCount; k++)
      {
         if(!g_indepPivots[k].hasIP) continue;
         if(!IsPivotTimeframeMatch(k, g_drawnBoxes[boxIdx].tfTag)) continue;
         if(g_indepPivots[k].time <= g_drawnBoxes[boxIdx].t1)
         {
            bool pivotValidForTrade = (isBull ? !g_indepPivots[k].isHigh : g_indepPivots[k].isHigh);
            if(pivotValidForTrade)
            {
               if(closestPivotTime == 0 || g_indepPivots[k].time > closestPivotTime)
               {
                  closestPivotTime = g_indepPivots[k].time;
                  pivotP = g_indepPivots[k].price;
               }
            }
         }
      }
   }
   else
   {
      if(isSwap) isBull = g_drawnBoxes[boxIdx].isSwapBull;
      else if(isRS) isBull = g_drawnBoxes[boxIdx].isRSBull;
      else if(isLS) isBull = g_drawnBoxes[boxIdx].isLSBull;
      else isBull = g_drawnBoxes[boxIdx].isBullish;
   }

   int bStartIdx = FindBarIndex(chartTime, copied, g_drawnBoxes[boxIdx].t1);
   datetime formEnd = (g_drawnBoxes[boxIdx].formationTime > 0) ? g_drawnBoxes[boxIdx].formationTime : g_drawnBoxes[boxIdx].t1;
   int bEndIdx   = FindBarIndex(chartTime, copied, formEnd);
   if(bEndIdx < bStartIdx) bEndIdx = bStartIdx;

   double patternHigh = g_drawnBoxes[boxIdx].top;
   double patternLow  = g_drawnBoxes[boxIdx].bottom;

   if(isOI && pivotP > 0)
   {
      if(pivotP > patternHigh) patternHigh = pivotP;
      if(pivotP < patternLow)  patternLow  = pivotP;
   }

   for(int ck = bStartIdx; ck <= bEndIdx && ck < copied; ck++)
   {
      if(chartHigh[ck] > patternHigh) patternHigh = chartHigh[ck];
      if(chartLow[ck] < patternLow)   patternLow  = chartLow[ck];
   }

   if(isBull)
   {
      entryPrice = g_drawnBoxes[boxIdx].top;
      slPrice    = patternLow - bufferPips;
   }
   else
   {
      entryPrice = g_drawnBoxes[boxIdx].bottom;
      slPrice    = patternHigh + bufferPips;
   }

   double risk = MathAbs(entryPrice - slPrice);
   if(risk < _Point * 2.0) risk = _Point * 2.0;

   double tps[4];
   datetime tpHitTime[4] = {0, 0, 0, 0};
   for(int tp = 0; tp < 4; tp++)
   {
      if(isBull) tps[tp] = entryPrice + risk * (tp + 1);
      else       tps[tp] = entryPrice - risk * (tp + 1);
   }

   datetime baseTime = (g_drawnBoxes[boxIdx].formationTime > 0) ? g_drawnBoxes[boxIdx].formationTime : g_drawnBoxes[boxIdx].t1;
   datetime confirmTime = g_drawnBoxes[boxIdx].confirmationTime;
   if(confirmTime <= 0 || confirmTime > baseTime + PeriodSeconds(g_drawnBoxes[boxIdx].tf) * 15)
      confirmTime = baseTime;

   int confirmIdx = FindBarIndex(chartTime, copied, confirmTime);
   if(confirmIdx < 0) confirmIdx = FindBarIndex(chartTime, copied, baseTime);
   if(confirmIdx < 0) confirmIdx = 0;

   double boxHeight = MathAbs(g_drawnBoxes[boxIdx].top - g_drawnBoxes[boxIdx].bottom);
   double minDeparturePrice = isBull ? (entryPrice + boxHeight * 0.3) : (entryPrice - boxHeight * 0.3);

   bool isEntered = false;
   int  entryBarIdx = -1;
   datetime entryTime = 0;
   int departedBar = -1;

   double simSpread = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * _Point;
   if(simSpread <= 0) simSpread = 1.0 * pipSize;

   datetime maxBoxTime = baseTime + PeriodSeconds(g_drawnBoxes[boxIdx].tf) * 40;

   int cancelBarIdx = -1;
   string cancelReasonStr = "";

   for(int k = confirmIdx; k < copied; k++)
   {
      // ابطال ۱: انقضای زمانی معامله با گذشت از اعتبار باکس
      if(chartTime[k] > maxBoxTime)
      {
         cancelBarIdx = k;
         cancelReasonStr = "EXPIRED ⏱ (پایان اعتبار زمانی باکس)";
         break;
      }

      // ابطال ۲: برخورد قیمت به حد ضرر در هر زمان ستاپ را فوراً لغو می‌کند
      if(isBull)
      {
         if(chartLow[k] <= slPrice)
         {
            cancelBarIdx = k;
            cancelReasonStr = "CANCELLED ❌ (نقض حد ضرر قبل از ورود)";
            break;
         }
      }
      else
      {
         double barSpread = GetBarSpread(k, chartSpread, simSpread);
         if((chartHigh[k] + barSpread) >= slPrice)
         {
            cancelBarIdx = k;
            cancelReasonStr = "CANCELLED ❌ (نقض حد ضرر قبل از ورود)";
            break;
         }
      }

      if(departedBar < 0)
      {
         // تایید پرتاب و کلوز کامل کندل در بیرون از باکس
         if(isBull && chartClose[k] >= minDeparturePrice) departedBar = k;
         else if(!isBull && chartClose[k] <= minDeparturePrice) departedBar = k;

         // مهلت خروج اولیه از باکس حداکثر ۳۰ کندل
         datetime maxDepTime = confirmTime + PeriodSeconds(g_drawnBoxes[boxIdx].tf) * 30;
         if(chartTime[k] > maxDepTime)
         {
            cancelBarIdx = k;
            cancelReasonStr = "NO BREAKOUT ⏱ (عدم خروج قیمت از گره)";
            break;
         }
      }
      else // ورود منحصراً روی کندل‌های بعد از پرتاب اولیه (پولبک واقعی)
      {
         double barSpread = GetBarSpread(k, chartSpread, simSpread);

         if(isBull)
         {
            if((chartLow[k] + barSpread) <= entryPrice)
            {
               isEntered = true;
               entryBarIdx = k;
               entryTime = chartTime[k];
               break;
            }
         }
         else
         {
            if(chartHigh[k] >= entryPrice)
            {
               isEntered = true;
               entryBarIdx = k;
               entryTime = chartTime[k];
               break;
            }
         }

         // مهلت بازگشت پولبک بر مبنای تایم‌فریم الگو و پارامتر ورودی InpLimitExpirationBars
         datetime maxLimitTime = chartTime[departedBar] + PeriodSeconds(g_drawnBoxes[boxIdx].tf) * ActiveLimitExpirationBars();
         if(chartTime[k] > maxLimitTime)
         {
            cancelBarIdx = k;
            cancelReasonStr = "NO PULLBACK 💨 (پرتاب مستقیم بدون پولبک)";
            break;
         }
      }
   }

   int hitTP = -1;
   bool isClosed = false;
   datetime exitTime = 0;

   if(isEntered)
   {
      // به‌روزرسانی نهایی حد ضرر و ریسک بر مبنای نوک واقعی شدوها تا لحظه ورود
      for(int ck = bStartIdx; ck <= entryBarIdx && ck < copied; ck++)
      {
         if(chartHigh[ck] > patternHigh) patternHigh = chartHigh[ck];
         if(chartLow[ck] < patternLow)   patternLow  = chartLow[ck];
      }

      if(isBull) slPrice = patternLow - bufferPips;
      else       slPrice = patternHigh + bufferPips;

      risk = MathAbs(entryPrice - slPrice);
      if(risk < _Point * 2.0) risk = _Point * 2.0;

      for(int tp = 0; tp < 4; tp++)
      {
         if(isBull) tps[tp] = entryPrice + risk * (tp + 1);
         else       tps[tp] = entryPrice - risk * (tp + 1);
      }

      int maxHit = 0;
      datetime hitTime = 0;
      for(int k = entryBarIdx; k < copied; k++)
      {
         if(isBull)
         {
            for(int tp = maxHit; tp < 4; tp++)
            {
               if(chartHigh[k] >= tps[tp])
               {
                  maxHit = tp + 1;
                  hitTime = chartTime[k];
                  if(tpHitTime[tp] == 0) tpHitTime[tp] = chartTime[k];
               }
            }

            if(chartLow[k] <= slPrice)
            {
               hitTP = maxHit;
               isClosed = true;
               exitTime = (maxHit > 0) ? hitTime : chartTime[k];
               break;
            }

            if(maxHit == 4)
            {
               hitTP = 4;
               isClosed = true;
               exitTime = hitTime;
               break;
            }
         }
         else // SELL
         {
            double barSpread = GetBarSpread(k, chartSpread, simSpread);
            for(int tp = maxHit; tp < 4; tp++)
            {
               if((chartLow[k] + barSpread) <= tps[tp])
               {
                  maxHit = tp + 1;
                  hitTime = chartTime[k];
                  if(tpHitTime[tp] == 0) tpHitTime[tp] = chartTime[k];
               }
            }

            if((chartHigh[k] + barSpread) >= slPrice)
            {
               hitTP = maxHit;
               isClosed = true;
               exitTime = (maxHit > 0) ? hitTime : chartTime[k];
               break;
            }

            if(maxHit == 4)
            {
               hitTP = 4;
               isClosed = true;
               exitTime = hitTime;
               break;
            }
         }
      }

      if(!isClosed)
      {
         hitTP = maxHit;
         exitTime = (maxHit > 0) ? hitTime : chartTime[copied - 1];
      }
   }

   string pfx = FP_PREFIX + "CLICK_TRADE_";

   // انتخاب پالت رنگی معامله
   color tradeClr = InpUniqueTradeColors ? GetTradeSetupColor(boxIdx) : InpTradeTPColor;
   color entryClr = InpUniqueTradeColors ? tradeClr : InpTradeEntryColor;
   color slClr    = InpUniqueTradeColors ? tradeClr : InpTradeSLColor;
   color tpClr    = InpUniqueTradeColors ? tradeClr : InpTradeTPColor;

   string resText = "";
   color resColor = clrSilver;

   if(!isEntered)
   {
      if(cancelReasonStr != "")
      {
         resText = cancelReasonStr;
         resColor = (StringFind(cancelReasonStr, "CANCELLED") >= 0) ? clrSandyBrown : clrSilver;
      }
      else
      {
         resText = "PENDING ⏳ (در انتظار پولبک لایو)";
         resColor = clrGold;
      }
   }
   else if(hitTP == 4)   { resText = "WIN 1:4 🎯 (تارگت ۴)"; resColor = clrLime; }
   else if(hitTP == 3)   { resText = "WIN 1:3 🚀 (تارگت ۳)"; resColor = clrSpringGreen; }
   else if(hitTP == 2)   { resText = "WIN 1:2 ✨ (تارگت ۲)"; resColor = clrMediumSpringGreen; }
   else if(hitTP == 1)   { resText = "WIN 1:1 👍 (تارگت ۱)"; resColor = clrAqua; }
   else if(isClosed)     { resText = "STOP LOSS ❌ (حد ضرر)"; resColor = clrCrimson; }
   else                  { resText = "IN TRADE ⏱ (معامله باز)"; resColor = clrGold; }

   double riskPts = (_Point > 0) ? (risk / _Point) : 0.0;
   double slPips  = risk / pipSize;
   bool isFiltered = IsSetupFilteredOut(role, (entryTime > 0 ? entryTime : baseTime), riskPts);
   string filterReason = isFiltered ? GetFilterRejectionReason(role, (entryTime > 0 ? entryTime : baseTime), riskPts) : "مجاز (تایید فیلترها) ✅";

   int smartScore = CalculateSmartSetupScore(role, (entryTime > 0 ? entryTime : baseTime), riskPts);
   string scoreTier = GetSmartScoreTier(smartScore);
   string exitPlan = GetRecommendedExitPlan(smartScore, role);

   // اگر ورود انجام شده باشد، خطوط گرافیکی ستاپ روی چارت ترسیم شوند
   if(isEntered)
   {
      datetime t1 = entryTime;
      datetime t2 = exitTime;
      if(t2 <= t1) t2 = t1 + PeriodSeconds(_Period) * 10;

      // خط عمودی زمان تایید
      string confLine = pfx + "CONFIRM_VLINE";
      ObjectCreate(0, confLine, OBJ_VLINE, 0, confirmTime, 0);
      ObjectSetInteger(0, confLine, OBJPROP_COLOR, clrDarkTurquoise);
      ObjectSetInteger(0, confLine, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, confLine, OBJPROP_STYLE, STYLE_DOT);
      ObjectSetInteger(0, confLine, OBJPROP_SELECTABLE, false);

      string confLbl = pfx + "CONFIRM_LBL";
      ObjectCreate(0, confLbl, OBJ_TEXT, 0, confirmTime, isBull ? g_drawnBoxes[boxIdx].top : g_drawnBoxes[boxIdx].bottom);
      ObjectSetString(0, confLbl, OBJPROP_TEXT, "📍 زمان تایید لایو");
      ObjectSetInteger(0, confLbl, OBJPROP_COLOR, clrDarkTurquoise);
      ObjectSetInteger(0, confLbl, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, confLbl, OBJPROP_ANCHOR, isBull ? ANCHOR_LOWER : ANCHOR_UPPER);
      ObjectSetInteger(0, confLbl, OBJPROP_SELECTABLE, false);

      // پس‌زمینه رنگی محدوده سود و زیان (Shading)
      if(InpShowTradeShading)
      {
         double tpTop = isBull ? tps[3] : entryPrice;
         double tpBtm = isBull ? entryPrice : tps[3];
         string profitZone = pfx + "PROFIT_BG";
         ObjectCreate(0, profitZone, OBJ_RECTANGLE, 0, t1, tpTop, t2, tpBtm);
         ObjectSetInteger(0, profitZone, OBJPROP_COLOR, C'15,35,55');
         ObjectSetInteger(0, profitZone, OBJPROP_FILL, true);
         ObjectSetInteger(0, profitZone, OBJPROP_BACK, true);
         ObjectSetInteger(0, profitZone, OBJPROP_SELECTABLE, false);

         double slTop = isBull ? entryPrice : slPrice;
         double slBtm = isBull ? slPrice : entryPrice;
         string lossZone = pfx + "LOSS_BG";
         ObjectCreate(0, lossZone, OBJ_RECTANGLE, 0, t1, slTop, t2, slBtm);
         ObjectSetInteger(0, lossZone, OBJPROP_COLOR, C'55,35,15');
         ObjectSetInteger(0, lossZone, OBJPROP_FILL, true);
         ObjectSetInteger(0, lossZone, OBJPROP_BACK, true);
         ObjectSetInteger(0, lossZone, OBJPROP_SELECTABLE, false);
      }

      // خط نقطه ورود (Entry Line)
      string entryLine = pfx + "ENTRY";
      ObjectCreate(0, entryLine, OBJ_TREND, 0, t1, entryPrice, t2, entryPrice);
      ObjectSetInteger(0, entryLine, OBJPROP_COLOR, entryClr);
      ObjectSetInteger(0, entryLine, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, entryLine, OBJPROP_STYLE, STYLE_DASH);
      ObjectSetInteger(0, entryLine, OBJPROP_RAY_RIGHT, false);
      ObjectSetInteger(0, entryLine, OBJPROP_SELECTABLE, false);

      string entryLbl = pfx + "ENTRY_LBL";
      ObjectCreate(0, entryLbl, OBJ_TEXT, 0, t1, entryPrice);
      ObjectSetString(0, entryLbl, OBJPROP_TEXT, " ENTRY");
      ObjectSetInteger(0, entryLbl, OBJPROP_COLOR, entryClr);
      ObjectSetInteger(0, entryLbl, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, entryLbl, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(0, entryLbl, OBJPROP_SELECTABLE, false);

      // خط حد ضرر (Stop Loss)
      string slLine = pfx + "SL";
      ObjectCreate(0, slLine, OBJ_TREND, 0, t1, slPrice, t2, slPrice);
      ObjectSetInteger(0, slLine, OBJPROP_COLOR, slClr);
      ObjectSetInteger(0, slLine, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, slLine, OBJPROP_STYLE, STYLE_DOT);
      ObjectSetInteger(0, slLine, OBJPROP_RAY_RIGHT, false);
      ObjectSetInteger(0, slLine, OBJPROP_SELECTABLE, false);

      string slLbl = pfx + "SL_LBL";
      ObjectCreate(0, slLbl, OBJ_TEXT, 0, t2, slPrice);
      ObjectSetString(0, slLbl, OBJPROP_TEXT, " SL");
      ObjectSetInteger(0, slLbl, OBJPROP_COLOR, slClr);
      ObjectSetInteger(0, slLbl, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, slLbl, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(0, slLbl, OBJPROP_SELECTABLE, false);

      // خطوط تارگت‌های ۴ گانه
      for(int tp = 0; tp < 4; tp++)
      {
         datetime tpEnd = (tpHitTime[tp] > 0) ? tpHitTime[tp] : t2;
         if(tpEnd <= t1) tpEnd = t1 + PeriodSeconds(_Period);

         string tpLine = pfx + "TP" + IntegerToString(tp + 1);
         ObjectCreate(0, tpLine, OBJ_TREND, 0, t1, tps[tp], tpEnd, tps[tp]);
         ObjectSetInteger(0, tpLine, OBJPROP_COLOR, tpClr);
         ObjectSetInteger(0, tpLine, OBJPROP_WIDTH, (hitTP >= tp + 1 ? 2 : 1));
         ObjectSetInteger(0, tpLine, OBJPROP_STYLE, (hitTP >= tp + 1 ? STYLE_SOLID : STYLE_DOT));
         ObjectSetInteger(0, tpLine, OBJPROP_RAY_RIGHT, false);
         ObjectSetInteger(0, tpLine, OBJPROP_SELECTABLE, false);

         string tpLbl = tpLine + "_LBL";
         ObjectCreate(0, tpLbl, OBJ_TEXT, 0, tpEnd, tps[tp]);
         ObjectSetString(0, tpLbl, OBJPROP_TEXT, "TP" + IntegerToString(tp + 1) + " (1:" + IntegerToString(tp + 1) + ")");
         ObjectSetInteger(0, tpLbl, OBJPROP_COLOR, tpClr);
         ObjectSetInteger(0, tpLbl, OBJPROP_FONTSIZE, 8);
         ObjectSetInteger(0, tpLbl, OBJPROP_ANCHOR, (isBull ? ANCHOR_LOWER : ANCHOR_UPPER));
         ObjectSetInteger(0, tpLbl, OBJPROP_SELECTABLE, false);
      }

      // برچسب نتیجه روی انتهای خط ورود
      string resLbl = pfx + "RESULT_LBL";
      ObjectCreate(0, resLbl, OBJ_TEXT, 0, t2, entryPrice);
      ObjectSetString(0, resLbl, OBJPROP_TEXT, " " + role + " " + (isBull ? "BUY" : "SELL") + " -> " + resText);
      ObjectSetInteger(0, resLbl, OBJPROP_COLOR, resColor);
      ObjectSetInteger(0, resLbl, OBJPROP_FONTSIZE, 9);
      ObjectSetInteger(0, resLbl, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(0, resLbl, OBJPROP_SELECTABLE, false);
   }

   // رسم پنل اطلاعاتی پیشرفته HUD در بالای چارت
   RenderFocusHUD(boxIdx, role, isBull, isEntered, resText, resColor,
                  entryPrice, slPrice, slPips, tps, hitTP, entryTime,
                  entryBarIdx, exitTime, smartScore, scoreTier, filterReason,
                  exitPlan, cancelReasonStr);

   // ثبت در کامنت چارت و لاگ ترمینال
   string tradeType = isBull ? "BUY 🔵" : "SELL 🟠";
   string dirFarsi  = isBull ? "خرید (گره صعودی)" : "فروش (گره نزولی)";

   string logMsg = StringFormat(
      "═══════════════════════════════════════════════════\n"
      "🎯 [FlagPro ستاپ معامله - حالت تمرکز]\n"
      "📦 گره / باکس: %s [%s]\n"
      "💎 امتیاز هوشمند ستاپ: %d / 100 [%s]\n"
      "📋 برنامه خروج پیشنهادی: %s\n"
      "🛡️ وضعیت فیلتر ضد استاپ: %s\n"
      "⚡ سیگنال: %s | %s\n"
      "📍 نقطه ورود (Entry): %s\n"
      "🛑 حد ضرر (Stop Loss): %s (ریسک: %.1f پیپ)\n"
      "🎯 تارگت ۱: %s (1:1) | تارگت ۲: %s (1:2)\n"
      "🎯 تارگت ۳: %s (1:3) | تارگت ۴: %s (1:4)\n"
      "📊 وضعیت: %s\n"
      "⌨️ جهت خروج از حالت تمرکز: کلید [Esc] یا کلیک روی فضای خالی چارت\n"
      "═══════════════════════════════════════════════════",
      g_drawnBoxes[boxIdx].tfTag, role,
      smartScore, scoreTier,
      exitPlan,
      filterReason,
      tradeType, dirFarsi,
      DoubleToString(entryPrice, _Digits),
      DoubleToString(slPrice, _Digits), slPips,
      DoubleToString(tps[0], _Digits), DoubleToString(tps[1], _Digits),
      DoubleToString(tps[2], _Digits), DoubleToString(tps[3], _Digits),
      resText
   );

   Comment(logMsg);
   Print(logMsg);
}
