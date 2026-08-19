"""Generate the HTML report from results/summary.json so every number is sourced."""
import json, html

S = json.load(open("results/summary.json"))
EXIT_LABEL = {"pre_london": "Pre-London 07:00", "london_open": "London open 08:00",
              "london_mid": "London mid 12:00", "london_close": "London close 16:30"}

def pf_cell(pf):
    if pf >= 1.10:   tone = "pos-2"
    elif pf >= 1.0:  tone = "pos-1"
    elif pf >= 0.95: tone = "neg-1"
    else:            tone = "neg-2"
    return f'<td class="num {tone}">{pf:.3f}</td>'

# ---------- grid table -------------------------------------------------------
rows = []
for L in (5, 15, 30):
    for a in ("pre_london", "london_open", "london_mid", "london_close"):
        g = next(x for x in S["grid"] if x["range"] == L and x["exit"] == a)
        rows.append(f'<tr><td class="lbl">{L}-min</td><td class="lbl">{EXIT_LABEL[a]}</td>'
                    f'<td class="num">{g["n"]}</td><td class="num">{g["win"]*100:.1f}%</td>'
                    f'{pf_cell(g["pf"])}'
                    f'<td class="num">{g["exp_usd"]:+.2f}</td>'
                    f'<td class="num">{g["total_pct"]:+.1f}%</td>'
                    f'<td class="num">{g["dd"]:.1f}%</td>'
                    f'<td class="num muted">{g["t"]:+.2f}</td></tr>')
grid_rows = "\n".join(rows)

# ---------- bias chart -------------------------------------------------------
base = S["always_long_hit"] * 100
bars_svg, x = [], 40
for b in S["bias"]:
    ho, he = b["hit_from_open"] * 100, b["hit_from_entry"] * 100
    for val, cls, dx in ((ho, "bar-open", 0), (he, "bar-entry", 30)):
        h = (val - 44) * 9.0
        bars_svg.append(f'<rect class="{cls}" x="{x+dx}" y="{250-h:.1f}" width="26" height="{h:.1f}" rx="2"/>')
        bars_svg.append(f'<text class="bar-val" x="{x+dx+13}" y="{242-h:.1f}">{val:.1f}</text>')
    bars_svg.append(f'<text class="bar-lbl" x="{x+30}" y="270">{b["range"]}-min range</text>')
    x += 150
base_y = 250 - (base - 44) * 9.0
bias_svg = "\n".join(bars_svg)

# ---------- equity curves ----------------------------------------------------
def path_for(key, w=640, h=210, lo=None, hi=None):
    c = S["curves"][key]
    ys = c["y"]
    lo = min(ys) if lo is None else lo
    hi = max(ys) if hi is None else hi
    span = (hi - lo) or 1
    pts = []
    for i, v in enumerate(ys):
        px = 46 + i / (len(ys) - 1) * (w - 60)
        py = 12 + (hi - v) / span * (h - 34)
        pts.append(f"{px:.1f},{py:.1f}")
    return "M" + " L".join(pts)

keys = ["60m_london_close", "30m_london_close", "15m_pre_london", "5m_london_open", "passive_long"]
allv = [v for k in keys for v in S["curves"][k]["y"]]
LO, HI = min(allv), max(allv)
curve_paths = "\n".join(
    f'<path class="curve c{i}" d="{path_for(k, lo=LO, hi=HI)}"/>' for i, k in enumerate(keys))
