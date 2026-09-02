//+------------------------------------------------------------------+
//| Flag_Types.mqh                                                   |
//| FlagPro Data Structures and Global Types                         |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""

#include <MarketStructureEngine.mqh>

// پیشوند اختصاصی اشیاء گرافیکی FlagPro جهت جلوگیری از هرگونه تداخل با سایر اندیکاتورها
#define FP_PREFIX "FLAGPRO_"

enum ENUM_LABEL_STYLE
{
   LABEL_COMPACT,   // کوتاه و تمیز (مانند M15➔H1)
   LABEL_FULL,      // متن کامل
   LABEL_TOOLTIP    // فقط هنگام بردن موس روی خط (چارت کاملاً خلوت و بدون متن)
};

// ساختار نگهداری مشخصات باکس‌ها
struct SBoxInfo
{
   string          boxName;
   string          boxKey;
   ENUM_TIMEFRAMES tf;
   string          tfTag;
   int             swingIdx;
   datetime        t1;
   datetime        t2;
   double          top;
   double          bottom;
   color           baseColor;
   int             baseWidth;
   ENUM_LINE_STYLE baseStyle;
   bool            isBullish;
   bool            isPreIP;
   bool            isLSBull;
   bool            isBOFlag;
   bool            isRSBull;
   bool            isOInner;
   bool            isOInnerBull;
   bool            isSwap;
   bool            isSwapBull;
   string          swapSourceRole;
   string          rsTags[];
   bool            isMacro;
   datetime        targetIPTime;
   bool            targetIPIsHigh;
};

// ساختار نگهداری معاملات بک‌تست
struct STradeSetup
{
   string   boxName;
   string   boxRole;
   ENUM_TIMEFRAMES tf;
   string   tfTag;
   bool     isBuy;
   datetime entryTime;
   double   entryPrice;
   double   slPrice;
   double   risk;
   double   tp1;
   double   tp2;
   double   tp3;
   double   tp4;
   datetime exitTime;
   int      hitTP; // 0=SL hit, 1=TP1, 2=TP2, 3=TP3, 4=TP4, -1=Open
   bool     isClosed;
};

// ساختار نگهداری پیووت‌های مستقل
struct SIndepPivot
{
   datetime time;
   double   price;
   bool     isHigh;
   bool     hasIP;
   string   tfTags[];
   color    clr;
};

// متغیرها و آرایه‌های سراسری FlagPro
SPivot          g_pivotsH1[];
int             g_pivotCountH1 = 0;
SBoxInfo        g_drawnBoxes[];
int             g_boxCount = 0;
int             g_clickCounter = 0;
STradeSetup     g_tradeSetups[];
int             g_tradeCount = 0;
SIndepPivot     g_indepPivots[];
int             g_indepCount = 0;

string          g_selectedBoxName = "";
string          g_selectedExtBoxName = "";
color           g_origBoxColor = clrNONE;
int             g_origBoxWidth = 1;
ENUM_LINE_STYLE g_origBoxStyle = STYLE_SOLID;
bool            g_forceRecalc = true;
