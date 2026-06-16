//+------------------------------------------------------------------+
//| MarketStructure.mq5 - v10 - Simple & Stable                     |
//+------------------------------------------------------------------+
#property copyright "MS v10"
#property version   "10.0"
#property indicator_chart_window
#property indicator_buffers 4
#property indicator_plots   4

#property indicator_label1 "High Line"
#property indicator_type1  DRAW_SECTION
#property indicator_color1 clrDodgerBlue
#property indicator_width1 2

#property indicator_label2 "Low Line"
#property indicator_type2  DRAW_SECTION
#property indicator_color2 clrOrangeRed
#property indicator_width2 2

#property indicator_label3 "High Dot"
#property indicator_type3  DRAW_ARROW
#property indicator_color3 clrDodgerBlue
#property indicator_width3 3

#property indicator_label4 "Low Dot"
#property indicator_type4  DRAW_ARROW
#property indicator_color4 clrOrangeRed
#property indicator_width4 3

input int  InpPivot = 5;    // Pivot strength (کندل چپ/راست)
input bool InpLabels = true;
input int  InpLabelSize = 9;
input color InpColorHH = clrLime;
input color InpColorLL = clrRed;
input color InpColorHL = clrAqua;
input color InpColorLH = clrOrange;

double H[], L[], HD[], LD[];
string pfx;
int    lastRates = 0;

// ذخیره نقاط ساختار - حداکثر 5000 نقطه
#define MAX_PTS 5000
int    ptBar[MAX_PTS];
double ptPrice[MAX_PTS];
bool   ptHigh[MAX_PTS];
int    ptN = 0;

//+------------------------------------------------------------------+
int OnInit()
{
   SetIndexBuffer(0,H,  INDICATOR_DATA);
   SetIndexBuffer(1,L,  INDICATOR_DATA);
   SetIndexBuffer(2,HD, INDICATOR_DATA);
   SetIndexBuffer(3,LD, INDICATOR_DATA);
   PlotIndexSetInteger(2,PLOT_ARROW,108);
   PlotIndexSetInteger(3,PLOT_ARROW,108);
   PlotIndexSetDouble(0,PLOT_EMPTY_VALUE,EMPTY_VALUE);
   PlotIndexSetDouble(1,PLOT_EMPTY_VALUE,EMPTY_VALUE);
   PlotIndexSetDouble(2,PLOT_EMPTY_VALUE,EMPTY_VALUE);
   PlotIndexSetDouble(3,PLOT_EMPTY_VALUE,EMPTY_VALUE);
   pfx = "MS10_"+(string)_Period+"_";
   IndicatorSetString(INDICATOR_SHORTNAME,"Market Structure");
   lastRates = 0;
   ptN = 0;
   DelObjs();
   return INIT_SUCCEEDED;
}

void OnDeinit(const int r) { DelObjs(); }

