//+------------------------------------------------------------------+
//|                                                 CarryTradeEA.mq5 |
//|                                  Copyright 2025, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Ali Amani"
#property link      "https://www.mql5.com"
#property version   "1.00"

#include <Trade\Trade.mqh>

CTrade *Trade;
CPositionInfo PositionInfo;
COrderInfo OrderInfo;

input group "GENERAL INPOUT"
//high swap and low spread
input string MySymbol = "XAUUSD";
input ENUM_TIMEFRAMES PeriodTraded = PERIOD_M5;
input int EAMagic = 7667;
input int MaxSlippage = 1;

input group "SPREAD FILTER INPUTS"
input bool UseSpreadFilter = true;
input double MaxSpread = 2;
input double BalanceIncrease = 1000;
input double VolumeIncrease = 0.05;
input int StopLoss = 5;


double MaxSpreadPoints,STP
;

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int NumOfTrades(const ENUM_POSITION_TYPE PosType)
  {
   int Num = 0;
   for(int i=PositionsTotal()-1;i>=0;i--)
     {
      if(!PositionInfo.SelectByIndex(i))
         continue;
      if(PositionInfo.Magic()!= EAMagic)
         continue;
      if(PositionInfo.Symbol()!= MySymbol)
         continue;
      if(PositionInfo.PositionType() != PosType)
         continue;
      Num++;
     }
   return Num;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool SpreadGood()
  {
   if(!UseSpreadFilter)
      return true;
   if(SymbolInfoInteger(MySymbol,SYMBOL_SPREAD) <= MaxSpreadPoints)
      return true;
   return false;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool BuySignal()
  {
   if(SymbolInfoDouble(MySymbol,SYMBOL_SWAP_LONG) > 15 && NumOfTrades(POSITION_TYPE_BUY) == 0 && SpreadGood())
      return true;
   return false;

  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool SellSignal()
  {
   if(SymbolInfoDouble(MySymbol,SYMBOL_SWAP_SHORT) > 15 && NumOfTrades(POSITION_TYPE_SELL) == 0 && SpreadGood())
      return true;
   return false;

  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double LotSize()
  {
   double Lot = NormalizeDouble(VolumeIncrease*AccountInfoDouble(ACCOUNT_BALANCE)/BalanceIncrease,2);
   if(Lot > SymbolInfoDouble(MySymbol,SYMBOL_VOLUME_MAX))
      Lot = SymbolInfoDouble(MySymbol,SYMBOL_VOLUME_MAX);
   if(Lot < SymbolInfoDouble(MySymbol,SYMBOL_VOLUME_MIN))
      Lot = SymbolInfoDouble(MySymbol,SYMBOL_VOLUME_MIN);
   return Lot;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Buy()
  {
   if(BuySignal())
     {
      double ASK = SymbolInfoDouble(MySymbol, SYMBOL_ASK);
      double LotUsed = LotSize();
      if(!Trade.Buy(LotSize(), MySymbol, ASK, ASK-STP,0))
         Print("failed Buy due to :", GetLastError());
     }
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Sell()
  {
   if(SellSignal())
     {
      double BID = SymbolInfoDouble(MySymbol, SYMBOL_BID);
      double LotUsed = LotSize();
      if(!Trade.Sell(LotSize(), MySymbol, BID, BID+STP,0))
         Print("failed Sell due to :", GetLastError());
     }
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void ClosePositions()
  {
   if(NumOfTrades(POSITION_TYPE_BUY) + NumOfTrades(POSITION_TYPE_SELL) == 0)
      return;
   for(int i=PositionsTotal()-1;i>=0;i--)
     {
      if(!PositionInfo.SelectByIndex(i))
         continue;
      if(PositionInfo.Magic()!= EAMagic)
         continue;
      if(PositionInfo.Symbol()!= MySymbol)
         continue;
      if(iTime(MySymbol,PERIOD_D1,0) > PositionInfo.Time())
         Trade.PositionClose(PositionInfo.Ticket());
     }
  }
  
  
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   ChartSetInteger(0, CHART_SHOW_GRID, false);
   ChartSetInteger(0, CHART_MODE, CHART_CANDLES);
   ChartSetInteger(0, CHART_COLOR_BACKGROUND, clrBlack);
   ChartSetInteger(0, CHART_COLOR_FOREGROUND, clrWhite);
   ChartSetInteger(0, CHART_COLOR_CANDLE_BULL, clrGreen);
   ChartSetInteger(0, CHART_COLOR_CHART_UP, clrGreen);
   ChartSetInteger(0, CHART_COLOR_CANDLE_BEAR, clrWhite);
   ChartSetInteger(0, CHART_COLOR_CHART_DOWN, clrWhite);
   ChartSetInteger(0, CHART_COLOR_STOP_LEVEL, clrGold);
   ChartSetInteger(0, CHART_SHOW_VOLUMES, false);
   MaxSpreadPoints = MaxSpread *10;
   STP = StopLoss*10*SymbolInfoDouble(MySymbol,SYMBOL_POINT);

   Trade = new CTrade;
   ulong MaxSlipoagePnts = MaxSlippage * 10;
   Trade.SetDeviationInPoints(MaxSlipoagePnts);

   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
//---
   delete Trade;

  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
//---
     ClosePositions();
     MqlDateTime DateInfo;
     TimeCurrent(DateInfo);
     if(DateInfo.day_of_week == SymbolInfoInteger(MySymbol,SYMBOL_SWAP_ROLLOVER3DAYS))
     {
      DateInfo.hour =23;
      DateInfo.min = 58;
      DateInfo.sec = 00;
      
      datetime OpenTime = StructToTime(DateInfo);
      if(TimeCurrent() >= OpenTime)
      {
         Buy();
         Sell();
      }
     }
  }
//+------------------------------------------------------------------+
