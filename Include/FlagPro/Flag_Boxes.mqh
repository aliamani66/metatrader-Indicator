//+------------------------------------------------------------------+
//| Flag_Boxes.mqh                                                   |
//| FlagPro Box Processing: LS, RS, OInner & Universal Swap Engine   |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""

//+------------------------------------------------------------------+
//| Process Timeframe Swings & Draw Flag Boxes                       |
//+------------------------------------------------------------------+
void ProcessTF(ENUM_TIMEFRAMES tf, int sBars, color clr,
               const datetime &chartTime[], const double &chartHigh[], const double &chartLow[],
               int ratesTotal, int daysBack)
{
   SPivot pivots[];
   if(g_testerStartBase == 0)
      g_testerStartBase = TimeCurrent();

   int maxBars = InpMaxBarsTF;
   if(daysBack > 0)
   {
      int secPerBar = PeriodSeconds(tf);
      if(secPerBar <= 0) secPerBar = 60;
      int elapsedSec = (g_testerStartBase > 0) ? (int)(TimeCurrent() - g_testerStartBase) : 0;
      if(elapsedSec < 0) elapsedSec = 0;
      maxBars = ((daysBack * 86400 + elapsedSec) / secPerBar) + 1000;
   }
   else
   {
      if(tf == PERIOD_D1)       maxBars = 500;
      else if(tf == PERIOD_W1)  maxBars = 200;
      else if(tf == PERIOD_H4)  maxBars = 1000;
      else if(tf == PERIOD_H1)  maxBars = 1500;
      else if(tf == PERIOD_M15) maxBars = 2000;
      else if(tf == PERIOD_M5)  maxBars = 3000;
      else if(tf == PERIOD_M1)  maxBars = 5000;
   }

   if(!BuildAlternatingPivots(tf, sBars, maxBars, pivots))
   {
      return;
   }

   int count = ArraySize(pivots);
   if(count < 2) return;

   if(tf == PERIOD_H1)
   {
      ArrayResize(g_pivotsH1, count);
      for(int i = 0; i < count; i++) g_pivotsH1[i] = pivots[i];
      g_pivotCountH1 = count;
   }

   string tfTag = TFName(tf);
   string tfSymbol = (tf == PERIOD_H1) ? "H1" : tfTag;

   datetime limitTime = 0;
   if(daysBack > 0)
   {
      datetime baseTime = ((bool)MQLInfoInteger(MQL_TESTER)) ? g_testerStartBase : TimeCurrent();
      limitTime = baseTime - daysBack * 24 * 60 * 60;
   }

   //--- مرحله ۱: مشخص کردن اینکه کدام یال‌ها و پیووت‌ها متعلق به باکس‌های پرچم هستند
   bool isLegBox[];
   ArrayResize(isLegBox, count);
   ArrayInitialize(isLegBox, false);

   bool pivotInBox[];
   ArrayResize(pivotInBox, count);
   ArrayInitialize(pivotInBox, false);

   for(int i = 0; i < count - 1; i++)
   {
      if(IsValidFlagLeg(i, pivots, count))
      {
         isLegBox[i] = true;
         pivotInBox[i]     = true;
         pivotInBox[i + 1] = true;
      }
   }

   //--- مرحله ۲: شناسایی پیووت‌های مستقل و باکس‌های ماقبل آن‌ها (Pre-IP)
   bool isPreIPBox[];
   ArrayResize(isPreIPBox, count);
   ArrayInitialize(isPreIPBox, false);

   bool targetIPIsHighArr[];
   ArrayResize(targetIPIsHighArr, count);
   ArrayInitialize(targetIPIsHighArr, false);

   datetime targetIPTimeArr[];
   ArrayResize(targetIPTimeArr, count);
   ArrayInitialize(targetIPTimeArr, 0);

   for(int p = 0; p < count; p++)
   {
      if(pivotInBox[p])
         continue;

      int prevBoxLegIdx = -1;
      for(int k = p - 1; k >= 0; k--)
      {
         if(isLegBox[k])
         {
            prevBoxLegIdx = k;
            break;
         }
      }

      if(prevBoxLegIdx >= 0)
      {
         isPreIPBox[prevBoxLegIdx] = true;
         datetime exactIPTime = GetExactPivotChartTime(pivots[p].time, tf, pivots[p].price, pivots[p].isHigh,
                                                       chartTime, chartHigh, chartLow, ratesTotal);
         targetIPIsHighArr[prevBoxLegIdx] = pivots[p].isHigh;
         targetIPTimeArr[prevBoxLegIdx]   = exactIPTime;
      }
   }

   //--- مرحله ۳: تجمیع پیووت‌ها در مخزن سراسری جهت شناسایی گره‌های OInner و رسم مارکرها
   for(int p = 0; p < count; p++)
      {
         bool isIndependent = !pivotInBox[p];
         if(InpOnlyPureIndependent && !isIndependent)
            continue;

         datetime exactTime = GetExactPivotChartTime(pivots[p].time, tf, pivots[p].price, pivots[p].isHigh,
                                                     chartTime, chartHigh, chartLow, ratesTotal);

         int foundIdx = -1;
         for(int k = 0; k < g_indepCount; k++)
         {
            if(g_indepPivots[k].isHigh == pivots[p].isHigh)
            {
               if(MathAbs(g_indepPivots[k].time - exactTime) <= 7200 &&
                  MathAbs(g_indepPivots[k].price - pivots[p].price) <= 10 * _Point)
               {
                  foundIdx = k;
                  break;
               }
            }
         }

         if(foundIdx >= 0)
         {
            if(isIndependent) g_indepPivots[foundIdx].hasIP = true;
            bool exists = false;
            for(int t = 0; t < ArraySize(g_indepPivots[foundIdx].tfTags); t++)
            {
               if(g_indepPivots[foundIdx].tfTags[t] == tfSymbol) { exists = true; break; }
            }
            if(!exists)
            {
               int len = ArraySize(g_indepPivots[foundIdx].tfTags);
               ArrayResize(g_indepPivots[foundIdx].tfTags, len + 1);
               g_indepPivots[foundIdx].tfTags[len] = tfSymbol;
            }
         }
         else
         {
            ArrayResize(g_indepPivots, g_indepCount + 1);
            g_indepPivots[g_indepCount].time   = exactTime;
            g_indepPivots[g_indepCount].price  = pivots[p].price;
            g_indepPivots[g_indepCount].isHigh = pivots[p].isHigh;
            g_indepPivots[g_indepCount].hasIP  = isIndependent;
            g_indepPivots[g_indepCount].clr    = pivots[p].isHigh ? InpIndepColorHigh : InpIndepColorLow;
            ArrayResize(g_indepPivots[g_indepCount].tfTags, 1);
            g_indepPivots[g_indepCount].tfTags[0] = tfSymbol;
            g_indepCount++;
         }
      }

   //--- مرحله ۴: رسم باکس‌های پرچم
   for(int i = 0; i < count - 1; i++)
   {
      if(!isLegBox[i])
         continue;

      SPivot p1 = pivots[i];
      SPivot p2 = pivots[i + 1];

      if(daysBack > 0 && p1.time < limitTime)
         continue;

      double boxTop    = MathMax(p1.price, p2.price);
      double boxBottom = MathMin(p1.price, p2.price);

      int idx1 = FindBarIndex(chartTime, ratesTotal, p1.time);
      int idx2 = FindBarIndex(chartTime, ratesTotal, p2.time);
      if(idx1 < 0 || idx2 < 0) continue;

      int idxStart = MathMin(idx1, idx2);
      int idxEnd   = MathMax(idx1, idx2);

      // ===== امتداد به عقب (Backward Extension) =====
      int leftIdx = idxStart;
      for(int k = idxStart - 1; k >= 0; k--)
      {
         bool candleInsideBox = (chartLow[k] >= boxBottom && chartHigh[k] <= boxTop);
         if(!candleInsideBox)
         {
            leftIdx = k + 1;
            break;
         }
         leftIdx = k;
      }
      if(leftIdx > 0) leftIdx--;

      // ===== امتداد به جلو (Forward Extension) و تشخیص قطعی جهت شکست =====
      int rightIdx = idxEnd;
      bool brokeUp = false;
      bool brokeDown = false;
      for(int k = idxEnd + 1; k < ratesTotal; k++)
      {
         if(chartHigh[k] > boxTop)
         {
            brokeUp = true;
            rightIdx = k;
            break;
         }
         else if(chartLow[k] < boxBottom)
         {
            brokeDown = true;
            rightIdx = k;
            break;
         }
         rightIdx = k;
      }
      if(rightIdx <= leftIdx && leftIdx < ratesTotal - 1) rightIdx = leftIdx + 1;
      if(rightIdx < ratesTotal - 1) rightIdx++;

      datetime t1 = chartTime[leftIdx];
      datetime t2 = chartTime[rightIdx];

      string boxKey = IntegerToString((int)p1.time) + "_" + IntegerToString((int)p2.time);
      string boxType = (p1.isHigh ? "B" : "R");
      string preTag = (isPreIPBox[i] && InpHighlightPreIP) ? "_PREIP_" : "_";
      string boxName = FP_PREFIX + "BOX_" + tfTag + preTag + boxType + "_" + boxKey;
      
      // ثبت باکس در مخزن سراسری
      ArrayResize(g_drawnBoxes, g_boxCount + 1);
      g_drawnBoxes[g_boxCount].boxName   = boxName;
      g_drawnBoxes[g_boxCount].boxKey    = boxKey;
      g_drawnBoxes[g_boxCount].tf        = tf;
      g_drawnBoxes[g_boxCount].tfTag     = tfSymbol;
      g_drawnBoxes[g_boxCount].swingIdx  = i;
      g_drawnBoxes[g_boxCount].t1        = t1;
      g_drawnBoxes[g_boxCount].t2        = t2;
      g_drawnBoxes[g_boxCount].formationTime = chartTime[idxEnd];
      g_drawnBoxes[g_boxCount].confirmationTime = chartTime[idxEnd] + PeriodSeconds(tf) * InpSwingBars;
      g_drawnBoxes[g_boxCount].top       = boxTop;
      g_drawnBoxes[g_boxCount].bottom    = boxBottom;
      g_drawnBoxes[g_boxCount].baseColor      = clr;
      g_drawnBoxes[g_boxCount].baseWidth      = InpLineWidth;
      g_drawnBoxes[g_boxCount].baseStyle      = GetTFLineStyle(tf);
      
      // قانون بنیادین پرایس‌اکشن:
      // خروج از کف یعنی گره مقاومت نزولی است (Bearish)
      // خروج از سقف یعنی گره حمایت صعودی است (Bullish)
      bool isBullish = (!p1.isHigh && p2.isHigh);
      if(brokeUp) isBullish = true;
      else if(brokeDown) isBullish = false;
      g_drawnBoxes[g_boxCount].isBullish      = isBullish;
      g_drawnBoxes[g_boxCount].isPreIP        = isPreIPBox[i];
      g_drawnBoxes[g_boxCount].isLSBull       = targetIPIsHighArr[i];
      g_drawnBoxes[g_boxCount].targetIPTime   = targetIPTimeArr[i];
      g_drawnBoxes[g_boxCount].targetIPIsHigh = targetIPIsHighArr[i];
      g_drawnBoxes[g_boxCount].isBOFlag       = false;
      g_drawnBoxes[g_boxCount].isRSBull       = false;
      g_drawnBoxes[g_boxCount].isOInner       = false;
      g_drawnBoxes[g_boxCount].isOInnerBull   = false;
      g_drawnBoxes[g_boxCount].isSwap         = false;
      g_drawnBoxes[g_boxCount].isSwapBull     = false;
      g_drawnBoxes[g_boxCount].swapSourceRole = "";
      ArrayResize(g_drawnBoxes[g_boxCount].rsTags, 0);

      if(isPreIPBox[i] && InpHighlightPreIP)
      {
         int tagLen = ArraySize(g_drawnBoxes[g_boxCount].rsTags);
         ArrayResize(g_drawnBoxes[g_boxCount].rsTags, tagLen + 1);
         g_drawnBoxes[g_boxCount].rsTags[tagLen] = "LS";
      }

      g_drawnBoxes[g_boxCount].isMacro = (tf == PERIOD_W1 || tf == PERIOD_D1 || tf == PERIOD_H4);
      g_boxCount++;
   }

   // فیلتر حذف باکس‌های هم‌پوشان
   if(InpRemoveOverlapping)
   {
      for(int i = 0; i < g_boxCount; i++)
      {
         if(g_drawnBoxes[i].tf != tf) continue;
         if(g_drawnBoxes[i].top < 0) continue;

         double top1 = g_drawnBoxes[i].top;
         double bot1 = g_drawnBoxes[i].bottom;
         datetime t1 = g_drawnBoxes[i].t1;
         datetime t2 = g_drawnBoxes[i].t2;

         for(int j = i + 1; j < g_boxCount; j++)
         {
            if(g_drawnBoxes[j].tf != tf) continue;
            if(g_drawnBoxes[j].top < 0) continue;

            double top2 = g_drawnBoxes[j].top;
            double bot2 = g_drawnBoxes[j].bottom;
            datetime jt1 = g_drawnBoxes[j].t1;
            datetime jt2 = g_drawnBoxes[j].t2;

            bool timeOverlap = !(t2 < jt1 || jt2 < t1);
            if(!timeOverlap) continue;

            double interTop = MathMin(top1, top2);
            double interBot = MathMax(bot1, bot2);
            if(interTop <= interBot) continue;

            double h1 = top1 - bot1;
            double h2 = top2 - bot2;
            double interH = interTop - interBot;

            if(h1 > 0 && h2 > 0)
            {
               double ratio1 = interH / h1;
               double ratio2 = interH / h2;

               if(ratio1 > 0.80 || ratio2 > 0.80)
               {
                  int idx1 = i, idx2 = j;
                  if(g_drawnBoxes[idx1].isPreIP && !g_drawnBoxes[idx2].isPreIP)
                     g_drawnBoxes[idx2].top = -1;
                  else if(!g_drawnBoxes[idx1].isPreIP && g_drawnBoxes[idx2].isPreIP)
                  {
                     g_drawnBoxes[idx1].top = -1;
                     break;
                  }
                  else
                  {
                     double area1 = MathAbs(g_drawnBoxes[idx1].top - g_drawnBoxes[idx1].bottom) * (double)(g_drawnBoxes[idx1].t2 - g_drawnBoxes[idx1].t1 + 1);
                     double area2 = MathAbs(g_drawnBoxes[idx2].top - g_drawnBoxes[idx2].bottom) * (double)(g_drawnBoxes[idx2].t2 - g_drawnBoxes[idx2].t1 + 1);
                     if(area1 >= area2)
                        g_drawnBoxes[idx2].top = -1;
                     else
                     {
                        g_drawnBoxes[idx1].top = -1;
                        break;
                     }
                  }
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Process and draw RS Breakout Lines directly from LS Launch Boxes |
//+------------------------------------------------------------------+
void ProcessRSLinesFromLSBoxes(const datetime &chartTime[], const double &chartHigh[], const double &chartLow[], int ratesTotal)
{
   for(int b = 0; b < g_boxCount; b++)
   {
      if(g_drawnBoxes[b].top <= 0) continue;
      if(!g_drawnBoxes[b].isPreIP) continue;

      bool targetIsHigh   = g_drawnBoxes[b].targetIPIsHigh;
      datetime targetTime = g_drawnBoxes[b].targetIPTime;
      datetime startTime  = targetTime;

      double linePrice = targetIsHigh ? g_drawnBoxes[b].bottom : g_drawnBoxes[b].top;
      color lineColor  = targetIsHigh ? InpOriginColorLow : InpOriginColorHigh;

      int targetBarIdx = FindBarIndex(chartTime, ratesTotal, targetTime);
      int searchStart  = targetBarIdx >= 0 ? targetBarIdx : FindBarIndex(chartTime, ratesTotal, startTime);
      if(searchStart < 0) searchStart = 0;

      int breakIdx = ratesTotal - 1;
      for(int k = searchStart + 1; k < ratesTotal; k++)
      {
         if(targetIsHigh)
         {
            if(chartLow[k] < linePrice)
            {
               breakIdx = k;
               break;
            }
         }
         else
         {
            if(chartHigh[k] > linePrice)
            {
               breakIdx = k;
               break;
            }
         }
      }

      datetime endTime = chartTime[breakIdx];
      if(endTime <= startTime && ratesTotal > 0) endTime = chartTime[ratesTotal - 1];

      if(InpEnableOriginLines)
      {
         string lineName = FP_PREFIX + "RS_LINE_" + g_drawnBoxes[b].tfTag + "_" + IntegerToString((int)startTime);

         if(ObjectFind(0, lineName) >= 0) ObjectDelete(0, lineName);
         ObjectCreate(0, lineName, OBJ_TREND, 0, startTime, linePrice, endTime, linePrice);
         ObjectSetInteger(0, lineName, OBJPROP_COLOR, lineColor);
         ObjectSetInteger(0, lineName, OBJPROP_STYLE, g_drawnBoxes[b].baseStyle);
         ObjectSetInteger(0, lineName, OBJPROP_WIDTH, InpOriginLineWidth);
         ObjectSetInteger(0, lineName, OBJPROP_RAY_RIGHT, false);
         ObjectSetInteger(0, lineName, OBJPROP_SELECTABLE, false);

         string tooltip = "RS Line " + g_drawnBoxes[b].tfTag + (targetIsHigh ? " Low" : " High") +
                          "\nPrice: " + DoubleToString(linePrice, _Digits) +
                          "\nStart: " + TimeToString(startTime);
         ObjectSetString(0, lineName, OBJPROP_TOOLTIP, tooltip);

         if(InpOriginLabelStyle != LABEL_TOOLTIP)
         {
            string lblName = lineName + "_LBL";
            string lblText = "RS " + g_drawnBoxes[b].tfTag;
            
            if(ObjectFind(0, lblName) >= 0) ObjectDelete(0, lblName);
            
            double posRatio = 0.50;
            if(g_drawnBoxes[b].tf == PERIOD_H1)  posRatio = 0.25;
            if(g_drawnBoxes[b].tf == PERIOD_M15) posRatio = 0.45;
            if(g_drawnBoxes[b].tf == PERIOD_M5)  posRatio = 0.65;
            if(g_drawnBoxes[b].tf == PERIOD_M1)  posRatio = 0.85;

            datetime lblTime = (datetime)(startTime + (endTime - startTime) * posRatio);
            ObjectCreate(0, lblName, OBJ_TEXT, 0, lblTime, linePrice);
            ObjectSetString(0, lblName, OBJPROP_TEXT, lblText);
            ObjectSetInteger(0, lblName, OBJPROP_COLOR, lineColor);
            ObjectSetInteger(0, lblName, OBJPROP_FONTSIZE, 8);
            ObjectSetInteger(0, lblName, OBJPROP_ANCHOR, (targetIsHigh ? ANCHOR_LOWER : ANCHOR_UPPER));
            ObjectSetInteger(0, lblName, OBJPROP_SELECTABLE, false);
         }
      }

      // هایلایت و ثبت تگ RS برای گره در لحظه شکست یا اولین گره بعد از شکست خط
      if(InpHighlightBreakoutFlags && breakIdx < ratesTotal - 1)
      {
         int matchedBoxIdx = -1;

         // حالت ۱: اگر شکست واقعاً داخل گره رخ داده باشد
         for(int ob = 0; ob < g_boxCount; ob++)
         {
            if(g_drawnBoxes[ob].t1 >= targetTime - 60)
            {
               if(endTime >= g_drawnBoxes[ob].t1 && endTime <= g_drawnBoxes[ob].t2)
               {
                  if(linePrice >= g_drawnBoxes[ob].bottom && linePrice <= g_drawnBoxes[ob].top)
                  {
                     matchedBoxIdx = ob;
                     break;
                  }
               }
            }
         }

         // حالت ۲: اولین گره بعدی بعد از زمان شکست
         if(matchedBoxIdx < 0)
         {
            datetime minNextTime = 0;
            for(int ob = 0; ob < g_boxCount; ob++)
            {
               if(g_drawnBoxes[ob].t1 >= endTime)
               {
                  if(matchedBoxIdx < 0 || g_drawnBoxes[ob].t1 < minNextTime)
                  {
                     minNextTime = g_drawnBoxes[ob].t1;
                     matchedBoxIdx = ob;
                  }
               }
            }
         }

         if(matchedBoxIdx >= 0)
         {
            g_drawnBoxes[matchedBoxIdx].isBOFlag = true;
            g_drawnBoxes[matchedBoxIdx].isRSBull = !targetIsHigh;
            if(endTime > g_drawnBoxes[matchedBoxIdx].confirmationTime)
               g_drawnBoxes[matchedBoxIdx].confirmationTime = endTime;

            bool alreadyTagged = false;
            for(int t = 0; t < ArraySize(g_drawnBoxes[matchedBoxIdx].rsTags); t++)
            {
               if(g_drawnBoxes[matchedBoxIdx].rsTags[t] == "RS") { alreadyTagged = true; break; }
            }
            if(!alreadyTagged)
            {
               int tagLen = ArraySize(g_drawnBoxes[matchedBoxIdx].rsTags);
               ArrayResize(g_drawnBoxes[matchedBoxIdx].rsTags, tagLen + 1);
               g_drawnBoxes[matchedBoxIdx].rsTags[tagLen] = "RS";
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Process and Tag First Post-IP Nodes as OInner                    |
//+------------------------------------------------------------------+
void ProcessOInnerBoxes()
{
   for(int k = 0; k < g_indepCount; k++)
   {
      if(!g_indepPivots[k].hasIP) continue;

      datetime pivotTime = g_indepPivots[k].time;
      bool isHigh        = g_indepPivots[k].isHigh;

      for(int t = 0; t < ArraySize(g_indepPivots[k].tfTags); t++)
      {
         string tfStr = g_indepPivots[k].tfTags[t];
         
         // پیدا کردن زمان پیووت بعدی در این تایم‌فریم تا باکس‌های بعد از آن به اشتباه به این پیووت وصل نشوند
         datetime nextPivotTime = 0;
         for(int n = 0; n < g_indepCount; n++)
         {
            if(!g_indepPivots[n].hasIP) continue;
            if(g_indepPivots[n].time > pivotTime)
            {
               for(int nt = 0; nt < ArraySize(g_indepPivots[n].tfTags); nt++)
               {
                  if(g_indepPivots[n].tfTags[nt] == tfStr)
                  {
                     if(nextPivotTime == 0 || g_indepPivots[n].time < nextPivotTime)
                        nextPivotTime = g_indepPivots[n].time;
                  }
               }
            }
         }

         int firstBoxIdx = -1;
         datetime minBoxTime = 0;
         for(int ob = 0; ob < g_boxCount; ob++)
         {
            if(g_drawnBoxes[ob].top <= 0) continue;
            if(g_drawnBoxes[ob].tfTag != tfStr) continue;

            // قانون قطعی پرایس‌اکشن:
            // سقف مستقل فقط با گره نزولی (که از کف شکسته: !isBullish) جفت می‌شود
            // کف مستقل فقط با گره صعودی (که از سقف شکسته: isBullish) جفت می‌شود
            if(isHigh && g_drawnBoxes[ob].isBullish) continue;
            if(!isHigh && !g_drawnBoxes[ob].isBullish) continue;

            // باکسی که قبلاً او‌اینر پیووت دیگری شده بازنویسی نشود
            if(g_drawnBoxes[ob].isOInner) continue;

            // باکس باید بعد از این پیووت باشد
            if(g_drawnBoxes[ob].t1 < pivotTime - 60) continue;

            // و باکس حتما باید قبل از پیووت بعدی باشد (نباید پیووت دیگری بین آن‌ها بیفتد)
            if(nextPivotTime > 0 && g_drawnBoxes[ob].t1 >= nextPivotTime) continue;

            if(firstBoxIdx < 0 || g_drawnBoxes[ob].t1 < minBoxTime)
            {
               minBoxTime = g_drawnBoxes[ob].t1;
               firstBoxIdx = ob;
            }
         }

         if(firstBoxIdx >= 0)
         {
            g_drawnBoxes[firstBoxIdx].isOInner = true;
            // قانون اصیل پرایس‌اکشن:
            // گره مشتق‌شده از سقف (High) ذاتاً نزولی و بیریش است (isHigh => isOInnerBull = false => OInner-BE)
            // گره مشتق‌شده از کف (Low) ذاتاً صعودی و بولیش است (!isHigh => isOInnerBull = true => OInner-BU)
            g_drawnBoxes[firstBoxIdx].isOInnerBull = !isHigh;
            g_drawnBoxes[firstBoxIdx].isBullish    = !isHigh;

            datetime ipConfirm = g_indepPivots[k].time + PeriodSeconds(g_drawnBoxes[firstBoxIdx].tf) * InpSwingBars;
            if(ipConfirm > g_drawnBoxes[firstBoxIdx].confirmationTime)
               g_drawnBoxes[firstBoxIdx].confirmationTime = ipConfirm;

            bool alreadyTagged = false;
            for(int tg = 0; tg < ArraySize(g_drawnBoxes[firstBoxIdx].rsTags); tg++)
            {
               if(g_drawnBoxes[firstBoxIdx].rsTags[tg] == "OInner") { alreadyTagged = true; break; }
            }
            if(!alreadyTagged)
            {
               int tagLen = ArraySize(g_drawnBoxes[firstBoxIdx].rsTags);
               ArrayResize(g_drawnBoxes[firstBoxIdx].rsTags, tagLen + 1);
               g_drawnBoxes[firstBoxIdx].rsTags[tagLen] = "OInner";
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Universal Box Swap System (S-Prefix Breakout & Reaction Flags)   |
//+------------------------------------------------------------------+
void ProcessUniversalSwapLines(const datetime &chartTime[], const double &chartHigh[], const double &chartLow[], int ratesTotal)
{
   if(!InpEnableSwapLines) return;

   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;
   int initialBoxCount = g_boxCount;
   for(int b = 0; b < initialBoxCount; b++)
   {
      if(g_drawnBoxes[b].top <= 0) continue;
      bool isBull = g_drawnBoxes[b].isBullish;
      if(g_drawnBoxes[b].isSwap)        isBull = g_drawnBoxes[b].isSwapBull;
      else if(g_drawnBoxes[b].isOInner) isBull = g_drawnBoxes[b].isOInnerBull;
      else if(g_drawnBoxes[b].isBOFlag) isBull = g_drawnBoxes[b].isRSBull;
      else if(g_drawnBoxes[b].isPreIP)  isBull = g_drawnBoxes[b].isLSBull;
      datetime startTime = g_drawnBoxes[b].t2;
      int startSearchIdx = FindBarIndex(chartTime, ratesTotal, g_drawnBoxes[b].t2);
      if(startSearchIdx < 0) startSearchIdx = FindBarIndex(chartTime, ratesTotal, startTime);
      if(startSearchIdx < 0) startSearchIdx = 0;

      // قانون اصیل پرایس‌اکشن:
      // باکس صعودی حمایت است و به محض شکست کف (bottom) باطل و قطع می‌شود.
      // باکس نزولی مقاومت است و به محض شکست سقف (top) باطل و قطع می‌شود.
      double breakPrice = isBull ? g_drawnBoxes[b].bottom : g_drawnBoxes[b].top;

      bool isBroken = false;
      int breakIdx = ratesTotal - 1;
      for(int k = startSearchIdx + 1; k < ratesTotal; k++)
      {
         if(isBull)
         {
            if(chartLow[k] < breakPrice)
            {
               isBroken = true;
               breakIdx = k;
               break;
            }
         }
         else
         {
            if(chartHigh[k] > breakPrice)
            {
               isBroken = true;
               breakIdx = k;
               break;
            }
         }
      }

      datetime liveTime = (ratesTotal > 0) ? chartTime[ratesTotal - 1] : 0;
      datetime endTime = isBroken ? chartTime[breakIdx] : liveTime;
      if(endTime <= g_drawnBoxes[b].t1 && ratesTotal > 0) endTime = liveTime;

      // امتداد باکس دقیقا تا لحظه شکست سطح (و توقف کامل در کندل شکست)
      g_drawnBoxes[b].t2 = endTime;

      string srcRole = "Flag";
      for(int tg = 0; tg < ArraySize(g_drawnBoxes[b].rsTags); tg++)
      {
         if(g_drawnBoxes[b].rsTags[tg] == "OInner") { srcRole = "OInner"; break; }
         if(g_drawnBoxes[b].rsTags[tg] == "RS")     { srcRole = "RS";     break; }
         if(g_drawnBoxes[b].rsTags[tg] == "LS")     { srcRole = "LS";     break; }
      }

      if(isBroken && breakIdx < ratesTotal - 1)
      {
         int matchedBoxIdx = -1;
         for(int ob = 0; ob < g_boxCount; ob++)
         {
            if(ob == b) continue;
            if(g_drawnBoxes[ob].top <= 0) continue;
            if(g_drawnBoxes[ob].t1 >= startTime &&
               endTime >= g_drawnBoxes[ob].t1 &&
               endTime <= g_drawnBoxes[ob].t2 + PeriodSeconds(g_drawnBoxes[ob].tf) * 5)
            {
               double tolerance = MathMax(pipSize * 2.0, (g_drawnBoxes[ob].top - g_drawnBoxes[ob].bottom) * 0.50);
               if(breakPrice >= (g_drawnBoxes[ob].bottom - tolerance) && breakPrice <= (g_drawnBoxes[ob].top + tolerance))
               {
                  matchedBoxIdx = ob;
                  break;
               }
            }
         }

         if(matchedBoxIdx >= 0)
         {
            g_drawnBoxes[matchedBoxIdx].isSwap = true;
            g_drawnBoxes[matchedBoxIdx].isSwapBull = !isBull;
            g_drawnBoxes[matchedBoxIdx].swapSourceRole = srcRole;
            if(endTime > g_drawnBoxes[matchedBoxIdx].confirmationTime)
               g_drawnBoxes[matchedBoxIdx].confirmationTime = endTime;

            string sTag = "S-" + srcRole;
            bool alreadyTagged = false;
            for(int tg = 0; tg < ArraySize(g_drawnBoxes[matchedBoxIdx].rsTags); tg++)
            {
               if(g_drawnBoxes[matchedBoxIdx].rsTags[tg] == sTag) { alreadyTagged = true; break; }
            }
            if(!alreadyTagged)
            {
               int tagLen = ArraySize(g_drawnBoxes[matchedBoxIdx].rsTags);
               ArrayResize(g_drawnBoxes[matchedBoxIdx].rsTags, tagLen + 1);
               g_drawnBoxes[matchedBoxIdx].rsTags[tagLen] = sTag;
            }
         }
      }
   }
}
