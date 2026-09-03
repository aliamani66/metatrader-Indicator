//+------------------------------------------------------------------+
//|                                     FlagPro_VisualTester.mq5     |
//|                 Visual Mode Tester EA for FlagPro Indicator      |
//+------------------------------------------------------------------+
#property copyright   "FlagPro Visual Tester"
#property version     "1.00"
#property tester_indicator "FlagPro.ex5"

int g_indicatorHandle = INVALID_HANDLE;

int OnInit()
{
   g_indicatorHandle = iCustom(_Symbol, _Period, "FlagPro");
   if(g_indicatorHandle == INVALID_HANDLE)
   {
      Print("❌ خطا در ایجاد هندل FlagPro: ", GetLastError());
      return INIT_FAILED;
   }
   Print("🚀 FlagPro با موفقیت در محیط تستر بارگذاری شد.");
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