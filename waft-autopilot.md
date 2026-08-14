# AUTOPILOT — autonomous work protocol for the WAFT dashboard

<!-- AUTOSTATE-BEGIN -->
## AUTOSTATE — generated 2026-08-13 09:14Z by `stategen.py`. Do not hand-edit.

Everything in this block is measured off the workspace at the moment it ran, and
nothing in it is remembered. If it contradicts a narrative STATE block below,
**this block is right and the prose is stale** — that is the whole point of it.

### the artifacts
- source  `waft-dashboard.src.html`  1,253,044 bytes, sha `ae0443d65eea`, 39m ago
- built   `waft-dashboard.html`  1,659,538 bytes, 37m ago

### the last battery
- log     `suites.run23.log`, 3m ago
- verdict **63 passed**
- ran AFTER the newest source edit, so its verdict is about this code.

### the suite registry
- 3 of them are build GATES run by `build.mjs` on every bake: ladtest, railtest, scoretest
- **62 suites registered**, 53 browser-driven
- every suite on disk is registered and every registered suite is on disk.

### the relay archive
- HEAD    `81b533275 13 Aug 08:26Z waft 2026-08-13T08:26:02Z ok=1 err=0`
- tag     `presquash-20260804` present
- tag     `archive-local-20260806` present
- bars    newest print 69m ago (`2026-08-13.jsonl`, 445 rows)
- level with `origin/main` as of the last fetch (48m ago)

### the packed toolchain
- newest  `waft-toolchain.tgz`  1,233,359 bytes, 0s ago
- contains the source that is on disk (sha `ae0443d65eea`)

### the audit list
- **13 of 13 shipped**
- every item is present in the workspace and covered by a registered suite.
- item 7 self-tests clean (`watch.py --selftest`)

### the lessons
- **12 lessons**, 4 enforced by a check in `lessons.py`, 8 still prose
- every unenforced one says why it cannot be mechanised.

### the prose anchors
- 9 prose anchors, worst at 46% of its tolerance; 1 bin anchor(s) within two bins of the window edge

### the queue
- 18 items, 13 marked DONE, 5 open

<!-- AUTOSTATE-END -->

Written 2026-08-07 ~10:00Z. Walton is away for hours-to-days and has authorised
continuous autonomous development: "keep autonomously working throughout and
developing until we have reached something similar to our end goal. Do this step
by step and make sure to always audit and plan your next steps."

## THE END GOAL, in his words across the session
A dashboard that is visually immediate rather than word-heavy (key info stands
out via size/weight/colour — colour never alone), covers MHI/NQ/YM as deeply as
ES/RTY, stays honestly live (never stale-while-looking-live), and whose every
number is measured rather than remembered. Plus the daily brief cycle.

## PER-WAKEUP PROTOCOL (follow in order, every time)
1. AUDIT FIRST: read this file; check the last battery log (`tail -5
   /tmp/dash/suites*.out`, newest number = latest); `git -C /tmp/wd fetch` +
   merge (origin/main may have moved); check droplet feed health via
   `latest/free-bars.json` symbols/ts. If anything is red, FIX BEFORE NEW WORK.
2. ONE SCOPED CHANGE per wakeup (or one coherent pair). Batch all source edits,
   refresh ONCE at the end (the prose treadmill: SCENARIOS ages drift ±2h).
3. VERIFY: build (all 11 gates) + full battery detached (~18 min; poll with
   `ps -eo pid,etime,args`, NEVER pgrep -f). New geometry/painter work needs its
   own suite + guardtest (reachability preconditions: unless/unlessWhy pattern).
4. DELIVER: SendUserFile the three artifacts (waft-dashboard.html, .src.html,
   toolchain tarball incl. mhi-ibkr.json + av-y30.json), status "normal", short
   caption. Low-noise: no proactive pings unless something is genuinely urgent.
5. RECORD: update the "STATE" and "QUEUE" sections below (this file is the
   memory across compactions — assume the next wakeup remembers NOTHING else).
6. SCHEDULE the next wakeup via mcp__claude-code-remote__send_later with a
   message that names the ONE task, points here, and says "work autonomously,
   Walton is away". Cadence guidance: substantive blocks, not pings —
   3–6h apart while work remains; longer overnight. Monday 00:00Z trigger
   (trig_011mCNWVeq9Dsa8JFvaBFMSo) fires the Monday brief into THIS session —
   do not duplicate it, and leave the workspace green before it fires.

## HARD CONSTRAINTS (unchanged, non-negotiable)
- Security block as in the Monday trigger text: read-only GitHub token; /tmp/wd
  not /tmp/wdfull; no trade/order/alert endpoints on Webull OR IBKR ever; no
  routing around WebFetch/robots blocks; do not mention the waft-droplet token.
- Do NOT use AskUserQuestion. Walton is away; make the reasonable call, state it.
- CALLS entries are judged at resolution, never re-judged. Don't touch 31 Jul oil.
- Friday trigger: do not re-push. Monday trigger: updated 7 Aug ~09:25Z, current.
- Edits via python str.replace with count asserts. NEVER `ladgen.py > file`
  (it writes its own file). httpd: bare setsid incantation, check before builds.
- ES5 in the painter. innerText=reader cost, textContent=losslessness.

## STATE as of 2026-08-11 ~14:00Z (audit item 12 SHIPPED — THE AUDIT LIST IS CLOSED)
- AUDIT ITEM 12 SHIPPED: MHI measured on the contract that actually trades.
  Pulled 1,382 fifteen-minute HKFE bars (10 Jul - 10 Aug, 723,458 contracts)
  through the IBKR read-only connector — twelve times the 123-bar fixture the
  board had been carrying, and it includes the after-hours session.
  · mhigen.py builds the block: volume profile, POC, value area, session weights,
    typical 30-minute travel, weighted turn levels, and the roll detector LIFTED
    from liquidity2 rather than copied.
  · THE NUMBER THIS BOARD NEVER HAD: 44 points per 30 minutes = HK$440 a
    contract. A cash index cannot produce it — an index has no contract.
  · Value 25,650-26,025, POC 25,850, and the day session alone picks the SAME
    POC — the opposite of what the same test says on ES, so the all-hours profile
    is usable here where it is not there.
  · After-hours carries 62% of the bars and 19% of the volume, so a turn there
    weighs 0.38 against 1.00. Measured from this window's own volume.
  · Levels are labelled TURNS, never stop pools: this feed has no order book
    either, and the card already refuses that claim elsewhere.
- THE BASIS IS NOW REFUSED, AND THE REFUSAL IS A MEASUREMENT. Across 61 instants
  where both series print, the middle half of the readings spans 23.7 points
  against a 22.8-point floor set by the CASH FEED'S OWN bar-to-bar movement — so
  what looked like a basis is dominated by the two feeds not being stamped
  together. Tightening the match from 300s to 30s was tried FIRST and moved
  nothing (61 samples -> 60, identical distribution), which rules out timestamp
  slop and leaves feed lag. The -5.8 this board published was false precision by
  an order of magnitude. It matters less than it did: the figures above need no
  basis at all. BI_BASIS is left alone — at 0.99978 vs 1.0 the difference is under
  a quarter of a 25-point bin, which the new measurement strengthens rather than
  contradicts.
- NEW SUITES -> 56: mhitest.mjs, mhi_guardtest.mjs. Its sharpest check came from
  its own guardtest: a mutant that inflated the headline move sailed through
  because the suite only checked the MONEY figure, so the panel could print
  "66 pt / 30 min" beside "HK$440 a contract" — one quantity contradicting itself
  in two lines. Both halves are now checked, and cross-checked at the multiplier.
- EVERY AUDIT ITEM IS NOW CLOSED: 1,2,3,4,5,6,8,9,10,11,12,13 shipped; 7 delivered
  as a droplet script with a one-paste install (it cannot run from this container).

