//+------------------------------------------------------------------+
//| Flag_TradeTestModule.mqh                                         |
//| Dedicated Interactive Trade Test Module & Box Focus Mode Engine  |
//| FlagPro Quantitative Trading Systems                             |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""

// متغیرهای وضعیت حالت تمرکز (Focus Mode)
bool            g_focusModeActive         = false;
int             g_focusBoxIdx             = -1;
string          g_origFocusBoxName        = "";
color           g_origFocusColor          = clrNONE;
int             g_origFocusWidth          = 1;
ENUM_LINE_STYLE g_origFocusStyle          = STYLE_SOLID;
ulong           g_lastTradeTestActionTick = 0;

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
                    string filterReason, string exitPlan, string cancelReasonStr,
                    bool isFiltered = false);
void CleanupFocusHUD();

//+------------------------------------------------------------------+
//| پاکسازی پنل اطلاعاتی HUD                                         |
//+------------------------------------------------------------------+
void CleanupFocusHUD()
{
   ObjectsDeleteAll(0, FP_PREFIX + "FOCUS_HUD_");
}

//+------------------------------------------------------------------+
//| خروج از حالت تمرکز و بازگردانی چارت به وضعیت عادی (Exit Focus)   |
//+------------------------------------------------------------------+
void ExitFocusMode()
{
   if(!g_focusModeActive && g_selectedBoxName == "") return;

   // ۱. بازگردانی خصوصیات اختصاصی باکس فوکوس‌شده
   if(g_focusBoxIdx >= 0 && g_focusBoxIdx < g_boxCount)
   {
      string fName = g_drawnBoxes[g_focusBoxIdx].boxName;
      if(ObjectFind(0, fName) >= 0)
      {
         if(g_origFocusColor != clrNONE)
            ObjectSetInteger(0, fName, OBJPROP_COLOR, g_origFocusColor);
         ObjectSetInteger(0, fName, OBJPROP_WIDTH, g_origFocusWidth > 0 ? g_origFocusWidth : 1);
         ObjectSetInteger(0, fName, OBJPROP_STYLE, g_origFocusStyle);
      }
   }

   // ۲. نمایان‌سازی تمام باکس‌ها (دست‌نخورده ماندن رنگ‌ها و استایل‌ها)
   for(int b = 0; b < g_boxCount; b++)
   {
      ObjectSetInteger(0, g_drawnBoxes[b].boxName, OBJPROP_TIMEFRAMES, OBJ_ALL_PERIODS);

      string lblName = FP_PREFIX + "LBL_" + g_drawnBoxes[b].boxName;
      if(ObjectFind(0, lblName) >= 0)
         ObjectSetInteger(0, lblName, OBJPROP_TIMEFRAMES, OBJ_ALL_PERIODS);

      string extName = FP_PREFIX + "EXT_" + g_drawnBoxes[b].boxName;
      if(ObjectFind(0, extName) >= 0)
         ObjectSetInteger(0, extName, OBJPROP_TIMEFRAMES, OBJ_ALL_PERIODS);
   }

   // ۳. نمایان‌سازی مجدد خطوط ساختار و معاملات خودکار
   int totalObjs = ObjectsTotal(0, 0, -1);
   for(int i = totalObjs - 1; i >= 0; i--)
   {
      string oName = ObjectName(0, i);
      if(StringFind(oName, FP_PREFIX + "IP_") == 0 ||
         StringFind(oName, FP_PREFIX + "RS_") == 0 ||
         StringFind(oName, FP_PREFIX + "SWAP_") == 0 ||
         StringFind(oName, FP_PREFIX + "STRUCT_") == 0 ||
         StringFind(oName, FP_PREFIX + "PIVOT_") == 0 ||
         StringFind(oName, FP_PREFIX + "AUTO_TR_") == 0 ||
         StringFind(oName, FP_PREFIX + "AUTOTRADE_") == 0)
      {
         ObjectSetInteger(0, oName, OBJPROP_TIMEFRAMES, OBJ_ALL_PERIODS);
      }
   }

   // ۴. حذف کامل خطوط معامله کلیک و پنل HUD
   ObjectsDeleteAll(0, FP_PREFIX + "CLICK_TRADE_");
   CleanupFocusHUD();
   Comment("");

   g_focusModeActive  = false;
   g_focusBoxIdx      = -1;
   g_selectedBoxName  = "";
   g_origFocusBoxName = "";
   g_origFocusColor   = clrNONE;

   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| ورود به حالت تمرکز برای یک باکس (Focus Mode Activation)           |
//+------------------------------------------------------------------+
void EnterFocusMode(int boxIdx, bool toggle = true)
{
   if(boxIdx < 0 || boxIdx >= g_boxCount) return;

   string boxName = g_drawnBoxes[boxIdx].boxName;

   // اگر قبلاً روی همین باکس بودیم و toggle فعال است، خروج
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

   // ذخیره ویژگی‌های اصلی فقط همین باکس
   if(ObjectFind(0, boxName) >= 0)
   {
      g_origFocusColor = (color)ObjectGetInteger(0, boxName, OBJPROP_COLOR);
      g_origFocusWidth = (int)ObjectGetInteger(0, boxName, OBJPROP_WIDTH);
      g_origFocusStyle = (ENUM_LINE_STYLE)ObjectGetInteger(0, boxName, OBJPROP_STYLE);
   }

   // ۱. برجسته‌سازی طلایی باکس انتخابی
   ObjectSetInteger(0, boxName, OBJPROP_TIMEFRAMES, OBJ_ALL_PERIODS);
   ObjectSetInteger(0, boxName, OBJPROP_COLOR, clrGold);
   ObjectSetInteger(0, boxName, OBJPROP_WIDTH, 3);
   ObjectSetInteger(0, boxName, OBJPROP_STYLE, STYLE_SOLID);

   string fLbl = FP_PREFIX + "LBL_" + boxName;
   if(ObjectFind(0, fLbl) >= 0)
      ObjectSetInteger(0, fLbl, OBJPROP_TIMEFRAMES, OBJ_ALL_PERIODS);

   // ۲. پنهان‌سازی سایر باکس‌ها (بدون دستکاری رنگ و استایل آنها)
   for(int b = 0; b < g_boxCount; b++)
   {
      if(b == boxIdx) continue;

      ObjectSetInteger(0, g_drawnBoxes[b].boxName, OBJPROP_TIMEFRAMES, OBJ_NO_PERIODS);

      string lblName = FP_PREFIX + "LBL_" + g_drawnBoxes[b].boxName;
      if(ObjectFind(0, lblName) >= 0)
         ObjectSetInteger(0, lblName, OBJPROP_TIMEFRAMES, OBJ_NO_PERIODS);

      string extName = FP_PREFIX + "EXT_" + g_drawnBoxes[b].boxName;
      if(ObjectFind(0, extName) >= 0)
         ObjectSetInteger(0, extName, OBJPROP_TIMEFRAMES, OBJ_NO_PERIODS);
   }

   // ۳. پنهان‌سازی تمام خطوط ساختاری و معاملات قبلی
   int totalObjs = ObjectsTotal(0, 0, -1);
   for(int i = totalObjs - 1; i >= 0; i--)
   {
      string oName = ObjectName(0, i);
      if(StringFind(oName, FP_PREFIX + "IP_") == 0 ||
         StringFind(oName, FP_PREFIX + "RS_") == 0 ||
         StringFind(oName, FP_PREFIX + "SWAP_") == 0 ||
         StringFind(oName, FP_PREFIX + "STRUCT_") == 0 ||
         StringFind(oName, FP_PREFIX + "PIVOT_") == 0 ||
         StringFind(oName, FP_PREFIX + "AUTO_TR_") == 0 ||
         StringFind(oName, FP_PREFIX + "AUTOTRADE_") == 0)
      {
         ObjectSetInteger(0, oName, OBJPROP_TIMEFRAMES, OBJ_NO_PERIODS);
      }
   }

   // ۴. شبیه‌سازی دقیق و رسم سطوح معامله باکس و پنل HUD
   ShowTradeSetupForBox(boxIdx);

   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| رسم پنل شیک اطلاعاتی HUD در بالای چارت                          |
//+------------------------------------------------------------------+
void RenderFocusHUD(int boxIdx, string role, bool isBull, bool isEntered,
                    string resText, color resColor, double entryPrice, double slPrice,
                    double riskPips, double &tps[], int hitTP, datetime entryTime,
                    int entryBarIdx, datetime exitTime, int smartScore, string scoreTier,
                    string filterReason, string exitPlan, string cancelReasonStr,
                    bool isFiltered = false)
{
   CleanupFocusHUD();

   string pfx = FP_PREFIX + "FOCUS_HUD_";

   // ۱. پس‌زمینه پنل (OBJ_RECTANGLE_LABEL)
   string bgName = pfx + "BG";
   ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, bgName, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE, 20);
   ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE, 30);
   ObjectSetInteger(0, bgName, OBJPROP_XSIZE, 570);
   ObjectSetInteger(0, bgName, OBJPROP_YSIZE, 160);
   ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR, C'18,22,28');
   ObjectSetInteger(0, bgName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, bgName, OBJPROP_COLOR, clrGold);
   ObjectSetInteger(0, bgName, OBJPROP_WIDTH, 2);
   ObjectSetInteger(0, bgName, OBJPROP_BACK, false);
   ObjectSetInteger(0, bgName, OBJPROP_SELECTABLE, false);

   // دکمه خروج اختصاصی در گوشه بالای پنل HUD
   string btnClose = pfx + "CLOSE";
   ObjectCreate(0, btnClose, OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, btnClose, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, btnClose, OBJPROP_XDISTANCE, 555);
   ObjectSetInteger(0, btnClose, OBJPROP_YDISTANCE, 35);
   ObjectSetInteger(0, btnClose, OBJPROP_XSIZE, 26);
   ObjectSetInteger(0, btnClose, OBJPROP_YSIZE, 20);
   ObjectSetString(0, btnClose, OBJPROP_TEXT, "✕");
   ObjectSetString(0, btnClose, OBJPROP_FONT, "Arial");
   ObjectSetInteger(0, btnClose, OBJPROP_FONTSIZE, 9);
   ObjectSetInteger(0, btnClose, OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, btnClose, OBJPROP_BGCOLOR, C'160,35,35');
   ObjectSetInteger(0, btnClose, OBJPROP_BORDER_COLOR, clrRed);
   ObjectSetInteger(0, btnClose, OBJPROP_SELECTABLE, false);

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
   if(isFiltered)
   {
      if(isEntered)
      {
         statusStr = StringFormat("🛡️ فیلتر شده (عدم معامله) | شبیه‌سازی: %s", resText);
         resColor = (StringFind(resText, "STOP LOSS") >= 0) ? clrSalmon : clrSkyBlue;
      }
      else
      {
         statusStr = StringFormat("🛡️ فیلتر شده (عدم معامله) | وضعیت ستاپ: %s", (cancelReasonStr != "" ? cancelReasonStr : "عدم تاچ ورود"));
         resColor = clrSandyBrown;
      }
   }
   else if(isEntered)
   {
      statusStr = StringFormat("📊 وضعیت معامله: %s | ریسک: %.1f پیپ | R:R معادل: 1:%.0f",
                               resText, riskPips, (hitTP > 0 ? (double)hitTP : 0.0));
   }
   else
   {
      statusStr = StringFormat("⚠️ دلیل عدم ورود: %s",
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

   // ۵. ردیف ۳: اطلاعات زمانی
   string l3 = pfx + "TIMING";
   ObjectCreate(0, l3, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, l3, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, l3, OBJPROP_XDISTANCE, 32);
   ObjectSetInteger(0, l3, OBJPROP_YDISTANCE, 98);
   string timeStr = "";
   if(isEntered && entryTime > 0)
   {
      timeStr = StringFormat("⏱ تاچ ورود: %s  |  خروج: %s",
                             TimeToString(entryTime, TIME_DATE|TIME_MINUTES),
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
//| شبیه‌سازی سریع معامله باکس و ترسیم سطوح روی چارت                  |
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

   // بررسی اولیه شرط سلاطین طلایی (بدون خروج زودهنگام جهت نمایش کامل دلیل در HUD)
   bool isKingRejected = (InpOnlyTradeKings || InpTradeOnlyGoldenKings) && !IsQualifiedKing(g_drawnBoxes[boxIdx].tf, role);

   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;
   double bufferPips = ActiveSLOffsetPips() * pipSize;

   bool isBull       = true;
   double entryPrice = 0;
   double slPrice    = 0;
   double risk       = 0;
   double tps[4];
   datetime tpHitTime[4] = {0, 0, 0, 0};
   bool isEntered    = false;
   int  entryBarIdx  = -1;
   datetime entryTime = 0;
   int hitTP         = -1;
   bool isClosed     = false;
   datetime exitTime = 0;
   string cancelReasonStr = "";

   datetime baseTime = (g_drawnBoxes[boxIdx].formationTime > 0) ? g_drawnBoxes[boxIdx].formationTime : g_drawnBoxes[boxIdx].t1;
   datetime confirmTime = g_drawnBoxes[boxIdx].confirmationTime;
   if(confirmTime <= 0 || confirmTime > baseTime + PeriodSeconds(g_drawnBoxes[boxIdx].tf) * 15)
      confirmTime = baseTime;

   // ۱. بازیابی فوق سریع از مخزن از پیش محاسبه‌شده معاملات (0ms بدون نیاز به کپی کندل‌ها)
   int matchedTrade = -1;
   for(int t = 0; t < g_tradeCount; t++)
   {
      if(g_tradeSetups[t].boxName == g_drawnBoxes[boxIdx].boxName)
      {
         matchedTrade = t;
         break;
      }
   }

   if(matchedTrade >= 0)
   {
      isEntered    = true;
      isBull       = g_tradeSetups[matchedTrade].isBuy;
      entryPrice   = g_tradeSetups[matchedTrade].entryPrice;
      slPrice      = g_tradeSetups[matchedTrade].slPrice;
      risk         = g_tradeSetups[matchedTrade].risk;
      tps[0]       = g_tradeSetups[matchedTrade].tp1;
      tps[1]       = g_tradeSetups[matchedTrade].tp2;
      tps[2]       = g_tradeSetups[matchedTrade].tp3;
      tps[3]       = g_tradeSetups[matchedTrade].tp4;
      tpHitTime[0] = g_tradeSetups[matchedTrade].tp1Time;
      tpHitTime[1] = g_tradeSetups[matchedTrade].tp2Time;
      tpHitTime[2] = g_tradeSetups[matchedTrade].tp3Time;
      tpHitTime[3] = g_tradeSetups[matchedTrade].tp4Time;
      entryTime    = g_tradeSetups[matchedTrade].entryTime;
      exitTime     = g_tradeSetups[matchedTrade].exitTime;
      hitTP        = g_tradeSetups[matchedTrade].hitTP;
      isClosed     = g_tradeSetups[matchedTrade].isClosed;
      role         = g_tradeSetups[matchedTrade].boxRole;
   }
   else
   {
      // ۲. در صورتی که معامله در مخزن نبود (مثلاً وارد نشده یا منقضی شده)، فقط ۲۰۰ کندل اطراف باکس بررسی شود
      if(isOI)
      {
         isBull = g_drawnBoxes[boxIdx].isOInnerBull;
      }
      else
      {
         if(isSwap) isBull = g_drawnBoxes[boxIdx].isSwapBull;
         else if(isRS) isBull = g_drawnBoxes[boxIdx].isRSBull;
         else if(isLS) isBull = g_drawnBoxes[boxIdx].isLSBull;
         else isBull = g_drawnBoxes[boxIdx].isBullish;
      }

      if(isBull)
      {
         entryPrice = g_drawnBoxes[boxIdx].top;
         slPrice    = g_drawnBoxes[boxIdx].bottom - bufferPips;
      }
      else
      {
         entryPrice = g_drawnBoxes[boxIdx].bottom;
         slPrice    = g_drawnBoxes[boxIdx].top + bufferPips;
      }

      risk = MathAbs(entryPrice - slPrice);
      if(risk < _Point * 2.0) risk = _Point * 2.0;

      for(int tp = 0; tp < 4; tp++)
      {
         if(isBull) tps[tp] = entryPrice + risk * (tp + 1);
         else       tps[tp] = entryPrice - risk * (tp + 1);
      }

      datetime startReq = baseTime - PeriodSeconds(_Period) * 15;
      datetime stopReq  = baseTime + PeriodSeconds(g_drawnBoxes[boxIdx].tf) * 400;
      if(stopReq > TimeCurrent()) stopReq = TimeCurrent();

      MqlRates rates[];
      ArraySetAsSeries(rates, false);
      int copied = CopyRates(_Symbol, _Period, startReq, stopReq, rates);

      if(copied <= 5)
      {
         int startShift = iBarShift(_Symbol, _Period, baseTime, false);
         if(startShift >= 0)
         {
            int barsToCopy = startShift + 50;
            if(barsToCopy > 15000) barsToCopy = 15000;
            copied = CopyRates(_Symbol, _Period, 0, barsToCopy, rates);
         }
      }

      if(copied > 5)
      {
         double boxHeight = MathAbs(g_drawnBoxes[boxIdx].top - g_drawnBoxes[boxIdx].bottom);
         double minDeparturePrice = isBull ? (entryPrice + boxHeight * 0.3) : (entryPrice - boxHeight * 0.3);
         datetime maxBoxTime = baseTime + PeriodSeconds(g_drawnBoxes[boxIdx].tf) * 40;
         int departedBar = -1;
         int entryBar = -1;

         // پیدا کردن کندل شروع بررسی (تأیید ساختار)
         int startK = 0;
         for(int k = 0; k < copied; k++)
         {
            if(rates[k].time >= confirmTime)
            {
               startK = k;
               break;
            }
         }

         for(int k = startK; k < copied; k++)
         {
            // ۱. انقضای زمانی در صورت عدم خروج
            if(departedBar < 0 && rates[k].time > maxBoxTime)
            {
               cancelReasonStr = "EXPIRED ⏱ (عدم خروج قیمت ظرف ۴۰ کندل)";
               break;
            }

            // ۲. نقض حد ضرر قبل از ورود
            if(isBull && rates[k].low <= slPrice)
            {
               cancelReasonStr = "CANCELLED ❌ (نقض حد ضرر قبل از ورود)";
               break;
            }
            else if(!isBull && rates[k].high >= slPrice)
            {
               cancelReasonStr = "CANCELLED ❌ (نقض حد ضرر قبل از ورود)";
               break;
            }

            // ۳. بررسی پرتاب اولیه و خروج از گره (Breakout/Departure)
            if(departedBar < 0)
            {
               if(isBull && rates[k].close >= minDeparturePrice) departedBar = k;
               else if(!isBull && rates[k].close <= minDeparturePrice) departedBar = k;

               datetime maxDepTime = confirmTime + PeriodSeconds(g_drawnBoxes[boxIdx].tf) * 30;
               if(rates[k].time > maxDepTime)
               {
                  cancelReasonStr = "NO BREAKOUT ⏱ (عدم خروج قیمت ظرف ۳۰ کندل)";
                  break;
               }
            }
            else
            {
               // ۴. بررسی پولبک و تاچ نقطه ورود
               if(isBull && rates[k].low <= entryPrice)
               {
                  isEntered = true;
                  entryBar = k;
                  entryBarIdx = k;
                  entryTime = rates[k].time;
                  break;
               }
               else if(!isBull && rates[k].high >= entryPrice)
               {
                  isEntered = true;
                  entryBar = k;
                  entryBarIdx = k;
                  entryTime = rates[k].time;
                  break;
               }

               // بررسی مهلت بازگشت پولبک
               datetime maxLimitTime = rates[departedBar].time + PeriodSeconds(g_drawnBoxes[boxIdx].tf) * ActiveLimitExpirationBars();
               if(rates[k].time > maxLimitTime)
               {
                  cancelReasonStr = "NO PULLBACK 💨 (انقضای مهلت بازگشت پولبک)";
                  break;
               }
            }
         }

         // ۵. اگر ورود انجام شد، شبیه‌سازی دقیق تارگت‌ها و حد ضرر (TP/SL)
         if(isEntered && entryBar >= 0)
         {
            double currentSL = slPrice;
            for(int k = entryBar; k < copied; k++)
            {
               if(isBull)
               {
                  if(rates[k].low <= currentSL)
                  {
                     isClosed = true;
                     exitTime = rates[k].time;
                     break;
                  }
                  for(int tp = (hitTP > 0 ? hitTP : 0); tp < 4; tp++)
                  {
                     if(rates[k].high >= tps[tp])
                     {
                        hitTP = tp + 1;
                        tpHitTime[tp] = rates[k].time;
                        if(hitTP == 1) currentSL = entryPrice;
                        else if(hitTP == 2) currentSL = tps[0];
                        else if(hitTP == 3) currentSL = tps[1];
                     }
                  }
                  if(hitTP == 4)
                  {
                     isClosed = true;
                     exitTime = tpHitTime[3];
                     break;
                  }
               }
               else // SELL
               {
                  if(rates[k].high >= currentSL)
                  {
                     isClosed = true;
                     exitTime = rates[k].time;
                     break;
                  }
                  for(int tp = (hitTP > 0 ? hitTP : 0); tp < 4; tp++)
                  {
                     if(rates[k].low <= tps[tp])
                     {
                        hitTP = tp + 1;
                        tpHitTime[tp] = rates[k].time;
                        if(hitTP == 1) currentSL = entryPrice;
                        else if(hitTP == 2) currentSL = tps[0];
                        else if(hitTP == 3) currentSL = tps[1];
                     }
                  }
                  if(hitTP == 4)
                  {
                     isClosed = true;
                     exitTime = tpHitTime[3];
                     break;
                  }
               }
            }
         }

         if(!isEntered && cancelReasonStr == "")
         {
            cancelReasonStr = (departedBar < 0) ? "NO BREAKOUT ⏱ (عدم خروج قیمت ظرف ۳۰ کندل)" : "NO PULLBACK 💨 (پرتاب مستقیم بدون پولبک)";
         }
      }
      else
      {
         cancelReasonStr = "PENDING ⏳ (در انتظار دریافت دیتای چارت)";
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
   double slPips  = (pipSize > 0) ? (risk / pipSize) : 0.0;
   bool isFiltered = IsSetupFilteredOut(role, (entryTime > 0 ? entryTime : baseTime), riskPts);
   string filterReason = isFiltered ? GetFilterRejectionReason(role, (entryTime > 0 ? entryTime : baseTime), riskPts) : "مجاز (تایید فیلترها) ✅";

   if(isKingRejected)
   {
      isFiltered = true;
      filterReason = "👑 فیلتر سلاطین: ساختار غیرسلطان (معامله فقط روی الگوهای برتر مجاز است)";
   }

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
      string finalTxt = "";
      if(isFiltered)
         finalTxt = " " + role + " " + (isBull ? "BUY" : "SELL") + " [🛡️ فیلتر شده] -> شبیه‌سازی: " + resText;
      else
         finalTxt = " " + role + " " + (isBull ? "BUY" : "SELL") + " -> " + resText;
      ObjectSetString(0, resLbl, OBJPROP_TEXT, finalTxt);
      ObjectSetInteger(0, resLbl, OBJPROP_COLOR, (isFiltered && isClosed) ? clrSalmon : resColor);
      ObjectSetInteger(0, resLbl, OBJPROP_FONTSIZE, 9);
      ObjectSetInteger(0, resLbl, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(0, resLbl, OBJPROP_SELECTABLE, false);
   }

   // رسم پنل اطلاعاتی پیشرفته HUD در بالای چارت
   RenderFocusHUD(boxIdx, role, isBull, isEntered, resText, resColor,
                  entryPrice, slPrice, slPips, tps, hitTP, entryTime,
                  entryBarIdx, exitTime, smartScore, scoreTier, filterReason,
                  exitPlan, cancelReasonStr, isFiltered);

   // ثبت در کامنت چارت و لاگ ترمینال
   string tradeType = isBull ? "BUY 🔵" : "SELL 🟠";
   string dirFarsi  = isBull ? "خرید (گره صعودی)" : "فروش (گره نزولی)";

   string statusDisplay = "";
   if(isFiltered)
   {
      if(isEntered) statusDisplay = StringFormat("🛡️ فیلتر شده (عدم معامله) | شبیه‌سازی: %s", resText);
      else          statusDisplay = StringFormat("🛡️ فیلتر شده (عدم معامله) | وضعیت ستاپ: %s", (cancelReasonStr != "" ? cancelReasonStr : "عدم تاچ"));
   }
   else if(isEntered)
   {
      statusDisplay = resText;
   }
   else
   {
      statusDisplay = (cancelReasonStr != "" ? cancelReasonStr : "در انتظار پولبک معتبر");
   }

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
      statusDisplay
   );

   Comment(logMsg);
   Print(logMsg);
}

//+------------------------------------------------------------------+
//| ماژول اختصاصی مدیریت رویدادهای چارت (OnTradeTestChartEvent)        |
//| بازگشت true در صورت پردازش رویداد توسط ماژول تست                |
//+------------------------------------------------------------------+
bool OnTradeTestChartEvent(const int id,
                           const long &lparam,
                           const double &dparam,
                           const string &sparam)
{
   static ulong lastActionTick = 0;

   // ۱. رویداد کیبورد: کلید Escape جهت خروج از حالت تمرکز
   if(id == CHARTEVENT_KEYDOWN)
   {
      if(lparam == 27) // Escape key
      {
         if(IsFocusModeActive())
         {
            ExitFocusMode();
            Print("FlagPro: خروج از حالت تمرکز با فشردن کلید Escape.");
            return true;
         }
      }
      return false;
   }

   // ۲. رویداد کلیک مستقیم روی آبجکت‌ها
   if(id == CHARTEVENT_OBJECT_CLICK)
   {
      // دکمه خروج [✕] در گوشه HUD
      if(sparam == FP_PREFIX + "FOCUS_HUD_CLOSE")
      {
         ExitFocusMode();
         lastActionTick = GetTickCount64();
         return true;
      }

      // کلیک روی آبجکت‌های درون خود HUD (مانند عنوان یا کادر)
      if(StringFind(sparam, FP_PREFIX + "FOCUS_HUD_") == 0)
      {
         return true; // درون پنل مصرف می‌شود و از خروج جلوگیری می‌کند
      }

      // بررسی کلیک روی کادر مستطیل باکس یا برچسب متنی آن
      string targetBoxName = "";
      if(StringFind(sparam, FP_PREFIX + "BOX_") == 0)
      {
         targetBoxName = sparam;
      }
      else if(StringFind(sparam, FP_PREFIX + "LBL_") == 0)
      {
         targetBoxName = sparam;
         StringReplace(targetBoxName, FP_PREFIX + "LBL_", "");
      }

      if(targetBoxName != "")
      {
         for(int b = 0; b < g_boxCount; b++)
         {
            if(g_drawnBoxes[b].boxName == targetBoxName)
            {
               lastActionTick = GetTickCount64();
               EnterFocusMode(b, true); // با کلیک مجدد روی همان باکس toggle می‌شود
               return true;
            }
         }
      }
   }

   // ۳. رویداد کلیک روی فضای چارت (CHARTEVENT_CLICK)
   if(id == CHARTEVENT_CLICK)
   {
      // جلوگیری از تداخل رویداد کلیک ماوس ناشی از کلیک روی آبجکت (Debounce)
      if(GetTickCount64() - lastActionTick < 350)
      {
         return true;
      }

      int x = (int)lparam;
      int y = (int)dparam;

      // اگر کلیک داخل کادر پنل HUD در گوشه بالای چارت باشد، نادیده بگیر
      if(IsFocusModeActive())
      {
         if(x >= 20 && x <= 530 && y >= 30 && y <= 195)
         {
            return true;
         }
      }

      int subWindow = 0;
      datetime clickTime = 0;
      double   clickPrice = 0.0;
      if(!ChartXYToTimePrice(0, x, y, subWindow, clickTime, clickPrice))
      {
         return false;
      }

      // اگر در حالت تمرکز هستیم:
      if(IsFocusModeActive())
      {
         // هرگونه کلیک روی فضای چارت (خارج از پنل HUD) حالت تمرکز را خاتمه می‌دهد
         ExitFocusMode();
         lastActionTick = GetTickCount64();
         return true;
      }
      else // اگر در حالت تمرکز نیستیم:
      {
         // بررسی کلیک داخل هر یک از باکس‌های نمایان
         for(int b = 0; b < g_boxCount; b++)
         {
            if(g_drawnBoxes[b].top <= 0) continue;
            double top = MathMax(g_drawnBoxes[b].top, g_drawnBoxes[b].bottom);
            double btm = MathMin(g_drawnBoxes[b].top, g_drawnBoxes[b].bottom);

            if(clickTime >= g_drawnBoxes[b].t1 && clickTime <= g_drawnBoxes[b].t2 &&
               clickPrice >= btm && clickPrice <= top)
            {
               lastActionTick = GetTickCount64();
               EnterFocusMode(b, true);
               return true;
            }
         }
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| مقداردهی اولیه ماژول تست معاملات                                 |
//+------------------------------------------------------------------+
void InitTradeTestModule()
{
   g_focusModeActive  = false;
   g_focusBoxIdx      = -1;
   g_selectedBoxName  = "";
   g_origFocusBoxName = "";
   g_origFocusColor   = clrNONE;

   // پاکسازی هرگونه اشیاء بازمانده از قبل
   ObjectsDeleteAll(0, FP_PREFIX + "CLICK_TRADE_");
   CleanupFocusHUD();
}

//+------------------------------------------------------------------+
//| آزادسازی ماژول تست معاملات                                       |
//+------------------------------------------------------------------+
void DeinitTradeTestModule()
{
   ExitFocusMode();
}
