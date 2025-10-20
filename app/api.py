from fastapi import FastAPI
import pandas as pd
from .db import ENGINE

app = FastAPI(title="NFL Best Bets (DraftKings)")

@app.get("/recs/top")
def top_recs(limit: int = 10, min_edge: float = 0.015, market: str | None = None):
    q = """
      SELECT * FROM recommendations
      WHERE edge >= %(min_edge)s
      """ + ("" if market is None else " AND market=%(market)s ") + """
      ORDER BY confidence DESC, edge DESC
      LIMIT %(limit)s
    """
    df = pd.read_sql(q, ENGINE, params={"limit": limit, "min_edge": min_edge, "market": market})
    return df.to_dict(orient="records")

@app.get("/projections")
def projections():
    q = """
      SELECT season, game_id, home_team, away_team, proj_home_pts, proj_away_pts,
             proj_spread, proj_total, home_wp, asof_snapshot
      FROM projections
      ORDER BY asof_snapshot DESC, home_team
      LIMIT 100
    """
    df = pd.read_sql(q, ENGINE)
    return df.to_dict(orient="records")
