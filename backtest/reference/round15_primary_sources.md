# Round 15 — Primary-source specs: intraday momentum, overnight/intraday split, Concretum ORB, pre-FOMC drift, TSMOM

**Date:** 2026-08-26. **Purpose:** exact rule specifications, key numbers, and post-publication
decay evidence for five literatures, ahead of testing on our own data (5-min SPX/NDX/RTY CFDs
2005–2025, 5-min spot gold 2020–2025, daily FX/metals/energy/yield series).

**Access caveat (read this first).** This session's egress proxy blocked *all* direct PDF/page
fetches (SSRN, arXiv, NBER, NY Fed, journal sites, authors' pages all denied at the proxy).
Every fact below was extracted via web-search retrieval of the primary documents' text
(search-engine renderings of the paper PDFs and official pages), not by reading the PDFs
end-to-end. Primary URLs are cited for every claim; numbers are quoted only where the search
retrieval surfaced them verbatim from the primary document or its official abstract. Where a
number could not be recovered verbatim, that is said explicitly rather than approximated.
Table/page numbers are given only where recoverable. Before implementation, pull the cited
PDFs from an unrestricted network and verify the flagged items.

---

## 1. Gao, Han, Li, Zhou (2018), "Market intraday momentum", *JFE* 129(2), 394–414

**Primary sources:**
- Published version: https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351 (paywalled; abstract read)
- SSRN working paper (id 2440866): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866
- Open-access accepted manuscript: https://researchmgt.monash.edu/ws/files/519509174/494419119_oa.pdf (egress-blocked here; use to verify)
- Earlier SSRN version titled "Intraday Momentum: The First Half-Hour Return Predicts the Last Half-Hour Return": https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2552752

### Predictor definition (the load-bearing detail)
- The **first half-hour return `r1` is measured from the *previous day's close*** (16:00 ET
  close of day *t−1*) **to 10:00 ET of day *t***, i.e. it *includes the overnight gap*. This is
  stated in the published abstract: "the first half-hour return on the market **as measured
  from the previous day's market close** predicts the last half-hour return."
  (https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414)
- The day is cut into 13 half-hours (09:30–16:00 ET). `r13` = last half-hour return,
  **15:30–16:00 ET**, the dependent variable. `r12` = twelfth half-hour, **15:00–15:30 ET**,
  used as a second predictor.
- Notation: `r13,t = α + β1·r1,t + β12·r12,t + ε` with Newey–West (1987) t-statistics.

