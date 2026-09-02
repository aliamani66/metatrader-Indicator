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

   datetime chartTime[];
   double chartHigh[], chartLow[];
   ArraySetAsSeries(chartTime, false);
   ArraySetAsSeries(chartHigh, false);
   ArraySetAsSeries(chartLow, false);

   int copied = CopyTime(_Symbol, _Period, 0, 30000, chartTime);
   CopyHigh(_Symbol, _Period, 0, 30000, chartHigh);
   CopyLow(_Symbol, _Period, 0, 30000, chartLow);
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
      if(isLS) tagCombo += (tagCombo == "" ? "LS" : "+LS");
      if(isOI) tagCombo += (tagCombo == "" ? "OInner" : "+OInner");
      if(isRS) tagCombo += (tagCombo == "" ? "RS" : "+RS");
      if(isSwap) tagCombo += (tagCombo == "" ? swapTag : "+" + swapTag);
      if(tagCombo != "") role = tagCombo;
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

   int boxEndIdx = FindBarIndex(chartTime, copied, g_drawnBoxes[boxIdx].t2);
   if(boxEndIdx < 0) boxEndIdx = 0;

   bool isEntered = false;
   int  entryBarIdx = -1;
   datetime entryTime = 0;

   for(int k = boxEndIdx; k < copied; k++)
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

   int hitTP = -1;
   bool isClosed = false;
   datetime exitTime = 0;

   if(!isEntered)
   {
      entryTime = g_drawnBoxes[boxIdx].t2;
      exitTime  = chartTime[copied - 1];
   }
   else
   {
      int maxHit = 0;
      for(int k = entryBarIdx; k < copied; k++)
      {
         if(isBull)
         {
            if(chartLow[k] <= slPrice)
            {
               hitTP = maxHit;
               isClosed = true;
               exitTime = chartTime[k];
               break;
            }
            for(int tp = maxHit; tp < 4; tp++)
            {
               if(chartHigh[k] >= tps[tp]) maxHit = tp + 1;
            }
            if(maxHit == 4)
            {
               hitTP = 4;
               isClosed = true;
               exitTime = chartTime[k];
               break;
            }
         }
         else
         {
            if(chartHigh[k] >= slPrice)
            {
               hitTP = maxHit;
               isClosed = true;
               exitTime = chartTime[k];
               break;
            }
            for(int tp = maxHit; tp < 4; tp++)
            {
               if(chartLow[k] <= tps[tp]) maxHit = tp + 1;
            }
            if(maxHit == 4)
            {
               hitTP = 4;
               isClosed = true;
               exitTime = chartTime[k];
               break;
            }
         }
      }

      if(!isClosed)
      {
         hitTP = maxHit;
         exitTime = chartTime[copied - 1];
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
}

//+------------------------------------------------------------------+
//| Export All Detected Trade Setups to CSV File                     |
//+------------------------------------------------------------------+
void ExportAllTradesToCSV()
{
   string filename = "flagpro_trades_export.csv";
   int handle = FileOpen(filename, FILE_WRITE | FILE_CSV | FILE_ANSI, ",");
   if(handle == INVALID_HANDLE)
   {
      Print("❌ FlagPro: خطا در باز کردن فایل CSV: ", GetLastError());
      return;
   }

   FileWrite(handle,
             "BoxIndex",
             "BoxName",
             "Timeframe",
             "Role",
             "Direction",
             "BoxTimeStart",
             "BoxTimeEnd",
             "EntryTime",
             "ExitTime",
             "EntryPrice",
             "StopLoss",
             "RiskPoints",
             "TP1",
             "TP2",
             "TP3",
             "TP4",
             "Outcome",
             "HitTargetRatio",
             "IsClosed");

   datetime chartTime[];
   double chartHigh[], chartLow[];
   ArraySetAsSeries(chartTime, false);
   ArraySetAsSeries(chartHigh, false);
   ArraySetAsSeries(chartLow, false);

   int copied = CopyTime(_Symbol, _Period, 0, 50000, chartTime);
   CopyHigh(_Symbol, _Period, 0, 50000, chartHigh);
   CopyLow(_Symbol, _Period, 0, 50000, chartLow);
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
         if(isLS) tagCombo += (tagCombo == "" ? "LS" : "+LS");
         if(isOI) tagCombo += (tagCombo == "" ? "OInner" : "+OInner");
         if(isRS) tagCombo += (tagCombo == "" ? "RS" : "+RS");
         if(isSwap) tagCombo += (tagCombo == "" ? swapTag : "+" + swapTag);
         if(tagCombo != "") role = tagCombo;
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

      int boxEndIdx = FindBarIndex(chartTime, copied, g_drawnBoxes[b].t2);
      if(boxEndIdx < 0) boxEndIdx = 0;

      bool isEntered = false;
      int  entryBarIdx = -1;
      datetime entryTime = 0;

      for(int k = boxEndIdx; k < copied; k++)
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
         for(int k = entryBarIdx; k < copied; k++)
         {
            if(isBull)
            {
               if(chartLow[k] <= slPrice)
               {
                  hitTP = maxHit;
                  isClosed = true;
                  exitTime = chartTime[k];
                  break;
               }
               for(int tp = maxHit; tp < 4; tp++)
               {
                  if(chartHigh[k] >= tps[tp]) maxHit = tp + 1;
               }
               if(maxHit == 4)
               {
                  hitTP = 4;
                  isClosed = true;
                  exitTime = chartTime[k];
                  break;
               }
            }
            else
            {
               if(chartHigh[k] >= slPrice)
               {
                  hitTP = maxHit;
                  isClosed = true;
                  exitTime = chartTime[k];
                  break;
               }
               for(int tp = maxHit; tp < 4; tp++)
               {
                  if(chartLow[k] <= tps[tp]) maxHit = tp + 1;
               }
               if(maxHit == 4)
               {
                  hitTP = 4;
                  isClosed = true;
                  exitTime = chartTime[k];
                  break;
               }
            }
         }

         if(!isClosed)
         {
            hitTP = maxHit;
            exitTime = chartTime[copied - 1];
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

      FileWrite(handle,
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

      exportedCount++;
   }

   FileClose(handle);
   Print("📁 FlagPro: تعداد ", exportedCount, " موقعیت معاملاتی با موفقیت در فایل MQL5/Files/flagpro_trades_export.csv ذخیره شد.");
}
