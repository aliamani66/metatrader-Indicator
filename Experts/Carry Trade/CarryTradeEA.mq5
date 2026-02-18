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
double MaxSpreadPoints = MaxSpread * 10 ;

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
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
//---

  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
//---

  }
//+------------------------------------------------------------------+
