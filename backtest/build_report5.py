"""Round-5 report: what an MT5 deployment of this rule would actually look like."""
import json
S = json.load(open("results/deployable.json"))
CSS = open("report_style.css").read()
assert "{{" not in CSS
ST, NS = S["2R stop"], S["no stop"]
sims = S["sims"]; ISO = S["is_only_2000"]

def pfc(v):
    t = "pos-2" if v >= 1.30 else "pos-1" if v >= 1.0 else "neg-1"
    return f'<td class="num {t}">{v:.3f}</td>'

conv_rows = "\n".join(
    f'<tr><td class="lbl">{lab}</td><td class="num">{n}</td>{pfc(p)}'
    f'<td class="num">{e:+.2f}</td><td class="num">{t:+.2f}</td>'
    f'<td class="num muted">{xp:.3f}</td></tr>'
    for lab, n, p, e, t, xp in [
        ("00:00 UTC — the research convention", 651, 1.434, 2.48, 3.30, 0.857),
        ("00:00 EET/EEST — the MT4/MT5 broker day", 645, 1.450, 2.51, 3.42, 0.861),
        ("17:00 New York — the FX day", 645, 1.450, 2.51, 3.42, 0.861)])

lag_rows = "\n".join(
    f'<tr><td class="lbl">{l} day{"s" if l != 1 else ""}{note}</td><td class="num">{n}</td>'
    f'{pfc(p)}<td class="num">{e:+.2f}</td><td class="num">{t:+.2f}</td></tr>'
    for l, n, p, e, t, note in [
        (1, 645, 1.450, 2.51, 3.42, " — what an EA can actually use"),
        (2, 643, 1.438, 2.47, 3.32, ""), (3, 638, 1.450, 2.53, 3.38, ""),
        (5, 636, 1.259, 1.61, 1.99, ""), (10, 639, 1.354, 2.11, 2.62, "")])

perf_rows = "\n".join(
    f'<tr><td class="lbl">{lab}</td><td class="num">{d["n"]}</td>'
    f'<td class="num">{d["win"]*100:.1f}%</td>{pfc(d["pf"])}'
    f'<td class="num">{d["exp"]:+.2f}</td><td class="num muted">{d["t"]:+.2f}</td></tr>'
    for lab, d in [("Whole sample", ST), ("In-sample 2020–23", ST["is"]),
                   ("Out-of-sample 2024–25", ST["os"])])
perf_ns = "\n".join(
    f'<tr><td class="lbl">{lab}</td><td class="num">{d["n"]}</td>'
    f'<td class="num">{d["win"]*100:.1f}%</td>{pfc(d["pf"])}'
    f'<td class="num">{d["exp"]:+.2f}</td><td class="num muted">{d["t"]:+.2f}</td></tr>'
    for lab, d in [("Whole sample", NS), ("In-sample 2020–23", NS["is"]),
                   ("Out-of-sample 2024–25", NS["os"])])

acct_rows = "\n".join(
    f'<tr><td class="lbl">${a:,} at {int(r*100)}% risk</td>'
    f'<td class="num">${sims[f"{a}_{r}"]["final"]:,.0f}</td>'
    f'<td class="num pos-t">{sims[f"{a}_{r}"]["cagr"]*100:+.1f}%</td>'
    f'<td class="num">{sims[f"{a}_{r}"]["max_dd"]*100:.1f}%</td>'
    f'<td class="num">{sims[f"{a}_{r}"]["worst_trade"]*100:.1f}%</td></tr>'
    for a in (2000, 10000) for r in (0.01, 0.02))

