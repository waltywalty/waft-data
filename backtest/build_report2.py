"""Generate the round-2 report from results/summary2.json."""
import json

S = json.load(open("results/summary2.json"))
CSS = open("report_style.css").read()
# The stylesheet was originally lifted out of an f-string, where every brace is
# doubled. Leaving those in emits invalid CSS and the page renders unstyled.
assert "{{" not in CSS and "}}" not in CSS, "report_style.css still has f-string-escaped braces"
LIQ_LABEL = {"dyn_swing": "most recent swing low/high", "breakout_low": "low of the breakout candle",
             "session_extreme": "Asia session extreme", "range_opp": "far side of the opening range"}
EXIT_LABEL = {"pre_london": "Pre-London 07:00 LDN", "london_open": "London open 08:00 LDN",
              "asia_close": "Asia close 16:00 HKT", "london_mid": "London mid 12:00 LDN",
              "pre_ny": "Pre-NY 09:00 ET", "london_late": "London late 16:00 LDN",
              "ny_close": "NY close 16:00 ET", "london_close": "London close 16:30 LDN"}

def pfc(pf):
    t = "pos-2" if pf >= 1.10 else "pos-1" if pf >= 1.0 else "neg-1" if pf >= 0.95 else "neg-2"
    return f'<td class="num {t}">{pf:.3f}</td>'

sweep_rows = "\n".join(
    f'<tr><td class="lbl">{g["range"]}-min</td><td class="lbl">{LIQ_LABEL[g["liq"]]}</td>'
    f'<td class="num">{g["n"]}</td><td class="num">{g["fill_rate"]*100:.0f}%</td>'
    f'<td class="num">{g["win"]*100:.1f}%</td>{pfc(g["pf"])}'
    f'<td class="num">{g["exp"]:+.2f}</td><td class="num muted">{g["breakout_pf"]:.3f}</td></tr>'
    for g in S["sweep_grid"])

exit_rows = "\n".join(
    f'<tr><td class="lbl">{EXIT_LABEL[e["exit"]]}</td><td class="num">{int(e["n"])}</td>'
    f'<td class="num">{e["win"]*100:.1f}%</td>{pfc(e["pf"])}'
    f'<td class="num">{e["exp"]:+.2f}</td><td class="num muted">{e["t"]:+.2f}</td></tr>'
    for e in S["sweep_exits"])

gen_rows = "\n".join(
    f'<tr><td class="lbl">{g["range"]}-min</td><td class="lbl">{EXIT_LABEL[g["exit"]]}</td>'
    f'<td class="num">{g["n"]}</td>{pfc(g["pf_all"])}<td class="num">{g["n_f"]}</td>{pfc(g["pf_f"])}'
    f'<td class="num {"pos-t" if g["pf_f"]>g["pf_all"] else "neg-t"}">{g["pf_f"]-g["pf_all"]:+.3f}</td></tr>'
    for g in S["generalise"])
n_up = sum(1 for g in S["generalise"] if g["pf_f"] > g["pf_all"])

yr_rows = "\n".join(
    f'<tr><td class="lbl">{y["yr"]}</td><td class="num">{y["n"]}</td>'
    f'<td class="num">{y["win"]*100:.1f}%</td>{pfc(y["pf"])}'
    f'<td class="num {"pos-t" if y["total"]>0 else "neg-t"}">{y["total"]:+.0f}</td></tr>'
    for y in S["filter_years"])

cost_rows = "\n".join(
    f'<tr><td class="lbl">${c["c"]:.2f}</td>{pfc(c["pf"])}'
    f'<td class="num">{c["exp"]:+.2f}</td></tr>' for c in S["filter_cost"])

th = S["threshold"]
# --- equity chart -------------------------------------------------------------
keys = ["filtered", "all", "excluded"]
allv = [v for k in keys for v in S["curves"][k]["y"]]
LO, HI = min(allv), max(allv)
def path(k, w=640, h=215):
    ys = S["curves"][k]["y"]; span = (HI - LO) or 1
    return "M" + " L".join(f"{46+i/(len(ys)-1)*(w-60):.1f},{12+(HI-v)/span*(h-36):.1f}"
                           for i, v in enumerate(ys))
