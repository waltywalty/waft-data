"""Round-8 report: the NY fade, and three strategies from the wild."""
import json

F = json.load(open("results/ny_fade.json"))
M = json.load(open("results/meanrev.json"))
J = json.load(open("results/judas.json"))
J2 = json.load(open("results/judas2.json"))
A = json.load(open("results/adapt.json"))
R = json.load(open("reference/strategy_research.json"))["research"]
CSS = open("report_style.css").read()
assert "{{" not in CSS

pc = lambda v, hi=1.0: "pos-1" if v >= hi else "neg-1"
pc2 = lambda v: "pos-2" if v >= 1.3 else "pos-1" if v >= 1.0 else "neg-1" if v >= 0.8 else "neg-2"


def num(v, fmt=".3f", cls=None):
    c = f' class="num {cls}"' if cls else ' class="num"'
    return f"<td{c}>{v:{fmt}}</td>"


def srow(s, lbl, halves=True):
    h = ""
    if halves and s and "is_pf" in s:
        agree = '<span class="pos-t">agree</span>' if s.get("agree") else '<span class="neg-t">disagree</span>'
        h = (f'<td class="num muted">{s["is_pf"]:.3f}</td>'
             f'<td class="num muted">{s["os_pf"]:.3f}</td><td class="lbl">{agree}</td>')
    return (f'<tr><td class="lbl">{lbl}</td><td class="num">{s["n"]}</td>'
            f'{num(s["pf"], cls=pc(s["pf"]))}{num(s["exp"], "+.2f")}'
            f'{num(s["t"], "+.2f")}{h}</tr>')


# ---------------------------------------------------------------- 02 fade
bf = F["grid"]["by_filter"]
ford = "\n".join(
    f'<tr><td class="lbl">{k}</td><td class="num">{v["n"]}</td>'
    f'{num(v["median_pf"], cls=pc(v["median_pf"]))}'
    f'{num(v["best_t"], "+.2f")}<td class="num">{v["n_above_1"]}/{v["n"]}</td></tr>'
    for k, v in bf.items())

EXL = {"ny+30m": "First 30 min", "ny+60m": "First hour", "ny+90m": "First 90 min",
       "ny+2h": "First 2 hours", "ny_lunch": "To NY lunch", "ny_close": "To NY close",
       "range_mid": "Range midpoint", "range_far": "Far side of range",
       "prev_day": "Previous day H/L", "asia": "Asia H/L", "london": "London H/L"}
ftop = "\n".join(
    f'<tr><td class="lbl">{int(r["range"])}-min</td><td class="lbl">{EXL[r["exit"]]}</td>'
    f'<td class="lbl muted">{r["filter"]}</td><td class="num">{int(r["n"])}</td>'
    f'<td class="num">{r["win"]*100:.1f}%</td>{num(r["pf"], cls=pc(r["pf"]))}'
    f'{num(r["t"], "+.2f")}</tr>' for r in F["grid"]["top8"])

fvar = "\n".join(srow(s, s["label"], halves=False) for s in
                 F["variations"]["stop"] + F["variations"]["overshoot"])
fcost = "\n".join(
    f'<tr><td class="lbl">${c["cost"]:.2f}</td>{num(c["pf"], cls=pc(c["pf"]))}'
    f'{num(c["exp"], "+.2f")}</tr>' for c in F["variations"]["costs"])
fisos = "\n".join(
    f'<tr><td class="lbl">{r["range"]}-min · {EXL[r["exit"]]}</td>'
    f'<td class="lbl muted">{r["filter"]}</td><td class="num">{int(r["is_n"])}</td>'
    f'{num(r["is_pf"])}<td class="num muted">{r["is_t"]:+.2f}</td>'
    f'<td class="num">{int(r["os_n"])}</td>{num(r["os_pf"], cls=pc(r["os_pf"]))}</tr>'
    for r in F["isos"]["honest_top5"])

# ---------------------------------------------------------------- 04 meanrev
g = {(r["tf"], r["trigger"], r["k"]): r for r in M["grid"]}
mrows = ""
for k in (1.5, 2.0, 2.6, 3.0, 3.5):
    cells = ""
    for tf in (5, 15, 60):
        for tr in ("close_out", "close_back"):
            r = g.get((tf, tr, k))
            if r:
                cells += (f'<td class="num {pc2(r["pf"])}">{r["pf"]:.3f}'
                          f'<span class="muted" style="font-size:11px"> ({r["n"]})</span></td>')
            else:
                cells += '<td class="num muted">—</td>'
    star = ' <span class="muted">&larr; as advertised</span>' if k == 2.6 else ""
    mrows += f'<tr><td class="lbl">{k:.1f}&sigma;{star}</td>{cells}</tr>\n'

