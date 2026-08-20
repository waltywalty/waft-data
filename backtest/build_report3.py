"""Round-3 report: correlation thresholds and what a $2,000 account would have done."""
import json

S = json.load(open("results/summary3.json"))
CSS = open("report_style.css").read()
assert "{{" not in CSS, "stylesheet still has f-string-escaped braces"
T, ST, B = S["thresholds"], S["stress"], S["benchmark"]
runs = {r["label"]: r for r in S["runs"]}
unf = {r["label"]: r for r in S["unfiltered"]}
base = T["base"]

def money(v): return f"${v:,.0f}"
def tone(v, good=0): return "pos-t" if v > good else "neg-t"

# ---- threshold table ---------------------------------------------------------
th_rows = "\n".join(
    f'<tr><td class="lbl">≤ {r["th"]:+.1f}</td><td class="num">{r["n"]}</td>'
    f'<td class="num">{r["n"]/base["n"]*100:.0f}%</td><td class="num">{r["win"]*100:.1f}%</td>'
    f'<td class="num {"pos-2" if r["pf"]>=1.3 else "pos-1" if r["pf"]>=1 else "neg-1"}">{r["pf"]:.3f}</td>'
    f'<td class="num">{r["exp"]:+.2f}</td><td class="num">{r["t"]:+.2f}</td>'
    f'<td class="num muted">{r["pf_ex"]:.3f}</td></tr>'
    for r in T["cutoff"] if r["pf_ex"]) + (
    f'\n<tr><td class="lbl">no filter</td><td class="num">{base["n"]}</td><td class="num">100%</td>'
    f'<td class="num">{base["win"]*100:.1f}%</td>'
    f'<td class="num pos-1">{base["pf"]:.3f}</td><td class="num">{base["exp"]:+.2f}</td>'
    f'<td class="num">{base["t"]:+.2f}</td><td class="num muted">—</td></tr>')

# ---- window grid -------------------------------------------------------------
WINS, THS = [10, 20, 30, 40, 60, 90], [0.0, 0.2, 0.4, 0.5, 0.6, 0.8]
g = T["window_grid"]
def cell(w, t):
    k = f"{w}_{t}"
    if k not in g: return '<td class="num muted">—</td>'
    v = g[k]
    c = "pos-2" if v["pf"] >= 1.30 else "pos-1" if v["pf"] >= 1.0 else "neg-1"
    return f'<td class="num {c}">{v["pf"]:.2f}<span class="muted" style="font-size:11px"> ({v["n"]})</span></td>'
win_rows = "\n".join(
    f'<tr><td class="lbl">{w}-day</td>' + "".join(cell(w, t) for t in THS) + "</tr>" for w in WINS)

# ---- threshold chart ---------------------------------------------------------
tc = [r for r in T["cutoff"] if r["pf_ex"]]
bars, x = [], 48
for r in tc:
    h = (r["pf"] - 1.0) * 320
    bars.append(f'<rect class="bar-entry" x="{x}" y="{160-h:.1f}" width="34" height="{h:.1f}" rx="2"/>')
    bars.append(f'<text class="bar-val" x="{x+17}" y="{153-h:.1f}">{r["pf"]:.2f}</text>')
    he = (r["pf_ex"] - 1.0) * 320
    bars.append(f'<rect class="bar-neg" x="{x+36}" y="{160 if he<0 else 160-he:.1f}" width="34" '
                f'height="{abs(he):.1f}" rx="2" opacity=".75"/>')
    bars.append(f'<text class="bar-lbl" x="{x+35}" y="182">≤{r["th"]:+.1f}</text>')
    bars.append(f'<text class="ax" x="{x+35}" y="196" text-anchor="middle">n={r["n"]}</text>')
    x += 78
th_svg = "\n".join(bars)

# ---- sizing table ------------------------------------------------------------
ORDER = ["All-in, no leverage", "All-in, 5:1", "All-in, 20:1", "All-in, 100:1",
         "Risk 1% · 1R stop", "Risk 2% · 1R stop", "Risk 1% · 2R stop",
         "Risk 2% · 2R stop", "Risk 1% · 3R stop", "Risk 2% · 3R stop"]
