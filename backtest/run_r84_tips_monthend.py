"""Attempt 61 (Round 84): month-end index-extension long on 10-year TIPS (FRED DFII10 real yield), the in-market
replication after attempt 60 bounded the effect to the US. Single selectable cell (floor 2.0), same window, bar,
cut, proxy and read-onlys as attempt 60 v2 (run_r83_monthend_global.main), plus a registered read-only split of
C1 by 10-year-TIPS settlement months (Jan/Mar/May/Jul/Sep/Nov: the constant-maturity point rolls onto the new
issue at the month-end close) vs other months, and the nominal-orthogonalised differential (beta on the DGS10
same-window price from the market's own IS controls) as the pre-stated mechanism discriminator.
Inflation accrual is omitted from the proxy (conservative for the long; common to events and controls).
Outputs results/r84_tips_monthend_{is,oos}.json. OOS only with UNSEAL_OK=1 --unseal after an IS pass.
"""
import run_r83_monthend_global as R

MARKETS = {"US": R.MARKETS["US"], "TIPS": ("fred_DFII10.csv", 2, True)}
R.SPLIT_MONTHS = {1, 3, 5, 7, 9, 11}

if __name__ == "__main__":
    R.main(MARKETS, t_floor_is=2.0, tag="r84_tips_monthend", single=True)
