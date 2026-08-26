"""Generate results/trade_journal.html - a self-saving forward-test journal.

The page carries its trades as embedded JSON and, via the artifact runtime's
`artifact` capability, republishes itself when a row is added or removed, so
the record lives in the page. The page embeds its own pristine template (a
text/plain slot with `</` escaped) so each save regenerates the document from
the template + state, never from the live DOM.
"""
import json

TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Asia Gold Trade Journal</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:wght@600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root { --ground:#FBFBFC; --surface:#FFFFFF; --sunk:#F3F4F7; --ink:#16191F;
  --ink-2:#4A515E; --ink-3:#7C8496; --rule:#DFE2E9; --brass:#8A6420;
  --pos:#1B6E55; --pos-bg:#E4F1EB; --neg:#A83226; --neg-bg:#FAE7E4; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --ground:#0E1116; --surface:#161A21; --sunk:#1B2029; --ink:#E8EAEF;
  --ink-2:#A7AEBC; --ink-3:#767E8E; --rule:#272D38; --brass:#D5A64A;
  --pos:#5CBE99; --pos-bg:#14291F; --neg:#E58275; --neg-bg:#2C1714; } }
:root[data-theme="dark"] { --ground:#0E1116; --surface:#161A21; --sunk:#1B2029;
  --ink:#E8EAEF; --ink-2:#A7AEBC; --ink-3:#767E8E; --rule:#272D38;
  --brass:#D5A64A; --pos:#5CBE99; --pos-bg:#14291F; --neg:#E58275; --neg-bg:#2C1714; }
* { box-sizing:border-box; }
body { margin:0; background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:16px; line-height:1.55; }
.wrap { max-width:860px; margin:0 auto; padding:28px 18px 80px; }
h1 { font-family:Spectral,Georgia,serif; font-weight:600; font-size:30px; margin:0 0 4px; }
.sub { color:var(--ink-2); margin:0 0 20px; max-width:60ch; }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:1px;
  background:var(--rule); border:1px solid var(--rule); border-radius:6px; overflow:hidden; margin:0 0 24px; }
.stat { background:var(--surface); padding:12px 14px; }
.stat .k { font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.08em;
  text-transform:uppercase; color:var(--ink-3); }
.stat .v { font-family:"IBM Plex Mono",monospace; font-size:20px; margin-top:3px;
  font-variant-numeric:tabular-nums; }
form { background:var(--surface); border:1px solid var(--rule); border-radius:6px;
  padding:16px; display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
  gap:12px; align-items:end; margin-bottom:10px; }
label { display:grid; gap:5px; font-size:12px; color:var(--ink-2); font-weight:500; }
input, .seg button { font-family:"IBM Plex Mono",monospace; font-size:16px; color:var(--ink);
  background:var(--sunk); border:1px solid var(--rule); border-radius:6px;
  padding:12px 10px; min-height:48px; width:100%; }
input:focus { outline:2px solid var(--brass); }
.seg { display:flex; gap:6px; }
.seg button { cursor:pointer; font-weight:600; }
.seg button.on-L { background:var(--pos-bg); color:var(--pos); border-color:var(--pos); }
.seg button.on-S { background:var(--neg-bg); color:var(--neg); border-color:var(--neg); }
.add { grid-column:1 / -1; font-family:"IBM Plex Sans",sans-serif; font-size:16px; font-weight:600;
  color:#fff; background:var(--brass); border:none; border-radius:6px; padding:14px; min-height:50px; cursor:pointer; }
.notice { min-height:22px; font-size:13px; color:var(--ink-3); margin:6px 2px 18px; }
.tblwrap { overflow-x:auto; border:1px solid var(--rule); border-radius:6px; background:var(--surface); }
table { border-collapse:collapse; width:100%; font-size:14px; }
th { font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.07em; text-transform:uppercase;
  color:var(--ink-3); text-align:right; padding:10px 12px; border-bottom:1px solid var(--rule); }
th:first-child { text-align:left; }
td { padding:9px 12px; border-bottom:1px solid var(--rule); text-align:right;
  font-family:"IBM Plex Mono",monospace; font-variant-numeric:tabular-nums; }
td:first-child { text-align:left; }
tr:last-child td { border-bottom:none; }
.pnl-pos { color:var(--pos); } .pnl-neg { color:var(--neg); }
.del { background:none; border:none; color:var(--ink-3); font-size:16px; cursor:pointer; padding:4px 8px; }
.empty { padding:26px; text-align:center; color:var(--ink-3); font-size:14px; }
footer { margin-top:26px; font-size:12.5px; color:var(--ink-3); max-width:64ch; }
</style></head><body>
<div class="wrap">
<h1>Asia Gold Trade Journal</h1>
<p class="sub">One row per trade: the paper forward test of the deployed rule. Adding or
removing a row saves the page itself &mdash; this page is the record.</p>
<div class="stats" id="stats"></div>
<form id="f" autocomplete="off">
  <label>Date<input type="date" id="f-date"></label>
  <label>Side<span class="seg"><button type="button" id="btnL">LONG</button><button type="button" id="btnS">SHORT</button></span></label>
  <label>Entry<input type="text" inputmode="decimal" id="f-entry" placeholder="4661.8"></label>
  <label>Stop<input type="text" inputmode="decimal" id="f-stop" placeholder="4616.3"></label>
  <label>Exit<input type="text" inputmode="decimal" id="f-exit" placeholder="4685.0"></label>
  <button class="add" type="submit">Add trade &amp; save</button>
</form>
<div class="notice" id="notice"></div>
<div class="tblwrap"><table>
<thead><tr><th>Date</th><th>Side</th><th>Entry</th><th>Stop</th><th>Exit</th><th>P&amp;L $/oz</th><th></th></tr></thead>
<tbody id="rows"></tbody>
</table></div>
<footer>Rule reminder: corr &le; 0.5, first 60m close beyond the 09:30&ndash;10:30 HKT
range, stop 2&times; range, flat 16:00 New York, flat 1% risk. Log every trade the
alerts fire, including losers &mdash; the monthly review scores this page against the
playbook.</footer>
</div>
<script id="state" type="application/json">@@STATE@@</script>
<script id="tpl" type="text/plain">@@TPL@@</script>
<script>
var state = JSON.parse(document.getElementById('state').textContent);
var tplRaw = document.getElementById('tpl').textContent.replace(/<\\\\\\//g, '</');
var art = null, side = 'L';
if (window.claude && window.claude.use) {
  window.claude.use('artifact').then(function (a) { art = a; setNotice(a ? '' :
    'Read-only view: saving unavailable here. Rows added now will not persist.'); });
}
function esc(s) { return String(s).replace(/[&<>"]/g, function (c) {
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
function pnl(r) { return (r.side === 'L' ? 1 : -1) * (r.exit - r.entry); }
function render() {
  var tb = document.getElementById('rows');
  if (!state.trades.length) {
    tb.innerHTML = '<tr><td colspan="7" class="empty">No trades yet. The drought counts too - it is the filter working.</td></tr>';
  } else {
    tb.innerHTML = state.trades.map(function (r, i) {
      var p = pnl(r);
      return '<tr><td>' + esc(r.date) + '</td><td>' + (r.side === 'L' ? 'LONG' : 'SHORT') +
        '</td><td>' + r.entry.toFixed(2) + '</td><td>' + r.stop.toFixed(2) +
        '</td><td>' + r.exit.toFixed(2) + '</td><td class="' + (p >= 0 ? 'pnl-pos' : 'pnl-neg') +
        '">' + (p >= 0 ? '+' : '') + p.toFixed(2) + '</td>' +
        '<td><button class="del" data-i="' + i + '" aria-label="delete row">&#10005;</button></td></tr>';
    }).join('');
  }
  var ps = state.trades.map(pnl);
  var wins = ps.filter(function (x) { return x > 0; });
  var losses = ps.filter(function (x) { return x <= 0; });
  var gw = wins.reduce(function (a, b) { return a + b; }, 0);
  var gl = -losses.reduce(function (a, b) { return a + b; }, 0);
  var st = [['trades', ps.length],
            ['win rate', ps.length ? Math.round(100 * wins.length / ps.length) + '%' : '-'],
            ['total $/oz', ps.length ? (gw - gl >= 0 ? '+' : '') + (gw - gl).toFixed(1) : '-'],
            ['profit factor', gl > 0 ? (gw / gl).toFixed(2) : (gw > 0 ? '&infin;' : '-')]];
  document.getElementById('stats').innerHTML = st.map(function (s) {
    return '<div class="stat"><div class="k">' + s[0] + '</div><div class="v">' + s[1] + '</div></div>';
  }).join('');
}
function buildDoc() {
  return tplRaw.replace('@@' + 'STATE@@', JSON.stringify(state))
               .replace('@@' + 'TPL@@', tplRaw.replace(/<\\//g, '<\\\\/'));
}
function setNotice(m) { document.getElementById('notice').textContent = m; }
function save(msg) {
  render();
  if (!art) { setNotice('Not saved - this view cannot publish. ' + msg); return; }
  art.publish(buildDoc()).then(function () { setNotice('Saved. ' + msg); },
    function (e) { setNotice(e && e.code === 'conflict' ?
      'Another view saved first - reloading to the latest version.' :
      'Save failed (' + (e && e.code ? e.code : 'error') + '). Row is on screen but not stored.'); });
}
function pick(s) {
  side = s;
  document.getElementById('btnL').className = s === 'L' ? 'on-L' : '';
  document.getElementById('btnS').className = s === 'S' ? 'on-S' : '';
}
document.getElementById('btnL').addEventListener('click', function () { pick('L'); });
document.getElementById('btnS').addEventListener('click', function () { pick('S'); });
document.getElementById('f').addEventListener('submit', function (ev) {
  ev.preventDefault();
  var d = document.getElementById('f-date').value;
  var e = parseFloat(document.getElementById('f-entry').value);
  var st = parseFloat(document.getElementById('f-stop').value);
  var x = parseFloat(document.getElementById('f-exit').value);
  if (!d || !isFinite(e) || !isFinite(st) || !isFinite(x)) {
    setNotice('Fill in date, entry, stop and exit (numbers) first.'); return;
  }
  state.trades.push({ date: d, side: side, entry: e, stop: st, exit: x });
  state.trades.sort(function (a, b) { return a.date < b.date ? -1 : 1; });
  ['f-entry', 'f-stop', 'f-exit'].forEach(function (id) { document.getElementById(id).value = ''; });
  save('Trade added.');
});
document.getElementById('rows').addEventListener('click', function (ev) {
  var b = ev.target.closest('.del');
  if (!b) return;
  state.trades.splice(parseInt(b.dataset.i, 10), 1);
  save('Row removed.');
});
document.getElementById('f-date').value = new Date().toISOString().slice(0, 10);
pick('L');
render();
</script>
</body></html>"""

init = {"version": 1, "trades": []}
doc = TEMPLATE.replace("@@STATE@@", json.dumps(init))
doc = doc.replace("@@TPL@@", TEMPLATE.replace("</", "<\\/"))
open("results/trade_journal.html", "w").write(doc)
print(f"written results/trade_journal.html ({len(doc):,} bytes)")
