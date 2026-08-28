"""Regenerate results/pine_copy.html - the mobile paste-board for the
TradingView scripts - from the sources in tradingview/. Republish the artifact
after every change to the Pine files."""
import html

CSS = open("report_style.css").read()
assert "{{" not in CSS
ind = open("tradingview/AsiaOpenGold_indicator.pine").read()
strat = open("tradingview/AsiaOpenGold_strategy.pine").read()
hsi = open("tradingview/HSIPreOpenFade_indicator.pine").read()
d7 = open("tradingview/DoubleSeven_indicator.pine").read()
fp = {n: open(f"tradingview/footprint/FP{n}_{name}.pine").read()
      for n, name in ((0, "FootprintConsole"), (1, "SessionMap"), (2, "RVOL"), (3, "HTFBias"),
                      (4, "Absorption"), (5, "Displacement"), (6, "LiquiditySweeps"), (7, "SMCVisuals"))}


def card(cid, name, blurb, code):
    return f"""
<section class="script">
  <div class="script-head">
    <div>
      <h2>{name}</h2>
      <p class="blurb">{blurb}</p>
    </div>
    <button class="copy" data-target="{cid}">Copy code</button>
  </div>
  <div class="codewrap"><pre id="{cid}"><code>{html.escape(code)}</code></pre></div>
</section>"""


