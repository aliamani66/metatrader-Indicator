//+------------------------------------------------------------------+
//| Flag.mq5                                                          |
//| Flag / BOS continuation box indicator   v6.00                     |
//|                                                                    |
//| باکس‌های فقط High تا Low:                                          |
//| - فقط از High تا Low باکس رسم می‌شود                              |
//| - برای هر High باید سه تا (قبلی، جاری، بعدی) بررسی شود           |
//|                                                                    |
//| شرایط رسم باکس:                                                    |
//| 1. اگر H_next > H_cur و L_next > L_cur → صعودی → باکس از H تا L  |
//| 2. اگر H_next < H_cur و L_next > L_cur → باکس بکش                 |
//| 3. اگر H_next > H_cur و L_next < L_cur → باکس بکش                 |
//| 4. اگر H_next < H_cur و L_next < L_cur → باکس بکش (نزولی)        |
//| 5. اگر H_next < H_cur و H_prev < H_cur → هیچ باکسی نکش            |
//|                                                                    |
//| امتداد جلو: صعودی تا از High رد شود، نزولی تا از Low رد شود       |
//| امتداد عقب: صعودی تا به Low برسد، نزولی تا وارد High شود          |
//+------------------------------------------------------------------+
#property version   "6.00"
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

//--- Inputs : source structure timeframes
input ENUM_TIMEFRAMES InpTF1      = PERIOD_D1;
input bool             InpUseTF1  = true;
input color            InpColorTF1 = clrMagenta;

input ENUM_TIMEFRAMES InpTF2      = PERIOD_W1;
input bool             InpUseTF2  = true;
input color            InpColorTF2 = clrDodgerBlue;

input ENUM_TIMEFRAMES InpTF3      = PERIOD_H4;
input bool             InpUseTF3  = true;
input color            InpColorTF3 = clrWhite;

input ENUM_TIMEFRAMES InpTF4      = PERIOD_H1;
input bool             InpUseTF4  = true;
input color            InpColorTF4 = clrYellow;

input ENUM_TIMEFRAMES InpTF5      = PERIOD_M15;
input bool             InpUseTF5  = true;
input color            InpColorTF5 = clrLime;
input int              InpM15DaysBack = 20; // فقط برای 20 روز اخیر

input int    InpPivotBars1  = 3;
input bool   InpUsePivot1   = true;

input int    InpPivotBars2  = 5;
input bool   InpUsePivot2   = true;

input int    InpPivotBars3  = 8;
input bool   InpUsePivot3   = false;

input int    InpMaxBarsTF   = 3000;

input int    InpLineWidth   = 1;
input bool   InpShowLabel   = true;

//--- Pivot structure
struct SPivot { datetime time; double price; bool isHigh; };

