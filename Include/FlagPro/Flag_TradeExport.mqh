//+------------------------------------------------------------------+
//| Flag_TradeExport.mqh                                             |
//| Full Backtest Analytics & Multi-Symbol CSV Data Exporter         |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""

//+------------------------------------------------------------------+
//| ساختار نتیجه شبیه‌سازی برای یک مدل استاپ‌لاس                       |
//+------------------------------------------------------------------+
struct SimSLResult
{
   double   slPrice;
   double   riskPoints;
   double   exitPrice;
   datetime exitTime;
   int      hitTP;
   bool     isClosed;
   string   outcome;
};

//+------------------------------------------------------------------+
//| شبیه‌سازی مستقل نتیجه معامله با یک استاپ‌لاس خاص بر بستر M1 یا کندل |
//+------------------------------------------------------------------+
void SimulateSingleSLMode(bool isBull,
                          double entryPrice,
                          double slPrice,
                          double risk,
                          int entryBarIdx,
                          datetime entryTime,
                          const MqlRates &m1Rates[],
                          int m1Count,
                          const datetime &chartTime[],
                          const double &chartHigh[],
                          const double &chartLow[],
                          const double &chartClose[],
                          const int &chartSpread[],
                          int copied,
                          double simSpread,
                          SimSLResult &res)
{
   res.slPrice    = slPrice;
   res.riskPoints = risk / _Point;
   res.exitPrice  = 0.0;
   res.exitTime   = 0;
   res.hitTP      = -1;
   res.isClosed   = false;
   res.outcome    = "Open_Trade";

   if(entryBarIdx < 0 || entryTime <= 0)
   {
      res.outcome = "Pending";
      return;
   }

   double tps[4];
   for(int tp = 0; tp < 4; tp++)
      tps[tp] = isBull ? (entryPrice + risk * (tp + 1)) : (entryPrice - risk * (tp + 1));

   int maxHit = 0;
   datetime hitTime = 0;
   double currentSL = slPrice;

   if(m1Count > 1)
   {
      for(int m = 1; m < m1Count; m++)
      {
         if(isBull)
         {
            if(m1Rates[m].low <= currentSL)
            {
               res.hitTP = maxHit;
               res.isClosed = true;
               res.exitTime = m1Rates[m].time;
               res.exitPrice = currentSL;
               break;
            }
            for(int tp = maxHit; tp < 4; tp++)
            {
               if(m1Rates[m].high >= tps[tp])
               {
                  maxHit = tp + 1;
                  hitTime = m1Rates[m].time;
                  if(maxHit == 1) currentSL = entryPrice;
                  else if(maxHit == 2) currentSL = tps[0];
                  else if(maxHit == 3) currentSL = tps[1];
               }
            }
            if(maxHit == 4)
            {
               res.hitTP = 4;
               res.isClosed = true;
               res.exitTime = hitTime;
               res.exitPrice = tps[3];
               break;
            }
         }
         else // SELL
         {
            double barSpread = simSpread;
            if((m1Rates[m].high + barSpread) >= currentSL)
            {
               res.hitTP = maxHit;
               res.isClosed = true;
               res.exitTime = m1Rates[m].time;
               res.exitPrice = currentSL;
               break;
            }
            for(int tp = maxHit; tp < 4; tp++)
            {
               if((m1Rates[m].low + barSpread) <= tps[tp])
               {
                  maxHit = tp + 1;
                  hitTime = m1Rates[m].time;
                  if(maxHit == 1) currentSL = entryPrice;
                  else if(maxHit == 2) currentSL = tps[0];
                  else if(maxHit == 3) currentSL = tps[1];
               }
            }
            if(maxHit == 4)
            {
               res.hitTP = 4;
               res.isClosed = true;
               res.exitTime = hitTime;
               res.exitPrice = tps[3];
               break;
            }
         }
      }
   }
   else
   {
      for(int k = entryBarIdx; k < copied; k++)
      {
         if(isBull)
         {
            if(chartLow[k] <= currentSL)
            {
               res.hitTP = maxHit;
               res.isClosed = true;
               res.exitTime = chartTime[k];
               res.exitPrice = currentSL;
               break;
            }
            if(k > entryBarIdx)
            {
               for(int tp = maxHit; tp < 4; tp++)
               {
                  if(chartHigh[k] >= tps[tp])
                  {
                     maxHit = tp + 1;
                     hitTime = chartTime[k];
                     if(maxHit == 1) currentSL = entryPrice;
                     else if(maxHit == 2) currentSL = tps[0];
                     else if(maxHit == 3) currentSL = tps[1];
                  }
               }
               if(maxHit == 4)
               {
                  res.hitTP = 4;
                  res.isClosed = true;
                  res.exitTime = hitTime;
                  res.exitPrice = tps[3];
                  break;
               }
            }
         }
         else // SELL
         {
            double barSpread = GetBarSpread(k, chartSpread, simSpread);
            if((chartHigh[k] + barSpread) >= currentSL)
            {
               res.hitTP = maxHit;
               res.isClosed = true;
               res.exitTime = chartTime[k];
               res.exitPrice = currentSL;
               break;
            }
            if(k > entryBarIdx)
            {
               for(int tp = maxHit; tp < 4; tp++)
               {
                  if((chartLow[k] + barSpread) <= tps[tp])
                  {
                     maxHit = tp + 1;
                     hitTime = chartTime[k];
                     if(maxHit == 1) currentSL = entryPrice;
                     else if(maxHit == 2) currentSL = tps[0];
                     else if(maxHit == 3) currentSL = tps[1];
                  }
               }
               if(maxHit == 4)
               {
                  res.hitTP = 4;
                  res.isClosed = true;
                  res.exitTime = hitTime;
                  res.exitPrice = tps[3];
                  break;
               }
            }
         }
      }
   }

   if(!res.isClosed)
   {
      res.hitTP = maxHit;
      res.exitTime = (maxHit > 0) ? hitTime : (copied > 0 ? chartTime[copied - 1] : 0);
      res.exitPrice = (copied > 0) ? chartClose[copied - 1] : 0.0;
   }

   if(res.hitTP == 4)      res.outcome = "Win_1:4";
   else if(res.hitTP == 3) res.outcome = "Win_1:3";
   else if(res.hitTP == 2) res.outcome = "Win_1:2";
   else if(res.hitTP == 1) res.outcome = "Win_1:1";
   else if(res.isClosed)   res.outcome = "Loss_SL";
   else                    res.outcome = "Open_Trade";
}

