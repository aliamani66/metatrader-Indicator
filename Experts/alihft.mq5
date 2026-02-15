//+------------------------------------------------------------------+
//|                                                       alihft.mq5 |
//|                                  Copyright 2026, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"

#include <Trade\Trade.mqh>

CTrade *Trade;
CPositionInfo PositionInfo;
COrderInfo OrderInfo;

enum EnumRisk {UseFixedLot,UseBalanceLot};


input group "GENERAL PARAMETER"
input int EAMagic = 122332;
input string MySymbol = "EURUSD";
input ENUM_TIMEFRAMES MyTimeFrame = PERIOD_M1;
input int MaxSlippage = 1;

input group "SPRAD FILTER INPUTS"
input bool UseSpreadFilter = false;
input double MaxSpreadPoints = 0.5;

input group "TRADE MANAGEMENT"
input int StopLoss = 1;
input int PendingDistance = 2;

input group "RISK INPUTS"
input EnumRisk LotUsed = UseFixedLot;
input double BalanceIncrease = 1000;
input double VolumeIncrease = 0.1;
input double FixedLot = 0.1;

input group "TIMEZONE INPUTS"
input bool UseTimeZoneFilter1 = true;
input int StartHour1 = 10;
input int StartMinutes1 = 00;
input int EndHour1 = 10;
input int EndMinute1 = 30;

input bool UseTimeZoneFilter2 = true;
input int StartHour2 = 15;
input int StartMinutes2 = 00;
input int EndHour2 = 15;
input int EndMinute2 = 30;

input group "NEWS FILTER INPUT"
input bool UseNewsFilter = false;
input ENUM_CALENDAR_EVENT_IMPORTANCE NewsImportance = CALENDAR_IMPORTANCE_HIGH;
input uint MinutesToNews = 15;

int StartTimeSeconds1,StartTimeSeconds2,EndTimeSeconds1,EndTimeSeconds2,MyDigits;
double LotMax,LotMin,LotStep,MyPoint,Ask,Bid,BuyEntryPrice,SellEntryPrice,TradeGap,STP;
string BuyComment = "Buy", SellComment = "Sell";




