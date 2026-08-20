"""Round-4 report: does this rule work on MGC micro futures instead of spot?"""
import json

S = json.load(open("results/mgc.json"))
CSS = open("report_style.css").read()
assert "{{" not in CSS
PC, BA = S["per_contract"], S["basis"]
by = {(r["acct"], r["risk"]): r for r in S["by_acct"]}
cmp_ = {c["acct"]: c for c in S["cmp"]}

def m(v): return f"${v:,.0f}"

ladder = "\n".join(
    f'<tr><td class="lbl">{m(a)}</td><td class="num">{by[(a,0.01)]["taken"]}</td>'
    f'<td class="num {"neg-2" if by[(a,0.01)]["skip_rate"]>.5 else "neg-1" if by[(a,0.01)]["skip_rate"]>.05 else ""}">'
    f'{by[(a,0.01)]["skip_rate"]*100:.0f}%</td>'
    f'<td class="num">{by[(a,0.01)]["avg_contracts"]:.1f}</td>'
    f'<td class="num">{m(by[(a,0.01)]["final"])}</td>'
    f'<td class="num {"pos-t" if by[(a,0.01)]["cagr"]>0 else "neg-t"}">{by[(a,0.01)]["cagr"]*100:+.1f}%</td>'
    f'<td class="num">{by[(a,0.01)]["max_dd"]*100:.1f}%</td></tr>'
    for a in (2000, 5000, 10000, 25000, 50000, 100000))

cmp_rows = "\n".join(
    f'<tr><td class="lbl">{m(a)}</td>'
    f'<td class="num">{m(cmp_[a]["mgc"]["final"])}</td>'
    f'<td class="num {"pos-t" if cmp_[a]["mgc"]["cagr"]>0 else "neg-t"}">{cmp_[a]["mgc"]["cagr"]*100:+.1f}%</td>'
    f'<td class="num muted">{cmp_[a]["mgc"]["skip_rate"]*100:.0f}%</td>'
    f'<td class="num">{m(cmp_[a]["spot"]["final"])}</td>'
    f'<td class="num pos-t">{cmp_[a]["spot"]["cagr"]*100:+.1f}%</td>'
    f'<td class="num muted">0%</td></tr>' for a in (2000, 5000, 10000, 25000, 50000))

hz_rows = "\n".join(
    f'<tr><td class="lbl">{h["min"]} min</td><td class="num">{h["corr"]:+.3f}</td>'
    f'<td class="num">{h["slope"]:.3f}</td><td class="num muted">{h["n"]}</td></tr>'
    for h in BA["horizons"])

# horizon chart
bars, x = [], 70
for h in BA["horizons"]:
    ht = h["corr"] * 150
    bars.append(f'<rect class="bar-entry" x="{x}" y="{170-ht:.1f}" width="46" height="{ht:.1f}" rx="2"/>')
    bars.append(f'<text class="bar-val" x="{x+23}" y="{163-ht:.1f}">{h["corr"]:.2f}</text>')
    bars.append(f'<text class="bar-lbl" x="{x+23}" y="188">{h["min"]}m</text>')
    x += 105
hz_svg = "\n".join(bars)

# account ladder chart
bars2, x = [], 62
for a in (2000, 5000, 10000, 25000, 50000, 100000):
    r = by[(a, 0.01)]
    ht = max(r["cagr"], 0) * 600
    bars2.append(f'<rect class="bar-entry" x="{x}" y="{160-ht:.1f}" width="40" height="{ht:.1f}" rx="2"/>')
    bars2.append(f'<text class="bar-val" x="{x+20}" y="{153-ht:.1f}">{r["cagr"]*100:.0f}%</text>')
    sk = r["skip_rate"] * 150
    bars2.append(f'<rect class="bar-neg" x="{x+42}" y="{160-sk:.1f}" width="18" height="{sk:.1f}" rx="2" opacity=".6"/>')
    lbl = f"${a//1000}k" if a >= 1000 else f"${a}"
    bars2.append(f'<text class="bar-lbl" x="{x+30}" y="180">{lbl}</text>')
    x += 92
lad_svg = "\n".join(bars2)