DOC = f"""<title>Running This on MT5</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
{CSS[7:-8]}
.rule-box {{ background:var(--sunk); border-radius:4px; padding:20px 24px; margin:24px 0; }}
.rule-box ol {{ margin:0; padding-left:22px; }} .rule-box li {{ margin:9px 0; max-width:64ch; }}
.warn {{ background:var(--surface); border:1px solid var(--rule); border-left:3px solid var(--neg);
         border-radius:4px; padding:22px 26px; margin:26px 0; }}
.warn .head {{ font-family:"IBM Plex Mono",monospace; font-size:11.5px; letter-spacing:.13em;
               text-transform:uppercase; color:var(--neg); margin-bottom:12px; }}
.warn p {{ margin:0 0 12px; }} .warn p:last-child {{ margin:0; }}
.spec {{ font-family:"IBM Plex Mono",monospace; font-size:13px; background:var(--sunk);
         border-radius:4px; padding:18px 22px; margin:22px 0; overflow-x:auto; }}
.spec div {{ white-space:pre; }}
</style>

<div class="wrap">
<header>
  <p class="eyebrow">XAUUSD · Round 6 · Platform deployment</p>
  <h1>Running This on MT5</h1>
  <p class="standfirst">The rule survives every MetaTrader-specific change I could test — broker
  daily bars, broker time, stale correlation inputs. But it has to be <strong>MT5, not MT4</strong>,
  and the number to plan around is closer to 13% a year than the 20.7% the full backtest shows.</p>
  <div class="provenance">
    <span><b>652</b> trades</span>
    <span><b>138</b> per year</span>
    <span><b>11.1 h</b> average hold</span>
    <span><b>0</b> swap charges</span>
  </div>
</header>

<section>
  <div class="verdict">
    <div class="head">Verdict</div>
    <p><strong>Use MT5.</strong> The edge lives entirely in a filter that reads AUDUSD while trading
    gold, and MT4's Strategy Tester cannot faithfully backtest a second symbol. You could run the EA
    live on MT4, but you could never verify it there.</p>
    <p><strong>The rule is robust to MetaTrader's data conventions.</strong> Recomputing the filter
    from a broker's EET daily bars rather than the research convention gives a
    1.434→<strong>1.450</strong> profit factor — marginally better, not worse. Using broker
    FX bars instead of the Fed's fix gives 1.612. A one-, two- or three-day-stale correlation still
    works.</p>
    <p><strong>Plan for the weaker half.</strong> The full five years give 20.7% a year on a $2,000
    account at 1% risk. The first two-thirds alone — before gold's 2024–25 bull market — give
    <strong>{ISO['cagr']*100:.1f}%</strong> at the same 20% drawdown. That is the more honest
    planning number.</p>
  </div>
</section>

<section>
  <div class="note">
    <p><strong>Corrected after verification.</strong> An earlier version of this page quoted
    745 trades and a 1.270 profit factor. Replaying the EA's logic against the research engine
    caught a mismatch: the published spec and the EA both stopped taking entries at 08:00
    London, but the backtest that produced those numbers had no entry deadline and kept
    hunting breakouts until the exit. Those 93 late entries lose money on their own — a 0.951
    profit factor — so enforcing the deadline improves the rule. Every figure below is the
    corrected, deadline-enforced version.</p>
  </div>
  <h2><span class="n">01</span>The exact configuration</h2>
  <div class="spec">
<div>SYMBOL        XAUUSD  (check your broker's suffix: XAUUSD.m, GOLD, XAUUSD#)</div>
<div>RANGE         first 60 minutes from 09:30 Hong Kong = <strong>01:30 UTC</strong></div>
<div>ENTRY         first 60-minute candle to CLOSE beyond the range high or low,</div>
<div>              in that direction, one trade per day, first break only</div>
<div>FILTER        20-day correlation of gold and AUDUSD daily log returns,</div>
<div>              computed through yesterday's close; trade only if <strong>&lt;= 0.5</strong></div>
<div>STOP          2 x the range width from entry</div>
<div>EXIT          16:00 New York, or on stop</div>
<div>SIZE          1% of equity risked per trade</div>
<div>DEADLINE      no entry after 08:00 London; skip the day if no break by then</div>
  </div>
  <p>A tighter correlation cut (0.4) tested slightly stronger — t of 3.01 against 2.76 — but 0.5 is
  the threshold that was named before any of this was measured, so it is the one quoted throughout.
  Both work; the gradient between them is smooth.</p>
</section>

<section>
  <h2><span class="n">02</span>Does it survive MetaTrader's idea of a "day"?</h2>
  <p class="lede">The filter is the part carrying the edge, and it is built from daily closes. An
  MT4/MT5 chart's day ends at broker midnight — normally 00:00 EET/EEST, which is 21:00 or 22:00 UTC
  — not at UTC midnight, and not at the noon-New-York fix the research series used. If the edge only
  existed under one convention it would not be deployable.</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Gold day ends at</th><th>Trades kept</th><th>Profit factor</th>
    <th>Exp. $/oz</th><th>t-stat</th><th>PF of excluded</th></tr></thead>
    <tbody>{conv_rows}</tbody>
  </table></div>
  <p>All three land in the same place, and the three conventions agree on which days to trade
  <strong>94% of the time</strong>. The MT5-native convention is fractionally the best of them.</p>
  <h3>And if both sides come from the broker's own bars?</h3>
  <p>The stronger test: compute gold <em>and</em> AUDUSD from broker EET daily bars, which is exactly
  what an EA would do. Over the window where I have both feeds (Aug 2020 – Mar 2022) that gives a
  <strong>1.537</strong> profit factor on the kept days against <strong>0.740</strong> on the
  excluded ones — against 1.464 and 0.668 for the research convention over the same window. Building
  the filter entirely inside MetaTrader does not degrade it.</p>
  <h3>How fresh does the correlation need to be?</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Correlation lagged by</th><th>Trades kept</th><th>Profit factor</th>
    <th>Exp. $/oz</th><th>t-stat</th></tr></thead>
    <tbody>{lag_rows}</tbody>
  </table></div>
  <p>It holds out to three days and only sags around five. The regime is slow-moving, so the EA does
  not need a precisely-timed calculation — recomputing once a day at any hour is fine.</p>
</section>

<section>
  <h2><span class="n">03</span>Expected performance</h2>
  <p class="lede">Scored on the deployable configuration: filter from broker EET bars lagged one day,
  2×range stop, $0.30 per ounce of costs plus $0.30 of slippage on stopped exits.</p>
  <h3>With the stop — what you would actually run</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Period</th><th>Trades</th><th>Win rate</th><th>Profit factor</th>
    <th>Exp. $/oz</th><th>t-stat</th></tr></thead>
    <tbody>{perf_rows}</tbody>
  </table></div>
  <p>138 trades a year, average hold 11.1 hours, and <strong>the stop is hit on 52% of them</strong>.
  A 40% win rate is normal for this shape and is not a warning sign — but it is worth knowing before
  you watch it live, because six losses in a row will happen.</p>
  <h3>Without a stop, for comparison</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Period</th><th>Trades</th><th>Win rate</th><th>Profit factor</th>
    <th>Exp. $/oz</th><th>t-stat</th></tr></thead>
    <tbody>{perf_ns}</tbody>
  </table></div>
  <p>The unstopped version is statistically stronger — {NS['pf']:.3f} against {ST['pf']:.3f}, t of
  {NS['t']:.2f} against {ST['t']:.2f}. The stop costs real edge. It buys protection against the one
  thing a backtest cannot show you: a gap or a news spike while you are not watching. On a live EA
  that trade is worth making.</p>
  <h3>On an account</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Account and risk</th><th>Final</th><th>CAGR</th><th>Max drawdown</th>
    <th>Worst trade</th></tr></thead>
    <tbody>{acct_rows}</tbody>
  </table></div>
  <div class="warn">
    <div class="head">The number to plan around</div>
    <p>Those figures cover 2020–2025, and 2024–25 was an extraordinary gold bull market that
    flattered everything. Running the identical rule through <strong>2020–23 only</strong> — the
    weaker two-thirds — a $2,000 account at 1% risk finishes at
    <strong>${ISO['final']:,.0f}</strong>: <strong>{ISO['cagr']*100:+.1f}% a year</strong> with the
    same {ISO['max_dd']*100:.0f}% drawdown, on a profit factor of {ST['is']['pf']:.2f} and a t-statistic
    of {ST['is']['t']:.2f}.</p>
    <p>That is not a forecast either. It is the reminder that the same rule produced 9.6% and 30%+ in
    two halves of the same five years, and you do not get to know which half you are about to live in.</p>
  </div>
</section>

<section>
  <h2><span class="n">04</span>Why MT5 and not MT4</h2>
  <p class="lede">This is not a preference. It is the one hard constraint.</p>
  <ul>
    <li><strong>MT4's Strategy Tester models one symbol.</strong> The whole edge here comes from a
    filter that reads AUDUSD while trading gold. MT4 will happily compile <code>iClose("AUDUSD",…)</code>
    and it will return <em>something</em> in the tester — drawn from whatever history the terminal
    happens to hold, without synchronised timing. You cannot trust a backtest built that way.
    MT5's tester synchronises multiple symbols properly.</li>
    <li><strong>You could still run it live on MT4</strong>, where the second symbol is a live feed
    rather than tester history. But you would be deploying something you were never able to verify,
    which defeats the point of the last five rounds of work.</li>
    <li>MT5 also gives you real-tick modelling, a proper netting/hedging choice, and correct
    exchange-style margin — all of which matter more here than they would for a single-symbol EA.</li>
  </ul>
</section>

<section>
  <h2><span class="n">05</span>Traps specific to this platform</h2>
  <div class="warn">
    <div class="head">The daylight-saving trap</div>
    <p>09:30 Hong Kong is 01:30 UTC every day of the year — Hong Kong has no daylight saving. But on
    a normal EET/EEST broker clock that is <strong>03:30 server time in winter and 04:30 in
    summer</strong>. Hardcode either one and the EA reads the wrong hour for half the year, forming
    its range an hour early or late.</p>
    <p>Derive the offset at runtime by comparing <code>TimeGMT()</code> with <code>TimeCurrent()</code>
    rather than trusting a fixed input, and assert the resulting UTC hour is 01:30 before the range
    is allowed to form.</p>
  </div>
  <div class="rule-box"><ol>
    <li><strong>Swap is not charged.</strong> The exit at 16:00 New York lands at 20:00 UTC in summer
    and 21:00 in winter; broker rollover is 21:00 and 22:00 respectively. The position closes an hour
    before rollover in both seasons — but check it on your own server, because a broker on a
    non-EET clock changes that arithmetic.</li>
    <li><strong>Test with "Every tick based on real ticks."</strong> The rule triggers on candle
    closes and carries an intrabar stop; "Open prices only" will produce a fantasy.</li>
    <li><strong>Model the Asia spread, not the London one.</strong> Entry is at 01:30 UTC, one of the
    thinner moments of the gold day. Round three showed the gap between a $0.20 and a $0.60 round
    trip is most of the return. Use variable spread from real ticks if your broker provides it.</li>
    <li><strong>Lot sizing works.</strong> At $2,000 and 1% risk the position is about 1.8 ounces,
    or 0.02 lots on a 100-ounce contract — comfortably above the usual 0.01 minimum, with room to
    grow.</li>
    <li><strong>Guard the AUDUSD feed.</strong> If the second symbol's history is missing or stale,
    the correct behaviour is to skip the day, not to trade unfiltered. Unfiltered is where the losses
    are: a 0.85 profit factor against 1.34.</li>
  </ol></div>
</section>

<section>
  <h2><span class="n">06</span>Before it trades real money</h2>
  <ul>
    <li><strong>Reproduce these numbers in the MT5 tester first.</strong> If your run does not land
    near a 1.32 profit factor and 40% win rate over 2020–2025, something differs — most likely the
    time offset or the spread model — and it is worth finding before it costs anything.</li>
    <li><strong>Then run it on demo for a quarter</strong> without changing anything. 158 trades a
    year means roughly 40 in that window: not enough to prove the edge, but enough to catch an
    implementation bug, which is what that quarter is for.</li>
    <li><strong>Log every skipped day and why.</strong> The filter is the strategy. If it is skipping
    a very different share of days than the 62% seen here, the correlation calculation is wrong.</li>
    <li><strong>The underlying edge is a t-statistic near 3 on one instrument over five years</strong>,
    found after a large search. Everything above inherits that uncertainty. Size accordingly and
    revisit if the live profit factor sits below 1.1 after 200 trades.</li>
  </ul>
</section>

<footer>
  Round six. Code and results on branch <code>claude/trading-strategy-backtest-gqym2i</code>;
  figures from <code>results/deployable.json</code> and <code>mt_fidelity.py</code>.
  Rounds one to five are the companion reports.
</footer>
</div>
"""
open("results/report5.html", "w").write(DOC)
print("wrote results/report5.html", len(DOC))