msess = "\n".join(
    f'<tr><td class="lbl">{r["session"]}</td><td class="lbl muted">{r["trigger"]}</td>'
    f'<td class="num">{r["n"]}</td><td class="num">{r["win"]*100:.1f}%</td>'
    f'{num(r["pf"], cls=pc(r["pf"]))}{num(r["t"], "+.2f")}</tr>' for r in M["sessions"])

gate_rows = ""
for r in A["adx_gate"]:
    lbl = f'ADX {"&lt;" if r["side"] == "below" else "&ge;"} {r["th"]} ({"quiet" if r["side"] == "below" else "trending"})'
    gate_rows += srow(r, lbl)
for r in A["band_walk"]:
    gate_rows += srow(r, r["bucket"].replace(">=", "&ge;"))
gate_rows += srow(A["news_scrub"]["kept"], "outside 8:30/14:00 ET news windows")
gate_rows += srow(A["news_scrub"]["dropped"], "inside news windows")
for r in A["vwap_fade"]:
    gate_rows += srow(r, f'NY-anchored VWAP bands, k={r["k"]:.1f}')

misos = "\n".join(
    f'<tr><td class="lbl">{r["cell"]}</td><td class="num">{int(r["is_n"])}</td>'
    f'{num(r["is_pf"])}<td class="num muted">{r["is_t"]:+.2f}</td>'
    f'<td class="num">{int(r["os_n"])}</td>{num(r["os_pf"], cls=pc(r["os_pf"]))}</tr>'
    for r in M["isos"]["honest_top5"])
mcost = "\n".join(
    f'<tr><td class="lbl">${c["cost"]:.2f}</td>{num(c["pf"], cls=pc(c["pf"]))}'
    f'{num(c["exp"], "+.2f")}</tr>' for c in M["variations"]["costs"])

# ---------------------------------------------------------------- 05 judas
fu = J["funnel"]
frow = lambda s: (f'<tr><td class="lbl">{s}</td><td class="num">{fu[s]["days"]}</td>'
                  f'<td class="num">{fu[s].get("no_bias", 0)}</td>'
                  f'<td class="num">{fu[s].get("no_sweep", 0)}</td>'
                  f'<td class="num">{fu[s].get("no_reclaim", 0)}</td>'
                  f'<td class="num">{fu[s].get("stop_too_close", 0)}</td>'
                  f'<td class="num">{fu[s].get("ok", 0)}</td></tr>')
funnel = "\n".join(frow(s) for s in ("asia", "london", "ny"))

jgrid = sorted(J["grid"], key=lambda r: -r["t"])[:5]
jtop = "\n".join(
    f'<tr><td class="lbl">{r["session"]} / {r["bias"]} / {r["target"]}</td>'
    f'<td class="num">{r["n"]}</td><td class="num">{r["win"]*100:.1f}%</td>'
    f'{num(r["pf"], cls=pc(r["pf"]))}{num(r["t"], "+.2f")}</tr>' for r in jgrid)

jvar = "\n".join(srow(s, s["label"].replace(">=", "&ge;"), halves=False) for s in
                 J["variations"]["sweep_window"] + J["variations"]["widen"]
                 + J["variations"]["stop"])
jcost = "\n".join(
    f'<tr><td class="lbl">${c["cost"]:.2f}</td>{num(c["pf"], cls=pc(c["pf"]))}'
    f'{num(c["exp"], "+.2f")}</tr>' for c in J["variations"]["costs"])

jcanon = "\n".join(
    f'<tr><td class="lbl">{r["session"]} / {r["bias"]} / {r["target"]}</td>'
    f'<td class="num">{r["n"]}</td><td class="num">{r["win"]*100:.1f}%</td>'
    f'{num(r["pf"], cls=pc(r["pf"]))}{num(r["t"], "+.2f")}</tr>'
    for r in sorted(J2["canonical"], key=lambda r: -r["pf"]))
jdeep = ""
for cell, rows in J2["deep_sweep"].items():
    for r in rows:
        jdeep += (f'<tr><td class="lbl">{cell}</td><td class="lbl">&ge; ${r["dmin"]:.1f}</td>'
                  f'<td class="num">{r["n"]}</td>{num(r["pf"], cls=pc(r["pf"]))}'
                  f'{num(r["t"], "+.2f")}</tr>\n')
