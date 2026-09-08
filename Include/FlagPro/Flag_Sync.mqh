//+------------------------------------------------------------------+
//| Flag_Sync.mqh                                                    |
//| FlagPro Auto-Sync Engine: Tester ⇄ Indicator Live Synchronization|
//+------------------------------------------------------------------+
#property copyright "FlagPro Quantitative Trading Systems"
#property link      ""

// متغیرهای وضعیت همگام‌سازی زنده
bool     g_syncActive                 = false;
string   g_syncScenarioName           = "";
datetime g_syncLastFileModTime        = 0;

bool     g_syncOnlyTradeKings         = false;
bool     g_syncTradeOnlyGoldenKings   = false;
string   g_syncAllowedKingsList       = "";
string   g_syncDisabledKingsList      = "";
bool     g_syncEnableKingsM15         = true;
bool     g_syncEnableKingsM5          = true;
bool     g_syncEnableKingsM1          = true;
bool     g_syncFilterNightHours       = false;
bool     g_syncFilterPreLondonHunt    = false;
bool     g_syncFilterToxicPatterns    = false;
bool     g_syncFilterSingleLS         = false;
bool     g_syncFilterPureFlags        = false;
bool     g_syncFilterLowRewardVsFriction = false;
ENUM_SL_MODE    g_syncSLMode                 = SL_MODE_ATR_BUFFER;
double          g_syncSLFixedPips            = 3.0;
ENUM_TIMEFRAMES g_syncSLATRTimeframe         = PERIOD_CURRENT;
int             g_syncSLATRPeriod            = 14;
double          g_syncSLATRMultiplier        = 0.5;
double          g_syncSLBoxPercent           = 0.30;
double          g_syncSLMinPips              = 2.5;
double          g_syncSLMaxPips              = 40.0;
double          g_syncSLOffsetPips           = 3.0;
double   g_syncMaxEntryDeviationPips  = 2.5;
int      g_syncLimitExpirationBars    = 40;
bool     g_syncUseTF7                 = true;
bool     g_syncUseTF6                 = true;
bool     g_syncUseTF5                 = true;
bool     g_syncAllowOverlappingTrades = true;
bool     g_syncTradeMacroTFs          = false;
string   g_syncAllowedTradingHours    = "";
double   g_syncMinTradePotential     = 0.0;

#define SYNC_SCENARIO_FILENAME "FlagPro_ActiveScenario.ini"

//+------------------------------------------------------------------+
//| توابع هوشمند دریافت مقادیر فعال (با اولویت داده‌های Auto-Sync تستر) |
//+------------------------------------------------------------------+
bool ActiveOnlyTradeKings()       { return (g_syncActive ? g_syncOnlyTradeKings : InpOnlyTradeKings); }
bool ActiveTradeOnlyGoldenKings() { return (g_syncActive ? g_syncTradeOnlyGoldenKings : InpTradeOnlyGoldenKings); }
string ActiveAllowedKingsList()   { return (g_syncActive ? g_syncAllowedKingsList : InpAllowedKingsList); }
string ActiveDisabledKingsList()  { return (g_syncActive ? g_syncDisabledKingsList : InpDisabledKingsList); }
bool ActiveEnableKingsM15()       { return (g_syncActive ? g_syncEnableKingsM15 : InpEnableKingsM15); }
bool ActiveEnableKingsM5()        { return (g_syncActive ? g_syncEnableKingsM5 : InpEnableKingsM5); }
bool ActiveEnableKingsM1()        { return (g_syncActive ? g_syncEnableKingsM1 : InpEnableKingsM1); }
bool ActiveFilterNightHours()     { return (g_syncActive ? g_syncFilterNightHours : InpFilterNightHours); }
bool ActiveFilterPreLondonHunt()  { return (g_syncActive ? g_syncFilterPreLondonHunt : InpFilterPreLondonHunt); }
bool ActiveFilterToxicPatterns()  { return (g_syncActive ? g_syncFilterToxicPatterns : InpFilterToxicPatterns); }
bool ActiveFilterSingleLS()       { return (g_syncActive ? g_syncFilterSingleLS : InpFilterSingleLS); }
bool ActiveFilterPureFlags()      { return (g_syncActive ? g_syncFilterPureFlags : InpFilterPureFlags); }
bool ActiveFilterLowReward()      { return (g_syncActive ? g_syncFilterLowRewardVsFriction : InpFilterLowRewardVsFriction); }