### Key regression numbers (paper Table 2 in the SSRN/JFE versions)
- `r1` alone: **scaled (×100) slope 6.94, significant at 1%, R² = 1.6%**.
  Out-of-sample R² with `r1` as the only predictor: **1.4%**.
  (Sources: SSRN id 2440866 abstract/first pages as surfaced in search; mirror of the SSRN
  PDF: https://www.smallake.kr/wp-content/uploads/2015/01/SSRN-id2440866.pdf and
  https://assets.super.so/e46b77e7-ee08-445e-b43f-4ffd88ae0a0e/files/ee7dac49-530b-4950-b5d0-e0b5eee08f2e.pdf)
- `r1` + `r12` jointly: **R² = 2.6%**; "the slopes barely change from their individual
  regression values, and the joint R², 2.6%, is roughly equal to the sum of the individual
  R²s" (same sources). Individual `r12` slope/t-stat not recovered verbatim — verify in PDF.
- Exact Newey–West t-stat for the 6.94 slope not recovered verbatim here (the paper reports
  it significant at 1%) — verify in Table 2 of the PDF.

### Trading strategy and performance (paper Table 6 region)
- Rule: **at 15:30 ET, go long SPY for the last half-hour if `r1 > 0`, short if `r1 < 0`;
  flat close at 16:00**. (A second variant uses sign of `r12`; a third trades only when both
  agree.)
- Reported performance for the `r1` rule on SPY 1993–2013: **average annualized return 6.67%
  vs 6.04% for daily buy-and-hold, Sharpe 1.08 vs 0.29 for buy-and-hold** (as quoted from the
  paper by QuantifiedStrategies' review: https://www.quantifiedstrategies.com/day-trading-momentum-strategy/
  — secondary; verify against paper Table 6).
- Success rates: the paper reports success rates for the timing rules (one accessible
  replication quotes **50.93%** for the always-in r1 rule; the paper's own Table 6 success
  rates were not recoverable verbatim here — verify). (Replication thesis:
  https://www.diva-portal.org/smash/get/diva2:1878991/FULLTEXT01.pdf)

### Conditioning results
Predictability is **stronger on: high-volatility days, high-volume days, recession days, and
major macro news release days** (published abstract, all sources above). Recoverable numbers:
- Expansions: `r1` predicts `r13` weakly, **R² = 0.9%**; recessions: both `r1` and `r12`
  highly significant, **R² = 6.6%** (surfaced from the paper text via
  https://law-journals-books.vlex.com/vid/understanding-intraday-momentum-strategies-1049461706 search retrieval).
- High first-half-hour-volatility days: joint R² rises to **3.3%**.

### Sample
SPY intraday (minute-level, TAQ) **1993–2013**; robustness on other index ETFs (e.g. QQQ,
DIA, IWM) and futures in the paper's later tables (verify list in PDF).

### Post-2018 out-of-sample / decay evidence
1. **Baltussen, Da, Lammers, Martens (2021), "Hedging demand and market intraday momentum",
   *JFE* 142(1)**: 60+ futures (equities incl. S&P/ES, bonds, commodities, currencies)
   **1974–2020**; last-30-minute return positively predicted by rest-of-day return
   (previous close → 15:30) "everywhere"; effect **reverts over the next days**; driven by
   gamma-hedging demand (options + leveraged-ETF rebalancing).
   PDF: https://www3.nd.edu/~zda/intramom.pdf ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365 ;
   published: https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001598
2. **Rosa (2022), "Understanding intraday momentum strategies", *Journal of Futures Markets*
   42(12), 2218–2234**: out-of-sample extension of the Gao et al. overnight-signal rule on
   SPY — **"the predictability disappears in the out-of-sample period"**; a Markov-switching
   model finds predictability only in one regime; signal-strength thresholds beat the
   always-active rule. https://onlinelibrary.wiley.com/doi/abs/10.1002/fut.22375 ;
   https://econpapers.repec.org/RePEc:wly:jfutmk:v:42:y:2022:i:12:p:2218-2234
3. **Zarattini, Aziz, Barbon (2024)** (Section 3 below) is effectively a post-publication SPY
   test (2007–2024) with a modified (band-based, all-day) construction that still works
   on paper.
4. Secondary replication on futures: Quantitativo's ES/NQ implementation of the band-based
   variant reports 24.3% ann., Sharpe 1.67, +6 bps/trade, 38% win rate — blog-grade, not
   peer-reviewed. https://www.quantitativo.com/p/intraday-momentum-for-es-and-nq

**Net read:** the *published* Gao et al. rule (overnight+first-half-hour signal → last half
hour) decayed on SPY after the sample ended (Rosa 2022), but the broader
rest-of-day → last-half-hour effect is documented across 60+ futures over 46 years with an
economic mechanism (Baltussen et al. 2021). That version is the one worth testing.

---

## 2. Lou, Polk, Skouras (2019), "A tug of war: Overnight versus intraday expected returns", *JFE* 134(1), 192–213

**Primary sources:**
- Published: https://www.sciencedirect.com/science/article/abs/pii/S0304405X19300650 (paywalled)
- Author PDF: https://personal.lse.ac.uk/polk/research/TugOfWar.pdf (egress-blocked here)
- LSE eprint: http://eprints.lse.ac.uk/87481/ ; FMG DP744: https://researchonline.lse.ac.uk/id/eprint/119010/1/DP744.pdf
- NBER conference version: https://conference.nber.org/confer/2015/APf15/Lou_Polk_Skouras.pdf

### Decomposition methodology
- Intraday return: **open-to-close**, `r_intraday = P_close/P_open − 1`, using opening prices
  (TAQ-based; CRSP close-to-close for the total). Overnight return is backed out
  multiplicatively: **`r_overnight = (1 + r_close-to-close) / (1 + r_intraday) − 1`** — i.e.
  overnight is prior-close → today's open. (Construction as in the author PDF; formula
  restated here from the paper's standard method — verify notation on p. 195-ish of the
  published version. Sample is **1993–2013, constrained by TAQ availability**; search
  retrieval of the LSE PDF confirmed the sample statement.)

### Key results
- Across **14 trading strategies**, "profits are either earned entirely overnight (for
  reversal and a variety of momentum strategies) or entirely intraday, typically with profits
  of opposite signs across these components" (published abstract, all sources above).
- **All momentum-type abnormal returns accrue overnight; other characteristics (size, value
  etc.) earn their premia intraday.** Example recovered verbatim: industry-momentum hedge
  portfolio **overnight CAPM alpha +1.07%/month (t = 6.47)** vs **intraday CAPM alpha
  −0.63%/month**; overnight-minus-intraday spreads are "on the order of 2% per month".
  Another recovered figure: a past-one-month-intraday-return sort earns **+2.19%/month
  intraday** on the hedge portfolio; one component quoted at **−1.81%/month (t = −8.44)**
  (overnight leg of that reversal-type sort — verify which table, likely Table 2).
- **Clientele conclusion:** "relative to individuals, institutions prefer to trade during the
  day and against the momentum characteristic." Individual/retail order flow concentrates
  near the open; institutions trade intraday and lean against momentum names, so the
  momentum premium is realized overnight and partially reversed intraday. Momentum's
  overnight return is larger, and the intraday reversal stronger, when momentum-arbitrage
  activity is low or institutions' rebalancing needs are high.
- Firm-level: overnight (intraday) return continuation persists in the same session for
  **years**, with an offsetting cross-period (overnight↔intraday) reversal.

### Index-level overnight vs intraday, and futures/ES evidence
LPS is a **cross-sectional stock paper** — it does not give an index-CFD-tradable rule. The
index/futures-level facts come from the adjacent literature:
- **Cooper, Cliff, Gulen (2008), "Return differences between trading and non-trading hours:
  like night and day"** (SSRN 1004081): the U.S. equity premium in their sample is earned
  **entirely overnight** (night returns strongly positive; day returns ≈ 0 or negative), and
  this **holds for index futures as well as cash indexes**, robust across weekdays/months.
  Mirror of the SSRN PDF: https://assets.super.so/e46b77e7-ee08-445e-b43f-4ffd88ae0a0e/files/d0749895-bc80-4bf5-9b53-fed6eed60914.pdf
- **Boyarchenko, Larsen, Whelan (2023), "The Overnight Drift", *RFS* 36(9), 3502–3547** —
  the ES-specific decomposition: using **E-mini S&P 500 futures round-the-clock data
  1998–2019**, overnight returns concentrate in the **02:00–03:00 ET window (European open),
  ~3.6% annualized from that hour alone**; linked to inventory risk / order imbalances at the
  prior U.S. close; sell-offs produce robust positive overnight reversals, rallies much less.
  NY Fed staff report 917: https://www.newyorkfed.org/research/staff_reports/sr917 ;
  published: https://ideas.repec.org/a/oup/rfinst/v36y2023i9p3502-3547..html ;
  Liberty Street summary (May 2021): https://libertystreeteconomics.newyorkfed.org/2021/05/the-overnight-drift-in-us-equity-returns
- **Decay:** Boyarchenko–Larsen–Whelan, "The Disappearing Overnight Drift" (Liberty Street,
  **July 2026**; SSRN 7035838): with five more years of data, **the 02:00–03:00 ET window
  that earned ~3.7%/yr has averaged ≈ zero since 2021**.
  https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/ ;
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7035838

---

## 3. Zarattini & Aziz (Concretum Research) — SSRN catalogue

**Primary index:** https://concretumgroup.com/papers/ (egress-blocked here) and SSRN author
page https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=5831512. Zarattini's papers are
working papers (SSRN / Swiss Finance Institute), **not peer-reviewed journal publications**;
several won practitioner awards (Quantpedia 2024/2025, Charles H. Dow Award 2025).

### 3.1 "Can Day Trading Really Be Profitable?" — Zarattini & Aziz, Apr 2023, SSRN 4416622
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4416622
- **Rule (5-minute ORB on QQQ):** if QQQ rises (falls) in the first 5-minute bar
  (09:30–09:35 ET), buy (sell) at the open of the second bar (09:35 ET). Stop = low (high) of
  the first 5-min bar; **profit target = 10× the entry-to-stop distance (10R)**; otherwise
  exit at the close (EoD).
- **Instrument/sample:** QQQ, **2016–2023**.
- **Reported results:** ORB with leverage **+1,484% total vs +169% for QQQ buy-and-hold;
  Sharpe ≈ 2.4; beta ≈ 0**. Assumptions reported by reviewers: **$25,000 starting capital,
  max 4× leverage, $0.0005/share commission**.
  (Secondary confirmations of the numbers: https://therobusttrader.com/can-day-trading-really-be-profitable-rules-backtest-statistics-performance-analysis/ ,
  https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy/ — verify against the SSRN PDF.)

### 3.2 "Volume Weighted Average Price (VWAP): The Holy Grail for Day Trading Systems" — Zarattini & Aziz, Nov 2023, SSRN 4631351
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4631351
- **Rule (VWAP trend):** intraday long when price above session VWAP, short when below
  (VWAP cross system with their filters; exact entry/exit refinements in paper).
- **Instrument/sample:** QQQ (and leveraged TQQQ variant), 2016–2023 window as in their
  other papers (verify exact dates in PDF).
- **Reported results:** $25,000 → **$192,656 net of commissions (+671%), max drawdown 9.4%,
  Sharpe 2.1**. (Abstract figures via SSRN page/ResearchGate:
  https://www.researchgate.net/publication/376217460_Volume_Weighted_Average_Price_VWAP_The_Holy_Grail_for_Day_Trading_Systems)

### 3.3 "A Profitable Day Trading Strategy for the U.S. Equity Market" — Zarattini, Barbon & Aziz, Feb 2024, SSRN 4729284 (SFI 24-98)
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284
- **Rule:** 5-minute ORB applied not to an index ETF but to **"Stocks in Play"** — each day
  the top-20 stocks by abnormal relative volume (news-driven activity) from a 7,000+ stock
  universe, 2016–2023; same ORB entry/stop logic with position sizing by risk.
- **Reported results:** **+1,600%+ total net performance, Sharpe 2.81, annualized alpha 36%**,
  net of transaction costs. (SSRN abstract; QuantConnect replication write-up:
  https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)

### 3.4 "Beat the Market: An Effective Intraday Momentum Strategy for S&P 500 ETF (SPY)" — Zarattini, Aziz & Barbon, May 2024, SSRN 4824172 (SFI 24-97)
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172 ; OA PDF via Unisg:
https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download
- **Rule ("Noise Area" bands):** each minute, upper/lower boundaries = day's **open ×
  (1 ± average absolute return from open to that minute-of-day over the last 14 trading
  days)**; the upper band is shifted up by any overnight gap-down and the lower band down by
  any overnight gap-up. **At each HH:00 / HH:30 ET checkpoint**, if SPY is above the upper
  (below the lower) band, go/stay long (short); exit via a **dynamic trailing stop** (the
  band / VWAP, per paper) or at the close. Position sized to **2% daily vol target using
  14-day realized SPY vol, capped at 4× leverage**; commissions **$0.0035/share** (IBKR
  entry tier), slippage sensitivity analysed.
- **Instrument/sample:** SPY minute bars, **2007 – early 2024**.
- **Reported results:** **total +1,985% net, 19.6% annualized, Sharpe 1.33** vs SPY
  buy-and-hold Sharpe 0.45. (Abstract + reviews:
  https://www.sfi.ch/en/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy ,
  https://www.cxoadvisory.com/momentum-investing/complex-intraday-time-series-momentum-strategy-applied-to-spy/ ,
  https://quantmacro.substack.com/p/paper-review-an-effective-intraday)
- Third-party extension: Maróy (2025), SSRN 5095349, parameter/exit optimization on this
  strategy. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5095349
- **No Zarattini paper on ES futures intraday momentum was found** — the ES/NQ port is the
  Quantitativo blog replication cited in Section 1.

### 3.5 "The Power of Price Action Reading" — Zarattini & Stamatoudis, Jun 2024, SSRN 4879527 (their gap study)
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4879527 ; PDF:
https://concretumgroup.com/wp-content/uploads/2026/02/The-Power-Of-Price-Action-Reading.pdf
- **Design:** 9,794 large **overnight gap-up events** (average gap ≈ 28%) in US stocks
  2016–2023; baseline finding: **post-gap-up prices drift downward on average**; an
  experienced discretionary trader micromanaging entries/exits on the same events
  substantially improves P&L vs mechanical rules.

### 3.6 "A Century of Profitable Industry Trends" — Zarattini & Antonacci, Jun 2024, SSRN 4857230
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4857230 ; award version:
https://cmtassociation.org/wp-content/uploads/2025/09/2025-Dow-Winner-A-Century-of-Profitable-Trends.pdf
- Long-only trend following across **48 industry portfolios, 1926–2024**: **18.5%/yr vs
  9.7% for the US market, annualized alpha 10.9%, ~60% drawdown reduction** vs passive.

### 3.7 Others noted on their index (not fully specified here)
Crypto trend following with Donchian-channel ensembles and vol-based sizing; a
**rebalance-timing-luck** study (identical momentum strategies differing only in rebalance
date diverge by ~350 bps/yr, 1991–2024). Via https://concretumgroup.substack.com/about

**Costs caveat for all Concretum papers:** costs are commissions-only at IBKR retail tiers
($0.0005–$0.0035/share) plus modelled slippage sensitivities; no exchange/SEC fees or
borrow costs on shorts; all results are same-team backtests without independent refereeing.

---

## 4. Lucca & Moench (2015), "The Pre-FOMC Announcement Drift", *Journal of Finance* 70(1), 329–371

**Primary sources:**
- Published: https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12196
- NY Fed Staff Report 512 (open): https://www.newyorkfed.org/research/staff_reports/sr512.html ;
  PDF mirrors: https://www.bostonfed.org/-/media/Documents/conference/PDF/Lucca_preFOMCDrift.pdf ,
  https://conference.nber.org/confer/2013/MEs13/Lucca_Moench.pdf
- SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1923197

### Exact specification
- **Window:** the 24 hours before scheduled FOMC announcements. Announcements were released
  at/around **14:15 ET**; the tradable version in the paper: **buy the S&P 500 at 14:00 ET
  the day before a scheduled announcement, sell at 14:00 ET on announcement day (15 minutes
  before release), cash otherwise.**
- **Magnitude:** S&P 500 excess return averages **+49 bps in the 24h pre-FOMC window**,
  sample **September 1994 – March 2011** (8 scheduled meetings/yr). Since 1994, **more than
  80% of the U.S. equity premium was earned in these windows**. The 14:00→14:00 strategy's
  **annualized Sharpe ≈ 1.14**. (All from the staff-report text as surfaced:
  https://www.newyorkfed.org/research/staff_reports/sr512.html and mirrors above; also the
  Liberty Street post "The Puzzling Pre-FOMC Announcement 'Drift'": https://fedinprint.org/item/fednls/86814)
- **Instruments used:** S&P 500 cash index plus **S&P 500 futures Sep 1994–Sep 1997 and
  E-mini ES futures from Sep 10, 1997** for the around-the-clock measurement (per the
  disappearing-drift follow-up describing the construction:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/).
- **Cross-asset:** similar pre-FOMC returns in major international equity indices; **no
  drift in U.S. Treasuries or money-market futures**. Drift not explained by realized risk
  in the window (excess-return-to-risk puzzle). Pre-1994 (before announcement-time
  regularization): no comparable drift.

### Post-publication evidence
1. **Lucca & Moench, Liberty Street Economics, Nov 2018, "The Pre-FOMC Announcement Drift:
   More Recent Evidence"**: drift continued post-2011 **only for meetings with a Chair press
   conference**. https://libertystreeteconomics.newyorkfed.org/2018/11/the-pre-fomc-announcement-drift-more-recent-evidence/
2. **Kurov, Wolfe, Gilbert (2021), "The disappearing pre-FOMC announcement drift", *Finance
   Research Letters* 40**: extending to Dec 2019, the drift **essentially disappeared after
   2015** for both press-conference and non-press-conference meetings; decline attributed to
   reduced market-condition uncertainty. https://www.sciencedirect.com/science/article/abs/pii/S1544612320315956 ;
   open PMC copy: https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/ ; working paper:
   https://www.skidmore.edu/economics/documents/KurovWolfeGilbert-TheDisappearingPre-FOMC-Announce-Drift-200914.pdf
3. Mixed later evidence: "The pre-FOMC announcement drift: short-lived or long-lasting?"
   (*Applied Economics*, 2024) examines financial and volatility markets.
   https://www.tandfonline.com/doi/full/10.1080/00036846.2024.2322573
4. Note: announcement time moved to **14:00 ET** with press conferences at 14:30 from 2011–13
   onward — window definition must follow the *scheduled release time per meeting*, not a
   fixed clock time, when testing.

---

## 5. Moskowitz, Ooi, Pedersen (2012), "Time series momentum", *JFE* 104(2), 228–250 — gold/commodity-relevant extract

**Primary sources:**
- Published (open on ScienceDirect): https://www.sciencedirect.com/science/article/pii/S0304405X11002613
- Author PDF: https://w4.stern.nyu.edu/facdir/lpederse/papers/TimeSeriesMomentum.pdf (blocked here; mirrors:
  https://fairmodel.econ.yale.edu/ec439/jpde.pdf , https://elmwealth.com/wp-content/uploads/2017/06/timeseriesmomentum.pdf)
- Original per-asset dataset published by AQR: https://www.aqr.com/Insights/Datasets/Time-Series-Momentum-Original-Paper-Data

### Core rule (TSMOM 12,1)
- Universe: **58 futures/forwards** — 24 commodities (incl. **gold**), 12 FX cross pairs,
  9 developed equity indices, 13 developed bond futures; sample **Jan 1965 – Dec 2009**
  (TSMOM factor evaluated 1985–2009 when all assets exist).
- Signal, evaluated monthly per instrument: **sign of the instrument's own past 12-month
  excess return**. Long if positive, short if negative; **hold 1 month**, re-form monthly.
- **Position sizing:** each position scaled to **40% ex-ante annualized volatility**
  (`position = 40%/σ_{t−1}`); with 58 instruments this yields a portfolio annualized vol of
  **≈12%** (1985–2009). σ is the **exponentially weighted** ex-ante vol of daily returns with
  a **center of mass of 60 days** (δ = 60/61; annualized with 261 trading days) — formula in
  Section 2 of the paper (mirrored PDFs above; the EWMA parameters could not be re-verified
  through the proxy — check §2.2 before coding).
- Predictability regression: scaled returns `r_t/σ_{t−1}` on lagged `r_{t−h}/σ_{t−h−1}`,
  pooled; positive and significant for lags 1–12 months, partial reversal beyond ~1 year.

### Gold / per-asset numbers
- "**Every single futures contract** exhibits positive predictability from past one-year
  returns" and **52 of 58 are statistically significant at the 5% level** — gold included.
  Per-asset 12-month TSMOM Sharpe ratios are plotted in **Figure 2 Panel A** (t-stats in
  **Figure 1**). The **exact gold Sharpe value is not printed in text and was not
  recoverable through this session's blocked proxy** — read it off Figure 2 in the mirrored
  PDF, or compute it directly from AQR's published original-paper dataset (link above),
  which is the cleaner route.
- Diversified TSMOM across all assets: **annualized Sharpe > 1 (gross of transaction
  costs), ≈2.5× the equity market's Sharpe**, low correlation to passive benchmarks and
  standard factors; performs best in extreme markets ("TSMOM smile").

### Best-known simplified daily implementation
- **Quantpedia's canonical simplification** ("Time Series Momentum Effect"): monthly, go
  long/short each instrument by the sign of its past-12-month return, vol-scale positions —
  https://quantpedia.com/strategies/time-series-momentum-effect
- **Hurst, Ooi, Pedersen (AQR), "A Century of Evidence on Trend-Following Investing" /
  "Demystifying Managed Futures"**: the standard practitioner variant — equal-weighted
  combination of **1-month, 3-month and 12-month** TSMOM signals, vol-scaled; AQR PDF:
  https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/Demystifying-Managed-Futures.pdf
- For daily data the accepted simplification is: signal = sign(close_t / close_{t−252} − 1)
  (or past-12m excess return vs cash), evaluated daily or monthly, position = target_vol/σ_t
  with an EWMA σ. Open replication code: https://github.com/rkohli3/TSMOM

---

## 6. What is testable on our data

Ranked by (a) fit to our data, (b) survival of post-publication evidence, (c) implementation
risk. House rules apply throughout (holdout, gradient-not-peak, both-halves sign test,
max-stat randomisation, cost sensitivity — `backtest/reference/README.md`).

### A. 5-minute SPX/NDX/RTY CFDs, 2005–2025, 24h sessions — best fit
1. **Gao-style intraday momentum, Baltussen variant (top pick).** Predictor: prior RTH close
   (16:00 ET) → 15:30 ET return (or first-half-hour r1 = prior close → 10:00 ET); trade
   15:30–16:00 ET. Directly implementable on all three indices; our 2005–2025 window brackets
   the 2013 sample end and 2018/2021 publication dates, so the **decay test (Rosa 2022) is
   the primary question**, not the in-sample effect. Both r1-only and rest-of-day variants
   should be pre-registered; count both in the multiple-testing budget.
2. **Pre-FOMC drift.** 24h sessions make the 14:00→release-time window fully tradable on
   SPX CFDs. Scheduled FOMC dates/times are public; sample gives ~160 events over 2005–2025.
   Expectation from the literature: positive 2005–2015, ≈0 or negative after (Kurov et al.).
   Clean event-study, few parameters — good candidate despite low event count.
3. **Overnight drift (Boyarchenko et al.).** 24h CFD sessions expose the 02:00–03:00 ET
   European-open window directly. Literature says the effect existed 1998–2019 and **died
   after 2021** — a replication on our data is a decay-confirmation exercise; CFD overnight
   financing/spread will likely dominate a 1-hour-per-day 3.6%/yr gross effect. Low priority
   as a strategy, useful as a data-validation exercise.
4. **Zarattini noise-band intraday momentum.** Implementable on index CFDs (bands from the
   09:30 open, HH:00/HH:30 checkpoints). Heavier parameterisation (14-day window, band gap
   adjustments, trailing stop, vol targeting) = large multiple-testing surface and no
   independent refereeing; treat reported Sharpes as upper bounds. ORB (5-min) is testable
   too but the QQQ/stocks-in-play economics (news-driven single names) do not transfer to
   index CFDs.
5. **Lou-Polk-Skouras proper: not testable** — it is a cross-sectional single-stock design.
   Only the index-level overnight-vs-intraday split (Cooper-Cliff-Gulen flavour) is testable:
   decompose our CFD close-to-close into 16:00→09:30 and 09:30→16:00 legs and test the
   night/day premium split. Costs again decisive.

### B. 5-minute spot gold, 2020–2025 — partial fit
- **Intraday momentum**: Baltussen et al. include gold futures in their 60+ universe, so a
  gold last-half-hour test (rest-of-COMEX-day → 15:30–16:00 ET window, or the 13:30 ET COMEX
  pit close) is literature-backed. But **5 years ≈ 1,250 obs with R² ~1–3%** — power is
  marginal; treat as confirmatory of the CFD result, not standalone.
- **Pre-FOMC**: the original paper finds the drift in equities, *not* in rates; gold is
  untested there — any gold pre-FOMC test is exploratory and must be labelled as such.
- **TSMOM on 5 years of intraday gold: not testable** (needs a 12-month lookback and decades
  of monthly observations for power). Use the daily series instead.

### C. Daily FX/metals/energy/yield series — TSMOM territory
- **TSMOM 12,1 with 40%/σ sizing** is directly implementable across the daily universe and is
  the only one of the five literatures designed for this data shape. Gold-specific prior:
  positive but individually weak (one of 58 positives; significance borderline per asset) —
  judge by the cross-asset gradient, not gold's own p-value. Benchmark against AQR's
  published original dataset before trusting our own series (data-provenance rule).
- The 1/3/12-month ensemble (Hurst-Ooi-Pedersen) is the pre-registered robustness variant.

### Cross-cutting warnings
- Three of the five literatures have **documented post-publication decay** (Gao/SPY via Rosa
  2022; pre-FOMC via Kurov et al. 2021; overnight drift via NY Fed 2026). Only TSMOM and the
  broad-futures intraday momentum (Baltussen) have held up in refereed extensions. Priors
  should be set accordingly.
- Concretum results are unrefereed same-team backtests with retail-commission-only costs;
  reproduce before believing any headline Sharpe.
- Every number above flagged "verify" must be checked against the actual PDF from an
  unrestricted network before being hard-coded into a test spec.
