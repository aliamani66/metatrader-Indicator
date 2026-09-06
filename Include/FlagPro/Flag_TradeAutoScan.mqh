//+------------------------------------------------------------------+
//| Flag_TradeAutoScan.mqh                                           |
//| Automated Historical Trade Setup Scanner & Chart Renderer        |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""

//+------------------------------------------------------------------+
//| پاکسازی کامل پس‌زمینه رنگی معاملات (شدو سبز و قرمز)              |
//+------------------------------------------------------------------+
void DeleteAllTradeShadings()
{
   for(int i = ObjectsTotal(0, -1, OBJ_RECTANGLE) - 1; i >= 0; i--)
   {
      string objName = ObjectName(0, i, -1, OBJ_RECTANGLE);
      if(StringFind(objName, "_LOSS_BG") >= 0 || StringFind(objName, "_PROFIT_BG") >= 0)
      {
         ObjectDelete(0, objName);
      }
   }
}

//+------------------------------------------------------------------+
//| Render Automatic Trade Setups with Full Lifecycle Persistence    |
//+------------------------------------------------------------------+
void RenderAutoTradeSetups(const datetime &chartTime[], const double &chartHigh[], const double &chartLow[], const double &chartClose[], int ratesTotal)
{
   if(!InpShowTradeShading)
      DeleteAllTradeShadings();

   if(!InpAutoDrawTrades || ratesTotal < 10) return;

   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;
   double bufferPips = InpRSPipBuffer * pipSize;
   double simSpread = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * _Point;
   if(simSpread <= 0) simSpread = 1.0 * pipSize;

   int chartSpread[];
   ArraySetAsSeries(chartSpread, false);
   CopySpread(_Symbol, _Period, 0, ratesTotal, chartSpread);

   // مرحله ۱: شناسایی و ثبت معاملات جدید در مخزن پایدار g_tradeSetups
   for(int b = 0; b < g_boxCount; b++)
   {
      g_drawnBoxes[b].hasTradeEntered = false;
      if(g_drawnBoxes[b].top <= 0) continue;
      if(!InpTradeMacroTFs && g_drawnBoxes[b].tf >= PERIOD_H1) continue;
      if(g_effectiveStartDate > 0 && g_drawnBoxes[b].t1 < g_effectiveStartDate) continue;

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

      // فقط سلاطین طلایی تاییدشده مجاز به معامله هستند
      if(!IsQualifiedKing(g_drawnBoxes[b].tf, role)) continue;

      bool isBull = true;
      double entryPrice = 0;
      double slPrice    = 0;

      double pivotP = 0;
      if(isOI)
      {
         isBull = g_drawnBoxes[b].isOInnerBull;
         datetime closestPivotTime = 0;
         for(int k = 0; k < g_indepCount; k++)
         {
            if(!g_indepPivots[k].hasIP) continue;
            if(!IsPivotTimeframeMatch(k, g_drawnBoxes[b].tfTag)) continue;
            if(g_indepPivots[k].time <= g_drawnBoxes[b].t1)
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
         if(isSwap) isBull = g_drawnBoxes[b].isSwapBull;
         else if(isRS) isBull = g_drawnBoxes[b].isRSBull;
         else if(isLS) isBull = g_drawnBoxes[b].isLSBull;
         else isBull = g_drawnBoxes[b].isBullish;
      }

      int bStartIdx = FindBarIndex(chartTime, ratesTotal, g_drawnBoxes[b].t1);
      datetime formEnd = (g_drawnBoxes[b].formationTime > 0) ? g_drawnBoxes[b].formationTime : g_drawnBoxes[b].t1;
      int bEndIdx   = FindBarIndex(chartTime, ratesTotal, formEnd);
      if(bEndIdx < bStartIdx) bEndIdx = bStartIdx;

      double patternHigh = g_drawnBoxes[b].top;
      double patternLow  = g_drawnBoxes[b].bottom;

      if(isOI && pivotP > 0)
      {
         if(pivotP > patternHigh) patternHigh = pivotP;
         if(pivotP < patternLow)  patternLow  = pivotP;
      }

      // اسکن دقیق شدوی تمام کندل‌ها در بازه الگو تا خط استاپ حتماً بالای نوک شدوها قرار گیرد
      for(int ck = bStartIdx; ck <= bEndIdx && ck < ratesTotal; ck++)
      {
         if(chartHigh[ck] > patternHigh) patternHigh = chartHigh[ck];
         if(chartLow[ck] < patternLow)   patternLow  = chartLow[ck];
      }

      if(isBull)
      {
         entryPrice = g_drawnBoxes[b].top;
         slPrice    = patternLow - bufferPips;
      }
      else
      {
         entryPrice = g_drawnBoxes[b].bottom;
         slPrice    = patternHigh + bufferPips;
      }

      double risk = MathAbs(entryPrice - slPrice);
      if(risk < _Point * 2.0) risk = _Point * 2.0;

      // ۱. فیلترهای الگویی اولیه و اصطکاک (مستقل از زمان ورود)
      if(InpFilterSingleLS && IsSingleLSPattern(role)) continue;
      if(InpFilterToxicPatterns && IsToxicPattern(role)) continue;
      if(InpFilterPureFlags && IsPureNoiseFlag(role)) continue;
      if(InpFilterLowRewardVsFriction && IsRewardLessThanFriction(risk / _Point)) continue;

      datetime baseTime = (g_drawnBoxes[b].formationTime > 0) ? g_drawnBoxes[b].formationTime : g_drawnBoxes[b].t1;
      datetime confirmTime = g_drawnBoxes[b].confirmationTime;
      if(confirmTime <= 0 || confirmTime > baseTime + PeriodSeconds(g_drawnBoxes[b].tf) * 15)
         confirmTime = baseTime;

      int confirmIdx = FindBarIndex(chartTime, ratesTotal, confirmTime);
      if(confirmIdx < 0) confirmIdx = FindBarIndex(chartTime, ratesTotal, baseTime);
      if(confirmIdx < 0) confirmIdx = 0;

      double boxHeight = MathAbs(g_drawnBoxes[b].top - g_drawnBoxes[b].bottom);
      double minDeparturePrice = isBull ? (entryPrice + boxHeight * 0.3) : (entryPrice - boxHeight * 0.3);

      bool isEntered = false;
      int  entryBarIdx = -1;
      int  departedBar = -1;
      datetime entryTime = 0;
      datetime maxBoxTime = baseTime + PeriodSeconds(g_drawnBoxes[b].tf) * 40;

      for(int k = confirmIdx; k < ratesTotal; k++)
      {
         if(departedBar < 0 && chartTime[k] > maxBoxTime) break;

         if(isBull && chartLow[k] <= slPrice) break;
         if(!isBull && (chartHigh[k] + GetBarSpread(k, chartSpread, simSpread)) >= slPrice) break;

         if(departedBar < 0)
         {
            if(isBull && chartClose[k] >= minDeparturePrice) departedBar = k;
            else if(!isBull && chartClose[k] <= minDeparturePrice) departedBar = k;
            if(k - confirmIdx > 30) break;
         }
         else
         {
            double barSpread = GetBarSpread(k, chartSpread, simSpread);
            if(isBull && (chartLow[k] + barSpread) <= entryPrice)
            {
               isEntered = true;
               entryBarIdx = k;
               entryTime = chartTime[k];
               break;
            }
            else if(!isBull && chartHigh[k] >= entryPrice)
            {
               isEntered = true;
               entryBarIdx = k;
               entryTime = chartTime[k];
               break;
            }
            // مهلت بازگشت پولبک حداکثر ۴۰ کندل (مطابق اکسپرت تستر)
            if(k - departedBar > 40) break;
         }
      }

      if(!isEntered) continue;

      // ۲. فیلترهای زمانی ورود (بر مبنای زمان واقعی ورود entryTime - هماهنگ ۱۰۰٪ با اکسپرت)
      if(InpFilterNightHours && IsNightSessionHour(entryTime)) continue;
      if(InpFilterPreLondonHunt && IsPreLondonHour(entryTime)) continue;

      g_drawnBoxes[b].hasTradeEntered = true;

      // به‌روزرسانی نهایی حد ضرر و تارگت‌ها بر مبنای نوک واقعی شدوها از ابتدا تا دقیقاً لحظه ورود (entryBarIdx)
      for(int ck = bStartIdx; ck <= entryBarIdx && ck < ratesTotal; ck++)
      {
         if(chartHigh[ck] > patternHigh) patternHigh = chartHigh[ck];
         if(chartLow[ck] < patternLow)   patternLow  = chartLow[ck];
      }

      if(isBull) slPrice = patternLow - bufferPips;
      else       slPrice = patternHigh + bufferPips;

      risk = MathAbs(entryPrice - slPrice);
      if(risk < _Point * 2.0) risk = _Point * 2.0;

      // محاسبه فوری سرنوشت و زمان خروج واقعی معامله
      double tps[4];
      for(int tp = 0; tp < 4; tp++)
         tps[tp] = isBull ? entryPrice + risk * (tp + 1) : entryPrice - risk * (tp + 1);

      int hitTP = 0;
      bool isClosed = false;
      datetime exitTime = 0;
      datetime hitTime = 0;
      datetime tpTimes[4] = {0, 0, 0, 0};
      double currentSL = slPrice;

      for(int k = entryBarIdx; k < ratesTotal; k++)
      {
         if(isBull)
         {
            for(int tp = hitTP; tp < 4; tp++)
            {
               if(chartHigh[k] >= tps[tp])
               {
                  hitTP = tp + 1;
                  hitTime = chartTime[k];
                  if(tpTimes[tp] == 0) tpTimes[tp] = chartTime[k];
                  // انتقال به بریک‌ایون پس از تاچ TP1 و تریلینگ به TP1 و TP2
                  if(hitTP == 1) currentSL = entryPrice;
                  else if(hitTP == 2) currentSL = tps[0];
                  else if(hitTP == 3) currentSL = tps[1];
               }
            }
            if(chartLow[k] <= currentSL)
            {
               isClosed = true;
               exitTime = chartTime[k];
               break;
            }
            if(hitTP == 4)
            {
               isClosed = true;
               exitTime = hitTime;
               break;
            }
         }
         else
         {
            double barSpread = GetBarSpread(k, chartSpread, simSpread);
            for(int tp = hitTP; tp < 4; tp++)
            {
               if((chartLow[k] + barSpread) <= tps[tp])
               {
                  hitTP = tp + 1;
                  hitTime = chartTime[k];
                  if(tpTimes[tp] == 0) tpTimes[tp] = chartTime[k];
                  // انتقال به بریک‌ایون پس از تاچ TP1 و تریلینگ به TP1 و TP2
                  if(hitTP == 1) currentSL = entryPrice;
                  else if(hitTP == 2) currentSL = tps[0];
                  else if(hitTP == 3) currentSL = tps[1];
               }
            }
            if((chartHigh[k] + barSpread) >= currentSL)
            {
               isClosed = true;
               exitTime = chartTime[k];
               break;
            }
            if(hitTP == 4)
            {
               isClosed = true;
               exitTime = hitTime;
               break;
            }
         }
      }

      if(!isClosed)
         exitTime = (hitTP > 0) ? hitTime : chartTime[ratesTotal - 1];

      // بررسی عدم تکرار معامله در مخزن ماندگار g_tradeSetups
      bool exists = false;
      for(int t = 0; t < g_tradeCount; t++)
      {
         if(g_tradeSetups[t].boxName == g_drawnBoxes[b].boxName && g_tradeSetups[t].entryTime == entryTime)
         {
            exists = true;
            break;
         }
      }

      if(!exists)
      {
         // بررسی تداخل فقط در صورت غیرفعال بودن معاملات همزمان توسط کاربر
         if(!InpAllowOverlappingTrades)
         {
            bool isBusy = false;
            for(int t = 0; t < g_tradeCount; t++)
            {
               if(g_tradeSetups[t].tf == g_drawnBoxes[b].tf)
               {
                  if(entryTime >= g_tradeSetups[t].entryTime && entryTime < g_tradeSetups[t].exitTime)
                  {
                     isBusy = true;
                     break;
                  }
               }
            }
            if(isBusy) continue;
         }

         ArrayResize(g_tradeSetups, g_tradeCount + 1);
         g_tradeSetups[g_tradeCount].boxName    = g_drawnBoxes[b].boxName;
         g_tradeSetups[g_tradeCount].boxRole    = role;
         g_tradeSetups[g_tradeCount].tf         = g_drawnBoxes[b].tf;
         g_tradeSetups[g_tradeCount].tfTag      = g_drawnBoxes[b].tfTag;
         g_tradeSetups[g_tradeCount].isBuy      = isBull;
         g_tradeSetups[g_tradeCount].entryTime  = entryTime;
         g_tradeSetups[g_tradeCount].entryPrice = entryPrice;
         g_tradeSetups[g_tradeCount].slPrice    = slPrice;
         g_tradeSetups[g_tradeCount].risk       = risk;
         g_tradeSetups[g_tradeCount].tp1        = tps[0];
         g_tradeSetups[g_tradeCount].tp2        = tps[1];
         g_tradeSetups[g_tradeCount].tp3        = tps[2];
         g_tradeSetups[g_tradeCount].tp4        = tps[3];
         g_tradeSetups[g_tradeCount].exitTime   = exitTime;
         g_tradeSetups[g_tradeCount].hitTP      = hitTP;
         g_tradeSetups[g_tradeCount].isClosed   = isClosed;
         g_tradeSetups[g_tradeCount].tp1Time    = tpTimes[0];
         g_tradeSetups[g_tradeCount].tp2Time    = tpTimes[1];
         g_tradeSetups[g_tradeCount].tp3Time    = tpTimes[2];
         g_tradeSetups[g_tradeCount].tp4Time    = tpTimes[3];
         g_tradeCount++;
      }
   }

   // مرحله ۲: بروزرسانی وضعیت معاملات باز
   for(int t = 0; t < g_tradeCount; t++)
   {
      double tps[4];
      tps[0] = g_tradeSetups[t].tp1;
      tps[1] = g_tradeSetups[t].tp2;
      tps[2] = g_tradeSetups[t].tp3;
      tps[3] = g_tradeSetups[t].tp4;

      if(!g_tradeSetups[t].isClosed)
      {
         int entryBarIdx = FindBarIndex(chartTime, ratesTotal, g_tradeSetups[t].entryTime);
         if(entryBarIdx < 0) entryBarIdx = 0;

         int currentHitTP = g_tradeSetups[t].hitTP;
         datetime hitTime = 0;

         double currentSL = g_tradeSetups[t].slPrice;
         if(currentHitTP == 1) currentSL = g_tradeSetups[t].entryPrice;
         else if(currentHitTP == 2) currentSL = tps[0];
         else if(currentHitTP >= 3) currentSL = tps[1];

         for(int k = entryBarIdx; k < ratesTotal; k++)
         {
            if(g_tradeSetups[t].isBuy)
            {
               for(int tp = currentHitTP; tp < 4; tp++)
               {
                  if(chartHigh[k] >= tps[tp])
                  {
                     currentHitTP = tp + 1;
                     hitTime = chartTime[k];
                     if(tp == 0 && g_tradeSetups[t].tp1Time == 0) g_tradeSetups[t].tp1Time = hitTime;
                     else if(tp == 1 && g_tradeSetups[t].tp2Time == 0) g_tradeSetups[t].tp2Time = hitTime;
                     else if(tp == 2 && g_tradeSetups[t].tp3Time == 0) g_tradeSetups[t].tp3Time = hitTime;
                     else if(tp == 3 && g_tradeSetups[t].tp4Time == 0) g_tradeSetups[t].tp4Time = hitTime;

                     // به‌روزرسانی حد ضرر دینامیک
                     if(currentHitTP == 1) currentSL = g_tradeSetups[t].entryPrice;
                     else if(currentHitTP == 2) currentSL = tps[0];
                     else if(currentHitTP == 3) currentSL = tps[1];
                  }
               }
               if(chartLow[k] <= currentSL)
               {
                  g_tradeSetups[t].isClosed = true;
                  g_tradeSetups[t].exitTime = chartTime[k];
                  break;
               }
               if(currentHitTP == 4)
               {
                  g_tradeSetups[t].isClosed = true;
                  g_tradeSetups[t].exitTime = hitTime;
                  break;
               }
            }
            else
            {
               double barSpread = GetBarSpread(k, chartSpread, simSpread);
               for(int tp = currentHitTP; tp < 4; tp++)
               {
                  if((chartLow[k] + barSpread) <= tps[tp])
                  {
                     currentHitTP = tp + 1;
                     hitTime = chartTime[k];
                     if(tp == 0 && g_tradeSetups[t].tp1Time == 0) g_tradeSetups[t].tp1Time = hitTime;
                     else if(tp == 1 && g_tradeSetups[t].tp2Time == 0) g_tradeSetups[t].tp2Time = hitTime;
                     else if(tp == 2 && g_tradeSetups[t].tp3Time == 0) g_tradeSetups[t].tp3Time = hitTime;
                     else if(tp == 3 && g_tradeSetups[t].tp4Time == 0) g_tradeSetups[t].tp4Time = hitTime;

                     // به‌روزرسانی حد ضرر دینامیک
                     if(currentHitTP == 1) currentSL = g_tradeSetups[t].entryPrice;
                     else if(currentHitTP == 2) currentSL = tps[0];
                     else if(currentHitTP == 3) currentSL = tps[1];
                  }
               }
               if((chartHigh[k] + barSpread) >= currentSL)
               {
                  g_tradeSetups[t].isClosed = true;
                  g_tradeSetups[t].exitTime = chartTime[k];
                  break;
               }
               if(currentHitTP == 4)
               {
                  g_tradeSetups[t].isClosed = true;
                  g_tradeSetups[t].exitTime = hitTime;
                  break;
               }
            }
         }

         g_tradeSetups[t].hitTP = currentHitTP;
         if(!g_tradeSetups[t].isClosed)
            g_tradeSetups[t].exitTime = chartTime[ratesTotal - 1];
      }
   }

   // مرحله ۳: رسم گرافیک معاملات بر روی چارت (اولویت قطعی با جدیدترین معاملات از امروز به گذشته)
   // جهت جلوگیری از پر شدن حافظه اشیاء متاتریدر و تضمین رسم کامل معاملات روزها و ماه‌های اخیر
   ObjectsDeleteAll(0, FP_PREFIX + "AUTO_TR_");

   int drawnCount = 0;
   int maxTradesToDraw = 2000;

   for(int t = g_tradeCount - 1; t >= 0; t--)
   {
      // 👑 فقط رسم معاملات ۱۸ سلطان برگزیده بر اساس تایم‌فریم
      if((InpOnlyTradeKings || InpTradeOnlyGoldenKings) && !IsQualifiedKing(g_tradeSetups[t].tf, g_tradeSetups[t].boxRole))
         continue;

      datetime t1 = g_tradeSetups[t].entryTime;
      if(g_effectiveStartDate > 0 && t1 < g_effectiveStartDate)
         continue;

      if(drawnCount >= maxTradesToDraw)
         break;

      drawnCount++;

      double tps[4];
      tps[0] = g_tradeSetups[t].tp1;
      tps[1] = g_tradeSetups[t].tp2;
      tps[2] = g_tradeSetups[t].tp3;
      tps[3] = g_tradeSetups[t].tp4;

      datetime t2 = g_tradeSetups[t].exitTime;
      if(t2 <= t1) t2 = t1 + PeriodSeconds(_Period) * 10;

      string pfx = FP_PREFIX + "AUTO_TR_" + IntegerToString(t) + "_";
      int hitTP = g_tradeSetups[t].hitTP;
      int activeTP = (hitTP > 0) ? (hitTP - 1) : 0;
      double activeTPPrice = (activeTP == 0 ? tps[0] : (activeTP == 1 ? tps[1] : (activeTP == 2 ? tps[2] : tps[3])));

      // ۰. بک‌گراند کم‌رنگ و ملایم معامله (فقط در صورت روشن بودن InpShowTradeShading)
      if(InpShowTradeShading)
      {
         bool drawProfit = (!g_tradeSetups[t].isClosed || hitTP > 0);
         bool drawLoss   = (!g_tradeSetups[t].isClosed || hitTP == 0);

         if(drawProfit)
         {
            double tpTop = g_tradeSetups[t].isBuy ? activeTPPrice : g_tradeSetups[t].entryPrice;
            double tpBtm = g_tradeSetups[t].isBuy ? g_tradeSetups[t].entryPrice : activeTPPrice;
            string profitZone = pfx + "PROFIT_BG";
            ObjectCreate(0, profitZone, OBJ_RECTANGLE, 0, t1, tpTop, t2, tpBtm);
            ObjectSetInteger(0, profitZone, OBJPROP_COLOR, C'15,35,55'); // آبی دودی ملایم
            ObjectSetInteger(0, profitZone, OBJPROP_FILL, true);
            ObjectSetInteger(0, profitZone, OBJPROP_BACK, true);
            ObjectSetInteger(0, profitZone, OBJPROP_SELECTABLE, false);
         }

         if(drawLoss)
         {
            double slTop = g_tradeSetups[t].isBuy ? g_tradeSetups[t].entryPrice : g_tradeSetups[t].slPrice;
            double slBtm = g_tradeSetups[t].isBuy ? g_tradeSetups[t].slPrice : g_tradeSetups[t].entryPrice;
            string lossZone = pfx + "LOSS_BG";
            ObjectCreate(0, lossZone, OBJ_RECTANGLE, 0, t1, slTop, t2, slBtm);
            ObjectSetInteger(0, lossZone, OBJPROP_COLOR, C'55,35,15'); // کهربایی نارنجی ملایم
            ObjectSetInteger(0, lossZone, OBJPROP_FILL, true);
            ObjectSetInteger(0, lossZone, OBJPROP_BACK, true);
            ObjectSetInteger(0, lossZone, OBJPROP_SELECTABLE, false);
         }
      }
      else
      {
         string profitZone = pfx + "PROFIT_BG";
         string lossZone   = pfx + "LOSS_BG";
         if(ObjectFind(0, profitZone) >= 0) ObjectDelete(0, profitZone);
         if(ObjectFind(0, lossZone) >= 0)   ObjectDelete(0, lossZone);
      }

      // انتخاب پالت رنگی معامله (در صورت روشن بودن InpUniqueTradeColors هر معامله رنگ مجزا و اختصاصی دارد)
      color tradeClr = InpUniqueTradeColors ? GetTradeSetupColor(t) : InpTradeTPColor;
      color entryClr = InpUniqueTradeColors ? tradeClr : InpTradeEntryColor;
      color slClr    = InpUniqueTradeColors ? tradeClr : InpTradeSLColor;
      color tpClr    = InpUniqueTradeColors ? tradeClr : InpTradeTPColor;

      // ۱. خط ورود (امتداد تا انتهای معامله t2 با خط‌چین)
      string entryLine = pfx + "ENTRY";
      ObjectCreate(0, entryLine, OBJ_TREND, 0, t1, g_tradeSetups[t].entryPrice, t2, g_tradeSetups[t].entryPrice);
      ObjectSetInteger(0, entryLine, OBJPROP_COLOR, entryClr);
      ObjectSetInteger(0, entryLine, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, entryLine, OBJPROP_STYLE, STYLE_DASH);
      ObjectSetInteger(0, entryLine, OBJPROP_RAY_RIGHT, false);
      ObjectSetInteger(0, entryLine, OBJPROP_SELECTABLE, false);

      string entryLbl = pfx + "ENTRY_LBL";
      ObjectCreate(0, entryLbl, OBJ_TEXT, 0, t1, g_tradeSetups[t].entryPrice);
      ObjectSetString(0, entryLbl, OBJPROP_TEXT, " Entry");
      ObjectSetInteger(0, entryLbl, OBJPROP_COLOR, entryClr);
      ObjectSetInteger(0, entryLbl, OBJPROP_FONTSIZE, 7);
      ObjectSetInteger(0, entryLbl, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(0, entryLbl, OBJPROP_SELECTABLE, false);

      // ۲. خط حد ضرر متمایز از خط قرمز تستر (امتداد تا انتهای معامله t2 با نقطه‌چین و برچسب SL)
      string slLine = pfx + "SL";
      ObjectCreate(0, slLine, OBJ_TREND, 0, t1, g_tradeSetups[t].slPrice, t2, g_tradeSetups[t].slPrice);
      ObjectSetInteger(0, slLine, OBJPROP_COLOR, slClr);
      ObjectSetInteger(0, slLine, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, slLine, OBJPROP_STYLE, STYLE_DOT);
      ObjectSetInteger(0, slLine, OBJPROP_RAY_RIGHT, false);
      ObjectSetInteger(0, slLine, OBJPROP_SELECTABLE, false);

      string slLbl = pfx + "SL_LBL";
      ObjectCreate(0, slLbl, OBJ_TEXT, 0, t2, g_tradeSetups[t].slPrice);
      ObjectSetString(0, slLbl, OBJPROP_TEXT, " SL");
      ObjectSetInteger(0, slLbl, OBJPROP_COLOR, slClr);
      ObjectSetInteger(0, slLbl, OBJPROP_FONTSIZE, 7);
      ObjectSetInteger(0, slLbl, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(0, slLbl, OBJPROP_SELECTABLE, false);

      // ۳. خطوط تارگت‌های ۴ گانه (فقط تا جایی که تاچ شده‌اند امتداد دارند و بیشتر ادامه پیدا نمی‌کنند)
      datetime tpTimes[4];
      tpTimes[0] = g_tradeSetups[t].tp1Time;
      tpTimes[1] = g_tradeSetups[t].tp2Time;
      tpTimes[2] = g_tradeSetups[t].tp3Time;
      tpTimes[3] = g_tradeSetups[t].tp4Time;

      for(int p = 0; p < 4; p++)
      {
         // خط TP فقط تا جایی امتداد دارد که تاچ شده است؛ بیشتر ادامه پیدا نکند
         datetime tpEnd = (tpTimes[p] > 0) ? tpTimes[p] : t2;
         if(tpEnd <= t1) tpEnd = t1 + PeriodSeconds(_Period);

         string tpLine = pfx + "TP" + IntegerToString(p + 1);
         ObjectCreate(0, tpLine, OBJ_TREND, 0, t1, tps[p], tpEnd, tps[p]);
         ObjectSetInteger(0, tpLine, OBJPROP_COLOR, tpClr);
         ObjectSetInteger(0, tpLine, OBJPROP_WIDTH, (hitTP >= p + 1 ? 2 : 1));
         ObjectSetInteger(0, tpLine, OBJPROP_STYLE, (hitTP >= p + 1 ? STYLE_SOLID : STYLE_DOT));
         ObjectSetInteger(0, tpLine, OBJPROP_RAY_RIGHT, false);
         ObjectSetInteger(0, tpLine, OBJPROP_SELECTABLE, false);

         string tpLbl = pfx + "TP" + IntegerToString(p + 1) + "_LBL";
         ObjectCreate(0, tpLbl, OBJ_TEXT, 0, tpEnd, tps[p]);
         ObjectSetString(0, tpLbl, OBJPROP_TEXT, StringFormat(" TP%d", p + 1));
         ObjectSetInteger(0, tpLbl, OBJPROP_COLOR, tpClr);
         ObjectSetInteger(0, tpLbl, OBJPROP_FONTSIZE, 7);
         ObjectSetInteger(0, tpLbl, OBJPROP_ANCHOR, ANCHOR_LEFT);
         ObjectSetInteger(0, tpLbl, OBJPROP_SELECTABLE, false);
      }

      // ۴. برچسب نتیجه در انتهای معامله
      string resLbl = pfx + "RES_LBL";
      string resTxt = "";
      if(!g_tradeSetups[t].isClosed)
         resTxt = (hitTP > 0) ? StringFormat("⏳ باز: TP%d (+%dR)", hitTP, hitTP) : "⏳ در حال معامله...";
      else
         resTxt = (hitTP > 0) ? StringFormat("🎯 TP%d (+%dR)", hitTP, hitTP) : "❌ SL (-1R)";

      color resClr = InpUniqueTradeColors ? tradeClr : ((hitTP > 0) ? InpTradeTPColor : (g_tradeSetups[t].isClosed ? InpTradeSLColor : clrGold));

      double labelPrice = (hitTP > 0) ? activeTPPrice : g_tradeSetups[t].slPrice;
      ObjectCreate(0, resLbl, OBJ_TEXT, 0, t2, labelPrice);
      ObjectSetString(0, resLbl, OBJPROP_TEXT, " " + resTxt + " [" + g_tradeSetups[t].boxRole + "]");
      ObjectSetInteger(0, resLbl, OBJPROP_COLOR, resClr);
      ObjectSetInteger(0, resLbl, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, resLbl, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(0, resLbl, OBJPROP_SELECTABLE, false);
   }
}