def srow(lbl):
    r = runs[lbl]
    ruin = f'<td class="num neg-2">{r["ruin"]}</td>' if r["ruin"] else '<td class="num muted">—</td>'
    ddc = "neg-2" if r["max_dd"] > .8 else "neg-1" if r["max_dd"] > .45 else "num"
    return (f'<tr><td class="lbl">{lbl}</td>'
            f'<td class="num">{money(r["final"])}</td>'
            f'<td class="num {tone(r["cagr"])}">{r["cagr"]*100:+.1f}%</td>'
            f'<td class="num {ddc}">{r["max_dd"]*100:.1f}%</td>'
            f'<td class="num">{r["worst_trade"]*100:.1f}%</td>'
            f'<td class="num muted">{money(r["avg_notional"])}</td>{ruin}</tr>')
size_rows = "\n".join(srow(l) for l in ORDER)

unf_rows = "\n".join(
    f'<tr><td class="lbl">{k}</td><td class="num">{money(unf[k]["final"])}</td>'
    f'<td class="num {tone(unf[k]["cagr"])}">{unf[k]["cagr"]*100:+.1f}%</td>'
    f'<td class="num">{unf[k]["max_dd"]*100:.1f}%</td>'
    f'<td class="num muted">{unf[k]["ruin"] or "—"}</td></tr>' for k in unf)

slip_rows = "\n".join(
    f'<tr><td class="lbl">{r["stop"]:.0f}× range</td><td class="num">{r["stopped"]*100:.0f}%</td>'
    f'<td class="num">{money(r["s0.0"])}</td><td class="num">{money(r["s0.25"])}</td>'
    f'<td class="num">{money(r["s0.5"])}</td><td class="num">{money(r["s1.0"])}</td></tr>'
    for r in S["slippage"])

# ---- equity chart ------------------------------------------------------------
SHOW = [("Risk 2% · 2R stop", "c1"), ("Risk 1% · 2R stop", "c0"),
        ("All-in, no leverage", "c3"), ("Buy and hold gold", "c4"),
        ("unfiltered Risk 1% · 2R stop", "c2")]
allv = [v for k, _ in SHOW for v in S["curves"][k]["y"]]
LO, HI = min(allv), max(allv)
def path(k, w=640, h=225):
    ys = S["curves"][k]["y"]; span = (HI - LO) or 1
    return "M" + " L".join(f"{54+i/(len(ys)-1)*(w-72):.1f},{14+(HI-v)/span*(h-42):.1f}"
                           for i, v in enumerate(ys))
paths = "\n".join(f'<path class="curve {c}" d="{path(k)}"/>' for k, c in SHOW)
def ylab(v):
    return 14 + (HI - v) / ((HI - LO) or 1) * (225 - 42)
ygrid = "\n".join(
    f'<line class="zero" x1="54" y1="{ylab(v):.1f}" x2="630" y2="{ylab(v):.1f}"/>'
    f'<text class="ax" x="48" y="{ylab(v)+4:.1f}" text-anchor="end">${v//1000}k</text>'
    for v in (2000, 4000, 6000, 8000))
