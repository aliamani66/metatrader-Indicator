//+------------------------------------------------------------------+
//| Flag_Filters.mqh                                                 |
//| Dedicated Anti-SL Filter Module for FlagPro                      |
//| Handles pattern toxicity, session hours, and noise filtering     |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""

//+------------------------------------------------------------------+
//| فیلتر ۱: بررسی باکس‌های منفرد LS بدون تلاقی                       |
//| آمار ۳ ماهه: ۱۳۱۱ حذف | ۸۹۹ استاپ نجات‌یافته | دقت: ۶۸.۶٪           |
//+------------------------------------------------------------------+
bool IsSingleLSPattern(const string roleTag)
{
   if(roleTag == "LS-BE" || roleTag == "LS-BU")
      return true;
   return false;
}

//+------------------------------------------------------------------+
//| فیلتر ۲: بررسی ساعات شبانه و بسته شدن نیویورک (۲۱ تا ۰۱)          |
//| آمار ۳ ماهه: ۶۰۷ حذف | ۳۹۶ استاپ نجات‌یافته | دقت: ۶۵.۲٪           |
//+------------------------------------------------------------------+
bool IsNightSessionHour(const datetime entryTime)
{
   if(entryTime <= 0) return false;
   MqlDateTime dt;
   TimeToStruct(entryTime, dt);

   // ساعات ۲۱:۰۰، ۲۲:۰۰، ۲۳:۰۰، ۰۰:۰۰ (بسته شدن نیویورک و اسپرد Rollover)
   if(dt.hour == 21 || dt.hour == 22 || dt.hour == 23 || dt.hour == 0)
      return true;

   return false;
}

//+------------------------------------------------------------------+
//| فیلتر ۳: بررسی زنجیره‌های سمی و فرسایشی با استاپ بالای ۷۰٪          |
//| آمار ۳ ماهه: ۲۹۶ حذف | ۲۰۹ استاپ نجات‌یافته | دقت: ۷۰.۶٪           |
//+------------------------------------------------------------------+
bool IsToxicPattern(const string roleTag)
{
   // ۱. زنجیره نزولی فرسایشی با استاپ ۷۰.۵٪
   if(StringFind(roleTag, "LS-BE > RS-BE") >= 0)
      return true;

   // ۲. زنجیره صعودی اشباع خرید با استاپ ۷۰.۲٪
   if(StringFind(roleTag, "LS-BU > RS-BU") >= 0)
      return true;

   // ۳. زنجیره خسته‌کننده ۳ مرحله‌ای نزولی با استاپ ۹۳.۸٪
   if(StringFind(roleTag, "LS-BE > OInner-BE > RS-BE") >= 0)
      return true;

   // ۴. تضاد ۱۸۰ درجه بال ال‌اس نزولی با بدنه صعودی با استاپ ۷۵.۰٪
   if(StringFind(roleTag, "LS-BE > OInner-BU > RS-BU") >= 0)
      return true;

   // ۵. تکمیل امواج صعودی اشباع با استاپ ۷۱.۴٪
   if(StringFind(roleTag, "LS-BU > OInner-BU > RS-BU") >= 0)
      return true;

   return false;
}

//+------------------------------------------------------------------+
//| فیلتر ۴: بررسی فلگ‌های ساده بدون تلاقی (نویز بازار)              |
//| آمار ۳ ماهه: ۵۷۷ حذف | ۳۴۸ استاپ نجات‌یافته | دقت: ۶۰.۳٪           |
//+------------------------------------------------------------------+
bool IsPureNoiseFlag(const string roleTag)
{
   if(roleTag == "Flag" || roleTag == "Flag-BE" || roleTag == "Flag-BU")
      return true;
   return false;
}

