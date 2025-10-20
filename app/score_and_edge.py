import numpy as np, pandas as pd
from sqlalchemy import text
from .db import ENGINE
from sqlalchemy import text

def american_to_prob(odds: int) -> float:
    return (100/(-odds+100)) if odds<0 else (100/(odds+100))

def kelly(p, price):
    b = (abs(price)/100.0) if price>0 else (100.0/abs(price))
    return max(0.0, (p*(b+1)-1)/b)

def latest_snapshot_ts() -> str:
    q = "SELECT snapshot_ts FROM odds_raw ORDER BY snapshot_ts DESC LIMIT 1"
    df = pd.read_sql(q, ENGINE)
    return df.iloc[0,0] if not df.empty else None

def load_odds(snapshot_ts: str) -> pd.DataFrame:
    q = """
      SELECT * FROM odds_raw
      WHERE snapshot_ts = :snap AND book='DraftKings'
    """
    return pd.read_sql(text(q), ENGINE, params={"snap": snapshot_ts})

def compute_edges(proj: pd.DataFrame, odds: pd.DataFrame) -> pd.DataFrame:
    recs=[]
    for _,p in proj.iterrows():
        gid = p["game_id"]
        od = odds[odds["event_id"]==gid]
        if od.empty: 
            continue
        # MONEYLINE
        ml = od[od["market"]=="h2h"]
        for side, p_model in [("home", p["home_wp"]), ("away", 1-p["home_wp"])]:
            subset = ml[ml["outcome"].str.contains(side, case=False, na=False)]
            for _,o in subset.iterrows():
                imp = american_to_prob(int(o["price_american"]))
                ev  = p_model - imp
                k   = kelly(p_model, int(o["price_american"]))
                conf = "HIGH" if ev>0.03 else "MED" if ev>0.015 else "LOW"
                recs.append(dict(
                    snapshot_ts=od["snapshot_ts"].iloc[0],
                    game_id=gid, home_team=p["home_team"], away_team=p["away_team"],
                    market="moneyline", selection=side,
                    best_book="DraftKings", best_price=int(o["price_american"]),
                    line_point=None, model_prob=round(p_model,4),
                    edge=round(ev,4), kelly_frac=round(k,3),
                    confidence=conf, notes=""
                ))
        # SPREADS
        sp = od[od["market"]=="spreads"]
        for side, pred_margin in [("home", p["proj_spread"]), ("away", -p["proj_spread"])]:
            subset = sp[sp["outcome"].str.contains(side, case=False, na=False)]
            for _,o in subset.iterrows():
                line = float(o["point"])
                # Normal error proxy for cover prob
                sd = 13.0
                from math import erf, sqrt
                z = (pred_margin - line)/sd
                p_cover = 0.5*(1+erf(z/sqrt(2)))
                imp = american_to_prob(int(o["price_american"]))
                ev  = p_cover - imp
                k   = kelly(p_cover, int(o["price_american"]))
                conf = "HIGH" if ev>0.03 else "MED" if ev>0.015 else "LOW"
                recs.append(dict(
                    snapshot_ts=od["snapshot_ts"].iloc[0],
                    game_id=gid, home_team=p["home_team"], away_team=p["away_team"],
                    market="spreads", selection=f"{side} {line:+}",
                    best_book="DraftKings", best_price=int(o["price_american"]),
                    line_point=line, model_prob=round(p_cover,4),
                    edge=round(ev,4), kelly_frac=round(k,3),
                    confidence=conf, notes=""
                ))
        # TOTALS
        tot = od[od["market"]=="totals"]
        for side, pred_total in [("over", p["proj_total"]), ("under", p["proj_total"])]:
            for _,o in tot[tot["outcome"].str.contains(side, case=False, na=False)].iterrows():
                line = float(o["point"])
                sd = 14.0
                from math import erf, sqrt
                z = (pred_total - line)/sd
                p_hit = 0.5*(1+erf(z/sqrt(2))) if side=="over" else 1 - 0.5*(1+erf(z/sqrt(2)))
                imp = american_to_prob(int(o["price_american"]))
                ev  = p_hit - imp
                k   = kelly(p_hit, int(o["price_american"]))
                conf = "HIGH" if ev>0.03 else "MED" if ev>0.015 else "LOW"
                recs.append(dict(
                    snapshot_ts=od["snapshot_ts"].iloc[0],
                    game_id=gid, home_team=p["home_team"], away_team=p["away_team"],
                    market="totals", selection=f"{side} {line}",
                    best_book="DraftKings", best_price=int(o["price_american"]),
                    line_point=line, model_prob=round(p_hit,4),
                    edge=round(ev,4), kelly_frac=round(k,3),
                    confidence=conf, notes=""
                ))
    return pd.DataFrame(recs)

def persist_recs(df: pd.DataFrame):
    if not len(df): return
    df.to_sql("recommendations", ENGINE, if_exists="append", index=False, method="multi")

def run_edges_for_latest_snapshot():
    snap = latest_snapshot_ts()
    if not snap:
        raise RuntimeError("No odds snapshot found.")
    proj = pd.read_sql(text("SELECT * FROM projections WHERE asof_snapshot = :snap"), ENGINE, params={"snap": snap})
    if proj.empty:
        raise RuntimeError("No projections found for latest snapshot.")
    odds = load_odds(snap)
    recs = compute_edges(proj, odds)
    persist_recs(recs)
    return snap, recs
