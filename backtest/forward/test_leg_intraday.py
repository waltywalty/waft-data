"""Structural tests for leg_intraday (Round 71): direction rules, calendar, no-lookahead,
contract isolation. Synthetic bars only - no market data is read."""
import datetime as dt
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leg_intraday as L  # noqa: E402

NY = "America/New_York"


def _write(dirpath, name, contract, bars):
    """bars: list of (ts_ny_str, open, close)."""
    ts = [pd.Timestamp(t, tz=NY).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ") for t, _, _ in bars]
    d = dict(time=ts, open=[o for _, o, _ in bars], close=[c for _, _, c in bars],
             high=[max(o, c) for _, o, c in bars], low=[min(o, c) for _, o, c in bars],
             volume=[1] * len(bars), contract=contract)
    json.dump(d, open(os.path.join(dirpath, name), "w"))


def _session(date, px, step=0.0, extra=()):
    """A full 09:30-16:55 session of 5m bars at px (+step per bar) on `date` (YYYY-MM-DD)."""
    out = []
    t = pd.Timestamp(f"{date} 09:30", tz=NY)
    p = px
    while t.hour * 100 + t.minute <= 1655:
        out.append((t.strftime("%Y-%m-%d %H:%M"), p, p + step)); p += step
        t += pd.Timedelta(minutes=5)
    return out + list(extra)


def test_third_friday():
    assert L.third_friday(dt.date(2026, 9, 18))
    assert not L.third_friday(dt.date(2026, 9, 11))
    assert not L.third_friday(dt.date(2026, 9, 25))
    assert L.third_friday(dt.date(2026, 10, 16))


def test_f2_f3_directions():
    with tempfile.TemporaryDirectory() as td:
        bars = _session("2026-09-10", 100.0, step=0.1)      # rising day: 15:50 open > 09:30 open
        _write(td, "es_5m_a.json", "ESZ6", bars)
        rows = L.es_events(L.load_5m(td, "es"))
        f2 = [r for r in rows if r["spec"] == "F2"]; f3 = [r for r in rows if r["spec"] == "F3"]
        assert len(f2) == 1 and f2[0]["dir"] == 1 and f2[0]["pnl"] > 0
        # push 15:50 open -> 16:00 print is positive on the rising day, so F3 is SHORT
        assert len(f3) == 1 and f3[0]["dir"] == -1
        assert abs(f3[0]["entry"] - (100.0 + 0.1 * 78)) < 1e-6 and abs(f3[0]["exit"] - (100.0 + 0.1 * 81)) < 1e-6
        assert not [r for r in rows if r["spec"] == "F1"]     # 2026-09-10 is not a third Friday


def test_f1_gap_fade_uses_prior_session_same_contract():
    with tempfile.TemporaryDirectory() as td:
        prev = _session("2026-09-17", 100.0)                 # flat day, last RTH print 100.0
        fri = _session("2026-09-18", 101.0, step=-0.05)      # gap +1.0 on the third Friday, then fades
        _write(td, "es_5m_a.json", "ESZ6", prev + fri)
        rows = [r for r in L.es_events(L.load_5m(td, "es")) if r["spec"] == "F1"]
        assert len(rows) == 1 and rows[0]["dir"] == -1 and rows[0]["pnl"] > 0
        assert rows[0]["note"] == "gap +1.00"
    with tempfile.TemporaryDirectory() as td:
        _write(td, "es_5m_a.json", "ESU6", _session("2026-09-17", 100.0))
        _write(td, "es_5m_b.json", "ESZ6", _session("2026-09-18", 101.0, step=-0.05))
        rows = [r for r in L.es_events(L.load_5m(td, "es")) if r["spec"] == "F1"]
        assert rows == []                                     # prior print on another contract -> void


def test_f4_sunday_gap():
    with tempfile.TemporaryDirectory() as td:
        fri = _session("2026-09-11", 2000.0)                 # Friday, last bar 16:55 close 2000
        sun = []
        t = pd.Timestamp("2026-09-13 18:00", tz=NY); p = 2010.0   # Sunday reopen gap +10, then fades 0.1/bar
        while t < pd.Timestamp("2026-09-14 03:05", tz=NY):
            sun.append((t.strftime("%Y-%m-%d %H:%M"), p, p - 0.1)); p -= 0.1
            t += pd.Timedelta(minutes=5)
        _write(td, "gc_5m_a.json", "GCZ6", fri + sun)
        rows = L.gc_events(L.load_5m(td, "gc"))
        assert len(rows) == 1 and rows[0]["spec"] == "F4" and rows[0]["dir"] == -1 and rows[0]["pnl"] > 0
        assert rows[0]["date"] == "2026-09-14" and rows[0]["note"] == "gap +10.00"


def test_missing_bar_voids():
    with tempfile.TemporaryDirectory() as td:
        bars = [b for b in _session("2026-09-10", 100.0, step=0.1) if not b[0].endswith("15:50")]
        _write(td, "es_5m_a.json", "ESZ6", bars)
        rows = L.es_events(L.load_5m(td, "es"))
        assert not [r for r in rows if r["spec"] in ("F2", "F3")]


def test_score_bar_logic():
    rows = [dict(spec="F2", pnl=1.0, R=0.05, R15=0.04, R20=0.03, date=f"2026-01-{i%28+1:02d}") for i in range(50)]
    sc = L.score(rows)
    assert sc["F2"]["n"] == 50 and sc["F2"]["x1"]["t"] is None          # zero variance -> no t
    rows = [dict(spec="F2", pnl=1.0 + 0.01 * (i % 5), R=0.05 + 0.001 * (i % 5), R15=0.04, R20=0.03,
                 date=f"2026-01-{i%28+1:02d}") for i in range(50)]
    assert L.score(rows)["F2"]["bar"] is True
    rows[0]["R20"] = -5.0
    assert L.score(rows)["F2"]["bar"] is False


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_") and callable(v):
            v(); print("ok", k)
