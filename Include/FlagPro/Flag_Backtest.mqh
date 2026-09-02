//+------------------------------------------------------------------+
//| Flag_Backtest.mqh                                                |
//| FlagPro Trade Simulation Engine, Target Analytics & CSV Exporter |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""

//+------------------------------------------------------------------+
//| Interactive On-Demand Trade Simulation for Clicked Box in History |
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
   double chartHigh[], chartLow[];
   ArraySetAsSeries(chartTime, false);
   ArraySetAsSeries(chartHigh, false);
   ArraySetAsSeries(chartLow, false);

   int copied = CopyTime(_Symbol, _Period, 0, 250000, chartTime);
   CopyHigh(_Symbol, _Period, 0, 250000, chartHigh);
   CopyLow(_Symbol, _Period, 0, 250000, chartLow);
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

   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;
   double bufferPips = InpRSPipBuffer * pipSize;

   bool isBull = true;
   double entryPrice = 0;
   double slPrice    = 0;

   if(isOI)
   {
      double   pivotP = 0;
      datetime closestPivotTime = 0;
      for(int k = 0; k < g_indepCount; k++)
      {
         if(!g_indepPivots[k].hasIP) continue;
         if(g_indepPivots[k].time <= g_drawnBoxes[boxIdx].t1)
         {
            if(closestPivotTime == 0 || g_indepPivots[k].time > closestPivotTime)
            {
               closestPivotTime = g_indepPivots[k].time;
               pivotP = g_indepPivots[k].price;
               isBull = !g_indepPivots[k].isHigh;
            }
         }
      }

      if(pivotP == 0)
      {
         isBull = g_drawnBoxes[boxIdx].isOInnerBull;
         pivotP = isBull ? g_drawnBoxes[boxIdx].bottom : g_drawnBoxes[boxIdx].top;
      }

      if(isBull)
      {
         entryPrice = g_drawnBoxes[boxIdx].top;
         slPrice    = pivotP - 2.0 * pipSize;
      }
      else
      {
         entryPrice = g_drawnBoxes[boxIdx].bottom;
         slPrice    = pivotP + 2.0 * pipSize;
      }
   }
   else
   {
      if(isSwap) isBull = g_drawnBoxes[boxIdx].isSwapBull;
      else if(isRS) isBull = g_drawnBoxes[boxIdx].isRSBull;
      else if(isLS) isBull = g_drawnBoxes[boxIdx].isLSBull;
      else isBull = g_drawnBoxes[boxIdx].isBullish;

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
   }

   double risk = MathAbs(entryPrice - slPrice);
   if(risk < _Point * 2.0) risk = _Point * 2.0;

   double tps[4];
   for(int tp = 0; tp < 4; tp++)
   {
      if(isBull) tps[tp] = entryPrice + risk * (tp + 1);
      else       tps[tp] = entryPrice - risk * (tp + 1);
   }

   datetime startTime = g_drawnBoxes[boxIdx].formationTime;
   if(startTime <= 0) startTime = g_drawnBoxes[boxIdx].t1;

   int boxEndIdx = FindBarIndex(chartTime, copied, startTime);
   if(boxEndIdx < 0) boxEndIdx = 0;

   bool isEntered = false;
   int  entryBarIdx = -1;
   datetime entryTime = 0;

   // جستجوی پولبک برای ورود به معامله
   // ابتدا قیمت باید از گره خارج شود و سپس به سطح ورود (entryPrice) پولبک بزند
   bool hasExited = false;
   for(int k = boxEndIdx; k < copied; k++)
   {
      if(!hasExited)
      {
         if(isBull && chartHigh[k] > entryPrice) hasExited = true;
         else if(!isBull && chartLow[k] < entryPrice) hasExited = true;
      }
      
      if(hasExited)
      {
         if(isBull)
         {
            if(chartLow[k] <= entryPrice && chartHigh[k] >= entryPrice)
            {
               isEntered = true;
               entryBarIdx = k;
               entryTime = chartTime[k];
               break;
            }
         }
         else
         {
            if(chartHigh[k] >= entryPrice && chartLow[k] <= entryPrice)
            {
               isEntered = true;
               entryBarIdx = k;
               entryTime = chartTime[k];
               break;
            }
         }
      }
   }

   int hitTP = -1;
   bool isClosed = false;
   datetime exitTime = 0;

   if(!isEntered)
   {
      entryTime = startTime;
      exitTime  = chartTime[copied - 1];
   }
   else
   {
      int maxHit = 0;
      datetime hitTime = 0;
      for(int k = entryBarIdx; k < copied; k++)
      {
         if(isBull)
         {
            // بررسی برخورد به تارگت‌های سود
            for(int tp = maxHit; tp < 4; tp++)
            {
               if(chartHigh[k] >= tps[tp])
               {
                  maxHit = tp + 1;
                  hitTime = chartTime[k];
               }
            }

            // بررسی حد ضرر
            if(chartLow[k] <= slPrice)
            {
               hitTP = maxHit;
               isClosed = true;
               exitTime = (maxHit > 0) ? hitTime : chartTime[k];
               break;
            }

            // اگر به آخرین تارگت (TP4) رسید خروج کامل
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
            // بررسی برخورد به تارگت‌های سود
            for(int tp = maxHit; tp < 4; tp++)
            {
               if(chartLow[k] <= tps[tp])
               {
                  maxHit = tp + 1;
                  hitTime = chartTime[k];
               }
            }

            // بررسی حد ضرر
            if(chartHigh[k] >= slPrice)
            {
               hitTP = maxHit;
               isClosed = true;
               exitTime = (maxHit > 0) ? hitTime : chartTime[k];
               break;
            }

            // اگر به آخرین تارگت (TP4) رسید خروج کامل
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

   datetime t1 = entryTime;
   datetime t2 = exitTime;
   if(t2 <= t1) t2 = t1 + PeriodSeconds(_Period) * 10;

   string pfx = FP_PREFIX + "CLICK_TRADE_";

   string entryLine = pfx + "ENTRY";
   ObjectCreate(0, entryLine, OBJ_TREND, 0, t1, entryPrice, t2, entryPrice);
   ObjectSetInteger(0, entryLine, OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, entryLine, OBJPROP_WIDTH, 2);
   ObjectSetInteger(0, entryLine, OBJPROP_STYLE, STYLE_SOLID);
   ObjectSetInteger(0, entryLine, OBJPROP_RAY_RIGHT, false);
   ObjectSetInteger(0, entryLine, OBJPROP_SELECTABLE, false);

   string slLine = pfx + "SL";
   ObjectCreate(0, slLine, OBJ_TREND, 0, t1, slPrice, t2, slPrice);
   ObjectSetInteger(0, slLine, OBJPROP_COLOR, clrRed);
   ObjectSetInteger(0, slLine, OBJPROP_WIDTH, 2);
   ObjectSetInteger(0, slLine, OBJPROP_STYLE, STYLE_DASH);
   ObjectSetInteger(0, slLine, OBJPROP_RAY_RIGHT, false);
   ObjectSetInteger(0, slLine, OBJPROP_SELECTABLE, false);

   for(int tp = 0; tp < 4; tp++)
   {
      string tpLine = pfx + "TP" + IntegerToString(tp + 1);
      ObjectCreate(0, tpLine, OBJ_TREND, 0, t1, tps[tp], t2, tps[tp]);
      ObjectSetInteger(0, tpLine, OBJPROP_COLOR, clrLimeGreen);
      ObjectSetInteger(0, tpLine, OBJPROP_WIDTH, (hitTP >= tp + 1 ? 2 : 1));
      ObjectSetInteger(0, tpLine, OBJPROP_STYLE, (hitTP >= tp + 1 ? STYLE_SOLID : STYLE_DOT));
      ObjectSetInteger(0, tpLine, OBJPROP_RAY_RIGHT, false);
      ObjectSetInteger(0, tpLine, OBJPROP_SELECTABLE, false);

      string tpLbl = tpLine + "_LBL";
      ObjectCreate(0, tpLbl, OBJ_TEXT, 0, t2, tps[tp]);
      ObjectSetString(0, tpLbl, OBJPROP_TEXT, "TP" + IntegerToString(tp + 1) + " (1:" + IntegerToString(tp + 1) + ")");
      ObjectSetInteger(0, tpLbl, OBJPROP_COLOR, clrLimeGreen);
      ObjectSetInteger(0, tpLbl, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, tpLbl, OBJPROP_ANCHOR, (isBull ? ANCHOR_LOWER : ANCHOR_UPPER));
      ObjectSetInteger(0, tpLbl, OBJPROP_SELECTABLE, false);
   }

   string resText = "";
   color resColor = clrSilver;
   if(!isEntered)        { resText = "PENDING ⏳"; resColor = clrSilver; }
   else if(hitTP == 4)   { resText = "WIN 1:4 🎯"; resColor = clrLime; }
   else if(hitTP == 3)   { resText = "WIN 1:3 🚀"; resColor = clrMediumSpringGreen; }
   else if(hitTP == 2)   { resText = "WIN 1:2 ✨"; resColor = clrSpringGreen; }
   else if(hitTP == 1)   { resText = "WIN 1:1 👍"; resColor = clrAqua; }
   else if(isClosed)     { resText = "STOP LOSS ❌"; resColor = clrRed; }
   else                  { resText = "IN TRADE ⏱"; resColor = clrGold; }

   string resLbl = pfx + "RESULT_LBL";
   ObjectCreate(0, resLbl, OBJ_TEXT, 0, t2, entryPrice);
   ObjectSetString(0, resLbl, OBJPROP_TEXT, " " + role + " " + (isBull ? "BUY" : "SELL") + " -> " + resText);
   ObjectSetInteger(0, resLbl, OBJPROP_COLOR, resColor);
   ObjectSetInteger(0, resLbl, OBJPROP_FONTSIZE, 9);
   ObjectSetInteger(0, resLbl, OBJPROP_ANCHOR, ANCHOR_LEFT);
   ObjectSetInteger(0, resLbl, OBJPROP_SELECTABLE, false);

   double riskPts = (_Point > 0) ? (risk / _Point) : 0.0;
   bool isFiltered = IsSetupFilteredOut(role, entryTime, riskPts);
   string filterReason = isFiltered ? GetFilterRejectionReason(role, entryTime, riskPts) : "مجاز (تایید فیلترها) ✅";

   string tradeType = isBull ? "BUY 🟢" : "SELL 🔴";
   string dirFarsi  = isBull ? "خرید (گره صعودی)" : "فروش (گره نزولی)";
   double slPips = risk / pipSize;

   int smartScore = CalculateSmartSetupScore(role, entryTime, riskPts);
   string scoreTier = GetSmartScoreTier(smartScore);
   string exitPlan = GetRecommendedExitPlan(smartScore, role);

   string logMsg = StringFormat(
      "═══════════════════════════════════════════════════\n"
      "🎯 [FlagPro ستاپ معامله]\n"
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

//+------------------------------------------------------------------+
//| Export All Detected Trade Setups to CSV File                     |
//+------------------------------------------------------------------+
void ExportAllTradesToCSV()
{
   string symClean = _Symbol;
   StringReplace(symClean, "!", "");
   StringReplace(symClean, "#", "");
   string symFilename = "flagpro_trades_" + symClean + ".csv";
   int handleSym = FileOpen(symFilename, FILE_WRITE | FILE_CSV | FILE_ANSI, ",");
   int handle = FileOpen("flagpro_trades_export.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ",");

   if(handle == INVALID_HANDLE && handleSym == INVALID_HANDLE)
   {
      Print("❌ FlagPro: خطا در باز کردن فایل CSV: ", GetLastError());
      return;
   }

   string header = "Symbol,BoxIndex,BoxName,Timeframe,Role,Direction,BoxTimeStart,BoxTimeEnd,EntryTime,ExitTime,EntryPrice,StopLoss,RiskPoints,TP1,TP2,TP3,TP4,Outcome,HitTargetRatio,IsClosed";
   if(handle != INVALID_HANDLE) FileWrite(handle, "Symbol", "BoxIndex", "BoxName", "Timeframe", "Role", "Direction", "BoxTimeStart", "BoxTimeEnd", "EntryTime", "ExitTime", "EntryPrice", "StopLoss", "RiskPoints", "TP1", "TP2", "TP3", "TP4", "Outcome", "HitTargetRatio", "IsClosed");
   if(handleSym != INVALID_HANDLE) FileWrite(handleSym, "Symbol", "BoxIndex", "BoxName", "Timeframe", "Role", "Direction", "BoxTimeStart", "BoxTimeEnd", "EntryTime", "ExitTime", "EntryPrice", "StopLoss", "RiskPoints", "TP1", "TP2", "TP3", "TP4", "Outcome", "HitTargetRatio", "IsClosed");

   datetime chartTime[];
   double chartHigh[], chartLow[];
   ArraySetAsSeries(chartTime, false);
   ArraySetAsSeries(chartHigh, false);
   ArraySetAsSeries(chartLow, false);

   int copied = CopyTime(_Symbol, _Period, 0, 250000, chartTime);
   CopyHigh(_Symbol, _Period, 0, 250000, chartHigh);
   CopyLow(_Symbol, _Period, 0, 250000, chartLow);
   if(copied < 10)
   {
      FileClose(handle);
      return;
   }

   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;
   double bufferPips = InpRSPipBuffer * pipSize;
   int exportedCount = 0;

   for(int b = 0; b < g_boxCount; b++)
   {
      if(g_drawnBoxes[b].top <= 0) continue;
      if(!InpTradeMacroTFs && g_drawnBoxes[b].tf >= PERIOD_H1) continue;
      string role = "Flag";
      bool isSwap = g_drawnBoxes[b].isSwap;
      bool isLS   = false;
      bool isRS   = false;
      bool isOI   = false;
      string swapTag = "";

      if(isSwap)
      {
         role = "S-" + g_drawnBoxes[b].swapSourceRole;
      }
      else
      {
         for(int tg = 0; tg < ArraySize(g_drawnBoxes[b].rsTags); tg++)
         {
            string tgName = g_drawnBoxes[b].rsTags[tg];
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
            string lsDir = g_drawnBoxes[b].isLSBull ? "-BU" : "-BE";
            tagCombo += (tagCombo == "" ? "LS" + lsDir : " > LS" + lsDir);
         }
         if(isOI)
         {
            string oiDir = g_drawnBoxes[b].isOInnerBull ? "-BU" : "-BE";
            tagCombo += (tagCombo == "" ? "OInner" + oiDir : " > OInner" + oiDir);
         }
         if(isRS)
         {
            string rsDir = g_drawnBoxes[b].isRSBull ? "-BU" : "-BE";
            tagCombo += (tagCombo == "" ? "RS" + rsDir : " > RS" + rsDir);
         }
         if(isSwap)
         {
            string swDir = g_drawnBoxes[b].isSwapBull ? "-BU" : "-BE";
            string fullSwap = swapTag + swDir;
            tagCombo += (tagCombo == "" ? fullSwap : " > " + fullSwap);
         }
         if(tagCombo != "") role = tagCombo;
         else role = "Flag-" + (g_drawnBoxes[b].isBullish ? "BU" : "BE");
      }

      bool isBull = true;
      double entryPrice = 0;
      double slPrice = 0;

      if(isOI)
      {
         double pivotP = 0;
         datetime closestPivotTime = 0;
         for(int k = 0; k < g_indepCount; k++)
         {
            if(!g_indepPivots[k].hasIP) continue;
            if(g_indepPivots[k].time <= g_drawnBoxes[b].t1)
            {
               if(closestPivotTime == 0 || g_indepPivots[k].time > closestPivotTime)
               {
                  closestPivotTime = g_indepPivots[k].time;
                  pivotP = g_indepPivots[k].price;
                  isBull = !g_indepPivots[k].isHigh;
               }
            }
         }

         if(pivotP == 0)
         {
            isBull = g_drawnBoxes[b].isOInnerBull;
            pivotP = isBull ? g_drawnBoxes[b].bottom : g_drawnBoxes[b].top;
         }

         if(isBull)
         {
            entryPrice = g_drawnBoxes[b].top;
            slPrice    = pivotP - 2.0 * pipSize;
         }
         else
         {
            entryPrice = g_drawnBoxes[b].bottom;
            slPrice    = pivotP + 2.0 * pipSize;
         }
      }
      else
      {
         if(isSwap) isBull = g_drawnBoxes[b].isSwapBull;
         else if(isRS) isBull = g_drawnBoxes[b].isRSBull;
         else if(isLS) isBull = g_drawnBoxes[b].isLSBull;
         else isBull = g_drawnBoxes[b].isBullish;

         if(isBull)
         {
            entryPrice = g_drawnBoxes[b].top;
            slPrice    = g_drawnBoxes[b].bottom - bufferPips;
         }
         else
         {
            entryPrice = g_drawnBoxes[b].bottom;
            slPrice    = g_drawnBoxes[b].top + bufferPips;
         }
      }

      double risk = MathAbs(entryPrice - slPrice);
      if(risk < _Point * 2.0) risk = _Point * 2.0;

      double tps[4];
      for(int tp = 0; tp < 4; tp++)
      {
         if(isBull) tps[tp] = entryPrice + risk * (tp + 1);
         else       tps[tp] = entryPrice - risk * (tp + 1);
      }

      datetime startTime = g_drawnBoxes[b].formationTime;
      if(startTime <= 0) startTime = g_drawnBoxes[b].t1;

      int boxEndIdx = FindBarIndex(chartTime, copied, startTime);
      if(boxEndIdx < 0) boxEndIdx = 0;

      bool isEntered = false;
      int  entryBarIdx = -1;
      datetime entryTime = 0;

      bool hasExited = false;
      for(int k = boxEndIdx; k < copied; k++)
      {
         if(!hasExited)
         {
            if(isBull && chartHigh[k] > entryPrice) hasExited = true;
            else if(!isBull && chartLow[k] < entryPrice) hasExited = true;
         }

         if(hasExited)
         {
            if(isBull)
            {
               if(chartLow[k] <= entryPrice && chartHigh[k] >= entryPrice)
               {
                  isEntered = true;
                  entryBarIdx = k;
                  entryTime = chartTime[k];
                  break;
               }
            }
            else
            {
               if(chartHigh[k] >= entryPrice && chartLow[k] <= entryPrice)
               {
                  isEntered = true;
                  entryBarIdx = k;
                  entryTime = chartTime[k];
                  break;
               }
            }
         }
      }

      int hitTP = -1;
      bool isClosed = false;
      datetime exitTime = 0;

      if(!isEntered)
      {
         hitTP = -1;
         isClosed = false;
         entryTime = 0;
         exitTime = 0;
      }
      else
      {
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
               for(int tp = maxHit; tp < 4; tp++)
               {
                  if(chartLow[k] <= tps[tp])
                  {
                     maxHit = tp + 1;
                     hitTime = chartTime[k];
                  }
               }

               if(chartHigh[k] >= slPrice)
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

      string outcomeStr = "Pending";
      if(isEntered)
      {
         if(hitTP == 4) outcomeStr = "Win_1:4";
         else if(hitTP == 3) outcomeStr = "Win_1:3";
         else if(hitTP == 2) outcomeStr = "Win_1:2";
         else if(hitTP == 1) outcomeStr = "Win_1:1";
         else if(isClosed)   outcomeStr = "Loss_SL";
         else outcomeStr = "Open_Trade";
      }

      if(handle != INVALID_HANDLE)
      {
         FileWrite(handle,
                   _Symbol,
                   IntegerToString(b),
                   g_drawnBoxes[b].boxName,
                   g_drawnBoxes[b].tfTag,
                   role,
                   (isBull ? "BUY" : "SELL"),
                   TimeToString(g_drawnBoxes[b].t1),
                   TimeToString(g_drawnBoxes[b].t2),
                   (entryTime > 0 ? TimeToString(entryTime) : "None"),
                   (exitTime > 0 ? TimeToString(exitTime) : "None"),
                   DoubleToString(entryPrice, _Digits),
                   DoubleToString(slPrice, _Digits),
                   DoubleToString(risk / _Point, 1),
                   DoubleToString(tps[0], _Digits),
                   DoubleToString(tps[1], _Digits),
                   DoubleToString(tps[2], _Digits),
                   DoubleToString(tps[3], _Digits),
                   outcomeStr,
                   IntegerToString(hitTP),
                   (isClosed ? "True" : "False"));
      }

      if(handleSym != INVALID_HANDLE)
      {
         FileWrite(handleSym,
                   _Symbol,
                   IntegerToString(b),
                   g_drawnBoxes[b].boxName,
                   g_drawnBoxes[b].tfTag,
                   role,
                   (isBull ? "BUY" : "SELL"),
                   TimeToString(g_drawnBoxes[b].t1),
                   TimeToString(g_drawnBoxes[b].t2),
                   (entryTime > 0 ? TimeToString(entryTime) : "None"),
                   (exitTime > 0 ? TimeToString(exitTime) : "None"),
                   DoubleToString(entryPrice, _Digits),
                   DoubleToString(slPrice, _Digits),
                   DoubleToString(risk / _Point, 1),
                   DoubleToString(tps[0], _Digits),
                   DoubleToString(tps[1], _Digits),
                   DoubleToString(tps[2], _Digits),
                   DoubleToString(tps[3], _Digits),
                   outcomeStr,
                   IntegerToString(hitTP),
                   (isClosed ? "True" : "False"));
      }

      exportedCount++;
   }

   if(handle != INVALID_HANDLE) FileClose(handle);
   if(handleSym != INVALID_HANDLE) FileClose(handleSym);
   Print("📁 FlagPro: تعداد ", exportedCount, " موقعیت معاملاتی ", _Symbol, " با موفقیت در فایل‌های CSV ذخیره شد.");
}