//+------------------------------------------------------------------+
//| فیلتر ۵: بررسی ساعت ۰۷:۰۰ صبح (شکار استاپ آسیا قبل از لندن)      |
//| آمار ۳ ماهه: ۱۶۷ حذف | ۹۸ استاپ نجات‌یافته | دقت: ۵۸.۷٪            |
//+------------------------------------------------------------------+
bool IsPreLondonHour(const datetime entryTime)
{
   if(entryTime <= 0) return false;
   MqlDateTime dt;
   TimeToStruct(entryTime, dt);
   return (dt.hour == 7);
}

//+------------------------------------------------------------------+
//| فیلتر ۶: بررسی اقتصادی سود TP1 در برابر اصطکاک (کمیسیون + اسپرد) |
//+------------------------------------------------------------------+
bool IsRewardLessThanFriction(double riskPoints)
{
   if(!InpFilterLowRewardVsFriction) return false;
   if(riskPoints <= 0) return false;

   double pipVal = 10.0; // 1 pip = 10 points
   double commInPips = InpBrokerCommissionPerLot / 10.0;
   double totalFrictionPips = InpEstimatedSpreadPips + commInPips;
   double minRequiredPoints = totalFrictionPips * InpMinNetProfitRatioTP1 * pipVal;

   return (riskPoints <= minRequiredPoints);
}

//+------------------------------------------------------------------+
//| ارزیابی جامع فیلتر بودن یک ستاپ معاملاتی بر اساس تنظیمات ورودی   |
//+------------------------------------------------------------------+
bool IsSetupFilteredOut(const string roleTag, const datetime entryTime, double riskPoints = 0.0)
{
   if(InpFilterSingleLS && IsSingleLSPattern(roleTag))
      return true;

   if(InpFilterNightHours && IsNightSessionHour(entryTime))
      return true;

   if(InpFilterPreLondonHunt && IsPreLondonHour(entryTime))
      return true;

   if(InpFilterToxicPatterns && IsToxicPattern(roleTag))
      return true;

   if(InpFilterPureFlags && IsPureNoiseFlag(roleTag))
      return true;

   if(InpFilterLowRewardVsFriction && IsRewardLessThanFriction(riskPoints))
      return true;

   return false;
}

//+------------------------------------------------------------------+
//| دریافت دلیل فیلتر شدن به همراه درصد دقت دقیق جهت نمایش در چارت  |
//+------------------------------------------------------------------+
string GetFilterRejectionReason(const string roleTag, const datetime entryTime, double riskPoints = 0.0)
{
   if(InpFilterLowRewardVsFriction && IsRewardLessThanFriction(riskPoints))
   {
      double pips = riskPoints / 10.0;
      double costPips = InpEstimatedSpreadPips + (InpBrokerCommissionPerLot / 10.0);
      return StringFormat("💰 فیلتر اصطکاک: سود TP1 (%.1f پیپ) کمتر یا سربه‌سر با کمیسیون و اسپرد (%.1f پیپ) است!", pips, costPips);
   }

   if(InpFilterSingleLS && IsSingleLSPattern(roleTag))
      return "⛔ فیلتر باکس منفرد LS [دقت فیلتر: ۶۸.۶٪ | از هر ۱۰ ترید حذفی، ۷ تا استاپ بود]";

   if(InpFilterToxicPatterns && IsToxicPattern(roleTag))
      return "⛔ فیلتر زنجیره سمی و فرسایشی [دقت فیلتر: ۷۰.۶٪ | از هر ۱۰ ترید حذفی، ۷ تا استاپ بود]";

   if(InpFilterNightHours && IsNightSessionHour(entryTime))
      return "⏰ فیلتر ساعات شبانه ۲۱ تا ۰۱ [دقت فیلتر: ۶۵.۲٪ | از هر ۳ ترید حذفی، ۲ تا استاپ بود]";

   if(InpFilterPreLondonHunt && IsPreLondonHour(entryTime))
      return "⏰ فیلتر ساعت ۰۷:۰۰ قبل لندن [دقت فیلتر: ۵۸.۷٪ | از هر ۱۰ ترید حذفی، ۶ تا استاپ بود]";

   if(InpFilterPureFlags && IsPureNoiseFlag(roleTag))
      return "📦 فیلتر فلگ ساده بدون تلاقی [دقت فیلتر: ۶۰.۳٪ | از هر ۵ ترید حذفی، ۳ تا استاپ بود]";

   return "مجاز (تایید فیلترها) ✅";
}

