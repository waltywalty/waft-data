// Minimal MQL5 API shim: enough type and signature fidelity for a C++ compiler to
// type-check an EA's body. It does NOT emulate MetaTrader - it exists so that g++
// can find typos, undeclared identifiers, wrong argument counts and type errors.
#pragma once
#include <cstdio>
#include <cstring>
#include <cmath>
#include <cfloat>
#include <string>
#include <vector>
#include <algorithm>
#include <climits>

typedef long          datetime;
// ulong comes from <sys/types.h> on Linux
typedef unsigned int  uint;
typedef long long     longlong;
using string = std::string;

struct MqlDateTime { int year, mon, day, hour, min, sec, day_of_week, day_of_year; };
struct MqlRates { datetime time; double open, high, low, close; long tick_volume, spread, real_volume; };

template <class T> struct MqlArray {
   std::vector<T> v; bool series = false;
   T &operator[](int i) { if((int)v.size() <= i) v.resize(i + 1); return v[i]; }
};
template <class T> int ArrayResize(MqlArray<T> &a, int n) { a.v.resize(n); return n; }
template <class T> void ArraySetAsSeries(MqlArray<T> &a, bool s) { a.series = s; }
template <class T> void ZeroMemory(T &x) { std::memset(&x, 0, sizeof(T)); }

enum ENUM_TIMEFRAMES { PERIOD_M5, PERIOD_D1 };
enum ENUM_SYMBOL_INFO_DOUBLE { SYMBOL_TRADE_TICK_VALUE, SYMBOL_TRADE_TICK_SIZE,
                               SYMBOL_VOLUME_MIN, SYMBOL_VOLUME_MAX, SYMBOL_VOLUME_STEP,
                               SYMBOL_ASK, SYMBOL_BID };
enum ENUM_SYMBOL_INFO_INTEGER { SYMBOL_DIGITS };
enum ENUM_POSITION_PROPERTY_STRING { POSITION_SYMBOL };
enum ENUM_POSITION_PROPERTY_INTEGER { POSITION_MAGIC, POSITION_TIME };
enum ENUM_ACCOUNT_INFO_DOUBLE { ACCOUNT_EQUITY };
enum { INIT_SUCCEEDED = 0, INIT_FAILED = 1 };
enum { TIME_DATE = 1, TIME_MINUTES = 2 };

extern string _Symbol;

datetime TimeGMT();
datetime TimeCurrent();
void     TimeToStruct(datetime t, MqlDateTime &s);
datetime StructToTime(MqlDateTime &s);
string   TimeToString(datetime t, int mode = 0);

template <class... A> void Print(A... a) {}
template <class... A> void PrintFormat(const char *f, A... a) {}

inline double MathMax(double a, double b) { return a > b ? a : b; }
inline double MathMin(double a, double b) { return a < b ? a : b; }
inline double MathLog(double a) { return std::log(a); }
inline double MathSqrt(double a) { return std::sqrt(a); }
inline double MathRound(double a) { return std::round(a); }
inline double MathFloor(double a) { return std::floor(a); }
inline double NormalizeDouble(double v, int d) { return v; }

int  CopyRates(string sym, ENUM_TIMEFRAMES tf, int start, int count, MqlArray<MqlRates> &r);
int  CopyRates(string sym, ENUM_TIMEFRAMES tf, datetime from, datetime to, MqlArray<MqlRates> &r);
datetime iTime(string sym, ENUM_TIMEFRAMES tf, int shift);
double   iClose(string sym, ENUM_TIMEFRAMES tf, int shift);
bool     SymbolSelect(string sym, bool select);
double   SymbolInfoDouble(string sym, ENUM_SYMBOL_INFO_DOUBLE p);
long     SymbolInfoInteger(string sym, ENUM_SYMBOL_INFO_INTEGER p);
double   AccountInfoDouble(ENUM_ACCOUNT_INFO_DOUBLE p);
int      PositionsTotal();
ulong    PositionGetTicket(int i);
string   PositionGetString(ENUM_POSITION_PROPERTY_STRING p);
long     PositionGetInteger(ENUM_POSITION_PROPERTY_INTEGER p);

class CTrade {
public:
   void SetExpertMagicNumber(long m) {}
   void SetDeviationInPoints(long d) {}
   void SetTypeFillingBySymbol(string s) {}
   bool Buy(double vol, string sym = "", double price = 0.0, double sl = 0.0,
            double tp = 0.0, string comment = "") { return true; }
   bool Sell(double vol, string sym = "", double price = 0.0, double sl = 0.0,
             double tp = 0.0, string comment = "") { return true; }
   bool PositionClose(ulong ticket, ulong dev = ULONG_MAX) { return true; }
   uint ResultRetcode() { return 0; }
   string ResultRetcodeDescription() { return ""; }
};
