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

   // Extract previous High and previous Low before idx
   double prevH = -1, prevL = -1;
   for(int j = idx - 1; j >= 0; j--)
   {
      if(pivots[j].isHigh && prevH < 0) prevH = pivots[j].price;
      if(!pivots[j].isHigh && prevL < 0) prevL = pivots[j].price;
      if(prevH > 0 && prevL > 0) break;
   }

   // Extract next High and next Low after idx+1
   double nextH = -1, nextL = -1;
   for(int j = idx + 2; j < totalCount; j++)
   {
      if(pivots[j].isHigh && nextH < 0) nextH = pivots[j].price;
      if(!pivots[j].isHigh && nextL < 0) nextL = pivots[j].price;
      if(nextH > 0 && nextL > 0) break;
   }

   // 1. اصلاح نزولی در روند صعودی: Drop (High -> Low)
   if(p1.isHigh && !p2.isHigh)
   {
      if(prevL > 0 && p2.price > prevL)
      {
         // شرط ۱: اگر سقف بعد و کف بعد هر دو پایین‌تر بیایند -> چرخش روند
         if(nextH > 0 && nextH < p1.price && nextL > 0 && nextL < p2.price)
            return false;

         // شرط ۲: تأیید ادامه روند صعودی (شکست سقف P1 در سوینگ‌های بعد)
         bool brokeAboveP1 = false;
         bool hasFutureHighs = false;
         for(int j = idx + 2; j < totalCount && j <= idx + 8; j++)
         {
            if(pivots[j].isHigh)
            {
               hasFutureHighs = true;
               if(pivots[j].price > p1.price)
               {
                  brokeAboveP1 = true;
                  break;
               }
            }
         }
         // اگر سوینگ‌های بعدی شکل گرفته‌اند ولی هیچ‌کدام نتوانسته‌اند بالای P1 بروند -> سقف مستقل
         if(hasFutureHighs && !brokeAboveP1)
            return false;

         return true;
      }
   }
   // 2. اصلاح صعودی در روند نزولی: Rally (Low -> High)
   else if(!p1.isHigh && p2.isHigh)
   {
      if(prevH > 0 && p2.price < prevH)
      {
         // شرط ۱: اگر کف بعد و سقف بعد هر دو بالاتر بیایند -> چرخش روند
         if(nextL > 0 && nextL > p1.price && nextH > 0 && nextH > p2.price)
            return false;

         // شرط ۲: تأیید ادامه روند نزولی (شکست کف P1 در سوینگ‌های بعد)
         bool brokeBelowP1 = false;
         bool hasFutureLows = false;
         for(int j = idx + 2; j < totalCount && j <= idx + 8; j++)
         {
            if(!pivots[j].isHigh)
            {
               hasFutureLows = true;
               if(pivots[j].price < p1.price)
               {
                  brokeBelowP1 = true;
                  break;
               }
            }
         }
         // اگر سوینگ‌های بعدی شکل گرفته‌اند ولی هیچ‌کدام نتوانسته‌اند زیر P1 بروند -> کف مستقل
         if(hasFutureLows && !brokeBelowP1)
            return false;

         return true;
      }
   }

   return false;
}