ENUM_SL_MODE    ActiveSLMode()             { return (g_syncActive ? g_syncSLMode : InpSLMode); }
double          ActiveSLFixedPips()        { return (g_syncActive ? g_syncSLFixedPips : InpSLFixedPips); }
double          ActiveSLOffsetPips()       { return ActiveSLFixedPips(); }
ENUM_TIMEFRAMES ActiveSLATRTimeframe()     { return (g_syncActive ? g_syncSLATRTimeframe : InpSLATRTimeframe); }
int             ActiveSLATRPeriod()        { return (g_syncActive ? g_syncSLATRPeriod : InpSLATRPeriod); }
double          ActiveSLATRMultiplier()    { return (g_syncActive ? g_syncSLATRMultiplier : InpSLATRMultiplier); }
double          ActiveSLBoxPercent()       { return (g_syncActive ? g_syncSLBoxPercent : InpSLBoxPercent); }
double          ActiveSLMinPips()          { return (g_syncActive ? g_syncSLMinPips : InpSLMinPips); }
double          ActiveSLMaxPips()          { return (g_syncActive ? g_syncSLMaxPips : InpSLMaxPips); }
double ActiveMaxEntryDeviationPips(){ return (g_syncActive ? g_syncMaxEntryDeviationPips : InpMaxEntryDeviationPips); }
int  ActiveLimitExpirationBars()  { return (g_syncActive ? g_syncLimitExpirationBars : InpLimitExpirationBars); }
bool ActiveUseTF7()               { return (g_syncActive ? g_syncUseTF7 : InpUseTF7); }
bool ActiveUseTF6()               { return (g_syncActive ? g_syncUseTF6 : InpUseTF6); }
bool ActiveUseTF5()               { return (g_syncActive ? g_syncUseTF5 : InpUseTF5); }
bool ActiveAllowOverlappingTrades(){ return (g_syncActive ? g_syncAllowOverlappingTrades : InpAllowOverlappingTrades); }
bool ActiveTradeMacroTFs()        { return (g_syncActive ? g_syncTradeMacroTFs : InpTradeMacroTFs); }
string ActiveAllowedTradingHours(){ return (g_syncActive ? g_syncAllowedTradingHours : InpAllowedTradingHours); }
double ActiveMinTradePotential() { return (g_syncActive ? g_syncMinTradePotential : InpMinTradePotential); }