//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   if(rates_total < InpPivot*2+3) return 0;
   // فقط وقتی کندل جدید بسته شد
   if(rates_total == lastRates) return rates_total;
   lastRates = rates_total;

   // پاک کردن
   ArrayInitialize(H, EMPTY_VALUE);
   ArrayInitialize(L, EMPTY_VALUE);
   ArrayInitialize(HD,EMPTY_VALUE);
   ArrayInitialize(LD,EMPTY_VALUE);
   DelObjs();
   ptN = 0;

   //--- گام ۱: پیدا کردن swing high/low با روش ساده
   // از index 0 (قدیمی‌ترین) تا rates_total-1 (جدیدترین)
   // آرایه‌ها از قدیم به جدید هستن (time[0]=قدیمی)

   // موقت - استفاده از آرایه‌های ثابت برای جلوگیری از کرش
   // حداکثر 5000 پیوت خام
   #define MAX_RAW 5000
   static int    rBar[MAX_RAW];
   static double rPrice[MAX_RAW];
   static bool   rHigh[MAX_RAW];
   int rN = 0;

   int lim = rates_total - InpPivot - 1;
   for(int i = InpPivot; i <= lim && rN < MAX_RAW-1; i++)
   {
      bool isH=true, isL=true;
      for(int k=1; k<=InpPivot; k++)
      {
         if(high[i-k]>=high[i]||high[i+k]>=high[i]) { isH=false; break; }
      }
      for(int k=1; k<=InpPivot; k++)
      {
         if(low[i-k]<=low[i]||low[i+k]<=low[i]) { isL=false; break; }
      }
      if(isH && !isL) { rBar[rN]=i; rPrice[rN]=high[i]; rHigh[rN]=true;  rN++; }
      else if(isL && !isH) { rBar[rN]=i; rPrice[rN]=low[i];  rHigh[rN]=false; rN++; }
   }

   if(rN < 2) { Print("MS: pivots=",rN," too few"); return rates_total; }

   //--- گام ۲: فیلتر تناوب - حذف پیوت‌های هم‌نوع متوالی
   // اگه دو High پشت سر هم: بالاترین بمونه
   // اگه دو Low  پشت سر هم: پایین‌ترین بمونه
   static int    fBar[MAX_RAW];
   static double fPrice[MAX_RAW];
   static bool   fHigh[MAX_RAW];
   int fN = 0;

   fBar[0]=rBar[0]; fPrice[0]=rPrice[0]; fHigh[0]=rHigh[0]; fN=1;
   for(int i=1; i<rN; i++)
   {
      if(rHigh[i]==fHigh[fN-1])
      {
         if( rHigh[i] && rPrice[i]>fPrice[fN-1]) { fBar[fN-1]=rBar[i]; fPrice[fN-1]=rPrice[i]; }
         if(!rHigh[i] && rPrice[i]<fPrice[fN-1]) { fBar[fN-1]=rBar[i]; fPrice[fN-1]=rPrice[i]; }
      }
      else if(fN < MAX_RAW-1)
      { fBar[fN]=rBar[i]; fPrice[fN]=rPrice[i]; fHigh[fN]=rHigh[i]; fN++; }
   }

   if(fN < 2) { Print("MS: after filter=",fN); return rates_total; }

   //--- گام ۳: فیلتر تایید ساختار
   // High تایید = وقتی Low بعدی از آخرین Low تایید شده پایین‌تر بره
   // Low  تایید = وقتی High بعدی از آخرین High تایید شده بالاتر بره
   // اگه تایید نشد: candidate رو با نقطه جدیدتر جایگزین کن

   // candidate: آخرین پیوتی که هنوز تایید نشده
   double candPrice = fPrice[0];
   int    candBar   = fBar[0];
   bool   candHigh  = fHigh[0];

   // آخرین تایید شده از هر نوع
   double lastH = -1, lastL = 1e15;
   bool   hasH  = false, hasL = false;

   // اولین نقطه همیشه ثبت می‌شه
   ptBar[ptN]=fBar[0]; ptPrice[ptN]=fPrice[0]; ptHigh[ptN]=fHigh[0]; ptN++;
   if(fHigh[0]) { lastH=fPrice[0]; hasH=true; }
   else         { lastL=fPrice[0]; hasL=true; }

   for(int i=1; i<fN && ptN<MAX_PTS-1; i++)
   {
      double p = fPrice[i];
      int    b = fBar[i];
      bool   isH = fHigh[i];

      if(isH)
      {
         // این High هست
         if(!candHigh)
         {
            // قبلی Low بود (candidate)، الان High اومد
            // آیا این High از lastH بالاتره؟ → Low candidate تایید می‌شه
            if(hasH && p > lastH)
            {
               // Low قبلی تایید شد
               ptBar[ptN]=candBar; ptPrice[ptN]=candPrice; ptHigh[ptN]=false; ptN++;
               lastL=candPrice; hasL=true;
               // الان این High رو candidate کن
               candPrice=p; candBar=b; candHigh=true;
            }
            else if(!hasH)
            {
               // اولین High
               ptBar[ptN]=candBar; ptPrice[ptN]=candPrice; ptHigh[ptN]=false; ptN++;
               lastL=candPrice; hasL=true;
               candPrice=p; candBar=b; candHigh=true;
            }
            else
            {
               // High بالاتر نیومد → Low candidate رو آپدیت نکن، این High رو نادیده بگیر
               // ولی اگه High جدید بالاتر از candidate قبلی بود، candidate رو آپدیت کن
               // (چون هنوز Low تایید نشده)
            }
         }
         else
         {
            // قبلی هم High بود (candidate)
            // بالاترین رو نگه دار
            if(p > candPrice) { candPrice=p; candBar=b; }
         }
      }
      else
      {
         // این Low هست
         if(candHigh)
         {
            // قبلی High بود (candidate)، الان Low اومد
            // آیا این Low از lastL پایین‌تره؟ → High candidate تایید می‌شه
            if(hasL && p < lastL)
            {
               // High قبلی تایید شد
               ptBar[ptN]=candBar; ptPrice[ptN]=candPrice; ptHigh[ptN]=true; ptN++;
               lastH=candPrice; hasH=true;
               candPrice=p; candBar=b; candHigh=false;
            }
            else if(!hasL)
            {
               ptBar[ptN]=candBar; ptPrice[ptN]=candPrice; ptHigh[ptN]=true; ptN++;
               lastH=candPrice; hasH=true;
               candPrice=p; candBar=b; candHigh=false;
            }
            // اگه Low بالاتر از lastL اومد: High هنوز تایید نشده، Low candidate ذخیره نمی‌کنیم
         }
         else
         {
            // قبلی هم Low بود
            if(p < candPrice) { candPrice=p; candBar=b; }
         }
      }
   }

   Print("MS: raw=",rN," filt=",fN," confirmed=",ptN);
   if(ptN < 2) return rates_total;

   //--- گام ۴: رسم
   double dH=-1, dL=1e15;
   bool fstH=true, fstL=true;

   for(int i=1; i<ptN; i++)
   {
      int    b1=ptBar[i-1], b2=ptBar[i];
      double p1=ptPrice[i-1], p2=ptPrice[i];

      if(ptHigh[i]) { H[b1]=p1; H[b2]=p2; HD[b2]=p2; }
      else          { L[b1]=p1; L[b2]=p2; LD[b2]=p2; }

      if(!InpLabels) continue;

      string txt; color tc;
      double off = p2*0.0012;
      if(off < _Point*5) off = _Point*5;

      if(ptHigh[i])
      {
         if(fstH)        { txt="H"; tc=InpColorHH; fstH=false; }
         else if(p2>dH)  { txt="HH"; tc=InpColorHH; }
         else            { txt="LH"; tc=InpColorLH; }
         dH=p2;
         string nm=pfx+"H"+IntegerToString(i);
         if(ObjectCreate(0,nm,OBJ_TEXT,0,time[b2],p2+off))
         {
            ObjectSetString(0,nm,OBJPROP_TEXT,txt);
            ObjectSetInteger(0,nm,OBJPROP_COLOR,tc);
            ObjectSetInteger(0,nm,OBJPROP_FONTSIZE,InpLabelSize);
            ObjectSetString(0,nm,OBJPROP_FONT,"Arial Bold");
            ObjectSetInteger(0,nm,OBJPROP_ANCHOR,ANCHOR_LOWER);
            ObjectSetInteger(0,nm,OBJPROP_SELECTABLE,false);
         }
      }
      else
      {
         if(fstL)        { txt="L"; tc=InpColorLL; fstL=false; }
         else if(p2<dL)  { txt="LL"; tc=InpColorLL; }
         else            { txt="HL"; tc=InpColorHL; }
         dL=p2;
         string nm=pfx+"L"+IntegerToString(i);
         if(ObjectCreate(0,nm,OBJ_TEXT,0,time[b2],p2-off))
         {
            ObjectSetString(0,nm,OBJPROP_TEXT,txt);
            ObjectSetInteger(0,nm,OBJPROP_COLOR,tc);
            ObjectSetInteger(0,nm,OBJPROP_FONTSIZE,InpLabelSize);
            ObjectSetString(0,nm,OBJPROP_FONT,"Arial Bold");
            ObjectSetInteger(0,nm,OBJPROP_ANCHOR,ANCHOR_UPPER);
            ObjectSetInteger(0,nm,OBJPROP_SELECTABLE,false);
         }
      }
   }

   ChartRedraw(0);
   return rates_total;
}

//+------------------------------------------------------------------+
void DelObjs()
{
   int n=ObjectsTotal(0,0,-1);
   for(int i=n-1;i>=0;i--)
   {
      string nm=ObjectName(0,i,0,-1);
      if(StringFind(nm,pfx)==0) ObjectDelete(0,nm);
   }
}
