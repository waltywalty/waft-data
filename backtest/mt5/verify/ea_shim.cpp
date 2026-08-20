#include "mql5_shim.h"
string _Symbol = "XAUUSD";
//+------------------------------------------------------------------+
//|                                                AsiaOpenGold.mq5  |
//|  Asia-open range breakout on gold, gated by the gold/AUDUSD      |
//|  correlation regime.                                             |
//|                                                                  |
//|  Rule:                                                           |
//|    - Range = first 60 minutes from 09:30 Hong Kong (01:30 UTC).  |
//|    - Enter on the first 60-minute block to CLOSE beyond that     |
//|      range, in that direction. One trade per day, first break.   |
//|    - Only trade when the 20-day correlation of gold and AUDUSD   |
//|      daily log returns, computed through yesterday's close, is   |
//|      at or below a threshold (default 0.5).                      |
//|    - Stop at 2 x the range width. Exit at 16:00 New York.        |
//|    - Risk a fixed percentage of equity per trade.                |
//|                                                                  |
//|  All session times are handled in UTC with explicit European and |
//|  US daylight-saving rules, because 09:30 Hong Kong lands on a    |
//|  DIFFERENT broker-server hour in summer than in winter.          |
//+------------------------------------------------------------------+
// [stripped] #property copyright "Asia-open gold breakout"
// [stripped] #property version   "1.00"

// [stripped] #include <Trade\Trade.mqh>

//--- inputs
// [stripped] input group           "Instruments"
string          InpAudSymbol      = "AUDUSD";   // AUDUSD symbol (match your broker's suffix)
// [stripped] input group           "Signal"
int             InpRangeMinutes   = 60;         // Opening range length, minutes
int             InpRangeStartUtcH = 1;          // Range start hour, UTC
int             InpRangeStartUtcM = 30;         // Range start minute, UTC
int             InpEntryCutoffLdn = 8;          // No entry after this hour, London time
// [stripped] input group           "Correlation filter"
bool            InpUseFilter      = true;       // Apply the correlation filter
int             InpCorrDays       = 20;         // Rolling window, days
double          InpCorrMax        = 0.50;       // Trade only when correlation <= this
// [stripped] input group           "Risk"
double          InpRiskPercent    = 1.0;        // Risk per trade, % of equity
double          InpStopRangeMult  = 2.0;        // Stop distance, multiples of range width
double          InpMaxLots        = 0.0;        // Hard lot cap (0 = no cap)
// [stripped] input group           "Execution"
int             InpMagic          = 930115;     // Magic number
int             InpSlippage       = 20;         // Max deviation, points
int             InpExitHourNY     = 16;         // Exit hour, New York time

//--- state
CTrade   trade;
datetime g_offsetCheckedDay = 0;
int      g_gmtOffsetSec = 0;      // server time minus GMT, seconds
datetime g_lastTradedDay = 0;     // UTC date of the last day we opened a trade
datetime g_lastCheckedBar = 0;
double   g_rangeHigh = 0.0, g_rangeLow = 0.0;
datetime g_rangeDay = 0;          // UTC date the current range belongs to
bool     g_rangeValid = false;
bool     g_filterPassed = false;

//+------------------------------------------------------------------+
//| Helpers: calendar                                                |
//+------------------------------------------------------------------+
datetime DayStartUtc(datetime t)
  {
   return (datetime)((long)t - (long)t % 86400);
  }

//--- day-of-week for a UTC date, 0 = Sunday
int DowUtc(datetime t)
  {
   MqlDateTime s; TimeToStruct(t, s);
   return s.day_of_week;
  }