## STATE as of 2026-08-11 ~11:00Z (audit item 7 DELIVERED as a droplet script)
- AUDIT ITEM 7: watch.py, the relay-side watcher. It cannot be installed from
  here — the droplet is not reachable from this container and its keys never come
  into chat — so it is delivered as a file plus a one-paste install, which is the
  same shape as GUARD_FIX.
  · WATCHES ONLY WHAT THE PAGE ALREADY COMMITTED TO IN WRITING: the trigger and
    invalidation of every live PLAN entry, PARSED OUT OF THE SHIPPED PAGE so the
    watcher cannot hold its own stale copy of a level. It is not a signal
    generator; an alert on something nobody wrote down beforehand is a new
    opinion arriving at 6am.
  · TOUCHED, NOT CLOSED — the same words the plan card uses, carried into the
    alert so nothing is louder than what the board itself would say.
  · ONE ALERT PER LEVEL PER DAY via a state file. Without it a level sitting
    inside the day range re-fires every poll, and a channel that cries once a
    minute gets muted before the one that matters.
  · Two sinks: alerts.json beside the other latest/ files (always), and an
    optional WAFT_WATCH_HOOK URL from the environment. NO KEY IN THE FILE.
  · `--selftest` drives every rule with known answers; it caught two of my own
    errors on the first run — an assertion that had the market backwards (a
    BELOW level above the day's high HAS been satisfied), and an entry regex that
    modelled the literal's whitespace and matched ZERO entries on the live page,
    reporting "nothing to watch" indistinguishably from a quiet day.
  · Dry run against the live payload agrees with the board: RTY short's
    invalidation at 3,015.00 shows traded, which is what the plan card already
    says ("1 invalidated by the tape").
- REMAINING FROM THE AUDIT: only item 12 (MHI real futures data, L). It needs a
  data source rather than page work — the HK board's levels are still measured on
  the cash index with a dated basis beside them, which the card states.

## STATE as of 2026-08-11 ~10:00Z (audit item 5 SHIPPED — the trade journal)
- AUDIT ITEM 5 SHIPPED: the trade journal, bottom of the deck under sizing.
  The scorecard grades the ANALYSIS; nothing recorded what was DONE. A board can
  be right about a level all week while the account bleeds out in a session
  nobody looked at.
  · Records contract / side / entry / exit / contracts / note; splits P&L BY
    SESSION using sessAt() — the same function the clock, the pace model and the
    liquidity weights use — and prices a point from SIZE_SPEC, the same table the
    sizing card uses. Neither is re-derived.
  · CURRENCIES ARE NEVER ADDED. MHI settles in HK dollars; a session holding both
    keeps two totals and says why. Each total is coloured by ITS OWN sign — the
    first version took the row colour from the first currency and printed a
    +HK$400 in the loss colour beside a -US$20.
  · THE CONCLUSION IS WITHHELD BELOW TWELVE TRADES. The audit's bet (Asian hours
    are net negative, the NY open carries the account) is a thing to MEASURE, not
    to assert. Under twelve, the card prints the exact counts and totals and says
    the split is not yet a finding, with the threshold stated.
  · NOTHING PERSISTS, and jrtest checks that as a claim about the whole page (no
    localStorage / sessionStorage / cookie / indexedDB anywhere). What survives is
    an EXPORT: `var JOURNAL_IN = [...]`, the data in the shape the page would bake
    it, which round-trips every field including the note.
  · A row it cannot score is not scored: no exit means no P&L, never a silent
    zero that would flatter the session it landed in.
- THE SCOPE TRAP, FIFTH TIME, AND IT WAS LOUD FOR ONCE. The engine went inside
  live() while its form wiring runs before live() is reached; then, moved out, its
  `drawJournal()` first-paint call still sat in a wiring IIFE ABOVE the `var
  JOURNAL` declaration — hoisted, undefined, threw on .length. On this page a
  top-level throw does not cost one card: it aborts the rest of the script and
  takes every painter after it. Rule reinforced: state ahead of every consumer,
  exports beside the state, and the FIRST PAINT issued by the engine itself.
- NEW SUITES -> 54: jrtest.mjs, jr_guardtest.mjs. Eight mutants, all caught,
  including the multiplier dropped, a short scored as a long, contract count
  ignored, and HK dollars added to US.

## STATE as of 2026-08-11 ~07:30Z (audit item 13 part-SHIPPED — cadence + home screen)
- ADAPTIVE POLL CADENCE. A fixed 60s was wrong in both directions at once: ~900
  pointless requests across a weekend halt on a borrowed phone connection, and
  far too slow twenty minutes either side of the bell. Six tiers, chosen from the
  clock and strictly ordered: bell 20s < cash 45s < Europe/evening 60s < Asia
  120s < shut 15min, with a scheduled release inside twenty minutes outranking
  the hour (through nextEvent(), the same selector the countdown and summary use).
  The Asian tier is MEASURED, not assumed: this archive's own session weights put
  ~half the bars and under a tenth of the volume there.
  · SELF-RESCHEDULING TIMEOUT, not an interval. An interval fixes the cadence at
    the moment it was created — page-open, hours before the bell it must speed up
    for. The tier is re-asked after every request.
  · THE CADENCE IS PRINTED on the feed bar. A page that changes its own refresh
    rate silently makes "quiet by design" and "broken" render identically, and
    the second is the failure the guard banner exists to report.
  · A floor: no TRADING tier may be slower than the guard's six-minute lag line,
    so the page can never make its own quote look stale by choosing not to ask.
- ADD TO HOME SCREEN: apple-mobile-web-app-capable / status-bar-style / title,
  mobile-web-app-capable, theme-color, color-scheme. NO MANIFEST, deliberately —
  it would have to be a data: URL to stay inside one file and browsers differ on
  honouring that, so it would be a claim the page cannot check. polltest asserts
  the manifest stays absent.
- localStorage prefs (the rest of audit 13) NOT done and should not be: the page
  has a standing rule against browser storage. The journal (item 5) inherits that
  constraint — it needs an in-session card plus export, not persistence.
- NEW SUITES -> 52: polltest.mjs, poll_guardtest.mjs. Five of the six tiers
  cannot be reached by waiting, so every one is driven through a pinned instant.
  The event tier reports NOT REACHED today: the baked calendar holds no future
  event, which is a fact about the data rather than about the rule.

## STATE as of 2026-08-11 ~05:00Z (audit item 10 SHIPPED — the desktop deck)
- AUDIT ITEM 10 SHIPPED: above 1100px the cards flow into columns. Measured:
  28,290px on a phone -> 12,949px at 1440 (2 cols) -> 9,121px at 1920 (3 cols).
  · MULTI-COLUMN, NOT GRID. A grid puts cards in rows and a row is as tall as its
    tallest member; on a board running from a four-line note to a 300px volume
    profile that leaves gaps the size of the cards. Columns pack continuously.
    The cost is column-major reading order, which on a screen wide enough to show
    both columns at once is not a cost.
  · New `.deck` wrapper holds the content cards; the chrome (masthead, rail, feed
    bar, health banner, countdown, summary bar, footer) stays full width.
  · NOTHING BELOW 1100px CHANGED, and desktest checks the 430px column FIRST and
    treats any change to it as THE failure — every geometry suite runs at 430px,
    so a leaked rule would be measured by all of them, but only after shipping.
- A PRE-EXISTING PHONE DEFECT, found by desktest on its first run: `.tap-strip`
  is a flex row of twelve day cells with `flex:1` and the default
  `min-width:auto`, so the cells refused to shrink below their own word width and
  ran 16px past a card that is `overflow:hidden`. A phone reader was SILENTLY
  LOSING the right-hand end — the most recent days — on the card whose entire
  subject is which days the feed froze. Now wraps (`flex:1 1 58px; min-width:0`).
- NEW SUITES -> 50: desktest.mjs, desk_guardtest.mjs. Mutant C (break-inside
  dropped) is caught by a check on the DECLARED value, because its effect is
  currently masked: every deck child sets overflow:hidden, which makes it a block
  formatting context and already monolithic in multicol. The doubling ends
  silently the first time a card is written without it.
- THE TOKEN FAMILY EARNED ITS KEEP ON THE NEXT REFRESH. The ES shelf-top pool
  re-keyed 7,777.08 -> 7,785.70 (3.45 bins) absorbing the Asian session: 31 turns
  -> 97, still Asian-led at 49. Beyond one bin, so the tokens REFUSED and the
  build went red rather than printing a ghost. The resolver now names the nearest
  pool, its distance in bins and its turn count, so re-anchoring is a one-line
  edit instead of an investigation. Also: a dangling token no longer double-
  reports (its anchor price was being audited as a quoted level, producing a
  second, misleading "POOL but only BIN"), and the generic unresolved-token
  backstop now fires only for tokens no resolver claimed.

## STATE as of 2026-08-11 ~02:00Z (audit item 8 SHIPPED — the six-line summary)
- AUDIT ITEM 8 SHIPPED: six lines at the top, above everything that needs
  scrolling. Session / Risk / Levels / Plan / Feed / Next.
  · THE ONE RULE: it computes NOTHING. Each line is PUBLISHED BY THE CARD THAT
    OWNS IT, from the card's own rendered values, as it finishes painting. The
    risk figure is literally $("toneFig").textContent read back. The bar cannot
    disagree with the board because the string it shows is the string the card
    wrote. The two lines with no card — the session clock and the next catalyst —
    call clockAt() and nextEvent(), the same functions their counterparts call.
  · nextEvent() EXTRACTED so the hero countdown and the summary select from one
    list by one rule. They were two loops, i.e. two chances to name a different
    event across a boundary minute.
  · A LINE WHOSE PUBLISHER DID NOT RUN SAYS SO. paintAll's caller swallows
    throws, so a dead painter takes its own card down silently six screens below.
    A dash at the top is the fastest possible notice. Strict instant equality:
    every publisher is handed paintAll's nowMs, so anything that does not match
    did not run.
- TWO REAL DEFECTS THE SUMMARY FOUND ON ITS FIRST RENDER:
  1. paintAll passed `atMs` to paintTone/paintTrend and `nowMs` to everything
     else. On a live poll atMs is undefined, so those two fell back to their own
     Date.now() and painted at a different instant from the rest of the board.
     Invisible on every frozen render, because there the two agree. Fixed.
  2. The plan line read "3 decided against" on a board with two no-trades and one
     setup the tape had invalidated — `dead` covered both. Now counted apart.
- RAIL IDS ARE NAME-DERIVED, NOT POSITIONAL. `node.id = "rail-" + i` meant
  inserting the summary bar renamed every card below it: bakedup's caption
  exemption was keyed to rail-11, the decision card became rail-12, and a build
  that had passed for a week refused itself over paragraphs that had always
  legitimately repeated. bakedup now scopes that exemption by `#decBody` — what
  the card IS rather than where it sits.