jisos = "\n".join(
    f'<tr><td class="lbl">{r["cell"]}</td><td class="num">{int(r["is_n"])}</td>'
    f'{num(r["is_pf"])}<td class="num muted">{r["is_t"]:+.2f}</td>'
    f'<td class="num">{int(r["os_n"])}</td>{num(r["os_pf"], cls=pc(r["os_pf"]))}</tr>'
    for r in J["isos"]["honest_top5"])

# ---------------------------------------------------------------- 06 adaptations
astops = ""
for r in A["atr_stops"]:
    if r["f"] is None:
        lbl = "no stop"
    elif r["f"] == "2R":
        lbl = "2 &times; range (deployed)"
    else:
        lbl = f'{r["f"]:.2f} &times; ATR14'
    sr = "" if r.get("stop_rate") is None else f'{r["stop_rate"] * 100:.0f}%'
    astops += (f'<tr><td class="lbl">{lbl}</td><td class="num">{sr}</td>'
               f'<td class="num">{r["n"]}</td>{num(r["pf"], cls=pc2(r["pf"]))}'
               f'{num(r["t"], "+.2f")}<td class="num muted">{r["is_pf"]:.3f}</td>'
               f'<td class="num muted">{r["os_pf"]:.3f}</td></tr>\n')

aq = lambda rows, name: "\n".join(
    f'<tr><td class="lbl">{name} quintile {r["q"]}</td><td class="num">{r["n"]}</td>'
    f'{num(r["pf"], cls=pc2(r["pf"]))}{num(r["t"], "+.2f")}'
    f'<td class="num muted">{r["is_pf"]:.3f}</td><td class="num muted">{r["os_pf"]:.3f}</td>'
    f'<td class="lbl">{"<span class=pos-t>agree</span>" if r["agree"] else "<span class=neg-t>disagree</span>"}</td></tr>'
    for r in rows)
aratr = aq(A["ratr_quintiles"], "range/ATR")
arvol = aq(A["rvol_quintiles"], "rel. volume")

acrab = "".join(srow(A["crabel"][k], lbl) for k, lbl in
                (("nr7_on", "after an NR7 session"), ("nr7_off", "not after NR7"),
                 ("inside_on", "after an inside day"), ("inside_off", "not after inside day")))
adelay = (srow(A["trigger_delay"]["first"], "break on the first post-range candle")
          + srow(A["trigger_delay"]["later"], "break on a later candle"))
aveto = (srow(A["prior_day_veto"]["vetoed"], "trades the veto would drop")
         + srow(A["prior_day_veto"]["kept"], "trades the veto keeps"))

fb = A["first_bar"]
afb = ""
for tf in (5, 15):
    for sk, sl in (("bar", "bar extreme"), ("0.1", "0.10&times;ATR"), ("0.25", "0.25&times;ATR")):
        a_, f_ = fb.get(f"{tf}_{sk}_all"), fb.get(f"{tf}_{sk}_filt")
        if a_ and f_:
            afb += (f'<tr><td class="lbl">{tf}m bar, stop at {sl}</td>'
                    f'<td class="num">{a_["n"]}</td>{num(a_["pf"], cls=pc(a_["pf"]))}'
                    f'<td class="num">{f_["n"]}</td>{num(f_["pf"], cls=pc(f_["pf"]))}'
                    f'{num(f_["t"], "+.2f")}</tr>\n')

# ---------------------------------------------------------------- research cards
def card(i, extra):
    r = R[i]
    return f"""<div class="verdict"><div class="head">{r["strategy"]}</div>
<p>{r["what_it_is"]}</p>{extra}
<p class="muted" style="font-size:13.5px">{len(r["sources"])} sources reviewed; full structured notes in
<code>backtest/reference/strategy_research.json</code>.</p></div>"""


FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Spectral:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600'
         '&family=IBM+Plex+Mono:wght@400;500&display=swap">')

