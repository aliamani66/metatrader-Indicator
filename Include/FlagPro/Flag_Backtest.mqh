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
   double chartHigh[], chartLow[], chartClose[];
   ArraySetAsSeries(chartTime, false);
   ArraySetAsSeries(chartHigh, false);
   ArraySetAsSeries(chartLow, false);
   ArraySetAsSeries(chartClose, false);

   int copied = CopyTime(_Symbol, _Period, 0, 250000, chartTime);
   CopyHigh(_Symbol, _Period, 0, 250000, chartHigh);
   CopyLow(_Symbol, _Period, 0, 250000, chartLow);
   CopyClose(_Symbol, _Period, 0, 250000, chartClose);
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
      isBull = g_drawnBoxes[boxIdx].isOInnerBull; // جهت ترید حتماً جهت خود گره OInner است

      double   pivotP = 0;
      datetime closestPivotTime = 0;
      for(int k = 0; k < g_indepCount; k++)
      {
         if(!g_indepPivots[k].hasIP) continue;
         if(g_indepPivots[k].time <= g_drawnBoxes[boxIdx].t1)
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

      if(pivotP == 0)
      {
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

   datetime confirmTime = g_drawnBoxes[boxIdx].confirmationTime;
   if(confirmTime <= 0) confirmTime = g_drawnBoxes[boxIdx].formationTime + PeriodSeconds(g_drawnBoxes[boxIdx].tf) * InpSwingBars;
   if(confirmTime <= 0) confirmTime = g_drawnBoxes[boxIdx].t1;

   int confirmIdx = FindBarIndex(chartTime, copied, confirmTime);
   if(confirmIdx < 0) confirmIdx = 0;

   double boxHeight = MathAbs(g_drawnBoxes[boxIdx].top - g_drawnBoxes[boxIdx].bottom);
   double minDeparturePrice = isBull ? (entryPrice + boxHeight * 0.3) : (entryPrice - boxHeight * 0.3);

   bool isEntered = false;
   int  entryBarIdx = -1;
   datetime entryTime = 0;

   // جستجوی پولبک برای ورود به معامله مطابق با لایو بازار:
   // ۱. شروع جستجو فقط از زمان تایید قطعی استراکچر در لایو (confirmTime)
   // ۲. قیمت باید ابتدا با کلوز کندل فاصله بگیرد (departedBar)
   // ۳. ورود منحصراً در کندل‌های بعدی روی پولبک و لمس سطح ورود (k > departedBar)
   int departedBar = -1;
   datetime maxBoxTime = g_drawnBoxes[boxIdx].t2;
   if(maxBoxTime <= confirmTime) 
      maxBoxTime = confirmTime + PeriodSeconds(g_drawnBoxes[boxIdx].tf) * 40;

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

      // ابطال ۲: برخورد قیمت به حد ضرر در هر زمان (حتی قبل از پرتاب) ستاپ را فوراً لغو می‌کند
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
         if(chartHigh[k] >= slPrice)
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
         if(k - confirmIdx > 30)
         {
            cancelBarIdx = k;
            cancelReasonStr = "NO BREAKOUT ⏱ (عدم خروج قیمت از گره)";
            break;
         }
      }
      else // ورود منحصراً روی کندل‌های بعد از پرتاب اولیه (پولبک واقعی)
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

         // مهلت بازگشت پولبک حداکثر ۶۰ کندل بعد از پرتاب
         if(k - departedBar > 60)
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

   if(!isEntered)
   {
      entryTime = confirmTime;
      if(cancelBarIdx >= 0)
         exitTime = chartTime[cancelBarIdx];
      else
         exitTime = chartTime[copied - 1];
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

   // ۳. خط عمودی شفاف زمان تایید آلارم لایو (Confirmation Time Marker)
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

   // --- بک‌گراند رنگی ملایم و شفاف برای ناحیه سود (سبز) و ناحیه ریسک (قرمز) مشابه تریدینگ‌ویو ---
   // ۱. ناحیه سود (Profit Zone: بین نقطه ورود و تارگت‌ها)
   double tpTop = isBull ? tps[3] : entryPrice;
   double tpBtm = isBull ? entryPrice : tps[3];
   string profitZone = pfx + "PROFIT_BG";
   ObjectCreate(0, profitZone, OBJ_RECTANGLE, 0, t1, tpTop, t2, tpBtm);
   ObjectSetInteger(0, profitZone, OBJPROP_COLOR, C'6,36,20'); // سبز ملایم زمردی در پس‌زمینه
   ObjectSetInteger(0, profitZone, OBJPROP_FILL, true);
   ObjectSetInteger(0, profitZone, OBJPROP_BACK, true); // رسم در پس‌زمینه (پشت کندل‌ها)
   ObjectSetInteger(0, profitZone, OBJPROP_SELECTABLE, false);

   // ۲. ناحیه ریسک (Risk Zone: بین نقطه ورود و حد ضرر)
   double slTop = isBull ? entryPrice : slPrice;
   double slBtm = isBull ? slPrice : entryPrice;
   string lossZone = pfx + "LOSS_BG";
   ObjectCreate(0, lossZone, OBJ_RECTANGLE, 0, t1, slTop, t2, slBtm);
   ObjectSetInteger(0, lossZone, OBJPROP_COLOR, C'38,10,14'); // زرشکی ملایم در پس‌زمینه
   ObjectSetInteger(0, lossZone, OBJPROP_FILL, true);
   ObjectSetInteger(0, lossZone, OBJPROP_BACK, true); // رسم در پس‌زمینه (پشت کندل‌ها)
   ObjectSetInteger(0, lossZone, OBJPROP_SELECTABLE, false);

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
   if(!isEntered)
   {
      if(cancelReasonStr != "")
      {
         resText = cancelReasonStr;
         resColor = (StringFind(cancelReasonStr, "CANCELLED") >= 0) ? clrSalmon : clrSilver;
      }
      else
      {
         resText = "PENDING ⏳ (در انتظار پولبک لایو)";
         resColor = clrGold;
      }
   }
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
//| Render Automatic Trade Setups for all Valid & Entered Boxes     |
//+------------------------------------------------------------------+
void RenderAutoTradeSetups(const datetime &chartTime[], const double &chartHigh[], const double &chartLow[], const double &chartClose[], int ratesTotal)
{
   ObjectsDeleteAll(0, FP_PREFIX + "AUTO_TR_");
   if(!InpAutoDrawTrades || ratesTotal < 10) return;

   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;
   double bufferPips = InpRSPipBuffer * pipSize;

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
      double slPrice    = 0;

      if(isOI)
      {
         isBull = g_drawnBoxes[b].isOInnerBull;
         double   pivotP = 0;
         datetime closestPivotTime = 0;
         for(int k = 0; k < g_indepCount; k++)
         {
            if(!g_indepPivots[k].hasIP) continue;
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
         if(pivotP == 0) pivotP = isBull ? g_drawnBoxes[b].bottom : g_drawnBoxes[b].top;

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

      // فیلتر هوشمند ضد استاپ: اگر ستاپ فیلتر باشد، گرافیک معامله رسم نمی‌شود
      if(IsSetupFilteredOut(role, g_drawnBoxes[b].t1, risk / _Point))
         continue;

      datetime confirmTime = g_drawnBoxes[b].confirmationTime;
      if(confirmTime <= 0) confirmTime = g_drawnBoxes[b].formationTime + PeriodSeconds(g_drawnBoxes[b].tf) * InpSwingBars;
      if(confirmTime <= 0) confirmTime = g_drawnBoxes[b].t1;

      int confirmIdx = FindBarIndex(chartTime, ratesTotal, confirmTime);
      if(confirmIdx < 0) confirmIdx = 0;

      double boxHeight = MathAbs(g_drawnBoxes[b].top - g_drawnBoxes[b].bottom);
      double minDeparturePrice = isBull ? (entryPrice + boxHeight * 0.3) : (entryPrice - boxHeight * 0.3);

      bool isEntered = false;
      int  entryBarIdx = -1;
      datetime entryTime = 0;
      int departedBar = -1;
      datetime maxBoxTime = g_drawnBoxes[b].t2;
      if(maxBoxTime <= confirmTime)
         maxBoxTime = confirmTime + PeriodSeconds(g_drawnBoxes[b].tf) * 40;

      for(int k = confirmIdx; k < ratesTotal; k++)
      {
         if(chartTime[k] > maxBoxTime) break;

         // اگر قبل از ورود به حد ضرر بخورد، ستاپ لغو می‌شود
         if(isBull && chartLow[k] <= slPrice) break;
         if(!isBull && chartHigh[k] >= slPrice) break;

         if(departedBar < 0)
         {
            if(isBull && chartClose[k] >= minDeparturePrice) departedBar = k;
            else if(!isBull && chartClose[k] <= minDeparturePrice) departedBar = k;
            if(k - confirmIdx > 30) break;
         }
         else
         {
            if(isBull && chartLow[k] <= entryPrice && chartHigh[k] >= entryPrice)
            {
               isEntered = true;
               entryBarIdx = k;
               entryTime = chartTime[k];
               break;
            }
            else if(!isBull && chartHigh[k] >= entryPrice && chartLow[k] <= entryPrice)
            {
               isEntered = true;
               entryBarIdx = k;
               entryTime = chartTime[k];
               break;
            }
            if(k - departedBar > 60) break;
         }
      }

      // فقط برای باکس‌هایی که معامله روی آن‌ها تایید و فعال شده گرافیک کشیده شود
      if(!isEntered)
         continue;

      // محاسبه تارگت‌ها
      double tps[4];
      for(int tp = 0; tp < 4; tp++)
      {
         if(isBull) tps[tp] = entryPrice + risk * (tp + 1);
         else       tps[tp] = entryPrice - risk * (tp + 1);
      }

      int hitTP = 0;
      bool isClosed = false;
      datetime exitTime = 0;
      datetime hitTime = 0;

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
               }
            }
            if(chartLow[k] <= slPrice)
            {
               isClosed = true;
               exitTime = (hitTP > 0) ? hitTime : chartTime[k];
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
            for(int tp = hitTP; tp < 4; tp++)
            {
               if(chartLow[k] <= tps[tp])
               {
                  hitTP = tp + 1;
                  hitTime = chartTime[k];
               }
            }
            if(chartHigh[k] >= slPrice)
            {
               isClosed = true;
               exitTime = (hitTP > 0) ? hitTime : chartTime[k];
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

      datetime t1 = entryTime;
      datetime t2 = exitTime;
      if(t2 <= t1) t2 = t1 + PeriodSeconds(_Period) * 10;

      string pfx = FP_PREFIX + "AUTO_TR_" + IntegerToString(b) + "_";

      // ۱. ناحیه سود (سبز زمردی ملایم در پس‌زمینه)
      double tpTop = isBull ? tps[3] : entryPrice;
      double tpBtm = isBull ? entryPrice : tps[3];
      string profitZone = pfx + "PROFIT_BG";
      ObjectCreate(0, profitZone, OBJ_RECTANGLE, 0, t1, tpTop, t2, tpBtm);
      ObjectSetInteger(0, profitZone, OBJPROP_COLOR, C'6,36,20');
      ObjectSetInteger(0, profitZone, OBJPROP_FILL, true);
      ObjectSetInteger(0, profitZone, OBJPROP_BACK, true);
      ObjectSetInteger(0, profitZone, OBJPROP_SELECTABLE, false);

      // ۲. ناحیه ریسک (زرشکی ملایم در پس‌زمینه)
      double slTop = isBull ? entryPrice : slPrice;
      double slBtm = isBull ? slPrice : entryPrice;
      string lossZone = pfx + "LOSS_BG";
      ObjectCreate(0, lossZone, OBJ_RECTANGLE, 0, t1, slTop, t2, slBtm);
      ObjectSetInteger(0, lossZone, OBJPROP_COLOR, C'38,10,14');
      ObjectSetInteger(0, lossZone, OBJPROP_FILL, true);
      ObjectSetInteger(0, lossZone, OBJPROP_BACK, true);
      ObjectSetInteger(0, lossZone, OBJPROP_SELECTABLE, false);

      // ۳. خط ورود سفید
      string entryLine = pfx + "ENTRY";
      ObjectCreate(0, entryLine, OBJ_TREND, 0, t1, entryPrice, t2, entryPrice);
      ObjectSetInteger(0, entryLine, OBJPROP_COLOR, clrWhite);
      ObjectSetInteger(0, entryLine, OBJPROP_WIDTH, 2);
      ObjectSetInteger(0, entryLine, OBJPROP_STYLE, STYLE_SOLID);
      ObjectSetInteger(0, entryLine, OBJPROP_RAY_RIGHT, false);
      ObjectSetInteger(0, entryLine, OBJPROP_SELECTABLE, false);

      // ۴. خط حد ضرر قرمز
      string slLine = pfx + "SL";
      ObjectCreate(0, slLine, OBJ_TREND, 0, t1, slPrice, t2, slPrice);
      ObjectSetInteger(0, slLine, OBJPROP_COLOR, clrRed);
      ObjectSetInteger(0, slLine, OBJPROP_WIDTH, 2);
      ObjectSetInteger(0, slLine, OBJPROP_STYLE, STYLE_DASH);
      ObjectSetInteger(0, slLine, OBJPROP_RAY_RIGHT, false);
      ObjectSetInteger(0, slLine, OBJPROP_SELECTABLE, false);

      // ۵. خطوط تارگت‌های سود سبز
      for(int tp = 0; tp < 4; tp++)
      {
         string tpLine = pfx + "TP" + IntegerToString(tp + 1);
         ObjectCreate(0, tpLine, OBJ_TREND, 0, t1, tps[tp], t2, tps[tp]);
         ObjectSetInteger(0, tpLine, OBJPROP_COLOR, clrLimeGreen);
         ObjectSetInteger(0, tpLine, OBJPROP_WIDTH, (hitTP >= tp + 1 ? 2 : 1));
         ObjectSetInteger(0, tpLine, OBJPROP_STYLE, (hitTP >= tp + 1 ? STYLE_SOLID : STYLE_DOT));
         ObjectSetInteger(0, tpLine, OBJPROP_RAY_RIGHT, false);
         ObjectSetInteger(0, tpLine, OBJPROP_SELECTABLE, false);
      }

      // ۶. برچسب شفاف نتیجه
      string resLbl = pfx + "RES_LBL";
      string resTxt = (hitTP > 0) ? StringFormat("🎯 TP%d (+%dR)", hitTP, hitTP) : (isClosed ? "❌ SL (-1R)" : "⏳ OPEN");
      color resClr = (hitTP > 0) ? clrLimeGreen : (isClosed ? clrTomato : clrGold);

      ObjectCreate(0, resLbl, OBJ_TEXT, 0, t2, entryPrice);
      ObjectSetString(0, resLbl, OBJPROP_TEXT, resTxt);
      ObjectSetInteger(0, resLbl, OBJPROP_COLOR, resClr);
      ObjectSetInteger(0, resLbl, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, resLbl, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(0, resLbl, OBJPROP_SELECTABLE, false);
   }
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
   double chartHigh[], chartLow[], chartClose[];
   ArraySetAsSeries(chartTime, false);
   ArraySetAsSeries(chartHigh, false);
   ArraySetAsSeries(chartLow, false);
   ArraySetAsSeries(chartClose, false);

   int barsToCopy = (InpBacktestDays > 0) ? (InpBacktestDays * 1440 * 2 + 1000) : 50000;
   int copied = CopyTime(_Symbol, _Period, 0, barsToCopy, chartTime);
   CopyHigh(_Symbol, _Period, 0, barsToCopy, chartHigh);
   CopyLow(_Symbol, _Period, 0, barsToCopy, chartLow);
   CopyClose(_Symbol, _Period, 0, barsToCopy, chartClose);
   if(copied < 10)
   {
      if(handle != INVALID_HANDLE) FileClose(handle);
      if(handleSym != INVALID_HANDLE) FileClose(handleSym);
      return;
   }

   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;
   double bufferPips = InpRSPipBuffer * pipSize;
   int exportedCount = 0;

   datetime minBacktestTime = (InpBacktestDays > 0) ? (TimeCurrent() - InpBacktestDays * 24 * 3600) : 0;
   for(int b = 0; b < g_boxCount; b++)
   {
      if(g_drawnBoxes[b].top <= 0) continue;
      if(minBacktestTime > 0 && g_drawnBoxes[b].t1 < minBacktestTime) continue;
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
         isBull = g_drawnBoxes[b].isOInnerBull; // جهت ترید حتماً جهت خود گره OInner است

         double pivotP = 0;
         datetime closestPivotTime = 0;
         for(int k = 0; k < g_indepCount; k++)
         {
            if(!g_indepPivots[k].hasIP) continue;
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

         if(pivotP == 0)
         {
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

      datetime confirmTime = g_drawnBoxes[b].confirmationTime;
      if(confirmTime <= 0) confirmTime = g_drawnBoxes[b].formationTime + PeriodSeconds(g_drawnBoxes[b].tf) * InpSwingBars;
      if(confirmTime <= 0) confirmTime = g_drawnBoxes[b].t1;

      int confirmIdx = FindBarIndex(chartTime, copied, confirmTime);
      if(confirmIdx < 0) confirmIdx = 0;

      double boxHeight = MathAbs(g_drawnBoxes[b].top - g_drawnBoxes[b].bottom);
      double minDeparturePrice = isBull ? (entryPrice + boxHeight * 0.3) : (entryPrice - boxHeight * 0.3);

      bool isEntered = false;
      int  entryBarIdx = -1;
      datetime entryTime = 0;

      // شبیه‌سازی دقیق ورود بر اساس لایو بازار:
      // ۱. تایید هویت گره در لایو (confirmTime)
      // ۲. پرتاب و کلوز کامل کندل در بیرون از محدوده (departedBar)
      // ۳. اردر لیمیت روی پولبک و ورود منحصراً در کندل‌های بعدی (k > departedBar)
      int departedBar = -1;
      datetime maxBoxTime = g_drawnBoxes[b].t2;
      if(maxBoxTime <= confirmTime) 
         maxBoxTime = confirmTime + PeriodSeconds(g_drawnBoxes[b].tf) * 40;

      for(int k = confirmIdx; k < copied; k++)
      {
         // ابطال ۱: انقضای زمانی معامله با گذشت از اعتبار باکس
         if(chartTime[k] > maxBoxTime) break;

         // ابطال ۲: برخورد قیمت به حد ضرر در هر زمان (حتی قبل از پرتاب) ستاپ را فوراً لغو می‌کند
         if(isBull)
         {
            if(chartLow[k] <= slPrice) break;
         }
         else
         {
            if(chartHigh[k] >= slPrice) break;
         }

         if(departedBar < 0)
         {
            // تایید پرتاب و کلوز کامل کندل در بیرون از باکس
            if(isBull && chartClose[k] >= minDeparturePrice) departedBar = k;
            else if(!isBull && chartClose[k] <= minDeparturePrice) departedBar = k;

            // مهلت خروج اولیه از باکس حداکثر ۳۰ کندل
            if(k - confirmIdx > 30) break;
         }
         else // ورود منحصراً روی کندل‌های بعد از پرتاب اولیه (پولبک واقعی)
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

            // مهلت بازگشت پولبک حداکثر ۶۰ کندل بعد از پرتاب
            if(k - departedBar > 60) break;
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
