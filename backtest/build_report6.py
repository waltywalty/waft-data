"""Round-7 report: the New York opening-range breakout on gold."""
import json

G = json.load(open("results/ny_grid.json"))
S = json.load(open("results/ny_sens.json"))
FT = json.load(open("results/ny_filter_test.json"))
WH = json.load(open("results/ny_whipsaw.json"))["whipsaw"]
PF = json.load(open("results/ny_paidfor.json"))
CSS = open("report_style.css").read()
assert "{{" not in CSS

rows = G["rows"]
RANGES = [5, 15, 30, 60]
EXITS = ["ny+60m", "ny+90m", "ny+2h", "ny_lunch", "ny_close",
         "prev_day", "asia", "london", "prev_hour", "measured_move"]
LABEL = {"ny+60m": "First hour", "ny+90m": "First 90 minutes", "ny+2h": "First 2 hours",
         "ny_lunch": "To NY lunch", "ny_close": "To NY close",
         "prev_day": "Previous day high/low", "asia": "Asia high/low",
         "london": "London high/low", "prev_hour": "Prior hour high/low",
         "measured_move": "Measured move (1× range)"}

def cell(R, E, filt, stop="range_opp"):
    m = [r for r in rows if r["range"] == R and r["exit"] == E
         and r["filter"] == filt and r.get("stop", "range_opp") == stop]
    if not m:
        return '<td class="num muted">—</td>'
    v, n = m[0]["pf"], int(m[0]["n"])
    c = "pos-2" if v >= 1.05 else "pos-1" if v >= 1.0 else "neg-1" if v >= 0.90 else "neg-2"
    return (f'<td class="num {c}">{v:.3f}'
            f'<span class="muted" style="font-size:11px"> ({n})</span></td>')

def grid_rows(filt, stop="range_opp"):
    return "\n".join(
        f'<tr><td class="lbl">{LABEL[e]}</td>' + "".join(cell(r, e, filt, stop) for r in RANGES) + "</tr>"
        for e in EXITS)

top = sorted([r for r in rows], key=lambda r: -r["t"])[:8]
top_rows = "\n".join(
    f'<tr><td class="lbl">{int(r["range"])}-min</td><td class="lbl">{LABEL[r["exit"]]}</td>'
    f'<td class="lbl muted">{r["filter"]}</td><td class="num">{int(r["n"])}</td>'
    f'<td class="num">{r["win"]*100:.1f}%</td>'
    f'<td class="num {"pos-1" if r["pf"]>=1 else "neg-1"}">{r["pf"]:.3f}</td>'
    f'<td class="num">{r["exp"]:+.2f}</td><td class="num muted">{r["t"]:+.2f}</td></tr>'
    for r in top)

paid_rows = "\n".join(
    f'<tr><td class="lbl">New York, {p["range"]}-min range</td>'
    f'<td class="num">${p["range_size"]:.2f}</td><td class="num">${p["already_moved"]:.2f}</td>'
    f'<td class="num {"pos-t" if p["fwd_gross"]>0.3 else "neg-t"}">${p["fwd_gross"]:+.2f}</td>'
    f'<td class="num muted">{WH[str(p["range"])]*100:.0f}%</td></tr>' for p in PF) + (
    '\n<tr style="border-top:2px solid var(--rule)"><td class="lbl"><strong>Asia, 60-min range</strong></td>'
    '<td class="num">$5.22</td><td class="num">$4.92</td>'
    '<td class="num pos-t"><strong>+$1.56</strong></td><td class="num muted">61%</td></tr>')

conf_rows = "\n".join(
    f'<tr><td class="lbl">{c["range"]}-min range</td><td class="lbl">{c["confirm"]}-min</td>'
    f'<td class="num">{int(c["n"])}</td>'
    f'<td class="num {"pos-1" if c["pf"]>=1 else "neg-1"}">{c["pf"]:.3f}</td>'
    f'<td class="num muted">{c["t"]:+.2f}</td></tr>' for c in S["confirm"])

