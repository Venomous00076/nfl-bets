"""
Projection core:
- Convert blended EPA/SR to points per game proxy
- Derive spread/total
- Win prob from spread (logistic)
- Robust mapping from DraftKings team strings -> canonical team codes
"""
import numpy as np
import pandas as pd
from .db import ENGINE
from sqlalchemy import text
from .util_team_names import dk_to_code, code_to_name

HOME_EDGE_PTS = 1.5  # base home advantage

def load_latest_team_feats() -> pd.DataFrame:
    q = """
    SELECT DISTINCT ON (season, team)
           season, team, feat, asof_game
    FROM team_features
    ORDER BY season, team, asof_game DESC
    """
    return pd.read_sql(q, ENGINE)

def team_strength_to_ppg(feat_row):
    epa = feat_row["feat"]["epa"]
    sr  = feat_row["feat"]["sr"]
    base = 21 + 40*epa + 7*(sr-0.5)  # rough heuristic centered around ~21
    return max(10, min(45, base))    # clamp to reasonable band

def pair_games_from_odds_snapshot(snapshot_ts: str) -> pd.DataFrame:
    q = """
    WITH latest AS (
      SELECT * FROM odds_raw
      WHERE snapshot_ts = :snap AND book='DraftKings'
    )
    SELECT DISTINCT event_id as game_id,
           MAX(home_team) as home_team_str,
           MAX(away_team) as away_team_str,
           MIN(commence_time) as commence_time
    FROM latest
    GROUP BY event_id
    """
    return pd.read_sql(text(q), ENGINE, params={"snap": snapshot_ts})

def build_projections(snapshot_ts: str) -> pd.DataFrame:
    teams = load_latest_team_feats()
    if teams.empty:
        return pd.DataFrame()
    teams.set_index(["team"], inplace=True)

    games = pair_games_from_odds_snapshot(snapshot_ts)
    rows=[]
    for _,g in games.iterrows():
        home_code = dk_to_code(g["home_team_str"])
        away_code = dk_to_code(g["away_team_str"])
        if not home_code or not away_code:
            # skip games we can't map
            continue
        if home_code not in teams.index or away_code not in teams.index:
            continue

        f_home = teams.loc[home_code]
        f_away = teams.loc[away_code]

        ph = team_strength_to_ppg(f_home)
        pa = team_strength_to_ppg(f_away)
        ph += HOME_EDGE_PTS

        proj_spread = ph - pa
        proj_total  = ph + pa

        # Logistic WP from spread (coefs can be tuned)
        beta0, beta1 = 0.0, 0.23
        home_wp = 1/(1 + np.exp(-(beta0 + beta1*proj_spread)))

        rows.append(dict(
            season=int(pd.to_datetime(g["commence_time"]).year) if pd.notnull(g["commence_time"]) else 2025,
            game_id=g["game_id"],
            home_team=home_code, away_team=away_code,
            proj_home_pts=round(ph,2), proj_away_pts=round(pa,2),
            proj_spread=round(proj_spread,2), proj_total=round(proj_total,2),
            home_wp=round(float(home_wp),4)
        ))
    return pd.DataFrame(rows)

def persist_projections(df: pd.DataFrame, snapshot_ts: str):
    if not len(df): return
    df["asof_snapshot"] = snapshot_ts
    df.to_sql("projections", ENGINE, if_exists="append", index=False, method="multi")