//--- UTC timestamp of the Nth given weekday of a month; n = -1 means the last one
datetime NthWeekdayUtc(int year, int month, int weekday, int n, int hour)
  {
   MqlDateTime s; ZeroMemory(s);
   s.year = year; s.mon = month; s.day = 1;
   s.hour = hour; s.min = 0; s.sec = 0;
   datetime first = StructToTime(s);
   if(n > 0)
     {
      int shift = (weekday - DowUtc(first) + 7) % 7;
      return first + (datetime)((shift + (n - 1) * 7) * 86400);
     }
   // last weekday of the month: walk back from the 1st of the next month
   int ny = (month == 12) ? year + 1 : year;
   int nm = (month == 12) ? 1 : month + 1;
   MqlDateTime e; ZeroMemory(e); e.year = ny; e.mon = nm; e.day = 1; e.hour = hour; e.min = 0; e.sec = 0;
   datetime nextFirst = StructToTime(e);
   datetime last = nextFirst - 86400;
   int back = (DowUtc(last) - weekday + 7) % 7;
   return last - (datetime)(back * 86400);
  }

//--- European summer time: last Sunday of March 01:00 UTC to last Sunday of October 01:00 UTC
bool IsEuropeDST(datetime utc)
  {
   MqlDateTime s; TimeToStruct(utc, s);
   datetime start = NthWeekdayUtc(s.year, 3, 0, -1, 1);
   datetime end   = NthWeekdayUtc(s.year, 10, 0, -1, 1);
   return (utc >= start && utc < end);
  }

//--- US daylight time: 2nd Sunday of March 07:00 UTC to 1st Sunday of November 06:00 UTC
bool IsUsDST(datetime utc)
  {
   MqlDateTime s; TimeToStruct(utc, s);
   datetime start = NthWeekdayUtc(s.year, 3, 0, 2, 7);
   datetime end   = NthWeekdayUtc(s.year, 11, 0, 1, 6);
   return (utc >= start && utc < end);
  }

//--- UTC offsets, in hours, of the two centres we anchor to
int LondonOffset(datetime utc) { return IsEuropeDST(utc) ? 1 : 0; }
int NewYorkOffset(datetime utc) { return IsUsDST(utc) ? -4 : -5; }

//--- convert a UTC instant to broker server time
datetime UtcToServer(datetime utc) { return utc + (datetime)g_gmtOffsetSec; }

