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

enum EnumRisk{UseFixedLot,UseBalanceLot};


input group "GENERAL PARAMETER"
input int EAMagic = 122332;
input string MySymbol = "EURUSD";
input ENUM_TIMEFRAMES MyTimeFrame = PERIOD_M1;
input int MaxSlippage = 1;

input group "SPRAD FILTER INPUTS"
input bool UseSpreadFilter = false; 
input double MaxSpreadPoints = 0.5;


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

int StartTimeSeconds1,StartTimeSeconds2,EndTimeSeconds1,EndTimeSeconds2;



double LotMax,LotMin,LotStep;



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


int NumTrades(const ENUM_POSITION_TYPE PosType) { 
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

int TotalTrades(){
   return NumTrades(POSITION_TYPE_BUY) + NumTrades(POSITION_TYPE_SELL);
}


int NumPending(const string OrderComment){
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

bool TradeSession1(){

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


bool TradeSession2(){

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

bool SpradGood(){
   if(!UseSpreadFilter)
      return true;
   if(SymbolInfoInteger(MySymbol,SYMBOL_SPREAD)<=MaxSpreadPoints)
      return true;
   return false; 
}


bool NewsPresent(ENUM_CALENDAR_EVENT_IMPORTANCE Importance , uint Seconds = 900){
   if(!UseNewsFilter)
      return true;
   MqlCalendarValue Values[];
   ResetLastError();
   int NewsTotal = CalendarValueHistory(Values, TimeCurrent(), TimeCurrent()+Seconds, NULL, NULL);
   if(NewsTotal<=0)
   {
      if(GetLastError() > 0){
         Print("Failed to get news because of error :" + GetLastError() );
      } else {
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
   Comment("Spread = " , SymbolInfoInteger(MySymbol,SYMBOL_SPREAD));
   
  }
//+------------------------------------------------------------------+