- NEW SUITES -> 48: sumtest.mjs, sum_guardtest.mjs. sum_guardtest found four
  holes in sumtest on its first run: a mutant that made the bar THROW rather than
  mis-render exited without naming any property; the hero-shares-nextEvent check
  was written as a skip when it should be a failure; and two mutants were
  mis-anchored.

## STATE as of 2026-08-10 ~23:30Z (audit item 9 SHIPPED — tap to reveal)
- AUDIT ITEM 9 SHIPPED: the 190 `title` attributes are reachable by thumb.
  A title is a HOVER affordance; on the device this board is read on it does not
  degrade, it is ABSENT. 190 sentences written, generated, baked, shipped and
  shown to nobody.
  · ONE DELEGATED LISTENER on document, capture phase, reading the attribute at
    tap time. That is the whole design: every card rebuilds its DOM on the poll,
    so per-element wiring would cover fewer and fewer elements as painters were
    added. An element painted one second ago is covered by construction.
  · The title is LEFT IN PLACE, not moved to data-*. Pointer users keep the
    native tooltip, screen readers keep the same string, and there is exactly one
    copy of the text — a second copy is a second thing to go stale.
  · IT DOES NOT STEAL A TAP. tipFor scans the chain for an owner BEFORE taking a
    title. 15 of the 190 sit on rail chips (<button>) and stay hover-only; that
    cost is STATED in the suite output rather than hidden.
  · Bubble: textContent (never innerHTML — nothing in a title is markup, and
    treating it as markup is an injection surface fed by a generator), clamped
    into the viewport on both axes, dismissed by a second tap / Escape / scroll /
    resize. Scroll dismisses rather than follows: the bubble is anchored to a rect
    taken at tap time and one that drifts points at the wrong thing.
  · 24px hit area via ::after on marks, which moves no ink — those marks are
    positioned by percentage against an axis and nudging one would make it claim
    a distance it does not have. (Also closes half of audit item 13.)
- NEW SUITES -> 46: tiptest.mjs, tip_guardtest.mjs. The guardtest earned its keep
  twice: mutant B proved the anti-steal check was VACUOUS (it tapped a ladder row
  that carried no title anywhere in its chain, so no bubble could ever appear),
  and behind that it exposed a real page gap — tipFor took the tapped node's title
  before scanning the chain, so a titled span inside a clickable row would have
  opened a bubble while the row expanded underneath it. Mutant G covers that case
  and is currently NOT REACHED (measured: zero titled nodes sit inside a clickable
  ancestor today), so it is reported as evidence of nothing rather than passing.
- TEST TRAP recorded: the page dismisses on scroll, and scrollIntoView on a mark
  inside a chart wrapper scrolls THE WRAPPER, not the window. A settle-loop
  watching window.scrollY declares the page still and is then interrupted
  mid-tap. Count scroll EVENTS on capture instead — the same set the page hears.

## STATE as of 2026-08-10 ~21:30Z (audit item 6 SHIPPED — roll + MHI expiry + the token family)
- AUDIT ITEM 6 SHIPPED: futures roll DETECTION and DISCLOSURE.
  · Detector `roll_break()` in liquidity2.py. THE TEST IS THE GAP, NOT THE STEP:
    this bar's OPEN against the previous bar's CLOSE. The first version measured
    close-to-close and flagged RTY 31 Jul 13:45Z — a real 14.6pt cash-open move
    at 7x the typical, which traded the whole way down inside itself on 7,782
    lots. A fast market has a LARGE range and a SMALL gap; a roll has a SMALL
    range and a LARGE gap. Elapsed-time test kept (>900s = weekend/halt/outage,
    already explained). Threshold 6.0x the contract's own typical 30-min move.
  · Emits `roll:[]` per symbol into LIQ, plus `after`/`of` — the near-side bar
    count. The archive is CUMULATIVE (`from` is the first bar ever written), so
    a break NEVER AGES OUT; the only honest number is what share of the profile
    is the contract you are trading now.
  · DISCLOSES, never back-adjusts. A large gap across a quiet bar is a contract
    change under one reading and a real event under another; subtracting would
    corrupt the second to tidy the first. rollpage.mjs asserts the POC is
    identical with and without the flag.
  · Painters: `rollEl()` (full banner, Session liquidity card, mounted AHEAD of
    the early return) and `rollChip()` (one line, ladder + both symbols on the
    levels card). Every chip quotes the BANNER'S OWN step, so two painters
    reading one field cannot silently disagree.
- MHI EXPIRY COUNTDOWN (audit §4.4): `mhiExpiryState()` + `mhiExpiry()` on the
  HK ladder. Reads 15 SESSIONS today. Weekdays counted in HKT and it says HK
  holidays are not in the page. States the basis's own AGE (5 days) and that it
  dies with the contract. CONTRACT.HSI gained `ltdMs`/`basisMs` EPOCHS — the
  arithmetic never parses its own display label, and toktest-style guard asserts
  epoch and label agree. NO DECAY MODEL: theory says a basis walks to zero
  linearly, but this board's own measurements (+29/-5/+22/+15/+16 over one week)
  refuse it, so the figure is dated, not extrapolated.
- THE POOL-ANCHORED TOKEN FAMILY — the 10 Aug refresh produced THIRTEEN
  contradicted claims and every one was the same defect: prose pinned to a pool
  COORDINATE the generator had since re-keyed (ES 7,775.94 -> 7,777.08, gaining
  four turns; RTY 3,048.96 -> 3,048.67). Hand-fixing thirteen numbers would have
  made the build green and re-armed the trap. So four new token classes, in both
  resolvers: `{{pool SYM P}}`, `{{turns SYM P}}`, `{{mix SYM P RTH|EU|EV|A}}`,
  `{{rank SYM P}}`.
  · THE PRICE IN A POOL TOKEN IS AN ANCHOR, NOT A CLAIM. Tolerance is ONE BIN
    WIDTH — inside a bin the profile cannot tell two prices apart, so a pool that
    drifted less than a bin is the same object by the only measure this page has.
  · TWO pools inside a bin is a HARD FAIL (ambiguous). An ambiguous anchor is
    worse than a missing one: it resolves silently and can resolve differently
    tomorrow with no figure ever looking wrong.
  · `{{rank}}` reports ties as "joint second" rather than breaking them. Rank
    claims were five of the thirty-seven failures on 5 Aug.
  · `{{mix}}` keeps the PHRASING with the author and generates only the number:
    "{{mix ES 7777.08 A}} of them Asian". Zero renders "none", not blank.
- NEW SUITES -> 44 (were 39): rolltest.py, roll_guardtest.py, rollpage.mjs,
  toktest.mjs, tok_guardtest.mjs. Two of them found real holes in themselves:
  roll_guardtest mutant C proved rolltest's threshold checks were reading the
  constant they were testing (fixed with ABSOLUTE anchors: an ordinary 1.5x
  session gap must stay quiet, and 4.0 <= ROLL_STEP_X <= 6.0); tok_guardtest
  mutant B proved every toktest probe used the pool's EXACT current key, so a
  silent return to exact matching was invisible — fixed with DRIFTED anchors at
  0.4 of a bin (must resolve) and 1.8 bins (must be refused).
- toktest closes a gap nothing had ever covered: prose_levels.py and scenTok()
  are two implementations of one grammar and nothing compared them. A divergence
  is invisible from both sides — the gate reports a clean page about sentences
  that were never printed. It drives both with the same tokens through a
  `WAFT_TOKPROBE` env door and compares the WORDS.

## WHERE THE OLD STATE BLOCKS WENT
Nineteen superseded STATE blocks — every finished piece of work back to 7 August —
now live in `AUTOPILOT-history.md`. They were 37% of this file and were re-read on
every wakeup to answer questions that stategen.py answers from the workspace. Go
there when you need why a past decision was made; you do not need it to work.