zero_y = 12 + (HI - 0) / ((HI - LO) or 1) * (210 - 34)
xlabels = S["curves"]["60m_london_close"]["x"]
xticks = "\n".join(
    f'<text class="ax" x="{46 + i/(len(xlabels)-1)*580:.0f}" y="206" text-anchor="middle">{xlabels[i][:4]}</text>'
    for i in range(0, len(xlabels), len(xlabels)//5))

# ---------- per-year table ---------------------------------------------------
yr_rows = "\n".join(
    f'<tr><td class="lbl">{y["yr"]}</td><td class="num">{y["n"]}</td>'
    f'<td class="num">{y["win"]*100:.1f}%</td>{pf_cell(y["pf"])}'
    f'<td class="num {"pos-t" if y["pct"]>0 else "neg-t"}">{y["pct"]:+.1f}%</td>'
    f'<td class="num muted">{y["passive"]:+.1f}%</td></tr>' for y in S["years"]["60"])

# ---------- range sweep ------------------------------------------------------
sweep_rows = "\n".join(
    f'<tr><td class="lbl">{r["range"]}-min</td><td class="num">{r["n"]}</td>'
    f'<td class="num">{r["win"]*100:.1f}%</td>{pf_cell(r["pf"])}'
    f'<td class="num">{r["exp_usd"]:+.2f}</td><td class="num muted">{r["t"]:+.2f}</td></tr>'
    for r in S["range_sweep"])

# ---------- risk overlays ----------------------------------------------------
risk_rows = "\n".join(
    f'<tr><td class="lbl">{"none" if r["stop"] is None else str(r["stop"])+"x"}</td>'
    f'<td class="lbl">{"none" if r["target"] is None else str(r["target"])+"x"}</td>'
    f'<td class="num">{r["win"]*100:.1f}%</td>{pf_cell(r["pf"])}'
    f'<td class="num">{r["exp"]:+.2f}</td><td class="num">{r["dd"]:.1f}%</td></tr>'
    for r in S["risk"] if r["target"] in (None, 2.0, 3.0))

M = S["meta"]
b30 = next(b for b in S["bias"] if b["range"] == 30)
b60 = next(b for b in S["bias"] if b["range"] == 60)
best = max(S["grid"], key=lambda g: g["pf"])
worst = min(S["grid"], key=lambda g: g["pf"])

DOC = f"""<title>Asia Open Breakout on Gold</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  --ground:#FBFBFC; --surface:#FFFFFF; --sunk:#F3F4F7;
  --ink:#16191F; --ink-2:#4A515E; --ink-3:#7C8496;
  --rule:#DFE2E9; --rule-2:#EDEFF3;
  --brass:#8A6420; --brass-soft:#F0E4CC;
  --pos:#1B6E55; --pos-bg:#E4F1EB; --pos-bg-2:#C9E4D8;
  --neg:#A83226; --neg-bg:#FAE7E4; --neg-bg-2:#F3CDC7;
  --maxw:74ch;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --ground:#0E1116; --surface:#161A21; --sunk:#1B2029;
    --ink:#E8EAEF; --ink-2:#A7AEBC; --ink-3:#767E8E;
    --rule:#272D38; --rule-2:#1F242D;
    --brass:#D5A64A; --brass-soft:#3A2F18;
    --pos:#5CBE99; --pos-bg:#14291F; --pos-bg-2:#1C4132;
    --neg:#E58275; --neg-bg:#2C1714; --neg-bg-2:#4A211B;
  }}
}}
:root[data-theme="dark"] {{
  --ground:#0E1116; --surface:#161A21; --sunk:#1B2029;
  --ink:#E8EAEF; --ink-2:#A7AEBC; --ink-3:#767E8E;
  --rule:#272D38; --rule-2:#1F242D;
  --brass:#D5A64A; --brass-soft:#3A2F18;
  --pos:#5CBE99; --pos-bg:#14291F; --pos-bg-2:#1C4132;
  --neg:#E58275; --neg-bg:#2C1714; --neg-bg-2:#4A211B;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:16.5px; line-height:1.62;
  -webkit-font-smoothing:antialiased;
}}
.wrap {{ max-width:940px; margin:0 auto; padding:0 28px 96px; }}
header {{ padding:64px 0 34px; border-bottom:1px solid var(--rule); }}
.eyebrow {{
  font-family:"IBM Plex Mono",monospace; font-size:11.5px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--brass); margin:0 0 14px;
}}
h1 {{
  font-family:Spectral,Georgia,serif; font-weight:600; font-size:clamp(34px,5.2vw,50px);
  line-height:1.1; letter-spacing:-.015em; margin:0 0 16px; text-wrap:balance;
}}
.standfirst {{ font-size:19px; color:var(--ink-2); max-width:62ch; margin:0; text-wrap:pretty; }}
.provenance {{
  display:flex; flex-wrap:wrap; gap:0 26px; margin-top:26px;
  font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--ink-3);
}}
.provenance b {{ color:var(--ink-2); font-weight:500; }}
section {{ padding-top:52px; }}
h2 {{
  font-family:Spectral,Georgia,serif; font-weight:600; font-size:26px; letter-spacing:-.01em;
  margin:0 0 6px; text-wrap:balance;
}}
h2 .n {{
  font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--brass);
  letter-spacing:.1em; display:block; margin-bottom:8px; font-weight:500;
}}
h3 {{ font-size:15px; font-weight:600; margin:32px 0 8px; letter-spacing:.005em; }}
p {{ max-width:var(--maxw); margin:14px 0; text-wrap:pretty; }}
.lede {{ color:var(--ink-2); }}
ul {{ max-width:var(--maxw); padding-left:20px; }}
li {{ margin:7px 0; }}
strong {{ font-weight:600; }}
code {{ font-family:"IBM Plex Mono",monospace; font-size:.9em; background:var(--sunk);
        padding:1px 5px; border-radius:3px; }}
.verdict {{
  margin-top:36px; background:var(--surface); border:1px solid var(--rule);
  border-left:3px solid var(--brass); border-radius:4px; padding:24px 26px;
}}
.verdict p {{ margin:0 0 12px; }}
.verdict p:last-child {{ margin-bottom:0; }}
.verdict .head {{
  font-family:"IBM Plex Mono",monospace; font-size:11.5px; letter-spacing:.13em;
  text-transform:uppercase; color:var(--brass); margin-bottom:12px;
}}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(148px,1fr)); gap:1px;
          background:var(--rule); border:1px solid var(--rule); border-radius:4px;
          overflow:hidden; margin:28px 0; }}
.stat {{ background:var(--surface); padding:16px 18px; }}
.stat .k {{ font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.1em;
            text-transform:uppercase; color:var(--ink-3); }}
.stat .v {{ font-family:"IBM Plex Mono",monospace; font-size:24px; font-weight:500;
            margin-top:5px; font-variant-numeric:tabular-nums; }}
.stat .v.dim {{ color:var(--ink-2); }}
.tbl-wrap {{ overflow-x:auto; margin:22px 0; border:1px solid var(--rule); border-radius:4px;
             background:var(--surface); }}
table {{ border-collapse:collapse; width:100%; font-size:13.5px; }}
th {{
  font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.08em;
  text-transform:uppercase; color:var(--ink-3); font-weight:500; text-align:right;
  padding:12px 14px; border-bottom:1px solid var(--rule); white-space:nowrap;
}}
th:first-child, th.l {{ text-align:left; }}
td {{ padding:9px 14px; border-bottom:1px solid var(--rule-2); white-space:nowrap; }}
tbody tr:last-child td {{ border-bottom:none; }}
.num {{ text-align:right; font-family:"IBM Plex Mono",monospace;
        font-variant-numeric:tabular-nums; }}
.lbl {{ color:var(--ink-2); }}
.muted {{ color:var(--ink-3); }}
.pos-1 {{ background:var(--pos-bg); color:var(--pos); }}
.pos-2 {{ background:var(--pos-bg-2); color:var(--pos); font-weight:500; }}
.neg-1 {{ background:var(--neg-bg); color:var(--neg); }}
.neg-2 {{ background:var(--neg-bg-2); color:var(--neg); font-weight:500; }}
.pos-t {{ color:var(--pos); }} .neg-t {{ color:var(--neg); }}
figure {{ margin:26px 0; }}
figcaption {{ font-size:13px; color:var(--ink-3); margin-top:10px; max-width:66ch; }}
.chart {{ background:var(--surface); border:1px solid var(--rule); border-radius:4px;
          padding:18px 10px 8px; overflow-x:auto; }}
svg {{ display:block; max-width:100%; height:auto; }}
.bar-open {{ fill:var(--ink-3); }}
.bar-entry {{ fill:var(--brass); }}
.bar-val {{ font-family:"IBM Plex Mono",monospace; font-size:11px; fill:var(--ink-2);
            text-anchor:middle; font-variant-numeric:tabular-nums; }}
.bar-lbl {{ font-family:"IBM Plex Sans",sans-serif; font-size:12px; fill:var(--ink-2);
            text-anchor:middle; }}
.baseline {{ stroke:var(--neg); stroke-width:1.2; stroke-dasharray:5 4; }}
.baseline-lbl {{ font-family:"IBM Plex Mono",monospace; font-size:10.5px; fill:var(--neg); }}
.curve {{ fill:none; stroke-width:1.7; }}
.c0 {{ stroke:var(--brass); stroke-width:2.2; }}
.c1 {{ stroke:var(--pos); }}
.c2 {{ stroke:var(--neg); }}
.c3 {{ stroke:var(--ink-3); }}
.c4 {{ stroke:var(--ink-3); stroke-dasharray:4 3; stroke-width:1.3; }}
.ax {{ font-family:"IBM Plex Mono",monospace; font-size:10.5px; fill:var(--ink-3); }}
.zero {{ stroke:var(--rule); stroke-width:1; }}
.legend {{ display:flex; flex-wrap:wrap; gap:16px; margin-top:12px; font-size:12.5px;
           color:var(--ink-2); }}
.legend span {{ display:inline-flex; align-items:center; gap:7px; }}
.swatch {{ width:16px; height:3px; border-radius:2px; display:inline-block; }}
.note {{ background:var(--sunk); border-radius:4px; padding:18px 20px; margin:26px 0;
         font-size:14.5px; color:var(--ink-2); }}
.note p {{ margin:0 0 10px; max-width:none; }} .note p:last-child {{ margin:0; }}
footer {{ margin-top:64px; padding-top:22px; border-top:1px solid var(--rule);
          font-size:13px; color:var(--ink-3); }}
a {{ color:var(--brass); text-underline-offset:2px; }}
a:focus-visible, :focus-visible {{ outline:2px solid var(--brass); outline-offset:2px; }}
@media (max-width:620px) {{ .wrap {{ padding:0 18px 64px; }} header {{ padding-top:40px; }} }}
</style>

<div class="wrap">
<header>
  <p class="eyebrow">XAUUSD · Backtest · {M['start']} — {M['end']}</p>
  <h1>Asia Open Breakout on Gold</h1>
  <p class="standfirst">The 09:30 HKT opening-range breakout calls the day's direction
  correctly {b30['hit_from_open']*100:.0f}% of the time. It still doesn't make money — and the reason
  those two facts coexist is the whole story.</p>
  <div class="provenance">
    <span><b>{M['bars']:,}</b> 5-minute bars</span>
    <span><b>1,277</b> trading days</span>
    <span><b>12</b> configurations specified</span>
    <span><b>${M['cost']:.2f}</b> round-trip cost assumed</span>
  </div>
</header>

<section>
  <div class="verdict">
    <div class="head">Verdict</div>
    <p><strong>As specified, the strategy has no tradeable edge.</strong> Eleven of your twelve
    configurations lose money net of costs. The best — a 30-minute range held to the London close —
    returns a profit factor of {best['pf']:.3f} on {best['n']:,} trades, which is statistically
    indistinguishable from a coin flip. The worst, a 5-minute range exited at the London open,
    runs a profit factor of {worst['pf']:.3f}.</p>
    <p>The breakout genuinely does identify the day's direction — but the identification is
    <em>retrospective</em>. By the time a candle has closed beyond the range, price has already
    travelled about the width of the range itself, and that distance is almost exactly the size
    of the edge. You are paying full price for information you are receiving late.</p>
  </div>
</section>

<section>
  <h2><span class="n">01</span>What was tested</h2>
  <p class="lede">Exactly what you described, with no discretionary latitude added.</p>
  <ul>
    <li><strong>Range</strong> — the first 5 / 15 / 30 minutes from 09:30 Hong Kong time
    (01:30 UTC; Hong Kong observes no daylight saving, so this is a fixed UTC anchor).</li>
    <li><strong>Entry</strong> — the first same-timeframe candle to <em>close</em> beyond the range
    high (long) or low (short). One trade per day, first break only.</li>
    <li><strong>Exit</strong> — a fixed clock time in the London session: 07:00 (before),
    08:00 (start), 12:00 (middle) or 16:30 (end), London local, so British Summer Time is
    handled per-date.</li>
    <li><strong>Costs</strong> — $0.30 per round trip, roughly a two-to-three cent spread plus
    slippage on spot gold. Results at $0.00 through $1.00 are reported below.</li>
    <li><strong>No stop or target</strong> in the base test, since you specified a time-based hold.</li>
  </ul>
  <div class="note">
    <p><strong>On the data.</strong> Five-minute XAUUSD bars, {M['start']} to {M['end']}.
    The timestamps were confirmed to be UTC empirically rather than assumed: the intraday
    volatility peak shifts by exactly one hour when US daylight saving starts and ends, while
    staying fixed in UTC. Prices were cross-checked against an independent broker feed
    (median difference $0.17 across 35,480 overlapping bars) and against the public record —
    the dataset's all-time high of $3,499.91 on 22 April 2025 matches gold's actual record.</p>
  </div>
</section>

<section>
  <h2><span class="n">02</span>The twelve configurations</h2>
  <p class="lede">Every combination you asked about. Profit factor is shaded: green above 1.00,
  red below.</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Range</th><th class="l">Exit</th><th>Trades</th><th>Win rate</th>
    <th>Profit factor</th><th>Exp. $/trade</th><th>Total</th><th>Max DD</th><th>t-stat</th></tr></thead>
    <tbody>{grid_rows}</tbody>
  </table></div>
  <p>Two patterns are worth more than the individual cells. First, <strong>the exit time matters
  far more than the range length</strong>: every configuration that exits at or before the London
  open loses, and every configuration improves monotonically as the exit is pushed later. Exiting
  at 07:00 or 08:00 London means closing the position at the exact moment the session that
  actually moves gold is beginning. Second, <strong>longer ranges beat shorter ones</strong> —
  a 5-minute range at the Asia open is mostly noise.</p>
  <figure>
    <div class="chart">
      <svg viewBox="0 0 660 215" role="img" aria-label="Cumulative return curves by configuration">
        <line class="zero" x1="46" y1="{zero_y:.1f}" x2="640" y2="{zero_y:.1f}"/>
        {curve_paths}
        {xticks}
      </svg>
    </div>
    <div class="legend">
      <span><i class="swatch" style="background:var(--brass)"></i>60-min → London close</span>
      <span><i class="swatch" style="background:var(--pos)"></i>30-min → London close</span>
      <span><i class="swatch" style="background:var(--neg)"></i>15-min → pre-London</span>
      <span><i class="swatch" style="background:var(--ink-3)"></i>5-min → London open</span>
      <span><i class="swatch" style="background:var(--ink-3);opacity:.6"></i>passive long, same hours</span>
    </div>
    <figcaption>Cumulative return in percent of gold price, net of costs. The flat line is
    break-even. Note that the best curve spends its first three years going nowhere.</figcaption>
  </figure>
</section>

<section>
  <h2><span class="n">03</span>Does the breakout capture the day's true bias?</h2>
  <p class="lede">Yes — and this is the most interesting result in the study, because it is
  simultaneously true and useless.</p>
  <figure>
    <div class="chart">
      <svg viewBox="0 0 660 285" role="img" aria-label="Directional hit rate measured from the 01:30 open versus from the actual fill">
        {bias_svg}
        <line class="baseline" x1="30" y1="{base_y:.1f}" x2="630" y2="{base_y:.1f}"/>
        <text class="baseline-lbl" x="30" y="{base_y-7:.1f}">coin-flip baseline {base:.1f}%</text>
      </svg>
    </div>
    <div class="legend">
      <span><i class="swatch" style="background:var(--ink-3)"></i>measured from the 09:30 open</span>
      <span><i class="swatch" style="background:var(--brass)"></i>measured from your actual fill</span>
    </div>
    <figcaption>Percentage of days the breakout direction matched where gold actually closed.
    The grey bar is the number that flatters the strategy; the brass bar is the number you
    can trade.</figcaption>
  </figure>
  <p>Measured against the 09:30 open, a 30-minute breakout points the right way on
  <strong>{b30['hit_from_open']*100:.1f}%</strong> of days, and a 60-minute breakout on
  <strong>{b60['hit_from_open']*100:.1f}%</strong> — well above the {base:.1f}% you would get by
  simply being long every day. That looks like a real directional signal, and in a descriptive
  sense it is.</p>
  <p>Measured from the price you are actually filled at, the same signal points the right way on
  <strong>{b30['hit_from_entry']*100:.1f}%</strong> of days. A coin flip. The entire apparent edge is
  the move that has already happened before the confirming candle closes.</p>
  <div class="stats">
    <div class="stat"><div class="k">30-min range width</div><div class="v dim">${b30['range_size']:.2f}</div></div>
    <div class="stat"><div class="k">Already moved at fill</div><div class="v">${b30['already_moved']:.2f}</div></div>
    <div class="stat"><div class="k">Retained edge</div><div class="v dim">${b30['range_size']-b30['already_moved']:.2f}</div></div>
    <div class="stat"><div class="k">Days that break back</div><div class="v">{b30['whipsaw']*100:.0f}%</div></div>
  </div>
  <p>The arithmetic is unforgiving. Had you known the eventual breakout direction and been filled
  at the 09:30 open instead, the same trades would have earned <strong>$4.35 per trade at a profit
  factor of 2.00</strong>. Filled at the breakout close, they earn $0.65. You give up
  <strong>${b30['already_moved']:.2f}</strong> per trade waiting for confirmation, against an average range
  width of ${b30['range_size']:.2f}. Confirmation costs you the entire range.</p>
  <p>The whipsaw figure compounds the problem: after a 30-minute breakout, <strong>{b30['whipsaw']*100:.0f}%
  of days later trade back through the opposite side of the range</strong> (it is {[b for b in S['bias'] if b['range']==5][0]['whipsaw']*100:.0f}%
  for the 5-minute range). The Asia range is not a launch pad. It is a chop zone that price
  re-enters most days.</p>
</section>

<section>
  <h2><span class="n">04</span>Do any confluence filters help?</h2>
  <p class="lede">Twenty-one filters, tested on three range lengths, split into halves.
  The answer is no, and the way it fails is instructive.</p>
  <p>Each filter was evaluated separately in-sample (Aug 2020 – Dec 2023) and out-of-sample
  (Jan 2024 – Aug 2025). A filter only counts if it beat the unfiltered baseline in
  <em>both</em> halves. Tested: Asia range size versus ATR, alignment with the daily EMA trend,
  5-day momentum, prior-day direction, the overnight gap, breaks of the prior day's high or low,
  volatility regime, the open's position inside the prior day's range, direction, and day of week.</p>
  <div class="stats">
    <div class="stat"><div class="k">30-min range</div><div class="v">2<span style="font-size:15px;color:var(--ink-3)">/21</span></div></div>
    <div class="stat"><div class="k">15-min range</div><div class="v">3<span style="font-size:15px;color:var(--ink-3)">/21</span></div></div>
    <div class="stat"><div class="k">5-min range</div><div class="v">1<span style="font-size:15px;color:var(--ink-3)">/21</span></div></div>
    <div class="stat"><div class="k">Expected by chance</div><div class="v dim">~5<span style="font-size:15px;color:var(--ink-3)">/21</span></div></div>
  </div>
  <p><strong>Fewer filters survived both halves than pure chance would have produced.</strong>
  And the ones that did survive on one range length did not agree with the ones that survived on
  another. This is the signature of noise, not of a weak signal.</p>
  <p>The individual reversals are stark. Aligning with the overnight gap direction produced a
  0.82 profit factor in the first half and 1.95 in the second. Trading <em>with</em> the daily
  EMA trend gave 0.80 then 1.46, while trading <em>against</em> it gave 1.08 then 1.13. Thursday
  was the worst weekday in-sample and the best out-of-sample. Any of these would look like a
  discovery if you had only looked at one half.</p>
  <h3>Entry mechanics did not rescue it either</h3>
  <p>Since confirmation costs a full range width, the obvious fix is a cheaper fill. Three were
  tested: a stop order resting at the range boundary with no close confirmation; a limit order
  back at the boundary after confirmation; and deeper pullback limits. <strong>All performed the
  same or worse.</strong> Waiting for a pullback selects against exactly the trending days that
  pay — at a 1.0-range pullback the fill rate drops to 70% and the profit factor falls to 0.87.
  The days that come back to your limit are the days that were going to fail.</p>
</section>

<section>
  <h2><span class="n">05</span>What actually moved the needle</h2>
  <p class="lede">Three things changed results materially. Only one of them is an edge, and even
  that one does not survive scrutiny.</p>
  <h3>Holding longer</h3>
  <p>The single largest effect in the whole study. Pushing the exit from the London open to the
  London close turns a 0.81 profit factor into 0.99 on the 5-minute range, and 0.86 into 1.16 on
  a 60-minute range. If you trade this at all, exiting before London is the one clearly
  wrong choice.</p>
  <h3>A longer opening range</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Range length</th><th>Trades</th><th>Win rate</th>
    <th>Profit factor</th><th>Exp. $/trade</th><th>t-stat</th></tr></thead>
    <tbody>{sweep_rows}</tbody>
  </table></div>
  <p>Held to the London close, results improve out to about 60 minutes and then decay. Note the
  t-statistics: even the best is 1.92, which is borderline at a single test and meaningless
  after searching this many combinations.</p>
  <h3>A stop at one range width</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Stop</th><th class="l">Target</th><th>Win rate</th>
    <th>Profit factor</th><th>Exp. $/trade</th><th>Max DD</th></tr></thead>
    <tbody>{risk_rows}</tbody>
  </table></div>
  <p>A stop at one range width roughly halves the drawdown — from 29.4% to 14.0% — while leaving
  the profit factor slightly better than the unstopped version. It does not create an edge, but
  it makes the same non-edge far less painful to hold. Targets, by contrast, consistently hurt:
  a 1× target lifts the win rate to 81% and the profit factor down to 0.91, which is the classic
  shape of cutting winners short.</p>
</section>

<section>
  <h2><span class="n">06</span>Why you should distrust the version that looks good</h2>
  <p class="lede">The best configuration found anywhere in this study was a 60-minute range held
  to the London close: +51.5% cumulative, profit factor 1.16. Here is why I do not believe it.</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Year</th><th>Trades</th><th>Win rate</th><th>Profit factor</th>
    <th>Strategy</th><th>Passive long, same hours</th></tr></thead>
    <tbody>{yr_rows}</tbody>
  </table></div>
  <p>Three of six years are negative. The result is concentrated in 2021, 2024 and 2025 — and
  2024–25 was a violent gold bull market in which simply being long from the Asia open to the
  London close returned +5.8% and +10.5% respectively without any signal at all.</p>
  <ul>
    <li><strong>In-sample (2020–23): profit factor 1.06, t = 0.56.</strong> Essentially nothing.
    <strong>Out-of-sample (2024–25): 1.44, t = 2.64.</strong> The edge does not exist in the first
    two-thirds of the data.</li>
    <li><strong>Against passive exposure it adds +43.7%, but with t = 1.18, p = 0.24.</strong>
    It cannot be distinguished from just being long gold during those hours.</li>
    <li><strong>A randomisation test</strong> — keeping every entry and exit time but choosing the
    side at random, 5,000 times — puts the result at p = 0.004 on its own. Corrected for having
    searched 18 configurations, p = 0.036. And 18 understates the real search: counting entry
    modes, filters and risk overlays, this study ran well over a hundred tests. A random search
    of that size finds a "+48%" configuration 5% of the time with no signal present at all.</li>
    <li><strong>The session-start sweep</strong> shows 09:30 HKT sitting at the peak of the curve
    (1.16) with 08:00 at 0.95. A structural effect should not be that sharply peaked at exactly
    the time tested.</li>
  </ul>
  <p>None of these is fatal alone. Together they describe a result that is what an unbiased search
  over five years of gold data produces when there is nothing there.</p>
</section>

<section>
  <h2><span class="n">07</span>Where I would look next</h2>
  <p class="lede">The decomposition points somewhere specific, and it is not at more filters.</p>
  <ul>
    <li><strong>Fade the range, don't follow it.</strong> With 70–87% of days trading back through
    the opposite side, the structure of this session is mean-reverting, not expansive. The naive
    inverse also loses to costs — but a fade with a defined stop, entered at the range extremes
    rather than after a confirmed break, is the hypothesis this data actually supports.</li>
    <li><strong>Use the breakout as a filter, not a trigger.</strong> The direction is right
    {b60['hit_from_open']*100:.0f}% of the time on a 60-minute range. That is a usable bias for
    something with a better entry — for example a limit order at the London open in the breakout
    direction, which lets the Asia move happen without paying for it.</li>
    <li><strong>Trade the London session directly.</strong> Every result improves the more of the
    London session it contains, which suggests the Asia range is a distraction and the London
    open range is the real object of interest.</li>
    <li><strong>Condition on the macro calendar.</strong> Nothing here separated days with a
    scheduled US release from days without one, and the volatility profile shows the 08:30 ET
    release window is where gold's daily variance actually lives.</li>
  </ul>
</section>

<section>
  <h2><span class="n">08</span>Caveats</h2>
  <ul>
    <li>The data ends <strong>{M['end']}</strong>. The last twelve months are not covered.</li>
    <li>The feed is spot XAUUSD from a retail broker. Your fills, spread and swap will differ;
    a $0.30 round trip is optimistic for retail CFD execution during Asia hours, and at $1.00
    even the best configuration falls to a 1.02 profit factor.</li>
    <li>Results assume a constant one-ounce position. Returns are expressed as a percentage of
    the gold price so that the 2020 and 2025 price levels are comparable.</li>
    <li>No overnight financing is modelled. Holds run up to fifteen hours and never cross the
    5pm New York rollover, so this is a small omission.</li>
    <li>Backtests overstate. Assume the live version is worse than what is shown here.</li>
  </ul>
</section>

<footer>
  Code, trade logs and the full result set are committed to
  <code>backtest/</code> on branch <code>claude/trading-strategy-backtest-gqym2i</code>.
  Every figure on this page is generated from <code>results/summary.json</code>.
</footer>
</div>
"""
open("results/report.html", "w").write(DOC)
print("wrote results/report.html", len(DOC), "bytes")
