//+------------------------------------------------------------------+
//| Flag_TradeTypes.mqh                                              |
//| FlagPro Shared Trade Simulation Types, Spreads & Palette Helpers |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""

//+------------------------------------------------------------------+
//| تطبیق تایم‌فریم پیووت با باکس مربوطه                              |
//+------------------------------------------------------------------+
bool IsPivotTimeframeMatch(int pivotIdx, const string boxTfTag)
{
   if(pivotIdx < 0 || pivotIdx >= g_indepCount) return false;
   for(int t = 0; t < ArraySize(g_indepPivots[pivotIdx].tfTags); t++)
   {
      if(g_indepPivots[pivotIdx].tfTags[t] == boxTfTag)
         return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| دریافت اسپرد دقیق کندل با استفاده از دیتای هیستوری بروکر          |
//+------------------------------------------------------------------+
double GetBarSpread(int k, const int &chartSpread[], double fallbackSpread)
{
   if(k >= 0 && k < ArraySize(chartSpread) && chartSpread[k] > 0)
      return (double)chartSpread[k] * _Point;
   return fallbackSpread;
}

//+------------------------------------------------------------------+
//| پالت رنگی معاملات جهت تفکیک کامل معاملات همزمان روی چارت         |
//| فاقد هرگونه رنگ سبز و قرمز (بدون تداخل با خطوط تستر متاتریدر)   |
//+------------------------------------------------------------------+
color GetTradeSetupColor(int tradeIndex)
{
   static const color s_tradePalette[12] = {
      clrDodgerBlue,       // ۱. آبی آسمانی زنده (C'30,144,255')
      clrDarkOrange,       // ۲. نارنجی تیره (C'255,140,0')
      clrMagenta,          // ۳. سرخابی (C'255,0,255')
      clrCyan,             // ۴. فیروزه‌ای روشن (C'0,255,255')
      clrGold,             // ۵. طلایی (C'255,215,0')
      clrDeepPink,         // ۶. صورتی پررنگ (C'255,20,147')
      clrMediumSlateBlue,  // ۷. آبی بنفش متالیک (C'123,104,238')
      clrSandyBrown,       // ۸. کهربایی شنی (C'244,164,96')
      clrTurquoise,        // ۹. فیروزه‌ای دریایی (C'64,224,208')
      clrCoral,            // ۱۰. مرجانی (C'255,127,80')
      clrViolet,           // ۱۱. بنفش روشن (C'238,130,238')
      clrCornflowerBlue    // ۱۲. آبی متالیک (C'100,149,237')
   };
   return s_tradePalette[MathAbs(tradeIndex) % 12];
}

//+------------------------------------------------------------------+
//| محاسبه مستقل و ایمن ATR تاریخی بدون ایجاد هندل یا نشتی حافظه     |
//+------------------------------------------------------------------+
double GetCalculatedATR(const string symbol, ENUM_TIMEFRAMES tf, int period, datetime barTime)
{
   if(period <= 0) period = 14;
   if(tf == PERIOD_CURRENT || tf == 0) tf = _Period;

   MqlRates rates[];
   ArraySetAsSeries(rates, true);

   int copied = 0;
   if(barTime > 0)
      copied = CopyRates(symbol, tf, barTime, period + 2, rates);

   if(copied < period + 1)
      copied = CopyRates(symbol, tf, 0, period + 2, rates);

   if(copied < 2) return 0.0;

   double sumTR = 0.0;
   int count = 0;
   for(int i = 0; i < period && (i + 1) < copied; i++)
   {
      double h = rates[i].high;
      double l = rates[i].low;
      double prevClose = rates[i + 1].close;
      double tr = MathMax(h - l, MathMax(MathAbs(h - prevClose), MathAbs(l - prevClose)));
      sumTR += tr;
      count++;
   }

   if(count > 0)
      return (sumTR / (double)count);

   return 0.0;
}

//+------------------------------------------------------------------+
//| موتور جامع محاسبه حد ضرر (Multi-Mode Stop Loss Engine)          |
//+------------------------------------------------------------------+
double CalculateSetupStopLoss(bool isBuy,
                             double entryPrice,
                             double patternHigh,
                             double patternLow,
                             double boxHeight,
                             datetime evalTime,
                             ENUM_TIMEFRAMES boxTf,
                             double pipSize = 0.0)
{
   if(pipSize <= 0.0)
      pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;

   ENUM_SL_MODE    slMode        = ActiveSLMode();
   double          fixedPips     = ActiveSLFixedPips();
   ENUM_TIMEFRAMES atrTf         = ActiveSLATRTimeframe();
   int             atrPeriod     = ActiveSLATRPeriod();
   double          atrMultiplier = ActiveSLATRMultiplier();
   double          boxPercent    = ActiveSLBoxPercent();
   double          minPips       = ActiveSLMinPips();
   double          maxPips       = ActiveSLMaxPips();

   double slPrice = 0.0;

   switch(slMode)
   {
      case SL_MODE_FIXED_PIPS:
      {
         double buffer = fixedPips * pipSize;
         slPrice = isBuy ? (patternLow - buffer) : (patternHigh + buffer);
         break;
      }

      case SL_MODE_ATR_BUFFER:
      {
         ENUM_TIMEFRAMES calcTf = (atrTf == PERIOD_CURRENT || atrTf == 0) ? boxTf : atrTf;
         if(calcTf == PERIOD_CURRENT || calcTf == 0) calcTf = _Period;
         double atr = GetCalculatedATR(_Symbol, calcTf, atrPeriod, evalTime);
         double buffer = (atr > 0.0) ? (atr * atrMultiplier) : (fixedPips * pipSize);
         slPrice = isBuy ? (patternLow - buffer) : (patternHigh + buffer);
         break;
      }

      case SL_MODE_PURE_ATR:
      {
         ENUM_TIMEFRAMES calcTf = (atrTf == PERIOD_CURRENT || atrTf == 0) ? boxTf : atrTf;
         if(calcTf == PERIOD_CURRENT || calcTf == 0) calcTf = _Period;
         double atr = GetCalculatedATR(_Symbol, calcTf, atrPeriod, evalTime);
         double buffer = (atr > 0.0) ? (atr * atrMultiplier) : (fixedPips * pipSize);
         slPrice = isBuy ? (entryPrice - buffer) : (entryPrice + buffer);
         break;
      }

      case SL_MODE_BOX_PERCENT:
      {
         double bHeight = (boxHeight > 0.0) ? boxHeight : (patternHigh - patternLow);
         if(bHeight <= 0.0) bHeight = fixedPips * pipSize;
         double buffer = bHeight * boxPercent;
         slPrice = isBuy ? (patternLow - buffer) : (patternHigh + buffer);
         break;
      }

      default:
      {
         double buffer = fixedPips * pipSize;
         slPrice = isBuy ? (patternLow - buffer) : (patternHigh + buffer);
         break;
      }
   }

   // 🛡️ اعمال سپرهای ایمنی هوشمند (Safety Clamping)
   double riskDist = MathAbs(entryPrice - slPrice);
   double riskPips = (pipSize > 0.0) ? (riskDist / pipSize) : 0.0;

   // ۱. حداقل مجاز فاصله حد ضرر (Min SL)
   if(minPips > 0.0 && riskPips < minPips)
   {
      slPrice = isBuy ? (entryPrice - minPips * pipSize) : (entryPrice + minPips * pipSize);
   }

   // ۲. حداکثر مجاز فاصله حد ضرر (Max SL)
   if(maxPips > 0.0 && riskPips > maxPips)
   {
      slPrice = isBuy ? (entryPrice - maxPips * pipSize) : (entryPrice + maxPips * pipSize);
   }

   // حداقل مطلق فاصله به پوینت جهت پیشگیری از خطای اردر
   double minSafeDist = _Point * 2.0;
   if(MathAbs(entryPrice - slPrice) < minSafeDist)
   {
      slPrice = isBuy ? (entryPrice - minSafeDist) : (entryPrice + minSafeDist);
   }

   return NormalizeDouble(slPrice, _Digits);
}