//+------------------------------------------------------------------+
//| محاسبه امتیاز هوشمند ستاپ معاملاتی (Smart Setup Score: 0 - 100)  |
//+------------------------------------------------------------------+
int CalculateSmartSetupScore(const string roleTag, const datetime entryTime, double riskPoints)
{
   int baseScore = 60;
   
   // ۱. امتیاز قدرت ساختار بر اساس سودآوری و وین‌ریت تاریخی
   if(roleTag == "RS-BU") baseScore = 95;
   else if(roleTag == "OInner-BE > RS-BU") baseScore = 92;
   else if(roleTag == "OInner-BU > RS-BU") baseScore = 90;
   else if(roleTag == "RS-BE") baseScore = 88;
   else if(roleTag == "OInner-BU") baseScore = 85;
   else if(roleTag == "OInner-BE") baseScore = 82;
   else if(roleTag == "OInner-BU > RS-BE") baseScore = 82;
   else if(StringFind(roleTag, "S-") == 0) baseScore = 55;
   else baseScore = 50;

   // ۲. مؤلفه سشن نقدینگی (لندن و نیویورک)
   int sessionMod = 0;
   if(entryTime > 0)
   {
      MqlDateTime dt;
      TimeToStruct(entryTime, dt);
      if(dt.hour >= 10 && dt.hour <= 19) sessionMod = 5;      // اوج نقدینگی لندن و نیویورک
      else if(dt.hour >= 8 && dt.hour < 10) sessionMod = 2;   // افتتاحیه اروپا
      else sessionMod = -5;                                  // کم‌حجم یا شیفت شب
   }

   // ۳. نسبت سود به اصطکاک (اندازه باکس)
   int sizeMod = 0;
   if(riskPoints >= 40) sizeMod = 5;       // بزرگتر از ۴ پیپ
   else if(riskPoints >= 25) sizeMod = 2;  // ۲.۵ تا ۴ پیپ
   else if(riskPoints < 15) sizeMod = -10; // کمتر از ۱.۵ پیپ (جریمه اصطکاک)

   int finalScore = baseScore + sessionMod + sizeMod;
   if(finalScore > 100) finalScore = 100;
   if(finalScore < 0) finalScore = 0;
   return finalScore;
}

//+------------------------------------------------------------------+
//| تعیین رده کیفی بر اساس امتیاز هوشمند                             |
//+------------------------------------------------------------------+
string GetSmartScoreTier(int score)
{
   if(score >= 90) return "💎 درجه الماس (Diamond Tier)";
   if(score >= 80) return "🥇 درجه طلا (Gold Tier)";
   if(score >= 70) return "🥈 درجه نقره (Silver Tier)";
   return "🥉 درجه برنز (Bronze Tier)";
}

//+------------------------------------------------------------------+
//| استراتژی خروج پلکانی پیشنهادی هوشمند                             |
//+------------------------------------------------------------------+
string GetRecommendedExitPlan(int score, const string roleTag)
{
   if(score >= 90)
      return "پلکانی رانر امواج بزرگ 🚀 [TP1: ۵۰٪ + ریسک‌فری | TP2: ۲۵٪ | TP4: ۲۵٪ رانر]";
   else if(score >= 80)
      return "پلکانی استاندارد 🌟 [TP1: ۵۰٪ + ریسک‌فری | TP2: ۲۵٪ | TP3: ۲۵٪]";
   else
      return "اسکلپ سریع ⚡ [TP1: ۷۰٪ + ریسک‌فری | TP2: ۳۰٪]";
}