//+------------------------------------------------------------------+
//| Init                                                             |
//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(InpSlippage);
   trade.SetTypeFillingBySymbol(_Symbol);

   // Derive the broker's UTC offset at runtime. Never hardcode a server hour:
   // 01:30 UTC is 03:30 server time in winter and 04:30 in summer on an EET broker.
   g_gmtOffsetSec = (int)(TimeCurrent() - TimeGMT());
   int offH = (int)MathRound(g_gmtOffsetSec / 3600.0);
   g_gmtOffsetSec = offH * 3600;                       // snap to a whole hour
   PrintFormat("Broker clock is UTC%+d. %02d:%02d UTC = %02d:%02d server time.",
               offH, InpRangeStartUtcH, InpRangeStartUtcM,
               (InpRangeStartUtcH + offH + 24) % 24, InpRangeStartUtcM);

   if(InpUseFilter)
     {
      if(!SymbolSelect(InpAudSymbol, true))
        {
         PrintFormat("ERROR: cannot select %s. The correlation filter needs it. "
                     "Add it to Market Watch, or check the symbol suffix.", InpAudSymbol);
         return(INIT_FAILED);
        }
     }
   if(InpRangeMinutes % 5 != 0)
     {
      Print("ERROR: range length must be a multiple of 5 minutes.");
      return(INIT_FAILED);
     }
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| The correlation filter                                           |
//| Returns false and sets ok=false when the data is unusable - in    |
//| that case the caller must SKIP the day, never trade unfiltered.   |
//+------------------------------------------------------------------+
bool CorrelationOk(double &corrOut, bool &dataOk)
  {
   corrOut = 0.0; dataOk = false;
   int need = InpCorrDays + 2;                 // n returns needs n+1 closes, +1 for today's bar
   MqlArray<MqlRates> g, a;
   ArraySetAsSeries(g, true); ArraySetAsSeries(a, true);
   if(CopyRates(_Symbol, PERIOD_D1, 0, need + 3, g) < need) return(false);
   if(CopyRates(InpAudSymbol, PERIOD_D1, 0, need + 3, a) < need) return(false);

   // Bar 0 is today and is still forming. Use bars 1..N so the filter only ever
   // sees closed days - this is the "lagged one day" version that was validated.
   // Require the two symbols' most recent CLOSED daily bars to be the same day,
   // otherwise one feed is stale and the comparison is meaningless.
   if(g[1].time != a[1].time)
     {
      PrintFormat("Feed mismatch: %s last closed daily bar %s, %s %s. Skipping.",
                  _Symbol, TimeToString(g[1].time), InpAudSymbol, TimeToString(a[1].time));
      return(false);
     }

   MqlArray<double> rg, ra;
   ArrayResize(rg, InpCorrDays); ArrayResize(ra, InpCorrDays);
   for(int i = 0; i < InpCorrDays; i++)
     {
      int k = i + 1;                            // 1..InpCorrDays
      if(g[k].close <= 0 || g[k+1].close <= 0 || a[k].close <= 0 || a[k+1].close <= 0)
         return(false);
      if(g[k].time != a[k].time || g[k+1].time != a[k+1].time)
        {
         Print("Daily bars are not aligned between the two symbols. Skipping.");
         return(false);
        }
      rg[i] = MathLog(g[k].close / g[k+1].close);
      ra[i] = MathLog(a[k].close / a[k+1].close);
     }

   double mg = 0, ma = 0;
   for(int i = 0; i < InpCorrDays; i++) { mg += rg[i]; ma += ra[i]; }
   mg /= InpCorrDays; ma /= InpCorrDays;
   double sgg = 0, saa = 0, sga = 0;
   for(int i = 0; i < InpCorrDays; i++)
     {
      double dg = rg[i] - mg, da = ra[i] - ma;
      sgg += dg * dg; saa += da * da; sga += dg * da;
     }
   if(sgg <= 0.0 || saa <= 0.0) return(false);
   corrOut = sga / MathSqrt(sgg * saa);
   dataOk = true;
   return(corrOut <= InpCorrMax);
  }

//+------------------------------------------------------------------+
//| Build today's opening range from M5 bars                         |
//+------------------------------------------------------------------+
bool BuildRange(datetime dayUtc)
  {
   datetime startUtc = dayUtc + InpRangeStartUtcH * 3600 + InpRangeStartUtcM * 60;
   datetime endUtc   = startUtc + InpRangeMinutes * 60;
   MqlArray<MqlRates> r;
   // CopyRates(from,to) is inclusive of bars whose OPEN time is in [from, to],
   // so stop one bar short of the range end.
   int n = CopyRates(_Symbol, PERIOD_M5, UtcToServer(startUtc), UtcToServer(endUtc - 300), r);
   int expect = InpRangeMinutes / 5;
   if(n < expect)
     {
      PrintFormat("Range window incomplete (%d of %d M5 bars). Skipping the day.", n, expect);
      return(false);
     }
   double hi = -DBL_MAX, lo = DBL_MAX;
   for(int i = 0; i < n; i++) { hi = MathMax(hi, r[i].high); lo = MathMin(lo, r[i].low); }
   if(hi <= lo) return(false);
   g_rangeHigh = hi; g_rangeLow = lo; g_rangeDay = dayUtc; g_rangeValid = true;
   PrintFormat("Range %s: %.2f / %.2f (width %.2f)",
               TimeToString(dayUtc, TIME_DATE), hi, lo, hi - lo);
   return(true);
  }