//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double LotSize()
  {
   double Lot;
   if(LotUsed == UseFixedLot)
      Lot= FixedLot;
   else
      Lot = NormalizeDouble(VolumeIncrease*AccountInfoDouble(ACCOUNT_BALANCE)/BalanceIncrease,2);
   Lot = MathRound(Lot/LotStep)*LotStep;
   if(Lot>LotMax)
      Lot = LotMax;
   if(Lot < LotMin)
      Lot = LotMin;
   return Lot;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int NumTrades(const ENUM_POSITION_TYPE PosType)
  {
   int Num = 0;
   for(int i=PositionsTotal()-1;i>0;i--)
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
int TotalTrades()
  {
   return NumTrades(POSITION_TYPE_BUY) + NumTrades(POSITION_TYPE_SELL);
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int NumPending(const string OrderComment)
  {
   int Num = 0;
   for(int i=0;i<OrdersTotal();i++)
     {
      if(!OrderInfo.SelectByIndex(i))
         continue;
      if(OrderInfo.Magic()!=EAMagic)
         continue;
      if(OrderInfo.Symbol()!=MySymbol)
         continue;
      if(OrderInfo.Comment()!= OrderComment)
         continue;
      Num++;
     }
   return Num;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool TradeSession1()
  {

   if(!UseTimeZoneFilter1)
      return true;
   datetime MidNight = iTime(MySymbol, PERIOD_D1,0);
   datetime StartingTime = MidNight + (datetime)StartTimeSeconds1;
   datetime CurrentTime = TimeCurrent();
   datetime EndTime = MidNight + (datetime)EndTimeSeconds1;
   if(CurrentTime > StartingTime && CurrentTime < EndTime)
      return true;
   return false;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool TradeSession2()
  {

   if(!UseTimeZoneFilter2)
      return true;
   datetime MidNight = iTime(MySymbol, PERIOD_D1,0);
   datetime StartingTime = MidNight + (datetime)StartTimeSeconds2;
   datetime CurrentTime = TimeCurrent();
   datetime EndTime = MidNight + (datetime)EndTimeSeconds2;
   if(CurrentTime > StartingTime && CurrentTime < EndTime)
      return true;
   return false;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool SpradGood()
  {
   if(!UseSpreadFilter)
      return true;
   if(SymbolInfoInteger(MySymbol,SYMBOL_SPREAD)<=MaxSpreadPoints)
      return true;
   return false;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool NewsPresent(ENUM_CALENDAR_EVENT_IMPORTANCE Importance, uint Seconds = 900)
  {
   if(!UseNewsFilter)
      return true;
   MqlCalendarValue Values[];
   ResetLastError();
   int NewsTotal = CalendarValueHistory(Values, TimeCurrent(), TimeCurrent()+Seconds, NULL, NULL);
   if(NewsTotal<=0)
     {
      if(GetLastError() > 0)
        {
         Print("Failed to get news because of error :" + (string)GetLastError());
        }
      else
        {
         Print("There is no news for the current symbol");
         return false;
        }
     }
   for(int i=0;i<NewsTotal;i++)
     {
      MqlCalendarEvent Event;
      CalendarEventById(Values[i].event_id,Event);

      MqlCalendarCountry Country;
      CalendarCountryById(Event.country_id,Country);

      if(StringFind(MySymbol,Country.currency) >-1)
        {
         if(Event.importance == Importance)
            if(TimeCurrent()-Values[i].time<Seconds)
               return true;
        }

     }
   return false;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void EnterTrades()
  {
   if(TotalTrades()!=0)
      return;

   double Margin;
   if(NumPending(BuyComment) == 0)
     {
      BuyEntryPrice = Ask + TradeGap;
      double BuySL = BuyEntryPrice - STP;
      if(OrderCalcMargin(ORDER_TYPE_BUY,MySymbol,LotSize(),Ask,Margin) && Margin <= AccountInfoDouble(ACCOUNT_MARGIN_FREE))
         Trade.BuyStop(LotSize(),BuyEntryPrice,MySymbol,BuySL,0,ORDER_TIME_GTC,0,BuyComment);

     }
   if(NumPending(SellComment) == 0)
     {
      SellEntryPrice = Ask + TradeGap;
      double SellSL = BuyEntryPrice + STP;
      if(OrderCalcMargin(ORDER_TYPE_BUY,MySymbol,LotSize(),Ask,Margin) && Margin <= AccountInfoDouble(ACCOUNT_MARGIN_FREE))
         Trade.SellStop(LotSize(),SellEntryPrice,MySymbol,SellSL,0,ORDER_TIME_GTC,0,SellComment);

     }

  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void DeletePending(const string OrderComment)
  {

   for(int i=OrdersTotal();i>0;i--)
     {
      ulong Ticket = OrderInfo.Ticket();
      if(!OrderInfo.Select(Ticket))
         continue;
      if(OrderInfo.Comment()!= OrderComment)
         continue;
      if(!Trade.OrderDelete(Ticket))
         Print("Failed to delete pending order because : ", GetLastError());
     }
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void TrailingStop()
  {

   if(TotalTrades()==0)
      return;
   for(int i=PositionsTotal();i>=0;i--)
     {
      if(!PositionInfo.SelectByIndex(i))
         continue;
      if(PositionInfo.Magic()!= EAMagic)
         continue;
      if(PositionInfo.Symbol() != MySymbol)
         continue;
      double CurrentSL = PositionInfo.StopLoss();
      double OpeningPrice = PositionInfo.PriceOpen();
      double PositionTP = PositionInfo.TakeProfit();
      double CurrentPrice = PositionInfo.PriceCurrent();
      double TrailBy = STP;
      double BuyTrailPrice = NormalizeDouble(OpeningPrice+STP, MyDigits);
      double SellTrailPrice = NormalizeDouble(OpeningPrice-STP, MyDigits);

      if(PositionInfo.PositionType() == POSITION_TYPE_BUY)
         if(CurrentPrice < BuyTrailPrice)
            continue;
      if(PositionInfo.PositionType() == POSITION_TYPE_SELL)
         if(CurrentPrice > SellTrailPrice)
            continue;

      double NewSL = PositionInfo.PositionType() == POSITION_TYPE_BUY?CurrentPrice-TrailBy:CurrentPrice+TrailBy;
      if(PositionInfo.PositionType() == POSITION_TYPE_BUY && NewSL <= CurrentSL)
         continue;

      if(PositionInfo.PositionType() == POSITION_TYPE_SELL && NewSL >= CurrentSL)
         continue;
      ulong Ticket = PositionInfo.Ticket();

      if(!Trade.PositionModify(Ticket,NewSL,PositionTP))
         Alert("Error Modifying Position due too:", GetLastError());
     }
  }
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
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

   Trade = new CTrade;
   Trade.SetExpertMagicNumber(EAMagic);
   Trade.SetDeviationInPoints(MaxSlippage*10);

   LotMax = SymbolInfoDouble(MySymbol, SYMBOL_VOLUME_MAX);
   LotMin = SymbolInfoDouble(MySymbol,SYMBOL_VOLUME_MIN);
   LotStep = SymbolInfoDouble(MySymbol,SYMBOL_VOLUME_STEP);

   StartTimeSeconds1=(60*60*StartHour1)+(60*StartMinutes1);
   StartTimeSeconds2=(60*60*StartHour2)+(60*StartMinutes2);
   EndTimeSeconds1= (60*60*EndHour1)+(60*EndMinute1);
   EndTimeSeconds2= (60*60*EndHour2)+(60*EndMinute2);

   MyPoint =SymbolInfoDouble(MySymbol,SYMBOL_POINT);
   MyDigits = (int)SymbolInfoInteger(MySymbol,SYMBOL_DIGITS);

   TradeGap = PendingDistance*10*MyPoint;
   STP = StopLoss*10*MyPoint;

//---
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
// Comment("Spread = ", SymbolInfoInteger(MySymbol,SYMBOL_SPREAD));
   Ask = SymbolInfoDouble(MySymbol,SYMBOL_ASK);
   Bid = SymbolInfoDouble(MySymbol,SYMBOL_BID);

   if((TradeSession1() || TradeSession2()) && !NewsPresent(NewsImportance,MinutesToNews*60))
      if(SpradGood())
         EnterTrades();
   if(NumTrades(POSITION_TYPE_BUY)>0 && NumPending(SellComment) > 0)
      DeletePending(SellComment);
   if(NumTrades(POSITION_TYPE_SELL)>0 && NumPending(BuyComment) > 0)
      DeletePending(BuyComment);
   TrailingStop();

  }
//+------------------------------------------------------------------+
