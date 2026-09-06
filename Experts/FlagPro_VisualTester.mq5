//+------------------------------------------------------------------+
//|                                     FlagPro_VisualTester.mq5     |
//|                 Visual Mode Tester EA for FlagPro Indicator      |
//+------------------------------------------------------------------+
#property copyright   "FlagPro Visual Tester"
#property version     "1.01"
#property tester_indicator "FlagPro.ex5"

#include <FlagPro\Flag_Types.mqh>

//+------------------------------------------------------------------+
//| ورودی‌های تنظیمات اندیکاتور در محیط تستر                         |
//+------------------------------------------------------------------+
input group "=== 🎯 ۱. تنظیم بازه تاریخی و عملکرد ==="
input datetime          InpHistoryStartDate   = D'2025.01.01 00:00';    // 📅 تاریخ شروع دلخواه
input int               InpHistoryDays        = 2;                      // ⏳ یا تعداد روز گذشته
input ENUM_HISTORY_MODE InpHistoryMode        = HIST_DAYS_BACK;         // ⚙️ مبنای بازه تاریخی
input bool              InpShowBoxes          = false;                  // 👁️ رسم باکس‌های قیمتی
input bool              InpAutoDrawTrades     = true;                   // 🎯 رسم معاملات روی چارت
input bool              InpExportCSV          = true;                   // 📁 استخراج خودکار فایل CSV

input group "=== 👑 ۲. سلاطین طلایی معاملاتی ==="
input bool              InpOnlyTradeKings     = true;                   // 👑 فقط معامله و رسم سلاطین برگزیده
input bool              InpEnableKingsM15     = true;                   // 👑 فعال‌سازی سلاطین M15
input bool              InpEnableKingsM5      = true;                   // 👑 فعال‌سازی سلاطین M5
input bool              InpEnableKingsM1      = true;                   // 👑 فعال‌سازی سلاطین M1
input bool              InpTradeOnlyGoldenKings = true;                 // 👑 قفل انحصاری سلاطین طلایی
input string            InpAllowedKingsList   = "";                     // 👑 لیست انحصاری سلاطین مجاز
input bool              InpAllowOverlappingTrades = true;               // 🔓 اجازه معاملات همزمان

input group "=== 🛡️ ۳. فیلترهای ضد استاپ، اصطکاک و حد ضرر ==="
input bool              InpEnableTradeSetup   = true;                   // فعال‌سازی ستاپ معاملاتی
input double            InpSLOffsetPips       = 8.0;                    // 🛡️ فاصله اطمینان حد ضرر (پیپ)
input bool              InpFilterNightHours   = true;                   // 🛡️ فیلتر ۱: مسدودسازی شب
input bool              InpFilterPreLondonHunt= true;                   // 🛡️ فیلتر ۲: مسدودسازی قبل لندن
input bool              InpFilterToxicPatterns= true;                   // 🛡️ فیلتر ۳: حذف زنجیره‌های سمی
input bool              InpFilterSingleLS     = true;                   // 🛡️ فیلتر ۴: حذف باکس‌های منفرد LS
input bool              InpFilterPureFlags    = true;                   // 🛡️ فیلتر ۵: حذف فلگ‌های بدون تلاقی
input bool              InpFilterLowRewardVsFriction = true;            // 💰 فیلتر اصطکاک کمیسیون
input double            InpBrokerCommissionPerLot    = 6.0;             // کمیسیون بروکر در هر ۱ لات ($)
input double            InpEstimatedSpreadPips       = 0.8;             // اسپرد تخمینی (پیپ)
input double            InpMinNetProfitRatioTP1      = 1.0;             // حداقل نسبت سود TP1 به کل اصطکاک

input group "=== ⏱️ ۴. تایم‌فریم‌های فعال معامله ==="
input bool              InpUseTF7             = true;                   // محاسبه ۱ دقیقه (M1)
input bool              InpUseTF6             = true;                   // محاسبه ۵ دقیقه (M5)
input bool              InpUseTF5             = true;                   // محاسبه ۱۵ دقیقه (M15)
input bool              InpTradeMacroTFs      = false;                  // معامله در تایم‌های ماکرو

int g_indicatorHandle = INVALID_HANDLE;

int OnInit()
{
   g_indicatorHandle = iCustom(_Symbol, _Period, "FlagPro",
                               InpHistoryStartDate,
                               InpHistoryDays,
                               InpHistoryMode,
                               InpShowBoxes,
                               InpAutoDrawTrades,
                               InpExportCSV,
                               InpOnlyTradeKings,
                               InpEnableKingsM15,
                               InpEnableKingsM5,
                               InpEnableKingsM1,
                               InpTradeOnlyGoldenKings,
                               InpAllowedKingsList,
                               InpAllowOverlappingTrades,
                               InpEnableTradeSetup,
                               InpSLOffsetPips,
                               InpFilterNightHours,
                               InpFilterPreLondonHunt,
                               InpFilterToxicPatterns,
                               InpFilterSingleLS,
                               InpFilterPureFlags,
                               InpFilterLowRewardVsFriction,
                               InpBrokerCommissionPerLot,
                               InpEstimatedSpreadPips,
                               InpMinNetProfitRatioTP1,
                               InpUseTF7,
                               InpUseTF6,
                               InpUseTF5,
                               InpTradeMacroTFs);
   if(g_indicatorHandle == INVALID_HANDLE)
   {
      Print("❌ خطا در ایجاد هندل FlagPro: ", GetLastError());
      return INIT_FAILED;
   }
   Print("🚀 FlagPro با موفقیت با پارامترهای سفارشی در محیط تستر بارگذاری شد.");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(g_indicatorHandle != INVALID_HANDLE)
   {
      IndicatorRelease(g_indicatorHandle);
      g_indicatorHandle = INVALID_HANDLE;
   }
}

void OnTick()
{
}