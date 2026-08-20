"""Mechanically rewrite MQL5-only syntax into C++ so g++ can type-check the body.
Only syntax is touched; no logic is altered."""
import re, sys
src = open(sys.argv[1]).read()
out, n_arr = [], 0
for line in src.split("\n"):
    s = line
    if s.strip().startswith("#property") or s.strip().startswith("#include <Trade"):
        out.append("// [stripped] " + s.strip()); continue
    if re.match(r"\s*input\s+group\b", s):
        out.append("// [stripped] " + s.strip()); continue
    s = re.sub(r"^(\s*)input\s+", r"\1", s)                      # input X y = z;  ->  X y = z;
    # dynamic array declarations:  MqlRates g[], a[];  ->  MqlArray<MqlRates> g, a;
    m = re.match(r"^(\s*)(\w+)\s+((?:\w+\[\]\s*,\s*)*\w+\[\])\s*;\s*$", s)
    if m:
        indent, typ, names = m.groups()
        names = ", ".join(x.strip().replace("[]", "") for x in names.split(","))
        s = f"{indent}MqlArray<{typ}> {names};"
        n_arr += 1
    out.append(s)
body = "\n".join(out)
hdr = '#include "mql5_shim.h"\nstring _Symbol = "XAUUSD";\n'
open(sys.argv[2], "w").write(hdr + body + """
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
""")
print(f"rewrote {n_arr} dynamic-array declarations")