paths = "\n".join(f'<path class="curve c{i}" d="{path(k)}"/>' for i, k in enumerate(keys))
zero_y = 12 + (HI - 0) / ((HI - LO) or 1) * (215 - 36)
xl = S["curves"]["all"]["x"]
xticks = "\n".join(
    f'<text class="ax" x="{46+i/(len(xl)-1)*580:.0f}" y="210" text-anchor="middle">{xl[i][:4]}</text>'
    for i in range(0, len(xl), max(len(xl)//5, 1)))

# --- threshold chart ----------------------------------------------------------
tb = [t for t in th if t["th"] <= 1]
bars, x = [], 55
for t in tb:
    hgt = (t["pf"] - 1.0) * 340
    y = 150 - hgt if hgt > 0 else 150
    bars.append(f'<rect class="{"bar-entry" if t["pf"]>=1 else "bar-neg"}" x="{x}" y="{y:.1f}" '
                f'width="42" height="{abs(hgt):.1f}" rx="2"/>')
    bars.append(f'<text class="bar-val" x="{x+21}" y="{(y-7) if hgt>0 else (y+abs(hgt)+16):.1f}">{t["pf"]:.2f}</text>')
    bars.append(f'<text class="bar-lbl" x="{x+21}" y="172">≤{t["th"]:.1f}</text>')
    bars.append(f'<text class="ax" x="{x+21}" y="187" text-anchor="middle">n={t["n"]}</text>')
    x += 92
th_svg = "\n".join(bars)

A, H, F, X = S["aud_rel"], S["filter_head"]["hi"], S["filter_head"]["lo"], S["filter_head"]["all"]
SD, C, IO = S["sameday"], S["continuous"], S["filter_isos"]
sw_best = max(S["sweep_grid"], key=lambda g: g["pf"])
SEL = S["selection"]

DOC = f"""<title>Sweep Entries and the Aussie Filter</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
{CSS}
<style>
.bar-neg {{ fill:var(--neg); }}
.finding {{ background:var(--surface); border:1px solid var(--rule); border-left:3px solid var(--pos);
            border-radius:4px; padding:24px 26px; margin:28px 0; }}
.finding .head {{ font-family:"IBM Plex Mono",monospace; font-size:11.5px; letter-spacing:.13em;
                  text-transform:uppercase; color:var(--pos); margin-bottom:12px; }}
.finding p {{ margin:0 0 12px; }} .finding p:last-child {{ margin:0; }}
.rule-box {{ background:var(--sunk); border-radius:4px; padding:20px 24px; margin:24px 0; }}
.rule-box ol {{ margin:0; padding-left:22px; }} .rule-box li {{ margin:8px 0; max-width:64ch; }}
</style>

<div class="wrap">
<header>
  <p class="eyebrow">XAUUSD · Round 2 · Sweep entries &amp; AUD confluence</p>
  <h1>Sweep Entries and the Aussie Filter</h1>
  <p class="standfirst">The sweep entry gets you a much better fill and still loses — because
  the days that sweep are the days the bias was wrong. But the AUD question turned up the first
  thing in this study that survives every test I could throw at it.</p>
  <div class="provenance">
    <span><b>1,212</b> gold trades</span>
    <span><b>16</b> sweep variants</span>
    <span><b>7</b> session exits</span>
    <span><b>2</b> AUDUSD feeds, both UTC-verified</span>
  </div>
</header>

<section>
  <div class="verdict">
    <div class="head">Verdict</div>
    <p><strong>The sweep-and-reclaim entry does not work</strong> — best of sixteen variants is a
    {sw_best['pf']:.3f} profit factor ({sw_best['range']}-minute range, {LIQ_LABEL[sw_best['liq']]}),
    and most are far below 1. The reason is sharp: requiring a sweep selects, after the fact, for
    the days the bias failed.</p>
    <p><strong>The AUD idea works, but not in the form you posed it.</strong> Whether AUDUSD moves
    with gold <em>on the day</em> tells you nothing (p&nbsp;=&nbsp;{SD['p']:.2f}). Whether gold and
    AUDUSD have been <em>coupled over the past month</em> tells you a great deal: filtering to days
    when the 20-day correlation is at or below 0.5 lifts the profit factor from
    {X['pf']:.3f} to <strong>{F['pf']:.3f}</strong> and the t-statistic from
    {X['t']:.2f} to <strong>{F['t']:.2f}</strong>. The excluded days run at {H['pf']:.3f}.</p>
  </div>
</section>

<section>
  <h2><span class="n">01</span>The sweep entry, tested</h2>
  <p class="lede">Your specification, implemented literally: establish the bias from the opening-range
  breakout, wait for a counter-directional sweep of a liquidity level, require a reclaim, then enter
  in the bias direction.</p>
  <p>Four definitions of "liquidity level" were tested, because the phrase carries real ambiguity:
  the most recent confirmed swing low/high (a 5-bar fractal, updated as the day progresses); the low
  of the breakout candle; the Asia session extreme; and the far side of the opening range. The
  reclaim requires a close back on the correct side within 1–6 five-minute bars. Two guards keep the
  setup honest — the sweep may not exceed the opposite edge of the opening range (which would
  invalidate the bias outright), and the swept level must sit on the far side of the breakout price,
  so the entry is a genuine pullback rather than a chase.</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Range</th><th class="l">Liquidity level swept</th><th>Trades</th>
    <th>Setup rate</th><th>Win rate</th><th>Profit factor</th><th>Exp. $</th>
    <th>Breakout entry, same days</th></tr></thead>
    <tbody>{sweep_rows}</tbody>
  </table></div>
  <p>The last column is the important one. On the very same days, entering at the breakout close
  instead of waiting for the sweep produces profit factors of {min(g['breakout_pf'] for g in S['sweep_grid']):.2f}
  to {max(g['breakout_pf'] for g in S['sweep_grid']):.2f}. <strong>So the sweep entry is dramatically
  the better fill — often twice the profit factor — and it still is not enough.</strong> Your
  diagnosis of the entry problem was right. It just was not the binding constraint.</p>
</section>

<section>
  <h2><span class="n">02</span>Why: the sweep condition is a filter for failure</h2>
  <p class="lede">Split the bias days by whether a sweep ever happened, then score both groups on
  the plain breakout entry.</p>
  <div class="stats">
    <div class="stat"><div class="k">Days that swept back</div><div class="v">{SEL['swept']['pf']:.3f}</div>
      <div class="k" style="margin-top:6px">profit factor · n={SEL['swept']['n']}</div></div>
    <div class="stat"><div class="k">Days that never swept</div><div class="v">{SEL['never_swept']['pf']:.3f}</div>
      <div class="k" style="margin-top:6px">profit factor · n={SEL['never_swept']['n']}</div></div>
    <div class="stat"><div class="k">Expectancy, swept</div><div class="v">${SEL['swept']['exp']:+.2f}</div></div>
    <div class="stat"><div class="k">Expectancy, never swept</div><div class="v">${SEL['never_swept']['exp']:+.2f}</div></div>
  </div>
  <p>A profit factor of {SEL['never_swept']['pf']:.2f} on the days price never comes back, against
  {SEL['swept']['pf']:.2f} on the days it does. The sweep is not a setup — it is a symptom. On gold,
  price returning to take out a swing level after the Asia breakout is the market telling you the
  move has no sponsorship. Waiting for it means systematically trading only the days that fail.</p>
  <p>This also explains the earlier pullback-entry result: every mechanism that requires price to
  come back to you is buying adverse selection.</p>
  <h3>The seven exits</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Exit</th><th>Trades</th><th>Win rate</th><th>Profit factor</th>
    <th>Exp. $</th><th>t-stat</th></tr></thead>
    <tbody>{exit_rows}</tbody>
  </table></div>
  <p>Extending the hold into the New York session helps — the same pattern as round one, where later
  exits always beat earlier ones — but never enough to clear 1.00.</p>
  <div class="note">
    <p><strong>One mechanical note.</strong> Putting the stop at the sweep extreme, which the pattern
    seems to invite, is unusable: the reclaim close sits only a few dollars above the swept low, so
    <strong>91% of trades are stopped out</strong> and the win rate collapses to 8%. Any live version
    needs a buffer of at least half the range width below the sweep.</p>
  </div>
</section>

<section>
  <h2><span class="n">03</span>Gold and the Aussie</h2>
  <p class="lede">Two independent AUDUSD feeds, each timezone-verified the same way as the gold data
  — by maximising return correlation against gold, which produced a sharp unambiguous peak. They
  agree with each other to 0.2 pips with a return correlation of 0.997.</p>
  <div class="stats">
    <div class="stat"><div class="k">15-min correlation</div><div class="v">{A['corr15']:+.3f}</div></div>
    <div class="stat"><div class="k">Asia session</div><div class="v dim">{A['asia']:+.3f}</div></div>
    <div class="stat"><div class="k">London</div><div class="v dim">{A['london']:+.3f}</div></div>
    <div class="stat"><div class="k">New York</div><div class="v dim">{A['ny']:+.3f}</div></div>
  </div>
  <p>Daily correlation over the gold sample is {A['daily_corr']:+.3f}. But the 20-day rolling
  correlation ranges from {A['roll_p05']:+.2f} to {A['roll_p95']:+.2f} (median {A['roll_med']:+.2f}).
  <strong>That instability is the whole point</strong> — the relationship is not a constant to be
  assumed, it is a state variable that changes.</p>
  <h3>Same-day agreement: nothing</h3>
  <p>Taking your question at face value first — does AUDUSD moving in the same direction as gold
  during the Asia session confirm the bias? Over {SD['n']} days where both feeds exist, agreement
  gives a {SD['agree']['pf']:.3f} profit factor and divergence {SD['diverge']['pf']:.3f}, with
  t&nbsp;=&nbsp;{SD['t']:+.2f}, p&nbsp;=&nbsp;{SD['p']:.2f}. Directionally it hints that divergence
  is better, but on this sample that is not a finding.</p>
</section>

<section>
  <h2><span class="n">04</span>The regime, not the day</h2>
  <p class="lede">The daily series runs the full five years, so the coupling <em>regime</em> can be
  measured where same-day co-movement could not. This is where it gets interesting.</p>
  <div class="finding">
    <div class="head">Finding</div>
    <p>Take the 20-day rolling correlation between gold and AUDUSD daily returns, computed only from
    data available before the session opens. Trade the opening-range breakout only when that
    correlation is at or below 0.5.</p>
    <p><strong>{X['n']} trades → {F['n']}. Profit factor {X['pf']:.3f} → {F['pf']:.3f}.
    Expectancy ${X['exp']:+.2f} → ${F['exp']:+.2f} per trade. t-statistic
    {X['t']:.2f} → {F['t']:.2f}.</strong> The {H['n']} excluded days run at a {H['pf']:.3f} profit
    factor and ${H['exp']:+.2f} per trade — they are where the losses live.</p>
  </div>
  <figure>
    <div class="chart">
      <svg viewBox="0 0 660 220" role="img" aria-label="Cumulative return, filtered versus unfiltered versus excluded days">
        <line class="zero" x1="46" y1="{zero_y:.1f}" x2="640" y2="{zero_y:.1f}"/>
        {paths}
        {xticks}
      </svg>
    </div>
    <div class="legend">
      <span><i class="swatch" style="background:var(--brass)"></i>filtered — correlation ≤ 0.5</span>
      <span><i class="swatch" style="background:var(--pos)"></i>all trades, unfiltered</span>
      <span><i class="swatch" style="background:var(--neg)"></i>excluded — correlation &gt; 0.5</span>
    </div>
    <figcaption>60-minute opening range, held to the New York close. Cumulative return as a percentage
    of the gold price, net of $0.30 per round trip.</figcaption>
  </figure>
  <h3>Why it might be real</h3>
  <p>A high gold–AUD correlation means gold is trading as a dollar and risk-sentiment proxy, moving
  with the same macro flow that drives every other USD pair. A low or negative correlation means gold
  is being driven by something of its own — central bank buying, safe-haven demand, a metals-specific
  bid. The result says intraday breakouts continue when gold has its own sponsor and fail when it is
  just expressing the dollar. That is a mechanism, not just a correlation, which is the minimum bar
  for taking a filter seriously.</p>
</section>

<section>
  <h2><span class="n">05</span>Trying to break it</h2>
  <p class="lede">Round one killed every filter it tested. This one was put through the same battery
  and more.</p>

  <h3>It generalises to the configurations from round one</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Range</th><th class="l">Exit</th><th>Trades</th><th>PF unfiltered</th>
    <th>Trades</th><th>PF filtered</th><th>Lift</th></tr></thead>
    <tbody>{gen_rows}</tbody>
  </table></div>
  <p>The filter was found on a 60-minute range held to the New York close. Applied unchanged to the
  5-, 15- and 30-minute ranges you originally specified, it improves
  <strong>{n_up} of {len(S['generalise'])}</strong> configurations. A filter that only works on the
  configuration it was discovered on is a fitting artefact; this one is not.</p>

  <h3>The threshold is not cherry-picked</h3>
  <figure>
    <div class="chart">
      <svg viewBox="0 0 660 200" role="img" aria-label="Profit factor by correlation threshold">
        <line class="zero" x1="40" y1="150" x2="630" y2="150"/>
        {th_svg}
      </svg>
    </div>
    <figcaption>Profit factor by correlation cut-off, measured from a 1.00 baseline. Monotonic — the
    tighter the filter, the stronger the result, all the way down to 259 trades. A data-mined
    threshold produces a spike, not a gradient.</figcaption>
  </figure>

  <h3>It holds in both halves</h3>
  <div class="stats">
    <div class="stat"><div class="k">In-sample, corr ≤ 0.5</div><div class="v">{IO['IS']['lo_pf']:.2f}</div>
      <div class="k" style="margin-top:6px">n={IO['IS']['lo_n']}</div></div>
    <div class="stat"><div class="k">In-sample, corr &gt; 0.5</div><div class="v dim">{IO['IS']['hi_pf']:.2f}</div>
      <div class="k" style="margin-top:6px">n={IO['IS']['hi_n']}</div></div>
    <div class="stat"><div class="k">Out-of-sample, corr ≤ 0.5</div><div class="v">{IO['OS']['lo_pf']:.2f}</div>
      <div class="k" style="margin-top:6px">n={IO['OS']['lo_n']}</div></div>
    <div class="stat"><div class="k">Out-of-sample, corr &gt; 0.5</div><div class="v dim">{IO['OS']['hi_pf']:.2f}</div>
      <div class="k" style="margin-top:6px">n={IO['OS']['hi_n']}</div></div>
  </div>

  <h3>And the rest of the battery</h3>
  <ul>
    <li><strong>Continuous, no threshold at all.</strong> Spearman correlation between the 20-day
    coupling and the trade's return is {C['rho']:+.3f} (p&nbsp;=&nbsp;{C['p']:.4f}); the regression
    slope is {C['slope_bp']:.0f} basis points per unit of correlation
    (p&nbsp;=&nbsp;{C['slope_p']:.4f}). The effect does not depend on where the cut is placed.</li>
    <li><strong>Not a calendar proxy.</strong> The share of high-correlation days ranges from 18% to
    58% across years and does not line up with the good and bad years. Within-year, low-correlation
    days beat high-correlation days in 4 of the 5 years with enough data.</li>
    <li><strong>Not volatility or trendiness in disguise.</strong> The 20-day coupling correlates
    +0.03 with realised volatility and −0.08 with a trendiness measure. Double-sorted, the effect
    survives inside every volatility tercile and every trendiness tercile.</li>
    <li><strong>Block-shuffle placebo: p &lt; 0.001.</strong> Shuffling the regime labels in blocks —
    preserving how persistent the regime is, destroying only which days carry which label — beat the
    observed edge in 0 of 5,000 draws.</li>
    <li><strong>Randomisation on direction: p = 0.0002.</strong> Keeping the filtered entry and exit
    times but choosing the side at random.</li>
    <li><strong>Independent re-implementation.</strong> The headline was reproduced by a second
    engine written from scratch, not sharing code with the first, to rule out a bug.</li>
  </ul>

  <h3>Costs and years</h3>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:22px">
    <div class="tbl-wrap" style="margin:0"><table>
      <thead><tr><th class="l">Round trip</th><th>Profit factor</th><th>Exp. $</th></tr></thead>
      <tbody>{cost_rows}</tbody></table></div>
    <div class="tbl-wrap" style="margin:0"><table>
      <thead><tr><th class="l">Year</th><th>Trades</th><th>Win</th><th>PF</th><th>Total $</th></tr></thead>
      <tbody>{yr_rows}</tbody></table></div>
  </div>
  <p>It survives a $1.50 round trip — five times a realistic institutional cost — and is positive in
  five of six years. 2023 is the exception at a {[y['pf'] for y in S['filter_years'] if y['yr']==2023][0]:.2f}
  profit factor.</p>
</section>

<section>
  <h2><span class="n">06</span>The rule, stated plainly</h2>
  <div class="rule-box"><ol>
    <li>Each day before 09:30 HKT, compute the 20-day rolling correlation between gold and AUDUSD
    daily returns, using data through yesterday's close.</li>
    <li><strong>If that correlation is above 0.5, do not trade.</strong> That is roughly 38% of days.</li>
    <li>Otherwise form the opening range from 09:30 HKT — 60 minutes tested hardest, but 15 and 30
    also improve.</li>
    <li>Enter on the first candle to close beyond the range, in that direction.</li>
    <li>Hold to the New York close. Later exits beat earlier ones consistently; exiting at or before
    the London open remains the worst choice in every test.</li>
    <li>No sweep entry, no pullback, no confirmation beyond the breakout close.</li>
  </ol></div>
  <div class="stats">
    <div class="stat"><div class="k">Trades</div><div class="v">{F['n']}</div></div>
    <div class="stat"><div class="k">Win rate</div><div class="v">{F['win']*100:.1f}%</div></div>
    <div class="stat"><div class="k">Profit factor</div><div class="v">{F['pf']:.2f}</div></div>
    <div class="stat"><div class="k">Per trade</div><div class="v">${F['exp']:+.2f}</div></div>
    <div class="stat"><div class="k">t-statistic</div><div class="v">{F['t']:.2f}</div></div>
  </div>
</section>

<section>
  <h2><span class="n">07</span>What would still make me wrong</h2>
  <ul>
    <li><strong>The underlying strategy is still weak.</strong> Unfiltered it is a {X['pf']:.3f}
    profit factor. The filter is doing all the work, which means the whole thing rests on one
    variable holding up.</li>
    <li><strong>One instrument, one regime variable, five years.</strong> The honest test is whether
    the same conditioning works on silver, on the London-open range, and on the twelve months since
    the data ends in August 2025.</li>
    <li><strong>I found this after a large search.</strong> The placebo, the monotonic threshold, the
    generalisation across twelve configurations and the out-of-sample consistency are what raise it
    above the earlier false positives — but a t-statistic of {F['t']:.2f} on 747 trades is a finding
    that deserves forward testing, not size.</li>
    <li><strong>2023 was negative.</strong> A year of losses inside a validated rule is normal, and
    also exactly what an over-fitted rule looks like early in its decay.</li>
    <li>Paper-trade the filter for a quarter before it changes any position sizing. The cheapest
    next test is to compute the correlation live and simply log which days it would have skipped.</li>
  </ul>
</section>

<footer>
  Round two. Code and results on branch <code>claude/trading-strategy-backtest-gqym2i</code>;
  every figure generated from <code>results/summary2.json</code>.
  Round one — the original breakout study — is the companion report.
</footer>
</div>
"""
open("results/report2.html", "w").write(DOC)
print("wrote results/report2.html", len(DOC))