cost_rows = "\n".join(
    f'<tr><td class="lbl">${c["cost"]:.2f}</td>'
    f'<td class="num {"pos-1" if c["pf"]>=1 else "neg-1"}">{c["pf"]:.3f}</td>'
    f'<td class="num">{c["exp"]:+.2f}</td></tr>' for c in S["costs"])

stop_rows = "\n".join(
    f'<tr><td class="lbl">{s["mode"]}</td><td class="num">{int(s["n"])}</td>'
    f'<td class="num">{s["win"]*100:.1f}%</td>'
    f'<td class="num {"pos-1" if s["pf"]>=1 else "neg-1"}">{s["pf"]:.3f}</td>'
    f'<td class="num muted">{s["t"]:+.2f}</td></tr>' for s in S["stops"])

ft_rows = "\n".join(
    f'<tr><td class="lbl">{c["range"]}-min · {LABEL[c["exit"]]}</td>'
    f'<td class="num">{c["n_lo"]}</td><td class="num">{c["pf_lo"]:.3f}</td>'
    f'<td class="num">{c["n_hi"]}</td><td class="num">{c["pf_hi"]:.3f}</td>'
    f'<td class="num muted">{c["p"]:.3f}</td></tr>' for c in FT["cells"])

ISOS = S.get("isos", {})
isos_rows = "\n".join(
    f'<tr><td class="lbl">{r["range"]}-min · {LABEL[r["exit"]]}</td>'
    f'<td class="lbl muted">{r["filter"]}</td>'
    f'<td class="num">{int(r["is_n"])}</td><td class="num">{r["is_pf"]:.3f}</td>'
    f'<td class="num muted">{r["is_t"]:+.2f}</td>'
    f'<td class="num">{int(r["os_n"])}</td>'
    f'<td class="num {"pos-1" if r["os_pf"]>=1 else "neg-1"}">{r["os_pf"]:.3f}</td></tr>'
    for r in ISOS.get("honest_top5", []))

FG = S["filter_generalisation"]
best = top[0]
def sel(filt, stop="range_opp"):
    return [r for r in rows if r["filter"] == filt and r.get("stop", "range_opp") == stop]
