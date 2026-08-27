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
<p class="eyebrow">Asia gold strategy &middot; TradingView port &middot; four scripts: gold, HSI fade, Double Seven</p>
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
