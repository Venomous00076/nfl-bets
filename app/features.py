import json
import pandas as pd
from sqlalchemy import text
from .db import ENGINE

def load_team_game_features() -> pd.DataFrame:
    q = """
    SELECT season, game_id, posteam as team, play_id, epa, success, play_type
    FROM raw_pbp
    """
    df = pd.read_sql(q, ENGINE)
    g = df.groupby(["season","game_id","team"]).agg(
        plays=("play_id","count"),
        epa=("epa","mean"),
        sr=("success","mean"),
        rush_plays=("play_type", lambda s: (s=="run").sum()),
        pass_plays=("play_type", lambda s: (s=="pass").sum())
    ).reset_index()
    g["rush_rate"] = g["rush_plays"] / g["plays"]
    g["pass_rate"] = g["pass_plays"] / g["plays"]
    return g

def ewma_recent(team_games: pd.DataFrame, span_games: int = 2) -> pd.DataFrame:
    out=[]
    for (season, team), grp in team_games.sort_values("game_id").groupby(["season","team"]):
        tmp=grp.copy()
        for c in ["epa","sr","rush_rate","pass_rate"]:
            tmp[f"{c}_ewm"] = tmp[c].ewm(span=span_games, adjust=False).mean()
        out.append(tmp)
    return pd.concat(out) if out else pd.DataFrame(columns=team_games.columns)

def blend_recent_vs_season(df_ewm: pd.DataFrame, w_recent=0.6) -> pd.DataFrame:
    if df_ewm.empty:
        return df_ewm
    base = df_ewm.groupby(["season","team"]).agg(
        epa_season=("epa","mean"),
        sr_season=("sr","mean"),
        rush_rate_season=("rush_rate","mean"),
        pass_rate_season=("pass_rate","mean")
    ).reset_index()
    last = df_ewm.sort_values("game_id").groupby(["season","team"]).tail(1)
    m = last.merge(base, on=["season","team"])
    for c in ["epa","sr","rush_rate","pass_rate"]:
        m[f"{c}_blend"] = w_recent*m[f"{c}_ewm"] + (1-w_recent)*m[f"{c}_season"]
    return m

def persist_team_features(m: pd.DataFrame):
    if m.empty: return
    rows=[]
    for _,r in m.iterrows():
        feat = {
            "epa": float(r["epa_blend"]),
            "sr": float(r["sr_blend"]),
            "rush_rate": float(r["rush_rate_blend"]),
            "pass_rate": float(r["pass_rate_blend"]),
        }
        rows.append(dict(season=int(r["season"]), team=r["team"], feat=json.dumps(feat), asof_game=r["game_id"]))
    pd.DataFrame(rows).to_sql("team_features", ENGINE, if_exists="append", index=False, method="multi")

def run_features():
    team_games = load_team_game_features()
    ewm = ewma_recent(team_games, span_games=2)
    m = blend_recent_vs_season(ewm, w_recent=0.6)
    persist_team_features(m)

if __name__ == "__main__":
    run_features()