//+------------------------------------------------------------------+
//| Position sizing from the stop distance                           |
//+------------------------------------------------------------------+
double LotsForRisk(double stopDistancePrice)
  {
   if(stopDistancePrice <= 0.0) return(0.0);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickValue <= 0.0 || tickSize <= 0.0) return(0.0);

   double riskMoney = AccountInfoDouble(ACCOUNT_EQUITY) * InpRiskPercent / 100.0;
   double lossPerLot = (stopDistancePrice / tickSize) * tickValue;
   if(lossPerLot <= 0.0) return(0.0);
   double lots = riskMoney / lossPerLot;

   double minL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step > 0.0) lots = MathFloor(lots / step) * step;
   if(InpMaxLots > 0.0) lots = MathMin(lots, InpMaxLots);
   lots = MathMin(lots, maxL);
   if(lots < minL)
     {
      PrintFormat("Risk budget %.2f only supports %.4f lots, below the %.2f minimum. "
                  "Skipping - do NOT round up.", riskMoney, lots, minL);
      return(0.0);
     }
   return(NormalizeDouble(lots, 2));
  }

//+------------------------------------------------------------------+
//| Open position handling                                           |
//+------------------------------------------------------------------+
bool HasPosition()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic) return(true);
     }
   return(false);
  }

void CloseOurPosition(string why)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic)
        {
         PrintFormat("Closing #%I64u (%s)", tk, why);
         trade.PositionClose(tk);
        }
     }
  }

//+------------------------------------------------------------------+
//| Main                                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   datetime nowUtc = TimeGMT();
   datetime dayUtc = DayStartUtc(nowUtc);

   //--- the broker's own UTC offset shifts at the EET/EEST changeover, so re-derive
   //--- it daily rather than trusting the value captured at init
   if(g_offsetCheckedDay != dayUtc)
     {
      int off = (int)MathRound((TimeCurrent() - TimeGMT()) / 3600.0) * 3600;
      if(off != g_gmtOffsetSec)
        {
         PrintFormat("Broker UTC offset changed: %+d h -> %+d h", g_gmtOffsetSec / 3600, off / 3600);
         g_gmtOffsetSec = off;
         g_rangeValid = false;                  // rebuild against the new clock
        }
      g_offsetCheckedDay = dayUtc;
     }

   //--- time exit: 16:00 New York, DST-correct
   if(HasPosition())
     {
      datetime exitUtc = dayUtc + (InpExitHourNY - NewYorkOffset(nowUtc)) * 3600;
      // the trade opens in the Asia morning of the same UTC day, so the exit is later the same day
      if(nowUtc >= exitUtc) CloseOurPosition("time exit, 16:00 New York");
      else
        {
         // belt and braces: nothing here should ever be held for a whole day
         for(int i = PositionsTotal() - 1; i >= 0; i--)
           {
            ulong tk = PositionGetTicket(i);
            if(tk == 0) continue;
            if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
               PositionGetInteger(POSITION_MAGIC) == InpMagic &&
               (long)nowUtc - (long)PositionGetInteger(POSITION_TIME) + g_gmtOffsetSec > 86400)
               CloseOurPosition("stale position, over 24h old");
           }
        }
      return;                                   // never stack positions
     }

   //--- act once per closed M5 bar
   datetime barTime = iTime(_Symbol, PERIOD_M5, 0);
   if(barTime == g_lastCheckedBar) return;
   g_lastCheckedBar = barTime;

   if(g_lastTradedDay == dayUtc) return;        // one trade per day, already used

   datetime rangeStartUtc = dayUtc + InpRangeStartUtcH * 3600 + InpRangeStartUtcM * 60;
   datetime rangeEndUtc   = rangeStartUtc + InpRangeMinutes * 60;
   if(nowUtc < rangeEndUtc) return;             // range still forming

   //--- entry deadline, in London time
   datetime cutoffUtc = dayUtc + (InpEntryCutoffLdn - LondonOffset(nowUtc)) * 3600;
   if(nowUtc >= cutoffUtc) return;

   //--- build the range once per day
   if(!g_rangeValid || g_rangeDay != dayUtc)
     {
      g_rangeValid = false;
      if(!BuildRange(dayUtc)) { g_lastTradedDay = dayUtc; return; }  // mark the day done

      //--- correlation filter, evaluated once, right after the range forms
      double corr = 0.0; bool dataOk = false;
      if(InpUseFilter)
        {
         g_filterPassed = CorrelationOk(corr, dataOk);
         if(!dataOk)
           {
            Print("Correlation unavailable - SKIPPING the day rather than trading unfiltered.");
            g_lastTradedDay = dayUtc; return;
           }
         PrintFormat("corr(%s,%s,%dd) = %.3f -> %s", _Symbol, InpAudSymbol,
                     InpCorrDays, corr, g_filterPassed ? "trade" : "stand aside");
         if(!g_filterPassed) { g_lastTradedDay = dayUtc; return; }
        }
      else g_filterPassed = true;
     }
   if(!g_rangeValid || !g_filterPassed) return;

   //--- has a 60-minute block anchored on the range end just closed?
   // the M5 bar that just closed ended at `barTime` (server) = nowUtcBarEnd
   datetime justClosedEndUtc = (datetime)((long)barTime - g_gmtOffsetSec);
   long sinceEnd = (long)justClosedEndUtc - (long)rangeEndUtc;
   if(sinceEnd <= 0 || sinceEnd % (InpRangeMinutes * 60) != 0) return;

   double blockClose = iClose(_Symbol, PERIOD_M5, 1);
   if(blockClose <= 0.0) return;

   int dir = 0;
   if(blockClose > g_rangeHigh) dir = 1;
   else if(blockClose < g_rangeLow) dir = -1;
   if(dir == 0) return;

   //--- size and fire
   double width = g_rangeHigh - g_rangeLow;
   double stopDist = InpStopRangeMult * width;
   double lots = LotsForRisk(stopDist);
   if(lots <= 0.0) { g_lastTradedDay = dayUtc; return; }

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   bool ok = false;
   if(dir > 0)
      ok = trade.Buy(lots, _Symbol, 0.0, NormalizeDouble(ask - stopDist, digits), 0.0,
                     "AsiaOpenGold long");
   else
      ok = trade.Sell(lots, _Symbol, 0.0, NormalizeDouble(bid + stopDist, digits), 0.0,
                      "AsiaOpenGold short");

   if(ok)
     {
      g_lastTradedDay = dayUtc;
      PrintFormat("%s %.2f lots, range width %.2f, stop %.2f away",
                  dir > 0 ? "BUY" : "SELL", lots, width, stopDist);
     }
   else
      PrintFormat("Order failed: %d %s", trade.ResultRetcode(), trade.ResultRetcodeDescription());
  }
