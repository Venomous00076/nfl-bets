import datetime as dt
import pandas as pd
from sqlalchemy import text
from app.db import ENGINE
from app.util_team_names import dk_to_code, ALL_TEAM_CODES

def main():
    season = dt.datetime.utcnow().year

    # Try to pull team names from the latest odds snapshot (preferred)
    snap_df = pd.read_sql(text("SELECT snapshot_ts FROM odds_raw ORDER BY snapshot_ts DESC LIMIT 1"), ENGINE)
    if snap_df.empty:
        # No odds yet; just seed all 32 teams
        codes = set(ALL_TEAM_CODES)
    else:
        snap = snap_df.iloc[0,0]
        ev = pd.read_sql(
            text("SELECT DISTINCT home_team, away_team FROM odds_raw WHERE snapshot_ts = :snap AND book='DraftKings'"),
            ENGINE, params={"snap": snap}
        )
        codes = set()
        for _, r in ev.iterrows():
            for col in ("home_team","away_team"):
                c = dk_to_code(r[col])
                if c: codes.add(c)
        if not codes:
            codes = set(ALL_TEAM_CODES)

    rows=[]
    for code in sorted(codes):
        feat = dict(epa=0.0, sr=0.5, rush_rate=0.45, pass_rate=0.55)
        rows.append(dict(season=season, team=code, feat=feat, asof_game=f"BOOTSTRAP-{season}"))
    if rows:
        df = pd.DataFrame(rows)
        df.to_sql("team_features", ENGINE, if_exists="append", index=False, method="multi")
        print(f"Inserted {len(df)} bootstrap team_features rows for season {season}.")
    else:
        print("No rows to insert (unexpected).")

if __name__ == "__main__":
    main()