HTML_DOC = f"""<title>Pine Paste Board</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
{CSS}
<style>
.script {{ margin-top: 40px; }}
.script-head {{ display:flex; align-items:flex-start; justify-content:space-between; gap:16px; flex-wrap:wrap; }}
.script-head h2 {{ margin:0; }}
.blurb {{ margin:6px 0 0; color:var(--ink-2); max-width:52ch; }}
.copy {{ font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:15px; font-weight:600;
  color:#fff; background:var(--brass); border:none; border-radius:6px;
  padding:14px 22px; min-height:48px; cursor:pointer; flex-shrink:0; }}
.copy:active {{ opacity:.85; }}
.copy.done {{ background:var(--pos); }}
.codewrap {{ margin-top:16px; border:1px solid var(--rule); border-radius:4px;
  background:var(--sunk); max-height:420px; overflow:auto; -webkit-overflow-scrolling:touch; }}
.codewrap pre {{ margin:0; padding:16px 18px; font-family:"IBM Plex Mono",monospace;
  font-size:12.5px; line-height:1.5; color:var(--ink); white-space:pre; }}
.steps {{ counter-reset:s; display:grid; gap:14px; margin:26px 0 0; padding:0; list-style:none; max-width:66ch; }}
.steps li {{ counter-increment:s; display:flex; gap:14px; align-items:baseline; }}
.steps li::before {{ content:counter(s); font-family:"IBM Plex Mono",monospace; font-size:12px;
  color:var(--brass); border:1px solid var(--brass); border-radius:50%;
  width:22px; height:22px; display:inline-flex; align-items:center; justify-content:center; flex-shrink:0; }}
</style>
<div class="wrap">
<header>
<p class="eyebrow">TradingView scripts &middot; gold, HSI fade, Double Seven &middot; Project Footprint suite (FP1&ndash;FP7)</p>
<h1>Pine Paste Board</h1>
<p class="standfirst">Both scripts, ready to copy on any device. Tap Copy, then paste
into TradingView&rsquo;s Pine Editor over the existing script and Save. On an iPad use
Safari at tradingview.com (Request Desktop Website if the editor is missing) &mdash;
the native app has no Pine Editor.</p>
</header>

<section>
<h2>Updating a script you already added</h2>
<ol class="steps">
<li>Open the <strong>Pine Editor</strong> and load your saved copy (editor menu &rarr; Open).</li>
<li>Select all the old code, paste the new version over it, <strong>Save</strong> &mdash;
the chart updates in place; no need to remove and re-add.</li>
<li>The v1.1 indicator adds a bigger status card (position and text size are now in
Settings) and two new card rows: <strong>signals on chart</strong> and
<strong>last signal</strong>, so you can tell &ldquo;no signals loaded&rdquo; apart from
&ldquo;not spotting them&rdquo;.</li>
</ol>
</section>

{card("ind", "Signal indicator (v1.2)", "Now with three regime alerts (REGIME ON / OFF / APPROACHING) so the end of a drought reaches your phone, plus a corr-trend row on the card. Re-paste over v1.1 and re-create alerts to add the new ones.", ind)}
{card("strat", "Backtest strategy", "The full rule for the Strategy Tester, with webhook-ready order alerts for a bridge later.", strat)}
{card("hsi", "HSI pre-open fade (paper only)", "Watch-list item: fades a >=0.3-ATR push in the 09:15-09:30 HKT futures-only window. Load on an OANDA HK33HKD 15-minute chart; alerts FADE LONG / FADE SHORT / EXIT. Parameters frozen until 80 trades.", hsi)}
{card("d7", "Double Seven (paper only)", "Watch-list item 4 (round 28): buy a 7-day closing low above the 200-day SMA on the S&P, exit at a 7-day closing high, long only, no stop. Load on a DAILY S&P chart (SP:SPX or OANDA:SPX500USD); alerts D7 BUY / D7 EXIT fire at the close. Parameters frozen at the published 7/200.", d7)}

<section>
<h2>Project Footprint suite (round 33)</h2>
<p class="standfirst">Seven modular indicators for reading auction behaviour on
ES1!/NQ1!/RTY1!/GC1! &mdash; use real CME symbols, never CFDs (synthetic volume).
These are measurement instruments for discretionary context, not signals: the
evidence grades live in <code>reference/footprints.md</code>, and round 33
validation demoted sweep entries (FP6) to context-only. FP7 is visualization
only by design. <strong>Slot-limited? Load FP0 + FP2 only</strong> &mdash; the
console merges the whole validated overlay core into one indicator slot.</p>
</section>
{card("fp0", "FP0 Footprint Console (recommended)", "The one-slot merge of FP1 + FP3 + FP6: session shading and key minutes, session VWAP-sigma value proxy, the round-30 bias card, and liquidity levels with the sweep scoreboard - each layer toggleable in Settings. Pair with FP2 in its own pane and the whole validated suite costs two of your five slots.", fp[0])}
{card("fp1", "FP1 Session Map", "The chassis: RTH/Globex shading, key-minute markers (cash open, 10:00 data, MOC window; London fixes / COMEX settle / SGE on the Gold preset), session VWAP with sigma bands as a value-area proxy, prior RTH close.", fp[1])}
{card("fp2", "FP2 RVOL Engine", "Participation anomalies: volume vs its own time-of-day baseline (EMA per minute bucket) plus session-cumulative RVOL. The one place execution algos betray themselves. Real CME volume required. VALIDATED r33b: extreme RVOL predicts ~2x forward range (t &gt; +48, all instruments) - a volatility/regime tool; it carries NO directional information.", fp[2])}
{card("fp3", "FP3 HTF Bias", "The honest institutional-flow read (round 30): cumulative overnight vs intraday return tracks, rolling overnight drift, 200-day trend state, and a LONG/SHORT/NEUTRAL bias card. A filter, never a standalone trade.", fp[3])}
{card("fp4", "FP4 Absorption Proxy", "Effort-vs-result: high volume percentile + low range percentile at an N-bar extreme, with close-location direction. Includes a lower-timeframe CVD PROXY, labeled as such - Pine has no true aggressor delta. r33b: too rare to power a test (~2-8 events/yr) - context only.", fp[4])}
{card("fp5", "FP5 Displacement Meter", "Initiative vs rotational regime from TR/ATR with body dominance, plus an on-chart follow-through scoreboard that prints this symbol's actual next-bar base rate (usually a coin flip - that is the lesson). VALIDATED r33b: continuation is real gross on NDX (+2.4 bps/h, t +4.3) and SMALLER THAN ONE ROUND TRIP - net negative; regime context only.", fp[5])}
{card("fp6", "FP6 Liquidity Sweeps (context only)", "PDH/PDL, overnight extremes, opening range, with failed-break detection and a running scoreboard. Round 33: breaches close back inside 54-80% of the time but the reversal is worth <2bps and every tradeable cell loses - levels are context, sweep entries are not signals.", fp[6])}
{card("fp7", "FP7 SMC Visuals (viz only)", "Order blocks and FVGs, drawn with an honesty table: fill % is a base rate, not an edge (round 27: 0/12 cells). Zero strategy weight unless they ever pass validation.", fp[7])}

<footer><p>Generated from <code>backtest/tradingview/</code> by
<code>build_pine_copy.py</code> &mdash; the repository copy is the source of truth.</p></footer>
</div>
<script>
document.querySelectorAll('.copy').forEach(function (b) {{
  b.addEventListener('click', function () {{
    var text = document.getElementById(b.dataset.target).innerText;
    function done() {{
      b.classList.add('done'); b.textContent = 'Copied';
      setTimeout(function () {{ b.classList.remove('done'); b.textContent = 'Copy code'; }}, 2500);
    }}
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(text).then(done, fallback);
    }} else {{ fallback(); }}
    function fallback() {{
      var ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.focus(); ta.select();
      try {{ document.execCommand('copy'); done(); }} catch (e) {{
        b.textContent = 'Select the code and copy manually';
      }}
      document.body.removeChild(ta);
    }}
  }});
}});
</script>"""
open("results/pine_copy.html", "w").write(HTML_DOC)
print(f"written results/pine_copy.html ({len(HTML_DOC):,} bytes)")