//+------------------------------------------------------------------+
//| Export All Detected Trade Setups to CSV File                     |
//+------------------------------------------------------------------+
void ExportAllTradesToCSV()
{
   if(!InpExportCSV) return;

   static datetime lastExportTime = 0;
   if(TimeCurrent() - lastExportTime < 300 && !g_forceRecalc) return;
   lastExportTime = TimeCurrent();

   string symClean = _Symbol;
   StringReplace(symClean, "!", "");
   StringReplace(symClean, "#", "");
   string symFilename = "flagpro_trades_" + symClean + ".csv";
   int handleSym = FileOpen(symFilename, FILE_WRITE | FILE_CSV | FILE_ANSI, ",");

   if(handleSym == INVALID_HANDLE)
   {
      Print("❌ FlagPro: خطا در باز کردن فایل CSV: ", GetLastError());
      return;
   }

   FileWrite(handleSym, "Symbol", "BoxIndex", "BoxName", "Timeframe", "Role", "Direction", "BoxTimeStart", "BoxTimeEnd", "EntryTime", "ExitTime", "EntryPrice", "ExitPrice", "StopLoss", "RiskPoints", "TP1", "TP2", "TP3", "TP4", "Outcome", "HitTargetRatio", "IsClosed", "SpreadPoints", "SL_M0", "Pts_M0", "Exit_M0", "Hit_M0", "Out_M0", "SL_M1", "Pts_M1", "Exit_M1", "Hit_M1", "Out_M1", "SL_M2", "Pts_M2", "Exit_M2", "Hit_M2", "Out_M2", "SL_M3", "Pts_M3", "Exit_M3", "Hit_M3", "Out_M3");

   datetime chartTime[];
   double chartHigh[], chartLow[], chartClose[];
   int chartSpread[];
   ArraySetAsSeries(chartTime, false);
   ArraySetAsSeries(chartHigh, false);
   ArraySetAsSeries(chartLow, false);
   ArraySetAsSeries(chartClose, false);
   ArraySetAsSeries(chartSpread, false);

   datetime minBacktestTime = 0;
   if(InpBacktestStartDate > 0)
      minBacktestTime = InpBacktestStartDate;
   else if(InpBacktestDays > 0)
      minBacktestTime = (TimeCurrent() - InpBacktestDays * 24 * 3600);

   int effectiveBacktestDays = InpBacktestDays;
   if(InpBacktestStartDate > 0)
   {
      int startDays = (int)((TimeCurrent() - InpBacktestStartDate) / 86400) + 30;
      if(startDays > effectiveBacktestDays) effectiveBacktestDays = startDays;
   }

   int secPerBar = PeriodSeconds(_Period);
   if(secPerBar <= 0) secPerBar = 60;
   int barsToCopy = MathMax(InpMaxBarsTF, (int)((effectiveBacktestDays * 86400) / secPerBar) + 5000);
   int copied = CopyTime(_Symbol, _Period, 0, barsToCopy, chartTime);
   CopyHigh(_Symbol, _Period, 0, barsToCopy, chartHigh);
   CopyLow(_Symbol, _Period, 0, barsToCopy, chartLow);
   CopyClose(_Symbol, _Period, 0, barsToCopy, chartClose);
   CopySpread(_Symbol, _Period, 0, barsToCopy, chartSpread);
   if(copied < 10)
   {
      if(handleSym != INVALID_HANDLE) FileClose(handleSym);
      return;
   }

   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;
   double bufferPips = ActiveSLOffsetPips() * pipSize;
   double simSpread = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * _Point;
   if(simSpread <= 0) simSpread = 1.0 * pipSize;
   int exportedCount = 0;
   for(int b = 0; b < g_boxCount; b++)
   {
      if(g_drawnBoxes[b].top <= 0) continue;
      if(minBacktestTime > 0 && g_drawnBoxes[b].t1 < minBacktestTime) continue;
      if(!ActiveTradeMacroTFs() && g_drawnBoxes[b].tf >= PERIOD_H1) continue;
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

         if(g_drawnBoxes[b].isPreIP) isLS = true;
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

      // 🌟 استخراج تمام الگوها و ستاپ‌ها بدون فیلتر جهت تحلیل و شبیه‌سازی در داشبورد
      // if((InpOnlyTradeKings || InpTradeOnlyGoldenKings) && !IsQualifiedKing(g_drawnBoxes[b].tf, role)) continue;

      bool isBull = true;
      double entryPrice = 0;
      double slPrice = 0;

      double pivotP = 0;
      if(isOI)
      {
         isBull = g_drawnBoxes[b].isOInnerBull; // جهت ترید حتماً جهت خود گره OInner است

         datetime closestPivotTime = 0;
         for(int k = 0; k < g_indepCount; k++)
         {
            if(!g_indepPivots[k].hasIP) continue;
            if(!IsPivotTimeframeMatch(k, g_drawnBoxes[b].tfTag)) continue;
            if(g_indepPivots[k].time <= g_drawnBoxes[b].t1)
            {
               // پیووت مبنای استاپ باید با جهت پوزیشن همخوانی داشته باشد:
               // برای بای (isBull): پیووت کف (!isHigh)
               // برای سل (!isBull): پیووت سقف (isHigh)
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
         if(isSwap) isBull = g_drawnBoxes[b].isSwapBull;
         else if(isRS) isBull = g_drawnBoxes[b].isRSBull;
         else if(isLS) isBull = g_drawnBoxes[b].isLSBull;
         else isBull = g_drawnBoxes[b].isBullish;
      }

      int bStartIdx = FindBarIndex(chartTime, copied, g_drawnBoxes[b].t1);
      datetime formEnd = (g_drawnBoxes[b].formationTime > 0) ? g_drawnBoxes[b].formationTime : g_drawnBoxes[b].t1;
      int bEndIdx   = FindBarIndex(chartTime, copied, formEnd);
      if(bEndIdx < bStartIdx) bEndIdx = bStartIdx;

      double patternHigh = g_drawnBoxes[b].top;
      double patternLow  = g_drawnBoxes[b].bottom;

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

      double boxHeight = g_drawnBoxes[b].top - g_drawnBoxes[b].bottom;
      datetime evalTime = (g_drawnBoxes[b].formationTime > 0) ? g_drawnBoxes[b].formationTime : g_drawnBoxes[b].t1;

      if(isBull)
      {
         entryPrice = g_drawnBoxes[b].top;
      }
      else
      {
         entryPrice = g_drawnBoxes[b].bottom;
      }
      slPrice = CalculateSetupStopLoss(isBull, entryPrice, patternHigh, patternLow, boxHeight, evalTime, g_drawnBoxes[b].tf, pipSize);

      double risk = MathAbs(entryPrice - slPrice);
      if(risk < _Point * 2.0) risk = _Point * 2.0;

      // 🌟 فیلترهای الگویی اولیه و اصطکاک (جهت شبیه‌سازی در داشبورد، تمام ستاپ‌ها صادر می‌شوند)
      // if(InpFilterSingleLS && IsSingleLSPattern(role)) continue;
      // if(InpFilterToxicPatterns && IsToxicPattern(role)) continue;
      // if(InpFilterPureFlags && IsPureNoiseFlag(role)) continue;
      // if(InpFilterLowRewardVsFriction && IsRewardLessThanFriction(risk / _Point)) continue;

      double tps[4];
      for(int tp = 0; tp < 4; tp++)
      {
         if(isBull) tps[tp] = entryPrice + risk * (tp + 1);
         else       tps[tp] = entryPrice - risk * (tp + 1);
      }

      datetime baseTime = (g_drawnBoxes[b].formationTime > 0) ? g_drawnBoxes[b].formationTime : g_drawnBoxes[b].t1;
      datetime confirmTime = g_drawnBoxes[b].confirmationTime;
      if(confirmTime <= 0 || confirmTime > baseTime + PeriodSeconds(g_drawnBoxes[b].tf) * 15)
         confirmTime = baseTime;

      int confirmIdx = FindBarIndex(chartTime, copied, confirmTime);
      if(confirmIdx < 0) confirmIdx = FindBarIndex(chartTime, copied, baseTime);
      if(confirmIdx < 0) confirmIdx = 0;

      boxHeight = MathAbs(g_drawnBoxes[b].top - g_drawnBoxes[b].bottom);
      double minDeparturePrice = isBull ? (entryPrice + boxHeight * 0.3) : (entryPrice - boxHeight * 0.3);

      bool isEntered = false;
      int  entryBarIdx = -1;
      datetime entryTime = 0;

      // شبیه‌سازی دقیق ورود بر اساس لایو بازار:
      // ۱. تایید هویت گره در لایو (confirmTime)
      // ۲. پرتاب و کلوز کامل کندل در بیرون از محدوده (departedBar)
      // ۳. اردر لیمیت روی پولبک و ورود منحصراً در کندل‌های بعدی (k > departedBar)
      int departedBar = -1;
      datetime maxBoxTime = baseTime + PeriodSeconds(g_drawnBoxes[b].tf) * 40;

      for(int k = confirmIdx; k < copied; k++)
      {
         // ابطال ۱: انقضای زمانی معامله با گذشت از اعتبار باکس
         if(departedBar < 0 && chartTime[k] > maxBoxTime) break;

         // ابطال ۲: برخورد قیمت به حد ضرر در هر زمان (حتی قبل از پرتاب) ستاپ را فوراً لغو می‌کند
         if(isBull)
         {
            if(chartLow[k] <= slPrice) break;
         }
         else
         {
            if((chartHigh[k] + GetBarSpread(k, chartSpread, simSpread)) >= slPrice) break;
         }

         if(departedBar < 0)
         {
            // تایید پرتاب و کلوز کامل کندل در بیرون از باکس
            if(isBull && chartClose[k] >= minDeparturePrice) departedBar = k;
            else if(!isBull && chartClose[k] <= minDeparturePrice) departedBar = k;

            // مهلت خروج اولیه از باکس حداکثر ۳۰ کندل
            datetime maxDepTime = confirmTime + PeriodSeconds(g_drawnBoxes[b].tf) * 30;
            if(chartTime[k] > maxDepTime) break;
         }
         else // ورود منحصراً روی کندل‌های بعد از پرتاب اولیه (پولبک واقعی - دقیقاً مطابق اردر لیمیت اکسپرت)
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

            // مهلت بازگشت پولبک به ثانیه بر مبنای تایم‌فریم الگو و پارامتر ورودی InpLimitExpirationBars
            datetime maxLimitTime = chartTime[departedBar] + PeriodSeconds(g_drawnBoxes[b].tf) * ActiveLimitExpirationBars();
            if(chartTime[k] > maxLimitTime) break;
         }
      }

      // 🌟 شبیه‌سازی دقیق ۴ مدل استاپ‌لاس به صورت موازی
      SimSLResult slModesRes[4];
      MqlRates m1Rates[];
      int m1Count = 0;

      if(isEntered && entryTime > 0)
      {
         // بهینه‌سازی خواندن دیتای M1 (فقط یک بار برای تمام مدل‌ها)
         m1Count = CopyRates(_Symbol, PERIOD_M1, entryTime, chartTime[copied - 1], m1Rates);

         // اطمینان از اعمال سقف و کف دقیق شکل‌گیری تا پایان باکس
         for(int ck = bStartIdx; ck <= bEndIdx && ck < copied; ck++)
         {
            if(chartHigh[ck] > patternHigh) patternHigh = chartHigh[ck];
            if(chartLow[ck] < patternLow)   patternLow  = chartLow[ck];
         }
      }

      for(int sm = 0; sm < 4; sm++)
      {
         double smSL = CalculateSetupStopLoss(isBull, entryPrice, patternHigh, patternLow, boxHeight, evalTime, g_drawnBoxes[b].tf, pipSize, sm);
         double smRisk = MathAbs(entryPrice - smSL);
         if(smRisk < _Point * 2.0) smRisk = _Point * 2.0;

         SimulateSingleSLMode(isBull, entryPrice, smSL, smRisk,
                              entryBarIdx, entryTime, m1Rates, m1Count,
                              chartTime, chartHigh, chartLow, chartClose, chartSpread, copied, simSpread,
                              slModesRes[sm]);
      }

      // تعیین مدل فعال جهت حفظ سازگاری ۱۰۰٪ با ستون‌های اصلی CSV
      int activeMode = (int)ActiveSLMode();
      if(activeMode < 0 || activeMode > 3) activeMode = 0;

      slPrice             = slModesRes[activeMode].slPrice;
      risk                = slModesRes[activeMode].riskPoints * _Point;
      double   exitPrice  = slModesRes[activeMode].exitPrice;
      datetime exitTime   = slModesRes[activeMode].exitTime;
      int      hitTP      = slModesRes[activeMode].hitTP;
      bool     isClosed   = slModesRes[activeMode].isClosed;
      string   outcomeStr = slModesRes[activeMode].outcome;

      for(int tp = 0; tp < 4; tp++)
         tps[tp] = isBull ? (entryPrice + risk * (tp + 1)) : (entryPrice - risk * (tp + 1));

      double entrySpreadPts = (entryBarIdx >= 0) ? (GetBarSpread(entryBarIdx, chartSpread, simSpread) / _Point) : (simSpread / _Point);

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
                   DoubleToString(exitPrice, _Digits),
                   DoubleToString(slPrice, _Digits),
                   DoubleToString(risk / _Point, 1),
                   DoubleToString(tps[0], _Digits),
                   DoubleToString(tps[1], _Digits),
                   DoubleToString(tps[2], _Digits),
                   DoubleToString(tps[3], _Digits),
                   outcomeStr,
                   IntegerToString(hitTP),
                   (isClosed ? "True" : "False"),
                   DoubleToString(entrySpreadPts, 1),
                   // داده‌های تفکیکی ۴ مدل استاپ‌لاس جهت آزمایشگاه و بهینه‌ساز داشبورد
                   DoubleToString(slModesRes[0].slPrice, _Digits),
                   DoubleToString(slModesRes[0].riskPoints, 1),
                   DoubleToString(slModesRes[0].exitPrice, _Digits),
                   IntegerToString(slModesRes[0].hitTP),
                   slModesRes[0].outcome,
                   DoubleToString(slModesRes[1].slPrice, _Digits),
                   DoubleToString(slModesRes[1].riskPoints, 1),
                   DoubleToString(slModesRes[1].exitPrice, _Digits),
                   IntegerToString(slModesRes[1].hitTP),
                   slModesRes[1].outcome,
                   DoubleToString(slModesRes[2].slPrice, _Digits),
                   DoubleToString(slModesRes[2].riskPoints, 1),
                   DoubleToString(slModesRes[2].exitPrice, _Digits),
                   IntegerToString(slModesRes[2].hitTP),
                   slModesRes[2].outcome,
                   DoubleToString(slModesRes[3].slPrice, _Digits),
                   DoubleToString(slModesRes[3].riskPoints, 1),
                   DoubleToString(slModesRes[3].exitPrice, _Digits),
                   IntegerToString(slModesRes[3].hitTP),
                   slModesRes[3].outcome);
      }

      exportedCount++;
   }

   if(handleSym != INVALID_HANDLE) FileClose(handleSym);

   PrintFormat("📁 FlagPro: تعداد %d موقعیت معاملاتی %s با موفقیت در فایل «%s» ذخیره شد.", exportedCount, _Symbol, symFilename);
}