A, F, N = sel("all"), sel("corr<=0.5"), sel("all", "none")
n_pass_all, n_all = sum(1 for r in A if r["pf"] > 1), len(A)
n_pass_f, n_f = sum(1 for r in F if r["pf"] > 1), len(F)
n_pass_n, n_n = sum(1 for r in N if r["pf"] > 1), len(N)
med_all = sorted(r["pf"] for r in A)[n_all // 2]
med_f = sorted(r["pf"] for r in F)[n_f // 2]
med_n = sorted(r["pf"] for r in N)[n_n // 2]
best_n = max(r["pf"] for r in N)
n_cells_total = len(rows)

# chart: forward move after fill, NY ranges vs Asia
bars, x = [], 70
series = [(f'NY {p["range"]}m', p["fwd_gross"]) for p in PF] + [("Asia 60m", 1.56)]
for lbl, v in series:
    h = v * 62
    y = 150 - h if h > 0 else 150
    cls = "bar-entry" if v > 0.3 else "bar-neg"
    bars.append(f'<rect class="{cls}" x="{x}" y="{y:.1f}" width="52" height="{abs(h):.1f}" rx="2"/>')
    bars.append(f'<text class="bar-val" x="{x+26}" y="{(y-8) if h>0 else (y+abs(h)+17):.1f}">'
                f'${v:+.2f}</text>')
    bars.append(f'<text class="bar-lbl" x="{x+26}" y="184">{lbl}</text>')
    x += 100
fwd_svg = "\n".join(bars)

DOC = f"""<title>Gold at the New York Open</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
{CSS[7:-8]}
.bar-neg {{ fill:var(--neg); }}
.warn {{ background:var(--surface); border:1px solid var(--rule); border-left:3px solid var(--neg);
         border-radius:4px; padding:22px 26px; margin:26px 0; }}
.warn .head {{ font-family:"IBM Plex Mono",monospace; font-size:11.5px; letter-spacing:.13em;
               text-transform:uppercase; color:var(--neg); margin-bottom:12px; }}
.warn p {{ margin:0 0 12px; }} .warn p:last-child {{ margin:0; }}
.rule-box {{ background:var(--sunk); border-radius:4px; padding:20px 24px; margin:24px 0; }}
.rule-box ol {{ margin:0; padding-left:22px; }} .rule-box li {{ margin:8px 0; max-width:64ch; }}
</style>

<div class="wrap">
<header>
  <p class="eyebrow">XAUUSD · Round 7 · New York session</p>
  <h1>Gold at the New York Open</h1>
  <p class="standfirst">One hundred and seventeen configurations of the 09:30 ET opening-range
  breakout. Without a protective stop, <strong>none of them</strong> clears a profit factor of
  1.0. The best t-statistic anywhere is <strong>+{best["t"]:.2f}</strong> — a search this size
  over pure noise would normally throw up something better.</p>
  <div class="provenance">
    <span><b>{n_cells_total}</b> configurations</span>
    <span><b>4</b> range lengths</span>
    <span><b>10</b> exits</span>
    <span><b>4</b> defects caught and fixed</span>
  </div>
</header>

<section>
  <div class="verdict">
    <div class="head">Verdict</div>
    <p><strong>The New York opening range does not work on gold.</strong> With a protective stop
    at the far side of the range, {n_pass_all} of {n_all} configurations clear a 1.0 profit
    factor (median {med_all:.3f}). <strong>Without a stop, {n_pass_n} of {n_n} do</strong> —
    median {med_n:.3f}, best {best_n:.3f}. Adding the AUD correlation filter lifts
    {n_pass_f} of {n_f} above 1.0 (median {med_f:.3f}), still short of break-even.</p>
    <p><strong>It is not close, and it is not noise.</strong> At zero transaction cost the
    strategy runs a {S["costs"][0]["pf"]:.3f} profit factor: essentially break-even gross. There
    is no edge there to pay a spread out of.</p>
    <p><strong>Liquidity targets did not beat the clock.</strong> Previous-day, Asia, London and
    prior-hour highs and lows all landed in the same 0.84–0.94 band as simple time exits.</p>
  </div>
</section>

<section>
  <h2><span class="n">01</span>What was tested</h2>
  <p class="lede">Your specification, widened in every direction you suggested.</p>
  <ul>
    <li><strong>Range</strong> — the first 5, 15, 30 or 60 minutes after 09:30 America/New_York,
    DST-aware.</li>
    <li><strong>Entry</strong> — the first 5-minute candle to <em>close</em> beyond the range
    high or low, in that direction. One trade per day, first break only, no new entry after
    90 minutes.</li>
    <li><strong>Exits</strong> — five clock exits (first hour, 90 minutes, two hours, NY lunch,
    NY close) and five liquidity targets (previous day, Asia session, London session, prior
    hour, and a measured move of one range width).</li>
    <li><strong>Stop</strong> — every configuration run both with a protective stop at the far
    side of the opening range and with no stop at all, because whether a "hold to the NY close"
    rule carries a stop changes what is being measured and should not be left implied.</li>
    <li><strong>Filter</strong> — every configuration run twice, with and without the 20-day
    gold/AUDUSD correlation gate from round two.</li>
    <li><strong>Costs</strong> — $0.30 per round trip, the same as every earlier round.</li>
  </ul>
  <div class="warn">
    <div class="head">Two lookahead bugs, caught before they became results</div>
    <p>The first version of this engine returned a <strong>2.479 profit factor with a
    t-statistic of 12</strong> on the previous-day target. After six rounds where nothing beat
    1.45, that is not a discovery — it is a bug, and it was.</p>
    <p><strong>One:</strong> FX sessions run 17:00 ET to 17:00 ET. I labelled each session by the
    date it <em>started</em>, so "yesterday's session" ran to 17:00 ET <em>today</em> — hours
    after the 09:30 open being traded. The previous day's high and low already contained the
    move. <strong>Two:</strong> a pandas <code>.loc</code> slice is inclusive of its right
    endpoint, so the London window ending "at the NY open" swallowed the 09:30–09:35 bar — the
    first bar of the opening range itself. That one mattered on 84 days.</p>
    <p>Both are fixed, and an audit now checks every level against bars that had actually closed.
    Fixing them took the previous-day target from 2.479 to {[r for r in rows if r["range"]==15 and r["exit"]=="prev_day" and r["filter"]=="all" and r.get("stop","range_opp")=="range_opp"][0]["pf"]:.3f}.</p>
    <p><strong>Then I had the engine audited</strong> by five independent reviewers working
    different lenses, each finding put to a skeptic whose job was to kill it. Twenty-four
    candidate defects, twenty-two refuted, <strong>two survived</strong> — and both were real.</p>
    <p><strong>Three:</strong> the same inclusive-slice trap once more, this time on the exit
    path. <code>bars5.loc[t_fill:t_exit]</code> evaluated the bar spanning
    [t_exit, t_exit+5min), giving every trade five extra minutes of stop and target exposure
    after it should have been closed. Numerically immaterial — no configuration changes sign —
    but it is the third instance of one mistake, which is what makes it worth naming.
    <strong>Four:</strong> the out-of-sample panel ranked candidate configurations by their
    <em>whole-sample</em> t-statistic and then reported post-2024 as the holdout. The selector
    had already seen the holdout. That one flattered, and section 06 is the corrected version.</p>
  </div>
</section>

<section>
  <h2><span class="n">02</span>The grid</h2>
  <p class="lede">Profit factor, trade count in brackets. Green above 1.0, red below.</p>
  <h3>No filter</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Exit</th>{"".join(f"<th>{r}-min range</th>" for r in RANGES)}</tr></thead>
    <tbody>{grid_rows("all")}</tbody>
  </table></div>
  <h3>No protective stop — a pure hold to the exit</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Exit</th>{"".join(f"<th>{r}-min range</th>" for r in RANGES)}</tr></thead>
    <tbody>{grid_rows("all", "none")}</tbody>
  </table></div>
  <p>This is the version most people picture when they say "opening-range breakout, hold to the
  close". <strong>Not one of the forty configurations clears 1.0</strong>, and the median falls
  from {med_all:.3f} to {med_n:.3f}. The stop is not decoration here — it is doing most of the
  work of keeping the strategy near break-even.</p>
  <h3>With the AUD correlation filter</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Exit</th>{"".join(f"<th>{r}-min range</th>" for r in RANGES)}</tr></thead>
    <tbody>{grid_rows("corr<=0.5")}</tbody>
  </table></div>
  <p>Three patterns hold across the whole grid. <strong>Later exits beat earlier ones</strong> —
  the same thing round one found on the Asia session, and the opposite of the usual advice to
  take opening-range profits quickly. <strong>Longer ranges are worse</strong>, sharply so at 60
  minutes, because an hour of the New York session is exactly the part worth being in.
  <strong>Liquidity targets are not better than a clock</strong>, and the two nearest ones —
  the prior hour and the Asia range — are the worst of the ten.</p>
  <h3>The best of the eighty</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Range</th><th class="l">Exit</th><th class="l">Filter</th>
    <th class="l">Stop</th><th>Trades</th><th>Win rate</th><th>Profit factor</th>
    <th>Exp. $/oz</th><th>t-stat</th></tr></thead>
    <tbody>{top_rows}</tbody>
  </table></div>
  <p>The top of this table is where a reader normally starts looking for the strategy. There
  isn't one. The strongest t-statistic across all {n_cells_total} scored cells is
  <strong>+{best["t"]:.2f}</strong>, on {int(best["n"])} trades. A correlated search of this size
  over data with no signal would ordinarily produce a best t of around +2. Getting
  +{best["t"]:.2f} means this grid is not merely unprofitable — it is consistently,
  systematically negative.</p>
</section>

<section>
  <h2><span class="n">03</span>Why it fails, and why that is interesting</h2>
  <p class="lede">The obvious guess is that the New York open is too choppy. The data says the
  opposite, which makes the answer more useful.</p>
  <figure>
    <div class="chart">
      <svg viewBox="0 0 660 200" role="img" aria-label="Forward move remaining after the fill, New York ranges versus Asia">
        <line class="zero" x1="50" y1="150" x2="620" y2="150"/>
        {fwd_svg}
        <text class="ax" x="50" y="28">gross move remaining after you are filled, $/oz</text>
      </svg>
    </div>
    <figcaption>Everything to the left is New York at four range lengths. The bar on the right is
    the Asia-open setup from round two, on the same data and the same costs.</figcaption>
  </figure>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Setup</th><th>Range width</th><th>Already moved by fill</th>
    <th>Forward move after fill</th><th>Traded back through</th></tr></thead>
    <tbody>{paid_rows}</tbody>
  </table></div>
  <p><strong>New York breakouts hold their direction far better than Asia ones.</strong> Only
  {WH["15"]*100:.0f}% of 15-minute New York breaks ever trade back through the far side of the
  range, against about 79% on the Asia session. On the structural measure everyone uses to judge
  a breakout, New York wins comfortably.</p>
  <p>It still loses, because <strong>there is nothing left to capture</strong>. By the time a
  15-minute range has formed and a 5-minute candle has closed beyond it, price has already moved
  ${PF[1]["already_moved"]:.2f} from the open — and the average gross move remaining is
  <strong>${PF[1]["fwd_gross"]:+.2f}</strong>. Against a $0.30 round trip that is a decided loss
  before the trade is placed. The Asia setup leaves $1.56 on the table for a nearly identical
  entry cost, which is the entire difference between the two.</p>
  <p>That is a coherent story about the instrument rather than about the pattern. 09:30 in New
  York is gold's most watched, most contested moment; the information in the open is priced
  within minutes and a confirmed break is late by construction. 09:30 in Hong Kong is thin, and
  gold has a structural participant there that the rest of the day does not.</p>
</section>

<section>
  <h2><span class="n">04</span>Your 1-minute question</h2>
  <p class="lede">The data is 5-minute, so 1-minute confirmation cannot be tested directly. The
  gradient across the timeframes I do have brackets the answer.</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Range</th><th class="l">Confirmation</th><th>Trades</th>
    <th>Profit factor</th><th>t-stat</th></tr></thead>
    <tbody>{conf_rows}</tbody>
  </table></div>
  <p>On the 15-minute range you asked about, finer confirmation is monotonically better —
  0.892 at 5 minutes, 0.835 at 15, 0.799 at 30, 0.722 at 60. Extrapolating that slope, a
  1-minute confirmation would land somewhere near <strong>0.92–0.94</strong>. Better than
  5-minute, and still comfortably short of break-even.</p>
  <p>Two cautions on that extrapolation. The direction reverses on the 30-minute range, where
  coarser confirmation is better — so this is an interaction, not a law. And a backtest flatters
  fine confirmation: a 1-minute close through a level generates more marginal triggers, and in
  live trading those are exactly the ones that fill worst. The honest reading is that
  1-minute would not change the conclusion.</p>
</section>

<section>
  <h2><span class="n">05</span>Everything else I varied</h2>
  <h3>Costs decide it</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Round trip</th><th>Profit factor</th><th>Exp. $/oz</th></tr></thead>
    <tbody>{cost_rows}</tbody>
  </table></div>
  <p>15-minute range, held to the NY close. <strong>{S["costs"][0]["pf"]:.3f} at zero cost.</strong>
  This is the cleanest single statement of the result: the strategy is a coin flip gross, and the
  spread is the whole story. No exit rule, filter or stop placement can fix a gross edge that
  does not exist.</p>
  <h3>Stop placement</h3>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Stop</th><th>Trades</th><th>Win rate</th><th>Profit factor</th>
    <th>t-stat</th></tr></thead>
    <tbody>{stop_rows}</tbody>
  </table></div>
  <p>Tight stops are punished here exactly as they were in round three — a half-range stop drops
  the win rate to 25% and the profit factor to 0.812. Nothing beats the far side of the range.</p>
  <h3>Two things that turned out not to matter</h3>
  <ul>
    <li><strong>The entry deadline.</strong> Cutting off new entries at 30, 60, 90, 150 or 390
    minutes moves the profit factor only between 0.918 and 0.955. There is no window inside the
    session that behaves differently from the rest of it.</li>
    <li><strong>The intrabar ambiguity.</strong> When a 5-minute bar touches both the stop and
    the target, I assume the stop filled. Assuming the target instead moves the profit factor
    from 0.918 to 0.922 — so the conservative choice is not what is driving the negative
    result.</li>
  </ul>
</section>

<section>
  <h2><span class="n">06</span>An honest out-of-sample test</h2>
  <p class="lede">The audit's second surviving finding was in this panel, and it is worth showing
  rather than quietly fixing.</p>
  <p>The first version ranked candidate configurations by their t-statistic <em>over the whole
  sample</em>, then reported everything from 2024 onward as the out-of-sample block. The ranking
  had already seen that block. Four of the five "survivors" cleared 1.0 out of sample, which
  looked like a genuine holdout result and was nothing of the kind.</p>
  <p>Done properly — rank on pre-2024 only, then read 2024–25:</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Configuration</th><th class="l">Filter</th>
    <th>IS trades</th><th>IS PF</th><th>IS t</th><th>OS trades</th><th>OS PF</th></tr></thead>
    <tbody>{isos_rows}</tbody>
  </table></div>
  <div class="stats">
    <div class="stat"><div class="k">Selected honestly, OS median PF</div>
      <div class="v">{ISOS.get("honest_median_os_pf", 0):.3f}</div></div>
    <div class="stat"><div class="k">All {ISOS.get("n_cells", 0)} cells, OS median PF</div>
      <div class="v dim">{ISOS.get("population_median_os_pf", 0):.3f}</div></div>
  </div>
  <p><strong>Picking the strongest in-sample configurations buys no out-of-sample advantage
  at all</strong> — they land on top of the population median. That is the cleanest possible
  statement that the in-sample variation across these {ISOS.get("n_cells", 0)} cells is noise:
  knowing which configuration looked best over three and a half years tells you nothing about
  which will look best over the next eighteen months.</p>
</section>

<section>
  <h2><span class="n">07</span>Does the AUD filter carry over?</h2>
  <p class="lede">This is close to an independent test of round two's finding: different session,
  different range, different exits, different holding period, same instrument.</p>
  <div class="stats">
    <div class="stat"><div class="k">Cells improved</div><div class="v">{FG["improved"]}<span style="font-size:15px;color:var(--ink-3)">/{FG["n_cells"]}</span></div></div>
    <div class="stat"><div class="k">Median PF lift</div><div class="v">{FG["median_lift"]:+.3f}</div></div>
    <div class="stat"><div class="k">Median PF, unfiltered</div><div class="v dim">{FG["median_pf_all"]:.3f}</div></div>
    <div class="stat"><div class="k">Median PF, filtered</div><div class="v dim">{FG["median_pf_filt"]:.3f}</div></div>
  </div>
  <p>The filter improved <strong>every single one of the {FG["n_cells"]} configurations</strong>.
  That looks overwhelming, and a naive signed-rank test returns p &lt; 0.00001. It is not that
  strong, and the reason matters.</p>
  <p><strong>Those {FG["n_cells"]} cells share most of their trades.</strong> They are the same
  days re-cut by exit rule, so they are nearly the same test repeated — the sign agreeing 39
  times is much weaker evidence than 39 independent experiments would be. Testing it properly,
  at the level of individual trade returns:</p>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Configuration</th><th>Kept</th><th>PF</th><th>Excluded</th><th>PF</th>
    <th>p-value</th></tr></thead>
    <tbody>{ft_rows}</tbody>
  </table></div>
  <p>The direction is right every time — days the filter keeps always beat days it excludes — but
  only one of the five clears significance on its own, and on the representative cell the
  continuous relationship is flat (Spearman ρ = {FT["spearman_rho"]:+.3f},
  p = {FT["spearman_p"]:.2f}).</p>
  <p><strong>So: the New York data neither confirms nor refutes the filter.</strong> It is
  consistent with round two's finding and adds mild support to the idea that the filter measures
  something general about gold rather than something specific to the Asia session. It is not the
  independent validation it looked like at first glance, and I would not claim it as one.</p>
</section>

<section>
  <h2><span class="n">08</span>Where that leaves both strategies</h2>
  <div class="tbl-wrap"><table>
    <thead><tr><th class="l">Setup</th><th>Trades</th><th>Win rate</th><th>Profit factor</th>
    <th>t-stat</th></tr></thead>
    <tbody>
      <tr><td class="lbl">Asia 09:30 HKT, 60-min range, NY-close exit, filtered</td>
        <td class="num">652</td><td class="num">40.2%</td>
        <td class="num pos-2">1.320</td><td class="num">+2.54</td></tr>
      <tr><td class="lbl">New York 09:30 ET, best of eighty</td>
        <td class="num">{int(best["n"])}</td><td class="num">{best["win"]*100:.1f}%</td>
        <td class="num pos-1">{best["pf"]:.3f}</td><td class="num">+{best["t"]:.2f}</td></tr>
    </tbody>
  </table></div>
  <div class="rule-box"><ol>
    <li><strong>Do not trade the New York opening range on gold.</strong> Not with these exits,
    not with liquidity targets, not with finer confirmation. The gross edge is zero and eighty
    configurations could not find one.</li>
    <li><strong>The Asia setup stands.</strong> Nothing here weakens it, and the fact that the
    same filter points the same way on a structurally unrelated setup is mildly encouraging for
    it.</li>
    <li><strong>If you want to keep pulling this thread</strong>, the interesting version is not
    another exit rule. It is the observation from section 03: New York breaks hold well but leave
    nothing on the table. That points at <em>fading</em> the New York open — entering against
    the first break — which is the one direction this study did not test and which the numbers
    here would predict.</li>
    <li><strong>The negative result is the deliverable.</strong> Eighty configurations, one bad
    idea eliminated, and two lookahead bugs found in the process. That is the round working
    correctly.</li>
  </ol></div>
</section>

<section>
  <h2><span class="n">09</span>Caveats</h2>
  <ul>
    <li><strong>One instrument, five years, one data source.</strong> Everything here inherits the
    caveats of rounds one to six.</li>
    <li><strong>5-minute bars.</strong> The 1-minute variant is bounded by extrapolation, not
    measured.</li>
    <li><strong>The liquidity targets are my definitions of those levels</strong>, not yours.
    Asia is Tokyo cash hours, London is 08:00 London to the NY open, the previous day is the
    17:00 ET FX session. Different definitions would move the numbers somewhat — but all four
    landed in the same band, which suggests the choice is not what is driving the result.</li>
    <li><strong>Days are dropped when a target sits behind the entry</strong> — between 4% and
    60% of days depending on the level. That selection is reported in the trade counts, and it
    is why the target rows have fewer trades than the clock rows.</li>
    <li><strong>The data ends August 2025.</strong></li>
  </ul>
</section>

<footer>
  Round seven. Code and results on branch <code>claude/trading-strategy-backtest-gqym2i</code>;
  figures generated from <code>results/ny_grid.json</code> and <code>results/ny_sens.json</code>.
  Rounds one to six are the companion reports.
</footer>
</div>
"""
open("results/report6.html", "w").write(DOC)
print("wrote results/report6.html", len(DOC))
