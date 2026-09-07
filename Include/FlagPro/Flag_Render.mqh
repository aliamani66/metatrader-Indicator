//+------------------------------------------------------------------+
//| Flag_Render.mqh                                                  |
//| FlagPro Chart Rendering, Visual Styling & Click Interactivity    |
//+------------------------------------------------------------------+
#property copyright "FlagPro Indicator"
#property link      ""

// Forward declaration of ShowTradeSetupForBox defined in Flag_Backtest.mqh
void ShowTradeSetupForBox(int boxIdx);

//+------------------------------------------------------------------+
//| Helper: Draw Hollow Box on Chart with Custom Style               |
//+------------------------------------------------------------------+
void DrawHollowBox(string name, datetime t1, double top, datetime t2, double bottom,
                   color clr, int width, ENUM_LINE_STYLE style = STYLE_SOLID)
{
   if(!InpShowBoxes || !g_boxesVisible) return;
   if(ObjectFind(0, name) >= 0) ObjectDelete(0, name);
   ObjectCreate(0, name, OBJ_RECTANGLE, 0, t1, top, t2, bottom);
   ObjectSetInteger(0, name, OBJPROP_COLOR,      clr);
   ObjectSetInteger(0, name, OBJPROP_WIDTH,      width);
   ObjectSetInteger(0, name, OBJPROP_STYLE,      style);
   ObjectSetInteger(0, name, OBJPROP_FILL,       false);
   ObjectSetInteger(0, name, OBJPROP_BACK,       false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
}

//+------------------------------------------------------------------+
//| Apply High-Contrast Neutral Pro Chart Theme                      |
//+------------------------------------------------------------------+
void ApplyProChartTheme()
{
   if(!InpApplyProTheme) return;

   // پس‌زمینه سرمه‌ای/دودی ملایم برای محافظت از چشم
   color tvDarkBg       = C'20,24,35';

   ChartSetInteger(0, CHART_COLOR_BACKGROUND, tvDarkBg);
   ChartSetInteger(0, CHART_COLOR_FOREGROUND, clrSilver);
   ChartSetInteger(0, CHART_COLOR_GRID, clrNONE);
   ChartSetInteger(0, CHART_SHOW_GRID, false);
   ChartSetInteger(0, CHART_SHOW_VOLUMES, CHART_VOLUME_HIDE);
   ChartSetInteger(0, CHART_SHOW_ASK_LINE, false);
   ChartSetInteger(0, CHART_SHOW_LAST_LINE, false);

   // بازگرداندن رنگ کندل‌ها دقیقاً به سفید ملایم و خاکستری مورد علاقه کاربر
   ChartSetInteger(0, CHART_COLOR_CHART_UP,    clrSilver);
   ChartSetInteger(0, CHART_COLOR_CHART_DOWN,  clrDimGray);
   ChartSetInteger(0, CHART_COLOR_CANDLE_BULL, clrWhite);
   ChartSetInteger(0, CHART_COLOR_CANDLE_BEAR, (color)0x352B28);
   ChartSetInteger(0, CHART_COLOR_CHART_LINE,  clrLightSlateGray);
   ChartSetInteger(0, CHART_MODE, CHART_CANDLES);
}

//+------------------------------------------------------------------+
//| Render Final Boxes with Smart Filtering and Multi-Tagging        |
//+------------------------------------------------------------------+
void RenderFinalBoxes(const datetime &chartTime[], int ratesTotal)
{
   if(!InpShowBoxes || !g_boxesVisible)
   {
      // حذف قطعی تمام مستطیل‌های باکس و برچسب‌های متناظر از روی چارت
      ObjectsDeleteAll(0, FP_PREFIX + "BOX_");
      ObjectsDeleteAll(0, FP_PREFIX + "LBL_");
      return;
   }

   datetime liveTime = (ratesTotal > 0) ? chartTime[ratesTotal - 1] : 0;

   for(int b = 0; b < g_boxCount; b++)
   {
      // نادیده گرفتن باکس‌های حذف‌شده توسط فیلتر هم‌پوشانی یا نامعتبر
      if(g_drawnBoxes[b].top <= 0 || g_drawnBoxes[b].bottom <= 0)
         continue;

      // نادیده گرفتن باکس‌های قدیمی‌تر از تاریخ شروع واحد
      if(g_effectiveStartDate > 0 && g_drawnBoxes[b].t1 < g_effectiveStartDate)
         continue;

      bool isMacro = g_drawnBoxes[b].isMacro;
      bool hasRSTags = (ArraySize(g_drawnBoxes[b].rsTags) > 0);

      // فیلتر نحوه نمایش باکس‌ها روی چارت
      if(InpBoxDisplayFilter == BOX_FILTER_NONE)
         continue;

      if(InpBoxDisplayFilter == BOX_FILTER_TRADED_ONLY)
      {
         // فقط باکس‌هایی که معامله واقعی روی آن‌ها ثبت شده است رسم شوند
         if(!g_drawnBoxes[b].hasTradeEntered)
            continue;
      }
      else if(InpBoxDisplayFilter == BOX_FILTER_SETUPS_ONLY)
      {
         // فقط باکس‌های دارای الگوی ساختاری (LS, RS, OInner, Swap) رسم شوند
         if(!hasRSTags)
            continue;
      }
      // در حالت BOX_FILTER_ALL تمامی باکس‌ها (شامل سویینگ‌های ساده) رسم می‌شوند

      color drawClr = g_drawnBoxes[b].baseColor;
      int drawWidth = g_drawnBoxes[b].baseWidth;
      string roleTag = "";
      string shortRoleTag = "";

      ENUM_LINE_STYLE drawStyle = g_drawnBoxes[b].baseStyle;

      if(hasRSTags)
      {
         bool isLS = false;
         bool isRS = false;
         bool isOI = false;
         bool isSwap = false;
         string swapTag = "";

         for(int t = 0; t < ArraySize(g_drawnBoxes[b].rsTags); t++)
         {
            string tg = g_drawnBoxes[b].rsTags[t];
            if(tg == "LS") isLS = true;
            else if(tg == "RS") isRS = true;
            else if(tg == "OInner") isOI = true;
            else if(StringFind(tg, "S-") == 0)
            {
               isSwap = true;
               swapTag += (swapTag == "" ? "" : "+") + tg;
            }
         }

         string tagCombo = "";
         if(isLS)
         {
            string lsDir = g_drawnBoxes[b].isLSBull ? "-BU" : "-BE";
            tagCombo += (tagCombo == "" ? "LS" + lsDir : " > LS" + lsDir);
         }
         if(isOI)
         {
            string oiDir = g_drawnBoxes[b].isOInnerBull ? "-BU" : "-BE";
            tagCombo += (tagCombo == "" ? "OInner" + oiDir : " > OInner" + oiDir);
         }
         if(isRS)
         {
            string rsDir = g_drawnBoxes[b].isRSBull ? "-BU" : "-BE";
            tagCombo += (tagCombo == "" ? "RS" + rsDir : " > RS" + rsDir);
         }
         if(isSwap)
         {
            string swDir = g_drawnBoxes[b].isSwapBull ? "-BU" : "-BE";
            string fullSwap = swapTag + swDir;
            tagCombo += (tagCombo == "" ? fullSwap : " > " + fullSwap);
         }

         bool isBull = false;
         if(isSwap) isBull = g_drawnBoxes[b].isSwapBull;
         else if(isOI) isBull = g_drawnBoxes[b].isOInnerBull;
         else if(isRS) isBull = g_drawnBoxes[b].isRSBull;
         else if(isLS) isBull = g_drawnBoxes[b].isLSBull;
         else isBull = g_drawnBoxes[b].isBullish;

         roleTag = tagCombo;

         if(isSwap) shortRoleTag = swapTag + (g_drawnBoxes[b].isSwapBull ? "-BU" : "-BE");
         else if(isLS && isRS) shortRoleTag = "LS+RS" + (g_drawnBoxes[b].isRSBull ? "-BU" : "-BE");
         else if(isOI && isRS) shortRoleTag = "OInner+RS" + (g_drawnBoxes[b].isRSBull ? "-BU" : "-BE");
         else if(isLS && isOI) shortRoleTag = "LS+OInner" + (g_drawnBoxes[b].isOInnerBull ? "-BU" : "-BE");
         else if(isOI) shortRoleTag = "OInner" + (g_drawnBoxes[b].isOInnerBull ? "-BU" : "-BE");
         else if(isLS) shortRoleTag = "LS" + (g_drawnBoxes[b].isLSBull ? "-BU" : "-BE");
         else if(isRS) shortRoleTag = "RS" + (g_drawnBoxes[b].isRSBull ? "-BU" : "-BE");

         if(isSwap)
         {
            if(StringFind(swapTag, "S-OInner") >= 0)
               drawClr = isBull ? clrMediumSpringGreen : clrTomato;
            else if(StringFind(swapTag, "S-RS") >= 0)
               drawClr = isBull ? clrCyan : clrCoral;
            else if(StringFind(swapTag, "S-LS") >= 0)
               drawClr = isBull ? clrSpringGreen : clrHotPink;
            else
               drawClr = isBull ? InpSwapColorBull : InpSwapColorBear;

            drawWidth = InpSwapBoxWidth;
            drawStyle = STYLE_DOT;
         }
         else if(isLS && isRS)
         {
            drawClr   = isBull ? InpComboColorBull : InpComboColorBear;
            drawWidth = 3;
            drawStyle = STYLE_DASH;
         }
         else if(isOI && isRS)
         {
            drawClr   = isBull ? InpRSColorBull : InpRSColorBear;
            drawWidth = InpBreakoutFlagWidth;
            drawStyle = STYLE_DASH;
         }
         else if(isLS)
         {
            drawClr   = isBull ? InpLSColorBull : InpLSColorBear;
            drawWidth = InpPreIPWidth;
            drawStyle = STYLE_DASH;
         }
         else if(isOI)
         {
            drawClr   = isBull ? InpOInnerColorBull : InpOInnerColorBear;
            drawWidth = InpOInnerWidth;
            drawStyle = STYLE_DASH;
         }
         else if(isRS)
         {
            drawClr   = isBull ? InpRSColorBull : InpRSColorBear;
            drawWidth = InpBreakoutFlagWidth;
            drawStyle = STYLE_DOT;
         }
      }

      DrawHollowBox(g_drawnBoxes[b].boxName,
                    g_drawnBoxes[b].t1,
                    g_drawnBoxes[b].top,
                    g_drawnBoxes[b].t2,
                    g_drawnBoxes[b].bottom,
                    drawClr,
                    drawWidth,
                    drawStyle);

      if(InpShowLabel)
      {
         double labelPrice = g_drawnBoxes[b].top + (g_drawnBoxes[b].top - g_drawnBoxes[b].bottom) * 0.08;
         datetime labelTime = (datetime)((g_drawnBoxes[b].t1 + g_drawnBoxes[b].t2) / 2);
         string lblName = FP_PREFIX + "LBL_" + g_drawnBoxes[b].boxName;

         string displayTag = (InpLabelFormat == LABEL_CONCISE && shortRoleTag != "") ? shortRoleTag : roleTag;

         string lblText = g_drawnBoxes[b].tfTag;
         if(displayTag != "")
            lblText = g_drawnBoxes[b].tfTag + " [" + displayTag + "]";
         else
         {
            string flDir = g_drawnBoxes[b].isBullish ? "BU" : "BE";
            lblText = g_drawnBoxes[b].tfTag + " [" + flDir + "]";
         }

         if(ObjectFind(0, lblName) >= 0) ObjectDelete(0, lblName);
         ObjectCreate(0, lblName, OBJ_TEXT, 0, labelTime, labelPrice);
         ObjectSetString(0, lblName, OBJPROP_TEXT, lblText);
         ObjectSetInteger(0, lblName, OBJPROP_COLOR, drawClr);
         ObjectSetInteger(0, lblName, OBJPROP_FONTSIZE, 8);
         ObjectSetInteger(0, lblName, OBJPROP_ANCHOR, ANCHOR_LOWER);
         ObjectSetInteger(0, lblName, OBJPROP_SELECTABLE, false);
      }
   }
}

//+------------------------------------------------------------------+
//| Render Final Independent Pivots Markers                          |
//+------------------------------------------------------------------+
void RenderFinalIndependentPivots(const datetime &chartTime[], const double &chartHigh[], const double &chartLow[], int ratesTotal)
{
   if(!InpHighlightIndepPivots) return;

   for(int k = 0; k < g_indepCount; k++)
   {
      string combinedTFs = "";
      for(int t = 0; t < ArraySize(g_indepPivots[k].tfTags); t++)
      {
         combinedTFs += (t > 0 ? "/" : "") + g_indepPivots[k].tfTags[t];
      }

      string lblText = (g_indepPivots[k].hasIP ? "IP " : "") + combinedTFs;
      string ipName = FP_PREFIX + "IP_" + IntegerToString((int)g_indepPivots[k].time) + "_" + (g_indepPivots[k].isHigh ? "H" : "L") + "_" + IntegerToString(k);
      
      if(ObjectFind(0, ipName) >= 0) ObjectDelete(0, ipName);
      ObjectCreate(0, ipName, OBJ_ARROW, 0, g_indepPivots[k].time, g_indepPivots[k].price);
      ObjectSetInteger(0, ipName, OBJPROP_ARROWCODE, InpIndepMarkCode);
      ObjectSetInteger(0, ipName, OBJPROP_COLOR,      g_indepPivots[k].clr);
      ObjectSetInteger(0, ipName, OBJPROP_WIDTH,      InpIndepMarkWidth);
      ObjectSetInteger(0, ipName, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, ipName, OBJPROP_ANCHOR, (g_indepPivots[k].isHigh ? ANCHOR_BOTTOM : ANCHOR_TOP));

      if(InpIndepShowLabel)
      {
         string lblName = ipName + "_LBL";
         if(ObjectFind(0, lblName) >= 0) ObjectDelete(0, lblName);
         ObjectCreate(0, lblName, OBJ_TEXT, 0, g_indepPivots[k].time, g_indepPivots[k].price);
         ObjectSetString(0, lblName, OBJPROP_TEXT, lblText);
         ObjectSetInteger(0, lblName, OBJPROP_COLOR, g_indepPivots[k].clr);
         ObjectSetInteger(0, lblName, OBJPROP_FONTSIZE, 8);
         ObjectSetInteger(0, lblName, OBJPROP_ANCHOR, (g_indepPivots[k].isHigh ? ANCHOR_LOWER : ANCHOR_UPPER));
         ObjectSetInteger(0, lblName, OBJPROP_SELECTABLE, false);
      }
   }
}

//+------------------------------------------------------------------+
//| Clear Box Highlight                                              |
//+------------------------------------------------------------------+
void ClearBoxHighlight()
{
   if(g_selectedBoxName != "" && ObjectFind(0, g_selectedBoxName) >= 0)
   {
      ObjectSetInteger(0, g_selectedBoxName, OBJPROP_COLOR, g_origBoxColor);
      ObjectSetInteger(0, g_selectedBoxName, OBJPROP_WIDTH, g_origBoxWidth);
      ObjectSetInteger(0, g_selectedBoxName, OBJPROP_STYLE, g_origBoxStyle);
      ObjectSetInteger(0, g_selectedBoxName, OBJPROP_FILL,  false);
      ObjectSetInteger(0, g_selectedBoxName, OBJPROP_BACK,  false);
   }

   if(g_selectedExtBoxName != "" && ObjectFind(0, g_selectedExtBoxName) >= 0)
   {
      ObjectSetInteger(0, g_selectedExtBoxName, OBJPROP_COLOR, g_origBoxColor);
      ObjectSetInteger(0, g_selectedExtBoxName, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, g_selectedExtBoxName, OBJPROP_FILL,  false);
      ObjectSetInteger(0, g_selectedExtBoxName, OBJPROP_BACK,  false);
   }

   ObjectsDeleteAll(0, FP_PREFIX + "CLICK_TRADE_");

   g_selectedBoxName    = "";
   g_selectedExtBoxName = "";
   Comment("");
}

//+------------------------------------------------------------------+
//| Highlight Box on Click with Glowing Illumination & Fill          |
//+------------------------------------------------------------------+
void HighlightBox(int boxIdx)
{
   if(boxIdx < 0 || boxIdx >= g_boxCount) return;

   string boxName = g_drawnBoxes[boxIdx].boxName;
   if(boxName == g_selectedBoxName)
   {
      ClearBoxHighlight();
      ChartRedraw(0);
      return;
   }

   ClearBoxHighlight();

   if(ObjectFind(0, boxName) >= 0)
   {
      g_selectedBoxName = boxName;
      g_origBoxColor    = (color)ObjectGetInteger(0, boxName, OBJPROP_COLOR);
      g_origBoxWidth    = (int)ObjectGetInteger(0, boxName, OBJPROP_WIDTH);
      g_origBoxStyle    = (ENUM_LINE_STYLE)ObjectGetInteger(0, boxName, OBJPROP_STYLE);

      ObjectSetInteger(0, boxName, OBJPROP_COLOR, clrGold);
      ObjectSetInteger(0, boxName, OBJPROP_WIDTH, 3);
      ObjectSetInteger(0, boxName, OBJPROP_STYLE, STYLE_SOLID);
      ObjectSetInteger(0, boxName, OBJPROP_FILL,  false);
      ObjectSetInteger(0, boxName, OBJPROP_BACK,  false);

      ShowTradeSetupForBox(boxIdx);
   }

   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| رسم بج نسخه در گوشه بالا-راست چارت                               |
//+------------------------------------------------------------------+
void RenderVersionBadge(const string moduleName, const string version = FLAGPRO_VERSION)
{
   bool isEA = (StringFind(moduleName, "EA") >= 0 || StringFind(moduleName, "Trader") >= 0);
   string objName = FP_PREFIX + (isEA ? "VER_EA" : "VER_IND");
   if(ObjectFind(0, objName) < 0)
   {
      ObjectCreate(0, objName, OBJ_LABEL, 0, 0, 0);
   }
   int yDist = 20;
   if(isEA && ObjectFind(0, FP_PREFIX + "VER_IND") >= 0)
      yDist = 42;

   ObjectSetInteger(0, objName, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
   ObjectSetInteger(0, objName, OBJPROP_XDISTANCE, 20);
   ObjectSetInteger(0, objName, OBJPROP_YDISTANCE, yDist);
   ObjectSetInteger(0, objName, OBJPROP_ANCHOR, ANCHOR_RIGHT_UPPER);
   ObjectSetString(0, objName, OBJPROP_TEXT, StringFormat("⚡ %s %s", moduleName, version));
   ObjectSetString(0, objName, OBJPROP_FONT, "Segoe UI Black");
   ObjectSetInteger(0, objName, OBJPROP_FONTSIZE, 10);
   ObjectSetInteger(0, objName, OBJPROP_COLOR, isEA ? clrGold : clrAquamarine);
   ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, objName, OBJPROP_BACK, false);
   ObjectSetInteger(0, objName, OBJPROP_HIDDEN, true);
}

//+------------------------------------------------------------------+
//| رسم بج وضعیت همگام‌سازی تستر (Auto-Sync)                         |
//+------------------------------------------------------------------+
void RenderSyncStatusBadge()
{
   string objName = FP_PREFIX + "SYNC_BADGE";
   if(!g_syncActive || g_syncScenarioName == "")
   {
      ObjectDelete(0, objName);
      return;
   }

   if(ObjectFind(0, objName) < 0)
      ObjectCreate(0, objName, OBJ_LABEL, 0, 0, 0);

   int yDist = (ObjectFind(0, FP_PREFIX + "VER_EA") >= 0) ? 64 : 42;

   ObjectSetInteger(0, objName, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
   ObjectSetInteger(0, objName, OBJPROP_XDISTANCE, 20);
   ObjectSetInteger(0, objName, OBJPROP_YDISTANCE, yDist);
   ObjectSetInteger(0, objName, OBJPROP_ANCHOR, ANCHOR_RIGHT_UPPER);
   string syncText = StringFormat("🔄 تستر فعال: %s (%s)", g_syncScenarioName, (ActiveOnlyTradeKings() ? "👑 سلاطین" : "همه ستاپ‌ها"));
   ObjectSetString(0, objName, OBJPROP_TEXT, syncText);
   ObjectSetString(0, objName, OBJPROP_FONT, "Segoe UI Semibold");
   ObjectSetInteger(0, objName, OBJPROP_FONTSIZE, 9);
   ObjectSetInteger(0, objName, OBJPROP_COLOR, C'80,220,255'); // فیروزه‌ای درخشان
   ObjectSetInteger(0, objName, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, objName, OBJPROP_BACK, false);
   ObjectSetInteger(0, objName, OBJPROP_HIDDEN, true);
}