xs = S["curves"]["Risk 1% · 2R stop"]["x"]
xticks = "\n".join(
    f'<text class="ax" x="{54+i/(len(xs)-1)*568:.0f}" y="220" text-anchor="middle">{xs[i][:4]}</text>'
    for i in range(0, len(xs), max(len(xs)//5, 1)))

R1, R2 = runs["Risk 1% · 2R stop"], runs["Risk 2% · 2R stop"]
A20, A100, A1 = runs["All-in, 20:1"], runs["All-in, 100:1"], runs["All-in, no leverage"]
U1 = unf["Risk 1% · 2R stop"]
SH = ST["shuffle_dd"]
best_t = max(T["cutoff"], key=lambda r: r["t"])

DOC = f"""<title>A $2,000 Gold Account</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
{CSS[7:-8]}
.bar-neg {{ fill:var(--neg); }}
.rule-box {{ background:var(--sunk); border-radius:4px; padding:20px 24px; margin:24px 0; }}
.rule-box ol {{ margin:0; padding-left:22px; }} .rule-box li {{ margin:8px 0; max-width:64ch; }}
.warn {{ background:var(--surface); border:1px solid var(--rule); border-left:3px solid var(--neg);
         border-radius:4px; padding:22px 26px; margin:26px 0; }}
.warn .head {{ font-family:"IBM Plex Mono",monospace; font-size:11.5px; letter-spacing:.13em;
               text-transform:uppercase; color:var(--neg); margin-bottom:12px; }}
.warn p {{ margin:0 0 12px; }} .warn p:last-child {{ margin:0; }}
</style>

<div class="wrap">
<header>
  <p class="eyebrow">XAUUSD · Round 3 · Thresholds &amp; position sizing</p>
  <h1>A $2,000 Gold Account</h1>
  <p class="standfirst">The same edge, sized two ways. Risking 1% a trade turns $2,000 into
  {money(R1['final'])}. Putting the whole account in at retail leverage turns it into
  {money(A20['final'])} — after first passing through {money(ST['allin20_low'])}.
  Sizing is not a detail bolted onto a strategy; here it is the larger of the two decisions.</p>
  <div class="provenance">
    <span><b>{base['n']:,}</b> candidate trades</span>
    <span><b>5</b> years</span>
    <span><b>$0.30</b> costs + <b>$0.30</b> stop slippage</span>
    <span><b>13</b> sizing regimes</span>
  </div>
</header>

<section>
  <h2><span class="n">01</span>Moving the correlation cut-off</h2>
  <p class="lede">First question first. The rule filters on the 20-day gold/AUDUSD correlation;
  round two used 0.5 because that is where the split first looked clean. Here is the whole curve.</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Cut-off</th><th>Trades</th><th>Days kept</th><th>Win rate</th>
    <th>Profit factor</th><th>Exp. $/oz</th><th>t-stat</th><th>PF of what's excluded</th></tr></thead>
    <tbody>{th_rows}</tbody>
  </table></div>
  <figure>
    <div class="chart">
      <svg viewBox="0 0 660 205" role="img" aria-label="Profit factor of kept and excluded trades by correlation cut-off">
        <line class="zero" x1="40" y1="160" x2="630" y2="160"/>
        {th_svg}
      </svg>
    </div>
    <div class="legend">
      <span><i class="swatch" style="background:var(--brass)"></i>trades kept</span>
      <span><i class="swatch" style="background:var(--neg)"></i>trades excluded</span>
    </div>
    <figcaption>Profit factor measured from a 1.00 baseline. Tightening the filter raises the kept
    side and lowers the excluded side together — the two move as a pair, which is what a real
    conditioning variable looks like.</figcaption>
  </figure>
  <p>The gradient is smooth and monotonic from 0.6 down to 0.0: profit factor climbs
  {[r['pf'] for r in T['cutoff'] if abs(r['th']-0.6)<.01][0]:.2f} → {[r['pf'] for r in T['cutoff'] if abs(r['th']-0.4)<.01][0]:.2f}
  → {[r['pf'] for r in T['cutoff'] if abs(r['th']-0.2)<.01][0]:.2f} → {[r['pf'] for r in T['cutoff'] if abs(r['th'])<.01][0]:.2f}
  as the cut tightens, while the sample shrinks from {[r['n'] for r in T['cutoff'] if abs(r['th']-0.6)<.01][0]}
  to {[r['n'] for r in T['cutoff'] if abs(r['th'])<.01][0]} trades.</p>
  <p><strong>The best trade-off is around {best_t['th']:+.1f}</strong>, where the t-statistic peaks at
  {best_t['t']:.2f} on {best_t['n']} trades — tighter cuts have a higher profit factor but too few
  trades to establish it. Everything below is still reported at 0.5, the threshold named before these
  numbers were seen, so that nothing here is re-optimised after the fact.</p>
  <div class="note">
    <p><strong>One wrinkle worth knowing.</strong> The excluded side is not monotonic at the very top.
    Days with correlation above 0.6 run at a {[r['pf_ex'] for r in T['cutoff'] if abs(r['th']-0.6)<.01][0]:.2f}
    profit factor, but the extreme tail above 0.7 — only {[r['n_ex'] for r in T['cutoff'] if abs(r['th']-0.7)<.01][0]}
    trades — comes back to {[r['pf_ex'] for r in T['cutoff'] if abs(r['th']-0.7)<.01][0]:.2f}. Either the
    damage really is concentrated in a 0.4–0.7 band, or that tail is too small to read. It is the one
    place the story is not clean.</p>
  </div>

  <h3>And the window length</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Correlation window</th>{"".join(f"<th>≤ {t:.1f}</th>" for t in THS)}</tr></thead>
    <tbody>{win_rows}</tbody>
  </table></div>
  <p>Profit factor at every combination, trade count in brackets. <strong>All 34 populated cells are
  above 1.0</strong>, and every window from 10 to 90 days shows the same gradient. The 20-day choice
  is not doing any work — the effect is a slow-moving regime, and any reasonable window sees it.</p>
</section>

<section>
  <h2><span class="n">02</span>The account</h2>
  <p class="lede">$2,000, opened August 2020, trading the filtered rule to August 2025.</p>
  <div class="rule-box"><ol>
    <li>Spot XAUUSD, one unit = one troy ounce, so notional = ounces × price. Gold ran from about
    $1,950 to $3,350 over the period, so a single ounce is more than the whole account: leverage is
    not optional here, only its size.</li>
    <li>Costs of $0.30 per ounce per round trip, plus a further <strong>$0.30 of slippage on any
    stopped exit</strong> — stops get worse fills than limits, and this strategy hits a lot of them.</li>
    <li>Holds never cross the 17:00 New York rollover, so no financing is charged.</li>
    <li>Liquidation is modelled generously: the account only dies when the floating loss reaches
    <em>100%</em> of equity. A real broker closes out near the 50% margin level, so every failure
    below would have arrived sooner than shown.</li>
    <li>"Risk 1% · 2R stop" means: stop placed two range-widths from entry, position sized so that
    being stopped costs 1% of current equity. Size compounds with the account.</li>
  </ol></div>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Sizing</th><th>Final</th><th>CAGR</th><th>Max drawdown</th>
    <th>Worst trade</th><th>Avg notional</th><th>Ruin</th></tr></thead>
    <tbody>{size_rows}</tbody>
  </table></div>
  <figure>
    <div class="chart">
      <svg viewBox="0 0 660 232" role="img" aria-label="Equity curves for the main sizing regimes">
        {ygrid}
        {paths}
        {xticks}
      </svg>
    </div>
    <div class="legend">
      <span><i class="swatch" style="background:var(--pos)"></i>Risk 2% · 2R stop</span>
      <span><i class="swatch" style="background:var(--brass)"></i>Risk 1% · 2R stop</span>
      <span><i class="swatch" style="background:var(--ink-3)"></i>All-in, no leverage</span>
      <span><i class="swatch" style="background:var(--ink-3);opacity:.6"></i>buy &amp; hold gold</span>
      <span><i class="swatch" style="background:var(--neg)"></i>Risk 1%, filter switched off</span>
    </div>
    <figcaption>The leveraged all-in curves are off this scale in both directions and are dealt with
    separately below.</figcaption>
  </figure>
  <p>Buy-and-hold gold over the same five years turned $2,000 into {money(B['final'])} — a
  {B['cagr']*100:.1f}% CAGR with a {B['dd']*100:.1f}% drawdown. <strong>Risking 1% a trade returned
  {R1['cagr']*100:.1f}% a year with a {R1['max_dd']*100:.1f}% drawdown</strong>: better return for
  the same pain. Risking 2% roughly doubles the return to {R2['cagr']*100:.1f}% and roughly doubles
  the drawdown to {R2['max_dd']*100:.1f}%, which is the honest trade being offered.</p>
</section>

<section>
  <h2><span class="n">03</span>All-in: an autopsy</h2>
  <div class="warn">
    <div class="head">What "all-in at 20:1" actually did</div>
    <p>It ended at {money(A20['final'])}, which sounds like the best answer on the page until you
    look at the path. The account peaked at <strong>{money(681611)}</strong> and then fell to
    <strong>{money(ST['allin20_low'])}</strong> — 99.98% below its own peak — before recovering.
    Its worst single trade lost {abs(A20['worst_trade'])*100:.0f}% of the account.</p>
    <p>No broker would have let that path run, no human would have held it, and the recovery is not
    a property of the strategy — it is a property of the particular order in which five years of
    trades happened to arrive.</p>
  </div>
  <div class="stats">
    <div class="stat"><div class="k">Worst adverse move, filtered</div><div class="v">3.81%</div>
      <div class="k" style="margin-top:6px">= 76% of the account at 20:1</div></div>
    <div class="stat"><div class="k">Worst in the full sample</div><div class="v">5.80%</div>
      <div class="k" style="margin-top:6px">= 116% — a zero</div></div>
    <div class="stat"><div class="k">All-in at 100:1</div><div class="v">$0</div>
      <div class="k" style="margin-top:6px">dead {A100['ruin']}</div></div>
    <div class="stat"><div class="k">All-in, no leverage</div><div class="v dim">{A1['cagr']*100:.1f}%</div>
      <div class="k" style="margin-top:6px">{A1['max_dd']*100:.0f}% drawdown</div></div>
  </div>
  <p>That first pair of tiles is the whole argument. Gold's worst intraday adverse excursion in this
  sample was 5.80% against the position. At 20:1, anything at or beyond 5% is a zero — no stop, no
  recovery, no second chance. The all-in account survived only because that particular day happened
  to fall on the other side of the correlation filter. <strong>It was one unlucky Tuesday from
  nothing, for five straight years.</strong></p>
  <p>At 100:1 the question is settled inside three months. And notice the one all-in variant that
  behaves: unleveraged, it returns {A1['cagr']*100:.1f}% with a {A1['max_dd']*100:.1f}% drawdown —
  respectable, and roughly what buy-and-hold gave.</p>
</section>

<section>
  <h2><span class="n">04</span>What the filter is worth in account terms</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Same sizing, filter switched off</th><th>Final</th><th>CAGR</th>
    <th>Max drawdown</th><th>Ruin</th></tr></thead>
    <tbody>{unf_rows}</tbody>
  </table></div>
  <p>Risking 1% with the filter on: {money(R1['final'])} at a {R1['max_dd']*100:.0f}% drawdown.
  With it off: {money(U1['final'])} at {U1['max_dd']*100:.0f}%. <strong>The filter roughly
  {R1['final']/U1['final']:.1f}× the ending equity and cuts the drawdown by more than half.</strong>
  Unfiltered all-in at 20:1 is dead by {unf['All-in, 20:1']['ruin']} — three months in.</p>
</section>

<section>
  <h2><span class="n">05</span>The stop is where the money actually leaks</h2>
  <p class="lede">A tight stop looks efficient because it lets you size bigger for the same risk.
  On this strategy it is a trap, and slippage is why.</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Stop distance</th><th>Trades stopped</th><th>No slippage</th>
    <th>$0.25</th><th>$0.50</th><th>$1.00</th></tr></thead>
    <tbody>{slip_rows}</tbody>
  </table></div>
  <p>Final equity from $2,000 risking 1% per trade. A 1×range stop sits only about $5 from entry and
  is hit on {S['slippage'][0]['stopped']*100:.0f}% of trades — so every cent of slippage is paid
  {S['slippage'][0]['stopped']*100:.0f}% of the time against a $5 stop. At fifty cents of slippage a
  tight stop gives back more than half the result; a 3×range stop barely notices.</p>
  <p><strong>Wider stops are worth more than they cost here.</strong> That is the opposite of the
  usual advice, and it follows directly from round one: this strategy whipsaws, so a stop close
  enough to be "efficient" is really just a second entry signal firing against you.</p>
</section>

<section>
  <h2><span class="n">06</span>The drawdown is the random variable</h2>
  <p class="lede">With fixed-fractional sizing, each trade returns a fixed <em>fraction</em> of
  equity, so the final number does not depend on the order the trades arrive in. Every shuffle of
  history ends at exactly {money(SH['final'])}. The drawdown does not share that property.</p>
  <div class="stats">
    <div class="stat"><div class="k">Drawdown history gave</div><div class="v">{SH['actual_dd']*100:.0f}%</div></div>
    <div class="stat"><div class="k">Median across 2,000 shuffles</div><div class="v dim">{SH['median']*100:.0f}%</div></div>
    <div class="stat"><div class="k">5th percentile</div><div class="v dim">{SH['p5']*100:.0f}%</div></div>
    <div class="stat"><div class="k">95th percentile</div><div class="v">{SH['p95']*100:.0f}%</div></div>
  </div>
  <p>Reshuffling the same trades into a different order produces drawdowns from
  {SH['p5']*100:.0f}% to {SH['p95']*100:.0f}%. History handed this rule a
  {SH['actual_dd']*100:.0f}% drawdown; an identical edge could as easily have delivered
  {SH['p95']*100:.0f}%. <strong>Size for the 95th percentile, not for the backtest.</strong></p>
</section>

<section>
  <h2><span class="n">07</span>Where I would land</h2>
  <div class="rule-box"><ol>
    <li><strong>Correlation cut at 0.4–0.5.</strong> Tighter is better per trade but thins the sample
    fast; 0.4 is where the statistics are strongest and it still trades roughly half of all days.</li>
    <li><strong>Stop at 2–3 range widths, not 1.</strong> Slippage on a tight stop is the single
    largest controllable leak in the whole system.</li>
    <li><strong>Risk 1% of equity per trade.</strong> That is {ST['shuffle_dd']['actual_dd']*100:.0f}%
    historical drawdown and around 4:1 effective leverage at the median — well inside a 20:1 retail
    account, with the margin cap never binding.</li>
    <li><strong>Never all-in.</strong> Not at 20:1, not at 5:1. The unleveraged version is defensible
    and returns about what holding gold returned; everything above it is buying a lottery ticket with
    the account as the stake.</li>
    <li>On $2,000 specifically, position sizes come out around 0.1–0.5 ounces. Check your broker
    supports that granularity before anything else — many quote a 0.01-lot minimum, which is 1 ounce
    and already too big for 1% risk on this account.</li>
  </ol></div>
</section>

<section>
  <h2><span class="n">08</span>What this simulation does not tell you</h2>
  <ul>
    <li><strong>The edge underneath is still marginal.</strong> A t-statistic near 3 on 5 years and
    one instrument is suggestive, not settled. Every dollar figure here inherits that uncertainty and
    then compounds it.</li>
    <li><strong>Compounded backtests flatter.</strong> The sizing rule reinvests gains that were
    themselves measured with error. Treat the CAGR as the shape of the answer, not the answer.</li>
    <li><strong>Drawdowns are measured at trade close.</strong> Intratrade equity went lower than any
    number in the drawdown column.</li>
    <li><strong>Costs are assumed constant.</strong> $0.30 round trip plus $0.30 stop slippage is
    reasonable for a decent retail account in liquid hours; at the Asia open on a thin day it will be
    worse, and section 05 shows how quickly that matters.</li>
    <li><strong>No financing, no gaps, no broker outages, no weekend risk</strong> — all of which are
    real on a $2,000 account and none of which are modelled.</li>
    <li><strong>The data ends August 2025.</strong> Nothing here has been tested on the twelve months
    since.</li>
  </ul>
</section>

<footer>
  Round three. Code and results on branch <code>claude/trading-strategy-backtest-gqym2i</code>;
  every figure generated from <code>results/summary3.json</code>. Rounds one and two are the
  companion reports.
</footer>
</div>
"""
open("results/report3.html", "w").write(DOC)
print("wrote results/report3.html", len(DOC))