HTML = f"""<title>Borrowed Edges</title>
{FONTS}
{CSS}
<div class="wrap">
<header>
<p class="eyebrow">XAUUSD research &middot; round 8</p>
<h1>Three strategies from the wild, and a fade</h1>
<p class="standfirst">We fetched what practitioners actually do to make the opening-range
breakout, the 2.6-standard-deviation pullback, and the ICT &ldquo;Judas sweep&rdquo; work
&mdash; 56 sources across three research sweeps &mdash; then ran their mechanical
versions and our own adaptations through the house battery. Three clean negatives, one
mirror-image confirmation of our filter&rsquo;s mechanism, and two forward-test leads for
the one strategy that already works.</p>
<div class="provenance">
<span>data <b>350,903 &times; 5-min bars, Aug 2020 &ndash; Aug 2025</b></span>
<span>cost <b>$0.30/oz round trip</b></span>
<span>tests this round <b>&asymp; 330</b></span>
</div>
</header>

<section>
<h2><span class="n">01</span>The verdict up front</h2>
<div class="stats">
<div class="stat"><div class="k">NY fade &middot; 123 cells</div><div class="v neg-t">loses gross</div></div>
<div class="stat"><div class="k">2.6&sigma; fade &middot; zero-cost PF</div><div class="v dim">1.006</div></div>
<div class="stat"><div class="k">Judas sweep &middot; honest OOS PF</div><div class="v neg-t">0.201</div></div>
<div class="stat"><div class="k">Asia-ORB leads found</div><div class="v pos-t">2</div></div>
</div>
<div class="verdict">
<div class="head">Round-8 verdict</div>
<p><strong>Fading the New York open fails</strong> exactly as following it did: the fixed
reference cell loses $0.13/oz <em>before</em> costs. The NY open is two-sided noise once the
confirmation candle has closed &mdash; the candle itself consumes the move, in both directions.</p>
<p><strong>The 2.6&sigma; pullback is a spread-sized effect.</strong> Gold&rsquo;s 15-minute
closes do revert after a 2.6&sigma; stretch &mdash; by almost exactly one bid-ask spread.
Zero-cost PF 1.006; net PF 0.860. No practitioner gate (ADX regime, band-walk veto, news
scrub, VWAP anchoring) finds a sub-population that pays more.</p>
<p><strong>The Judas sweep is adversely selected on gold.</strong> It loses at zero cost
(PF 0.735 gross), every one of 45 + 12 cells and every canonical refinement stays under
water, and our take-everything win rate (27.1%) lands within 2.5 points of the one
independent mechanical ICT test we could find (29.6%). This replicates round 2&rsquo;s
sweep-entry result on a completely different construction.</p>
<p><strong>The useful output is on our own strategy:</strong> the practitioner research
suggested activity gating and exit-structure tests for the Asia ORB. Two survive with the
same sign in both halves &mdash; high relative volume in the opening range (top-quintile
PF 1.843) and Crabel&rsquo;s inside-day conditioning (PF 1.616) &mdash; and the stop-distance
gradient confirms tight stops only hurt. All of it stays a forward-test candidate; the
deployed configuration does not change on subgroup evidence this thin.</p>
</div>
</section>

<section>
<h2><span class="n">02</span>Fading the New York open</h2>
<p class="lede">Round 7 ended with a hypothesis: NY-open breaks hold direction but leave
nothing after the fill, so perhaps the money is on the other side. We built the mirror
engine &mdash; identical trigger, position inverted, stops beyond the break, reversion
targets &mdash; and proved it exact: on {F["symmetry"]["n"]:,} matched trades the fade&rsquo;s
P&amp;L is the follow&rsquo;s negated to machine precision, so any difference in results is
the strategy, not the code.</p>
<p>It loses. {bf["all"]["n_above_1"]} of {bf["all"]["n"]} unfiltered cells clear PF 1.0, the
best <em>t</em> anywhere unfiltered is {bf["all"]["best_t"]:+.2f}, and the zero-cost
expectancy of the reference cell is &minus;$0.13/oz &mdash; both directions of the NY open
lose before costs. One result is genuinely informative: the correlation filter&rsquo;s
ordering <strong>inverts</strong>, exactly as its mechanism predicts.</p>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Correlation regime</th><th>cells</th><th>median PF</th><th>best t</th><th>PF &gt; 1</th></tr></thead>
<tbody>{ford}</tbody></table></div>
<p>Fading is <em>worst</em> on low-correlation days &mdash; the days our Asia filter
selects because breakouts follow through &mdash; and least bad when gold trades as a dollar
proxy. The filter fails to produce a tradeable NY edge in either direction, but its
regime-ordering survives a mirror test it was never designed for. That is independent
evidence the regime is real.</p>
<h3>Best cells of 123 (in-sample, for the record)</h3>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Range</th><th class="l">Exit</th><th class="l">Filter</th><th>n</th><th>win</th><th>PF</th><th>t</th></tr></thead>
<tbody>{ftop}</tbody></table></div>
<h3>Parameter variations (fixed cell: 15-min range, midpoint target)</h3>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Variant</th><th>n</th><th>PF</th><th>exp $/oz</th><th>t</th></tr></thead>
<tbody>{fvar}</tbody></table></div>
<div class="tbl-wrap" style="max-width:420px"><table>
<thead><tr><th class="l">Round trip</th><th>PF</th><th>exp $/oz</th></tr></thead>
<tbody>{fcost}</tbody></table></div>
<h3>The honest out-of-sample gate</h3>
<p>Ranked on pre-2024 <em>t</em> only, then read on 2024-25. The in-sample winners &mdash;
all high-correlation fade cells &mdash; collapse out of sample: median OS PF
{F["isos"]["honest_median_os_pf"]:.3f} against a population median of
{F["isos"]["population_median_os_pf"]:.3f}. The corr&gt;0.5 fade &ldquo;edge&rdquo; was a
2020-23 artifact.</p>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Cell</th><th class="l">Filter</th><th>IS n</th><th>IS PF</th><th>IS t</th><th>OS n</th><th>OS PF</th></tr></thead>
<tbody>{fisos}</tbody></table></div>
</section>

<section>
<h2><span class="n">03</span>What practitioners actually do</h2>
<p class="lede">Three research sweeps, 56 sources: academic papers, independent
replications, quant-practitioner backtests, and the retail material itself. The short
versions, with what we chose to test:</p>
{card(0, '''<p><strong>What has evidence:</strong> the Zarattini&ndash;Aziz papers (QQQ and
&ldquo;Stocks in Play&rdquo;) are the only ORB results with audited-quality replication, and
the replication is sobering: the QQQ edge is $0.07/share gross and dies at ~2.2&cent; of
slippage; 76% of the filtered variant&rsquo;s profit came from 2022 alone. The one filter
that beat a placebo was cross-asset confirmation (t=2.05). QuantifiedStrategies found the
same ORB rules <em>negative</em> on gold futures &mdash; independently corroborating our
117-cell NY null. <strong>We tested:</strong> their ATR-fraction stops, Crabel&rsquo;s
NR7/inside-day conditioning, relative-volume gating, trigger-time, prior-day-range veto,
and the first-bar-direction entry &mdash; all transplanted onto the Asia ORB (section 06).</p>''')}
{card(1, '''<p><strong>What has evidence:</strong> there is no canonical &ldquo;2.6 SD&rdquo;
strategy; the number maps onto Belkhayate&rsquo;s gold-famous Centre-of-Gravity bands
(2.618), 99%-confidence Bollinger variants (z = 2.576), and VWAP band ladders. The honest
literature is negative for gold specifically: an OU mean-reversion falsification study
found <em>every</em> micro-gold-future configuration unprofitable after realistic friction,
and Bollinger&rsquo;s own canon warns that closes outside the band are continuation, not
reversion, signals. <strong>We tested:</strong> the full k-gradient (1.5&ndash;3.5&sigma;)
across three timeframes and both trigger styles, plus every gate practitioners claim
rescues it (section 04).</p>''')}
{card(2, '''<p><strong>What has evidence:</strong> nothing audited. ICT&rsquo;s Judas swing has
no verified track record; claimed 55-65% win rates come from discretionary backtests that
exclude invalid setups after the fact. The one independent mechanical test we found
(OffBeatForex) won 29.6% of take-everything setups and only profited by discarding 92% of
them. The canonical spec is real enough to freeze, though: killzone windows (London 02:00-05:00 ET,
NY 08:30-10:00 ET), PDH/PDL 4-scenario bias, wick-through-close-back sweeps, stops beyond
the sweep wick. <strong>We tested:</strong> the frozen spec across 45 cells, then the
canonical refinements &mdash; killzones, PDH/PDL bias, minimum sweep depth (section 05).</p>''')}
</section>

<section>
<h2><span class="n">04</span>The 2.6&sigma; pullback: a spread-sized truth</h2>
<p class="lede">Judged the house way: on the gradient, not at the advertised point.
Profit factor at $0.30/oz cost, by band width, timeframe and trigger
(<code>close_out</code> enters on the first close beyond the band;
<code>close_back</code> waits for the close back inside &mdash; the practitioners&rsquo;
confirmation):</p>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Band width</th><th>5m out</th><th>5m back</th><th>15m out</th><th>15m back</th><th>60m out</th><th>60m back</th></tr></thead>
<tbody>{mrows}</tbody></table></div>
<p>Everything liquid is negative; the only PF &gt; 1 cells are n &le; 250 tails at
3.5&sigma; &mdash; spikes, not slopes. The mechanism is in the cost ladder of the fixed
cell (15m, 2.6&sigma;, close-back):</p>
<div class="tbl-wrap" style="max-width:420px"><table>
<thead><tr><th class="l">Round trip</th><th>PF</th><th>exp $/oz</th></tr></thead>
<tbody>{mcost}</tbody></table></div>
<p><strong>At zero cost the strategy is exactly breakeven (PF 1.006, +$0.01/oz).</strong>
The mean reversion is real and worth one spread. There is nothing to harvest and nothing
mysterious to explain: gold&rsquo;s intraday stretches revert by precisely the amount the
market charges you to trade them.</p>
<h3>Sessions, and every gate the practitioners recommend</h3>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Session</th><th class="l">Trigger</th><th>n</th><th>win</th><th>PF</th><th>t</th></tr></thead>
<tbody>{msess}</tbody></table></div>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Gate (fixed cell)</th><th>n</th><th>PF</th><th>exp</th><th>t</th><th>20-23</th><th>24-25</th><th>sign</th></tr></thead>
<tbody>{gate_rows}</tbody></table></div>
<p>The claim that &ldquo;the trend gate <em>is</em> the strategy&rdquo; fails on gold: quiet-ADX
and trending-ADX trades lose at the same rate. So do the band-walk veto, the news scrub
(trades <em>inside</em> news windows were no worse), and VWAP anchoring (worse than the
rolling mean, t &minus;5.1 at 2&sigma;). Honest OOS: top-5 by IS <em>t</em> read
{M["isos"]["honest_median_os_pf"]:.3f} out of sample, population {M["isos"]["population_median_os_pf"]:.3f}
&mdash; nothing selectable either.</p>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Cell (tf / trigger / k)</th><th>IS n</th><th>IS PF</th><th>IS t</th><th>OS n</th><th>OS PF</th></tr></thead>
<tbody>{misos}</tbody></table></div>
</section>

<section>
<h2><span class="n">05</span>The Judas sweep: adverse selection, measured</h2>
<p class="lede">The user&rsquo;s spec, made mechanical: daily-structure gate (bullish
&rarr; longs only), causally-tracked unswept session and prior-day levels, a session-open
sweep against the bias, first 5-minute close back through the level as confirmation, stop
beyond the sweep extreme, one trade per session. 45 cells: 3 sessions &times; 3 bias
definitions &times; 5 targets.</p>
<div class="stats">
<div class="stat"><div class="k">grid median PF</div><div class="v neg-t">{J["grid_summary"]["median_pf"]:.3f}</div></div>
<div class="stat"><div class="k">best t of 45</div><div class="v dim">{J["grid_summary"]["best_t"]:+.2f}</div></div>
<div class="stat"><div class="k">zero-cost PF (fixed cell)</div><div class="v neg-t">0.735</div></div>
<div class="stat"><div class="k">honest OOS median</div><div class="v neg-t">{J["isos"]["honest_median_os_pf"]:.3f}</div></div>
</div>
<p>The fixed London cell loses <strong>$0.38/oz before any costs</strong>. This is not
friction; it is adverse selection: when a level is swept and reclaimed against the daily
trend, the reclaim close you buy is systematically followed by more of the original move.
Round 2 found the same for Asia sweep entries; this is an independent construction reaching
the same verdict, with a win rate (27.1% at 2R) almost identical to the one independent
mechanical ICT backtest in the literature (29.6%).</p>
<h3>Where the setup dies (sma20 bias, 2R target)</h3>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Session</th><th>days</th><th>no bias</th><th>no sweep</th><th>no reclaim</th><th>stop too close</th><th>trades</th></tr></thead>
<tbody>{funnel}</tbody></table></div>
<p>London mostly sweeps Asia&rsquo;s levels (153 of 192 trades), exactly as the ICT story
says &mdash; the sweeps happen; they just don&rsquo;t reverse. Median stop distance is
$1.54, so the $0.30 cost alone is {fu["cost_frac_of_r"]*100:.0f}% of one R before slippage.</p>
<h3>Least-bad of the 45 cells, and the variations</h3>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Cell</th><th>n</th><th>win</th><th>PF</th><th>t</th></tr></thead>
<tbody>{jtop}</tbody></table></div>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Variation (london / sma20 / 2R)</th><th>n</th><th>PF</th><th>exp</th><th>t</th></tr></thead>
<tbody>{jvar}</tbody></table></div>
<div class="tbl-wrap" style="max-width:420px"><table>
<thead><tr><th class="l">Round trip</th><th>PF</th><th>exp $/oz</th></tr></thead>
<tbody>{jcost}</tbody></table></div>
<h3>The canonical-ICT addendum</h3>
<p>The research surfaced refinements the base grid didn&rsquo;t use: the true killzone
windows (<code>ldnkz</code> opens 02:00 ET, <code>nykz</code> 08:30 ET), the PDH/PDL
4-scenario bias, and gold&rsquo;s &ldquo;deep sweep&rdquo; claim as a minimum-depth filter.
Every refinement moves the needle in the claimed direction; none gets near water:</p>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Cell</th><th>n</th><th>win</th><th>PF</th><th>t</th></tr></thead>
<tbody>{jcanon}</tbody></table></div>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Cell</th><th class="l">Min sweep depth</th><th>n</th><th>PF</th><th>t</th></tr></thead>
<tbody>{jdeep}</tbody></table></div>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Cell</th><th>IS n</th><th>IS PF</th><th>IS t</th><th>OS n</th><th>OS PF</th></tr></thead>
<tbody>{jisos}</tbody></table></div>
<p>The honest OOS is the worst this repo has recorded: the two Asia cells selected on
in-sample strength scored PF 0.000 out of sample &mdash; every 2024-25 trade lost.</p>
</section>

<section>
<h2><span class="n">06</span>Adapting the research to the strategy that works</h2>
<p class="lede">The productive half of the research was never the three new strategies
&mdash; it was the filter menu it suggested for our validated Asia ORB (n=652, PF 1.320,
t +2.54, the exact deployed trade set). 50 tests, each read with its 2020-23 / 2024-25
sign agreement.</p>
<h3>A. Stops: the Zarattini claim reverses on gold</h3>
<p>Their papers say tight ATR-fraction stops dominate. On gold the gradient runs smoothly
the other way &mdash; every tightening costs profit factor, and the no-stop hold is best.
Stops on this strategy only truncate a positive-drift distribution; the 2&times;-range stop
we deploy costs ~0.13 of PF and buys drawdown control, which remains a deliberate trade.</p>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Stop</th><th>stop-outs</th><th>n</th><th>PF</th><th>t</th><th>20-23</th><th>24-25</th></tr></thead>
<tbody>{astops}</tbody></table></div>
<h3>B. Activity gating: the edge lives on busy Asia opens</h3>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Bucket</th><th>n</th><th>PF</th><th>t</th><th>20-23</th><th>24-25</th><th>sign</th></tr></thead>
<tbody>{arvol}</tbody></table></div>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Bucket</th><th>n</th><th>PF</th><th>t</th><th>20-23</th><th>24-25</th><th>sign</th></tr></thead>
<tbody>{aratr}</tbody></table></div>
<p>Top-quintile relative volume (the gold analogue of &ldquo;Stocks in Play&rdquo;) is the
strongest subgroup either grid produced: PF 1.843, t +2.54, halves agreeing at 1.73 / 1.98.
The range-width/ATR version points the same way (q5 PF 1.733, agreeing) but its middle
quintiles are not monotone. Read both as one finding: <strong>the Asia edge concentrates on
high-activity opens</strong>, consistent with the ORB literature&rsquo;s
high-volatility-regime concentration.</p>
<h3>C. Crabel conditioning, trigger timing, and the rest</h3>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Condition</th><th>n</th><th>PF</th><th>exp</th><th>t</th><th>20-23</th><th>24-25</th><th>sign</th></tr></thead>
<tbody>{acrab}{adelay}{aveto}</tbody></table></div>
<p>Inside-day conditioning survives with agreement (PF 1.616 on n=94); NR7 does not
transfer (worse, and halves disagree). Earliest-break-is-best holds directionally but
weakly. The prior-day-range veto would delete trades that are <em>better</em> than the ones
it keeps &mdash; rejected.</p>
<h3>D. The first-bar-direction entry does not transfer</h3>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Variant</th><th>n (all)</th><th>PF (all)</th><th>n (corr&le;0.5)</th><th>PF (filtered)</th><th>t (filt.)</th></tr></thead>
<tbody>{afb}</tbody></table></div>
<p>Zarattini&rsquo;s 9:30-bar entry, transplanted to the Asia open, is dead: unfiltered PF
0.66&ndash;0.98, filtered at best breakeven, and 8 of 12 variants disagree across halves.
The 60-minute range confirmation is doing real selection work that a single bar cannot.</p>
<div class="note">
<p><strong>What changes, and what does not.</strong> Nothing here re-sizes the deployed
strategy. These are ~50 exploratory subgroup tests on an already-mined sample; by the
repo&rsquo;s standards the two survivors &mdash; top-quintile relative volume and inside-day
conditioning &mdash; are <em>forward-test candidates</em>: log them live alongside the
unconditioned strategy and evaluate on data neither this search nor the original one has
touched. The stop-gradient result stands on firmer ground (it is a re-read of a known
result on a smooth gradient) and its implication is a risk-preference choice, not an edge
claim.</p>
</div>
</section>

<section>
<h2><span class="n">07</span>The scoreboard</h2>
<div class="tbl-wrap"><table>
<thead><tr><th class="l">Round-8 study</th><th>tests</th><th class="l">headline</th><th class="l">verdict</th></tr></thead>
<tbody>
<tr><td class="lbl">NY-open fade</td><td class="num">141</td><td class="lbl">loses gross; corr ordering inverts as predicted</td><td class="lbl neg-t">dead</td></tr>
<tr><td class="lbl">2.6&sigma; pullback</td><td class="num">~90</td><td class="lbl">reversion exists, worth exactly one spread</td><td class="lbl neg-t">dead</td></tr>
<tr><td class="lbl">Judas sweep + canonical</td><td class="num">~100</td><td class="lbl">loses at zero cost; OOS 0.201</td><td class="lbl neg-t">dead</td></tr>
<tr><td class="lbl">Asia-ORB adaptations</td><td class="num">50</td><td class="lbl">rvol-q5 &amp; inside-day agree in both halves</td><td class="lbl pos-t">2 forward-test leads</td></tr>
</tbody></table></div>
<p>The repo&rsquo;s running tally after eight rounds: one strategy survives everything
(Asia 09:30-HKT 60-min ORB, corr &le; 0.5 &mdash; forward-test, don&rsquo;t size), and the
graveyard now holds raw breakouts (11/12), sweep-rejection entries (twice, independently),
same-day AUD confirmation, CNY as a filter, MGC under $25k, the NY open in both directions,
band mean reversion at every width, and the Judas sweep with and without its canon.</p>
</section>

<section>
<h2><span class="n">08</span>Methods, self-tests, and defects</h2>
<ul>
<li><strong>Symmetry proof.</strong> The fade engine is verified against the round-7 follow
engine: identical trade set, P&amp;L mirrored to 0.00e+00 on {F["symmetry"]["n"]:,} trades.</li>
<li><strong>Base-set drift caught by assertion.</strong> The adaptation script initially
rebuilt the Asia base with the research-side UTC correlation filter (n=657, PF 1.371); a
hard assert against the deployed numbers stopped it, and the script now loads the exact
deployed trade set (n=652, PF 1.320) from <code>trades_deployable.pkl</code>.</li>
<li><strong>One crash, no silent error.</strong> The first Block-B run died on a pandas
index-alignment bug in the reporting helper (boolean mask with a fresh index); it produced
a traceback, not wrong numbers, and was fixed and re-run.</li>
<li><strong>Causality.</strong> Sweep levels carry creation and first-crossing times, so
&ldquo;unswept at t&rdquo; is a lookup, not a scan; daily bias is lag-1 on FX sessions
labelled by end date; relative volume compares a completed range window to prior days;
every path walk excludes the right endpoint of open-stamped bars.</li>
<li><strong>Multiplicity.</strong> &asymp; 330 tests were run this round and all are
reported. No significance is claimed anywhere, so no max-statistic correction is invoked;
the two positive leads are named as candidates for forward testing precisely because
in-sample subgroup evidence at this test count cannot establish them.</li>
<li><strong>The 1-minute caveat stands.</strong> Data is 5-minute; the user&rsquo;s
1-minute confirmation variant remains bracketed, not measured.</li>
</ul>
<footer>
<p>Round 8 of the XAUUSD session-strategy research. Engines:
<code>ny_fade.py</code>, <code>meanrev.py</code>, <code>structure.py</code>,
<code>judas.py</code>; runners <code>run_ny_fade.py</code>, <code>run_meanrev.py</code>,
<code>run_judas.py</code>, <code>run_judas2.py</code>, <code>run_adapt.py</code>.
Research notes: <code>backtest/reference/strategy_research.json</code> (56 sources).
Cost model $0.30/oz round trip throughout; sensitivities at $0.00 / $0.15 / $0.60.</p>
</footer>
</section>
</div>
"""

open("results/report7.html", "w").write(HTML)
print(f"written results/report7.html ({len(HTML):,} bytes)")