//+------------------------------------------------------------------+

// stubs so the translation unit links
datetime TimeGMT() { return 0; }
datetime TimeCurrent() { return 0; }
void TimeToStruct(datetime, MqlDateTime &s) { ZeroMemory(s); }
datetime StructToTime(MqlDateTime &) { return 0; }
string TimeToString(datetime, int) { return ""; }
int CopyRates(string, ENUM_TIMEFRAMES, int, int, MqlArray<MqlRates> &) { return 0; }
int CopyRates(string, ENUM_TIMEFRAMES, datetime, datetime, MqlArray<MqlRates> &) { return 0; }
datetime iTime(string, ENUM_TIMEFRAMES, int) { return 0; }
double iClose(string, ENUM_TIMEFRAMES, int) { return 0; }
bool SymbolSelect(string, bool) { return true; }
double SymbolInfoDouble(string, ENUM_SYMBOL_INFO_DOUBLE) { return 1.0; }
long SymbolInfoInteger(string, ENUM_SYMBOL_INFO_INTEGER) { return 2; }
double AccountInfoDouble(ENUM_ACCOUNT_INFO_DOUBLE) { return 2000.0; }
int PositionsTotal() { return 0; }
ulong PositionGetTicket(int) { return 0; }
string PositionGetString(ENUM_POSITION_PROPERTY_STRING) { return ""; }
long PositionGetInteger(ENUM_POSITION_PROPERTY_INTEGER) { return 0; }
int main() { OnInit(); OnTick(); return 0; }
