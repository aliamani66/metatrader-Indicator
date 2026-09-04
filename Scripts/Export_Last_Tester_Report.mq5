//+------------------------------------------------------------------+
//|                                     Export_Last_Tester_Report.mq5|
//|                        Copyright 2026, FlagPro Master Strategy   |
//|                     https://github.com/aliamani55/mql5           |
//+------------------------------------------------------------------+
#property copyright "FlagPro Strategy Tester Exporter"
#property link      "https://github.com/aliamani55/mql5"
#property version   "1.00"
#property script_show_inputs

input string   InpReportFolder = "FlagPro_TesterReports"; // 📁 نام پوشه ذخیره در MQL5/Files
input double   InpDefaultLot   = 0.01;                  // 📦 حجم مبنا (جهت نرمال‌سازی پیپ)

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
{
   if(!HistorySelect(0, TimeCurrent()))
   {
      Print("❌ خطا در بارگذاری تاریخچه معاملات: ", GetLastError());
      return;
   }

   int totalDeals = HistoryDealsTotal();
   if(totalDeals <= 0)
   {
      Print("⚠️ هیچ معامله‌ای در تاریخچه تستر یا حساب یافت نشد.");
      return;
   }

   FolderCreate(InpReportFolder);
   double pipSize = (_Digits == 3 || _Digits == 5) ? _Point * 10.0 : _Point;

   string symClean = _Symbol;
   StringReplace(symClean, "!", "");
   StringReplace(symClean, "#", "");

   string filenameJson = InpReportFolder + "\\FlagPro_Tester_Export_" + symClean + "_" + TimeToString(TimeCurrent(), TIME_DATE) + ".json";
   string filenameCsv  = InpReportFolder + "\\FlagPro_Tester_Export_" + symClean + "_" + TimeToString(TimeCurrent(), TIME_DATE) + ".csv";

   int hCsv = FileOpen(filenameCsv, FILE_WRITE | FILE_CSV | FILE_ANSI, ",");
   if(hCsv != INVALID_HANDLE)
   {
      FileWrite(hCsv, "DealTicket", "PositionID", "OrderTicket", "Time", "Type", "Volume", "Price", "ProfitUSD", "ProfitPips", "Comment");
   }

   int hJson = FileOpen(filenameJson, FILE_WRITE | FILE_TXT | FILE_UNICODE);
   if(hJson == INVALID_HANDLE)
   {
      Print("❌ خطا در ایجاد فایل گزارش JSON: ", GetLastError());
      if(hCsv != INVALID_HANDLE) FileClose(hCsv);
      return;
   }

   FileWriteString(hJson, "{\n");
   FileWriteString(hJson, "  \"symbol\": \"" + _Symbol + "\",\n");
   FileWriteString(hJson, "  \"exportedAt\": \"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_MINUTES|TIME_SECONDS) + "\",\n");
   FileWriteString(hJson, "  \"deals\": [\n");

   int dealCount = 0;
   double totalProfitUSD = 0.0;
   double totalProfitPips = 0.0;
   int winCount = 0;
   int lossCount = 0;

   for(int i = 0; i < totalDeals; i++)
   {
      ulong dt = HistoryDealGetTicket(i);
      if(dt <= 0) continue;

      long entry = HistoryDealGetInteger(dt, DEAL_ENTRY);
      if(entry != DEAL_ENTRY_OUT) continue; // فقط معاملات تسویه و خروج

      string dealSym = HistoryDealGetString(dt, DEAL_SYMBOL);
      if(dealSym != "" && dealSym != _Symbol) continue;

      ulong posId = (ulong)HistoryDealGetInteger(dt, DEAL_POSITION_ID);
      ulong ordId = (ulong)HistoryDealGetInteger(dt, DEAL_ORDER);
      datetime dealTime = (datetime)HistoryDealGetInteger(dt, DEAL_TIME);
      long dealType = HistoryDealGetInteger(dt, DEAL_TYPE);
      double vol = HistoryDealGetDouble(dt, DEAL_VOLUME);
      double price = HistoryDealGetDouble(dt, DEAL_PRICE);
      double profit = HistoryDealGetDouble(dt, DEAL_PROFIT);
      string comment = HistoryDealGetString(dt, DEAL_COMMENT);

      double pips = 0.0;
      if(dealType == DEAL_TYPE_BUY) // بستن پوزیشن SELL با خرید
      {
         pips = (profit / (vol * 100000.0)) / _Point;
      }
      else
      {
         pips = (profit / (vol * 100000.0)) / _Point;
      }

      totalProfitUSD += profit;
      totalProfitPips += (profit / 0.1); // تقریبی برای 0.01 لات
      if(profit > 0) winCount++;
      else lossCount++;

      if(hCsv != INVALID_HANDLE)
      {
         FileWrite(hCsv, IntegerToString(dt), IntegerToString(posId), IntegerToString(ordId),
                   TimeToString(dealTime, TIME_DATE|TIME_MINUTES|TIME_SECONDS),
                   (dealType == DEAL_TYPE_BUY ? "BUY" : "SELL"),
                   DoubleToString(vol, 2), DoubleToString(price, _Digits),
                   DoubleToString(profit, 2), DoubleToString(pips, 1), comment);
      }

      if(dealCount > 0) FileWriteString(hJson, ",\n");
      string dJson = StringFormat("    {\"ticket\": %d, \"posId\": %d, \"time\": \"%s\", \"side\": \"%s\", \"vol\": %.2f, \"price\": %.5f, \"profit\": %.2f, \"comment\": \"%s\"}",
                                  dt, posId, TimeToString(dealTime, TIME_DATE|TIME_MINUTES|TIME_SECONDS),
                                  (dealType == DEAL_TYPE_BUY ? "BUY" : "SELL"), vol, price, profit, comment);
      FileWriteString(hJson, dJson);
      dealCount++;
   }

   FileWriteString(hJson, "\n  ],\n");
   FileWriteString(hJson, StringFormat("  \"summary\": {\"totalDeals\": %d, \"winCount\": %d, \"lossCount\": %d, \"totalProfitUSD\": %.2f}\n",
                                       dealCount, winCount, lossCount, totalProfitUSD));
   FileWriteString(hJson, "}\n");

   FileClose(hJson);
   if(hCsv != INVALID_HANDLE) FileClose(hCsv);

   PrintFormat("🎉 گزارش تستر با موفقیت استخراج شد! تعداد %d معامله خروج در پوشه MQL5/Files/%s ذخیره گردید.",
               dealCount, InpReportFolder);
}