//+------------------------------------------------------------------+
//| Build pivots: returns ALTERNATING High/Low pivots (not just HH/LL) |
//+------------------------------------------------------------------+
bool BuildAlternatingPivots(ENUM_TIMEFRAMES tf, int pivotBars, int maxBars, SPivot &pivots[])
{
   ArrayResize(pivots, 0);

   int availBars = iBars(_Symbol, tf);
   if(availBars <= 0) return false;
   int reqBars = MathMin(availBars, maxBars);
   if(reqBars < pivotBars * 2 + 3) return false;

   double high[], low[]; datetime tm[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low,  true);
   ArraySetAsSeries(tm,   true);

   int copied = CopyHigh(_Symbol, tf, 0, reqBars, high);
   if(copied < pivotBars * 2 + 3) return false;
   CopyLow(_Symbol, tf, 0, copied, low);
   CopyTime(_Symbol, tf, 0, copied, tm);

   ArraySetAsSeries(high, false);
   ArraySetAsSeries(low,  false);
   ArraySetAsSeries(tm,   false);

   int n = copied;

   // Step 1: Find all fractal pivots
   SPivot raw[]; int rc = 0;
   for(int i = pivotBars; i < n - pivotBars; i++)
   {
      bool isH = true, isL = true;
      for(int k = 1; k <= pivotBars; k++)
      {
         if(high[i-k] >= high[i] || high[i+k] >= high[i]) isH = false;
         if(low[i-k]  <= low[i]  || low[i+k]  <= low[i])  isL = false;
      }
      if(isH && !isL)
      {
         ArrayResize(raw, rc + 1);
         raw[rc].time = tm[i]; raw[rc].price = high[i]; raw[rc].isHigh = true;
         rc++;
      }
      else if(isL && !isH)
      {
         ArrayResize(raw, rc + 1);
         raw[rc].time = tm[i]; raw[rc].price = low[i]; raw[rc].isHigh = false;
         rc++;
      }
   }
   if(rc < 2) return false;

   // Step 2: Alternating filter
   ArrayResize(pivots, 1);
   pivots[0] = raw[0];
   int pCount = 1;

   for(int i = 1; i < rc; i++)
   {
      SPivot last = pivots[pCount - 1];
      SPivot cur  = raw[i];
      if(cur.isHigh == last.isHigh)
      {
         if(cur.isHigh && cur.price > last.price) pivots[pCount - 1] = cur;
         else if(!cur.isHigh && cur.price < last.price) pivots[pCount - 1] = cur;
      }
      else
      {
         ArrayResize(pivots, pCount + 1);
         pivots[pCount] = cur;
         pCount++;
      }
   }
   
   return (pCount >= 2);
}

//+------------------------------------------------------------------+
//| Floor search: largest chart bar index k such that chartTime[k]<=t|
//+------------------------------------------------------------------+
int FindBarIndex(const datetime &chartTime[], int ratesTotal, datetime t)
{
   if(ratesTotal <= 0) return -1;
   if(t <= chartTime[0]) return 0;
   if(t >= chartTime[ratesTotal - 1]) return ratesTotal - 1;

   int lo = 0, hi = ratesTotal - 1;
   while(lo < hi)
   {
      int mid = (lo + hi + 1) / 2;
      if(chartTime[mid] <= t) lo = mid;
      else hi = mid - 1;
   }
   return lo;
}

//+------------------------------------------------------------------+
void DrawHollowBox(string name, datetime t1, double top, datetime t2, double bottom,
                   color clr, int width)
{
   if(ObjectFind(0, name) >= 0) ObjectDelete(0, name);
   if(!ObjectCreate(0, name, OBJ_RECTANGLE, 0, t1, top, t2, bottom)) return;
   ObjectSetInteger(0, name, OBJPROP_COLOR,      clr);
   ObjectSetInteger(0, name, OBJPROP_WIDTH,      width);
   ObjectSetInteger(0, name, OBJPROP_FILL,       false);
   ObjectSetInteger(0, name, OBJPROP_BACK,       false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_RAY_RIGHT,  false);
}

//+------------------------------------------------------------------+
string TFName(ENUM_TIMEFRAMES tf)
{
   string s = EnumToString(tf);
   StringReplace(s, "PERIOD_", "");
   return s;
}

//+------------------------------------------------------------------+
//| حذف تکراری‌ها از رشته label (مثلاً 3D-5D-5D به 3D-5D تبدیل شود) |
//+------------------------------------------------------------------+
string RemoveDuplicates(string inputStr)
{
   if(inputStr == "") return "";
   
   string result = "";
   string parts[];
   ushort separator = '-';
   int count = StringSplit(inputStr, separator, parts);
   
   if(count <= 0) return inputStr;
   
   // اولین عنصر را اضافه کن
   result = parts[0];
   
   // بقیه را بررسی کن و فقط unique ها را اضافه کن
   for(int i = 1; i < count; i++)
   {
      bool exists = false;
      
      // بررسی کن آیا قبلاً اضافه شده
      string checkParts[];
      int checkCount = StringSplit(result, separator, checkParts);
      
      for(int j = 0; j < checkCount; j++)
      {
         if(checkParts[j] == parts[i])
         {
            exists = true;
            break;
         }
      }
      
      // اگر وجود نداشت، اضافه کن
      if(!exists)
      {
         result += "-" + parts[i];
      }
   }
   
   return result;
}

