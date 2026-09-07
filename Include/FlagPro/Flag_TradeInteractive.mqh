//+------------------------------------------------------------------+
//| Flag_TradeInteractive.mqh                                        |
//| Interactive Clicked Box Trade Simulation & Visualization Engine   |
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
   double bufferPips = InpRSPipBuffer * pipSize;

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
         if(k - confirmIdx > 30)
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

         // مهلت بازگشت پولبک بر مبنای پارامتر ورودی InpLimitExpirationBars
         if(k - departedBar > InpLimitExpirationBars)
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
      string noTradeMsg = StringFormat(
         "═══════════════════════════════════════════════════\n"
         "📦 باکس %s [%s]\n"
         "⚠️ سیگنال ورود به معامله صادر نشد!\n"
         "📋 وضعیت: %s\n"
         "═══════════════════════════════════════════════════",
         g_drawnBoxes[boxIdx].tfTag, role,
         (cancelReasonStr != "" ? cancelReasonStr : "عدم پولبک و ورود قیمت به باکس"));
      Comment(noTradeMsg);
      Print(noTradeMsg);
      return;
   }
   else
   {
      // به‌روزرسانی نهایی حد ضرر و ریسک بر مبنای نوک واقعی تمام شدوها از ابتدا تا دقیقاً لحظه ورود (entryBarIdx)
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
            // بررسی برخورد به تارگت‌های سود
            for(int tp = maxHit; tp < 4; tp++)
            {
               if(chartHigh[k] >= tps[tp])
               {
                  maxHit = tp + 1;
                  hitTime = chartTime[k];
                  if(tpHitTime[tp] == 0) tpHitTime[tp] = chartTime[k];
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
            // بررسی برخورد به تارگت‌های سود (با احتساب اسپرد خرید جهت تسویه)
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

            // بررسی حد ضرر (با احتساب اسپرد خرید جهت تسویه)
            if((chartHigh[k] + barSpread) >= slPrice)
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



   // بک‌گراند ملایم معامله (فقط در صورت روشن بودن InpShowTradeShading - رنگ‌های آبی و کهربایی بدون تداخل با قرمز/سبز تستر)
   if(InpShowTradeShading)
   {
      double tpTop = isBull ? tps[3] : entryPrice;
      double tpBtm = isBull ? entryPrice : tps[3];
      string profitZone = pfx + "PROFIT_BG";
      ObjectCreate(0, profitZone, OBJ_RECTANGLE, 0, t1, tpTop, t2, tpBtm);
      ObjectSetInteger(0, profitZone, OBJPROP_COLOR, C'15,35,55'); // آبی دودی ملایم
      ObjectSetInteger(0, profitZone, OBJPROP_FILL, true);
      ObjectSetInteger(0, profitZone, OBJPROP_BACK, true);
      ObjectSetInteger(0, profitZone, OBJPROP_SELECTABLE, false);

      double slTop = isBull ? entryPrice : slPrice;
      double slBtm = isBull ? slPrice : entryPrice;
      string lossZone = pfx + "LOSS_BG";
      ObjectCreate(0, lossZone, OBJ_RECTANGLE, 0, t1, slTop, t2, slBtm);
      ObjectSetInteger(0, lossZone, OBJPROP_COLOR, C'55,35,15'); // کهربایی نارنجی ملایم
      ObjectSetInteger(0, lossZone, OBJPROP_FILL, true);
      ObjectSetInteger(0, lossZone, OBJPROP_BACK, true);
      ObjectSetInteger(0, lossZone, OBJPROP_SELECTABLE, false);
   }
   else
   {
      string profitZone = pfx + "PROFIT_BG";
      string lossZone   = pfx + "LOSS_BG";
      if(ObjectFind(0, profitZone) >= 0) ObjectDelete(0, profitZone);
      if(ObjectFind(0, lossZone) >= 0)   ObjectDelete(0, lossZone);
   }

   // انتخاب پالت رنگی معامله (در صورت روشن بودن InpUniqueTradeColors هر معامله رنگ مجزا و اختصاصی دارد)
   color tradeClr = InpUniqueTradeColors ? GetTradeSetupColor(boxIdx) : InpTradeTPColor;
   color entryClr = InpUniqueTradeColors ? tradeClr : InpTradeEntryColor;
   color slClr    = InpUniqueTradeColors ? tradeClr : InpTradeSLColor;
   color tpClr    = InpUniqueTradeColors ? tradeClr : InpTradeTPColor;

   // ۱. خط نقطه ورود (خط‌چین)
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

   // ۲. خط حد ضرر متمایز از قرمز تستر (نقطه‌چین)
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

   // ۳. خطوط تارگت‌های ۴ گانه (فقط تا جایی که تاچ شده‌اند امتداد دارند)
   for(int tp = 0; tp < 4; tp++)
   {
      // خط TP فقط تا جایی امتداد می‌یابد که تاچ شده است و بیشتر ادامه پیدا نمی‌کند
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
   else if(hitTP == 4)   { resText = "WIN 1:4 🎯"; resColor = InpUniqueTradeColors ? tradeClr : InpTradeTPColor; }
   else if(hitTP == 3)   { resText = "WIN 1:3 🚀"; resColor = InpUniqueTradeColors ? tradeClr : InpTradeTPColor; }
   else if(hitTP == 2)   { resText = "WIN 1:2 ✨"; resColor = InpUniqueTradeColors ? tradeClr : InpTradeTPColor; }
   else if(hitTP == 1)   { resText = "WIN 1:1 👍"; resColor = InpUniqueTradeColors ? tradeClr : InpTradeTPColor; }
   else if(isClosed)     { resText = "STOP LOSS ❌"; resColor = InpUniqueTradeColors ? tradeClr : InpTradeSLColor; }
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

   string tradeType = isBull ? "BUY 🔵" : "SELL 🟠";
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

