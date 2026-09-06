//+------------------------------------------------------------------+
//| Flag_Pivots.mqh                                                  |
//| FlagPro Pivot Analysis, Search Helpers & Flag Validation         |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""

//+------------------------------------------------------------------+
//| Find Bar Index in non-series chartTime array (Binary Search)     |
//+------------------------------------------------------------------+
int FindBarIndex(const datetime &chartTime[], int ratesTotal, datetime t)
{
   if(ratesTotal <= 0) return -1;
   if(t <= chartTime[0]) return 0;
   if(t >= chartTime[ratesTotal - 1]) return ratesTotal - 1;

   int lo = 0, hi = ratesTotal - 1;
   while(lo < hi)
   {
      int mid = (lo + hi + 1) / 2;
      if(chartTime[mid] <= t) lo = mid;
      else hi = mid - 1;
   }
   return lo;
}

//+------------------------------------------------------------------+
//| Find Exact Candle Time on Chart matching Peak/Valley             |
//+------------------------------------------------------------------+
datetime GetExactPivotChartTime(datetime srcBarTime, ENUM_TIMEFRAMES srcTF, double price, bool isHigh,
                                const datetime &chartTime[], const double &chartHigh[], const double &chartLow[], int ratesTotal)
{
   int sec = PeriodSeconds(srcTF);
   datetime srcEndTime = srcBarTime + sec;

   int startIdx = FindBarIndex(chartTime, ratesTotal, srcBarTime);
   int endIdx   = FindBarIndex(chartTime, ratesTotal, srcEndTime);
   if(startIdx < 0) return srcBarTime;
   if(endIdx < 0) endIdx = ratesTotal - 1;

   datetime bestTime = srcBarTime;
   double bestDiff = 1e10;

   for(int k = startIdx; k <= endIdx && k < ratesTotal; k++)
   {
      double candlePrice = isHigh ? chartHigh[k] : chartLow[k];
      double diff = MathAbs(candlePrice - price);
      if(diff < bestDiff)
      {
         bestDiff = diff;
         bestTime = chartTime[k];
         if(diff < _Point * 0.5) break;
      }
   }
   return bestTime;
}

//+------------------------------------------------------------------+
//| Get distinct Line Style per Timeframe                            |
//+------------------------------------------------------------------+
ENUM_LINE_STYLE GetTFLineStyle(ENUM_TIMEFRAMES tf)
{
   switch(tf)
   {
      case PERIOD_D1:  return STYLE_DASH;       // روزانه: خط‌چین
      case PERIOD_W1:  return STYLE_DASH;       // هفتگی: خط‌چین
      case PERIOD_H4:  return STYLE_DOT;        // چهارساعته: نقطه‌چین
      case PERIOD_H1:  return STYLE_DASH;       // یک‌ساعته: خط‌چین
      case PERIOD_M15: return STYLE_DASH;       // ۱۵ دقیقه: خط‌چین
      case PERIOD_M5:  return STYLE_DOT;        // ۵ دقیقه: نقطه‌چین
      case PERIOD_M1:  return STYLE_DOT;        // ۱ دقیقه: نقطه‌چین
      default:         return STYLE_DASH;
   }
}

//+------------------------------------------------------------------+
//| Helper: Friendly Timeframe Name                                  |
//+------------------------------------------------------------------+
string TFName(ENUM_TIMEFRAMES tf)
{
   string s = EnumToString(tf);
   StringReplace(s, "PERIOD_", "");
   return s;
}

//+------------------------------------------------------------------+
//| Evaluate Corrective Pullback Flag Swings                         |
//+------------------------------------------------------------------+
bool IsValidFlagLeg(int idx, const SPivot &pivots[], int totalCount)
{
   if(idx < 0 || idx >= totalCount - 1) return false;

   SPivot p1 = pivots[idx];     // شروع یال جاری
   SPivot p2 = pivots[idx + 1]; // پایان یال جاری

   // استخراج سقف و کف قبلی منحصراً از امواج گذشته (بدون نگاه به آینده)
   double prevH = -1, prevL = -1;
   for(int j = idx - 1; j >= 0; j--)
   {
      if(pivots[j].isHigh && prevH < 0) prevH = pivots[j].price;
      if(!pivots[j].isHigh && prevL < 0) prevL = pivots[j].price;
      if(prevH > 0 && prevL > 0) break;
   }

   // ۱. اصلاح نزولی در روند صعودی: Drop (High -> Low)
   // شرط بقای ساختار صعودی: کف اصلاح (p2) باید بالاتر از کف قبلی (prevL) باشد
   if(p1.isHigh && !p2.isHigh)
   {
      if(prevL > 0 && p2.price > prevL)
         return true;
   }
   // ۲. اصلاح صعودی در روند نزولی: Rally (Low -> High)
   // شرط بقای ساختار نزولی: سقف اصلاح (p2) باید پایین‌تر از سقف قبلی (prevH) باشد
   else if(!p1.isHigh && p2.isHigh)
   {
      if(prevH > 0 && p2.price < prevH)
         return true;
   }

   return false;
}