//+------------------------------------------------------------------+
//| منطق باکس‌های فقط High تا Low - نسخه جدید:                        |
//| فقط از High تا Low باکس رسم می‌شود                                |
//| برای هر High باید قبلی، جاری، و بعدی بررسی شود                   |
//+------------------------------------------------------------------+
void ProcessTF(ENUM_TIMEFRAMES tf, int pivotBars, color clr,
               const datetime &chartTime[], const double &chartHigh[], const double &chartLow[],
               int ratesTotal, string &boxLabels[][2], int daysBack = 0) // اضافه کردن آرایه برای ذخیره label ها و محدودیت روز
{
   SPivot pivots[];
   if(!BuildAlternatingPivots(tf, pivotBars, InpMaxBarsTF, pivots)) return;

   string tfTag = TFName(tf) + "_P" + IntegerToString(pivotBars);
   int count = ArraySize(pivots);
   
   if(count < 3) return; // حداقل سه pivot نیاز است

   // محاسبه زمان محدودیت (اگر daysBack > 0)
   datetime limitTime = 0;
   if(daysBack > 0)
   {
      limitTime = TimeCurrent() - daysBack * 24 * 60 * 60;
   }

   // پردازش هر High که Low بعد از آن دارد
   for(int i = 1; i < count; i++)
   {
      SPivot cur = pivots[i];
      
      // بررسی محدودیت زمانی
      if(daysBack > 0 && cur.time < limitTime)
      {
         continue; // این pivot خیلی قدیمی است
      }
      
      // فقط High ها را در نظر بگیر
      if(!cur.isHigh) continue;
      
      // Low بعد از این High را پیدا کن
      int lowIdx = -1;
      for(int j = i + 1; j < count; j++)
      {
         if(!pivots[j].isHigh) 
         {
            lowIdx = j;
            break;
         }
      }
      
      if(lowIdx == -1) continue; // Low بعدی وجود ندارد
      
      SPivot curLow = pivots[lowIdx];
      double highPrice = cur.price;
      double lowPrice = curLow.price;
      
      // High قبلی و بعدی را پیدا کن
      double prevHigh = -1, nextHigh = -1;
      double prevLow = -1, nextLow = -1;
      datetime prevLowTime = 0;
      
      // High قبلی
      for(int j = i - 1; j >= 0; j--)
      {
         if(pivots[j].isHigh) 
         {
            prevHigh = pivots[j].price;
            break;
         }
      }
      
      // Low قبلی
      for(int j = i - 1; j >= 0; j--)
      {
         if(!pivots[j].isHigh) 
         {
            prevLow = pivots[j].price;
            prevLowTime = pivots[j].time;
            break;
         }
      }
      
      // High بعدی
      for(int j = lowIdx + 1; j < count; j++)
      {
         if(pivots[j].isHigh) 
         {
            nextHigh = pivots[j].price;
            break;
         }
      }
      
      // Low بعدی
      for(int j = lowIdx + 1; j < count; j++)
      {
         if(!pivots[j].isHigh) 
         {
            nextLow = pivots[j].price;
            break;
         }
      }
      
      // High و Low دوم بعدی
      double nextHigh2 = -1, nextLow2 = -1;
      int nextLowIdx = -1;
      
      // ابتدا Low بعدی را پیدا کن
      for(int j = lowIdx + 1; j < count; j++)
      {
         if(!pivots[j].isHigh) 
         {
            nextLowIdx = j;
            break;
         }
      }
      
      // اگر Low بعدی پیدا شد، High دوم بعدی را پیدا کن
      if(nextLowIdx > 0)
      {
         for(int j = nextLowIdx + 1; j < count; j++)
         {
            if(pivots[j].isHigh) 
            {
               nextHigh2 = pivots[j].price;
               break;
            }
         }
         
         // Low دوم بعدی را پیدا کن
         for(int j = nextLowIdx + 1; j < count; j++)
         {
            if(!pivots[j].isHigh) 
            {
               nextLow2 = pivots[j].price;
               break;
            }
         }
      }
      
      // شرط 1: اگر High بعدی و High قبلی پایین‌تر از High جاری باشند
      // بررسی می‌کنیم که آیا reversal واقعی وجود دارد یا نه
      if(nextHigh > 0 && prevHigh > 0 && nextHigh < highPrice && prevHigh < highPrice)
      {
         // بررسی کن: آیا High و Low جاری از قبلی پایین‌تر هستند؟ (downtrend)
         bool downtrend = (prevLow > 0 && highPrice < prevHigh && lowPrice < prevLow);
         
         // اگر در downtrend نیستیم، یعنی High مجزا است
         if(!downtrend)
         {
            // High مجزا است → این High باکس نمی‌گیرد
            continue;
         }
         
         // در downtrend هستیم - بررسی reversal واقعی با دو پیووت بعدی
         // بررسی reversal اول: High و Low بعدی اول هر دو بالاتر باشند
         bool reversal1 = (nextLow > 0 && nextHigh > highPrice && nextLow > lowPrice);
         
         // بررسی reversal دوم: High و Low دوم بعدی هم بالاتر باشند
         bool reversal2 = false;
         if(nextHigh2 > 0 && nextLow2 > 0)
         {
            reversal2 = (nextHigh2 > nextHigh && nextLow2 > nextLow);
         }
         
         // فقط اگر هر دو reversal کامل و قوی باشند → باکس نکش
         if(reversal1 && reversal2)
         {
            // بررسی اضافی: reversal2 باید قوی باشد
            double move1 = nextHigh - highPrice; // اولین حرکت صعودی
            double move2 = nextHigh2 - nextHigh; // دومین حرکت صعودی
            
            // اگر دومین حرکت هم قوی باشد → reversal تایید شده
            if(move2 >= move1 * 0.5) // حداقل 50% از حرکت اول
            {
               continue; // reversal قوی تایید شده - باکس نکش
            }
         }
         // در غیر این صورت در downtrend هستیم و باکس کشیده می‌شود
      }
      
      // شرط استثنا: اگر High جاری از قبلی و بعدی پایین‌تر و Low جاری از قبلی و بعدی بالاتر
      // این یک inside bar معتبر است → باکس بکش
      bool isValidInsideBar = false;
      if(prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
      {
         if(highPrice < prevHigh && highPrice < nextHigh && lowPrice > prevLow && lowPrice > nextLow)
         {
            isValidInsideBar = true;
         }
      }
      
      // شرط جدید: اگر High جاری < High قبلی و Low جاری > Low قبلی و Low جاری > Low بعدی
      // یعنی inside bar یا کندل محدود → باکس نکش (مگر اینکه inside bar معتبر باشد)
      if(!isValidInsideBar && prevHigh > 0 && prevLow > 0 && nextLow > 0)
      {
         if(highPrice < prevHigh && lowPrice > prevLow && lowPrice > nextLow)
         {
            // کندل محدود و مجزا → باکس نکش
            continue;
         }
      }
      
      // شرط فیلتر: اگر High بعدی و Low بعدی و Low قبلی همه بالاتر، ولی High قبلی پایین‌تر
      // (مگر اینکه inside bar معتبر باشد)
      if(!isValidInsideBar && prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
      {
         if(nextHigh > highPrice && nextLow > lowPrice && prevLow > lowPrice && prevHigh < highPrice)
         {
            // پیووت خاص → باکس نکش
            continue;
         }
      }
      
      // شرط 2: اگر Low بعدی و Low قبلی بالاتر از Low جاری → بررسی uptrend
      if(nextLow > 0 && prevLow > 0 && nextLow > lowPrice && prevLow > lowPrice)
      {
         // بررسی کن: آیا High و Low جاری از قبلی بالاتر هستند؟ (uptrend)
         bool uptrend = (prevHigh > 0 && highPrice > prevHigh && lowPrice > prevLow);
         
         if(uptrend)
         {
            // در uptrend هستیم - بررسی نقطه چرخش به سمت نزولی
            bool reversal1 = (nextHigh > 0 && nextHigh < highPrice && nextLow < lowPrice);
            
            bool reversal2 = false;
            if(nextHigh2 > 0 && nextLow2 > 0)
            {
               reversal2 = (nextHigh2 < nextHigh && nextLow2 < nextLow);
            }
            
            if(reversal1 && reversal2)
            {
               // بررسی قدرت reversal
               double move1 = highPrice - nextHigh;
               double move2 = nextHigh - nextHigh2;
               
               if(move2 >= move1 * 0.5)
               {
                  continue; // نقطه چرخش قوی به نزولی - باکس نکش
               }
            }
         }
         else
         {
            // Low مجزا نیست، بلکه ممکن است در downtrend باشد
            // در این حالت باید باکس کشیده شود
            // فقط اگر واقعاً Low مجزا باشد (نه قبلی بالاتر و نه بعدی بالاتر) باکس نکش
            // continue; // این خط را کامنت می‌کنیم
         }
      }
      
      // شرط 3: Inside bar نزولی - فقط اگر واقعاً inside bar با ادامه نزولی قوی باشد
      if(prevHigh > 0 && prevLow > 0 && nextHigh > 0 && nextLow > 0)
      {
         // بررسی inside bar واقعی
         bool isInsideBar = (highPrice < prevHigh && lowPrice > prevLow);
         
         if(isInsideBar)
         {
            // فقط اگر روند بعدی هم نزولی قوی است، باکس نکش
            // یعنی High و Low بعدی هر دو به طور قابل توجهی پایین‌تر باشند
            bool strongBearish = (nextHigh < highPrice && nextLow < lowPrice);
            
            // بررسی کن که آیا ادامه نزولی قوی است
            if(strongBearish && nextHigh2 > 0 && nextLow2 > 0)
            {
               // اگر حرکت دوم هم نزولی قوی باشد
               bool strongBearish2 = (nextHigh2 < nextHigh && nextLow2 < nextLow);
               
               if(strongBearish2)
               {
                  continue; // Inside bar با روند نزولی قوی - باکس نکش
               }
            }
         }
      }
      
      // تعیین نوع روند و محدوده باکس
      bool isBullish = false;
      double boxTop = highPrice;
      double boxBottom = lowPrice;
      
      // شرط ویژه: اگر High جاری < High قبلی و Low جاری < Low قبلی → باکس از Low قبلی تا High جاری
      if(prevHigh > 0 && prevLow > 0 && highPrice < prevHigh && lowPrice < prevLow)
      {
         isBullish = false; // روند نزولی
         boxTop = highPrice;
         boxBottom = prevLow; // استفاده از Low قبلی
      }
      else if(nextHigh > 0 && nextLow > 0)
      {
         // شرط 1: H_next > H_cur و L_next > L_cur → صعودی
         if(nextHigh > highPrice && nextLow > lowPrice)
         {
            isBullish = true;
            boxTop = highPrice;
            boxBottom = lowPrice;
         }
         // شرط 4: H_next < H_cur و L_next < L_cur → نزولی
         else if(nextHigh < highPrice && nextLow < lowPrice)
         {
            isBullish = false;
            boxTop = highPrice;
            boxBottom = lowPrice;
         }
         // شرط 2: H_next < H_cur و L_next > L_cur → باکس بکش
         else if(nextHigh < highPrice && nextLow > lowPrice)
         {
            isBullish = true; // فرض صعودی
            boxTop = highPrice;
            boxBottom = lowPrice;
         }
         // شرط 3: H_next > H_cur و L_next < L_cur → باکس بکش
         else if(nextHigh > highPrice && nextLow < lowPrice)
         {
            isBullish = false; // فرض نزولی
            boxTop = highPrice;
            boxBottom = lowPrice;
         }
         else
         {
            // هیچ شرطی برقرار نیست → باکس نکش
            continue;
         }
      }
      else
      {
         // nextHigh یا nextLow وجود ندارند → باکس نکش
         continue;
      }
      
      // بررسی حداقل اندازه باکس: باکس باید حداقل قابل مشاهده باشد
      double boxHeight = boxTop - boxBottom;
      if(boxHeight <= 0)
      {
         // ارتفاع باکس صفر یا منفی → باکس نکش
         continue;
      }
      
      int idxHigh = FindBarIndex(chartTime, ratesTotal, cur.time);
      int idxLow = FindBarIndex(chartTime, ratesTotal, curLow.time);
      if(idxHigh < 0 || idxLow < 0) continue;
      
      // برای باکس‌های نزولی که از prevLow استفاده می‌کنند، index آن را پیدا کن
      int idxPrevLow = -1;
      if(!isBullish && boxBottom == prevLow && prevLow > 0 && prevLowTime > 0)
      {
         idxPrevLow = FindBarIndex(chartTime, ratesTotal, prevLowTime);
      }

      // ===== امتداد به عقب =====
      // از High شروع می‌کنیم و به عقب می‌رویم تا کندلی که کاملاً داخل باکس نیست
      int leftIdx = idxHigh;
      
      for(int k = idxHigh - 1; k >= 0; k--)
      {
         // بررسی کنیم آیا این کندل کاملاً داخل باکس است
         bool candleInsideBox = (chartLow[k] >= boxBottom && chartHigh[k] <= boxTop);
         
         if(!candleInsideBox)
         {
            // اولین کندل خارج از باکس
            leftIdx = k + 1;
            break;
         }
         
         leftIdx = k;
      }
      
      // یک کندل بیشتر به عقب امتداد بده
      if(leftIdx > 0) leftIdx--;

      // ===== امتداد به جلو =====
      int rightIdx = idxLow;
      
      // برای باکس‌های نزولی که از prevLow استفاده می‌کنند
      if(idxPrevLow >= 0 && !isBullish && boxBottom == prevLow)
      {
         // از prevLow شروع می‌کنیم و به جلو می‌رویم تا قیمت از prevLow رد شود
         rightIdx = idxPrevLow;
         
         for(int k = idxPrevLow + 1; k < ratesTotal; k++)
         {
            // اگر قیمت از prevLow پایین‌تر رفت
            if(chartLow[k] < prevLow)
            {
               // امتداد متوقف می‌شود
               rightIdx = k - 1;
               break;
            }
            
            rightIdx = k;
         }
      }
      else
      {
         // برای بقیه باکس‌ها: منطق قبلی
         for(int k = idxLow + 1; k < ratesTotal; k++)
         {
            // اگر High کندل از boxBottom پایین‌تر رفت، یعنی کل کندل از پایین باکس رد شده
            if(chartHigh[k] < boxBottom)
            {
               // امتداد متوقف می‌شود
               rightIdx = k - 1;
               break;
            }
            
            // بررسی کنیم آیا این کندل کاملاً داخل باکس است
            bool candleInsideBox = (chartLow[k] >= boxBottom && chartHigh[k] <= boxTop);
            
            if(!candleInsideBox)
            {
               // اولین کندل خارج از باکس
               rightIdx = k - 1;
               break;
            }
            
            rightIdx = k;
         }
      }
      
      // یک کندل بیشتر به جلو امتداد بده
      if(rightIdx < ratesTotal - 1) rightIdx++;

      // رسم باکس: از boxTop تا boxBottom
      datetime t1 = chartTime[leftIdx];
      datetime t2 = chartTime[rightIdx];

      string boxName = "FLAG_BOX_" + tfTag + "_" + IntegerToString((int)cur.time) + "_" + IntegerToString((int)curLow.time);
      DrawHollowBox(boxName, t1, boxTop, t2, boxBottom, clr, InpLineWidth);

      // ذخیره کلید باکس و label برای این باکس
      string boxKey = IntegerToString((int)cur.time) + "_" + IntegerToString((int)curLow.time);
      
      // ساخت label: مقدار pivot + نماد timeframe (مثلاً 3D یا 5W)
      string tfSymbol = "";
      if(tf == PERIOD_D1) tfSymbol = "D";
      else if(tf == PERIOD_W1) tfSymbol = "W";
      else if(tf == PERIOD_H4) tfSymbol = "H4";
      else if(tf == PERIOD_H1) tfSymbol = "H1";
      else if(tf == PERIOD_M15) tfSymbol = "M15";
      else tfSymbol = TFName(tf);
      
      string labelText = IntegerToString(pivotBars) + tfSymbol;
      
      // اضافه کردن این label به آرایه
      int size = ArrayRange(boxLabels, 0);
      bool found = false;
      
      // پیدا کردن باکس در آرایه
      for(int b = 0; b < size; b++)
      {
         if(boxLabels[b][0] == boxKey)
         {
            // اضافه کردن label با -
            if(boxLabels[b][1] != "")
               boxLabels[b][1] += "-" + labelText;
            else
               boxLabels[b][1] = labelText;
            found = true;
            break;
         }
      }
      
      // اگر باکس جدید است، اضافه کن
      if(!found)
      {
         ArrayResize(boxLabels, size + 1, size + 100);
         boxLabels[size][0] = boxKey;
         boxLabels[size][1] = labelText;
      }
   }
}

//+------------------------------------------------------------------+
int OnInit()
{
   IndicatorSetString(INDICATOR_SHORTNAME, "Flag v6.00");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   ObjectsDeleteAll(0, "FLAG_");
}

//+------------------------------------------------------------------+

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
   if(rates_total < 10) return 0;

   static datetime lastSrcTime[5] = {0, 0, 0, 0, 0};

   ENUM_TIMEFRAMES tfArr[5]  = {InpTF1, InpTF2, InpTF3, InpTF4, InpTF5};
   bool            useArr[5] = {InpUseTF1, InpUseTF2, InpUseTF3, InpUseTF4, InpUseTF5};

   bool needRecalc = (prev_calculated == 0);
   for(int s = 0; s < 5; s++)
   {
      if(!useArr[s]) continue;
      datetime t0 = iTime(_Symbol, tfArr[s], 0);
      if(t0 != lastSrcTime[s]) { needRecalc = true; lastSrcTime[s] = t0; }
   }
   if(!needRecalc) return rates_total;

   ObjectsDeleteAll(0, "FLAG_");

   int pivotBarsArr[3] = {InpPivotBars1, InpPivotBars2, InpPivotBars3};
   bool usePivotArr[3] = {InpUsePivot1, InpUsePivot2, InpUsePivot3};
   
   // آرایه برای ذخیره label های هر باکس
   string boxLabels[][2]; // [i][0] = boxKey, [i][1] = combined label
   ArrayResize(boxLabels, 0);
   
   // آرایه رنگ‌ها برای هر timeframe
   color tfColorArr[5] = {InpColorTF1, InpColorTF2, InpColorTF3, InpColorTF4, InpColorTF5};
   
   Print("useArr[0]=", useArr[0], " useArr[1]=", useArr[1], " useArr[2]=", useArr[2], " useArr[3]=", useArr[3], " useArr[4]=", useArr[4]);
   Print("TF1=", tfArr[0], " TF2=", tfArr[1], " TF3=", tfArr[2], " TF4=", tfArr[3], " TF5=", tfArr[4]);
   
   for(int s = 0; s < 5; s++)
   {
      if(!useArr[s]) 
      {
         Print("Skipping TF ", s, " because useArr is false");
         continue;
      }
      
      ENUM_TIMEFRAMES currentTF = tfArr[s];
      color currentColor = tfColorArr[s]; // رنگ این timeframe
      
      Print("Processing TF ", s, ": ", currentTF, " with color: ", currentColor);
      
      // برای M15 فقط pivot 3 و فقط 2 روز اخیر
      if(currentTF == PERIOD_M15)
      {
         // فقط pivot 3
         if(InpUsePivot1 && InpPivotBars1 == 3)
         {
            Print("Calling ProcessTF for M15 with pivotBars=3, daysBack=", InpM15DaysBack);
            ProcessTF(currentTF, 3, currentColor, time, high, low, rates_total, boxLabels, InpM15DaysBack);
         }
         continue; // بقیه pivot ها برای M15 اجرا نشوند
      }
      
      // برای هر pivotBars که فعال است
      for(int p = 0; p < 3; p++)
      {
         if(!usePivotArr[p]) continue; // اگر این pivotBars غیرفعال است، رد شو
         
         // برای تایم فریم هفتگی فقط 3 و 5 را فعال کن (نه 8)
         if(currentTF == PERIOD_W1 && pivotBarsArr[p] == 8) continue;
         
         // برای H4 فقط pivot 5 را فعال کن
         if(currentTF == PERIOD_H4 && pivotBarsArr[p] != 5) continue;
         
         // برای H1 فقط pivot 3 و 5 را فعال کن
         if(currentTF == PERIOD_H1 && pivotBarsArr[p] != 3 && pivotBarsArr[p] != 5) continue;
         
         // Debug: چاپ کردن برای بررسی
         Print("Calling ProcessTF with TF=", currentTF, " pivotBars=", pivotBarsArr[p], " color=", currentColor);
         
         ProcessTF(currentTF, pivotBarsArr[p], currentColor, time, high, low, rates_total, boxLabels);
      }
   }

   // حالا label های ترکیبی را رسم کن
   if(InpShowLabel)
   {
      int labelCount = ArrayRange(boxLabels, 0);
      
      for(int i = 0; i < labelCount; i++)
      {
         string boxKey = boxLabels[i][0];
         string combinedLabel = boxLabels[i][1];
         
         if(combinedLabel == "") continue;
         
         // حذف تکراری‌ها از label
         combinedLabel = RemoveDuplicates(combinedLabel);
         
         // پیدا کردن اولین باکس با این کلید برای گرفتن موقعیت
         string searchPrefix = "FLAG_BOX_";
         int totalObjects = ObjectsTotal(0, 0, OBJ_RECTANGLE);
         
         for(int obj = 0; obj < totalObjects; obj++)
         {
            string objName = ObjectName(0, obj, 0, OBJ_RECTANGLE);
            
            if(StringFind(objName, searchPrefix) == 0 && StringFind(objName, boxKey) > 0)
            {
               // پیدا کردن موقعیت باکس
               datetime t1 = (datetime)ObjectGetInteger(0, objName, OBJPROP_TIME, 0);
               datetime t2 = (datetime)ObjectGetInteger(0, objName, OBJPROP_TIME, 1);
               double top = ObjectGetDouble(0, objName, OBJPROP_PRICE, 0);
               double bottom = ObjectGetDouble(0, objName, OBJPROP_PRICE, 1);
               color boxColor = (color)ObjectGetInteger(0, objName, OBJPROP_COLOR);
               
               // محاسبه موقعیت label
               double labelPrice = top + (top - bottom) * 0.12;
               datetime labelTime = (datetime)((t1 + t2) / 2); // وسط باکس
               
               // رسم label
               string lblName = "FLAG_LBL_" + boxKey;
               if(ObjectFind(0, lblName) >= 0) ObjectDelete(0, lblName);
               
               ObjectCreate(0, lblName, OBJ_TEXT, 0, labelTime, labelPrice);
               ObjectSetString(0, lblName, OBJPROP_TEXT, combinedLabel);
               ObjectSetInteger(0, lblName, OBJPROP_COLOR, boxColor);
               ObjectSetInteger(0, lblName, OBJPROP_FONTSIZE, 9);
               ObjectSetInteger(0, lblName, OBJPROP_ANCHOR, ANCHOR_CENTER);
               
               break; // فقط یک label برای هر باکس
            }
         }
      }
   }

   return rates_total;
}
//+------------------------------------------------------------------+