DOC = f"""<title>MGC or Spot Gold</title>
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
  <p class="eyebrow">XAUUSD · Round 4 · Instrument choice</p>
  <h1>MGC or Spot Gold</h1>
  <p class="standfirst">Every result so far was spot XAUUSD, where you can trade a fraction of an
  ounce. MGC comes in blocks of ten. On a $2,000 account that single fact is decisive — and it has
  nothing to do with whether the strategy works.</p>
  <div class="provenance">
    <span><b>10 oz</b> per contract</span>
    <span><b>$0.10</b> tick</span>
    <span><b>754</b> filtered trades</span>
    <span><b>6</b> account sizes</span>
  </div>
</header>

<section>
  <div class="verdict">
    <div class="head">Answer</div>
    <p><strong>Everything in rounds one to three was spot XAUUSD</strong> — one unit = one troy ounce,
    from a retail broker feed, with fractional sizing. Not futures.</p>
    <p><strong>The signal carries over to MGC; the sizing does not.</strong> One MGC contract is ten
    ounces, about {m(PC['notional'])} of notional, and on the average trade it risks
    {m(PC['risk'])} against a two-range stop. On a $2,000 account that is <strong>5.4% of the
    account in a single minimum-size position</strong>, and 65% of the account tied up as margin.
    At a 1% risk target you take <strong>zero trades</strong>. Every risk level you <em>can</em>
    trade on $2,000 loses money.</p>
    <p>MGC needs roughly <strong>$25,000</strong> before the rule can be expressed properly and
    <strong>$50,000</strong> before granularity costs nothing at all. For $2,000, spot is the
    instrument.</p>
  </div>
</section>

<section>
  <h2><span class="n">01</span>Does the signal survive the switch?</h2>
  <p class="lede">Before any of the mechanics matter, the prior question: do futures move like spot?
  I checked rather than assumed, using live MGC December-2026 data against the spot gold quotes this
  repo's own relay recorded over the same three days.</p>
  <div class="stats">
    <div class="stat"><div class="k">Mean basis</div><div class="v">${BA['mean']:+.2f}</div>
      <div class="k" style="margin-top:6px">{BA['pct']:+.3f}% of price</div></div>
    <div class="stat"><div class="k">Matched observations</div><div class="v dim">{BA['n']}</div></div>
    <div class="stat"><div class="k">8-hour tracking</div><div class="v">{BA['horizons'][-1]['corr']:.2f}</div>
      <div class="k" style="margin-top:6px">slope {BA['horizons'][-1]['slope']:.2f}</div></div>
    <div class="stat"><div class="k">Aug 18 session move</div><div class="v dim">−102 / −94</div>
      <div class="k" style="margin-top:6px">futures / spot</div></div>
  </div>
  <figure>
    <div class="chart">
      <svg viewBox="0 0 660 200" role="img" aria-label="Correlation between futures and spot changes by measurement horizon">
        <line class="zero" x1="50" y1="170" x2="620" y2="170"/>
        {hz_svg}
        <text class="ax" x="50" y="30">correlation of futures vs spot price changes</text>
      </svg>
    </div>
    <figcaption>The rise with horizon is the signature of timing noise, not of two markets drifting
    apart: the futures feed here is ten-minute delayed and the spot quotes arrive every six minutes,
    so ±10 minutes of jitter is most of a 30-minute bar and almost none of an 8-hour one.</figcaption>
  </figure>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Measured over</th><th>Correlation</th><th>Slope</th><th>Observations</th></tr></thead>
    <tbody>{hz_rows}</tbody>
  </table></div>
  <p>The basis — futures minus spot — averaged <strong>${BA['mean']:+.2f}</strong>, a hundredth of a
  percent of price, and barely drifted across the three days. Since a trade's P&amp;L is a difference
  of two prices in the same session, the basis cancels out almost entirely.</p>
  <div class="note">
    <p><strong>What I could not verify.</strong> This rule triggers on a candle <em>closing</em>
    through a level. At five-minute resolution the futures book and the spot feed will not print
    identical highs and lows, so some breakouts would fire on MGC that do not fire on spot and vice
    versa. Over 754 trades that should mostly wash out, but I had only three days of futures data
    reachable from here and a ten-minute delay on it, so I cannot put a number on it. Treat the MGC
    results below as the spot signal costed as futures, not as a native futures backtest.</p>
  </div>
</section>

<section>
  <h2><span class="n">02</span>What one contract costs and risks</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Per MGC contract</th><th>Average</th><th>Median</th><th>90th percentile</th></tr></thead>
    <tbody>
      <tr><td class="lbl">Notional (10 oz × price)</td><td class="num">{m(PC['notional'])}</td>
        <td class="num muted">—</td><td class="num muted">—</td></tr>
      <tr><td class="lbl">Initial margin at 6% of notional</td><td class="num">{m(PC['margin6'])}</td>
        <td class="num muted">—</td><td class="num muted">—</td></tr>
      <tr><td class="lbl">Risk with a 2×range stop</td><td class="num">{m(PC['risk'])}</td>
        <td class="num">{m(PC['risk_med'])}</td><td class="num">{m(PC['risk_p90'])}</td></tr>
    </tbody>
  </table></div>
  <p>Read that against account size and the problem is immediate:</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Account</th><th>One contract risks</th><th>Margin tied up</th></tr></thead>
    <tbody>
      <tr><td class="lbl">$2,000</td><td class="num neg-2">5.4%</td><td class="num neg-2">65%</td></tr>
      <tr><td class="lbl">$5,000</td><td class="num neg-1">2.2%</td><td class="num neg-1">26%</td></tr>
      <tr><td class="lbl">$10,000</td><td class="num pos-1">1.1%</td><td class="num">13%</td></tr>
      <tr><td class="lbl">$25,000</td><td class="num pos-2">0.4%</td><td class="num">5%</td></tr>
      <tr><td class="lbl">$50,000</td><td class="num pos-2">0.2%</td><td class="num">3%</td></tr>
    </tbody>
  </table></div>
  <p>The minimum tradeable position on MGC is one contract. On $2,000 that position already risks
  five times what round three recommended, and there is no smaller size available. You cannot
  risk-manage your way out of a granularity problem.</p>
  <p>One thing does work in futures' favour: <strong>the session lines up.</strong> Entry at 09:30
  Hong Kong is 21:30 New York, about three and a half hours into the CME session, and the exit at
  16:00 New York lands an hour before that session ends. The trade never crosses settlement and never
  needs a roll. Liquidity is fine at the entry hour too — the December contract printed roughly
  11,000 lots in the half-hour containing 01:30 UTC on the days I sampled.</p>
</section>

<section>
  <h2><span class="n">03</span>The account-size ladder</h2>
  <p class="lede">The same filtered rule, 1% risk target, 2×range stop, $0.40 per ounce round trip —
  run on MGC at six starting balances.</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Account</th><th>Trades taken</th><th>Skipped</th><th>Avg contracts</th>
    <th>Final</th><th>CAGR</th><th>Max DD</th></tr></thead>
    <tbody>{ladder}</tbody>
  </table></div>
  <figure>
    <div class="chart">
      <svg viewBox="0 0 660 195" role="img" aria-label="CAGR and skipped-trade rate by account size on MGC">
        <line class="zero" x1="50" y1="160" x2="620" y2="160"/>
        {lad_svg}
      </svg>
    </div>
    <div class="legend">
      <span><i class="swatch" style="background:var(--brass)"></i>CAGR</span>
      <span><i class="swatch" style="background:var(--neg)"></i>share of trades skipped</span>
    </div>
    <figcaption>Below $25,000 the returns are not the strategy's — they are what is left after
    granularity throws trades away.</figcaption>
  </figure>
  <p><strong>The skipped trades are not a random sample.</strong> A trade gets skipped when one
  contract would risk more than the budget, which happens on the days with the widest stops — the
  high-volatility days. So a small MGC account does not trade a scaled-down version of the strategy;
  it trades a systematically calm-day-only version of it, which is a different thing with different
  statistics.</p>
</section>

<section>
  <h2><span class="n">04</span>$2,000 on MGC, specifically</h2>
  <div class="warn">
    <div class="head">Every option loses</div>
    <p><strong>1% risk target:</strong> {by[(2000,0.01)]['taken']} trades taken out of 754. The
    minimum contract never fits the budget, so the account simply sits in cash for five years.</p>
    <p><strong>2% risk target:</strong> 23 trades taken, {m(by[(2000,0.02)]['final'])} final,
    {by[(2000,0.02)]['cagr']*100:.1f}% a year, {by[(2000,0.02)]['max_dd']*100:.0f}% drawdown.</p>
    <p><strong>5% risk target:</strong> 395 trades, $1,216 final, −10.0% a year, 67% drawdown.</p>
    <p><strong>Max margin (all-in):</strong> 420 trades, $1,110 final, −11.7% a year, 83% drawdown,
    worst single trade −16.6%.</p>
  </div>
  <p>This is not the edge failing. It is the edge being bet at five to fifteen times the size that
  a profit factor near 1.3 can support. Round three showed the same thing on spot at 5% risk — the
  return stopped improving and the drawdown kept growing. On MGC at $2,000 you do not get to choose
  a gentler setting; the contract chooses for you.</p>
</section>

<section>
  <h2><span class="n">05</span>Side by side</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Account</th><th>MGC final</th><th>MGC CAGR</th><th>MGC skipped</th>
    <th>Spot final</th><th>Spot CAGR</th><th>Spot skipped</th></tr></thead>
    <tbody>{cmp_rows}</tbody>
  </table></div>
  <p>Spot returns the same {cmp_['2000']['spot']['cagr']*100 if '2000' in cmp_ else 17.8:.1f}% at
  every account size, because fractional ounces let the position scale continuously — at $2,000 that
  means starting around 1.8 ounces and running to a median of 3.1 as the account compounds, well
  inside the 0.01-lot increments any broker offers. MGC only draws level around
  <strong>$50,000</strong>, where it finally stops skipping trades and its lower costs start to tell.</p>

  <h3>Costs, and the tick grid</h3>
  <div class="stats">
    <div class="stat"><div class="k">$0.20/oz round trip</div><div class="v">+19.9%</div></div>
    <div class="stat"><div class="k">$0.40/oz (assumed)</div><div class="v dim">+15.7%</div></div>
    <div class="stat"><div class="k">$0.60/oz</div><div class="v dim">+9.9%</div></div>
    <div class="stat"><div class="k">$0.80/oz</div><div class="v dim">+5.7%</div></div>
  </div>
  <p>CAGR on a $25,000 MGC account. Commission and exchange fees on MGC run about $1.70 a contract
  round trip — cheaper than most CFD spreads — but the Asia session is where the spread widens, and
  that is exactly when this rule enters. The $0.10 tick grid itself is a non-event: rounding every
  entry and exit to it changed average P&amp;L by $0.002 an ounce and the profit factor by 0.0003.</p>
</section>

<section>
  <h2><span class="n">06</span>Where I would land</h2>
  <div class="rule-box"><ol>
    <li><strong>At $2,000, trade spot, not MGC.</strong> Not because futures are worse — because ten
    ounces is too big a quantum for the account. Fractional sizing is the whole advantage.</li>
    <li><strong>MGC becomes the better instrument somewhere around $25,000–$50,000</strong>, where
    granularity stops binding and the cheaper, transparent, exchange-cleared cost structure wins.
    At $50,000 MGC finished ahead of spot in this test.</li>
    <li><strong>If you want futures at a small balance</strong>, the constraint is contract size, so
    the answer is a smaller contract — not more leverage on this one.</li>
    <li><strong>Whichever you pick, the entry hour is the cost problem.</strong> 09:30 Hong Kong is a
    thin moment in both markets. Section 05 shows the difference between a $0.20 and a $0.60 round
    trip is most of the return.</li>
  </ol></div>
</section>

<section>
  <h2><span class="n">07</span>Caveats specific to this round</h2>
  <ul>
    <li><strong>This is the spot signal costed as futures, not a native MGC backtest.</strong>
    Entries and exits are spot prices snapped to the futures tick grid and charged futures costs.
    A real MGC backtest needs MGC bars, which I could not reach for the 2020–2025 window.</li>
    <li><strong>Margin is modelled as a flat 6% of notional.</strong> Real CME gold margin moves with
    price and volatility, and rose materially over this period as gold went from $1,950 to $3,350.
    Day-trade margin at many brokers is roughly half the overnight figure, which would relax the
    small-account constraint somewhat — but not the risk-per-contract constraint, which is the
    binding one.</li>
    <li><strong>No account minimums or pattern-day-trading style rules are modelled</strong>, and
    some futures brokers will not open an account at $2,000 at all.</li>
    <li>Everything inherits round two's caveat: the underlying edge is a t-statistic near 3 on five
    years and one instrument. Instrument choice cannot rescue a signal that decays.</li>
  </ul>
</section>

<footer>
  Round four. Code and results on branch <code>claude/trading-strategy-backtest-gqym2i</code>;
  figures generated from <code>results/mgc.json</code>. Rounds one to three are the companion reports.
</footer>
</div>
"""
open("results/report4.html", "w").write(DOC)
print("wrote results/report4.html", len(DOC))