//+------------------------------------------------------------------+
//| ذخیره‌سازی مشخصات سناریوی فعال تستر در فایل مشترک (توسط اکسپرت)   |
//+------------------------------------------------------------------+
void SaveActiveScenarioToCommon(const string scenarioName,
                                bool onlyTradeKings,
                                bool tradeOnlyGoldenKings,
                                const string allowedKings,
                                const string disabledKings,
                                bool enableM15,
                                bool enableM5,
                                bool enableM1,
                                bool fNight,
                                bool fPreLon,
                                bool fToxic,
                                bool fSingleLS,
                                bool fPureFlags,
                                bool fLowReward,
                                double slOffset,
                                double maxDev,
                                int limitExpBars,
                                bool useTF7,
                                bool useTF6,
                                bool useTF5,
                                bool allowOverlap = true,
                                bool tradeMacro = false,
                                const string allowedHours = "",
                                double minPot = 0.0,
                                ENUM_SL_MODE slMode = SL_MODE_ATR_BUFFER,
                                double slFixed = 3.0,
                                ENUM_TIMEFRAMES slAtrTf = PERIOD_CURRENT,
                                int slAtrPer = 14,
                                double slAtrMul = 0.5,
                                double slBoxPct = 0.30,
                                double slMin = 2.5,
                                double slMax = 40.0)
{
   int hFile = FileOpen(SYNC_SCENARIO_FILENAME, FILE_WRITE | FILE_TXT | FILE_UNICODE | FILE_COMMON);
   if(hFile == INVALID_HANDLE)
      hFile = FileOpen(SYNC_SCENARIO_FILENAME, FILE_WRITE | FILE_TXT | FILE_UNICODE);

   if(hFile != INVALID_HANDLE)
   {
      FileWriteString(hFile, "[ActiveScenario]\r\n");
      FileWriteString(hFile, "Timestamp=" + IntegerToString((int)TimeCurrent()) + "\r\n");
      FileWriteString(hFile, "ScenarioName=" + (scenarioName == "" ? "پیش‌فرض تستر" : scenarioName) + "\r\n");
      FileWriteString(hFile, "Symbol=" + _Symbol + "\r\n");
      FileWriteString(hFile, "InpOnlyTradeKings=" + (onlyTradeKings ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpTradeOnlyGoldenKings=" + (tradeOnlyGoldenKings ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpAllowedKingsList=" + allowedKings + "\r\n");
      FileWriteString(hFile, "InpDisabledKingsList=" + disabledKings + "\r\n");
      FileWriteString(hFile, "InpEnableKingsM15=" + (enableM15 ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpEnableKingsM5=" + (enableM5 ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpEnableKingsM1=" + (enableM1 ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpFilterNightHours=" + (fNight ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpFilterPreLondonHunt=" + (fPreLon ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpFilterToxicPatterns=" + (fToxic ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpFilterSingleLS=" + (fSingleLS ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpFilterPureFlags=" + (fPureFlags ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpFilterLowRewardVsFriction=" + (fLowReward ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpSLOffsetPips=" + DoubleToString(slOffset, 1) + "\r\n");
      FileWriteString(hFile, "InpSLMode=" + IntegerToString((int)slMode) + "\r\n");
      FileWriteString(hFile, "InpSLFixedPips=" + DoubleToString(slFixed, 1) + "\r\n");
      FileWriteString(hFile, "InpSLATRTimeframe=" + IntegerToString((int)slAtrTf) + "\r\n");
      FileWriteString(hFile, "InpSLATRPeriod=" + IntegerToString(slAtrPer) + "\r\n");
      FileWriteString(hFile, "InpSLATRMultiplier=" + DoubleToString(slAtrMul, 2) + "\r\n");
      FileWriteString(hFile, "InpSLBoxPercent=" + DoubleToString(slBoxPct, 2) + "\r\n");
      FileWriteString(hFile, "InpSLMinPips=" + DoubleToString(slMin, 1) + "\r\n");
      FileWriteString(hFile, "InpSLMaxPips=" + DoubleToString(slMax, 1) + "\r\n");
      FileWriteString(hFile, "InpMaxEntryDeviationPips=" + DoubleToString(maxDev, 1) + "\r\n");
      FileWriteString(hFile, "InpLimitExpirationBars=" + IntegerToString(limitExpBars) + "\r\n");
      FileWriteString(hFile, "InpUseTF7=" + (useTF7 ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpUseTF6=" + (useTF6 ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpUseTF5=" + (useTF5 ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpAllowOverlappingTrades=" + (allowOverlap ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpTradeMacroTFs=" + (tradeMacro ? "true" : "false") + "\r\n");
      FileWriteString(hFile, "InpAllowedTradingHours=" + allowedHours + "\r\n");
      FileWriteString(hFile, "InpMinTradePotential=" + DoubleToString(minPot, 2) + "\r\n");
      FileClose(hFile);

      PrintFormat("🔄 [FlagPro Auto-Sync] سناریوی «%s» در فایل مشترک ذخیره شد جهت هماهنگی خودکار با اندیکاتور چارت.", scenarioName);
   }
}

//+------------------------------------------------------------------+
//| خواندن و اعمال مشخصات سناریوی فعال تستر در اندیکاتور چارت         |
//+------------------------------------------------------------------+
bool CheckAndLoadActiveScenario(bool forceReload = false)
{
   if(!FileIsExist(SYNC_SCENARIO_FILENAME, FILE_COMMON) && !FileIsExist(SYNC_SCENARIO_FILENAME))
      return false;

   int hFile = FileOpen(SYNC_SCENARIO_FILENAME, FILE_READ | FILE_TXT | FILE_UNICODE | FILE_COMMON);
   if(hFile == INVALID_HANDLE)
      hFile = FileOpen(SYNC_SCENARIO_FILENAME, FILE_READ | FILE_TXT | FILE_UNICODE);

   if(hFile == INVALID_HANDLE)
      return false;

   string scName = "";
   datetime ts = 0;
   bool oKings = false, gKings = false;
   string aList = "", dList = "";
   bool kM15 = true, kM5 = true, kM1 = true;
   bool fNight = false, fPreLon = false, fToxic = false, fSingleLS = false, fPure = false, fLow = false;
   double slOff = 3.0, maxDev = 2.5;
   int lBars = 40;
   bool uTF7 = true, uTF6 = true, uTF5 = true;
   bool aOverlap = true, tMacro = false;
   string aHours = "";
   double mPot = 0.0;
   ENUM_SL_MODE slM = InpSLMode;
   double slFixedVal = InpSLFixedPips;
   ENUM_TIMEFRAMES slAtrTfVal = InpSLATRTimeframe;
   int slAtrPerVal = InpSLATRPeriod;
   double slAtrMulVal = InpSLATRMultiplier;
   double slBoxPctVal = InpSLBoxPercent;
   double slMinVal = InpSLMinPips;
   double slMaxVal = InpSLMaxPips;

   while(!FileIsEnding(hFile))
   {
      string line = FileReadString(hFile);
      StringTrimLeft(line);
      StringTrimRight(line);
      if(StringLen(line) == 0 || StringSubstr(line, 0, 1) == ";" || StringSubstr(line, 0, 1) == "[")
         continue;

      int eqPos = StringFind(line, "=");
      if(eqPos <= 0) continue;

      string key = StringSubstr(line, 0, eqPos);
      string val = StringSubstr(line, eqPos + 1);
      StringTrimLeft(key); StringTrimRight(key);
      StringTrimLeft(val); StringTrimRight(val);

      if(key == "ScenarioName")                     scName = val;
      else if(key == "Timestamp")                   ts = (datetime)StringToInteger(val);
      else if(key == "InpOnlyTradeKings")           oKings = (val == "true" || val == "1");
      else if(key == "InpTradeOnlyGoldenKings")     gKings = (val == "true" || val == "1");
      else if(key == "InpAllowedKingsList")         aList = val;
      else if(key == "InpDisabledKingsList")        dList = val;
      else if(key == "InpEnableKingsM15")           kM15 = (val == "true" || val == "1");
      else if(key == "InpEnableKingsM5")            kM5 = (val == "true" || val == "1");
      else if(key == "InpEnableKingsM1")            kM1 = (val == "true" || val == "1");
      else if(key == "InpFilterNightHours")         fNight = (val == "true" || val == "1");
      else if(key == "InpFilterPreLondonHunt")       fPreLon = (val == "true" || val == "1");
      else if(key == "InpFilterToxicPatterns")      fToxic = (val == "true" || val == "1");
      else if(key == "InpFilterSingleLS")           fSingleLS = (val == "true" || val == "1");
      else if(key == "InpFilterPureFlags")          fPure = (val == "true" || val == "1");
      else if(key == "InpFilterLowRewardVsFriction") fLow = (val == "true" || val == "1");
      else if(key == "InpSLOffsetPips" || key == "InpSLFixedPips") { slOff = StringToDouble(val); slFixedVal = slOff; }
      else if(key == "InpSLMode")                   slM = (ENUM_SL_MODE)StringToInteger(val);
      else if(key == "InpSLATRTimeframe")          slAtrTfVal = (ENUM_TIMEFRAMES)StringToInteger(val);
      else if(key == "InpSLATRPeriod")             slAtrPerVal = (int)StringToInteger(val);
      else if(key == "InpSLATRMultiplier")         slAtrMulVal = StringToDouble(val);
      else if(key == "InpSLBoxPercent")            slBoxPctVal = StringToDouble(val);
      else if(key == "InpSLMinPips")               slMinVal = StringToDouble(val);
      else if(key == "InpSLMaxPips")               slMaxVal = StringToDouble(val);
      else if(key == "InpMaxEntryDeviationPips")    maxDev = StringToDouble(val);
      else if(key == "InpLimitExpirationBars")      lBars = (int)StringToInteger(val);
      else if(key == "InpUseTF7")                   uTF7 = (val == "true" || val == "1");
      else if(key == "InpUseTF6")                   uTF6 = (val == "true" || val == "1");
      else if(key == "InpUseTF5")                   uTF5 = (val == "true" || val == "1");
      else if(key == "InpAllowOverlappingTrades")   aOverlap = (val == "true" || val == "1");
      else if(key == "InpTradeMacroTFs")            tMacro = (val == "true" || val == "1");
      else if(key == "InpAllowedTradingHours")       aHours = val;
      else if(key == "InpMinTradePotential")        mPot = StringToDouble(val);
   }
   FileClose(hFile);

   if(!forceReload && g_syncActive && g_syncLastFileModTime == ts && g_syncScenarioName == scName)
      return false; // بدون تغییر

   g_syncActive                 = true;
   g_syncScenarioName           = scName;
   g_syncLastFileModTime        = ts;
   g_syncOnlyTradeKings         = oKings;
   g_syncTradeOnlyGoldenKings   = gKings;
   g_syncAllowedKingsList       = aList;
   g_syncDisabledKingsList      = dList;
   g_syncEnableKingsM15         = kM15;
   g_syncEnableKingsM5          = kM5;
   g_syncEnableKingsM1          = kM1;
   g_syncFilterNightHours       = fNight;
   g_syncFilterPreLondonHunt    = fPreLon;
   g_syncFilterToxicPatterns    = fToxic;
   g_syncFilterSingleLS         = fSingleLS;
   g_syncFilterPureFlags        = fPure;
   g_syncFilterLowRewardVsFriction = fLow;
   g_syncSLMode                 = slM;
   g_syncSLFixedPips            = slFixedVal;
   g_syncSLOffsetPips           = slFixedVal;
   g_syncSLATRTimeframe         = slAtrTfVal;
   g_syncSLATRPeriod            = slAtrPerVal;
   g_syncSLATRMultiplier        = slAtrMulVal;
   g_syncSLBoxPercent           = slBoxPctVal;
   g_syncSLMinPips              = slMinVal;
   g_syncSLMaxPips              = slMaxVal;
   g_syncMaxEntryDeviationPips  = maxDev;
   g_syncLimitExpirationBars    = lBars;
   g_syncUseTF7                 = uTF7;
   g_syncUseTF6                 = uTF6;
   g_syncUseTF5                 = uTF5;
   g_syncAllowOverlappingTrades = aOverlap;
   g_syncTradeMacroTFs          = tMacro;
   g_syncAllowedTradingHours    = aHours;
   g_syncMinTradePotential      = mPot;

   PrintFormat("⚡ [FlagPro Auto-Sync] اندیکاتور چارت با سناریوی تستر «%s» همگام شد! (سلاطین: %s | M1: %s | استاپ: مدل %d | کف سود: $%.1f)",
               g_syncScenarioName, (g_syncOnlyTradeKings ? "فعال" : "غیرفعال"), (g_syncUseTF7 ? "فعال" : "غیرفعال"),
               (int)g_syncSLMode, g_syncMinTradePotential);
   return true;
}
