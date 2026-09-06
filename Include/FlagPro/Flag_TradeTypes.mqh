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