## QUEUE (work top-down; move items to STATE when done)
0. DONE 7 Aug ~10:45Z (was W2): A1 phase 1 SHIPPED — {{age SYM PRICE}} tokens.
   scenTok/scenWordNum in painter (before scenSplit), applied to tag/rows/
   invalid AND scenState (both sides resolve identically); exported on __wf.
   prose_levels.resolve_tokens mirrors it, HARD-FAILS on missing referent and
   on any leftover {{; three resolver selftest cases added. Six age sites
   converted (3049.78 x3, 7820.25, 2987.21 x2). scentest rawTok DOM assertion;
   scen_guardtest mutant S (+ M/R/S anchors updated — my edits moved them,
   once() caught it). scen_guardtest 20/20. Battery suites14.out RUNNING at
   handoff — CHECK IT FIRST next wakeup. NOTE: suites13 died mid-run (container
   blip?), unexplained — if suites14 also dies mid-run, investigate before
   trusting any green.
   REVERT PATH if found red: src.bak-tokens + prose_levels.py.bak-tokens.
   W3 (phase 2) now covers: {{share SYM PRICE}}, {{above SYM PRICE}},
   {{px SYM}} classes + convert remaining drift sites + prove with double
   refresh. Ages were ~6 of ~15 treadmill repairs; shares/spot are the rest.
0b. DONE 7 Aug ~12:00Z: TRADE PLAN CARD SHIPPED (Walton asked where it was —
   it had never been built as itself). Bottom of page, var PLAN structured
   block (close30 discipline as data), drawPlan painter, status chips derive
   TRADED-vs-held from day range with the touch-not-close caveat enforced.
   plantest (11 checks) + plan_guardtest (A reachability-gated, B, C, control)
   registered — 37 suites, all green (suites15.out). Monday trigger updated:
   FIRST JOBS now include rewriting PLAN each brief. Roadmap v2 written
   (/tmp/dash/waft-roadmap-v2.md) after a full census scan (18 cards, 7,514
   vis words, 32 screens): new items N1 window-aware chips (needs in-page
   bars), N2 plan-in-brief-cycle assertion, N3 PLAN into prose_levels scope,
   N4 R-multiples, N5 sentiment card trim (445 words). C1 order re-ranked:
   Scorecard 737 → Decision 736 → Where-stood 617 → Session-liq 614.
0c. DONE 7 Aug ~12:50Z: A1 PHASE 2 SHIPPED — roadmap v2 confirmed as THE goal
   (Walton re-uploaded it). Five token classes now live: {{age}} {{share}}
   {{above}} {{range}}/{{rangebin}} {{px}}, painter + prose_levels mirrored,
   26 sites converted incl. the stale B/tag spot the guard never checked.
   Selftest: share/above/range/px good + missing-bin cases. THE PROOF LANDED:
   refresh #1 AND #2 both built with ZERO contradicted claims and zero hand
   repairs — the treadmill is dead for tokenized classes. Residual hand
   classes (phase 3 candidates): distances-with-spot pairs, d1 lows,
   turn counts/session mixes, superlatives, narrative state ("back at the
   trigger exactly"). kztest fixed en route: NQ/YM lanes' first battery hit a
   tick landing on an exact half-hundredth (34.375→printed 34.38, 0.005 off
   the strict tolerance) — suite now compares at the painter's PRINTED
   precision. 37/37 green (suites17.out).
1. DONE 7 Aug ~13:50Z [was W1]: post-NFP session complete. Reaction scored +
   verified (see STATE); 46-edit drift repair across A/B/C tags/rows/invalids,
   both tiles, HSI rows, PLAN card, CHAIN deixis; probs re-weighed with dated
   reasons; cluster-dedupe shipped in the landed-rows painter after bakedup
   flagged the x3 lead. Build green 11 gates + bakedup. suites18 launched.
   REVERT PATH: waft-dashboard.src.html.bak-w1repair (pre-repair source).
2. DONE 7 Aug ~21:40Z [was W2]: cash-close verdict recorded board-wide +
   N1 window-aware chips + N3 PLAN in guard scope (details in STATE).
   REVERT PATHS: src.bak-w2close (pre-verdict source), ladgen.py.bak-hsiclose,
   prose_levels.py.bak-n3.
3. DONE 8 Aug ~09:10Z [was W3]: C1/N5 shipped for Scorecard, Decision,
   Where-stood, Sentiment (details in STATE). Session liquidity DEFERRED —
   its candidate promotion is the nearest-untouched-level pair ("First in
   line — above/below"), currently buried in the bottom prose; it must be
   painter-composed from the same data the strip reads, never a second copy.
4. DONE 8 Aug ~17:15Z [was W4]: N2 + N4 + Session-liquidity promotion
   (details in STATE).
5. DONE 10 Aug ~03:00Z: floors check + the derived-routing fix it exposed.
6. DONE 10 Aug ~03:00Z: housekeeping sweep (nothing needed deleting).
7. DONE 10 Aug ~05:30Z: both calls resolved, no-trade state shipped, floor
   audit extended (details in STATE). PLAN did NOT need rewriting — N2 stays
   green because resolving an entry adds no new date; it is a NEW call that
   would trip it. Superseded text follows.
7x. [was next] Resolve the two pending calls and rewrite
   PLAN in the same pass: (a) 3 Aug term-premium, REGIME branch — needs
   Friday's 30y close vs 5.15% AND DXY vs 100 (entering Friday 5.22% / 99.95);
   DIAGNOSIS branch already hand-read (ISM Prices 71.1 vs >=73 threshold, did
   NOT break by 1.9, and the threshold WAS the prior). (b) Fri 7 Aug RTY
   short — the 13:00Z close was 3,032.40, above the 3,015.00 invalidation, so
   it INVALIDATED without ever triggering (trigger was a close below
   3,004.90); confirm from bars and record. Judged at resolution, never
   re-judged. Then var PLAN must be rewritten or plantest N2 goes red.
8. [NEXT] External audit items in its own priority order — 1 (DST+TZ, dated
   1 Nov + London move), 2 (live-print input), 4 (position sizing), 6 (futures
   roll, dated ~10 Sep and MHI 28 Aug). See STATE for the full ranked list.
9. DONE 10 Aug ~21:00Z: A1 phase 3 SHIPPED — and it went further than the
   item asked, because the diagnosis was wrong. The class was never "turn
   counts": it was PRICE COORDINATES. A pool re-keys as its cluster drifts, so
   {{turns RTY 3048.96}} would have dangled on exactly the refresh {{age RTY
   3048.96}} did. Shipped `{{pool}}` `{{turns}}` `{{mix}}` `{{rank}}` with the
   price as an ANCHOR (one bin width, ambiguity a hard fail) and the prose no
   longer carrying the coordinate at all. See STATE. Remaining treadmill
   classes now: profile-share phrasings not yet on {{share}}/{{range}}, and
   free-text claims about consumption ("no longer listed") that no token can
   check — those need a different mechanism, not another token.
8x. SUPERSEDED — item 8 above says "[NEXT] External audit items" and the audit
   list has been closed since 11 Aug. `stategen.py` derives it (13 of 13, each
   present and covered by a registered suite) and has been right about it longer
   than this queue has. Left visible rather than deleted, because a queue that
   quietly drops an item reads the same as one that finished it. THE RULE: when
   this queue and stategen disagree, stategen is right — it measured, this
   remembered.
10. DONE 13 Aug: the anchor gauge. `anchors.py` reports how much of the
   resolver's one-bin tolerance each prose anchor has spent, at the moment the
   pools move (tail of refresh.sh) rather than at the moment a bake breaks.
   It imports prose_levels rather than re-deriving the rule, `--selftest` proves
   the gauge and the gate read one scale, and `anchors_guardtest.py` seeds a
   divergence in both directions. First reading: 8 pool anchors, worst at 40%.
11. DONE 13 Aug — SHIPPED, and it found a false claim on its first run (see the
   section above). Original entry follows.
11x. THE ABSENCE CLAIMS — the last named treadmill class, and the one item
   9 said "no token can check". It can. The prose is full of assertions that
   something is GONE: "3,030.44 is no longer listed", "that pool has left the map
   without being traded through", "7,766.49 ends the week carrying no pool at
   all". Every one is checkable against exactly the data the pool anchors use —
   assert NOTHING within one bin — and every one silently becomes false the
   moment the clustering re-forms there. It has already happened twice in three
   sessions on RTY 3038.31, which the prose itself describes.
   SHAPE: `{{gone SYM PRICE}}`, rendering the formatted price so the sentence
   reads naturally and the figure is generated rather than typed, and HARD
   FAILING when a pool has come back. Opt-in, so it cannot become the noisy
   natural-language detector that L4 demonstrates is unshippable.
   Both resolvers (prose_levels + scenTok), a toktest cross-check, a
   tok_guardtest mutant per side. Then convert the existing absence claims.
12. [Backlog] Audit for more floor-beside-a-typed-list defects (see STATE).
   Sentiment-history persistence past 6 days; scorecard build-log fold;
   foldIntros losslessness gate; A2 range-claim checker; TAP_DP for MHI.
FULL ROADMAP: /tmp/dash/waft-roadmap.md (also delivered to Walton 7 Aug) — the
A1–E4 item list with goals and risks. Queue above = near-term slice of it.
Backlog (after): sentiment-history persistence beyond 6 days (archive grows now
that squash is off); scorecard build-log fold; foldIntros losslessness gate;
prose_levels range-claim checker ("N bins out of M"); TAP_DP for MHI dp.

## PYTHON ROUNDS 4.5 TO FOUR AND THE PAGE ROUNDS IT TO FIVE (12 Aug)
- toktest caught the two resolvers disagreeing: `{{age ES ...}}` resolved to
  "four" in prose_levels and "five" on the page. Not a bug in either half.
  Python's `round()` is BANKER'S ROUNDING (round-half-to-even, so round(4.5)==4)
  and JavaScript's `Math.round` is half-up (5). They agree on every age except one
  landing exactly on a half hour — and an ES pool sat at `age_h: 4.5`.
- The consequence is the exact failure toktest was built for: the gate verifying
  "four hours" while the reader saw "five". A one-hour lie about how stale a level
  is, invisible from both sides because neither was wrong on its own terms.
- THE PAGE IS WHAT A READER SEES, so the page's rule wins. All three sites in
  prose_levels now use `math.floor(x + 0.5)` — the resolver AND the self-test's
  own prose writer, because a generator that rounds differently from the checker
  can manufacture prose its own checker disagrees with.
- A probe set can only catch this on days a pool happens to sit on a .5, so
  toktest now asserts the RULE in source — no `int(round(` in prose_levels — which
  is reachable every run.
- kz_guardtest case P (the label-collision mutant, added hours earlier) went
  straight through: the refresh moved the clusters apart, so removing the fix
  changed nothing. Given a MEASURED precondition that asks the rendered page
  whether any lane at any pinned clock still has two marks inside the painter's
  own 9% threshold. `unless` now accepts an async handler returning its own reason,
  because this precondition needs a browser and cannot answer from the block alone.

## THE BOARD NOW AUDITS ITSELF (12 Aug) — audit item 14, unasked for
- XCHK: a dated independent cross-check, at the top of the page beside the
  data-health guard. Its standard was already the board's own — two sources
  agreeing, the rule that came out of 31 July when the tiles published a close
  that agreed with nothing — and every card had been built to that bar while the
  BOARD had not: every figure comes from one relay.
- FIRST RUN: SPX -0.3315% vs SPY -0.3195% (+1.2bp), RUT +0.3084% vs IWM +0.3367%
  (+2.8bp), NDX -0.3338% vs QQQ -0.3357% (-0.2bp), all on the Tue 11 Aug cash
  close against Alpha Vantage. Worst gap 2.8bp, inside what ETF tracking explains.
- FOUR STATES, THREE OF THEM UNREACHABLE BY WAITING, which is the whole reason the
  row is worth having: agrees (quiet, and the only one anybody ever sees), the two
  feeds disagree, the check has aged out, and there is no check at all. Driven
  through `__wf.seedXchk`, which writes, repaints and RETURNS the state.
- IT REFUSES TO OVERCLAIM, and the suite asserts each refusal is ON THE PAGE:
  direction and magnitude, not price, because ETF proxies track with slippage; it
  says nothing about the FUTURES the levels are drawn on; HSI and VIX are named as
  UNCHECKED rather than omitted (both are cnbc-sourced and cnbc is unreachable
  here); and it admits it does not run itself, because no toolchain path reaches an
  independent vendor without a key and keys do not enter this container.
- xchktest + xchk_guardtest -> 59 suites. Seven seeded defects, all caught.

## THE LADDER GUARD WAS DIVIDING BY A GUESS (12 Aug)
- The build stopped on "HSI: nearest level below is 6.67 moves away, limit 6x".
  It was not the market. ladtest read `LIQ[sym].t30` and, finding none for HSI,
  fell straight to a day-range estimate of 17.51 — while `MOVES.HSI` carries a
  MEASURED t30 of 48.61 from 275 real HKEX bars, put there by the item-12 futures
  work, and the page's own `pace()` falls back to exactly that. By the page's
  arithmetic the level is 2.40 moves away. The guard failed the build on a number
  the page never quotes.
- The guard's comment asserted "guard and page then quote the reader the same
  divisor". It was true when written and stopped being true when a data source
  appeared that nobody taught it about — the floor-beside-a-typed-list family
  again, and invisible because the estimate produced a PLAUSIBLE number rather
  than an error.
- Fixed by mirroring pace()'s chain exactly: measured profile, then measured
  MOVES, then the estimate. THE LIMIT IS UNTOUCHED — what changed is the divisor.
  A new check names any symbol that falls back to the estimate while a measurement
  exists, printing both figures, so the two can never silently diverge again.

## THE SECOND SOURCE IS NOT YAHOO (12 Aug) — a correction before any work was built on it
- I told Walton the Yahoo Finance MCP would be a genuine cross-check on the relay.
  IT WOULD NOT BE. `fetcher.py` imports the Webull data client, which is what the
  file is about — but the published payload tells the truth: `latest/free.json`
  stamps `src:"yahoo"` on ES, RTY, NQ, YM, SPX, RUT, NDX, DXY, GOLD, CRUDE and
  US10Y. Only HSI and VIX carry `src:"cnbc"`. Comparing the board against Yahoo
  would have been the same source wearing a different hat — agreement that proves
  nothing while looking exactly like verification, which is worse than no check.
  CHECK THE `src` FIELD BEFORE CALLING ANYTHING INDEPENDENT.
- What IS independent, from the tools now connected: Alpha Vantage, Equibles, and
  IBKR's read-only snapshot/history (already used for the MHI futures work). CNBC
  is blocked for WebFetch, so the two cnbc-sourced figures cannot be re-fetched here.
- FIRST CROSS-CHECK RUN, Alpha Vantage against the relay, Tuesday 11 Aug close:
  · SPY -0.3195% against the relay's SPX -0.331% — about one basis point apart,
    inside normal ETF tracking.
  · IWM +0.3367% against the relay's RUT +0.3084% — 2.8bp apart, same sign.
  · And the thing worth having: SPY DOWN while IWM UP on the same session, from a
    vendor with no connection to the relay. That independently corroborates the
    two-session inversion now written into the SCENARIOS prose — Monday RTY down
    while ES held, Tuesday exactly reversed.
  · STATED HONESTLY: this compares ETF PROXIES against index and futures figures,
    so it corroborates DIRECTION AND ROUGH MAGNITUDE, not price. A tracking gap of
    a few basis points is expected and is not evidence of a feed fault either way.

## WHAT THE FRESHER DATA BROKE, AND WHY THAT WAS THE POINT (12 Aug)
- Four suites went red on the refreshed archive and every one was a REAL finding
  rather than a flake. None of them could have been found without new data.
- KZTEST — A GENUINE RENDERING DEFECT ON THE LIVE BOARD. At 16:10Z both contracts
  had their nearest level each side within a few tenths of a typical move, so both
  diamonds landed on the middle of the track and the two × labels were drawn on top
  of each other: ES "0.1×" over "0.3×", RTY the same. The strip still looked
  confident; the only thing wrong with it was that neither number could be read.
  Fixed by anchoring the two labels OUTWARD when they would collide — the below one
  ends at its diamond, the above one starts at it, so each still touches its own
  mark (the property that stops a label claiming a distance its level does not have)
  and the boxes separate by construction. Threshold is the label's own width as a
  share of the track, ~9%. New case P in kz_guardtest seeds its removal.
- Cases G and H in kz_guardtest then failed as "anchor gone", because the fix moved
  the code they edit. That is the guardtest working: it refuses to report a mutant
  as caught when it was never applied. Both re-anchored to the new shape.
- TOK_GUARDTEST mutant D passed-anyway: the {{rank}} TIE branch stopped being
  exercised without anything changing in it. The refresh gave both symbols' top and
  mid pools distinct scores, so every probe landed on a unique value and deleting
  "joint " was a no-op. The tied pools were still on the board — the probe set was
  not pointed at them. toktest now SEEKS a tie, exactly as it already sought the
  zero case. Third time this same shape has bitten: a probe set that stops covering
  a branch because the data moved, while the suite goes on passing.
- TAP_GUARDTEST mutant B failed as "anchor gone" — it seeded its defect by rewriting
  a literal out of the generated TAP block ('"lag":6,"pt":45,'), which stopped
  existing the moment the block was regenerated. Coordinate-pinning inside a
  guardtest, the same defect the prose tokens exist to kill. Now seeded structurally
  by REVERSING the sort that produces the ordering, so it depends on the page's
  logic rather than on any day's numbers.

## THE ARCHIVE WAS TWO DAYS BEHIND, AND WHY THAT WAS INVISIBLE (12 Aug)
- The local clone stopped at 10 Aug 11:57Z while the relay kept publishing. A plain
  fetch did not move it: the relay had REWRITTEN its history at that exact point,
  so local and origin had diverged (4,006 local commits, 3,457 origin, sharing a
  base). Verified origin was a strict SUPERSET before taking it — identical row
  counts for every older day, 1,162 against 621 for 10 Aug — tagged the local state
  `archive-local-20260812` first, confirmed both protected tags survived, then reset.
- WHAT WAS ACTUALLY STALE, stated precisely because I overstated it to Walton at
  first: the page fetches quotes.json, free.json, free-bars.json and calendar.json
  LIVE from the repo, so prices, bars and the calendar were never stale on his
  phone. What ages between rebuilds is the BAKED half — volume profile, stop pools,
  killzone level history, seasonality medians, ladder levels, and the prose.
- stategen said "the feed may be down" when the truth was "your clone has not
  fetched". Same bar age, opposite actions — go fix the droplet, or type git fetch.
  It now reads `HEAD..origin/main` off the on-disk ref (no network) and names which
  one it is; a clone behind origin is a HARD problem because every generated block
  was measured on data that has since moved. Cases N and O in state_guardtest.
- TWO DAYS OF BARS MOVED THE STRUCTURE A LOT. ES 7,755.66 went 50 turns -> 139 (and
  re-keyed to 7,753.74, inside one bin, so its token resolved). RTY 3,048.67 left
  the map entirely WITHOUT BEING TRADED THROUGH — the two-session high was 3,045.80,
  so price never reached it; the cluster re-formed lower. 3,033.69 moved 2.83 bins.
- THE TOKEN FAMILY EARNED ITSELF HERE. It refused to re-anchor sentences onto a pool
  five bins away and named the nearest candidate with its turn count instead, so the
  decision stayed a judgement. Six passages were REWRITTEN rather than renumbered,
  because they described structures that had stopped existing. The trade-plan branch
  whose second leg named the dissolved pool is left AS WRITTEN and marked void by
  structure change — quietly re-pointing a trigger at a nearer price is how a
  condition stops meaning what it was agreed to mean.
- The two sessions inverted: Mon RTY -10.90 while ES held +3.75; Tue ES -15.50 while
  RTY took +14.50 back. Both directions dealt between 3,016.00 and 3,045.80.
- AS_OF now says what was and was NOT re-curated: structure prose re-cut against
  Mon/Tue, the market argument still Friday's and not re-argued.

## THE AUDIT LIST IS NOW DERIVED TOO (11 Aug)
- THE FAILURE THAT CAUSED IT: on 11 August I reported six audit items as
  "remaining" that had shipped hours earlier, and in the next breath called item 7
  absent because its delivery is a droplet script rather than page code. Both
  readings came out of memory. Neither survived thirty seconds of looking at the
  workspace. It happened ONE TURN after building stategen.py to prevent exactly
  that class of error — the tool tracked build and battery state and said nothing
  about the audit, so the one question being asked was the one it could not answer.
- `audit.spec.json` names, per item, the EVIDENCE that would exist if it were
  shipped: a marker in the page, or a file plus a self-test for the one item that
  lives on the droplet. stategen looks for that evidence instead of asking me.
- THE EVIDENCE IS TWO-PART. `page` proves the feature exists; `suites` proves
  somebody can tell when it breaks. Built-and-unguarded is a THIRD state, reported
  as itself rather than rounded into "done" — and it is advisory, not blocking,
  because it must never stop a battery.
- `expect` is what the ledger believes. Detection disagreeing with it is a HARD
  failure: an item recorded as shipped whose evidence has vanished is either a
  regression or a rename, and both should arrive now rather than the next time
  someone asks what is left.
- Four new cases in state_guardtest (J, K2, L, M). Two of my own markers were
  wrong when first written — item 10 said `min-width:1100px` against a source that
  says `@media (min-width: 1100px)`, item 13 said `pollEvery` against `POLL_TIERS`
  — and the ledger reported both as missing, which is the behaviour it exists for.
- STATUS, MEASURED: **13 of 13 audit items shipped**, every one covered by a
  registered suite, item 7 self-testing clean.

## THE MEMORY IS NOW HALF-DERIVED (11 Aug)
- `stategen.py` writes the AUTOSTATE block at the top of this file. Everything in
  it is MEASURED off the workspace when it runs; nothing is recalled. The
  narrative STATE blocks stay hand-written — "why the roll detector tests the gap
  rather than the step" is a judgement and cannot be derived from a file listing.
  If the two ever disagree, THE GENERATED BLOCK IS RIGHT.
- It exists for one question, asked first after every compaction and previously
  unanswerable without archaeology: IS THE GREEN I REMEMBER ABOUT THE CODE THAT
  IS HERE NOW? Three timestamps answer it — source, build, last battery — and any
  inversion means a remembered "all suites passed" is about a file that has since
  been edited.
- Wired into the two moments the answer changes: the end of `suites.sh` (AFTER
  the summary line — called before it, it read this run's own half-written log
  and correctly reported the battery as killed, which is a reporter crying wolf
  about itself) and the end of `refresh.sh`. Its exit code is discarded in both:
  a stale toolchain must not turn a green battery red.
- It also caught two live defects on its first run. `waft-dashboard.src.html` was
  never in the packed toolchain, while RESTORE.md told a restorer to copy it out
  after extracting — every restore had silently depended on the source arriving
  as a separate file. And `ladtest`/`railtest`/`scoretest` looked unregistered
  until the gate list was read out of `build.mjs` rather than typed into
  stategen — the floor-beside-a-typed-list trap, aimed at the new tool this time.
- `state_guardtest.py` stages nine broken workspaces and requires each to be
  NAMED. Two of its cases failed first time by nudging a clock 1.1s against a 2s
  tolerance band — the reporter was behaving exactly as specified and the test
  was wrong. -> 57 suites.

## ONE NAME FOR THE TOOLCHAIN (11 Aug)
- `pack.sh` emits `/tmp/waft-toolchain.tgz` and nothing else. Dated names
  (`waft-toolchain-20260810c.tgz` and five siblings) were invented to tell
  consecutive deliveries apart in chat; in a repository a new name does not
  overwrite, it sits beside. That already happened: the repo holds
  `waft-toolchain.tgz` from 5 Aug AND `waft-toolchain.tar.gz` from 10 Aug, and
  RESTORE.md points at the older one.
- BOTH COPIES IN THE REPO ARE DOUBLE-GZIPPED and `tar xzf` refuses both — the
  same failure RESTORE.md already documents from 3 August. Archives written here
  are clean single-gzip, so a layer is added somewhere in the upload path.
  RESTORE.md now PEELS gzip layers until a tar appears rather than trusting
  either end, and pack.sh refuses to finish unless it can extract what it just
  wrote and match the source inside it byte-for-byte against the one on disk.

## MEASURED AND REJECTED (do not retry blind)
- BATTERY PARALLELISM, 11 Aug. Microbenchmark said yes (two browser suites: 15s
  serial -> 9s concurrent, because most of a suite's clock is chromium starting
  and fixed waitForTimeout delays, which are idle). Full battery said no: ~30
  minutes against ~22, identical verdicts (56 passed both ways). Two reasons —
  the suites that MUST run alone (anything measuring layout, scroll settling or
  animation timing, where contention turns a measurement into a flake) are also
  the longest ones (kz_guardtest 160s, desk_guardtest 129s, seasgeo_guardtest
  125s), so the time is concentrated exactly where parallelism is not allowed;
  and on two cores each solo suite has to drain the background jobs first, and
  those barriers cost more than the overlap wins. It also cost per-suite progress
  output, which is what made the log pollable and diffable. Reverted; the reasoning
  is written into suites.sh so it is not retried from scratch. NOT ruled out:
  parallelising only the static-geometry suites at pinned clocks while keeping the
  scroll-settling ones solo — but that needs several repeat batteries to prove it
  does not flake, and an intermittent red here costs more than the time saved.

## THE LEDGER WAS EMPTY, AND THAT IS WHY THE RULE COULD NOT BE JUDGED (13 Aug)
- Walton left two things to me: whether Tuesday 11 Aug satisfies "the long end is
  UNCHANGED" in the 3 Aug defeat condition, and whether to rewrite the thesis.
  They turned out to be one thing.
- **THERE IS NO OPEN CALL ON THE BOARD.** 44 hit, 4 miss, 4 partial, 1 no-trade,
  nothing pending. `biCall` returns rows only for `cat:"market" && r:"pending"`, so
  the entire invalidation ledger renders nothing — and bitest section 7 had already
  noticed, reporting NOT REACHED because there was no break line to read. A ledger
  visible only while a trade is on is a ledger nobody sees between trades, which is
  most of the time.
- Worse: the DEFEAT condition was attached to the **6 Aug RTY short, which is
  resolved**. It was orphaned on a dead call. That is why it could not be checked —
  not only the schema gap the board had recorded, but no live subject to check.
- **CHAIN NODES NOW CARRY THEIR OWN DEFEAT CONDITIONS**, evaluated every poll in
  the ledger's own grammar. A standing rule is a claim whether or not money is on
  it. This also keeps the DOM wiring reachable between trades.
- THE SCHEMA GAP IS CLOSED. The 3 Aug entry named it — "there is no shape in the
  ledger for a spread condition, which is a schema gap rather than a feed gap and
  is therefore fixable here rather than upstream". Two leg sources:
  * `chgspread` — two instruments' session returns against each other, in bp, off
    `chg_pct` rather than differencing prices, because only one of those has to
    guess what the previous close was.
  * `curvechg` — one tenor's day as a MAGNITUDE, taken from `YCD.mv`, which the
    curve generator already computes from paired official closes. Not differenced
    here: a second implementation of one subtraction is the ladder-guard lesson.
  * Plus `not_above`/`not_below`, because the threshold is a measured magnitude and
    writing "2bp or less" as `below 2.001` reads as a typo six weeks later.
- **THE SESSION-AGREEMENT CHECK IS THE PART THAT MATTERS.** The two feeds run on
  different clocks — cash indices freeze at the NY close and carry that session's
  `chg_pct` for thirteen hours; treasury.gov publishes on its own schedule. Paired
  blind, the condition compares one index's Wednesday against the curve's Tuesday:
  each figure correct, the sentence between them false. Legs that name a session
  must name the same one, or the condition WAITS and says which two days it was
  being asked to compare.
- `biCurve(d)` reads the curve off the PAYLOAD first and YCD second, so bitest can
  drive every branch without mutating page state. A leg that could only read a
  global would have its branches exercised by whatever the curve says today — and
  four of this ledger's six states are already unreachable on a live tape.
- THE THRESHOLD IS DERIVED, NOT CHOSEN. Ten completed sessions in the relay (30 Jul
  – 12 Aug, a thin sample, stated as one): |Δ10y| sorts 0,0,2,2,4,5,6,7,7,8 and
  |Δ30y| 0,1,1,3,4,5,5,6,7. The bottom quartile is 2bp at both the 25th and 33rd
  percentile. Four of ten sessions qualify, so the condition CAN fire — the old one
  could not, which was the whole complaint.
- **AND IT IS SENSITIVE, WHICH IS SAID ON THE BOARD.** At 1bp only two sessions
  qualify and Tuesday is not one of them; at 2bp it is. 1bp is roughly the tenth
  percentile, so it would have to be argued for rather than derived.
- THE VERDICT: under the adopted (magnitude) reading the DEFEAT **fires on 11 Aug**
  — Δ10y 2bp, Δ30y 1bp, RUT over NDX +66bp. The rule that small caps cannot lead
  while the long end is under pressure has been beaten once. The competing
  (direction: "did not EASE") reading is stated on the board rather than buried;
  under it Tuesday is excluded and the node survives. Magnitude was adopted because
  the node's own examples of "clean relief days" were 5–6bp moves, so 2bp is inside
  the noise the rule was never about — and the direction reading admits one session
  in ten, putting the condition straight back where it started.
- ONE DEFEAT IS NOT A RETIREMENT, and the node says so: one session, recorded with
  its terms, on a rule handed relief twice that refused to lead both times.
- 13 new bitest cases + 6 wiring checks; 59 checks, 0 failed. Tuesday's data is a
  TEST CASE now, so the firing is reproducible rather than remembered.
- STILL WALTON'S: whether to open a new call. Writing one is a market judgement in
  his voice, not mine. The machinery is ready for it.

## THE BOARD WAS SAYING A LEVEL WAS GONE WHILE LISTING IT (13 Aug)
- `{{gone SYM PRICE}}` shipped, and it found a live contradiction on its first
  run — the same way `lessons.py` did. **RTY 3,030.44**: the prose said, in three
  separate places, "is still absent … nothing has re-formed there", "is not listed
  any more … with nothing left behind", "is no longer listed". A **fifty-turn
  pool** keys at 3,030.34, a tenth of a bin away. The same paragraph that called
  it gone was already quoting `{{pool RTY 3030.34}}` three sentences earlier as
  one of the three live clusters. A reader would have hit both inside one screen.
- WHY NOTHING CAUGHT IT, and this is the part worth keeping: every other token
  asserts a PRESENCE and fails when its structure moves. An absence claim matches
  no anchor by construction, so it trips no check — the sentence stays green
  precisely because the thing it names is not there. The whole token family had a
  hole shaped exactly like its own design.
- The three sentences were REWRITTEN, not re-pointed. Emptied-and-rebuilt is a
  different fact from emptied-and-left-empty, and the corrections say so and say
  the row had asserted the second while listing the first.
- The claims that DO hold are now tokenized and checked: ES 7,766.49 (three
  places) and RTY 3,038.31. Three outcomes: nothing within a bin renders the
  price; a pool within a bin is a HARD FAIL naming where it came back; no pool map
  at all is also a hard fail, because an absence nobody can verify is the sentence
  the token exists to stop shipping.
- OPT-IN ON PURPOSE. A detector that hunted absence claims in free text would fire
  on every "no" in the paragraph — L4 in the registry is the standing evidence for
  what happens next. The author writes the token where the claim is.
- Both resolvers, cross-checked by toktest (an absence with nothing near it must
  render the same words on both sides; one pointed at a live pool must be refused
  by both), and tok_guardtest mutants G and H break one side each.
- TWO THINGS LEARNED WHILE BUILDING IT:
  * The absence probe had to be DRIFTED. Written on a pool's exact key it is
    refused by any tolerance at all, including one that has silently shrunk to
    nothing — and a real sentence's anchor is the coordinate the level had when it
    was written, not today's key.
  * Mutant H first DELETED the lookup, which tripped prose_levels' own selftest,
    so python died before toktest could compare and the guard reported a harness
    failure. A mutant caught by the wrong thing proves nothing about the check it
    was written for. Re-seeded as a shrunk tolerance.
- `band_width(sym)` extracted: the tolerance rule was written out twice the moment
  a second token class needed it. toktest now asserts it is defined once and that
  both classes call it — but NOT by counting BAND lookups in the file, because
  prose_levels' selftest reads BAND directly and should: a fixture that took its
  expected values from the function under test would agree with it no matter what
  either of them said.

## A CHECK THAT WAS GREEN BECAUSE THE DATA NEVER ASKED (13 Aug)
- `dectest` failed its own control mid-battery: "a bar reaches past the mark
  exactly when the print covers the level", on 331% / 302% / 100%.
- The painter fills `pct/scale` and puts the mark AT `100/scale`, so at exactly
  100% they are the same number BY CONSTRUCTION — a level covered outright REACHES
  the mark and does not go past it. The check demanded strictly past, and had been
  green for a week only because no level had ever been covered at exactly 100.0%.
  RTY produced one and the check called correct rendering a defect.
- Restated as REACHES, in the direction each side must hold, with a tolerance that
  is not a fudge: both numbers are read back from the DOM at one decimal, and a
  true 99.96% prints as "100%" while filling 33.32 against a 33.3 mark, so the two
  printed figures cannot resolve the boundary more finely than that.
- The class is `check-that-cannot-fail` in the registry, seen from the other side:
  not a check that could never go red, but a check whose hard case the data had
  never presented. Nothing mechanical would have found it. What found it was a
  refresh moving the numbers, which is the argument for running the battery on
  fresh data rather than on the data the check was written against.

## THE TRAPS BELOW ARE PROSE, AND PROSE DOES NOT ENFORCE ITSELF (13 Aug)
- Walton's diagnosis, and it is right: context is lost, the same class of problem
  resurfaces, and the alternative is re-reading everything, which costs time and
  tokens and still misses things.
- MEASURED before acting. This file was 93,509 characters — about 23,000 tokens
  read on every wakeup — of which 37% was superseded STATE blocks. Twenty-six
  traps below, all prose. And one trap, "a thing pinned to a value the data moves
  out from under it", appears in this file FORTY-SEVEN times. It has recurred in
  curated prose, in tap_guardtest, in kz_guardtest, in toktest's probe set, in
  rolltest's thresholds, and in prose I re-anchored on 12 August that was dead by
  the 13th. Each time it was diagnosed and fixed LOCALLY and the class survived.
- The page already knew the principle. Beside BI_BASIS: "The comment above
  already described this failure happening once. Describing it was not enough."
- SO: `lessons.json` is the registry and `lessons.py` runs the ones that can be
  mechanised, in the battery. Three are enforced today (a guardtest naming a check
  its suite does not print; a mutation anchored on a generated figure; a displayed
  figure rounded banker's-style). Seven remain prose and are LISTED as unenforced
  with a reason, so the gap between what is remembered and what is checked is
  visible rather than comfortable. stategen reports the split every run.
- IT FOUND A REAL DEFECT ON ITS FIRST RUN: `ladgen.py` rounding a displayed day
  count with `int(round(...))` — the same banker's-rounding divergence that had a
  pool age reading four in the gate and five on the board the day before.
- AND IT NEARLY BECAME THE THING IT WARNS ABOUT. The first version reported 44
  violations of which one was real: any three-digit number, every `int(round(`,
  every `toFixed`. A linter that noisy is switched off in a day and takes the
  honest checks with it — the same failure stategen was designed against. L2 and
  L3 were narrowed to the exact shape of the defect and L4 was DEMOTED to prose,
  because a check that cannot be made precise should not be a check. Its guardtest
  now stages the false alarms as cases that must NOT fire.
- The superseded STATE blocks moved to `AUTOPILOT-history.md`. Nothing deleted;
  37% off what is read first.

## THE REGISTRY EARNED ITS KEEP WITHIN THE HOUR (13 Aug)
- The battery started right after the lessons work was killed mid-run when the
  container restarted. Before it died it produced the proof the registry was for:
  `tip_guardtest` printed **"the unmutated page does NOT pass — every mutant below
  is meaningless"**, and the truth was a thirty-second `page.goto` timeout. Nothing
  was wrong with the page.
- L5 had been applied to every MUTANT path the day before. Not one CONTROL path
  had it — fifteen files. And the control is where it matters most: a control
  failing marks every case in its file meaningless, so its sentence is the only one
  the reader acts on, and it was pointing at the wrong file.
- Fixed in all fifteen, across the three control shapes this toolchain uses (the
  inline `FAIL K` block, the shared `control()` helper, plan/size's hand-rolled
  one). L5 now checks the control path SEPARATELY — a mutant path carrying the
  branch says nothing about the control path, so it looks backwards a bounded
  distance from each control-failure report rather than anywhere in the file.
- `lessons_guardtest` gained cases E and N5: a control that blames the page must
  fire, a control that rules the harness out first must stay quiet.
- **THE RUNNER NOW RE-RUNS A BROWSER FAULT ONCE, AND SAYS SO.** A flake was
  costing a whole twenty-five-minute battery. `suites.sh` re-runs a suite that
  exits non-zero with no verdict line AND a Playwright signature — both halves
  required, so a real defect can never be swallowed. The retry is announced where
  it happens and listed again in the summary line, because a silent retry is how
  an intermittent defect gets laundered into a green.
- `runner_guardtest.sh` is new and tests exactly that, against four fake suites:
  one that dies like a browser and recovers (must be re-run, must be NAMED), one
  that fails with a verdict (must NOT be re-run), one that passes (untouched), one
  that dies both times (must fail, not loop). Plus a case proving the `WAFT_SUITES`
  door still replaces the list — without it every case above would silently be
  testing the real battery.
- The fake "a suite that passes" was itself reported UNGATED on first run, because
  it only owned `process.exit(0)`. The runner was right and the fixture was wrong,
  which is the `can_fail` check from 6 August doing its job against a file written
  ten minutes earlier.

## KNOWN TRAPS (learned this week — do not relearn)
NOTE: every trap below that could be mechanised has been. Check `lessons.py
--list` before adding a new one here — a trap that can fail a battery is worth
ten that can be forgotten.
- A PROBE SET THAT HOPES FOR ITS CASE STOPS TESTING WITHOUT CHANGING. toktest
  probed each symbol's TOP-SCORING pool. On 11 Aug the refresh gave both top
  pools turns in all four sessions, so the {{mix}} zero path was never exercised
  and a mutant that blanked it passed — while five ES pools and four RTY pools
  still had an absent session sitting right there. Nothing in the suite or the
  page had changed. A probe set must SEEK the shape it is testing (and report
  NOT REACHED when the data truly lacks it), never take whatever the top of a
  sorted list happens to be.
- ONE DEFECT MUST NOT REPORT AS TWO, ESPECIALLY NOT AS SOMETHING ELSE. A dangling
  pool token left its text in the body, so the level scanner then read the anchor
  price as a quoted level and added "prose says POOL but futures terms hold only
  BIN" — true of the anchor, irrelevant to the sentence, and pointing at a
  different repair. Unresolved tokens are now blanked (spaces, to keep offsets)
  before the scan, and the generic backstop fires only for tokens no resolver
  claimed. Thirteen failures became seven, all of them the same three problems.
- A PRECONDITION STATED IN A COMMENT IS NOT A PRECONDITION. kz_guardtest's C/D/N
  scaffold injected a level 2% ABOVE ES and argued in prose that it therefore sat
  off the axis. The killzone span is driven by the furthest of the PER-LANE
  NEAREST distances, so a far level in a direction where its lane holds nothing
  else does not sit off the axis — it BECOMES it. On 10 Aug ES had no standing
  level above at 09:10Z; nearX went 3.6 -> 19.5, the span went ~10 -> ~53, every
  lane compressed fivefold and two RTY labels 0.15x apart collided. A control
  failed on a rendering artefact it had created itself, in a lane it never
  touched. Fixed by injecting DOWNWARD and by MEASURING the precondition at every
  pinned clock before the cases run (clocks parsed out of kztest, not retyped).
  The comment was right for four days and wrong on the fifth and nothing noticed.
- A TEST THAT READS ITS OWN EXPECTATION FROM THE THING IT TESTS CANNOT FAIL.
  rolltest checked the roll threshold at ROLL_STEP_X +/- 0.4 — both derived from
  the constant — so a threshold dropped from 6.0 to 0.5 satisfied every case.
  Caught by its own guardtest. Fixed with ABSOLUTE anchors: an ordinary 1.5x
  session gap must stay quiet, and 4.0 <= ROLL_STEP_X <= 6.0 stated independently.
  Same shape as the toktest hole: every probe anchored on the pool's EXACT current
  key, so a silent return to exact matching was invisible until DRIFTED anchors
  (0.4 of a bin must resolve, 1.8 bins must be refused) went in.
- TWO IMPLEMENTATIONS OF ONE GRAMMAR DIVERGE, AND THE DIVERGENCE IS INVISIBLE
  FROM BOTH SIDES. prose_levels.py gates the build; scenTok() puts words in front
  of the reader. Nothing compared them until toktest. A gate reporting a clean
  page about sentences that were never printed looks exactly like a good day.
- ZERO OPEN CALLS is a real state and several suites had never seen it. Any
  check that reads open-call markup (.fbreak, the whole-reason fold, the
  archive window's open rule) must carry a reachability precondition. When
  adding one, keep the checks that must hold REGARDLESS outside the gate —
  entity escaping and label declaration are about the renderer, not the book.
- A DECODER THAT RESOLVES ENTITIES BUT NOT TAGS silently converts a
  losslessness check into a no-markup check. <textarea> parses its content as
  raw text; use a <div> and mirror what the painter's innerHTML does.
- WHEN ADDING A CATEGORY, add the SUM invariant, not just another slot in the
  per-state array — the array can only check states it already knows about,
  so it passes happily while a new one goes unnamed.
- A FLOOR BESIDE A TYPED LIST OF WHO IT APPLIES TO IS A FLOOR THAT CANNOT
  FIRE. kzgen's BARSYMS/QSYMS gated NQ/YM onto the quote path for three days
  after both floors cleared. Derive membership from the floor itself; keep
  typed lists ONLY for judgements about meaning, and say in a comment which
  kind each one is.
- A FIXED CONCLUSION UNDER A COMPUTED COUNT is the same defect as a fixed
  count under a computed list, one clause further along. The stood card
  computed "ES crossed N gaps" and then asserted "none coincided" as prose;
  when one did, the paragraph contradicted itself. Compute the verdict too.
- A derived figure REPLACING a typed one will usually differ a lot — expect
  it and read the difference as the bug report it is (3.33x -> 1.83x, "three
  contracts" -> five). Print the sample size beside every ratio, or a
  statistic on eight steps reads exactly like one on forty-six.
- NEVER edit the page source while a battery is running: every suite checks
  the artifact's bake-hash against the CURRENT source (fresh.mjs) and goes
  red with "a page that no longer exists" — suites21 died this way, 26 rows
  of noise from one careless edit. Prepare edits during a battery; APPLY
  after it ends (or accept re-running the whole battery).
- Weekend/halt measurement bases part company: kept-vs-raw tonehist rows
  (gap_by withheld past tolerance), trailing-24h "day range" stubs (ladtest
  estimate refusal >6h stale), d1/on windows rolling off closed sessions.
  Expect every "trailing window" figure to mean something different on a
  shut market, and write refusals rather than tolerances where possible.
- The stood-card advisory hand-types its cross-contract figures (3.33x/
  1.22x/0.96x, "three gaps, none coincided") — backlog: derive or tokenize;
  they matched the measured values as of 8 Aug.
- free-bars arrays are RING-ORDERED, not chronological — sort by timestamp
  before touching either end (bars[0] was 06:00Z when read naively).
- Playwright routes match in REVERSE registration order (catch-all abort must
  be registered FIRST), and the loader cache-busts with ?t=... so route globs
  need a trailing * after .json.
- claims_near fires on the price's OWNED SPAN (midpoint-to-midpoint between
  neighbouring prices): consecutive consumed-pool obituaries leak "turns"
  into each other's backward windows (put a negation word in the connective),
  and a spelled compound sliced at a span midpoint reads as its tail
  ("forty-eight turns" -> "eight turns") — keep counts out of inter-price
  gaps. Share-claims attach when the link text ends at/carries/holds/is —
  "coming to X% between them" does not attach.
- Pool keys DRIFT as turns accrue (3,049.78->3,048.96, 7,754.68->7,755.31):
  {{age}} token referents must be re-keyed when the guard reports the move;
  claims_near tolerates a bin, the token resolver does not.
- The prose guard's window semantics for plan/window fields: a 30-min close
  belongs to a window only if it ends AFTER the open (half-open start).
- A consumed pool can REBUILD within the hour if price camps on the price —
  never write a pool's obituary as final; phrase consumption as dated history
  and let the turn count carry the present. (7,766.49: 44 consumed at 12:30Z,
  46 listed by 14:12Z.)
- The prose guard fires claim words BOTH sides of a price within the segment
  window ("value area now tops out at X" fired VA on X) — negation-first
  works in either direction, and TRUE claims are always the safest fix.
- Simultaneous releases (payrolls day: 3 events, one 12:30Z minute) carry
  IDENTICAL scored legs — any per-event renderer prints the same measured
  paragraph N times, and reads as N independent moves. Dedupe in the painter
  (full lead once, ordinal pointers under it). bakedup only sees VISIBLE
  (innerText) repeats — closed folds legitimately hide identical bodies.
- Negation-first grammar: the negation must sit BETWEEN the price and the
  claim word in the segment. After a pool is consumed, grep EVERY site of the
  price (cross-references in OTHER contracts' rows, tiles, tags, state) — the
  W1 straggler was a C/ES row referencing an RTY-adjacent ES pool.
- Scenario probs are dated judgements: re-weigh only with reasons written
  into the tag, tied to conditions the branch itself wrote in advance; CALL
  records inside invalids are immutable like var CALLS.
- A guardtest case whose branch depends on live data MUST state a reachability
  precondition or a data change reads as suite blindness (pattern: tap C/G,
  kz I/M, seas E, landtest seeding) — and the precondition must be computed
  through the SAME precedence/composition the painter applies, not per-level
  (plan A hid behind an invalidation chip that outranked the mutated read).
- Cumulative profiles cannot decline while the window grows — "zero bins
  declined" is not evidence.
- A quiet predicate is live protection (GOLD's UNTRUSTED_PREV stays).
- IBKR/AV data enters ONLY as dated fixtures; claims carry their dates.
- refresh.sh merges the relay (post-squash divergence); verify tags
  presquash-20260804 + archive-local-20260806 survive any reset.
